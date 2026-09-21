---
name: ratify
description: >-
  补引擎自己给不出的缺口：把一份还带着未决项的制品（不变量卡、契约、签字版形态草案）从草稿变成**被冻结的法**
  的那段仪式——未决项逐条从文件里读出来呈给人（不是凭记忆挑几条）、一条一条当场裁、裁决带姓名与日期写回制品、
  再跑一次判据、最后才签；签字要么人自己来，要么以**受委托签署**落地并把人的授权原话写进锁文件。效果：人只回答
  「这条怎么办」，不需要记得还剩什么没定，也不需要敲命令。Use when: "冻结这张卡" / "签了吧" / "批准" / "立法" /
  "ratify" / "freeze the invariant card" / "把不变量定下来" / "我要签 G1" / "签了这个门" /
  抽完不变量、写完契约、或 /psl-derive 出完形态草案准备过 G1 时。NOT for:
  起草不变量（/invariant-extract）、写契约（/donewhen-extract）、写世界（/psl）、推形态（/psl-derive）。
  前置：有一份可裁可签的制品（不变量卡 / 契约 / G1 记录）、python3 + pyyaml。
argument-hint: "<card.yaml | contract.yaml> [--out <lock 路径>] [--stage g2|l5]"
version: 0.1.0
user-invocable: true
# 只能由人显式调起：它的终点是一次签字——冻结之后改被锁文件要走变更提案。
# 不能因为对话里出现「差不多了」「可以了」就被模型自行调起。
disable-model-invocation: true
---

# ratify — 把草稿变成法的那段仪式

产物：一份 `.lock`（哈希 + 签字人 + 时间戳）+ 被裁决填满的制品本身。本文件只写引擎给不出的东西：
仪式的顺序为什么不可调换（γ）、什么算一条裁决而不是拖延（φ）、授权怎么留痕（γ）、原语在哪（Π）。

## 缺口（Control + Judgment）

deletion 测试：撤掉本 skill，人说「冻结吧」，引擎会直接去跑 `lock_done_when.py sign`。三件事同时发生：
未决项没人提起（引擎记得的是它觉得有趣的那几条，不是文件里全部）、裁决只停在对话里（几周后没人知道
当初为什么这么定）、签字人写谁全凭手气。缺口是 **Control**（顺序与留痕）与 **Judgment**（什么算裁决）。

不是 Capability：呈现与写回由 `scripts/agenda.py` 做，冻结由 `../ai-dlc/scripts/lock_done_when.py` 做，
两者都已存在。本 skill 不重做它们，只保证它们按这个顺序、带着这些约束被用。

## 世界（Σ）

- **草稿可以有未决项，签字不能**。这是两件事，不是同一件事的两个阶段——`verify_card.py` 默认放行未决项
  （那正是草稿的用途），`--ready-to-sign` 才把它们升成拒。冻结是把「当下这份内容」按哈希钉死。
- **谁在签**。`lock_done_when.py sign` 的 `--signer-kind` 只有两种：
  - `human`：人自己跑那条命令，`--by` 是人名；
  - `delegated_agent`：人在对话里明确授权、由 agent 代跑，此时 `--authorization` **必填**，把人的授权原话
    （谁、什么时候、授权了什么）写进锁文件。没有 `--authorization` 的受委托签署会被脚本直接拒。
  **没有第三种。** 模型不得以 `human` 身份签字——那是伪造签名，不是省事。
- **制品的种类**。不变量卡（`territory_id` + `hard_invariants`）、done_when 契约、**G1 世界裁决记录**
  都走这段仪式；`sign` 对不变量卡会自己去跑卡的仪式检查，所以「跳过 ratify 直接签」这条路在卡上不存在。
- **末端不同，仪式相同**。卡与契约签在 `lock_done_when.py sign`；G1 签在
  `aidlc_state.py gate g1 --verdict pass --by <人> --signer-kind human --record <g1-record.md>`。
  两者前面那一段——从文件里读出未决项、逐条呈、当场裁、带姓名日期写回、再跑判据——是同一段。
  之所以不为 G1 另开一个 skill：人要的是「从草稿到签字」这段仪式本身，两个 skill 教同一件事早晚会漂成两套说法。
- **G1 裁的是推导产物，不是世界**。`gate g1` 要求 `world.derived_dir` 指向一个真实存在的 `derived/`
  （`/psl-derive` 的产出）。只有 PSL 没有形态草案时签不了，也不该签——"日历筛选器"那类错误发生在**推导**那一步。

## 判据（φ）：什么算一条裁决

- **裁决是决定，不是复述**。「这条冲突确实存在」不是裁决；「排除是有意的，按隐私要求，INV-003 收窄成
  未同步窗口内加密落盘」才是。
- **拖延不算裁决，但拖延是合法的**。「待定 / 再说 / 回头看」被 `agenda.py` 直接拒——它不是坏答案，
  它是**另一个去处**：移进 `open_questions`，带负责人与截止日期，然后这张卡先不签，或者签其余部分。
- **「不知道」也是合法答案**，处理同上：转成开放问题，不要猜一个答案填进去。一条猜出来的裁决会以
  「已裁决」的样子活很久。
- **裁决要能被复核**：写回时自动带日期与姓名。姓名是人的名字，不是 agent 的。
- **G1 上，PSL 的每一条 Open Question 都要有一行**，三选一：接受 seam / 现在回答 / 阻塞。
  跳过不是选项——承重空槽会以默认值的形态混进实现。
  **裁为「阻塞」的，G1 不能 PASS**：`agenda.py` 会把它单列出来，这不是提醒，是拦。

## 控制（γ）：顺序不可调换

1. **先读文件，再开口**。未决项由 `agenda.py <制品>` 从文件里列出来，**逐条呈现，不筛选**——
   与 `aidlc_state.py notes --for-gate` 同一条纪律：做「有趣度」筛选的那一刻，被筛掉的那条就是下次撞的墙。
2. **一条一条裁**。每条把证据（冲突两边、来路、statement）摆出来，等人回答；不要把五条打包成一个问题。
3. **当场写回**（`agenda.py --rule <n> --resolution "…" --by "<人名>"`），不要攒到最后——中途断了，
   已裁的部分留在文件里。
4. **再跑一次判据**：`verify_card.py --ready-to-sign`（卡）或对应制品的校验器。**不许跳过这一步**，
   因为裁决可能引出新的未决项（改写一条规则会动它的 survival_test）。
5. **最后才签**。人自己签 → 给命令、由人执行；人授权 agent 代签 → `--signer-kind delegated_agent`
   `--authorization "<人的原话 + 时间>"`。
6. **签完把话说全**：锁文件路径、被冻了哪些文件、签字人与方式、之后改这些文件要走变更提案。

## 原语（Π）

- `scripts/agenda.py <制品> [--json]` —— 未决项清单，带证据与写回位置；`--check` 只返回退出码；
  `--rule <n|id> --resolution "…" --by "<人名>"` 写回一条裁决（自动盖日期）。制品种类自动认：
  - **不变量卡**：冲突 / 低置信 / 未过存活测试；
  - **G1 记录**：四问未答 · PSL 的每条 Open Question · 分歧集与 flag · 应然↔现状对账 ·
    明确不做为空 · 外部证据 · 决定与签字版哈希。裁 OQ 时 `--verdict accept_seam|answer|blocking` 必填；
    `--psl` / `--derived` / `--dos` 指出要核对的那三样（不给就从记录 header 读 PSL）。
- `../invariant-extract/scripts/verify_card.py <卡> --ready-to-sign` —— 冻结前的判据。
- `../ai-dlc/scripts/aidlc_state.py gate g1 --verdict pass|reject --by <人名> --signer-kind human
  [--authorization "…"] --record <g1-record.md>` —— G1 的签字端；它自己还会核形态草案的 sha256
  与记录里写的是否一致，不一致直接拒。
- `../ai-dlc/scripts/lock_done_when.py sign --signer-kind human|delegated_agent --by <人名>
  [--authorization "…"] [--stage g2|l5] [--out <lock>] <文件...>` —— 冻结；卡上带未决项会被它自己拒。
- `../ai-dlc/scripts/lock_done_when.py verify --lock <lock>` —— 之后核对：被锁文件改了而没附变更提案 → 拒。
- `../ai-dlc/assets/change_proposal.md` —— 冻结之后要改被锁文件，唯一合法路径。

## 高危黑名单（不可豁免）

- **绝不以 `--signer-kind human` 代人签字**。人不在场就停下来，把命令交给人。
- **绝不筛选议程**。哪怕一条看起来显然，也要呈现——「显然」是引擎的判断，不是人的。
- **绝不把拖延写成裁决**。「待定」进 `open_questions`，不进 `resolution`。
- **绝不跳过第 4 步的复检**。裁决会改内容，改完的内容没被判据看过就不该被冻。
- **绝不在人没明确说「同意 / 签吧」时执行签字**——本 skill 的存在不等于授权。
- **绝不用 `--force-unresolved` 绕过未决项**，除非人明确要求且给出理由；理由会写进锁，那是给未来的人看的。
- **绝不在有「阻塞」OQ 时把 G1 判成 PASS**。阻塞是人自己下的判断，绕过它等于替人改主意。
- **绝不在没有 `derived/` 时签 G1**——那是在签空气；先 `/psl-derive`。

## 接线（在 AI-DLC 里的位置）

- **X1 的落地关**：`/invariant-extract` 出卡（硬不变量恒为 `propose`）→ **本 skill** 裁决 + 冻结 →
  `/spec-compile` 才有东西可编（把 □ 编成 property 测试 / fitness function）。签字只是让它成为法，
  编译才让它有牙齿。
- **与 G2 的关系**：一次交付运行里的 G2 有 slug 与状态机（`aidlc_state.py gate g2`），本 skill 管的是
  **仓库级立法**（不变量卡、跨运行的契约），两者用的是同一个 `lock_done_when.py`，留痕形状一致。
- **与 `/donewhen-extract` 的关系**：契约写完也可以走本 skill 冻结；卡与契约的未决项定义不同，
  `agenda.py` 目前只认卡的三类（冲突 / 低置信 / 存活测试），契约走它自己的校验器。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——结构过审 + 脚本在 fixtures 上冒烟（议程从文件读、拖延被拒、
裁决带姓名日期写回、受委托签署无授权被拒）。行为层（有没有真的减少「冻了没定的东西」）未跑。
