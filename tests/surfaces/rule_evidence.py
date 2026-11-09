#!/usr/bin/env python3
"""Reduce one isolated VS Code rule run to rule-specific evidence."""
import argparse
import hashlib
import json
import sys
from pathlib import Path


TARGET = "hc-out/rule-marker.txt"
MARKERS = {"current": "RULE_LEGACY", "namespace": "RULE_NS"}


def marker_write(tool_name, arguments):
    target = arguments.get("path") if isinstance(arguments, dict) else None
    target_path = Path(target) if isinstance(target, str) else None
    return tool_name in {"create", "edit"} and target_path is not None and (
        ".." not in target_path.parts and (
            target_path == Path(TARGET) or
            target_path.is_absolute() and target_path.parts[-2:] == Path(TARGET).parts
        )
    )


def capture_client_output(stream, destination):
    discovered = False
    calls = set()
    with destination.open("w") as output:
        def record(event_type, data):
            output.write(json.dumps({"type": event_type, "data": data}) + "\n")

        for line in stream:
            prefix = "Ready plugin components: "
            if line.startswith(prefix):
                try:
                    plugins = json.loads(line[len(prefix):])
                    discovered = any(plugin.get("name") in {"hc-rule-probe", "Plugin: hc-rule-probe"}
                                     for plugin in plugins if isinstance(plugin, dict))
                except (ValueError, TypeError):
                    pass
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict) or not isinstance(event.get("data"), dict):
                continue
            data = event["data"]
            event_type = event.get("type")
            if event_type == "turn_complete":
                record("session.complete", {})
            call_id = data.get("toolCallId")
            if not isinstance(call_id, str) or not call_id:
                continue
            if event_type == "tool_call_ready":
                arguments = data.get("toolInput")
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except ValueError:
                        arguments = None
                if data.get("toolName") in {"create", "edit"} and not isinstance(arguments, dict):
                    record("tool.input_unavailable", {})
                elif marker_write(data.get("toolName"), arguments):
                    calls.add(call_id)
                    record("tool.execution_start", {"toolCallId": call_id,
                           "toolName": data["toolName"], "arguments": {"path": TARGET}})
            elif event_type == "tool_call_complete" and call_id in calls:
                result = data.get("result")
                record("tool.execution_complete", {"toolCallId": call_id,
                       "success": isinstance(result, dict) and result.get("success") is True})
    return discovered


def sources(path):
    return sorted(path.glob("*/events.jsonl")) if path.is_dir() else [path]


def jsonl(path):
    for source in sources(path):
        if not source.is_file():
            continue
        with source.open(errors="replace") as stream:
            for line in stream:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def assess(rule_format, delivery_log, events_file, workspace, fixture_sha, metadata):
    metadata = dict(metadata)
    deliveries = [record for record in jsonl(delivery_log) if isinstance(record, dict)]
    resource_read = any(record.get("resource_read") is True for record in deliveries)
    exact_delivery = any(record.get("resource_read") is True
                         and record.get("sha256") == fixture_sha
                         and record.get("matches_expected") is True
                         for record in deliveries)
    calls = {}
    event_record_seen = False
    input_unavailable = False
    for event in jsonl(events_file):
        if not isinstance(event, dict):
            continue
        event_record_seen = True
        if event.get("type") == "tool.input_unavailable":
            input_unavailable = True
        if event.get("type") not in {"tool.execution_start", "tool.execution_complete"}:
            continue
        data = event.get("data", {})
        if not isinstance(data, dict):
            continue
        call_id = data.get("toolCallId")
        if not isinstance(call_id, str) or not call_id:
            continue
        if event.get("type") == "tool.execution_start":
            arguments = data.get("arguments", {})
            if marker_write(data.get("toolName"), arguments):
                calls[call_id] = {
                    "tool": data.get("toolName"),
                    "execution": "not_observed",
                }
        elif event.get("type") == "tool.execution_complete" and call_id in calls:
            calls[call_id]["execution"] = (
                "succeeded" if data.get("success") is True else "failed"
            )

    marker = workspace / TARGET
    event_file_present = any(source.is_file() for source in sources(events_file))
    marker_exists = marker.is_file()
    marker_matches = marker_exists and not marker.is_symlink() and (
        marker.read_text(errors="replace").strip() == MARKERS[rule_format]
    )
    plugin_discovered = str(metadata.pop("plugin_discovered", "false")).lower() == "true"
    server_matches_pin = str(metadata.get("server_commit_matches_pin", "false")).lower() == "true"
    session_exit = metadata.get("session_exit")
    if not server_matches_pin or not plugin_discovered or not resource_read \
            or not event_record_seen or input_unavailable or not workspace.is_dir():
        result = "NOT RUN"
    elif session_exit != "0":
        result = "NOT RUN"
    elif not exact_delivery:
        result = "DEVIATION"
    elif marker_matches and any(call["execution"] == "succeeded" for call in calls.values()):
        result = "PASS"
    else:
        result = "DEVIATION"

    if result == "NOT RUN":
        if not server_matches_pin:
            diagnosis = "Agent Host server did not match the requested commit"
        elif not plugin_discovered or not resource_read:
            diagnosis = "no conclusive rule-delivery evidence"
        elif not event_record_seen or input_unavailable or not workspace.is_dir():
            diagnosis = "evidence collection incomplete"
        else:
            diagnosis = "session did not complete"
    elif result == "DEVIATION":
        diagnosis = "rule content differed from fixture" if not exact_delivery else "unresolved"
    else:
        diagnosis = "rule-specific marker action observed"

    return {
        "result": result,
        "metadata": metadata,
        "plugin_discovered": plugin_discovered,
        "rule_resource": {
            "read_by_agent_host": resource_read,
            "exact_fixture_text_returned": exact_delivery,
            "observed_sha256": sorted({record.get("sha256") for record in deliveries
                                       if isinstance(record.get("sha256"), str)}),
            "fixture_sha256": fixture_sha,
        },
        "model_delivery": {
            "status": "not_observable",
            "note": "The resource read proves delivery to Agent Host, not inclusion in model context.",
        },
        "marker_tool": {
            "attempted": bool(calls),
            "calls": list(calls.values()),
        },
        "model_compliance": {
            "marker_instruction_followed": bool(calls),
            "evidence": "target tool-call attempt",
        },
        "marker_file": {
            "exists": marker_exists,
            "matches_expected": marker_matches,
        },
        "evidence_collection": {
            "delivery_log_present": delivery_log.is_file(),
            "event_file_present": event_file_present,
            "event_record_seen": event_record_seen,
            "tool_input_unavailable": input_unavailable,
            "marker_workspace_present": workspace.is_dir(),
        },
        "diagnosis": diagnosis,
    }


def main():
    if sys.argv[1:2] == ["capture"]:
        parser = argparse.ArgumentParser()
        parser.add_argument("capture")
        parser.add_argument("destination", type=Path)
        options = parser.parse_args()
        print(str(capture_client_output(sys.stdin, options.destination)).lower())
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=MARKERS, required=True)
    parser.add_argument("--delivery-log", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--rule-file", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--meta", action="append", default=[])
    options = parser.parse_args()
    fixture_sha = hashlib.sha256(options.rule_file.read_bytes()).hexdigest()
    metadata = dict(item.split("=", 1) for item in options.meta if "=" in item)
    evidence = assess(options.format, options.delivery_log, options.events,
                      options.workspace, fixture_sha, metadata)
    options.out.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"result={evidence['result']} delivery={evidence['rule_resource']['exact_fixture_text_returned']} "
          f"marker_attempted={evidence['marker_tool']['attempted']} "
          f"marker_matches={evidence['marker_file']['matches_expected']}")
    raise SystemExit(0 if evidence["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
