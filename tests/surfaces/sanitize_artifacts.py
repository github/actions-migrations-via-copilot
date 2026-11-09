"""Publish test evidence without connection tokens, credentials, or model catalogs."""
import argparse
import json
import os
import tempfile
from pathlib import Path
import re


def reject_symlink_components(path):
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError("Symlink in test evidence path")


def publish(source, destination):
    source = Path(os.path.abspath(source))
    destination = Path(os.path.abspath(destination))
    reject_symlink_components(source)
    reject_symlink_components(destination)
    source = source.resolve(strict=True)
    if not source.is_dir():
        raise ValueError("Test evidence source is not a directory")
    if destination == source or source in destination.parents:
        raise ValueError("Test evidence destination must be outside the source")
    destination.mkdir(parents=True, exist_ok=True)
    destination = destination.resolve(strict=True)
    if destination == source or source in destination.parents:
        raise ValueError("Test evidence destination must be outside the source")
    secrets = [value for name, value in os.environ.items()
               if name in {
                   "COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN",
                   "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
                   "ACTIONS_ID_TOKEN_REQUEST_URL", "ACTIONS_CACHE_URL",
                   "ACTIONS_RUNTIME_URL", "ACTIONS_RESULTS_URL",
               } and len(value) >= 8]
    token_pattern = re.compile(
        r"(?<![A-Za-z0-9_])(?:github_pat_[A-Za-z0-9_]{20,}|gh[opsur]_[A-Za-z0-9]{30,})(?![A-Za-z0-9_])"
    )
    runtime_pattern = re.compile(
        r"(?i)(\bACTIONS_(?:RUNTIME_TOKEN|ID_TOKEN_REQUEST_TOKEN|ID_TOKEN_REQUEST_URL|CACHE_URL|RUNTIME_URL|RESULTS_URL)"
        r"\b[\"']?\s*[:=]\s*[\"']?)[^\s,\"'}]+"
    )
    authorization_pattern = re.compile(
        r"(?i)(\bAuthorization[\"']?\s*:\s*[\"']?)(?:(?:Bearer|Basic)\s+)?[^\s,\"'}]+"
    )
    allowed = {"score.json", "probe.jsonl", "fixture-source.json", "plugin-guards.jsonl", "agent-selection.json"}

    def redact(value):
        if isinstance(value, dict):
            if {"raw", "payload", "toolArgs", "tool_input"}.intersection(value):
                raise ValueError("Raw tool payloads are not publishable evidence")
            return {key: "[redacted]" if key.lower() == "authorization" else redact(item)
                    for key, item in value.items()}
        if isinstance(value, list):
            return [redact(item) for item in value]
        if not isinstance(value, str):
            return value
        for secret in secrets:
            value = value.replace(secret, "[redacted]")
        value = token_pattern.sub("[redacted]", value)
        value = runtime_pattern.sub(r"\1[redacted]", value)
        value = authorization_pattern.sub(r"\1[redacted]", value)
        value = re.sub(r"tkn=[^\s\"'&<>]+", "tkn=REDACTED", value)
        return value.replace("Synthetic" + "Probe12345abcdef", "[fake-credential]")

    for path in source.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlink in test evidence")
        if not path.is_file() or path.name not in allowed:
            continue
        resolved = path.resolve(strict=True)
        if source not in resolved.parents:
            raise ValueError("Test evidence file is outside the source")
        if path.stat().st_nlink > 1:
            raise ValueError("Hard link in test evidence")
        text = path.read_text(errors="replace")
        if path.suffix == ".jsonl":
            text = "".join(json.dumps(redact(json.loads(line))) + "\n" for line in text.splitlines() if line.strip())
        else:
            text = json.dumps(redact(json.loads(text)), indent=2) + "\n"
        output = destination / path.relative_to(source)
        output.parent.mkdir(parents=True, exist_ok=True)
        reject_symlink_components(output.parent)
        if output.is_symlink():
            raise ValueError("Symlink in test evidence destination")
        with tempfile.NamedTemporaryFile("w", dir=output.parent, encoding="utf-8", delete=False) as handle:
            handle.write(text)
            temporary = Path(handle.name)
        os.replace(temporary, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    options = parser.parse_args()
    publish(options.source, options.destination)