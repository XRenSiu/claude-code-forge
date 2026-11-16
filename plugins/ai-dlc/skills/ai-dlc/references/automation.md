# Durable automation

`aidlc_state.py automation` executes approved command adapters and records every attempt outside the candidate. It uses the existing `ORDER`, sizing and `advance` guards. It does not create another lifecycle, sign G2/G3, accept its own checks, or obtain delivery permission from a successful command.

```sh
python3 scripts/aidlc_state.py automation worktree --repo /source/repo --root /control/runtime --slug fix-owner-scope --path /worktrees/fix-owner-scope --base main
python3 scripts/aidlc_state.py init --root /control/runtime --slug fix-owner-scope --title 'Restore owner revocation' --track task
python3 scripts/aidlc_state.py automation run --repo /worktrees/fix-owner-scope --root /control/runtime --slug fix-owner-scope --config /control/operators/automation.json
python3 scripts/aidlc_state.py automation status --repo /worktrees/fix-owner-scope --root /control/runtime --slug fix-owner-scope
```

Initialize from the new worktree so native repository assets and verification configuration bind the right checkout. The `worktree` command only creates a new branch/worktree and retains its base SHA; it never deletes an existing checkout. `cancel` records a durable cancellation and terminates the running adapter's owned process group. Resuming uses the same `run` command, journal, idempotency key and cumulative budget.

## Stage adapter contract

The operator config and adapter implementations must be outside candidate and runtime directories. Their hashes are frozen. No command comes from an issue body, product response, log or model-generated shell string. Commands are argv arrays executed without a shell.

| Current stage | Adapter work | Existing guard before leaving |
|---|---|---|
| intake | Capture problem, intended observable outcome, unknown decisions | Title and track |
| track | Select task/PSL and source assets | PSL G1/domain assets where required |
| issue | Create/reconcile the authorized issue and set its real identity | Issue number |
| branch | Use isolated worktree, record actual branch/base | Branch name |
| contract | Extract promises, map feature entries, freeze done-when | Contract schema and forbidden paths |
| g2 | Collect the authorized decision; absent decision returns wait | Genuine G2 record and contract lock |
| cards | Generate dependency cards, frozen checks and red baseline | L5 lock, red evidence, card lint |
| implement | Run implementation agent and relevant fast checks; update cards | Cards complete, pending work clear, calibration and lock |
| acceptance | Replay counterexamples, full Harness, calibrated product entries, configured protected submission/poll | Fleet/red-green/lock and configured current-candidate evidence |
| pr | Create/reconcile authorized PR | Real PR identity |
| review | Poll checks/reviews, classify failures and use existing fail/card loop | Verified review evidence |
| g3 | Collect the authorized merge decision | G3 and review/lock history |
| merge | Recheck fixed candidate/acceptance; merge only with scoped authorization | Reachable actual merge commit |
| release | Verify the merge candidate/dependencies; publish only with separate authorization | Release notes/tag or explicit native release policy |
| archive | Archive evidence and metrics; observe deployment and register regression/maintenance proposals | Adapter retains actual archive/feedback artifacts |

Adapters may call existing state commands to register actual outputs. They must not advance the stage, force a guard, edit a gate record directly, invent an issue number, or substitute a fixture identity for a real external action. A missing capability or decision stops at `waiting` with a reason and retained artifacts. This makes incompleteness inspectable; it is not silently converted into a completed stage.

Each adapter receives `AIDLC_REQUEST`, `AIDLC_RESPONSE`, `AIDLC_ATTEMPT`, `AIDLC_ROOT`, `AIDLC_SLUG`, `AIDLC_STAGE`. The request includes a unique invocation, stable external idempotency key, exact source/config digests and previous attempt. Write a fresh `AIDLC_RESPONSE` file:

```json
{"schema_version":1,"request_digest":"sha256:<canonical-request-digest>","status":"complete","domain":"none","evidence":["native-report.json"],"cost_microunits":null,"human_seconds":0}
```

Canonical hashing is `verification.digest(request)`. Status is `complete|failure|wait|error`; domain is `none|implementation|environment|checker|product|unknown`. Every response needs nonempty raw evidence beneath this attempt directory. Exit zero without a valid, invocation-bound response fails closed. An external completion additionally requires `outcome: confirmed`; unknown external outcomes must use an operator-configured read-only `reconcile_argv`. A completed issue/PR/deployment whose next guard fails is retained: resume retries the transition and does not repeat the action.

Example operator config (replace absolute paths with reviewed adapters):

```json
{
  "schema_version":1,
  "budget":{"max_attempts":30,"max_code_repairs":3,"max_environment_retries":2,"max_seconds":1800,"max_same_failure":3,"max_cost_microunits":null},
  "environment_keys":[],
  "protected_files":["done-when.yaml","tests/owner-scope.test.ts"],
  "adapters":{
    "implement":{"argv":["python3","/control/adapters/implement.py"],"files":["/control/adapters/implement.py"],"effect":"candidate","timeout_seconds":600},
    "acceptance":{"argv":["python3","/control/adapters/acceptance.py"],"files":["/control/adapters/acceptance.py"],"effect":"read","timeout_seconds":1200}
  },
  "delivery":{}
}
```

Declare every adapter dependency in `files`. Do not pin only a wrapper that imports mutable implementation code. `effect` is `read|candidate|external`; read adapters cannot modify candidate content. Merge/release additionally need `delivery.<stage>` with `candidate_sha`, `task_id`, future Unix `expires_at`, and an `authorization_ref` for the actual user/operator grant. Those fields record permission; they do not create it. The normal verification guard is queried again immediately before the action. A remote publisher must atomically enforce current candidate and scoped authorization itself; the local journal cannot make a network action atomic.

## Discover → reproduce → repair → verify → feedback

`automation run --mode cycle` operates a bounded defect-repair cycle, with adapters named `discover`, `reproduce`, `repair`, `verify`, `feedback` using the same contract. Discovery should call `project-impact` then `project-explore`; a failure returns its counterexample as raw evidence and a stable fingerprint. Reproduce must execute that same counterexample on a fresh instance. Only a reproduced implementation failure dispatches repair. Repair then runs the original predicates; verify must replay the counterexample and run the full native graph. Feedback writes a regression/maintenance proposal and measured costs, including unsuccessful attempts. A passing discovery skips repair; a non-reproducing failure remains visible in its earlier attempts.

This cycle is local exploration evidence and does not advance the AI-DLC lifecycle or grant acceptance. A deterministic repair adapter can validate orchestration, but does not demonstrate a model autonomously finding the repair. Production adapters can invoke the project's configured implementation agent; retain that invocation's actual output, costs, constraints and failure classification.

Budgets persist across resumes. Repeated identical failures escalate. Unknown costs stay null; when a monetary ceiling is configured, an unknown cost stops additional attempts. Environment retries do not spend code-repair allowance. Checker/product/unknown failures wait for the appropriate decision rather than editing checks until green. Metrics include all recorded attempts, elapsed time, known/unknown cost and explicitly reported human time; they are not a claim of autonomous-delivery rate or zero escaped defects.
