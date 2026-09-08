# 这个目录为什么还在说 `sdlc`

`dogfood/ring-audit/` 是 2026-09-05 那次自审的**完整归档**：账本行、门的裁决记录、失败报告、
issue / PR 正文、六轮评审的 findings。插件在 2026-09-08 从 `sdlc` 改名 AI-DLC，**这个目录一个字节
都没改**。

理由是插件自己的不变量 5：**产物可回滚，判据与失败记录不回滚**。一次改名不该让三周前的账本变成
另一副样子——那样做之后，任何一条"当时就这么写的"都不再可信。同样的理由适用于
`docs/reports/raising-the-floor-2026-09-05.*`（含两份冷读记录：那是读者当时真实说出的话）
与 `eval/effect/` 归档读数的旧 arm 标签。

## 一处例外：归档里的**脚本与锁**是指针，不是记录

冻结的是**记录**（账本行、门的裁决、失败报告、issue / PR 正文、六轮 findings）。
`check_anchors.py` / `render_audit.py` / `replay_card_commits.sh` 与 `anchors.lock` 不是记录，
是**指向现在这棵树的地址**：不改它们就跑不起来，而一个跑不起来的核对工具等于没有核对。
所以这四个文件里的路径改了，**它们锚住 / 复现的内容一个字节没动**。

改完之后 `check_anchors verify` 仍报大量 `GONE`，那不是改名的残留，是 v0.12.0 与本轮两次实质改动
让被锚住的行真的移位了——那正是漂移检测该说的话。这次自审是 2026-09-05 的快照，不是活契约。

对照表：

| 归档里写的 | 现在叫 |
|---|---|
| `sdlc`（插件） | AI-DLC |
| `plugins/sdlc/` | `plugins/ai-dlc/` |
| `/sdlc`（斜杠命令） | `/ai-dlc` |
| `.sdlc/`（运行时目录） | `.aidlc/`（旧目录仍可读，见 `aidlc_state.py` 的 `resolve_root`） |
| `sdlc_state.py` | `aidlc_state.py` |
| `sdlc-ring-audit`（这次自审的 slug） | 不变——它是这次运行的名字，不是插件的名字 |
