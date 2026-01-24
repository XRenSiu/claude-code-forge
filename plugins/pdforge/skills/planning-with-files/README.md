# Planning with Files (改进版)

> Manus 风格的持久化 Markdown 规划系统
> 
> 基于 OthmanAdi/planning-with-files，加入了多项改进

## 改进内容

相比原版，这个版本新增：

| 改进 | 说明 |
|------|------|
| **智能触发** | 基于工具调用次数决定是否重读计划（每 10 次） |
| **上下文压缩** | 3 级压缩策略，主动管理 context 大小 |
| **动态模板** | 3 种任务类型模板（编码/研究/通用） |
| **5 问检查** | 会话恢复时的上下文重建机制 |
| **增强错误追踪** | 强制保留错误记录，避免重复错误 |
| **Windows 支持** | 完整的 PowerShell 脚本 |

## 安装

### 方法 1: 复制到 Claude Code Skills 目录

```bash
# macOS/Linux
cp -r planning-with-files ~/.claude/skills/

# Windows (PowerShell)
Copy-Item -Recurse planning-with-files $env:USERPROFILE\.claude\skills\
```

### 方法 2: 项目级 Skill

```bash
cp -r planning-with-files .claude/skills/
```

## 使用

### 自动触发

当任务满足以下条件时自动触发：
- 任务超过 3 步
- 需要跨会话持久化
- 研究型任务
- 修改核心代码

### 手动触发

```
/planning-with-files
```

## 文件结构

```
planning-with-files/
├── SKILL.md              # 核心指令
├── scripts/
│   ├── init-session.sh   # 会话初始化
│   ├── init-session.ps1  # Windows 版
│   ├── check-complete.sh # 完成验证
│   └── check-complete.ps1
├── templates/
│   ├── generic_plan.md   # 通用任务模板
│   ├── coding_plan.md    # 编码任务模板
│   ├── research_plan.md  # 研究任务模板
│   ├── findings.md       # 发现记录模板
│   └── progress.md       # 进度日志模板
├── references/
│   ├── recovery.md       # 会话恢复指南
│   └── compression.md    # 上下文压缩策略
└── tests/
    └── pressure-tests.md # 压力测试场景
```

## 核心概念

### 三文件模式

| 文件 | 用途 |
|------|------|
| `task_plan.md` | 目标、阶段、错误追踪 |
| `findings.md` | 研究发现、技术决策 |
| `progress.md` | 会话日志、测试结果 |

### 关键规则

1. **2-Action Rule**: 每 2 次 view/browser 操作后，必须保存发现
2. **错误保留**: 不删除错误记录，让模型学习避免重复
3. **智能重读**: 每 10 次工具调用后重读 task_plan.md

## 致谢

- [OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files) - 原版
- Manus AI - Context Engineering 原理
- Anthropic - Claude Code Skills 系统
