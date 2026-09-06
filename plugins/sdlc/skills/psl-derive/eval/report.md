# psl-derive — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-09-05

> Author-run structural pass only (skillwise L0 linter + `bash plugins/sdlc/eval/smoke.sh`). Not a decorrelated
> two-judge read, not an L2 with/without comparison. Runtime claims are predictions.

## Verdict
- Tier-1 (structural): PASS (author-run) — no step-march, exit via `verify_derived.py`, routes by gap, high-risk fenced.
- Tier-2 (effect delta): NOT RUN → `static_only`.

## Scripts run
- `verify_derived.py` — good derived dir passes (4 files, all decisions cite existing PSL-IDs, dos-proposal passes verify_dos.py, no invented entities, divergence n:3 with agenda); bad dir rejected on 4 independent breaches (decision without ref, fake PSL-099, Step 1 in workflow, invented DateFilterCard)

## Fix list
- L2: run N=3 isolated derivations on one real PSL and hold a real G1 — measure whether the divergence set actually surfaces the PSL's underdetermined slots
- DOS proposal ↔ dos-extract actual ontology reconciliation is still manual (G1 record); a reconcile skill is a registered blank

## 2026-09-06 · dogfood 修复轮（I-19 / I-20 / I-06 / I-21 / I-32 / I-35 / I-36 / I-44 / I-48 / I-56 / I-58 / I-77）

仍是 `static_only`：新增的保证全在 L0 机械层，行为层（一次真实 N=3 推导 + 一次真人 G1）还没跑。

- 引用锚扩到 `UI-n` / `A-n` / `DP-n`，且逐个核存在性——三层同样承重，只认 PSL-NNN 会逼出装饰性引用。
- 「未被引用的规律」flag 分层（内容层规律缺席是正常的）并点名 G1 议程。
- 引用块剥离收回到开篇前言。上一轮为跳过模板引导语剥了全文，于是整篇 `> Step 1:` 零命中通过，
  本 skill 唯一"写 Σ/φ 不写流程"的机械执行被致盲——这是相对 origin/main 引入的回归，现已修复并有杀变异体的用例。
- `--round N`（N ≥ 2）落地定向重推的契约：上一轮归档 `round<N-1>/` · `round-diff.md` 指向该归档 ·
  `round: N` 声明 · 裁决落点表。对本次 dogfood 的真实第三轮产物跑 `--round 3`，如实报出三条 reject。
- 三条 G1 议程 flag：谓词无走查例、记录类型无落位、数据文件结构断言无行级定位符。
  这三条是启发式的——在真实 28 条决策上分别命中 5 / 1 / 2 条，其中 2 条（F-13、F-94，
  它们描述的是自己定义的产物）是误报。它们路由到人，不做判决。

冒烟：本轮 +31 条期望（单独看 196 → 225；并入已推进的基线后 246），0 失败。
27 个变异体经仓库自带的 `smoke.sh --mutate` 复核，无一存活。这个工具当场抓出本轮四条
期望是「因为别的原因才退出 1」——归档缺失时下一个检查接手、round-diff 缺失时未加保护的
read 抛异常。它们已改成断言具体的 reject 文案。
