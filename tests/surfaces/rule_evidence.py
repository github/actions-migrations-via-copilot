#!/usr/bin/env python3
"""Reduce one isolated VS Code rule run to rule-specific evidence."""
import argparse
import hashlib
import json
from pathlib import Path


TARGET = "hc-out/rule-marker.txt"
MARKERS = {"current": "RULE_LEGACY", "namespace": "RULE_NS"}


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
    deliveries = [record for record in jsonl(delivery_log) if isinstance(record, dict)]
    resource_read = any(record.get("resource_read") is True for record in deliveries)
    exact_delivery = any(record.get("resource_read") is True
                         and record.get("sha256") == fixture_sha
                         and record.get("matches_expected") is True
                         for record in deliveries)
    calls = {}
    event_record_seen = False
    for event in jsonl(events_file):
        if not isinstance(event, dict):
            continue
        event_record_seen = True
        if event.get("type") not in {"tool.execution_start", "tool.execution_complete"}:
            continue
        data = event.get("data", {})
        if not isinstance(data, dict):
            continue
        call_id = data.get("toolCallId")
        if event.get("type") == "tool.execution_start":
            arguments = json.dumps(data.get("arguments", {}), sort_keys=True)
            if TARGET in arguments:
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
    marker_matches = marker_exists and MARKERS[rule_format] in marker.read_text(errors="replace")
    plugin_discovered = str(metadata.pop("plugin_discovered", "false")).lower() == "true"
    server_matches_pin = str(metadata.get("server_commit_matches_pin", "false")).lower() == "true"
    session_exit = metadata.get("session_exit")
    if not server_matches_pin or not plugin_discovered or not resource_read \
            or not event_record_seen or not workspace.is_dir():
        result = "NOT RUN"
    elif not exact_delivery:
        result = "DEVIATION"
    elif marker_matches and any(call["execution"] == "succeeded" for call in calls.values()):
        result = "PASS"
    elif session_exit is not None and session_exit != "0":
        result = "NOT RUN"
    else:
        result = "DEVIATION"

    if result == "NOT RUN":
        if not server_matches_pin:
            diagnosis = "Agent Host server did not match the requested commit"
        elif not plugin_discovered or not resource_read:
            diagnosis = "no conclusive rule-delivery evidence"
        elif not event_record_seen or not workspace.is_dir():
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
            "marker_workspace_present": workspace.is_dir(),
        },
        "diagnosis": diagnosis,
    }


def main():
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


if __name__ == "__main__":
    main()
