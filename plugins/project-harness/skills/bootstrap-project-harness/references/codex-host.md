# Codex host qualification

Use this when the user requests a real Codex invocation, or the installed CLI fails before skill execution. Do not recursively launch model sessions during ordinary project bootstrap.

First inspect the binary selected by PATH and its version. A desktop application and a package-manager installation can ship different CLIs while sharing user configuration and model cache. Use the requested/configured model and inspect that binary's own model catalog:

```sh
node <skill>/scripts/codex-check.mjs --binary codex --model <requested-model> --out <task>/cli-preflight.json
```

Missing metadata or incompatible catalog shape calls for updating the owning CLI installation. Keep the user's model and account; do not edit the shared cache or silently choose a different model to hide incompatibility. `compatible_metadata` only establishes catalog compatibility. A successful live request is separate evidence. Installed Homebrew packages should be upgraded with Homebrew rather than replacing their symlinks manually.

For a real workflow, use the independent project worktree and the normal configured sandbox. Give write access to the external artifact directory when needed, retain JSONL events and final output, and use the project's Node version. Preserve ordinary system TMPDIR so fixtures do not inherit a different repository or ESM/CommonJS package boundary. Authorization to run tests normally includes their documented temporary fixtures and cleanup; it does not authorize product edits, remote mutation or desktop-data deletion.

Verify `node --version` inside the actual command shell. Login-shell initialization can replace the parent process's PATH. Set the approved Node installation in each relevant tool command (or use its absolute executable); changing only the CLI launch environment does not establish the runtime used by its tools. Do not change global shell configuration for a project-local version requirement.

Grade observable operations: skill/reference usage, successful survey, planned/applicable checks, fresh receipt and final doctor recheck. Parse tool completions, including nonzero exits and retries. An explicitly invoked skill may already be injected by the host, so absence of a separate `cat SKILL.md` is not sufficient to declare failure. The current candidate and manifest must independently match the receipt. Keep failed attempts and environmental context; do not select a successful old receipt from a previous session.

Model identity, reasoning setting, binary path/version and real usage counters belong to the evaluation record. Token counts aggregate across the session; they are not billing amounts. Plugin hook warnings and shell-initialization warnings should be separated from model-request or task failures. Never widen the sandbox merely to hide harmless startup noise.

Official model/configuration references: [Models](https://learn.chatgpt.com/docs/models), [Configuration](https://learn.chatgpt.com/docs/config-file/config-reference). Local CLI help and catalog are the exact installed-version interfaces.
