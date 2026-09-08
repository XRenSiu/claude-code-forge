# G2 判据冻结记录 — sdlc-ring-audit

> 签完就锁：冻结的是判据不是测试名（C1）。人确认判据、指派 human AC 的裁决人。本记录**不签锁**——编排者在状态机到达 g2 后跑 `lock_done_when.py sign --stage g2`；本记录只裁"这份契约能不能冻"并指派 G3 裁决人。
> 注：`assets/` 下只有 `g1_record.md` / `g3_record.md`，**没有 `g2_record.md` 模板**；本记录按 g1 模板的表头形状手写（见末节摩擦 1）。

**日期**: 2026-09-05　**签字人**: g2-judge　**签字性质**: delegated_agent（authorization：仓库所有者 XRenSiu 2026-09-05 原话 "需要人审核的地方，请你弄一个子agent代替我审核一下"；允许到：裁定契约可否冻结、指派 human AC 裁决人；不含签锁）　**契约**: `plugins/sdlc/dogfood/ring-audit/done_when.yaml`　**审阅稿 sha256**: `47a0c368fe1a6b5ac93109c10d0a9d013508f0673880452d126509d0a3322354`（编排者应用下方 E-1…E-7 后重算，锁里记的是修订稿哈希，不是这个）

> 审阅者全新上下文，只读：sdlc/SKILL.md（门 γ + 判据 φ 表）、donewhen-extract/SKILL.md（三纪律 + 术语映射）、done-when-v2-schema.yaml、done_when.yaml、issue-body.md、PSL v2、derived/form-draft.md（G1 定向重推稿）、dos.yaml、验证器与 verify_commit.py 源码。未读 AUDIT.md / audit.yaml（尚不存在）。

## 机械预门

```
$ python3 ../../skills/donewhen-extract/scripts/validate_done_when_v2.py done_when.yaml --json
{"verdict": "PASS", "acceptance": 12, "mechanical": 10, "human": 2, "tests_in_manifest": 0, "rejects": [],
 "flags": ["behavior empty — fine at G2; test-suite-generator / spec-compile fill it at L5"]}   exit=0
```

PASS 是必要条件不是裁决：验证器不核对 `expect` 键是否对应任何谓词源、不核对 `observe` 的仪器能否看见 `given`、不做 REQ 之外的覆盖检查（见摩擦 2）。下面是它检不到的部分。

## 判据确认（12 条 AC）

判据：可证伪（数值 / 枚举 / exit 码）· 孪生同 observe · expect ↔ F-13 谓词或 A1–A8 · 无矛盾 · 覆盖。

| AC | 可证伪 | 孪生 | ↔ F-13 / A-n | 判 | 一句理由 |
|---|---|---|---|---|---|
| AC-001-a | ✓ exit 0 / rings 10 / 计数 0 | AC-001-b 同 observe | F-13 Ring 集合；`exit: 0` 是全部 F-13 谓词的伞 | **✗** | `parts_without_finding` 用了 G1 签字版 F-01 / F-95 明令禁止作为判定单位的词 **Finding**；按形态写出的脚本永远不会发出这个键，闸读不到 → 改 `parts_without_assessment`（E-1） |
| AC-001-b | ✓ exit 1 / ring_missing | ← AC-001-a | A6 删环变体 exit 1；F-13 "打印失败谓词名" | ✓ | 错误 token 即谓词名，可读 |
| AC-002-a | ✓ 三计数 0 | AC-002-b 同 observe | F-13 psl_ids 非空且在索引内、evidence 非空；A4 | **✗** | `dims_with_unknown_psl_id` 依赖 PSL 规律索引，但 given 没给 `psl`（F-13 的 `--psl`）；不给索引这个谓词无定义 → 补 given（E-2） |
| AC-002-b | ✓ exit 1 / psl_id_missing | ← AC-002-a | A6 变体族之一 | ✓ | given 里 "finding dimension" 顺手改 assessment（E-1 一致性，非阻塞） |
| AC-003-a | ✓ 三计数 0 | AC-003-b 同 observe | F-02 枚举、F-03 rename=false、F-13 "rename 全 false"；A3 / A4 | ✓ | 布尔 / 枚举外 / rename=true 三个谓词都能数 |
| AC-003-b | ✓ exit 1 / boolean_implemented | ← AC-003-a | A4 "不返回布尔" 的反例 | ✓ | `rename_true` 与 `implemented_outside_enum` 没有各自的变体——归到 mutation 族（E-6），不另加 AC |
| AC-004-a | ✓ 三计数 0 | AC-004-b 同 observe | F-13 每 Ring 有 missing 键、无 FILLS 边的 Gap 在 missing；F-16 提案必有 source；A5 | ✓ | orphan_gaps 是 F-13 派生谓词的直译 |
| AC-004-b | ✓ exit 1 / proposal_without_source | ← AC-004-a | F-16 | ✓ | given "source finding" 改 assessment（E-1 一致性） |
| AC-005-a | human · checklist（每项打钩 = 二元） | 不适用（human） | A3；A5 的 deletion 一句 | **✗** | 覆盖缺口：**A1**（每 Part 的 Gap 原子 / Artifact / 闸-门 / Loop）、**A2**（pr-review vs code-reviewer 的 Artifact 对照与 distinct_exits / merge_candidate 裁决）、**A5** 的 missing 行内容（来源标签 + necessity + deletion 一句）没有任何 AC 检；"真实的 deletion 测试" 里 "真实" 是形容词，checklist 项要写成可打钩的判据 → 扩 statement（E-3） |
| AC-006-a | human · checklist | 不适用 | A7；F-15 | **✗** | 覆盖缺口：PSL γ done_when 明写 "删环变体 exit 1 **有记录**"、F-14 "无变体记录的 exit 0 标 uncalibrated"、A6 "两次运行都记录在 run_evidence"——没有 AC 检这条记录；A8 的 "skill-issues.md 路径" 与 git diff 记录也落在 run_evidence（F-15）而无 AC → 扩 statement（E-4） |
| AC-007-a | ✓ 计数 0 | AC-007-b 同 observe | A8；F-93 | **✗** | **observe 错仪器**：G1 签字版 F-13 定义 `check_audit.py <audit.yaml> [--psl]`，exit 0 **当且仅当**一组只看 audit.yaml 的谓词成立；它看不见 git。让 check-audit 扫提交 = 改 G1 已签的形态。能看见 given 的现有仪器是 `verify_commit.py --range --card`（按 card forbidden_files 拒 → "whitelist overflow"）→ 换 observe（E-5） |
| AC-007-b | ✓ exit 1 | ← AC-007-a | A8 | **✗** | 同上；错误 token 应是仪器真发的 `whitelist_overflow`，不是 check-audit 不会发的 `audited_dir_touched` |

**合计：6 ✓ / 6 ✗。** 6 个 ✗ 都不需要新增 AC，改字段即可 → FREEZE_AFTER_EDITS。

**矛盾检查**：given "complete audit.yaml" 在 AC-001-a / 002-a / 003-a / 004-a 复用四次，expect 键两两不交、无相反期望；unwanted 四条 given 各异。无矛盾。
**REQ 覆盖**：REQ-001..007 各 ≥ 1 AC（验证器已确认）。**A1–A8 覆盖**：A3 / A4 / A7 ✓；A6 / A8 半覆盖（缺 "有记录"）；**A1 / A2 无 AC**；A5 的 Gap 行内容无 AC——均由 E-3 / E-4 补齐。
**DOS 依赖**：issue 声明 objects [Node, Gate, Loop, Run, Event] → dos.yaml `objects:` 有 Run / Contract / WorkUnit / Gate / Event / Node / Loop，五个都在 ✓；invariants [R008, R017] → dos.yaml rules R008（Gate 签字人为人；enforced_by user_workflow）、R017（效果声明不超证据层级；user_workflow）都在 ✓——两条都是 `user_workflow`，即本次审计 Gap 第三来源 unenforced_rule 的样本，正确。

## Human AC 裁决人（G3）

| AC | judge | 角色对不对 | G3 裁决人（本次运行） |
|---|---|---|---|
| AC-005-a | tech | ✓ deletion 测试是否真、命名贴合、Gap 原子归类都是对 skill 架构的工程判断；主读者是插件作者 | **g3-judge**（delegated_agent，同一授权原话；全新上下文，不得是实现者、不得是本 g2-judge、不得读评审提示词） |
| AC-006-a | product | ✓ 检的是报告对读者是否诚实（PSL-006 / DP-1 "诚实 > 完整"）：代签有没有伪装成人签、自证据有没有装作已校准——这是产品层承诺不是实现细节 | **g3-judge**（同上） |

本次两个角色由同一个代签 agent 承担，角色区分是名义上的；G3 记录里两行都要写 `signer_kind: delegated_agent` + 授权引用。非代签运行里 E-4 塞进 AC-006-a 的校准记录项更适合 tech，长期应拆成 AC-006-b（judge: tech）——本次不加 AC，避免重开 G2。

## 阈值溯源

| 阈值 | 来源 | 判 |
|---|---|---|
| `rings == 10` | PSL γ done_when "九环 + 脊柱全覆盖"；issue hard_constraints "恰为 10 项" | 真 |
| `dims_with_psl_id_ratio >= 1.0` | PSL γ "每维 ≥ 1 PSL-ID"（≥ 1.0 即 == 1.0，写法可接受） | 真 |
| `card_commits_touching_audited_dirs == 0` | PSL γ "被审目录在卡提交里 git diff 为空"；A8；issue success_metric | 真 |
| `mutation_kill_rate >= 0.70` | sdlc team floor 默认（done-when-v2-schema 示例同值） | **接受为地板，附条件**：注释把变体限定为 "删环 / 清空 psl_ids / 布尔化 / 去 source 四族"——这四族恰是四条 unwanted AC 自身，脚本必杀，0.70 在 4 个变体上**按构造为绿**。变体族必须是 F-13 全部谓词（≥ 10 族：双生产者、human Gate 无 signer、delegated 无 authorization_ref、script Gate 渲染为"门"、evidence kind 越界 / ref 空、unknown psl_id、rename=true、implemented 枚举外、orphan gap、missing 键缺失），才有被杀不掉的可能 → E-6 |

`threshold_source` 字段丢了 issue 原文里的 "用户原话（四问全覆盖）"；不是阈值来源，不要求补。

## 约束（forbidden_paths 冻结集）

契约列了 `tests/**, done_when.yaml, dos.yaml, .done_when.lock` + 三个被审目录。方向对：被审目录进禁改集正是 PSL-003 / F-93 的机械化。两个问题：

1. **bare 文件名对本次运行不生效**。verify_commit.py 的 `glob_match` 对无 `**` 的模式做整路径 fnmatch；本次契约、dos、锁都在 `plugins/sdlc/dogfood/ring-audit/` 下，实测 `done_when.yaml` / `dos.yaml` / `.done_when.lock` 对真实路径**全部不匹配**，`tests/**` 只匹配仓库根的 tests/。验证器又硬性要求字面 `tests/**` 与 `done_when.yaml` 在列 → 两种写法并存（E-7）。done_when.yaml 本身另有锁哈希兜底；dos.yaml 与锁文件没有。
2. **G1 签字版形态没冻**。`derived/form-draft.md`（sha256 进了 g1-record）、PSL v2、g1-record.md、本记录、issue-body.md、`.sdlc/**` 都不在禁改集；卡若改形态草案，审计对着的规格就变了，这是 spec-gaming 的缝 → E-7 补入。

运行中为过门而修的 verifier bug（verify_derived.py / verify_issue.py / sdlc_state.py / g1_record.md / state.schema.json，见账本三条 deviation）**在本契约之外**：它们必须以无 `Card:` footer 的 `fix(sdlc):` 提交落地，且应在签锁之前落地——否则 AC-007-a 的回放基线与锁都混着未提交改动。当前 git status 显示这些文件在 **main** 上未提交（还夹着 humanize 插件的无关改动），先分流再签锁。

## 决定

- [ ] **FREEZE** — 按原样签
- [x] **FREEZE_AFTER_EDITS** — 编排者应用 E-1…E-7 后重跑验证器、重算 sha256、再 `lock_done_when.py sign --stage g2`；不新增 AC，无需再咨询本判
- [ ] **REJECT**

### E-1 词表（F-95：Finding 不是判定单位）

```yaml
# AC-001-a
    expect: { exit: 0, rings: 10, parts_without_assessment: 0 }
# AC-002-b
    given: { input: "audit.yaml with one assessment dimension whose psl_ids is empty" }
# AC-004-b
    given: { input: "audit.yaml with one proposal lacking a source assessment or gap id" }
```

### E-2 AC-002-a 补 PSL 索引（unknown_psl_id 的定义域）

```yaml
  - id: AC-002-a
    given: { input: "complete audit.yaml", psl: "PSL-sdlc-ring-audit index 001..017" }
```

### E-3 AC-005-a statement（补 A1 / A2 / A5；去形容词）

```yaml
  - id: AC-005-a
    req: REQ-005
    kind: human
    observe: "ui:AUDIT.md#ring-tables"
    statement: >-
      每个 Part 行给出 Gap 原子集合、独占 Artifact（或 role gate | orchestrator）、检它的 Gate（script 写"闸"、human 写"门"）与 Loop；
      needed 判定的 deletion 测试写出撤掉它后流水线会产出的具体错误产物或漏检（不接受"流程会断"一类泛语）；
      naming 判定先写来路（authored | adopted）再写贴合，misfit 时给建议名且建议名比原名更贴产物或位置并标"不重命名"；
      疑似重复的 Part 对（至少 pr-review vs code-reviewer、donewhen-extract vs acceptance-spec）带 Artifact 对照与 distinct_exits | merge_candidate | alternatives_of 裁决；
      每环表末尾的 missing 行带来源标签（lifecycle_blank | newly_identified | unenforced_rule）、necessity 与 deletion 一句
    judge: tech
    evidence: checklist
```

### E-4 AC-006-a statement（补 A6 "有记录" / uncalibrated；A8 路径与 diff 记录）

```yaml
  - id: AC-006-a
    req: REQ-006
    kind: human
    observe: "ui:AUDIT.md#run-evidence"
    statement: >-
      run_evidence 节列出 G1 / G2 / G3 的签字人、signer_kind 与授权引用，signer_kind = delegated_agent 的门不渲染为"人签"；
      列出 check-audit 对 audit.yaml 的 exit 0 与对删环变体的 exit 1 两次运行记录（缺变体记录时 exit 0 标 uncalibrated，A6 的回答如实带出该标记）；
      列出 Card-footer 提交对三个被审目录的 git diff --stat 记录（为空）与 skill-issues.md 的路径；外部证据的替代品标 substitute，不渲染为用户验证
    judge: product
    evidence: checklist
```

### E-5 AC-007-a / b 换 observe（仪器要能看见 given；F-13 的 check-audit 看不见 git）

```yaml
  - id: AC-007-a
    req: REQ-007
    kind: mechanical
    ears_type: event
    observe: "cli:verify-commit"
    given: { input: "each commit carrying a `Card: CARD-xx` footer on the feature branch, replayed as --range <sha>^..<sha> --card <its card>" }
    expect: { exit: 0, card_commits_touching_audited_dirs: 0 }
    paired_with: AC-007-b
  - id: AC-007-b
    req: REQ-007
    kind: mechanical
    ears_type: unwanted
    observe: "cli:verify-commit"
    given: { input: "a Card commit whose diff modifies a file under plugins/sdlc/skills/**" }
    expect: { exit: 1, error: whitelist_overflow }
    paired_with: AC-007-a
```

（`card_commits_touching_audited_dirs` = 回放中 exit 1 的提交数；原始 `git diff --stat` 证据按 E-4 进 run_evidence。）

### E-6 mutation 变体族（让 0.70 有被杀不掉的可能）

```yaml
  thresholds:
    rings: "== 10"
    dims_with_psl_id_ratio: ">= 1.0"
    card_commits_touching_audited_dirs: "== 0"
    mutation_kill_rate: ">= 0.70"        # /calibrate 的 mutation 镜：变体族 = F-13 全部谓词（≥ 10 族：删环 / 清空 psl_ids / unknown psl_id / evidence kind 越界或 ref 空 /
                                         # 布尔化 implemented / implemented 枚举外 / rename=true / 去 source / 双生产者非 alternatives_of / orphan gap / missing 键缺失 /
                                         # human Gate 无 signer / delegated 无 authorization_ref / script Gate 渲染为"门"），不是只取四条 unwanted AC 自身
  threshold_source: "PSL γ 约束（rings、psl_id、被审目录）+ Acceptance A6 / A8；mutation 阈值取 sdlc 默认 team floor，变体族按 F-13 谓词全集（G2 附条件接受）"
```

### E-7 forbidden_paths（保留验证器要的字面项，补对本次路径生效的写法与 G1 签字版形态）

```yaml
constraints:
  forbidden_paths:
    - tests/**
    - "**/tests/**"
    - done_when.yaml
    - "**/done_when.yaml"
    - dos.yaml
    - "**/dos.yaml"
    - .done_when.lock
    - "**/.done_when.lock"
    - plugins/sdlc/skills/**
    - plugins/sdlc/agents/**
    - plugins/sdlc/docs/**
    - plugins/sdlc/dogfood/ring-audit/PSL-sdlc-ring-audit.md
    - plugins/sdlc/dogfood/ring-audit/derived/**
    - plugins/sdlc/dogfood/ring-audit/issue-body.md
    - plugins/sdlc/dogfood/ring-audit/g1-record.md
    - plugins/sdlc/dogfood/ring-audit/g2-record.md
    - .sdlc/**
  mock_allowlist: []
```

## 与 G2 契约 / 模板的摩擦（进 skill-issues.md 候选）

1. **无 `g2_record.md` 模板**：assets/ 有 g1 / g3 记录模板，G2 这道"必过"门没有记录形状；SKILL.md 判据表也只写锁文件存在，人签的"判据对不对"没有落纸的槽。
2. **`validate_done_when_v2.py` PASS 远浅于三纪律**：不核对 `expect` 键与任何谓词源（本次 AC-001-a 用了形态禁止的词、AC-007 的 observe 看不见 given 都过了）、覆盖只到 REQ→AC 不到 PSL Acceptance / γ done_when、无矛盾扫描。I-08 已记两把尺子形状不同；G2 的裁决目前只能靠人（或代签 agent）手读。
3. **forbidden_paths 语义**：`glob_match` 对无 `/` 的模式不退回 basename 匹配（`matches_any` 会），而验证器又硬要 bare `done_when.yaml`——对任何契约不在仓库根的运行，禁改集一半是装饰。建议 `glob_match` 对无 `/` 模式加 basename 回退，或验证器接受 `**/done_when.yaml`。
4. **`lock_done_when.py sign` 只有 `--by`**：I-17 给 `sdlc_state.py gate` 加了 `--signer-kind / --authorization`，锁文件没有同款——本次锁里会写 `by: g2-judge` 而无代签标记，与 PSL-006 / SKILL.md 高危黑名单"--by 必须是人名"的字面冲突只能靠本记录与账本补。
5. **状态机落后于产物**：state.json `stage: track`、`gates.g1.verdict: reject`（第二轮 PASS 未记）、`contract: null`；issue-body.md 的 `__FORM_SHA__` 未填；分支仍是 main。`advance g2` 的前置（issue → branch → contract）全部未到，编排者要先补账再签锁。
6. **A6 记录项落到 product judge**：见 Human AC 表注；结构上应是 AC-006-b（tech），本次为不加 AC 而合并。

---

## 修订后复核（同日；契约扩至 20 AC，REQ-001..011）

**修订稿 sha256**: `cec7bdc57876278c79ebe5d37a6dccadebc585eb8942006e5487f035b0c07444`（仍不是签锁稿——见下方待应用清单）　**验证器**: `{"verdict":"PASS","acceptance":20,"mechanical":18,"human":2,"rejects":[]}` exit 0

**首轮七条编辑的应用状态**：E-1（Finding→Assessment 词表）已应用，AC-001-a 现为 `parts_without_assessment` ✓。**E-2 / E-3 / E-4 / E-5 / E-6 / E-7 均未应用**——AC-002-a 仍无 psl given、AC-005-a / AC-006-a statement 未扩、AC-007 仍 observe `cli:check-audit`、mutation 变体族仍四族、forbidden_paths 仍 bare 名。首轮的 6 ✗ 中 5 个仍 ✗，决定不变，只是清单变长。

### 新增 AC-008..011 的判据确认

新增理由（L4 两条 lint 同时成立逼出契约粒度与实现分区对齐）成立，且是本次 dogfood 的真实发现：契约层 REQ 的粒度在此之前从未被"卡装得下"约束过。接受新增 REQ；对 AC 的形状有异议。

| AC | 可证伪 | 孪生 | 来源 | 判 | 一句理由 |
|---|---|---|---|---|---|
| AC-008-a | ✓ 数值 | AC-008-b 同 observe | ARCHITECTURE §1 表 + agents + 脊柱四资产（口头） | **✗** | `parts_min: 13` 是**手数的下界**，且**数错了**：按 F-08（Part = §1 skill 列 + 人签门 + agents/*.md + 脊柱四资产 + sdlc）R0+R1+R2+spine 的推导无关子集是 14（psl · psl-derive · G1 · dos-extract · invariant-extract · issue · donewhen-extract · acceptance-spec · G2 · sdlc · graph.yaml · loops.yaml · routing.yaml · triggers.yaml）。下界 13 = 允许审计漏掉任意一个 Part 仍绿——正是"按构造为绿"的缝 |
| AC-008-b | ✓ exit 1 | ← AC-008-a | — | ✓（弱） | "把整组 parts 清空"是最钝的变体，任何脚本都杀得掉；锋利的变体是"删掉一个必需 Part"（E-8 换） |
| AC-009-a | ✓ | AC-009-b | 同上 | **✗** | `parts_min: 8` = 7 个推导无关项（test-suite-generator · spec-compile · calibrate · plan-cards · implement · commit · ratchet）**+ 1 个 agent（card-implementer）**。agent 属于哪个环是 F-08 规定要**从 graph.yaml Node.role 推出**、F-24 规定有冲突就写成 Assessment 的**审计产出**；把它数进阈值 = 契约替审计预判了答案 |
| AC-009-b | ✓ | ← | — | ✓（弱） | 同 AC-008-b |
| AC-010-a | ✓ | AC-010-b | 同上 | **✗** | `parts_min: 10` = 9 个推导无关项（acceptance-fleet · code-reviewer · qa-reviewer · pm-reviewer · spec-drift-detector · spec-gaming-detector · meta-judge · pr-review · G3）+ pr-reviewer agent；同 AC-009-a 的预判问题 |
| AC-010-b | ✓ | ← | — | ✓（弱） | 同上 |
| AC-011-a | ✓ | AC-011-b | 同上 | **✗** | `parts_min: 8` = 5 个推导无关项（pr · review-loop · release · retro · tune）+ 3 个 agent（comment-fixer · fix-verifier · review-triager）；fix-verifier 归 R5 还是 R7 恰是审计要回答的；`issue --escape` 不是第二个 Part（PSL-001 一 Part 一行，R8 出现是第二角色，写进 Assessment） |
| AC-011-b | ✓ | ← | — | ✓（弱） | 同上 |

**合计（20 AC）**：首轮 6 ✓ / 6 ✗ 中 AC-001-a 转 ✓ → 7 ✓ / 5 ✗；新增 4 ✓（弱）/ 4 ✗ → **11 ✓ / 9 ✗**。9 个 ✗ 全部改字段可修，不增 AC。

**对"要不要派生"的回答：要派生，不接受硬编码下界。** 三个理由都在上表：(1) 下界有 slack（A 组 13 < 14 已经漏了一个）；(2) 数字里埋了 agent 的环归属，那是审计的输出不是输入；(3) 数字不可复现——契约没写哪些项凑出了 13 / 8 / 10 / 8。派生的形状：每组把**推导无关的必需 Part 名单**写进 given（来源可点名：§1 skill 列 + 人签门 + 脊柱资产，`ls skills/ agents/ assets/*.yaml` 可复算），expect 检 `required_parts_missing: 0`；5 个 agent 不分组，作为全局必需项挂在 AC-001-a（环归属留给审计）。总数因此闭合：35 推导无关 + 5 agent = **40 Part**（28 skill 含 sdlc + 5 agent + 3 人签门 + 4 数据资产），AC-001-a 加 `parts_total: 40`。残余：凭空捏造一个 Part 名来凑数——契约层检不到（需要 check-audit 读仓库树），留给 AC-005-a 的 checklist 与 spec-gaming-detector，本记录如实登记。

**矛盾检查（20 AC）**：AC-008..011-a 的 given 多了 `rings` 过滤，与 AC-001..004-a 的全局 given 不同 → 不构成同 given；`parts_without_assessment: 0` 在全局与分组上同向。无矛盾。
**接口后果**：`rings` 过滤与 `required_parts` 谓词都不在 G1 签字版 F-13 的接口 `check_audit.py <audit.yaml> [--psl]` 里。它们是**同一输入（audit.yaml）上的视图与追加谓词**，不改任何已有谓词，性质与 AC-007 的"换输入"不同，可以接受——但形态草案有 sha256 在 g1-record 里，不能无声扩。要求：以 **F-13a** 追加进 form-draft.md（`[--rings R..] [--required-parts a,b,..]`；谓词 `required_parts_missing`、`parts_total`，`parts_without_assessment` 受 `--rings` 限定），由 g1-judge（delegated）在 g1-record.md 末尾追加一行变更记录并更新签字版哈希；不需要重推。

### 追加编辑（与首轮 E-2…E-7 一并应用）

#### E-8 AC-008..011 换成派生的必需名单（下界 → 名单；钝变体 → 删一项）

```yaml
  - id: AC-008-a
    req: REQ-008
    kind: mechanical
    ears_type: event
    observe: "cli:check-audit"
    given: { input: "complete audit.yaml", rings: "R0,R1,R2,spine",
             required_parts: "psl, psl-derive, human_gate.G1, dos-extract, invariant-extract, issue, donewhen-extract, acceptance-spec, human_gate.G2, sdlc, asset.graph.yaml, asset.loops.yaml, asset.routing.yaml, asset.triggers.yaml" }
    expect: { exit: 0, parts_without_assessment: 0, required_parts_missing: 0 }
    paired_with: AC-008-b
  - id: AC-008-b
    req: REQ-008
    kind: mechanical
    ears_type: unwanted
    observe: "cli:check-audit"
    given: { input: "audit.yaml with one required part of rings R0,R1,R2,spine removed", rings: "R0,R1,R2,spine" }
    expect: { exit: 1, error: required_part_missing }
    paired_with: AC-008-a
  - id: AC-009-a
    req: REQ-009
    kind: mechanical
    ears_type: event
    observe: "cli:check-audit"
    given: { input: "complete audit.yaml", rings: "R3,R4,R5",
             required_parts: "test-suite-generator, spec-compile, calibrate, plan-cards, implement, commit, ratchet" }
    expect: { exit: 0, parts_without_assessment: 0, required_parts_missing: 0 }
    paired_with: AC-009-b
  - id: AC-009-b
    req: REQ-009
    kind: mechanical
    ears_type: unwanted
    observe: "cli:check-audit"
    given: { input: "audit.yaml with one required part of rings R3,R4,R5 removed", rings: "R3,R4,R5" }
    expect: { exit: 1, error: required_part_missing }
    paired_with: AC-009-a
  - id: AC-010-a
    req: REQ-010
    kind: mechanical
    ears_type: event
    observe: "cli:check-audit"
    given: { input: "complete audit.yaml", rings: "R6",
             required_parts: "acceptance-fleet, code-reviewer, qa-reviewer, pm-reviewer, spec-drift-detector, spec-gaming-detector, meta-judge, pr-review, human_gate.G3" }
    expect: { exit: 0, parts_without_assessment: 0, required_parts_missing: 0 }
    paired_with: AC-010-b
  - id: AC-010-b
    req: REQ-010
    kind: mechanical
    ears_type: unwanted
    observe: "cli:check-audit"
    given: { input: "audit.yaml with one required part of ring R6 removed", rings: "R6" }
    expect: { exit: 1, error: required_part_missing }
    paired_with: AC-010-a
  - id: AC-011-a
    req: REQ-011
    kind: mechanical
    ears_type: event
    observe: "cli:check-audit"
    given: { input: "complete audit.yaml", rings: "R7,R8",
             required_parts: "pr, review-loop, release, retro, tune" }
    expect: { exit: 0, parts_without_assessment: 0, required_parts_missing: 0 }
    paired_with: AC-011-b
  - id: AC-011-b
    req: REQ-011
    kind: mechanical
    ears_type: unwanted
    observe: "cli:check-audit"
    given: { input: "audit.yaml with one required part of rings R7,R8 removed", rings: "R7,R8" }
    expect: { exit: 1, error: required_part_missing }
    paired_with: AC-011-a
```

#### E-9 AC-001-a 加全局闭合（总数 + 5 个 agent 不分组）

```yaml
  - id: AC-001-a
    req: REQ-001
    kind: mechanical
    ears_type: event
    observe: "cli:check-audit"
    given: { input: "complete audit.yaml", psl: "PSL-sdlc-ring-audit index 001..017",
             required_parts: "agent.card-implementer, agent.comment-fixer, agent.fix-verifier, agent.pr-reviewer, agent.review-triager" }
    expect: { exit: 0, rings: 10, parts_total: 40, parts_without_assessment: 0, required_parts_missing: 0 }
    paired_with: AC-001-b
```

#### E-10 thresholds 里的组阈值换成可复算的名单来源（替换 `parts_min_by_ring_group`）

```yaml
    parts_total: "== 40"                  # 28 skill（27 环上 + sdlc）+ 5 agent + 3 人签门 + 4 脊柱数据资产；`ls plugins/sdlc/skills plugins/sdlc/agents plugins/sdlc/skills/sdlc/assets/*.yaml` 可复算
    required_parts_by_ring_group: "R0-R2+spine: 14 names; R3-R5: 7; R6: 9; R7-R8: 5 — 名单见 AC-008..011-a given；agent 5 个不分组（环归属是审计输出，F-08 / F-24），挂 AC-001-a"
```

`threshold_source` 相应追加："required_parts 来源 ARCHITECTURE §1 表 skill 列 + 门列人签门 + 脊柱四资产 + agents/*.md 目录清单（2026-09-05 快照）"。

#### E-11 形态接口追加（不是契约文件的编辑，是签锁前置）

g1-judge（delegated）在 `derived/form-draft.md` 末尾追加 `[F-13a] check_audit.py 接口加 [--rings R0,..] [--required-parts a,b,..]；谓词加 required_parts_missing、parts_total；parts_without_assessment 受 --rings 限定 ← PSL-015, PSL-004`，在 `g1-record.md` 追加一行变更记录并更新签字版 sha256；issue-body.md 的 `__FORM_SHA__` 用更新后的值填。

### 决定（修订稿）

- [ ] **FREEZE**
- [x] **FREEZE_AFTER_EDITS** — 应用 **E-2 … E-11**（E-1 已应用）；不新增 AC；应用后重跑验证器、重算 sha256、E-11 的形态追加落地，再 `lock_done_when.py sign --stage g2`。若编排者选择保留 `parts_min` 下界而不派生，视为对本判的偏离：须在契约头注释写明四个数字各由哪些 Part 凑出并把 A 组改为 14，且在账本记 `deviation`——那样我不再阻塞，但记录在此：下界形状允许每组漏一个 Part 仍绿。
- [ ] **REJECT**

**G3 裁决人不变**：AC-005-a（tech）、AC-006-a（product）→ g3-judge（delegated_agent，同一授权）。新增 8 条全为 mechanical，不进 G3。

**新增摩擦**：7. 契约在 G2 审阅中途被改（先 12 后 20 AC）且首轮 6 条编辑只应用了 1 条——G2 记录与契约之间没有"编辑已应用"的机械核对（锁哈希只在签后起作用）；建议 g2-record 带一个 `applied_edits:` 清单，编排者签锁前逐条勾。8. L4 的 "REQ 一卡一主 + 40k" 反推契约 REQ 粒度，这条依赖在 SKILL.md Σ 表里没写（contract 行不知道 cards 行会反过来约束它）；进 skill-issues。

---

## 修订后复核（20 AC · 第二次）— 最终裁决

**复核稿 sha256**: `cbc30cc02faa07613a96223b536dbddd7c186deb66caf432b0add86260689b3d`　**验证器**: PASS · 20 AC · 18 mechanical / 2 human · 0 rejects

**E-1…E-7 逐条核实（读文件，不读汇报）**：E-1 词表——契约中已无 Finding 作判定单位 ✓；E-2 AC-002-a given 带 PSL 索引 ✓；E-3 AC-005-a statement 含 A1 四坐标 / A2 重复对裁决 / A5 missing 行 / "流程会断"排除句 ✓；E-4 AC-006-a statement 含两次运行记录与 uncalibrated / diff --stat / skill-issues.md / substitute ✓；E-5 AC-007-a/b observe `cli:verify-commit`、错误 `whitelist_overflow`，existence 加 `cli: verify-commit` ✓；E-6 变体族注释 = F-13 谓词全集，threshold_source 改 ✓；E-7 forbidden_paths 字面 + `**/` 形式 + PSL / derived/** / issue-body / g1-record / g2-record / .sdlc/** ✓。上一节"E-2…E-7 未应用"的陈述**已过时**，以本节为准。

**仓库侧摩擦 3 / 4 核实**：`verify_commit.py glob_match` 对无 `/` 模式退回 basename（实测 bare `done_when.yaml` / `dos.yaml` / `.done_when.lock` 现在命中嵌套路径），`**/tests/**` 任意深度命中 ✓；`lock_done_when.py sign` 有 `--signer-kind delegated_agent --authorization`，delegated 无 authorization 时拒绝，锁里记 signer_kind ✓。签锁时**必须**带这两个参数，否则锁读起来是人签（PSL-006）。

**AC-008..011 状态**：未变——仍是硬编码下界 `parts_min: 13 / 8 / 10 / 8`、twin 仍是"整组清空"、thresholds 仍 `parts_min_by_ring_group`。上一节的 4 ✗ 与 E-8…E-11 原样成立，理由不重复（A 组按 F-08 应为 14；agent 环归属是审计输出；数字不可复算；"清空"是最钝变体）。对编排者两问的直接回答：**要在检查时按名单派生**（given.required_parts，expect.required_parts_missing: 0），**不要 parts_min**；若坚持保留下界，则 threshold_source 必须加一行列出四个数字各由哪些 Part 凑出并把 13 改 14，且账本记 deviation——那时它是"有来源的下界"，我不阻塞但 slack 留档。

**A1–A8 覆盖（20 AC）**：A1 / A2 / A5 → AC-005-a（E-3）✓；A3 → AC-005-a + AC-003-a ✓；A4 → AC-003-a/b + AC-002-a ✓；A6 → AC-001-a/b + AC-006-a（E-4）✓；A7 → AC-006-a ✓；A8 → AC-007-a/b + AC-006-a ✓。**覆盖完整。** 新增 8 条不新增 A-n 覆盖，它们服务 L4 分卡。

**最终表**：11 ✓ / 9 ✗ → E-1…E-7 落地后 **16 ✓ / 4 ✗**（4 ✗ = AC-008-a / 009-a / 010-a / 011-a 的 parts_min）。

### 决定（最终）

- [ ] **FREEZE**
- [x] **FREEZE_AFTER_EDITS** — 只剩 **E-8 / E-9 / E-10**（契约文件）+ **E-11**（form-draft.md 追加 F-13a、g1-record.md 变更行与新签字版哈希、issue-body.md 填 `__FORM_SHA__`）。不增 AC；应用后重跑验证器、重算 sha256，无需再咨询本判。
- [ ] **REJECT**

### g2 锁应签的文件清单

编排者拟签：done_when.yaml · PSL-sdlc-ring-audit.md · derived/form-draft.md · derived/dos-proposal.yaml · g1-record.md · g2-record.md · issue-body.md。**同意，并加两项**：

1. `plugins/sdlc/dogfood/ring-audit/dos.yaml` — 它是 lint_cards 与 verify_issue 的词表闭包源，已在 forbidden_paths 里，却不在锁里；运行中改它会无声改变"名词能否解析"。
2. `plugins/sdlc/dogfood/ring-audit/invariants/sdlc-plugin.card.yaml` — state.json `world.invariants` 指向它，是世界层产物；建议签，非阻塞。

签锁顺序：E-8…E-10 → E-11（form-draft / g1-record / issue-body 改完）→ 本记录不再改 → 重算全部哈希 → `lock_done_when.py sign --stage g2 --by g2-judge --signer-kind delegated_agent --authorization "XRenSiu 2026-09-05: 需要人审核的地方，请你弄一个子agent代替我审核一下" <上述 9–10 个文件>` → `sdlc_state.py gate g2 --verdict pass --by g2-judge --signer-kind delegated_agent --authorization …`。锁签在 E-11 之前会把 `__FORM_SHA__` 占位符与旧形态哈希一起冻住。

**G3 裁决人（最终）**：AC-005-a judge tech、AC-006-a judge product → **g3-judge**（delegated_agent，同一授权；全新上下文，非实现者、非本 g2-judge）。

---

## applied_edits（签锁前核对；g2-judge 自行读文件并重算哈希）

- **applied_edits: E-1, E-2, E-3, E-4, E-5, E-6, E-7, E-8, E-9, E-10** — 全部核实落地于 `done_when.yaml` sha256 `9de4dc020760eb4b867bbf1ffc494db75aa27db79df5f9617e99eeeaa7002a48`（验证器 PASS · 20 AC · 18/2 · 0 rejects；AC-008..011-a required_parts 各 14 / 7 / 9 / 5 名，twin 为"删一个必需 Part → exit 1 required_part_missing"；AC-001-a 带 5 个 agent 与 parts_total 40；文件中已无 parts_min）。上两节"E-2…E-7 未应用"的读取是并行写入造成的旧副本（I-42），以本行为准。
- **契约文件本身：FREEZE，按该哈希原样可签。** 唯一签锁前置是 **E-11**（form-draft.md 追加 F-13a、g1-record.md 变更行与新签字版哈希、issue-body.md 填 `__FORM_SHA__`），它改的是锁清单里的其他文件，不是契约；E-11 落地后本记录不再改，再签。G3 裁决人不变：g3-judge（delegated_agent）。
- **confirm 42（签锁前最后一条）**：G1 第三轮 b 签字版 F-08（form-draft sha `746c56ef…880d`）把 human_gate 扩到 graph.yaml 全部五个 kind=human 节点（g1 / g2 / g3 / merge / harness-review，实测恰五个），Part 总数 = 28 + 5 + 5 + 4 = **42**；本记录前文的 40 按旧 F-08 计，**作废**。核实契约 sha `fb5af3f06734070c98481b27901ca895febf3ce873086dcf2d1ebdd7db0ca367`：AC-001-a `parts_total: 42`，AC-011-a required_parts 7 名（+ human_gate.merge / human_gate.harness-review），四组名单 14 + 7 + 9 + 7 + agent 5 = 42 闭合，验证器 PASS。残余（不阻塞）：F-06 / F-94 仍只许 G1 / G2 / G3 用"门"字，merge / harness-review 是 kind=human_gate 的 Part 但不是 Gate 对象，报告渲染时不得写成"门"——F-08 已把这一出入指定为两个 Part 的 Assessment，检查脚本的"无 script Gate 渲染为门"谓词管不到它，留给 AC-005-a checklist。**applied_edits 更新为 E-1…E-10 + parts_total 42，冻结稿 = `fb5af3f0…a367`。**
