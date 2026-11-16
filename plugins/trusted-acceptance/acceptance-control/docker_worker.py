#!/usr/bin/env python3
"""One leased local-pilot job. Docker candidate has no host mounts or credentials.

The frozen collector runs outside the candidate container, reads product network
boundaries and writes an ATTEMPT. Candidate stdout is never accepted as a verdict.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid

from service import Control
from protocol import digest, load, require


def docker(*args):
    result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=120)
    require(result.returncode == 0, "Docker command failed: " + result.stderr[:1000])
    return result.stdout.strip()


def environment(collector, observer_image):
    version = docker('run', '--rm', '--network', 'none', '--read-only', '--cap-drop=ALL', '--entrypoint', Path(collector).name, observer_image, '--version')
    return {'docker_server': json.loads(docker('version', '--format', '{{json .Server}}')), 'collector_runtime': version, 'observer_image': observer_image, 'sandbox_profile': 'two-containers-read-only-internal-network-v1'}


def run_job(control, token, project, timeout=300):
    job = control.claim(token, project, min(3600, timeout + 30))
    if not job:
        return {"status": "idle"}
    spec, binding = job["specification"], job["request"]["binding"]
    directory = control.root / "evidence" / (job["run_id"] + "-" + str(job["fence"]))
    directory.mkdir(mode=0o700)
    network, container, observer = "acceptance-net-" + uuid.uuid4().hex, "acceptance-candidate-" + uuid.uuid4().hex, 'acceptance-observer-' + uuid.uuid4().hex
    started, process = time.monotonic(), None
    try:
        bundle = {f: hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in sorted(spec["collector_files"])}
        require(digest(bundle) == binding["check_bundle_digest"], "collector changed after registration")
        inspected = json.loads(docker("image", "inspect", spec["image"]))[0]
        require(inspected["Id"] == binding["artifact_digest"], "image content does not match artifact binding")
        require(inspected["Config"].get("Labels", {}).get("org.opencontainers.image.revision") == binding["candidate_sha"], "image build provenance does not match candidate SHA")
        require(json.loads(docker('image', 'inspect', spec['observer_image']))[0]['Id'] == spec['observer_image'], 'observer image must be pinned by content ID')
        require(digest(environment(spec['collector_argv'][0], spec['observer_image'])) == binding['environment_digest'], 'execution environment changed since registration')
        docker("network", "create", "--internal", network)
        argv = ["run", "--detach", "--name", container, "--label", "forge.acceptance.run=" + job["run_id"],
                "--network", network, '--network-alias', 'product', "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=128",
                "--memory=2g", "--cpus=2", "--user=65534:65534", "--tmpfs", "/tmp:rw,nosuid,nodev,size=536870912,mode=1777",
                "--workdir", spec.get("candidate_workdir", "/app"),
                "--entrypoint", spec["candidate_argv"][0], spec["image"], *spec["candidate_argv"][1:]]
        docker(*argv)
        observation = json.loads(docker("inspect", container))[0]
        isolation = {"image": observation["Image"], "readonly_rootfs": observation["HostConfig"]["ReadonlyRootfs"],
            "privileged": observation["HostConfig"]["Privileged"], "cap_drop": observation["HostConfig"]["CapDrop"],
            "security_opt": observation["HostConfig"]["SecurityOpt"], "user": observation["Config"]["User"],
            "binds": observation["HostConfig"]["Binds"], "network_internal": json.loads(docker("network", "inspect", network))[0]["Internal"],
            'port_bindings': observation['HostConfig']['PortBindings'],
            "mounts": [{k: m[k] for k in ("Type", "Destination", "RW")} for m in observation["Mounts"]]}
        require(isolation["readonly_rootfs"] and not isolation["privileged"] and not isolation["binds"] and isolation["network_internal"], "candidate isolation not established")
        require(all(m["Type"] != "bind" for m in isolation["mounts"]), "host bind mount forbidden")
        require(not isolation['port_bindings'], 'candidate must not publish host ports')
        (directory / "isolation.json").write_text(json.dumps(isolation, indent=2))
        request = {**job, "product_url": "http://product:8080", "evidence_directory": '/evidence',
            "evidence_prefix": directory.name, "attempt_path": '/evidence/attempt.json', "isolation": isolation}
        (directory / "collector-request.json").write_text(json.dumps(request))
        env = {k: os.environ[k] for k in ("PATH", "HOME", "TMPDIR", "LANG", "TZ") if k in os.environ}
        observer_entry = Path(spec['collector_argv'][1]).resolve().relative_to(control.root / 'bundle').as_posix()
        docker('create', '--name', observer, '--label', 'forge.acceptance.run=' + job['run_id'], '--network', network,
            '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges', '--pids-limit=64', '--memory=256m', '--cpus=1',
            '--user', str(os.getuid()) + ':' + str(os.getgid()), '--tmpfs', '/tmp:rw,nosuid,nodev,size=16777216,mode=1777',
            '--mount', 'type=bind,src=' + str(control.root / 'bundle') + ',dst=/observer,readonly',
            '--mount', 'type=bind,src=' + str(directory) + ',dst=/evidence',
            '--env', 'ACCEPTANCE_COLLECTOR_REQUEST=/evidence/collector-request.json',
            '--entrypoint', Path(spec['collector_argv'][0]).name, spec['observer_image'], '/observer/' + observer_entry, *spec['collector_argv'][2:])
        observed = json.loads(docker('inspect', observer))[0]
        observer_record = {'image': observed['Image'], 'readonly_rootfs': observed['HostConfig']['ReadonlyRootfs'], 'user': observed['Config']['User'],
            'port_bindings': observed['HostConfig']['PortBindings'], 'mounts': [{k: m[k] for k in ('Type', 'Destination', 'RW')} for m in observed['Mounts']]}
        binds = [m for m in observer_record['mounts'] if m['Type'] == 'bind']
        require(observer_record['image'] == spec['observer_image'] and observer_record['readonly_rootfs'] and not observer_record['port_bindings'], 'observer image, rootfs or network isolation mismatch')
        require(sorted((m['Destination'], m['RW']) for m in binds) == [('/evidence', True), ('/observer', False)], 'observer must have only frozen bundle and per-attempt evidence mounts')
        isolation['observer'] = observer_record
        (directory / 'isolation.json').write_text(json.dumps(isolation, indent=2))
        (directory / 'collector-request.json').write_text(json.dumps(request))
        # Control token and database path are not passed to the collector or candidate.
        with (directory / "collector.stdout").open("wb") as stdout, (directory / "collector.stderr").open("wb") as stderr:
            process = subprocess.Popen(['docker', 'start', '--attach', observer], cwd=control.root, env=env, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True)
            while process.poll() is None:
                require(time.monotonic() - started < timeout, "collector timeout")
                require(stdout.tell() + stderr.tell() < 16 * 1024 * 1024, "collector output limit exceeded")
                with control.transaction() as db:
                    row = db.execute("SELECT status,fence FROM runs WHERE id=?", (job["run_id"],)).fetchone()
                    require(row["status"] == "running" and row["fence"] == job["fence"], "task cancelled or lease fenced")
                time.sleep(.1)
            require(process.returncode == 0, "collector failed; candidate outcome is not a pass")
        require(digest({f: hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in sorted(spec["collector_files"])}) == binding["check_bundle_digest"], "collector bundle changed during execution")
        attempt = load(directory / "attempt.json")
        for evidence in attempt["evidence"]:
            path = (control.root / "evidence" / evidence["path"]).resolve()
            require(path.is_relative_to(directory) and not path.is_symlink(), "collector evidence escapes attempt directory")
        decision = control.complete(job["run_id"], job["fence"], token, attempt, 0)  # no metered model or provider calls in this pilot
        return {"run_id": job["run_id"], "status": "complete", "evaluation": decision, "duration_seconds": time.monotonic() - started}
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        with control.transaction() as db:
            row = db.execute('SELECT status,fence FROM runs WHERE id=?', (job['run_id'],)).fetchone()
            current = row['status'] == 'running' and row['fence'] == job['fence']
        if not current:
            return {'run_id': job['run_id'], 'status': 'obsolete', 'reason': 'cancelled or fenced; late observation not published'}
        data = json.dumps({'failure_domain': 'environment', 'reason': str(error)[:2000]}).encode()
        (directory / 'worker-error.json').write_bytes(data)
        expected = set(spec['contract']['required_check_ids']) | set(spec['policy']['baseline_check_ids'])
        attempt = {'attempt_id': 'environment-error', 'sequence': 1, 'binding': binding, 'checks': [], 'evidence': [], 'findings': [], 'unverified': []}
        for number, check in enumerate(sorted(expected)):
            ref = 'environment-' + str(number)
            attempt['checks'].append({'id': check, 'status': 'error', 'failure_type': 'environment', 'requirement_ids': [c['id'] for c in spec['contract']['criteria'] if c['check_id'] == check],
                'expected': 'Independent collector completes the approved product check', 'observed': 'Candidate or collector execution failed', 'reproduction_ref': '', 'evidence_refs': [ref]})
            attempt['evidence'].append({'id': ref, 'check_id': check, 'type': 'diagnostic', 'path': directory.name + '/worker-error.json', 'digest': 'sha256:' + hashlib.sha256(data).hexdigest(), 'size_bytes': len(data)})
        decision = control.complete(job['run_id'], job['fence'], token, attempt, 0)
        return {'run_id': job['run_id'], 'status': 'complete', 'evaluation': decision}
    finally:
        if process:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        subprocess.run(["docker", "rm", "--force", "--volumes", container], capture_output=True, timeout=30)
        subprocess.run(["docker", "rm", "--force", "--volumes", observer], capture_output=True, timeout=30)
        subprocess.run(["docker", "network", "rm", network], capture_output=True, timeout=30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", required=True); parser.add_argument("--project", required=True)
    parser.add_argument("--token-file", required=True); parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    print(json.dumps(run_job(Control(args.control), Path(args.token_file).read_text().strip(), args.project, args.timeout), indent=2))
