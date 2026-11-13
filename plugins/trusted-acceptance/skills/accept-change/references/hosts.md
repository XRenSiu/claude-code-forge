# 宿主接入

## Claude Code

插件目录 `plugins/trusted-acceptance/skills/accept-change/` 可被插件系统发现。按本仓库流程安装 `trusted-acceptance` 后，使用 `/trusted-acceptance:accept-change`；无冲突时宿主也可提供 `/accept-change`。缓存和启用配置变更后需新开会话。

尚未推送的新插件还需在本机已登记 marketplace 的缓存中加入对应条目和插件源码；仅写 enabledPlugins、installed_plugins 和版本缓存仍可能得到 “not found in marketplace”。用 `claude plugin details trusted-acceptance@claude-code-forge` 确认加载到一个 accept-change Skill。也可使用 `claude --plugin-dir /absolute/plugin/path` 从源码加载。远端发布前，marketplace 自动更新可能覆盖本地新增条目。

Skill 不固定某种子代理或浏览器工具。正式执行走维护者配置的受保护控制入口。不要把上下文分叉、工具预授权或 Stop Hook 当作独立权限边界；Hook 最多提示开发者送验，最终交付门禁检查正式记录。

## Codex 与其他 Agent Skills 宿主

将整个 `accept-change/` 文件夹放入宿主支持的 skills 目录，保留 `references/`、`scripts/` 和 `assets/` 相对关系，用 `$accept-change` 或宿主技能选择器调用。公共客户端不依赖 Claude 专属工具。`version` 是本仓库的 frontmatter 扩展；只接受基础格式的宿主可将它移入 `metadata.version`，内容无需改写。

本仓库只按其约定同步 Claude 本机插件缓存；不会隐式修改其他宿主配置。Codex 当前会话的可用技能列表不会因为写入仓库而自动扩展。

## 控制入口配置

操作者从可信维护路径提供 `--config` 的绝对路径，示例结构见 `assets/control-config.example.json`。候选代码、需求附件和日志均无权替换 endpoint/token_env。token 只从环境变量读入，用于提交/读取受限项目的运行；不授予批准合同、改政策、写证据、签发正式检查或生产发布权限。

客户端要求 HTTPS、系统证书校验、1–60 秒超时、2 MiB JSON 响应上限并拒绝重定向。它不允许 `--insecure`，不执行远端返回命令，也不把 token 写进文件或错误输出。客户端路径检查无法替代操作系统 ACL；配置文件必须处于实现方不能改动的位置。
