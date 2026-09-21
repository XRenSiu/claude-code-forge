# PSL-continuation-ref

## Vision
- PSL-001 这个产品赌：世界不是表。

## Mental Model
- PSL-002 用户看见它才相信它还在。
- PSL-003 平时不出声。
  PSL-002 与本条不矛盾：做了事才出声。

## Domain Model
- PSL-004 Window 是第一类实体，不是一个文件。

## State Machine
- PSL-005 没有任何一条让窗口静默消失的边。

## Workflow
一笔编辑落下时，窗口就此打开。
消歧判据：固化失败不改变编辑的世界。

## Acceptance
- A-1 断网编辑 → 强杀 → 重开后改动仍在

## Open Questions
- OQ-1 压缩触发点无来源（承重：编一个数字比没有数字更危险）
