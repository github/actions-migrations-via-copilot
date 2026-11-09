"""Write explicit cloud-session plugin settings without relying on org defaults."""
import json
import hashlib
from pathlib import Path
import re
import sys


def settings_for(session, marketplace, revision=None):
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
    if revision is not None:
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("Marketplace revision must be a full commit SHA")
        settings["extraKnownMarketplaces"]["hc-probes"]["source"]["ref"] = revision
    return settings


def configure(workspace, session, marketplace, revision=None):
    settings = settings_for(session, marketplace, revision)
    destination = workspace / ".github/copilot/settings.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(settings, indent=2) + "\n")


def authorize(policy, repository, source_sha, fixture):
    source_repository = "github/actions-migrations-via-copilot"
    if repository.get("private") is not True or repository.get("archived") is not False:
        raise ValueError("Cloud tests require a private, non-archived test repository")
    if not repository.get("permissions", {}).get("push"):
        raise ValueError("Cloud test credentials cannot write to the target repository")
    if (policy.get("enabled") is not True or
            policy.get("repository") != repository.get("full_name") or
            policy.get("source_repository") != source_repository):
        raise ValueError("Default-branch policy does not authorize this cloud test target")
    approved = policy.get("source_commits")
    if (not re.fullmatch(r"[0-9a-f]{40}", source_sha) or not isinstance(approved, list) or
            source_sha not in approved):
        raise ValueError("The exact suite commit is not approved by the target repository")
    if fixture.get("source_repository") != source_repository or fixture.get("source_sha") != source_sha:
        raise ValueError("Published cloud fixture does not match the approved local suite commit")


def verify_marketplace(expected, published):
    def files(root):
        paths = list((root / "plugins").rglob("*"))
        paths.extend([root / ".github/plugin/marketplace.json", root / "fixture-source.json"])
        hashes = {}
        for path in paths:
            if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != root.parent):
                raise ValueError("Marketplace fixture contains a symlink")
            if path.is_dir():
                continue
            if not path.is_file():
                raise ValueError("Marketplace fixture file is missing")
            hashes[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return hashes

    expected_hashes = files(expected.resolve())
    published_hashes = files(published.resolve())
    if expected_hashes != published_hashes:
        raise ValueError("Published marketplace bytes do not match fixtures generated from the approved checkout")
    fixture = json.loads((published / "fixture-source.json").read_text())
    expected_plugins = {name: digest for name, digest in expected_hashes.items() if name.startswith("plugins/")}
    if fixture.get("files_sha256") != expected_plugins:
        raise ValueError("Published fixture hash inventory does not match the verified plugin files")


if __name__ == "__main__":
    if sys.argv[1] == "--verify-marketplace":
        verify_marketplace(Path(sys.argv[2]), Path(sys.argv[3]))
    elif sys.argv[1] == "--authorize":
        authorize(json.loads(Path(sys.argv[2]).read_text()), json.loads(Path(sys.argv[3]).read_text()),
                  sys.argv[4], json.loads(Path(sys.argv[5]).read_text()))
    elif sys.argv[1] == "--check":
        actual = json.loads(Path(sys.argv[2]).read_text())
        if actual != settings_for(sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else None):
            sys.exit("Default-branch plugin settings do not match this session; publish the matching configuration before starting it")
    else:
        configure(Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)