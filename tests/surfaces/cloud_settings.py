"""Write explicit cloud-session plugin settings without relying on org defaults."""
import json
from pathlib import Path
import re
import sys


def settings_for(session, marketplace):
    if session not in {"repo", "plugin", "none"}:
        raise ValueError("Unknown cloud session")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", marketplace):
        raise ValueError("Expected an owner/repo marketplace")
    names = {"actions-migrator", "hc-probe-a", "hc-probe-b", "hc-probe-ns"}
    enabled = {"actions-migrator"} if session == "repo" else names - {"actions-migrator"}
    if session == "none":
        enabled = set()
    settings = {
        "enabledPlugins": {f"{name}@hc-probes": name in enabled for name in sorted(names)},
        "extraKnownMarketplaces": {
            "hc-probes": {"source": {"source": "github", "repo": marketplace}},
        },
    }
    settings["enabledPlugins"]["actions-migrator@actions-migrations-via-copilot"] = False
    return settings


def configure(workspace, session, marketplace):
    settings = settings_for(session, marketplace)
    destination = workspace / ".github/copilot/settings.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(settings, indent=2) + "\n")


if __name__ == "__main__":
    if sys.argv[1] == "--check":
        actual = json.loads(Path(sys.argv[2]).read_text())
        if actual != settings_for(sys.argv[3], sys.argv[4]):
            sys.exit("Default-branch plugin settings do not match this session; publish the matching configuration before starting it")
    else:
        configure(Path(sys.argv[1]), sys.argv[2], sys.argv[3])