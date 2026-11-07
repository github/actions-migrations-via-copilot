"""Write explicit cloud-session plugin settings without relying on org defaults."""
import json
from pathlib import Path
import re
import sys


def configure(workspace, session, marketplace):
    if session not in {"repo", "plugin"}:
        raise ValueError("Unknown cloud session")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", marketplace):
        raise ValueError("Expected an owner/repo marketplace")
    names = {"actions-migrator", "hc-probe-a", "hc-probe-b", "hc-probe-ns"}
    enabled = {"actions-migrator"} if session == "repo" else names - {"actions-migrator"}
    settings = {
        "enabledPlugins": {f"{name}@hc-probes": name in enabled for name in sorted(names)},
        "extraKnownMarketplaces": {
            "hc-probes": {"source": {"source": "github", "repo": marketplace}},
        },
    }
    settings["enabledPlugins"]["actions-migrator@actions-migrations-via-copilot"] = False
    destination = workspace / ".github/copilot/settings.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(settings, indent=2) + "\n")


if __name__ == "__main__":
    configure(Path(sys.argv[1]), sys.argv[2], sys.argv[3])