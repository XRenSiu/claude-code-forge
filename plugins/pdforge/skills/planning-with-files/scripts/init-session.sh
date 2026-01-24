#!/bin/bash
# init-session.sh - 会话初始化和恢复脚本
# planning-with-files skill v2.0.0

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}[planning-with-files]${NC} Initializing..."

# 检查是否存在未同步的工作
PLAN_EXISTS=false
FINDINGS_EXISTS=false
PROGRESS_EXISTS=false

if [ -f "task_plan.md" ]; then
    PLAN_EXISTS=true
fi

if [ -f "findings.md" ]; then
    FINDINGS_EXISTS=true
fi

if [ -f "progress.md" ]; then
    PROGRESS_EXISTS=true
fi

# 场景 1: 完全新的会话
if [ "$PLAN_EXISTS" = false ] && [ "$FINDINGS_EXISTS" = false ] && [ "$PROGRESS_EXISTS" = false ]; then
    echo -e "${GREEN}Ready.${NC} No existing plan found."
    echo ""
    echo "To start a new task:"
    echo "  1. Determine task type (research/coding/debug/general)"
    echo "  2. Copy appropriate template from skill's templates/ folder"
    echo "  3. Fill in the Goal section"
    echo ""
    echo "Or invoke manually with: /planning-with-files"
    exit 0
fi

# 场景 2: 存在之前的工作，需要恢复上下文
echo -e "${YELLOW}Found existing planning files - recovering context...${NC}"
echo ""

# 显示 5-Question Check
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}              5-QUESTION CONTEXT RECOVERY                  ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Q1: 我在做什么？
echo -e "${GREEN}Q1: What am I doing?${NC}"
if [ "$PLAN_EXISTS" = true ]; then
    # 提取 Goal 部分
    echo "    → Reading task_plan.md Goal section..."
    if grep -q "## Goal" task_plan.md; then
        sed -n '/## Goal/,/## /p' task_plan.md | head -5 | tail -n +2 | sed 's/^/    /'
    fi
fi
echo ""

# Q2: 我做到哪了？
echo -e "${GREEN}Q2: Where did I leave off?${NC}"
if [ "$PLAN_EXISTS" = true ]; then
    echo "    → Current phase markers:"
    # 查找 CURRENT 标记或 in_progress 状态
    grep -E "(CURRENT|\*\*Status:\*\* in_progress|Status: in_progress)" task_plan.md 2>/dev/null | head -3 | sed 's/^/    /' || echo "    (No active phase found)"
    echo ""
    echo "    → Incomplete phases:"
    grep -E "^\s*- \[ \]" task_plan.md 2>/dev/null | head -5 | sed 's/^/    /' || echo "    (All phases complete!)"
fi
echo ""

# Q3: 我学到了什么？
echo -e "${GREEN}Q3: What have I learned?${NC}"
if [ "$FINDINGS_EXISTS" = true ]; then
    echo "    → findings.md exists with discoveries"
    # 显示 Quick Reference 部分
    if grep -q "## Quick Reference" findings.md; then
        echo "    → Key findings:"
        sed -n '/## Quick Reference/,/---/p' findings.md | grep "^[0-9]" | head -3 | sed 's/^/      /'
    fi
else
    echo "    → No findings.md found"
fi
echo ""

# Q4: 什么失败过？
echo -e "${GREEN}Q4: What has failed?${NC}"
if [ "$PLAN_EXISTS" = true ]; then
    if grep -q "## Errors Encountered" task_plan.md; then
        ERROR_COUNT=$(grep -c "^|" task_plan.md 2>/dev/null | tail -1 || echo "0")
        if [ "$ERROR_COUNT" -gt 2 ]; then
            echo "    → Found error records in task_plan.md"
            echo "    → READ THESE to avoid repeating mistakes!"
        else
            echo "    → No errors recorded yet"
        fi
    fi
fi
echo ""

# Q5: 下一步是什么？
echo -e "${GREEN}Q5: What's next?${NC}"
if [ "$PLAN_EXISTS" = true ]; then
    echo "    → Next unchecked item:"
    grep -E "^\s*- \[ \]" task_plan.md 2>/dev/null | head -1 | sed 's/^/    /' || echo "    (All items complete!)"
fi
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# 提醒重新读取文件
echo -e "${YELLOW}IMPORTANT:${NC} Read these files to fully restore context:"
[ "$PLAN_EXISTS" = true ] && echo "  • task_plan.md  - Goals, phases, errors, decisions"
[ "$FINDINGS_EXISTS" = true ] && echo "  • findings.md   - Research and technical notes"
[ "$PROGRESS_EXISTS" = true ] && echo "  • progress.md   - Session log and test results"
echo ""

# 检查是否有未完成的工作
if [ "$PLAN_EXISTS" = true ]; then
    INCOMPLETE=$(grep -c "\- \[ \]" task_plan.md 2>/dev/null || echo "0")
    if [ "$INCOMPLETE" -gt 0 ]; then
        echo -e "${YELLOW}⚠ $INCOMPLETE unchecked items remain. Resume work!${NC}"
    else
        echo -e "${GREEN}✓ All phases appear complete.${NC}"
    fi
fi

exit 0
