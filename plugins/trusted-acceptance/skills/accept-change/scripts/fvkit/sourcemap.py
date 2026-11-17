"""Model action <-> real code mapping, and the drift detector that keeps a model honest.

`source-map.yaml` is written by people: which file/symbol implements each model action, the
verbatim anchor text that must still exist there, the claimed atomicity boundary, and the
protected paths whose change invalidates the mapping. `source-map.lock.json` is written by
`fv source-map sync` after a review: per-file digests, the model digest, the git commit the
mapping was reviewed against and who reviewed it. `verify` compares all of that with the
current checkout; a model that "still passes" while the code moved on is reported STALE.
"""
import fnmatch
import json
import re
import subprocess
from pathlib import Path

from .values import FvError, digest, require, sha_bytes


def glob_match(path, pattern):
    """fnmatch with `**` spanning directories."""
    rx = ""
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            rx += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            rx += ".*"
            i += 2
        elif pattern[i] == "*":
            rx += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            rx += "[^/]"
            i += 1
        else:
            rx += re.escape(pattern[i])
            i += 1
    return re.fullmatch(rx, path) is not None


def git(root, *args, check=True):
    run = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=60)
    if check and run.returncode != 0:
        raise FvError("git %s failed: %s" % (" ".join(args[:2]), run.stderr.strip()[:200]))
    return run


def repo_root(start):
    return Path(git(start, "rev-parse", "--show-toplevel").stdout.strip()).resolve()


def changed_files(root, base):
    """Files that differ between `base` and the working tree, plus untracked files."""
    names = set()
    r = git(root, "diff", "--name-only", "--relative", base or "HEAD", "--", check=False)
    if r.returncode != 0 and base:
        raise FvError("unknown base revision %s" % base)
    names |= {n for n in r.stdout.splitlines() if n}
    names |= {n for n in git(root, "ls-files", "--others", "--exclude-standard").stdout.splitlines() if n}
    return sorted(names)


def _inside(root, rel):
    require(isinstance(rel, str) and rel and not rel.startswith("/") and "\\" not in rel, "invalid repository path %r" % rel)
    p = (root / rel).resolve()
    require(p == root or root in p.parents, "path escapes repository: %s" % rel)
    return p


def load_map(path):
    from .spec import _keys, load_document
    doc = load_document(path)
    _keys(doc, ["schema_version", "kind", "model", "actions"],
          ["root", "environment_actions", "observables", "protected_paths", "notes", "atomicity_assumptions"], "source map")
    require(doc["schema_version"] == 1 and doc["kind"] == "fv-source-map", "unsupported source map")
    for name, spec in doc["actions"].items():
        _keys(spec, ["locations"], ["atomicity", "notes"], "source map action " + name)
        require(isinstance(spec["locations"], list) and spec["locations"], "action %s needs at least one location" % name)
        for loc in spec["locations"]:
            _keys(loc, ["path", "anchor"], ["symbol", "notes"], "location of " + name)
            require(isinstance(loc["anchor"], str) and loc["anchor"].strip(), "action %s: anchor must be verbatim nonempty text" % name)
    for name, why in (doc.get("environment_actions") or {}).items():
        require(isinstance(why, str) and why.strip(), "environment action %s needs a reason (why no code implements it)" % name)
    for name, spec in (doc.get("observables") or {}).items():
        _keys(spec, ["locations"], ["notes"], "source map observable " + name)
    return doc


def _locations(doc):
    for kind in ("actions", "observables"):
        for name, spec in (doc.get(kind) or {}).items():
            for loc in spec["locations"]:
                yield kind, name, loc


def map_root(map_path, doc, root=None):
    """Paths in a source map are relative to `root:` (relative to the map file) or the git top level."""
    if root:
        return Path(root).resolve()
    if doc.get("root"):
        return (Path(map_path).resolve().parent / doc["root"]).resolve()
    return repo_root(Path(map_path).resolve().parent)


def lock_path(map_path):
    p = Path(map_path)
    return p.with_name(p.name.rsplit(".", 1)[0] + ".lock.json")


def verify(map_path, model, root=None):
    map_path = Path(map_path)
    doc = load_map(map_path)
    root = map_root(map_path, doc, root)
    issues, drift, stale = [], [], []
    actions = {a.name for a in model.actions}
    mapped, env_actions = set(doc["actions"]), set(doc.get("environment_actions") or {})
    if set(doc.get("observables") or {}) - set(model.observables):
        issues.append("observables mapped that the contract does not declare: %s" % sorted(set(doc["observables"]) - set(model.observables)))
    for a in sorted(actions - mapped - env_actions):
        issues.append("model action %s has no code location and no environment_actions reason" % a)
    for a in sorted((mapped | env_actions) - actions):
        issues.append("source map names %s, which is not a model action" % a)
    for a in sorted(mapped & env_actions):
        issues.append("action %s is both mapped and declared environment-only" % a)
    files = {}
    for kind, name, loc in _locations(doc):
        try:
            p = _inside(root, loc["path"])
        except FvError as error:
            issues.append(str(error))
            continue
        if not p.is_file():
            issues.append("%s %s: %s does not exist" % (kind[:-1], name, loc["path"]))
            continue
        data = p.read_bytes()
        files[loc["path"]] = sha_bytes(data)
        if data.decode("utf-8", "replace").count(loc["anchor"]) == 0:
            issues.append("%s %s: anchor no longer present in %s: %r" % (kind[:-1], name, loc["path"], loc["anchor"][:80]))
    lock_file = lock_path(map_path)
    lock = json.loads(lock_file.read_text()) if lock_file.is_file() else None
    protected = list(doc.get("protected_paths") or []) + sorted(files)
    if lock is None:
        stale.append("never synced: run `fv source-map sync` after reviewing the mapping")
    else:
        if lock.get("map_digest") != digest(doc):
            stale.append("source map edited since the last reviewed sync")
        if lock.get("model_digest") != model.digest:
            stale.append("model changed since the mapping was reviewed (%s)" % model.id)
        for path, d in sorted(files.items()):
            if lock.get("files", {}).get(path) != d:
                drift.append(path)
        commit = lock.get("commit")
        if commit:
            changed = [f for f in changed_files(root, commit) if any(glob_match(f, pat) for pat in protected)]
            if changed:
                stale.append("protected paths changed since reviewed commit %s: %s" % (commit[:12], changed[:20]))
    status = "BROKEN" if issues else "STALE" if (drift or stale) else "FRESH"
    return {"status": status, "issues": issues, "drifted_files": drift, "stale": stale,
            "files": files, "lock": lock, "map_digest": digest(doc), "model_digest": model.digest, "root": str(root)}


def sync(map_path, model, reviewer, reason, signer_kind="human", authorization=None, root=None):
    require(isinstance(reviewer, str) and reviewer.strip() and isinstance(reason, str) and reason.strip(),
            "sync records a review: --by and --reason are required")
    require(signer_kind in ("human", "delegated_agent"), "signer kind must be human|delegated_agent")
    require(signer_kind == "human" or (authorization and authorization.strip()),
            "a delegated sync must quote the human authorization")
    map_path = Path(map_path)
    doc = load_map(map_path)
    root = map_root(map_path, doc, root)
    result = verify(map_path, model, root)
    require(not result["issues"], "cannot sync a broken mapping: %s" % "; ".join(result["issues"]))
    protected = list(doc.get("protected_paths") or []) + sorted(result["files"])
    dirty = [f for f in changed_files(root, None) if any(glob_match(f, pat) for pat in protected)]
    require(not dirty, "commit the reviewed code first; uncommitted protected changes: %s" % dirty[:20])
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    from datetime import datetime, timezone
    lock = {"schema_version": 1, "kind": "fv-source-map-lock", "map_digest": result["map_digest"],
            "model_digest": model.digest, "model_id": model.id, "files": result["files"], "commit": head,
            "reviewed_by": reviewer, "signer_kind": signer_kind, "authorization": authorization, "reason": reason,
            "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat()}
    lp = lock_path(map_path)
    lp.write_text(json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    log = lp.with_name(lp.name.replace(".lock.json", ".sync-log.jsonl"))
    with log.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(lock, ensure_ascii=False, sort_keys=True) + "\n")
    return lock


def match_any(path, patterns):
    return any(glob_match(path, p) or fnmatch.fnmatch(path, p) for p in patterns)
