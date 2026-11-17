"""Adapters for external engines: TLC, Apalache, Quint (verify / run) and FizzBee.

fvkit closes the loop on its own; these adapters let a project keep existing .tla/.qnt/.fizz
assets. Each run stores argv, exit code, raw stdout/stderr (with digests) and the parsed
verdict. Two rules from the engines' own documentation are encoded, not left to prose:
  - `quint run` is random simulation: at best NO_VIOLATION_SAMPLED, evidence level E1;
  - `quint verify` / Apalache are bounded symbolic checks: at best BOUNDED_PASS (E2, bounded).
An engine that is missing, times out, or prints nothing recognisable is ERROR, never PASS.
"""
import re
import subprocess
import time
from pathlib import Path

from .values import FvError, require, sha_bytes

ENGINES = {
    "tlc": {"level": "E2", "default": "tlc"},
    "apalache": {"level": "E2", "default": "apalache-mc"},
    "quint-verify": {"level": "E2", "default": "quint"},
    "quint-run": {"level": "E1", "default": "quint"},
    "fizzbee": {"level": "E2", "default": "fizz"},
}
MAX_OUTPUT = 16 * 1024 * 1024


def argv_for(engine, tool, spec, config=None, invariants=(), bound=None, samples=None, seed=None, extra=()):
    require(engine in ENGINES, "unknown engine %s (choose %s)" % (engine, sorted(ENGINES)))
    tool = tool or ENGINES[engine]["default"]
    inv = list(invariants)
    if engine == "tlc":
        head = ["java", "-cp", tool, "tlc2.TLC"] if str(tool).endswith(".jar") else [tool]
        argv = head + ["-workers", "1"] + (["-config", str(config)] if config else []) + [str(spec)]
    elif engine == "apalache":
        argv = [tool, "check"] + (["--inv=" + ",".join(inv)] if inv else []) + (["--length=%d" % bound] if bound else []) + [str(spec)]
    elif engine == "quint-verify":
        argv = [tool, "verify", str(spec)] + (["--invariant=" + ",".join(inv)] if inv else []) + (["--max-steps=%d" % bound] if bound else [])
    elif engine == "quint-run":
        argv = [tool, "run", str(spec)] + (["--invariant=" + ",".join(inv)] if inv else []) + \
            (["--max-steps=%d" % bound] if bound else []) + (["--max-samples=%d" % samples] if samples else []) + \
            (["--seed=%d" % seed] if seed is not None else [])
    else:
        argv = [tool, str(spec)]
    return argv + list(extra)


def parse(engine, stdout, stderr="", exit_code=0):
    text = stdout + "\n" + stderr
    stats, violated = {}, []
    if engine == "tlc":
        m = re.search(r"(\d+) states generated, (\d+) distinct states found", text)
        if m:
            stats = {"generated": int(m.group(1)), "distinct": int(m.group(2))}
        violated = re.findall(r"Error: Invariant (\S+) is violated", text)
        if re.search(r"Error: Deadlock reached", text):
            violated.append("deadlock")
        if re.search(r"Error: Temporal properties were violated", text):
            violated.append("temporal")
        if violated:
            verdict = "FAIL"
        elif "Model checking completed. No error has been found." in text and exit_code == 0:
            verdict = "PASS"
        else:
            verdict = "ERROR"
    elif engine in ("apalache", "quint-verify"):
        if re.search(r"The outcome is: (?:Error|Deadlock)|Checker has found an error|\[violation\]", text):
            verdict = "FAIL"
        elif re.search(r"The outcome is: NoError|\[ok\] No violation found", text) and exit_code == 0:
            verdict = "BOUNDED_PASS"
        else:
            verdict = "ERROR"
    elif engine == "quint-run":
        if re.search(r"\[violation\]", text):
            verdict = "FAIL"
        elif re.search(r"\[ok\] No violation found", text) and exit_code == 0:
            verdict = "NO_VIOLATION_SAMPLED"
        else:
            verdict = "ERROR"
    elif engine == "fizzbee":
        if re.search(r"^\s*FAILED", text, re.M):
            verdict = "FAIL"
        elif re.search(r"^\s*PASSED", text, re.M) and exit_code == 0:
            verdict = "PASS"
        else:
            verdict = "ERROR"
    else:
        raise FvError("unknown engine " + engine)
    return {"verdict": verdict, "violated": violated, "stats": stats}


def run(engine, spec_files, out_dir, tool=None, config=None, invariants=(), bound=None, samples=None, seed=None,
        timeout=600, extra=()):
    from .receipt import make, now
    started = now()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=False)
    require(spec_files, "external run needs the spec file(s)")
    specs = [Path(p) for p in spec_files]
    for p in specs + ([Path(config)] if config else []):
        require(p.is_file(), "missing spec/config file: %s" % p)
    argv = argv_for(engine, tool, specs[0], config, invariants, bound, samples, seed, extra)
    tool_path = Path(tool) if tool and Path(tool).is_file() else None
    exit_code, stdout, stderr, error = None, b"", b"", None
    t0 = time.monotonic()
    try:
        proc = subprocess.run(argv, cwd=str(specs[0].parent), capture_output=True, timeout=timeout)
        exit_code, stdout, stderr = proc.returncode, proc.stdout[:MAX_OUTPUT], proc.stderr[:MAX_OUTPUT]
    except FileNotFoundError:
        error = "engine executable not found: %s" % argv[0]
    except subprocess.TimeoutExpired:
        error = "engine timed out after %ss" % timeout
    (out / "stdout.txt").write_bytes(stdout)
    (out / "stderr.txt").write_bytes(stderr)
    parsed = parse(engine, stdout.decode("utf-8", "replace"), stderr.decode("utf-8", "replace"), exit_code if exit_code is not None else -1)
    if error:
        parsed["verdict"] = "ERROR"
    result = {"exit_code": exit_code, "error": error, "millis": int((time.monotonic() - t0) * 1000),
              "stdout": {"file": "stdout.txt", "digest": sha_bytes(stdout)},
              "stderr": {"file": "stderr.txt", "digest": sha_bytes(stderr)}, "parsed": parsed}
    inputs = {"specs": [{"path": str(p), "digest": sha_bytes(p.read_bytes())} for p in specs],
              "config": {"path": str(config), "digest": sha_bytes(Path(config).read_bytes())} if config else None,
              "tool": {"path": str(tool_path), "digest": sha_bytes(tool_path.read_bytes())} if tool_path else {"command": argv[0]}}
    settings = {"engine": engine, "argv": [str(a) for a in argv], "invariants": list(invariants), "bound": bound,
                "samples": samples, "seed": seed, "timeout": timeout}
    receipt = make("external", inputs, settings, result, parsed["verdict"], ENGINES[engine]["level"], started)
    return receipt


def reparse(receipt, base_dir):
    """Re-derive the verdict from the stored raw output (when it is next to the receipt)."""
    res = receipt["result"]
    engine = receipt["settings"]["engine"]
    require(engine in ENGINES and receipt["evidence_level"] == ENGINES[engine]["level"], "external evidence level mismatch")
    if engine == "quint-run":
        require(receipt["verdict"] in ("NO_VIOLATION_SAMPLED", "FAIL", "ERROR"), "quint run is simulation; it cannot PASS")
    if engine in ("quint-verify", "apalache"):
        require(receipt["verdict"] in ("BOUNDED_PASS", "FAIL", "ERROR"), "bounded engines cannot report a complete PASS")
    if base_dir is None:
        return
    raw = {}
    for stream in ("stdout", "stderr"):
        p = Path(base_dir) / res[stream]["file"]
        require(p.is_file() and sha_bytes(p.read_bytes()) == res[stream]["digest"], "raw %s missing or changed" % stream)
        raw[stream] = p.read_bytes().decode("utf-8", "replace")
    parsed = parse(engine, raw["stdout"], raw["stderr"], res["exit_code"] if res["exit_code"] is not None else -1)
    if res.get("error"):
        parsed["verdict"] = "ERROR"
    require(parsed["verdict"] == receipt["verdict"] == res["parsed"]["verdict"], "stored engine output does not support the recorded verdict")
