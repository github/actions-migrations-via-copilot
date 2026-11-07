"""Publish test evidence without connection tokens, credentials, or model catalogs."""
import argparse
import os
from pathlib import Path
import re


def publish(source, destination):
    source = source.resolve()
    destination = destination.resolve()
    secrets = [value for name, value in os.environ.items()
               if name in {"COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"} and len(value) >= 8]
    allowed = {"score.json", "probe.jsonl", "events.jsonl", "session.log", "transcript.md",
               "stderr.log", "plugin-install.log", "agent-host.log", "agents.log",
               "hc-probe-agent.log", "hc-probe-ns-agent.log", "run.log"}
    for path in source.rglob("*"):
        if path.name not in allowed or not path.is_file():
            continue
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError("Symlink in test evidence")
        text = path.read_text(errors="replace")
        for secret in secrets:
            text = text.replace(secret, "[redacted]")
        text = re.sub(r"github_pat_[A-Za-z0-9_]{20,}|gh[opsur]_[A-Za-z0-9]{30,}", "[redacted]", text)
        text = re.sub(r"tkn=[^\s\"'&<>]+", "tkn=REDACTED", text)
        text = text.replace("Synthetic" + "Probe12345abcdef", "[fake-credential]")
        output = destination / path.relative_to(source)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    options = parser.parse_args()
    publish(options.source.resolve(), options.destination.resolve())