# bespoke-design-system skill issues — 2026-06-18

触发：用户反馈"生成的设计系统很普通很一般"。深挖生成内核后定位到 B5 `neighbor_check` 的结构性问题，并实测 corpus 距离分布发现编码器退化。本轮已修复 #1（语义反转），#2 记录待后续。

## 问题清单

| # | 位置 | 严重度 | 问题 | 状态 |
|---|------|--------|------|------|
| 1 | `checks/neighbor_check.py` | **blocker（核心价值失效）** | 闸门**奖励靠近 corpus**：`distance<0.3 → pass`。但 corpus 内部最大最近邻距离仅 **0.26**，pass 阈值设在其之上 → 闸门**从不拒绝任何东西**（no-op），且语义上**奖励 clone**。pipeline（B2 检索→B3 密集风格岛→B4 翻译）本就收敛到 corpus 成员，一个奖励"距离小"的闸门正好给抄袭盖绿章。 | ✅ 已修复 v1.11.0 |
| 2 | `tools/build_neighbor_corpus.py` `encode()` | **high（限制 #1 修复的有效性）** | 37 维编码**判别力不足**：约 50/137 系统塌成 <0.08 的近似重复。实测 `corporate`/`futuristic`/`sleek`/`storytelling` 距离全 = **0.0000**。根因实证：这些是 **stub tokens**，共用完全相同的 7 色 Tailwind 默认调色板（`#3B82F6/#8B5CF6/...`），只字体不同。 | ✅ 缓解 v1.13.0（encode 37→44 维，加 has_mono/num_families/更细色彩维；exact-0 坍缩对 ~5→3）。**剩 3 对真 stub 数据重复**（sleek/storytelling、cosmic/creative、colorful/simple：palette+font 全同）无解，需 re-extract 或排除——记为遗留数据任务 |
| 3 | `SKILL.md §一 产品诚实声明` | medium（定位与新语义冲突） | 声明"不出格（不会跑出已知好设计的范围）— 可量化下限保证"。这正是 #1 的病根：用"不出格"当卖点 = 把下限焊成天花板。v1.11.0 把 neighbor 改成独特性带后，"不出格=下限保证"的表述与新机制冲突，需重写产品自我定位。 | ✅ 已修复 v1.12.0（§一 改为"不抄袭 + 不平庸"，明确不再声称"不出格"；定位改为"协调前提下争取独特"） |

## 改动4 实施记录（v1.12.0 — taste-critic）

承接 #1 的诊断"neighbor 反转必要但不充分，真正治'很普通'要 taste critic"，本轮实施改动4：

- **新 agent** `agents/taste-critic.md`：独立对抗式评审，**只判独特性/有没有 POV**（4 个 Python check + rationale-judge 都看不见的维度）。5 项测试：clone / signature / POV / substitutable / modal-default。两模式：rank（B4.5 从 N 候选选优）/ gate（B5 第 6 闸）。
- **B4 改为先发散后收敛**：B4a 发散 3 个承诺不同 POV 的候选方向 → B4.5 taste-critic(rank) 选 winner（all_generic 则回炉重发散，不矮子拔将军）→ B4b 展开 winner，守住签名动作。
- **B5 加第 6 闸**：taste-critic(gate) 判成稿是否仍平庸（`generic`→reject，`derivative`→needs_revision）。
- 同步更新：SKILL.md（B4/B4.5/B5/铁律3/§一/anti-patterns/references）、b4/b5/b6 prompts、CLAUDE.md dogfooding 表（B4a/B4.5/B4b + taste-critic 行）、tacit-knowledge-boundary / dieter-rams（6 项 check）、两个 README、plugin/marketplace 描述。版本 1.11.0 → 1.12.0。
- **#2 编码器退化仍未解**：taste-critic 是 LLM 判断，绕开了 37 维编码器的分辨率瓶颈，所以它能抓 neighbor 抓不到的概念级平庸——但 neighbor_check 自身的判别力问题（#2）依旧存在，后续若要让 neighbor 更准仍需提升编码维度。

## 改动2/3/5 + 编码器#2 实施记录（v1.13.0 — distinctiveness kernel）

承接诊断的五条改造，本轮把剩余四条全部落地（改动1=v1.11.0、改动4=v1.12.0 已做）：

- **编码器#2**：`encode()` 37→44 维，新增 `palette_mean_L / L_contrast_range / chroma_spread / neutral_avg_chroma / has_mono / num_font_families_norm / weight_spread_norm`。重建 corpus，corporate↔futuristic、clean↔colorful 从 0.0→0.177（靠字体维分开）。NN 分布几乎不变（中位 0.119），改动1 阈值无需重校。剩 3 对真 stub 数据重复（见 #2）。验证：cursor 仍 clone、OPC 仍 distinctive。
- **改动2（B3 反极性）**：`b3_resolve.py` Step4 从"删孤立 outlier"反转为"选 anchor + 保留 productive_tension（孤立但 relevance≥p25 的规则，标注供 B4 发散）"，丢弃线 median→p25。冲突消解（Step2/3）不变（真逻辑冲突）。真实 OPC B2 实测：anchor=linear-app+vercel，55 条 productive_tension 被保留（含 cursor 极端负字距等签名，旧逻辑会丢）。输出加 `anchor` / `productive_tensions` 字段。
- **改动3（concept-first B0.5）**：新增 `prompts/b05-concept-seeding.md` + SKILL.md B0.5 阶段。为 brief 产 3 个发散 POV（非品类标签，≥1 bold），驱动 B1b（覆盖品类质心，防塌缩）+ B2（覆盖各 concept 的 tension_hint）+ B4a（发展种子而非重发明）。
- **改动5（概念级规则 + transformational 算子）**：规则 schema 加可选 `organizing_principle` / `signature_move`（非破坏；linear-app 压缩规则做示范）。B4 开"至多 1 个 `transformational: true`"受控例外（Boden transformational 有界化）：honest 空 source_rules + transformation_argument + confidence≤medium，由 taste-critic 验证服务 concept、rationale-judge 认标记不当 phantom（额度≤1，洞不重开）。

版本 1.12.0 → 1.13.0（SKILL.md / plugin.json / marketplace.json）。所有 spec 同步（B0-B6 流程、prompts、CLAUDE.md dogfooding 表、README、tacit/dieter 引用、37→44 维表述）。

**仍未做**：A1-A4 提取脚本批量回填 organizing_principle/signature_move（存量规则只示范了 1 条）；3 对 stub tokens re-extract/排除；端到端 dogfooding 验证整条新 B0.5→B5 流程（LLM 阶段无法单测，需跑真实 brief）。

## 根因定位

**#1 根因**：把"品味下限"实现成"最近邻 < 0.3"。在一个本就向 corpus 收敛的 pipeline 里，这不是下限而是**夹死在 corpus 凸包内的上限**。全局最优解 = 复刻最近的 corpus 成员（distance≈0 必过）。`examples/code-review-saas` 就是铁证：它是 Linear 换强调色，distance≈0.18，5/5 全绿。

**#2 根因**：编码维度集中在 brand color（4 维 ×1.5 权重）等低层 token 统计，缺少能捕捉**结构 gestalt / 概念**的维度。两个结构相同、仅配色不同的系统被判为"远"，而两个语义迥异、token 恰好相近的系统被判为"同一点"。

## 修复（本轮 #1）

`neighbor_check.py` 语义反转为**独特性带**（阈值从 corpus 分布校准）：

- `<0.05` → reject `derivative_clone`
- `0.05–0.12` → needs_review `derivative_suspect`（0.12 = corpus 最近邻中位数）
- `0.12–0.45` → pass `distinctive`
- `>0.45` → needs_review `far_outlier`（不再单凭距离 reject——本 check 分不清大胆与不自洽，交给 coherence/archetype/rationale）

**实测验证**：
- 真实 OPC 产出（draft-tokens.json）→ `pass/distinctive`（0.18，最近邻 lovable）✓
- 重编码任意 corpus 成员（cursor/stripe/notion/linear-app/vercel/apple）→ 全部 `reject/derivative_clone`（0.0）✓

同步更新：`SKILL.md` B5 表、`prompts/b5-p0-gate.md`、`scripts/build-neighbor-corpus.md`、根 `CLAUDE.md` dogfooding 表。版本 1.10.0 → 1.11.0（三处同步）。

## 本次是否影响产物质量

**影响重大且正面**：#1 修复把一个 no-op 且鼓励抄袭的闸门，变成能拦截 token clone 的真闸门。但**必须诚实**：这**治不好用户说的"很普通"**——感知层面的概念级平庸（如 OPC 在 0.18 判 pass 但人看着仍普通）在 37 维 token 距离里**看不见**（受 #2 编码器退化所限）。

**真正的杠杆是 taste critic（改动4）+ concept-first（改动3）**，neighbor 反转只是必要的前置清障（停止给抄袭盖绿章），非充分。详见对话中的五条重设计方案与 memory `project_bespoke_genericness_diagnosis.md`。
