# Local Docker control pilot and deployment boundary

The reference package now includes a durable controller (`service.py`) and a Docker worker (`docker_worker.py`). It runs fixed candidate images with an independent, frozen network observer. The controller's SQLite store owns task state, cumulative usage, full attempt history, request idempotency, leases/fencing, cancellation and the current candidate. It never loads a contract, endpoint or token from the submitted candidate.

The implemented mode is `local-pilot`. Its `/runs` API returns the existing strict client protocol, but an eligible local gate is reported as **blocked for formal acceptance**, with a reason. `/runs/<id>/pilot` additionally exposes the advisory decision. This prevents testing a local service from accidentally manufacturing an `accepted_for_stage` identity. The same-user host administrator still controls Docker and the control directory; this pilot proves candidate-container separation, not protection from the host implementer.

## Provision and execute

Use a NEW directory outside any candidate checkout. `control.json` contains `schema_version:1`, `mode:local-pilot`, and principals with `id`, SHA-256 `token_sha256`, `roles` (`submit`, `cancel`, or `collect`) and allowed `projects`. Keep the raw random tokens in mode-0600 files. The candidate receives neither these tokens nor host mounts.

An operator registers `specification.json` with `service.py register --control <dir> --specification <file>`. The specification binds the exact protocol `binding`, approved-for-this-pilot `contract` and `policy`, pinned image content ID, image revision label, collector argv and every frozen collector file under `<control>/bundle`, candidate argv/workdir, expiry and cumulative budget. Adapter digest includes the Docker worker implementation; environment digest includes actual Docker server/runtime versions and sandbox profile. Changes to the bundle, environment or candidate require a new binding/revision. New revisions cannot erase attempts, reset usage or enlarge the current task budget.

```sh
python3 acceptance-control/service.py serve --control /control/owner-pilot --port 8090
python3 acceptance-control/docker_worker.py --control /control/owner-pilot --project PostHolder --token-file /control/owner-pilot/collect.token --timeout 300
```

POST `/runs` uses Bearer auth and an `Idempotency-Key` header matching the strict request. Identical retries return the same run; different content under the same key returns 409. GET `/runs/<id>` is scoped to the submitting principal/project. POST `/cancel` requires the separate cancellation role and `{project_id,task_id}`. The HTTP listener is loopback-only for the pilot. It does not relax the formal client's HTTPS requirement; a local pilot caller uses its explicit local transport.

The worker claims one durable job, inspects both pinned images, creates an internal Docker network, and starts a non-root candidate with read-only rootfs, no capabilities, no-new-privileges, CPU/memory/PID bounds and no host bind mounts. A separate observer container receives the frozen bundle as a read-only mount and only its isolated evidence directory as a writable mount. It talks to the candidate over the internal network; no product port is published on the host. The database and control credentials are mounted into neither container. The observer must independently inspect network behavior and produce a typed ATTEMPT; candidate stdout is never a verdict. Raw files are hashed and reopened by the gate. Cancellation/supersession fences late workers; cleanup removes only owned containers, anonymous volumes and networks. A killed worker's expired lease can be reclaimed within the cumulative environment retry budget.

PostHolder supplies `scripts/harness/prepare-control-pilot.py` to export a fixed Git commit, build the image, freeze its external Node observer, provision synthetic identities and enqueue the request. The dependency image is selected explicitly and resolved to a content ID. Its qualification is recorded; a cached dependency image is not claimed to prove a fresh lockfile installation. Normal full native verification remains separate evidence.

## Moving beyond this pilot

Deploy the control directory, collector identities and publisher on a machine/account the implementation agent cannot modify. Have a maintainer approve contracts, catalog, fixture and deployment policy there. Preserve the database and evidence store with appropriate access control/backups. Add HTTPS and secret management, candidate source/build provenance from a trusted builder, a protected check publisher identity and branch/release rules that require that identity. The publisher must atomically recheck task/candidate/authorization/budget before signing and before delivery; the local pilot never signs in its place.

The package deliberately does not accept an HTTP `case.json` for signing, promote arbitrary agent findings into approved checks, or create production permissions from a config flag. GitHub check publication, production promotion and unattended real-account operation require their actual deployment adapters and scoped grants. The user-authorized local Docker pilot can complete while these production capabilities remain explicitly unconfigured.
