# Evidence-qualified regression learning

Self-improvement must change what the next run does. `project-learn.mjs` retains reproduced counterexamples, qualifies them against the same frozen predicates, and adds them to an outside regression corpus. `project-explore.mjs` with `corpus` runs those cases before its original random budget. The original native graph remains mandatory.

This mechanism only adds action sequences to existing indexed checks. It cannot change product requirements, checker code, fixture semantics, budgets, formal contracts or publisher permissions. Use Project Harness evolve for a justified tooling/rule change and AI-DLC retro/tune for cross-task process proposals. Those changes keep their existing review and qualification path.

## Execute the loop

Use the entry's required Node version and `node_args` (for example `node --import tsx`). Keep the original failed checkout and raw artifacts. The fixed checkout must already have a passing, current full native receipt.

```sh
node scripts/project-learn.mjs collect --store /outside/learning --exploration /outside/discovery/exploration.json
node scripts/project-learn.mjs qualify --store /outside/learning --case <returned-case-id> \
  --negative-root /outside/original-failing-checkout \
  --native-receipt /outside/full-native/run-*/receipt.json --out /outside/new-qualification
node scripts/project-learn.mjs promote --store /outside/learning \
  --qualification /outside/new-qualification/qualification.json --policy /outside/operators/learning.json
```

Collection reopens the original failure, a distinct reproduction and the reduced failure, checks all raw evidence and scenario bindings, and retains source bytes. Duplicate imports do not add samples. Qualification executes positive → original failing candidate → recovery with three fresh invocations and requires the same failed predicate. An ERROR is never a detected fault. It also binds the complete native receipt, its raw files and the fixed candidate. Promotion rechecks those artifacts and the exact candidate.

An outside operator policy records previously granted, bounded authorization. Its fields do not create permission. Example for a local pilot:

```json
{"schema_version":1,"authority":"local_advisory","project_root":"/outside/fixed-checkout","store":"/outside/learning","entries":["owner-authorization-revocation/sequences"],"allowed_operations":["append-regression","rollback-regression"],"max_active_cases":20,"expires_at":1800000000,"authorization_ref":"actual user/operator grant"}
```

The policy must be outside both candidate and store, name the actual fixed checkout and store, and be unexpired. Freeze it in the automation adapter's `files` when using AI-DLC. Automatic feedback can collect, qualify and promote within this grant; no broader grant follows from it.

For the next run, put `{"corpus":"/outside/learning","seed":19,"count":4,"length":8}` in an options file and pass it to `project-explore.mjs`. Exact `replay` and `corpus` are mutually exclusive. Then record the measured result:

```sh
node scripts/project-learn.mjs observe --store /outside/learning --exploration /outside/next-run/exploration.json
node scripts/project-learn.mjs status --store /outside/learning
node scripts/project-learn.mjs rollback --store /outside/learning --case <id> \
  --policy /outside/operators/learning.json --reason 'Concrete reason for reverting this learning'
```

Missing, stale or altered active evidence blocks corpus loading. A real product failure remains FAIL and does not automatically deactivate the case. Rollback removes only the selected active case, increments the catalog revision and retains qualification, failed attempts and observations. A dead writer's lock can be reclaimed; a live writer is never displaced.

Exit codes: `0` completes a successful learning operation, `1` reports a product FAIL or unsuccessful qualification, and `2` rejects invalid inputs or evidence. In particular, `observe` returning `1` with status `FAIL` means the failure was successfully recorded; it is not a failed catalog write. Inspect the returned status and retained evidence when orchestrating these commands.

Keep qualification/native evidence for as long as a case is active. The catalog is a local regression artifact, not a protected acceptance authority or a general-purpose memory store. A single successful trial establishes detection for that defect, not lower production escape rate or autonomous model repair capability. Fresh host skill discovery still needs a real new-session test.
