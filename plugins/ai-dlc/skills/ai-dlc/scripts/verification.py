"""Local orchestration of self-checks, reviews and remote acceptance.

These records are caches, not signatures. A protected service and delivery system
must independently enforce policy; editing a local state file cannot grant authority.
"""
import hashlib
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

MAX_JSON = 2 * 1024 * 1024
STAGES = {"acceptance", "merge", "release"}
BASE_ENV = {"PATH", "HOME", "TMPDIR", "TMP", "TEMP", "LANG", "LC_ALL", "TZ",
            "SystemRoot", "SYSTEMROOT", "USERPROFILE", "LOCALAPPDATA"}
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
ROUTES = {
    "accepted_for_stage": ("none", "continue_stage", False),
    "pending": ("pending", "poll_same_run", False),
    "needs_repair": ("implementation", "route_counterexample", True),
    "needs_review": ("review", "review_evidence", False),
    "infrastructure_blocked": ("environment", "repair_environment", False),
    "checker_blocked": ("checker", "repair_checker", False),
    "blocked": ("unknown", "resolve_missing_evidence_or_capability", False),
    "obsolete": ("obsolete", "archive_only", False),
}


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path):
    require(Path(path).is_file(), "expected a regular file: " + str(path))
    with open(path, "rb") as stream:
        h = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def read_json(path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, "duplicate JSON key: " + key)
            out[key] = value
        return out
    data = Path(path).read_bytes()
    require(len(data) <= MAX_JSON, "JSON exceeds size limit")
    return json.loads(data, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(VerificationError("non-finite JSON")))


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return str(path.resolve())


@contextmanager
def writer_lock(root):
    """Serialize CLI state mutations, including task cancellation and remote I/O."""
    try:
        import fcntl
    except ImportError:
        raise VerificationError("lifecycle writes require POSIX file locking") from None
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    with (path / ".writer.lock").open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def under(path, root):
    return Path(path).resolve().is_relative_to(Path(root).resolve())


def git(*args):
    run = subprocess.run(["git", *args], capture_output=True, timeout=30)
    require(run.returncode == 0, "git command failed: " + " ".join(args[:2]))
    return run.stdout


def repo_root():
    return Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve()


def migrate(st):
    require(st.get("version", 1) in (1, 2), "unsupported lifecycle state version")
    old = st.get("version", 1) == 1
    st["version"] = 2
    st.setdefault("task", {"id": st["slug"], "revision": 1, "status": "active"})
    st.setdefault("verification", {
        "self_check": {"status": "not_configured"},
        "review": {"status": "legacy_local" if old or st.get("acceptance") else "not_run"},
        "trusted": {"status": "not_configured", "runs": {}},
    })
    return st


def source(st, runtime_root):
    """Own snapshot namespace; never substitute this for a Harness/artifact digest."""
    root = repo_root()
    require(not under(root, runtime_root), "lifecycle runtime must not contain the project root")
    tracked = set(git("-C", str(root), "ls-files", "--cached", "-z").decode().split("\0"))
    names = sorted(set(git("-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")) - {""})
    require(len(names) <= 100000, "source scan exceeds limit")
    entries = []
    for name in names:
        path = root / name
        # Only the actual lifecycle runtime is excluded; product files remain visible.
        if name not in tracked and under(path, runtime_root):
            continue
        if path.is_symlink():
            entries.append([name, "symlink", os.readlink(path)])
        elif path.is_file():
            entries.append([name, path.stat().st_mode & 0o777, file_digest(path)])
        elif not path.exists():
            entries.append([name, "deleted"])
        else:
            raise VerificationError("submodule/directory requires an explicit source adapter: " + name)
    sha = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], capture_output=True, text=True).stdout.strip()
    dw = st.get("contract", {}).get("done_when")
    if dw and not Path(dw).is_absolute():
        dw = root / dw
    return {"candidate_sha": sha or None, "source_digest": digest(entries),
            "done_when_digest": file_digest(dw) if dw else None,
            "task_id": st["task"]["id"], "task_revision": st["task"]["revision"]}


def clean_candidate(runtime_root):
    # Exclude runtime only if it is untracked, never hide a tracked modification.
    root = repo_root()
    require(not git("-C", str(root), "diff", "--name-only").strip() and not git("-C", str(root), "diff", "--cached", "--name-only").strip(),
            "trusted acceptance needs a clean committed candidate")
    untracked = git("-C", str(root), "ls-files", "--others", "--exclude-standard", "-z").decode().split("\0")
    require(all(not p or under(root / p, runtime_root) for p in untracked), "untracked product files: commit the candidate first")


def exact_keys(value, keys, label):
    require(isinstance(value, dict) and set(value) == set(keys), label + " has missing or unknown fields")


def protected_file(path, root):
    p = Path(path)
    require(p.is_absolute() and p.is_file() and not under(p, root), "operator file must exist outside candidate: " + str(p))
    return p.resolve()


def validate_config(config, root):
    exact_keys(config, ["schema_version", "project_id", "artifacts_dir", "harness", "trusted"], "integration config")
    require(config["schema_version"] == 1, "unsupported integration config schema")
    require(isinstance(config["project_id"], str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:@+\-]{0,127}", config["project_id"]), "invalid project_id")
    output = Path(config["artifacts_dir"])
    require(output.is_absolute() and not under(output, root), "artifacts_dir must be outside candidate")
    harness = config["harness"]
    if harness is not None:
        exact_keys(harness, ["manifest", "runner", "node", "environment_keys", "timeout_seconds", "required_stages"], "harness config")
        for key in ("manifest", "runner"):
            p = Path(harness[key])
            require(not p.is_absolute() and ".." not in p.parts and under(root / p, root), "unsafe harness path")
        require(harness["manifest"] == ".harness/project.json", "runtime v1 reads .harness/project.json")
        require(isinstance(harness["node"], str) and bool(harness["node"]), "node command required")
        require(isinstance(harness["environment_keys"], list) and all(isinstance(x, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", x) for x in harness["environment_keys"]), "invalid environment_keys")
        require(type(harness["timeout_seconds"]) is int and 1 <= harness["timeout_seconds"] <= 3600, "invalid harness timeout")
        require(isinstance(harness["required_stages"], list) and set(harness["required_stages"]) <= {"pr", "merge", "release"}, "invalid harness required_stages")
    trusted = config["trusted"]
    if trusted is not None:
        exact_keys(trusted, ["client", "control_config", "required_stages", "baseline_check_ids", "check_bundle_digest", "adapter_digest", "environment_digest"], "trusted config")
        protected_file(trusted["client"], root)
        protected_file(trusted["control_config"], root)
        require(isinstance(trusted["required_stages"], list) and bool(trusted["required_stages"]) and set(trusted["required_stages"]) <= STAGES, "invalid trusted required_stages")
        require(isinstance(trusted["baseline_check_ids"], list) and all(isinstance(x, str) and x for x in trusted["baseline_check_ids"]), "invalid baseline_check_ids")
        for key in ("check_bundle_digest", "adapter_digest", "environment_digest"):
            require(isinstance(trusted[key], str) and DIGEST.fullmatch(trusted[key]), "invalid " + key)


def client_identity(config):
    trusted = config["trusted"]
    if trusted is None:
        return None
    client = Path(trusted["client"])
    return {"client": file_digest(client), "protocol": file_digest(client.with_name("protocol.py")),
            "control_config": file_digest(trusted["control_config"])}


def configure(st, path):
    root = repo_root()
    path = protected_file(path, root)
    config = read_json(path)
    validate_config(config, root)
    identity = {"path": str(path), "digest": file_digest(path), "client": client_identity(config)}
    previous = st["verification"].get("config")
    require(previous is None or previous == identity, "integration is fixed for this run; start a new task revision/run to change policy")
    st["verification"]["config"] = identity
    if previous is None:
        st["verification"]["self_check"] = {"status": "not_run" if config["harness"] else "not_configured"}
        st["verification"]["trusted"] = {"status": "not_requested" if config["trusted"] else "not_configured", "runs": {}}
    return config


def configuration(st):
    ref = st["verification"].get("config")
    if ref is None:
        return None
    path = protected_file(ref["path"], repo_root())
    require(file_digest(path) == ref["digest"], "integration config changed; policy must not drift during a run")
    config = read_json(path)
    validate_config(config, repo_root())
    require(client_identity(config) == ref["client"], "acceptance client/config changed; re-enroll with the reviewed version")
    return config


def artifact_dir(config, st, label):
    # IDs never become paths: the directory is derived from their digest.
    path = Path(config["artifacts_dir"]) / digest([config["project_id"], st["task"]["id"]])[7:23] / (label + "-" + uuid.uuid4().hex)
    path.mkdir(parents=True, exist_ok=False)
    require(not under(path, repo_root()), "artifacts resolve inside candidate")
    return path


def harness_identity(config):
    harness = config["harness"]
    require(harness is not None, "project harness is not configured")
    root = repo_root()
    env = {key: os.environ[key] for key in sorted(BASE_ENV | set(harness["environment_keys"])) if key in os.environ}
    node = shutil.which(harness["node"], path=env.get("PATH"))
    require(node is not None, "configured Node executable not found")
    runtime = root / ".harness/runtime"
    require(runtime.is_dir(), "project-owned .harness/runtime missing; bootstrap the project first")
    files = sorted(runtime.glob("*.mjs")) + [root / harness["runner"]]
    require(all(p.is_file() and not p.is_symlink() for p in files), "invalid project runtime assets")
    version = subprocess.run([node, "--version"], env=env, capture_output=True, text=True, timeout=10)
    version_text = version.stdout.strip()
    match = re.fullmatch(r"v(\d+)\.\d+\.\d+(?:[-+].*)?", version_text)
    require(version.returncode == 0 and match is not None and int(match.group(1)) >= 22,
            "Project Harness needs Node 22+; resolved " + str(node) + " (" + (version_text or "no version") +
            "). Set harness.node to the project's absolute Node executable.")
    identity = {"manifest": file_digest(root / harness["manifest"]),
                "runner": digest([[str(p.relative_to(root)), file_digest(p)] for p in files]),
                "environment": digest(env), "node": str(Path(node).resolve()), "node_version": version.stdout.strip()}
    return identity, env, node


def receipt_issues(receipt, manifest):
    require(isinstance(receipt, dict) and receipt.get("schema_version") == 1 and receipt.get("evidence_kind") == "project-self-check", "unsupported self-check receipt")
    checks = manifest.get("checks")
    require(isinstance(checks, list) and checks and all(isinstance(c, dict) and isinstance(c.get("id"), str) and type(c.get("required")) is bool for c in checks), "nonempty explicit check bindings required")
    expected = [c["id"] for c in checks]
    require(len(set(expected)) == len(expected), "duplicate manifest checks")
    results = receipt.get("results")
    require(isinstance(results, list) and all(isinstance(r, dict) and isinstance(r.get("id"), str) for r in results), "invalid check results")
    ids = [r["id"] for r in results]
    require(len(set(ids)) == len(ids) and set(ids) == set(expected) and receipt.get("expected_checks") == expected, "self-check coverage mismatch")
    required = {c["id"] for c in checks if c["required"]}
    issues = []
    if not required:
        issues.append("no required checks")
    if receipt.get("execution_complete") is not True or receipt.get("checks_passed") is not True:
        issues.append("execution incomplete or checks failed")
    for result in results:
        if result["id"] in required and result.get("status") != "PASS":
            issues.append(result["id"] + ": required check is " + str(result.get("status")))
    for key in ("candidate", "candidate_after"):
        candidate = receipt.get(key, {})
        require(isinstance(candidate, dict), "invalid receipt " + key)
        if candidate.get("complete") is not True or candidate.get("unknowns"):
            issues.append(key + ": incomplete candidate scope")
    before = receipt.get("candidate", {}).get("content_digest")
    after = receipt.get("candidate_after", {}).get("content_digest")
    if not before or before != after:
        issues.append("candidate changed during verification")
    return issues


def run_project(argv, cwd, env, timeout):
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
    except BaseException:
        # Generated Harness runners handle SIGTERM and abort their check process groups.
        process.terminate()
        try:
            process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
        raise


def run_harness(st, runtime_root):
    config = configuration(st)
    require(config is not None, "configure verification before running the harness")
    require(st["task"]["status"] == "active", "inactive task; archive only")
    h = config["harness"]
    identity, env, node = harness_identity(config)
    before = source(st, runtime_root)
    folder = artifact_dir(config, st, "self-check")
    record = {"status": "incomplete", "source": before, "identity": identity, "history_ref": str(folder), "authority": "project_self_check"}
    st["verification"]["self_check"] = record
    try:
        run = run_project([node, str(repo_root() / h["runner"]), str(folder)], repo_root(), env, h["timeout_seconds"])
        (folder / "stdout.txt").write_bytes(run.stdout)
        (folder / "stderr.txt").write_bytes(run.stderr)
        require(len(run.stdout) <= MAX_JSON, "runner output too large")
        result = json.loads(run.stdout)
        receipt_path = Path(result["receipt"]).resolve()
        require(under(receipt_path, folder), "runner receipt must be in this attempt's artifact directory")
        receipt = read_json(receipt_path)
        issues = receipt_issues(receipt, read_json(repo_root() / h["manifest"]))
        if source(st, runtime_root) != before or harness_identity(config)[0] != identity:
            issues.append("candidate, contract, runtime or environment changed during execution")
        if run.returncode != 0:
            issues.append("runner exit " + str(run.returncode))
        record.update(status="passed" if not issues else "failed", receipt_ref=str(receipt_path),
                      receipt_digest=file_digest(receipt_path), issues=issues)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        record.update(status="incomplete", issues=[str(error)])
    write_new(folder / "verification.json", record)
    return record


def review_issues(document):
    require(isinstance(document, dict), "review verdict must be an object")
    state = document.get("state_decision") or document.get("state")
    require(state in {"DONE", "FIX", "SPEC_DRIFT", "GAMING_RISK", "NEEDS_HUMAN"}, "invalid review decision")
    require("unevaluated_reviews" in document and isinstance(document["unevaluated_reviews"], list), "explicit unevaluated_reviews array required")
    return state


def record_review(st, runtime_root, path):
    document = read_json(path)
    decision = review_issues(document)
    record = {"status": "complete" if decision == "DONE" and not document["unevaluated_reviews"] else "needs_work",
              "authority": "local_review", "report_ref": str(Path(path).resolve()), "report_digest": file_digest(path)}
    # Legacy projects keep their workflow. Enrolled projects additionally bind all local evidence.
    if configuration(st) is not None:
        current = source(st, runtime_root)
        require(document.get("input_binding") == current, "review input_binding missing or stale; capture verification status.current_source before reviewing")
        record["source"] = current
    st["verification"]["review"] = record


def local_issues(st, runtime_root, stage):
    config = configuration(st)
    if config is None:
        return []
    issues = []
    current = source(st, runtime_root)
    h = config["harness"]
    if h and stage in h["required_stages"]:
        record = st["verification"]["self_check"]
        if record.get("status") != "passed":
            issues.append("current project self-check has not passed")
        elif record.get("source") != current or record.get("identity") != harness_identity(config)[0]:
            record["status"] = "stale"
            issues.append("project self-check is stale; rerun the project harness")
        elif file_digest(record["receipt_ref"]) != record["receipt_digest"]:
            record["status"] = "stale"
            issues.append("self-check receipt changed")
    review = st["verification"]["review"]
    if stage in {"pr", "merge"} and st.get("acceptance", {}).get("evaluation_result"):
        if review.get("source") != current or not review.get("report_ref") or file_digest(review["report_ref"]) != review.get("report_digest"):
            review["status"] = "stale"
            issues.append("local review is stale or legacy; record a review for the current candidate")
    return issues


def invoke_client(config, command, *args):
    t = config["trusted"]
    # No candidate checkout/commands in the authenticated client process.
    launcher = "import runpy,sys;sys.path.insert(0,sys.argv[1]);sys.argv=sys.argv[2:];runpy.run_path(sys.argv[0],run_name='__main__')"
    run = subprocess.run([sys.executable, "-I", "-c", launcher, str(Path(t["client"]).parent), t["client"], command, *map(str, args)],
                         cwd=Path(t["client"]).parent, capture_output=True, text=True, timeout=150)
    require(run.returncode in (0, 2, 3), "acceptance client failed: " + (run.stderr.strip()[:500] or str(run.returncode)))
    return run.returncode


def prepare(st, runtime_root, request_path, contract_path, proposal_path, artifact_path):
    from compile_acceptance import validate_proposal
    config = configuration(st)
    require(config is not None and config["trusted"] is not None, "trusted acceptance is not configured")
    require(st["task"]["status"] == "active", "inactive task; archive only")
    clean_candidate(runtime_root)
    request, contract, proposal = map(read_json, (request_path, contract_path, proposal_path))
    invoke_client(config, "validate-request", request_path)
    invoke_client(config, "validate-contract", contract_path)
    current = source(st, runtime_root)
    validate_proposal(proposal, st["contract"]["done_when"], contract)
    binding = request["binding"]
    require(binding["project_id"] == config["project_id"] == contract["project_id"], "project identity mismatch")
    require(binding["task_id"] == current["task_id"] == contract["task_id"] and binding["task_revision"] == current["task_revision"] == contract["task_revision"], "task identity mismatch")
    require(binding["candidate_sha"] == current["candidate_sha"], "candidate SHA mismatch")
    require(binding["artifact_digest"] == file_digest(artifact_path), "candidate artifact digest mismatch")
    require(binding["contract_digest"] == digest(contract), "approved contract digest mismatch")
    for key in ("check_bundle_digest", "adapter_digest", "environment_digest"):
        require(binding[key] == config["trusted"][key], "operator policy mismatch: " + key)
    stage = binding["stage"]
    require(stage in config["trusted"]["required_stages"], "stage not enrolled in trusted policy")
    trusted = st["verification"]["trusted"]
    old = trusted["runs"].get(stage)
    if old and read_json(old["request_ref"])["binding"] == binding:
        require(read_json(old["request_ref"]) == request and old["source"] == current and old["artifact_ref"] == str(Path(artifact_path).resolve()), "retry must reuse the same request/key and unchanged source/artifact")
        return old
    folder = artifact_dir(config, st, "trusted-" + stage)
    record = {"status": "prepared", "authority": "not_granted", "source": current,
              "request_ref": write_new(folder / "request.json", request), "request_digest": digest(request),
              "artifact_ref": str(Path(artifact_path).resolve()),
              "contract_ref": write_new(folder / "contract.json", contract), "history_ref": str(folder),
              "required_check_ids": sorted(set(contract["required_check_ids"]) | set(config["trusted"]["baseline_check_ids"]))}
    write_new(folder / "proposal.json", proposal)
    trusted["runs"][stage] = record
    trusted["status"] = "requested"
    return record


def route(decision):
    domain, action, code_budget = ROUTES.get(decision, ROUTES["blocked"])
    return {"domain": domain, "action": action, "consumes_code_budget": code_budget}


def invalidate(record, status="blocked", decision="blocked"):
    if record.get("authority") == "control_endpoint" and record.get("decision"):
        record["last_remote_decision"] = record["decision"]
    record.update(status=status, decision=decision, authority="not_granted", route=route(decision))


def refresh(st, runtime_root, stage, submit=False):
    record = st["verification"]["trusted"]["runs"].get(stage)
    require(record is not None, "prepare a trusted request for stage " + stage)
    invalidate(record)  # failed refreshes clear both the cached green and its next-action hint
    config = configuration(st)
    require(config is not None and config["trusted"] is not None, "trusted acceptance is not configured")
    if st["task"]["status"] != "active":
        invalidate(record, "obsolete", "obsolete")
        return record
    clean_candidate(runtime_root)
    require(record["source"] == source(st, runtime_root), "trusted request is stale; freeze and prepare the current candidate")
    request = read_json(record["request_ref"])
    require(digest(request) == record["request_digest"], "stored request changed")
    require(file_digest(record["artifact_ref"]) == request["binding"]["artifact_digest"], "candidate artifact changed")
    require(digest(read_json(record["contract_ref"])) == request["binding"]["contract_digest"], "stored approved contract changed")
    output = Path(record["history_ref"]) / ("result-" + uuid.uuid4().hex + ".json")
    args = ["--request", record["request_ref"], "--config", config["trusted"]["control_config"], "--output", output]
    if not submit:
        require(record.get("run_id"), "no remote run yet; submit the persisted request")
        args += ["--run-id", record["run_id"]]
    invoke_client(config, "submit" if submit else "get-result", *args)
    result = read_json(output)
    require(result["request_digest"] == record["request_digest"] and result["binding"] == request["binding"], "remote result identity mismatch")
    require(not record.get("run_id") or record["run_id"] == result["run_id"], "idempotent request changed run_id")
    # Re-check after I/O: cancellation or candidate changes cannot make a late answer current.
    require(record["source"] == source(st, runtime_root), "candidate changed while waiting for acceptance")
    require(file_digest(record["artifact_ref"]) == request["binding"]["artifact_digest"], "artifact changed while waiting for acceptance")
    decision = result["verification_decision"]
    if decision == "accepted_for_stage":
        actual = {item["id"]: item for item in result["checks"]}
        require(set(record["required_check_ids"]) <= set(actual), "remote result is missing required checks")
        require(all(actual[key]["status"] == "pass" for key in record["required_check_ids"]), "required check did not pass")
    record.update(status="accepted" if decision == "accepted_for_stage" else "pending" if result["state"] != "complete" else "blocked",
                  decision=decision, run_id=result["run_id"], result_ref=str(output), result_digest=file_digest(output),
                  authority="control_endpoint", route=route(decision), delivery_authorization="not_granted")
    return record


def required_stage(config, target):
    stage = "acceptance" if target == "pr" else target
    if config and config["trusted"] and stage in config["trusted"]["required_stages"]:
        return stage
    return None


def guard(st, runtime_root, target, refresh_remote=True):
    """Non-waivable local integration preconditions; remote enforcement remains necessary."""
    if st["task"]["status"] != "active":
        return ["task is " + st["task"]["status"] + "; archive only"]
    try:
        config = configuration(st)
        issues = local_issues(st, runtime_root, target)
        stage = required_stage(config, target)
        if stage:
            record = refresh(st, runtime_root, stage) if refresh_remote else st["verification"]["trusted"]["runs"].get(stage, {})
            if record.get("status") != "accepted" or record.get("authority") != "control_endpoint":
                issues.append("trusted " + stage + " acceptance is " + record.get("status", "not_requested"))
        return issues
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        record = st["verification"]["trusted"]["runs"].get("acceptance" if target == "pr" else target)
        if record is not None:
            invalidate(record)
        return [str(error)]


def task_update(st, status, revision, reason):
    require(reason.strip(), "task status/revision changes require a reason")
    task = st["task"]
    require(type(revision) is int and revision >= task["revision"], "task revision cannot decrease")
    require(task["status"] == "active" or status != "active" or revision > task["revision"], "reactivation needs a new revision")
    require(status in {"active", "cancelled", "superseded"}, "invalid task status")
    if status != task["status"] or revision != task["revision"]:
        st["verification"]["review"]["status"] = "stale"
        st["verification"]["self_check"]["status"] = "stale"
        for record in st["verification"]["trusted"]["runs"].values():
            invalidate(record, "obsolete", "obsolete")
    task.update(status=status, revision=revision, reason=reason)
    return task
