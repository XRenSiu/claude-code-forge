# 分歧集 — <feature>

n: 3                       # 独立推导次数；n: 1 时写明"未做分歧检验"
round: 1                   # 第 2 轮起必填，且与 `verify_derived.py --round` 一致
consistent_decisions: <k>  # 全部版本一致的决策数（= PSL 真正约束住的）

## 分歧（每条是 G1 的一项议程）

> 以 `| D-n` 开头的行必须是 **7 格**：# · 决策点 · v1 · v2 · v3 · 各自引用 · 议程。
> 最后一格是议程，不能空、不能留 `<…>` 占位——`verify_derived.py` 逐行检这一条。

| # | 决策点 | v1 | v2 | v3 | 各自引用 | 议程（改 PSL-xxx / 请人定 / 补 Mental Model） |
|---|---|---|---|---|---|---|
| D-1 | <…> | <…> | <…> | <…> | PSL-007 / PSL-007 / PSL-012 | <…> |

## PSL 欠定（推导中出现、PSL 里找不到依据的实体或决策）

- <实体 / 决策> — 出现在 v<k>；建议：进 PSL Domain Model / 进 open_questions / 舍弃

---

## 第 2 轮起：定向重推的形态（替代上面的分歧表）

G1 以 `rule_error` 否决、PSL 改过之后，用"新 PSL + G1 逐条裁决"做 **n=1 定向重推**是合法回退——
不必重跑 N 次独立推导。这一轮的 divergence.md 换成下面的形状（上面的 D-表不适用，删掉即可）：

```markdown
n: 1
round: 2
consistent_decisions: <k>

> **未做分歧检验**。上一轮（n: 3，见 `round1/divergence.md`）的分歧已由 G1 逐条裁定；
> 本轮输入 = 新 PSL + `g1-record.md` 的裁决，n=1 定向重推。

## G1 裁决 → 落点

| # | G1 ruling | applied in | note |
|---|---|---|---|
| 1 | <G1 的哪一条裁决> | <F-nn, F-mm> | <落地时的取舍> |

## PSL 欠定（新 PSL 之后仍无依据的项）

- <…>
```

**落盘纪律（不可省）**：覆盖上一轮的四个文件之前，先把它们原样归档到 `derived/round<n-1>/`，
再写 `derived/round-diff.md`（逐决策 diff，左侧明确指向那个归档目录）。少了归档，round-diff 的
左侧第三方无法复现，"只改了裁定点"就只是一句自述（dogfood 2026-09-05，I-35 / I-44）。
