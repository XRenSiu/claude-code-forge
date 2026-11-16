"""Durable, bounded execution of AI-DLC adapters. Not an acceptance authority.

The lifecycle remains aidlc_state.ORDER. This journal records work, never grants
gates or bypasses advance. Adapters are operator configured commands, not text
read from an issue, model response, repository hook or product observation.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time
import uuid

import verification as v

BASE_ENV = v.BASE_ENV
CYCLE = ["discover", "reproduce", "repair", "verify", "feedback"]
EXTERNAL = {"issue", "pr", "merge", "release"}
LIMIT = 2 * 1024 * 1024


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def git(repo, *args):
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=30)
    v.require(p.returncode == 0, "git failed: " + p.stderr[:1000])
    return p.stdout.strip()


def configuration(path, repo, runtime):
    path = Path(path).resolve()
    v.require(not v.under(path, repo) and not v.under(path, runtime), "automation config must be operator-owned, outside candidate and runtime")
    cfg = v.read_json(path)
    v.require(set(cfg) <= {"schema_version", "adapters", "budget", "environment_keys", "delivery", "protected_files"}, "unknown automation config field")
    v.require(cfg.get("schema_version") == 1 and isinstance(cfg.get("adapters"), dict), "invalid automation config")
    budget = cfg.get("budget", {})
    for key in ("max_attempts", "max_code_repairs", "max_environment_retries", "max_seconds", "max_same_failure"):
        v.require(type(budget.get(key)) is int and 0 < budget[key] <= 1000000, "missing or invalid budget: " + key)
    v.require(budget.get("max_cost_microunits") is None or type(budget["max_cost_microunits"]) is int and budget["max_cost_microunits"] > 0, "invalid cost ceiling")
    for name, adapter in cfg["adapters"].items():
        v.require(isinstance(adapter, dict) and set(adapter) <= {"argv", "timeout_seconds", "effect", "files", "reconcile_argv"}, "invalid adapter: " + name)
        for key in ("argv", "reconcile_argv"):
            argv = adapter.get(key)
            if key == "reconcile_argv" and argv is None:
                continue
            v.require(isinstance(argv, list) and argv and all(isinstance(x, str) and x and len(x) <= 8192 for x in argv), "adapter requires argv without shell: " + name)
        v.require(adapter.get("effect") in ("read", "candidate", "external"), "adapter effect required: " + name)
        v.require(type(adapter.get("timeout_seconds")) is int and 0 < adapter["timeout_seconds"] <= 3600, "invalid timeout")
        v.require(isinstance(adapter.get("files"), list) and adapter["files"], "pin adapter implementation files: " + name)
        for file in adapter["files"]:
            resolved = Path(file).resolve()
            v.require(not v.under(resolved, repo) and not v.under(resolved, runtime), "adapters must be outside candidate/runtime")
        pinned = {Path(f).resolve() for f in adapter['files']}
        for key in ('argv', 'reconcile_argv'):
            argv = adapter.get(key)
            if not argv: continue
            executable = Path(shutil.which(argv[0]) or argv[0]).resolve()
            v.require(executable.is_file(), 'adapter executable missing: ' + name)
            v.require(executable in pinned or len(argv) >= 2 and Path(argv[1]).is_absolute() and Path(argv[1]).resolve() in pinned,
                      'adapter entry must be a pinned operator file, not inline shell/code or an unpinned candidate script: ' + name)
    identity = {"config": v.file_digest(path), "files": {str(Path(f).resolve()): v.file_digest(f) for a in cfg["adapters"].values() for f in a["files"]},
        'executables': {str(Path(shutil.which(a[k][0]) or a[k][0]).resolve()): v.file_digest(shutil.which(a[k][0]) or a[k][0]) for a in cfg['adapters'].values() for k in ('argv', 'reconcile_argv') if a.get(k)}}
    return cfg, v.digest(identity)


def protected(repo, cfg):
    result = {}
    for name in cfg.get("protected_files", []):
        path = (Path(repo) / name).resolve()
        v.require(v.under(path, repo) and path.is_file(), "protected file missing or outside candidate: " + name)
        result[name] = v.file_digest(path)
    return result


def source(repo, runtime, slug):
    old = Path.cwd()
    try:
        os.chdir(repo)
        state = v.read_json(Path(runtime) / slug / "state.json") if (Path(runtime) / slug / "state.json").exists() else {"slug": slug, "task": {"id": slug, "revision": 1}}
        return v.source(state, runtime)
    finally:
        os.chdir(old)


@contextmanager
def lock(path):
    import fcntl
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise v.VerificationError("automation already running; use status or cancel") from None
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def execute(argv, packet, directory, repo, cfg, deadline, cancel):
    request = directory / "request.json"
    response = directory / "response.json"
    v.write_new(request, packet)
    env = {k: os.environ[k] for k in BASE_ENV | set(cfg.get("environment_keys", [])) if k in os.environ}
    env.update(AIDLC_REQUEST=str(request), AIDLC_RESPONSE=str(response), AIDLC_ATTEMPT=str(directory),
               AIDLC_ROOT=packet["runtime"], AIDLC_SLUG=packet["slug"], AIDLC_STAGE=packet["stage"])
    with (directory / "stdout.log").open("wb") as stdout, (directory / "stderr.log").open("wb") as stderr:
        p = subprocess.Popen(argv, cwd=repo, env=env, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True)
        why = None
        try:
            while p.poll() is None:
                if cancel.exists():
                    why = "cancelled"
                elif time.time() >= deadline:
                    why = "timeout"
                elif stdout.tell() + stderr.tell() > 8 * LIMIT:
                    why = "output_limit"
                if why:
                    break
                time.sleep(0.05)
        finally:
            # Kill the whole owned group, including children of an exited adapter.
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()
    if why or p.returncode != 0:
        return {"status": "error", "domain": "environment", "reason": why or "adapter exited " + str(p.returncode), "cost_microunits": None}
    v.require(response.is_file() and not response.is_symlink(), "adapter exited zero without response.json")
    result = v.read_json(response)
    v.require(set(result) <= {"schema_version", "request_digest", "status", "domain", "reason", "fingerprint", "evidence", "cost_microunits", "human_seconds", "outcome"}, "unknown adapter response field")
    v.require(result.get("schema_version") == 1 and result.get("request_digest") == v.digest(packet), "response does not bind this invocation")
    v.require(result.get("status") in ("complete", "failure", "wait", "error"), "invalid adapter status")
    v.require(result.get("domain") in ("none", "implementation", "environment", "checker", "product", "unknown"), "failure domain required")
    v.require(result.get("status") != "complete" or result.get("domain") == "none", "complete response has failure domain")
    cost = result.get("cost_microunits")
    v.require(cost is None or type(cost) is int and cost >= 0, "invalid cost")
    v.require(type(result.get("human_seconds", 0)) in (int, float) and 0 <= result.get("human_seconds", 0) <= 86400, "invalid human repair time")
    evidence = result.get("evidence")
    v.require(isinstance(evidence, list) and evidence, "adapter must retain raw evidence, including for failure")
    result["evidence"] = []
    for item in evidence:
        v.require(isinstance(item, str), "evidence must be a relative path")
        file = directory / item
        v.require(v.under(file, directory) and not file.is_symlink() and file.is_file() and 0 < file.stat().st_size <= 64 * 1024 * 1024, "invalid adapter evidence")
        result["evidence"].append({"path": str(file.resolve()), "digest": v.file_digest(file), "size_bytes": file.stat().st_size})
    return result


def state_command(repo, runtime, slug, *args):
    p = subprocess.run([sys.executable, str(Path(__file__).with_name("aidlc_state.py")), *args, "--root", str(runtime), "--slug", slug], cwd=repo, capture_output=True, text=True, timeout=1800)
    try:
        value = json.loads(p.stdout)
    except ValueError:
        value = {"output": p.stdout[-8192:], "error": p.stderr[-8192:]}
    return p.returncode == 0, value


def metrics(journal):
    attempts = journal["attempts"]
    costs = [a.get("result", {}).get("cost_microunits") for a in attempts]
    return {"attempts": len(attempts), "failed_attempts": sum(a.get("result", {}).get("status") in ("failure", "error") for a in attempts),
            "elapsed_seconds": round(time.time() - journal["started_at"], 3),
            "known_cost_microunits": sum(c for c in costs if c is not None), "total_cost_microunits": sum(costs) if all(c is not None for c in costs) else None,
            "human_seconds_reported": sum(a.get("result", {}).get("human_seconds", 0) for a in attempts),
            "delivery_authorization": "not_granted", "authority": "local_advisory"}


def run(repo, runtime, slug, config, mode="lifecycle", max_steps=100):
    repo, runtime = Path(repo).resolve(), Path(runtime).resolve()
    v.require(not v.under(runtime, repo), "automation runtime must be outside candidate")
    home = runtime / slug / "automation"
    home.mkdir(parents=True, exist_ok=True)
    path, cancel = home / "journal.json", home / "cancel"
    cfg, identity = configuration(config, repo, runtime)
    with lock(home / ".lock"):
        journal = v.read_json(path) if path.exists() else {"schema_version": 1, "mode": mode, "repo": str(repo), "slug": slug,
            "config_digest": identity, "protected": protected(repo, cfg), "started_at": time.time(), "attempts": [],
            "status": "ready", "cycle_stage": "discover", "code_repairs": 0, "environment_retries": 0}
        v.require(journal["config_digest"] == identity and journal["mode"] == mode and journal["repo"] == str(repo), "automation binding changed; start a new run, do not reset this budget")
        if journal["status"] in ("complete", "cancelled", "budget_exhausted", "needs_review"):
            return journal

        def persist(status, reason=None):
            journal["status"] = status
            journal["reason"] = reason
            journal["metrics"] = metrics(journal)
            write(path, journal)

        def advance(stage, record):
            import aidlc_state as lifecycle
            latest = v.read_json(runtime / slug / "state.json")
            if latest["stage"] != stage:
                persist("needs_review", "adapter advanced lifecycle; only the controller may advance")
                return False
            if stage == "archive":
                persist("complete")
                return False
            skips = lifecycle.effective_skips(latest)
            target = next(s for s in lifecycle.ORDER[lifecycle.ORDER.index(stage) + 1:] if s not in skips or s == "archive")
            ok, detail = state_command(repo, runtime, slug, "advance", target)
            record["advance"] = detail
            persist("ready" if ok else "waiting", None if ok else "existing lifecycle guard rejected transition to " + target)
            return ok

        for _ in range(max_steps):
            v.require(configuration(config, repo, runtime)[1] == identity, 'operator adapter or configuration changed during run')
            if cancel.exists():
                persist("cancelled", "operator cancelled")
                break
            v.require(protected(repo, cfg) == journal["protected"], "frozen contract/checker changed; open a new reviewed revision")
            budget = cfg["budget"]
            measured = metrics(journal)
            exhausted = (len(journal["attempts"]) >= budget["max_attempts"] or measured["elapsed_seconds"] >= budget["max_seconds"])
            ceiling = budget.get("max_cost_microunits")
            if ceiling and journal["attempts"] and (measured["total_cost_microunits"] is None or measured["known_cost_microunits"] >= ceiling):
                exhausted = True
            last = journal["attempts"][-1] if journal["attempts"] else None
            completed = last and last["state"] == "complete" and last.get("result", {}).get("status") == "complete"
            if exhausted and not (mode == "lifecycle" and completed and not last.get("advance", {}).get("ok")):
                persist("budget_exhausted", "task-wide attempt/time/cost budget exhausted or cost unknown")
                break
            if mode == "lifecycle":
                state = v.read_json(runtime / slug / "state.json")
                if state.get("task", {}).get("status", "active") != "active":
                    persist("cancelled", "task is cancelled or superseded")
                    break
                stage = state["stage"]
            else:
                state, stage = {}, journal["cycle_stage"]
            if completed and last["stage"] == stage:
                # An action may have succeeded while the downstream gate refused.
                # Resume that transition; never create a second issue/PR/deployment.
                v.require(last["after"] == source(repo, runtime, slug), "candidate changed after completed stage; reconcile before continuing")
                for item in last["result"]["evidence"]:
                    v.require(v.file_digest(item["path"]) == item["digest"], "completed stage evidence changed")
                if mode == 'lifecycle':
                    if not advance(stage, last):
                        break
                else:
                    target = {"discover": "feedback", "reproduce": "feedback", "repair": "verify", "verify": "feedback", "feedback": None}[stage]
                    if target is None:
                        persist('complete')
                        break
                    journal['cycle_stage'] = target
                    persist('ready')
                continue
            adapter = cfg["adapters"].get(stage)
            if not adapter:
                persist("waiting", "configure an adapter for " + stage)
                break
            if stage in EXTERNAL:
                v.require(adapter["effect"] == "external", "external stage must declare external effect")
            before = source(repo, runtime, slug)
            if stage in ("merge", "release"):
                permission = cfg.get("delivery", {}).get(stage, {})
                if not (permission.get("candidate_sha") == before["candidate_sha"] and permission.get("task_id") == slug
                        and permission.get("expires_at", 0) > time.time() and permission.get("authorization_ref")):
                    persist("waiting", "missing current, scoped " + stage + " authorization")
                    break
                # Recheck local and protected evidence immediately before external work.
                old = Path.cwd()
                try:
                    os.chdir(repo)
                    problems = v.guard(state, runtime, stage)
                finally:
                    os.chdir(old)
                if problems:
                    persist("waiting", "; ".join(problems))
                    break
            pending = journal["attempts"][-1] if journal["attempts"] and journal["attempts"][-1]["state"] == "started" else None
            if pending:
                v.require(pending["stage"] == stage and pending["source"] == before, "interrupted attempt candidate changed; manual reconciliation required")
                if adapter["effect"] == "external" and not adapter.get("reconcile_argv"):
                    persist("waiting", "external outcome unknown; read-only reconciliation adapter required")
                    break
            if stage == "repair" and not pending:
                if journal["code_repairs"] >= budget["max_code_repairs"]:
                    persist("budget_exhausted", "code repair budget exhausted")
                    break
                journal["code_repairs"] += 1
            attempt_id = str(uuid.uuid4())
            directory = home / "attempts" / attempt_id
            directory.mkdir(parents=True)
            packet = {"schema_version": 1, "attempt_id": attempt_id, "idempotency_key": pending["idempotency_key"] if pending else str(uuid.uuid4()),
                "stage": stage, "mode": mode, "slug": slug, "runtime": str(runtime), "source": before, "config_digest": identity,
                "reconcile": bool(pending and adapter["effect"] == "external"), "previous_attempt": journal["attempts"][-1] if journal["attempts"] else None}
            record = {"attempt_id": attempt_id, "idempotency_key": packet["idempotency_key"], "stage": stage, "source": before, "state": "started", "started_at": time.time(), "directory": str(directory)}
            if pending:
                pending["state"] = "interrupted"
            journal["attempts"].append(record)
            persist("running")  # durable before executing any side effect
            argv = adapter["reconcile_argv"] if packet["reconcile"] else adapter["argv"]
            try:
                result = execute(argv, packet, directory, repo, cfg, min(journal["started_at"] + budget["max_seconds"], time.time() + adapter["timeout_seconds"]), cancel)
            except (ValueError, OSError) as error:
                result = {"status": "error", "domain": "checker", "reason": str(error), "cost_microunits": None}
            record.update(result=result, ended_at=time.time())
            after = source(repo, runtime, slug)
            record["after"] = after
            if protected(repo, cfg) != journal["protected"] or (adapter["effect"] == "read" and before != after):
                record["state"] = "complete"
                persist("needs_review", "adapter changed frozen checks or read-only candidate")
                break
            if adapter["effect"] == "external" and result["status"] != "complete":
                # Keep started: even exit failure can happen AFTER an external side effect.
                persist("waiting", "external outcome unknown; reconcile before retry")
                break
            record["state"] = "complete"
            if adapter["effect"] == "external" and result["status"] == "complete" and result.get("outcome") != "confirmed":
                record["state"] = "started"
                persist("waiting", "external completion requires independently reconciled outcome=confirmed")
                break
            persist("running")  # completed output survives a crash before the transition
            if cancel.exists():
                persist("cancelled", "cancelled during adapter")
                break
            if result["status"] != "complete":
                domain = result.get("domain", "unknown")
                fingerprint = result.get("fingerprint") or v.digest({"stage": stage, "domain": domain, "reason": result.get("reason")})
                record["fingerprint"] = fingerprint
                repeated = sum(a.get("fingerprint") == fingerprint for a in journal["attempts"])
                if repeated >= budget["max_same_failure"]:
                    persist("needs_review", "same failure exhausted retry allowance")
                    break
                if result["status"] == "wait" or domain in ("checker", "product", "unknown"):
                    persist("waiting", result.get("reason", "adapter requires review"))
                    break
                if domain == "environment":
                    journal["environment_retries"] += 1
                    if journal["environment_retries"] > budget["max_environment_retries"]:
                        persist("budget_exhausted", "environment retry budget exhausted")
                        break
                elif mode == "cycle" and stage in ("discover", "verify", "reproduce"):
                    journal["cycle_stage"] = "repair" if stage == "reproduce" else "reproduce"
                else:
                    persist("waiting", "implementation failure: use the existing fail/card routing with this counterexample")
                    break
                persist("ready")
                continue
            if mode == "cycle":
                # A reproduced failure must be reported as failure/implementation.
                next_stage = {"discover": "feedback", "reproduce": "feedback", "repair": "verify", "verify": "feedback", "feedback": None}[stage]
                if next_stage is None:
                    persist("complete")
                    break
                journal["cycle_stage"] = next_stage
            else:
                if not advance(stage, record):
                    break
            persist("ready")
        return journal


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["run", "status", "cancel", "worktree"])
    p.add_argument("--root", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--repo", default=".")
    p.add_argument("--config")
    p.add_argument("--mode", choices=["lifecycle", "cycle"], default="lifecycle")
    p.add_argument("--max-steps", type=int, default=100)
    p.add_argument("--base", default="HEAD")
    p.add_argument("--path")
    a = p.parse_args()
    v.require(__import__('re').fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", a.slug), "invalid slug")
    home = Path(a.root).resolve() / a.slug / "automation"
    v.require(not v.under(home, a.repo), "automation runtime must be outside candidate")
    if a.action == "worktree":
        v.require(a.path and not Path(a.path).exists(), "worktree destination must be new")
        sha = git(a.repo, "rev-parse", a.base + "^{commit}")
        git(a.repo, "worktree", "add", "-b", "codex/" + a.slug, str(Path(a.path).resolve()), sha)
        value = {"repo": str(Path(a.path).resolve()), "base_sha": sha, "branch": "codex/" + a.slug}
        v.write_new(home / "worktree.json", value)
    elif a.action == "cancel":
        home.mkdir(parents=True, exist_ok=True)
        (home / "cancel").touch()
        value = {"cancel_requested": True}
    elif a.action == "status":
        value = v.read_json(home / "journal.json")
    else:
        v.require(a.config and 0 < a.max_steps <= 1000, "config and bounded max-steps required")
        value = run(a.repo, a.root, a.slug, a.config, a.mode, a.max_steps)
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0 if value.get("status", "complete") == "complete" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as error:
        print(json.dumps({"status": "blocked", "reason": str(error)}))
        sys.exit(2)
