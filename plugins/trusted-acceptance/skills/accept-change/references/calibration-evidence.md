# Product and calibration evidence

The portable validator consumes Project Harness product/calibration receipts. It verifies the complete launch → doctor → drive → observe → cleanup lifecycle; every expected claim has raw observations; hashes and sizes agree; baseline and recovery bind the same source; each specified fault changes source while keeping index/checker/fixture/environment fixed; and the intended business assertion, rather than a startup error, catches the fault. It recomputes the counts and score.

```sh
python3 scripts/acceptance.py validate-calibration /outside/run/calibration.json \
  --plan /reviewed/plan.json --features /reviewed/features.json
```

All three inputs are explicit. Both this output and candidate-provided artifacts are **local_advisory**, never `accepted_for_stage`. A copied JSON file cannot authenticate who ran the collector. The canonical validator lives in `scripts/verification_evidence.py`; AI-DLC ships a byte-identical copy so installations stay self-contained.

For a protected deployment, freeze the feature index, plan, observer/driver/fixture and validator in the approved check/adapter bundle. Re-run the complete qualification there, against the intended source and environment, before enabling the check. The protected qualification job must compare the returned binding to the independently measured candidate/checker/fixture/environment identities. Keep its receipt and all transitive raw artifacts as required evidence in the protected catalog; have the collector report checker qualification as a separate required check. The existing gate still checks the approved required-check set, evidence types, identities and history. This CLI does not change that policy or install an independent collector.

Route a surviving fault or invalid calibration to checker maintenance; a boot/cleanup/dependency problem to environment diagnosis; a reproducible product assertion to implementation repair. Freeze new bundle identities after checker changes. Keep unseen holdout ownership and evaluator isolation separate: a visible local fault set supplies neither.
