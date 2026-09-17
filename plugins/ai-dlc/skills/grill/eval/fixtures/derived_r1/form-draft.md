# 形态草案 — memory-time-search

source_psl: PSL-memory-time-search.md
derivation_run: 1 of 3

## 实体与数据形态
- [F-01] `Era` 作为一等实体持久化，含 label / span / scenes；落位：响应顶层键 `eras[]`，每条 `Memory` 以 `era_id` 引用它 ← PSL-001, PSL-004
- [F-02] `TimeRef` 带 ambiguity 属性，不落库；落位：只出现在响应顶层键 `time_ref`，请求侧不接受它 ← PSL-003

## 界面 / 接口形态
- [F-10] `POST /search/time` 返回 `disambiguation_prompt | era_card` 两种形态 ← PSL-003, PSL-005
- [F-11] 时期卡含场景摘要与代表性 Memory ← PSL-007

## 交互与消歧
- [F-20] 重叠 ≥ 2 时展示候选，不自动选 ← PSL-003

## 明确不做
- [F-90] 不提供日历筛选器 ← PSL-001, PSL-004
