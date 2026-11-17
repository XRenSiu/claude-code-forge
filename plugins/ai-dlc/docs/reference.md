# 原语与资产索引

这份文档回答一个问题：**手上这件事，有没有现成的脚本；有的话它检什么、退出码什么意思。**

它存在的理由是一次机械盘点。2026-09-06 数过一遍：8 个脚本、26 个资产在当时的六份文档里一次都没出现过。
一个自称「每一步产物要么被脚本检、要么被门挡」的插件，却没有一处能查到脚本清单。
使用者只能靠读源码或猜。

`eval/smoke.sh` 有一条期望盯着这份文档。任何 `skills/*/scripts/` 下的脚本或 `skills/*/assets/` 下的资产，
如果不在这里出现，冒烟就红。文档漂移在这个插件里是可以被机器发现的事。

> 文风残余（`humanlint --genre reference`）：标题密度 23/1k、最长连续平句 5。
> 两项都是索引类文档的固有形态——正文短、表多、表格行被当成等长句子。按 humanize 的交付契约，
> 改过一轮仍 flag 就交付并列出残余，不继续磨。

## 怎么读退出码

退出码分三类。别混。

| 类别 | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| 预门（`verify_*` / `validate_*` / `lint_*`） | 过（可能带 flag） | 拒（产物不合格） | IO 或用法错误 | 不用 |
| 结构闸（`verify_structure.py`、`verify_review_complete.py`） | 全部声明的都求值且满足 | 有一条被违反 / 显式否定 | IO 或用法错误 | 声明了但无法求值，**不是通过** |
| 术语传感器（`verify_vocabulary.py`，B 档） | 计入的发现 ≤ 阈值 | 超阈值（告警，不是一票否决） | IO 或用法错误 | 没有本体 / 词表为空，**未检不是通过** |
| 状态机与生成器（`aidlc_state.py`、`tune.py`） | 命令成功 | 前置条件不满足 | 用法错误 | 不用 |

flag 不等于 reject。预门过了但带 flag，意思是「机器判不了这条，路由给人」。
把 flag 当没看见，等于把该人判的东西默认判过。

---

## 脚本

### 脊柱与状态（`skills/ai-dlc/scripts/`）

验证接线见 [verification.md](../skills/ai-dlc/references/verification.md)。`aidlc_state.py verification` 提供 configure/status/run/prepare/submit/poll/check/task，submit/poll 的退出 3 表示等待；这些结果不授予交付权限。

| 新接口 | 职责 | 退出语义 |
|---|---|---|
| `verification.py` | 状态机使用的适配模块：项目运行时、自检/评审绑定、HTTPS 客户端、阶段刷新、任务失效 | 模块，错误由 verification 子命令记录 |
| `aidlc_state.py formal` | configure（`--entrance`）/ status / generation（`--kind rules\|model`）/ calibrate / qualify / conform / check / waive：形式化证据登记在运行状态里，`advance` 每次重新校验（见下文「形式化验证」） | 0 · 1 未满足 / 负面结论 · 2 用法或证据错误 |
| `automation.py` | 持久化执行阶段适配器，复用原 `advance` 门；支持隔离 worktree、发现/复现/修复/验证/反馈 cycle、恢复、对账、取消和累计预算。见 [自动化合同](../skills/ai-dlc/references/automation.md) | 0 完成 · 1 等待/未完成/预算耗尽 · 2 配置或绑定错误 |
| `improvement.py` | 重读 automation 原始证据，按独立任务去重，将失败分流到回归、工具或合同改进提案；不自动改预算与判据 | 0 汇总完成 · 1 来源拒绝 |
| `compile_acceptance.py` | 显式映射 done_when AC/义务到可信合同提案 | 0 可送审批 · 1 有未决项 · 2 无效输入 |
| `verification-config.example.json` | 项目外的集成配置模板，默认 trusted=null | 模板本身不启用正式门禁 |

| 脚本 | 干什么 | 关键退出码 |
|---|---|---|
| `aidlc_state.py` | 生命周期状态机：`init` / `show` / `set` / `advance` / `gate` / `card` / `size` / `plan` / `doctor` / `repo` / `note` / `notes` / `autonomy` / `fail` / `escape` / `acceptance` / `waive` / `report` / `check-clean` / `graph` / `loops` / `ledger` / `archive` / `sync-install`。**状态由它拥有，不手改**。`advance` 对着文件检：`implement` 跑 `lint_cards.py`，`pr` 读 final-state.json + `meets_done_when.py` 的报告，`archive` 读 release.notes 的 post-deploy 行与指着 merge.sha 的 tag，implement / acceptance / pr / merge 重跑锁校验；implement 还要 G2 裁决（cards 被跳过时也要）、l5 锁与已核验的红基线，pr 要红→绿证据与干净的锁历史，g3 / merge 要 pr-poll 的裁决文件，release / archive 要 merge.sha 已在 branch.base 里；`advance g2` 给契约校验带上 `--repo`（forbidden_paths 要盖住这个仓库真实的测试文件）。`doctor` 还报：会话里装的插件版本 vs 这份脚本 vs marketplace 登记（读 `CLAUDE_CONFIG_DIR`，缺省 `~/.claude`），而 `sync-install` 是那条发现的**修法**：把源码这一版复制进 plugin cache 并更新 `installed_plugins.json`，默认 dry-run、`--write` 才动、写完要开新会话（skill 列表在会话启动时定型）、宿主项目级 / 用户级里与插件同名或近名的 skill / command | 0 成功 · 1 前置不满足（`doctor` 的 1 = 有 error 级发现，它从不阻断门禁）· 2 用法 |
| `lock_done_when.py` | 契约的两段锁：`sign --stage g2\|l5` 算文件哈希并记签字人；按形状认出不变量卡（有 `territory_id` + `hard_invariants`）并自己跑 `verify_card.py --ready-to-sign`，带未决项拒签，`--force-unresolved --reason` 强签时把理由与未决项清单写进锁 | 0 · 1 拒 · 2 IO |
| `trace.py` | 决策迹查询：`why <AC-id>` / `impact` / `render` / `lint` | 0 · 1 · 2 |
| `sync_issue.py` | **阶段结果回 issue，先对账再渲染**：渲染只读 `state.json` / `.done_when.lock` / `done_when.yaml` / `cards/*.yaml` / `notes.md`（与 `advance` 同一条纪律——对着文件检，不对着谁的说法检）；对账三项：issue 正文的 AC id 集合 vs 冻结契约（任一方向的差都是「两份说法」）· 正文里的哈希是不是锁里那份（按**前缀**比，`abcdef12…` 这种 8 位写法要认；同一行写明「已被 supersede」的旧值算来路不算漂移）· **被锁文件在不在版本库**（锁住了未入库文件的签名没人能核对，那是冻结机制悬空，不是文档不同步）。发帖是对外副作用，**默认不发**；`--post` 按 `slug`+`stage` 打标记，同一阶段再跑是改那条帖不是再灌一层楼 | 0 对得上 · 1 有漂移（正文照常产出）· 2 用法/IO/发帖失败 |
| `verify_graph.py` | `graph.yaml` 的五条 lint（写范围有界 / 圈必须归环 / 评估者→实现者只带 fix_prompt / 人节点有恢复绑定 / fan_in 有 merge） | 0 · 1 拒 |
| `verify_loop.py` | `loops.yaml` 的环契约（generator ≠ verifier、stop 四键齐） | 0 · 1 拒 |
| `verify_sizing.py` | 体量网格的九条 lint：阶段名在 ORDER 里 / never_skippable 覆盖三道门 / 没有一档绕过它 / 每条 skip 有 why / **兜底档一个阶段也不跳（极性）** / `needs` 与 `when` 一致 / 每一档的剩余路径 `next_allowed` 真的放行（直接 import 真的那份，不重实现）/ **`repo_assets` 的键与档位在封闭集里且每档都有一条要求** / `calibration.by_tier` 每档都有一个封闭集里的档位 | 0 · 1 拒 · 2 用法/IO（**没有 3**：网格是自带资产，读不到是错误不是「未求值」） |
| `repo_assets.py` | X1 仓库级制品在不在（候选路径序：`--scope` 的限界上下文目录（不必是代码目录，横跨多个代码目录的上下文用 `docs/ontology/<context>`；目录不存在时报 `scope 目录不存在`，因为回落到仓库根的本体看起来和「这个上下文有本体」一样）→ 仓库根 → `docs/` → `ontology/`，`.aidlc/` 最后且命中即告警）、进没进 git（`git ls-files`）。**monorepo 一个 package 一份本体**，回落让仓库级的 `agent-map.md` 与 package 级的 `dos.yaml` 共存。被 `aidlc_state.py init/doctor/repo/prereqs`、`verify_issue.py --require-dos`、`lint_cards.py --require-dos` 共用——一份候选表，不是六份 | 0 齐全且都进了 git · 1 有缺失 / 未 tracked / 位置不共享 · 2 用法/IO |

`aidlc_state.py` 的子命令里最容易被漏的五个：

- `escape --layer <card|plan|task|ontology|world> --why … --by <人>`：R12 逃逸缺陷的登记入口（不是 `fail`）。计到归因层、追加
  `escape-defects.md`、镜像进归档——`metrics.py` 只读归档，只写 issue 的逃逸在复盘里等于没发生。运行时目录已清时 `--root specs`。
- `acceptance --result final-state.json [--meets meets_done_when.yaml]`：记录整体验收；`meets_done_when` 只能从 `meets_done_when.py`
  的报告进来（报告的 `done_when_sha256` 必须等于当前契约的哈希）。

- `size`：按 `assets/sizing.yaml` 的六条规则推体量档，输入只有四个可数的量（改动文件数、AC 数、human AC 数、轨道）。
  `--commit` 才写进 state。缺省是 M，S 的豁免只认 `size_source=derived`。
- `repo --scope plugins/<pkg>`：**第一次把 /ai-dlc 带进一个仓库时先跑这条**。X1 的仓库级制品（`dos.yaml` / `decisions.md` /
  `agent-map.md` / `invariants/`）在不在、进没进 git、这一档要求到哪一级、缺了怎么补。它们是
  **一次性、仓库级、全组共用一份**的制品：做一次，之后每个 slug 由 `init` 自动发现，不必手 set 路径。
  缺席时下游是**未检**不是通过——`/issue` 的闭包会退回自评，卡的 `dos_slice` 无人解析。
  L 档与 PSL 轨 `dos.yaml` 是 required，`advance issue` 拦得住；绿地走 `--force --reason greenfield`。
- `check-clean --as-hook`：会话结束前拒绝在有待写失败报告或脏卡时收工。配 Stop hook 用，模板在
  `skills/ai-dlc/assets/hooks/`，不自动安装。

### 世界（R0，仅 PSL 轨）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `verify_psl.py` | psl | PSL 六层齐不齐、Workflow 里有没有 Step N 式步骤、验收是不是「问 X → 返回 Y」、规律有没有稳定的 PSL-NNN id | 0 · 1 拒 |
| `verify_derived.py` | psl-derive | 推导产物：每条形态决策必须引用一个 PSL-ID；N 次隔离推导的分歧集必须在 | 0 · 1 拒 |
| `grill_loop.py` | grill | 对齐环的机械部分：`pending` 从 PSL Open Questions + divergence.md 抽待定清单；`resolve --from materials`（来路必须打得开）/ `--from human --by` / `defer --why` 是槽的三条出路，`--from default` 硬拒；`check` 四键停机 | pending/resolve/defer 0 · 1 拒；check 0 converged · 10 human · 20 continue · 1 stop |

### 契约（R2）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `verify_issue.py` | issue | issue body 的预门：模糊量词无阈值拒、缺 unhappy 孪生拒、observe 写文件路径拒；`--dos` 下词表闭包失败给 `force_track: psl` | 0 · 1 拒 · 2 IO |
| `verify_done_when.py` | donewhen-extract | done_when 卡的语义出口（矛盾检 + 覆盖检） | 0 · 1 拒 |
| `validate_done_when_v2.py` | donewhen-extract | **契约 v2 的唯一校验器**，编译在 `advance g2` 里。含 `constraints.structure` 的形状检查；`constraints.test_globs` 声明这个仓库的测试放在哪（缺省只有 `tests/**`），`--repo` 下 forbidden_paths 一个真实测试文件都盖不住 = 拒，盖住一部分 = flag，不带 `--repo` 输出 `test_coverage.checked: false` | 0 · 1 拒 · 2 IO |
| `convert_v1_to_v2.py` | donewhen-extract | acceptance-spec 的 v1 契约 → v2 骨架 | 0 · 2 IO |
| `divergence.py` | donewhen-extract | **N 份隔离草案的分歧集**：按 (req, ears_type, observe) 对齐，报五类分歧，每条带要问用户的话 | 0 分歧在阈值内 · 1 必须澄清 · 2 用法 |
| `validate_done_when.py` | acceptance-spec | v1 契约的出口（历史形态） | 0 · 1 拒 |

### 本体与不变量（R1 / X1）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `verify_dos.py` | dos-extract | dos.yaml 预门：>7 对象拒、UI/impl 后缀名拒、关系引用未声明对象拒、`open_questions` 空拒 | 0 · 1 拒 |
| `inventory.py` | dos-extract | 演绎扫描：名词 / 动词频次表，给分类判断当材料。代码通道含 Vue 单文件组件的 `<script>` 块；默认跳过测试文件（`*.spec.*` / `*.test.*` / `__tests__/` 等，表头计数，`--include-tests` 计入）；ALL_CAPS 常量进剪枝组；没有提取规则的语言（`.swift` / `.svelte` / `.php`…）按扩展名报「not scanned」——没扫和扫了没有，在频次表里长得一样 | 0 |
| `count_terms.py` | dos-extract | 文档通道的机械原语：词频统计 | 0（除非文件读不了） |
| `dos_closure.py` | dos-extract | **「一个 DOS 词能不能被解析」的唯一定义**；`verify_issue.py`、`lint_cards.py`、`verify_vocabulary.py` 都 import 它 | 库，非命令行 |
| `verify_vocabulary.py` | dos-extract | **跨制品术语传感器（B 档）**：契约 / 卡 / spec / issue / PR body 的**散文**里出现、`dos.yaml` 解析不了的领域名词，每条带 file:line 与本体里最近的可解析邻居；另报本体里无人使用的词（弱证据，不计入）。`--out` 缺省**不落文件**（B 档随手跑，不该在工作区留残留），要 facts 显式给 `--out`，要机器读用 `--json` | 0 过 · 1 超阈值 · 2 IO · **3 没有本体 = 未检**（`--require-ontology` → 1） |
| `reconcile_dos.py` | dos-extract | 应然本体（psl-derive 的提案）↔ 现状本体逐条对账 | 0 · 1 有冲突 |
| `verify_agent_map.py` | dos-extract | **仓库地图的预门**：`--probe` 逐条真跑命令并比对期望退出码（期望列 `no-probe: <理由>` 的行不执行、记 flag，理由必填，全套测试不许；probe 前比对 `.nvmrc` / `.node-version` 与 `node -v`，不一致出 flag，失败条目的拒绝里写明先排除环境）；陷阱必须有来路；占位符拒；`file:` 来路要指得到文件、行号不越界、`#"原文"` 仍逐字在源文件里（引用 CLAUDE.md / rules 而不是再抄一份，源头改了这一行就红）；没锚原文的 `file:` 记 flag | 0 · 1 拒 · 2 IO |
| `agenda.py` | ratify | 冻结前的议程：从制品里读出未决项（未裁的冲突 / 没人裁过的低置信 / 未过存活测试）并带证据与写回位置；`--rule … --resolution … --by …` 写回一条裁决并盖姓名日期；拖延（待定 / TBD）、空裁决、无姓名一律拒；`--check` 只返回退出码 | 0 · 1 仍有未决 · 2 用法 |
| `verify_card.py` | invariant-extract | 不变量卡：无 provenance 拒、hard 必须 propose、◊ 混进 □ 拒；`--ready-to-sign` 是冻结前的仪式——未裁的冲突 / 没人裁过的低置信条目 / 未过存活测试的条目从「草稿的未决项」升成拒，并点名 | 0 · 1 拒 |

### 计划与实现（R4 / R5）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `lint_cards.py` | plan-cards | 卡的三项校验（REQ 全覆盖且一卡一主 / 卡间无写冲突 / **`dos_slice` 结构化字段**的名词可解析）+ 上下文 ≤ 40k；`--impl-contract`（形式化模块，`advance implement` 自动带上）：实现契约的每个操作恰好归一张卡的 `formal_ops`，卡的白名单覆盖操作的 `code.file`，任何卡都不能写实现契约。卡的**散文**（title / notes）归 `verify_vocabulary.py`，两者不重叠 | 0 · 1 拒 · 2 IO |
| `slice_agent_map.py` | plan-cards | **按卡切仓库地图**：命令全给，目录 / 禁区 / 陷阱只给与 `allowed_files` 相交的行 | 0 · 1 缺节 · 2 IO |
| `verify_commit.py` | commit | 落地前三道闸：卡白名单溢出、G2 锁哈希、secrets 与调试代码 | 0 · 1 拒 · 2 git/IO |
| `commit.sh` | commit | 过闸后提交的薄封装 | — |

### 标准与测试（R3）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `derive_counts.py` | test-suite-generator | 从契约推每层该有多少测试 | 0 |
| `gen_existence.py` | test-suite-generator | 存在性测试的生成器（**不是闸**，没有拒绝路径） | 0 |
| `check_verbatim_names.py` | test-suite-generator | 测试名与契约 manifest 逐字一致 | 0 · 1 不一致 |
| `capture_red_baseline.py` | test-suite-generator | **红基线**：实现前跑一次，记录哪些测试是红的；实现者拿它自证红→绿 | 0 · 1 基线不是红 |
| `verify_red_green.py` | test-suite-generator | **红→绿证据的另一半**：基线里每条红测试现在都必须出现且通过；**消失的红测试算不绿**（删测试是最便宜的变绿）；基线 HEAD 必须是当前 HEAD 的祖先 | 0 green · 1 not green · 2 IO · **3 unevaluated**（基线无干净检出证据 / 非祖先 / 认不出测试行）——不是通过 |
| `verify_compile.py` | spec-compile | 可判性阶梯的产物检（fitness fn / eval_case / 评判程序） | 0 · 1 拒 |
| `verification_evidence.py` | calibrate / ai-dlc | 原始产品与校准证据链、当前候选/index/checker/fixture/env 绑定；与 trusted-acceptance 副本逐字一致 | 模块；拒绝缺失、篡改或过期证据 |
| `verify_calibration.py` | calibrate | **标准的标准**：mutation score / Krippendorff α ≥ 0.80 / holdout / 隔离，四不可破 | 0 元闸过 · 1 拒 |

### 形式化验证（R3 标准 · R6 验收，`skills/formal-verify/scripts/`）

`fv.py` + `fvkit/` 与 trusted-acceptance 的副本逐字一致（smoke 盯着）。只用标准库；YAML 资产需要 PyYAML。合同 / 模型 / 轨迹 / 源码映射 / 策略的格式见 [modeling-language.md](../skills/formal-verify/references/modeling-language.md)，证据等级见 [evidence-levels.md](../skills/formal-verify/references/evidence-levels.md)。

**生成方法来自上游、原样收录**：`skills/formal-verify/upstream/`（Spec Kit、Quint LLM Kit、Specula、TLA+ AgentSkills、Formal Verification Skills、pstack、FizzBee，许可证随附），`UPSTREAM.json` 钉住仓库、提交与每个文件的 sha256。三个 agent 只做适配，`fvkit/upstream.py` 检查原文完整性与引用，`fvkit/methods.py` 把每段流程的产出变成检查。对应关系见 [upstream-methods.md](../skills/formal-verify/references/upstream-methods.md)。

| 命令 | 干什么 | 退出码 |
|---|---|---|
| `fv.py requirements-check` | **AI 抽出的需求清单**：引文必须逐字在来源里；来源里每句规范性语句（必须 / 不得 / 不会 / 最终 / must / never …，表头除外）都落到需求、假设或带引文的 out_of_scope；done_when 的每条 AC 都有去处 | 0 COMPLETE · 1 GAPS |
| `fv.py trace-rules` | 规则追溯：每条需求被形式化或有处置，每条性质引用真实需求并写 `text`，每条假设有来源，`open_questions` 为空 | 0 TRACEABLE · 1 GAPS |
| `fv.py rules-divergence` | ≥2 份隔离生成的规则候选逐需求比较：覆盖 / 种类 / 有限域语义（带见证值）/ 文本（无 domain 时交人）/ 词表 / 假设 | 0 AGREED · 1 DIVERGENT（议程） |
| `fv.py model-divergence` | ≥2 份隔离生成的模型候选在观察者层面比较：规则判定、可达观测值、可观测迁移（带见证路径）；观察不到的内部步数差别不算 | 0 AGREED · 1 DIVERGENT |
| `fv.py resolve` | 给分歧项追加裁决（人；Agent 代签须附授权原话）；只增不删 | 0 · 2 |
| `fv.py upstream verify` / `refresh` | 收录的上游原文逐字节等于 `UPSTREAM.json`、许可证在、没有清单外文件；`refresh` 只从本地克隆复制已列出的文件并重钉哈希 | 0 INTACT · 1 TAMPERED |
| `fv.py intake-check` | Spec Kit clarify + Quint Step 1 / from-requirements：10 类歧义都有状态、Partial/Missing 已问或带理由延后、≤5 个以问号结尾且由人回答的问题、系统模型 4 项有出处、每条需求有抽取行、每个操作有粒度决定 | 0 COMPLETE · 1 GAPS |
| `fv.py check-review` | FVS 审阅契约（schema 2）：7 个审阅面、F-n 发现格式、PASS / APPROVE-WITH-EDITS / REVISE / BLOCKED 规则、完成标记防截断；`--triage` 核对作者处置（延后要人裁、作者不能自裁、合同改动前后摘要与保留的被审版本）；≤3 轮 | 0 REVIEWED · 1 NOT_REVIEWED |
| `fv.py model-review-check` | Quint review 6 项结构检查（fail 拒、warn 由人决定）+ 运行时检查由检查器重算（C-init / C-step / C-step-complete / R1 / R2，审阅者说 pass 而检查器发现死动作或空洞性质即拒）+ Specula 粒度审计（每个动作一行，该拆不拆即拒） | 0 REVIEWED · 1 NOT_REVIEWED |
| `fv.py brief-check` | 入口 B 的 Specula modeling brief（第 1–7 节、Category A/B、Scenario 字段）、defect-ledger.json 与 6.2 表一致、brief coverage（每个 Scenario / 不变量 / 6.1 发现都有落点，活性要公平） | 0 COMPLETE · 1 GAPS |
| `fv.py triage-check` | Specula spec-fidelity checklist（前提 → 实现守卫 `file:line` → 模型对照，Case B / C）+ bug-classification（状态与严重度一致）；输出路由 | 0 TRIAGED · 1 NOT_TRIAGED |
| `fv.py impl-contract draft\|check` | 05 实现契约：`draft` 从 QUALIFIED 模型推导 derived（读写集、共享 / 按 key 的读改写、必须原子的动作、并发冲突、公平、每条性质 / mutant / 假设的验收义务），其余留 TODO；`check` 重新推导并核对：没被改写、引用了 QUALIFIED 回执、状态 / 观测量 / 动作全有代码对应、原子机制与证据、幂等决定、四类故障只落在模型允许的状态、验收覆盖、至少一个负对照 | 0 READY · 1 NOT_READY |
| `fv.py impl-verify` | 07 实现一致性（E3）：约束的 evidence 逐字在代码里；跑验收测试（退出 0）与负对照（必须失败）；MBT 轨迹逐步对照模型且每个操作出现过；反例重放向量有一致轨迹；全新上下文的 fv-impl-review（覆盖、模型外行为的处置、假设、分级问题、钉住被审代码字节）；回执理由由记录的各部分重新推出 | 0 IMPLEMENTS · 1 NOT_IMPLEMENTED |
| `fv.py gen-evidence rules\|model` | AI 生成的收口：上游原文 INTACT；规则要 intake、FVS 审阅（+ 处置），High 影响的性质类需求被形式化；模型要每个候选的 Step 7 handoff 与模型审阅；采纳物在被比较之列、候选仍在且未改、分歧全裁；code-first 另需 Specula brief 与现状模型的校准回执（E0 回执） | 0 READY · 1 NOT_READY |
| `fv.py lint` | 合同 / 模型静态检：词表封闭（性质只能用 observables）、表达式白名单、名字冲突、对称集不得出现字面量 | 0 · 2 |
| `fv.py check` | 显式状态模型检查（BFS 最短反例；迁移性质；可达见证；死锁；弱 / 强公平下的活性 → 套索反例；对称约简） | 0 PASS · 1 FAIL · **3 BOUNDED_PASS / INCOMPLETE**（不是通过） |
| `fv.py simulate` | 种子随机模拟，E1 | 1 FAIL · **3 NO_VIOLATION_SAMPLED**（永不 PASS） |
| `fv.py mutate` / `qualify` | 声明 mutant 必须被**预期**性质杀死；`qualify` = 完整 + 见证 + 无死动作 + 必需 mutant 全杀（FV-G1 的机器部分） | 0 QUALIFIED · 1 NOT_QUALIFIED |
| `fv.py diff-contract` | 契约弱化检测：有限域精确，否则在模型 + 自动变异上抽样（标明 sampled）；删性质 / 加假设 / 缩小 forall 都算弱化 | 0 NOT_WEAKENED · APPROVED · 1 WEAKENED · 3 UNKNOWN |
| `fv.py trace-check` / `conform` | 真实代码轨迹对模型的一致性（部分观测、隐藏步、被拒步）+ 运行时监控；`conform` 再要求源码映射 FRESH（E3） | 0 CONFORMS · 1 NONCONFORMANT · 3 INCOMPLETE |
| `fv.py source-map verify` / `sync` | 动作 ↔ 代码的逐字锚点；受保护路径自审阅提交以来变了就 STALE；`sync` 必须有审阅人与理由 | 0 FRESH · 1 STALE / BROKEN |
| `fv.py gen-tests` | 模型驱动测试向量：迁移覆盖 / 旧反例重放（被拒步写成 `enabled: false`）/ 种子随机游走 | 0 |
| `fv.py impact` / `ci` | 由 git diff 推出受影响模块；按风险分层跑完整证据，任何一步没跑都是 UNSATISFIED | 0 SATISFIED · 1 UNSATISFIED |
| `fv.py external` | TLC / Apalache / Quint verify / Quint run / FizzBee 适配，原始输出留存可重解析；`quint run` 只有 E1 | 同 check；缺引擎 = 2 |
| `fv.py validate` / `report` | 重推 verdict、重放反例与见证；`--rerun` 重新执行并逐项比对；`report` 输出可声称 / 不可声称表 | 0 · 2 |
| `fv.py init` / `vendor` | 入口 A / B 的项目骨架（能直接 qualify）；把检查器复制进项目供 CI 自包含 | 0 |
| `formal_gate.py`（`skills/ai-dlc/scripts/`） | 状态机前置：fv 合同**与需求清单**在 G2/L5 锁里；插件自带的 `upstream/UPSTREAM.json` INTACT（项目换不掉方法）；`cards` 起要规则生成 READY（intake + FVS 审阅）；`implement` 起要模型生成 READY（handoff + 模型审阅；code-first 要 brief 与校准）、QUALIFIED 与实现契约 READY（`formal impl-contract`）；E3 模块 `acceptance` 起要当前代码对当前契约 IMPLEMENTS（`formal impl-verify`）；`formal triage` 记录反例分诊与路由；E3 模块 `pr` 起要当前的 CONFORMS + FRESH 映射；策略模式按 diff 推模块；签字的 `formal waive` 降级并强制 G3 | 由 `aidlc_state.py formal` / `advance` 报告；**不可 `--force`** |

### 验收（R6）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `verify_structure.py` | qa-reviewer | **A 档的结构闸**：圈复杂度（增量与绝对值）、重复块、依赖方向，只看本次 diff | 0 过 · 1 违反 · 2 IO · **3 声明了但无法求值** |
| `next_iteration.py` | acceptance-fleet | 从上一轮 ratchet-log 推下一轮的派发参数 | 0 · 1 上一轮不自洽 |
| `qa_facts.py` | acceptance-fleet | 把 qa-reviewer 的报告投影成**测量值**，供 spec-drift 比对 | 0 · 1 不是 qa 报告 |
| `meets_done_when.py` | acceptance-fleet | **达标比对器**：契约 `behavior.thresholds` 逐条对 `qa-measurements.yaml` 里的同名测量比（`--map` 可指路）；可选核 final-state 四态；报告带契约 sha256，`aidlc_state.py acceptance --meets` 核它 | 0 met · 1 not_met · 2 IO · **3 unevaluated**（声明了阈值没人量）——不是通过 |
| `verify_review_complete.py` | acceptance-fleet | **审查完成度闸（fleet S1.5，meta-judge 之前）**：每份 fleet 产物必须自带 `review_complete:` 标记，且 `findings_count` 与实到发现条数一致；`--clear` 在重派前把陈旧产物移进 `stale/`（移不删，且只在给定目录内动手）；`--size M --size-source default\|manual` 按 L 档全集取期望——子集是豁免，豁免只认推导来的档位 | 0 全部到齐且完成 · 1 显式声明没跑完 · 2 IO / 用法 · **3 缺文件 / 解析不了 / 缺标记 / 数目不符——不是通过**（`--require-complete` 把 3 变 1） |
| `pick_evaluators.py` | acceptance-fleet | **跨供应商分配**：探测可用供应商，按同源盲区排名分配，分不到就留 `same_vendor_caveat` | 0（无论是否跨供应商）· 2 配置读不了 |
| `compute_score.py` | spec-gaming-detector | 六种 RHD 模式的 gaming_risk_score（0–10） | 0 |
| `compute_confidence.py` | meta-judge | 多源 / 跨供应商发现的置信度加权 | 0 |
| `post_review.py` | pr-review | findings.yaml → GitHub review（**永不 approve**） | 0 · 1 · 2 |

### 交付与学习（R7 / R8）

| 脚本 | 所属 skill | 干什么 | 关键退出码 |
|---|---|---|---|
| `verify_pr.py` | pr | PR body 的产物序 + 体量分级（XL 必拆）+ 锁文件改动需附提案。`--sections` 把语义槽映射到团队自己的 PR 模板标题（槽键封闭集；豁免要 why 且逐条 flag；linked_issue / verification / acceptance_mapping 只能挪不能免）；远端与 base 是解析出来的：`--remote` → 头 / base 分支的跟踪远端 → 唯一远端（多远端无跟踪 = 同步检查记跳过，不猜 origin），`--base` → `<remote>/HEAD` → main / master 中唯一存在的那个（缺省即 flag） | 0 · 1 拒 · 2 git/IO 或 `--sections` 写错 |
| `pr-poll.sh` | review-loop | 零 token 阻塞等待；预算与终止谓词编译在脚本里；`done` / `predicate` 写 `pr-watch/pr-<N>.done.json`——`advance g3 / merge` 读它，不读引擎 set 的 `review.done` | 0 收敛 · 10 终态 · 20 未收敛 · 30 预算耗尽 |
| `verify_release.py` | release | changelog ↔ tag ↔ notes 一致、回滚先于部署、验证绿才算交付。`--scheme semver`（缺省，数字段不许前导零）/ `calver`（YY[YY].MM[.N…]，按段比大小，`--bump auto` 是用法错误）/ `external`（版本、tag、changelog 归外部发布系统，列进 `unchecked` 而不是算通过；发布说明仍然要检） | 0 · 1 拒 · 2 用法 |
| `metrics.py` | retro | X3 导出：lead time / 回流分布 / G1 拦截率 / human AC 占比 / 逃逸率 / 豁免数 / **按体量分桶** | 0 |
| `tune.py` | tune | 环的参数提案（封闭 target 集）：routing 预算、指纹阈值、MAX_ROUNDS、隔离等级、**跨供应商分配**、fix_list | 0 |
| `apply_proposal.py` | tune | 把提案变成 diff / patch —— **只出 diff，从不自动应用** | 0 · 1 |

### 插件自身的评估（`eval/`）

| 脚本 | 干什么 |
|---|---|
| `eval/smoke.sh` | 全仓脚本的冒烟期望；`--only <ERE>` 过滤，`--mutate <file> <old> <new>` 做变异自检（基线必须先绿，否则拒绝出结论） |
| `eval/effect/run.py` | 行为层对照的 `prepare` / `collect`；隔离断言、副本收分、mtime 判污染 |
| `eval/effect/score.py` | 汇总；样本 < 5 或差距在噪声带内**拒绝下结论**；两个维度分开判 |
| `eval/fixtures/anchor_crosscheck.py` | 证据锚点的独立交叉核对（不共用被测实现；锁路径随 audit.yaml 走，不依赖 cwd） |
| `eval/fixtures/doc_graph_counts.py` | 活文档里手抄的「N 节点 · M 边」必须等于 `verify_graph.py` 数出来的数 |
| `eval/test_formal.py` | 形式化验证在状态机里的接线：真实 git 仓库里的抢票示例，锁 / 资格 / 一致性 / 豁免 / 策略推模块 / 路由，每条拒绝配一条放行的孪生 |

---

## 资产（数据与模板）

先是数据。脚本读它，改它就改行为。

| 资产 | 谁读 | 是什么 |
|---|---|---|
| `ai-dlc/assets/routing.yaml` | `aidlc_state.py fail` | 回流路由表：信号 → 层 → 处理者 → 动作；分层预算；收敛检测阈值；v3 加形式化反例分诊 R17–R23 |
| `formal-verify/assets/formal-verification.yml` | GitHub Actions | 每个 PR 的 `fv ci`（vendored 检查器、按策略分层、回执作为 artifact） |
| `formal-verify/assets/example-ticket/` | `eval/test_formal.py`、smoke | 抢票示例：需求清单、两份规则候选与分歧裁决、审阅、两份模型候选与分歧裁决、合同、初版设计（反例）、修正设计（3 个 mutant）、源码映射、策略、向量、真实 SQLite 实现 + harness + 并发测试 |
| `ai-dlc/assets/sizing.yaml` | `aidlc_state.py size|plan|advance`、`verify_sizing.py` | v2：六条推导规则（带 `needs`）+ **`stages:` 广度网格** + `never_skippable`（三道门在里面）+ 每档的 `depth` / `test_strategy` + `recompose` 约束 + 预算覆盖 |
| `ai-dlc/assets/graph.yaml` | `verify_graph.py`、`aidlc_state.py graph` | 58 节点 / 83 边；节点带 `reads` / `must_not_read` / `writes` / `authority` |
| `ai-dlc/assets/loops.yaml` | `verify_loop.py`、`aidlc_state.py loops` | 七个环的契约：level / timescale / generator ≠ verifier / stop 四键（grill 环 v1.8.0 加入） |
| `ai-dlc/assets/triggers.yaml` | 人 | 每个环绑到哪个原生触发（`/goal` `/loop` Stop hook `/schedule`） |
| `acceptance-fleet/assets/evaluators.yaml` | `pick_evaluators.py` | 供应商声明与探测命令；每个槽的同源盲区排名 |
| `donewhen-extract/references/done-when-v2-schema.yaml` | 人 + `validate_done_when_v2.py` | **契约的唯一 schema**；含 `constraints.structure` |
| `dos-extract/assets/dos_template.yaml` | 人 | DOS 的 13 节结构：核心模型（objects ≤7 · relationships · rules · composition）+ 通用语言（vocabulary） |
| `invariant-extract/assets/invariant_card.yaml` | `verify_card.py` | 不变量卡的具名字段 |
| `donewhen-extract/assets/done_when_card.yaml` | `verify_done_when.py` | done_when 卡的具名字段 |
| `plan-cards/assets/card_template.yaml` | `lint_cards.py` | 任务卡的具名字段 |
| `spec-compile/assets/compile_manifest.yaml` | `verify_compile.py` | 可判性阶梯的产物清单 |
| `calibrate/assets/calibration_report.yaml` | `verify_calibration.py` | 校准报告的形状 |
| `pr-review/assets/findings_template.yaml` | 人 | 发现的三档归位形状 |
| `tune/assets/harness_proposals_template.yaml` | `apply_proposal.py` | 提案的具名字段 |

然后是模板。这些人填，脚本检产物。

| 资产 | 用在哪 |
|---|---|
| `issue/assets/issue_template.md` · `bug_extra.md` · `escape_extra.md` | issue body 的段落序；bug 与逃逸缺陷各多一段 |
| `ai-dlc/assets/g1_record.md` · `g1_interpretations.md` · `g2_record.md` · `g3_record.md` | 三道人签的门的记录形状 |
| `ai-dlc/assets/failure_report.md` | 升级时给 G3 的失败报告（人不看原始日志） |
| `ai-dlc/assets/ledger_template.md` | 账本的行形状 |
| `ai-dlc/assets/change_proposal.md` | 改锁内文件必须同 diff 附的变更提案 |
| `implement/assets/card_context.md` | **实现者能看到的全部输入**的形状（含 agent-map 切片） |
| `dos-extract/assets/agent_map_template.md` · `decisions_template.md` · `docs_extraction_prompt.md` · `dos_amendment_template.md` | 仓库地图 / 判断审计轨 / 文档扫描 / 本体修订 |
| `psl-derive/assets/workflow_template.md` · `form_draft_template.md` · `divergence_template.md` | U3 的三样推导产物 |
| `grill/assets/pending_template.yaml` | grill 环的待定清单形状（三来源 Q-n / D-n / U-n、四状态、三条出路） |
| `invariant-extract/assets/cross_territory_promotion_template.md` | 跨领地不变量的提升 |
| `pr/assets/pr_template.md` | PR body 的产物序 |
| `release/assets/changelog_entry_template.md` · `release_notes_template.md` | 交付产物 |
| `retro/assets/retro_template.md` | 复盘报告形状 |
| `acceptance-fleet/assets/round_diff_template.md` | 轮次间差异 |
| `issue/assets/escape_defect.md` | 逃逸缺陷登记行 |
