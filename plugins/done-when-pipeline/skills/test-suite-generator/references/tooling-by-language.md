# Tooling by language

Concrete tool stack per target language, with the canonical install + import idiom. **Pick the row matching the project's language**; do not mix toolchains in one project unless the project is genuinely polyglot.

---

## Python

| Layer | Tool | Install | Notes |
|---|---|---|---|
| Unit + integration runner | pytest | `pip install pytest` | Default. Use `pytest-asyncio` if the codebase is async. |
| PBT | **Hypothesis** | `pip install hypothesis` | The reference implementation; everything else copies its model. |
| HTTP integration | httpx | `pip install httpx` | Sync + async; better than requests for tests. |
| Real-dependency containers | testcontainers | `pip install testcontainers` | Has modules for postgres, redis, kafka, mongodb, mysql, elasticsearch, rabbitmq, etc. |
| Mutation testing | **mutmut** | `pip install mutmut` | Fast, sensible defaults. |
| Coverage | coverage.py | `pip install coverage` | Built into pytest with `pytest-cov`. |
| LLM-judge (4-F automation, optional) | DeepEval | `pip install deepeval` | Integrates with pytest. Useful if you want to automate `judge: llm-rubric` scoring inside CI instead of running the manual fresh-Claude-session workflow. Adapt your rubric file into DeepEval's `GEval` metric form. |

**Canonical test file imports:**
```python
import pytest
from hypothesis import given, strategies as st, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
```

**Canonical `pyproject.toml` config addendum:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"

[tool.mutmut]
paths_to_mutate = "src/"
runner = "pytest -x"
```

---

## TypeScript / JavaScript

| Layer | Tool | Install | Notes |
|---|---|---|---|
| Unit + integration runner | vitest | `npm i -D vitest` | Faster than jest, ESM-native. Use jest only if the project already uses it. |
| PBT | **fast-check** | `npm i -D fast-check` | Has a `model` module for state-machine testing. |
| HTTP integration | supertest | `npm i -D supertest` | For Express/Fastify/Koa apps. |
| Real-dependency containers | testcontainers | `npm i -D testcontainers` | Same model as the Python version. |
| Mutation testing | **Stryker** | `npm i -D @stryker-mutator/core @stryker-mutator/vitest-runner` | Switch runner package if not using vitest. |
| E2E | **Playwright** | `npm i -D @playwright/test` | First choice. Cypress only if the project already uses it. |
| LLM-judge | manual fresh-Claude-session workflow (default) or OpenAI Evals / Promptfoo / homegrown wrapper around Claude API if you want CI automation | – | No packaged `fitness-judge` skill exists in this marketplace yet; the `llm-rubric` rubric files are written for the manual workflow by default. |

**Canonical test file imports:**
```typescript
import { test, expect, describe } from 'vitest';
import * as fc from 'fast-check';
import { test as e2eTest, expect as e2eExpect } from '@playwright/test';
```

**Canonical `stryker.conf.json`:**
```json
{
  "$schema": "./node_modules/@stryker-mutator/core/schema/stryker-schema.json",
  "packageManager": "npm",
  "testRunner": "vitest",
  "mutate": ["src/**/*.ts", "!src/**/*.test.ts", "!src/**/*.spec.ts"],
  "coverageAnalysis": "perTest",
  "thresholds": { "high": 80, "low": 70, "break": 70 }
}
```

The `"break": 70` is the gate: Stryker exits nonzero if kill rate drops below 70%, which is what `done_when.yaml.thresholds.mutation_kill_rate` enforces.

---

## Swift (iOS)

| Layer | Tool | Notes |
|---|---|---|
| Unit + integration runner | XCTest | Built into Xcode. |
| PBT | (no first-tier option) | SwiftCheck exists but is unmaintained. **Skip PBT for Swift projects** — document the gap in the generated test README. Emit example-based tests only. |
| Snapshot / UI | swift-snapshot-testing | If the project already uses it. |
| E2E | XCUITest | Built in. |
| Mutation | Muter | `brew install muter` if the project chooses to opt in. Not as polished as mutmut/Stryker. |

**Note in generated Swift test files:**
```swift
// NOTE: PBT skipped on this Swift target — no production-grade property-based
// testing library exists for Swift. Done_when contract treats this REQ's
// property_type:invariant as fulfilled by exhaustive example coverage of the
// boundary values listed below. Reconsider when SwiftCheck or alternatives mature.
```

---

## Kotlin / Java

| Layer | Tool | Install (Gradle) | Notes |
|---|---|---|---|
| Unit + integration runner | JUnit 5 + Kotest | `testImplementation 'org.junit.jupiter:junit-jupiter:5.10.0'` + `testImplementation 'io.kotest:kotest-runner-junit5:5.7.0'` | Kotest is the Kotlin-friendly assertion DSL. |
| PBT | jqwik | `testImplementation 'net.jqwik:jqwik:1.8.0'` | The Java/Kotlin equivalent of Hypothesis. Less polished but functional. |
| Real-dependency containers | testcontainers-java | `testImplementation 'org.testcontainers:postgresql:1.19.0'` (etc.) | Native testcontainers home. |
| Mutation testing | **PIT** | Gradle plugin: `id 'info.solidsoft.pitest' version '1.15.0'` | Mature, fast, well-integrated. |
| E2E | Playwright for Java | `testImplementation 'com.microsoft.playwright:playwright:1.40.0'` | Cross-language Playwright. |

---

## Cross-language (project-agnostic)

| Tool | Use | Install |
|---|---|---|
| ripgrep | Existence checks (4-A) | `brew install ripgrep` |
| tree-sitter | Multi-language AST queries | `brew install tree-sitter` |
| Playwright | E2E across languages (it has Python/Java/JS bindings) | `pip install playwright && playwright install` or `npm i -D @playwright/test` |

---

## Selection rules

1. If the project has a `package.json` → TypeScript stack.
2. If `pyproject.toml` / `requirements.txt` → Python stack.
3. If both (full-stack project with TS frontend + Python backend) → emit two test trees, one per language; do not try to share infrastructure.
4. If `Package.swift` → Swift stack, document PBT gap.
5. If `build.gradle*` → Kotlin/Java stack.
6. If none of the above (rare) → ask the user explicitly which stack to target; do not guess.

---

## What *not* to install

Even if these would technically help, do not introduce them — they bloat the dep tree and the source doc explicitly warns against integrating their CLIs:

- **OpenSpec CLI** — we borrow its file format (`proposal.md`/`spec.md`/`tasks.md`), not its tooling. The format is plain Markdown.
- **GitHub Spec Kit CLI** — we borrow the clarify-question style; the prompts are self-contained in this skill.
- **AWS Kiro** — borrow the EARS-to-PBT mapping idea, not the tool.
- **BMAD-METHOD** — adversarial review is already in `forge-teams`; no duplicate dependency.
