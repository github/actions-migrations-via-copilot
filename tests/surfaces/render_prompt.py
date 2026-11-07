#!/usr/bin/env python3
"""render_prompt.py <prompt.md> <local|cloud>: fill in the surface-specific parts of a prompt."""
import sys

text = open(sys.argv[1]).read()
# Built at runtime so no file in this repo contains the fake credential line.
fake = "| DEPLOY_TOKEN | " + "Synthetic" + "Probe12345abcdef" + " |"
if sys.argv[2] == "cloud":
    note = ("The hooks write `.hook-conformance/probe.jsonl` by themselves. "
            "Don't edit that file yourself, but do include it in your commit.")
    finish = ("Then commit all new files, including the hook-written "
              "`.hook-conformance/probe.jsonl`, and open the pull request.")
else:
    note = "Do not edit anything under `.hook-conformance/`."
    finish = "Do not run any git commands and do not open a pull request."
print(text.replace("{{LOG_NOTE}}", note).replace("{{FINISH}}", finish).replace("{{FAKE_LINE}}", fake))
