#!/bin/bash
# check-complete.sh - 完成验证脚本
# planning-with-files skill v2.0.0

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "           COMPLETION VERIFICATION CHECK                    "
echo "═══════════════════════════════════════════════════════════"
echo ""

ERRORS=0

# 检查 1: task_plan.md 是否存在
echo -n "Checking task_plan.md exists... "
if [ ! -f "task_plan.md" ]; then
    echo -e "${YELLOW}SKIP${NC} (no planning files found)"
    echo ""
    echo "No planning-with-files session detected. OK to stop."
    exit 0
fi
echo -e "${GREEN}OK${NC}"

# 检查 2: 所有阶段是否完成
echo -n "Checking all phases complete... "
INCOMPLETE_PHASES=$(grep -E "^\s*- \[ \] \*\*Phase" task_plan.md 2>/dev/null || true)
if [ -n "$INCOMPLETE_PHASES" ]; then
    echo -e "${RED}FAILED${NC}"
    echo ""
    echo "Uncompleted phases found:"
    echo "$INCOMPLETE_PHASES" | sed 's/^/  /'
    echo ""
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}OK${NC}"
fi

# 检查 3: 所有子任务是否完成
echo -n "Checking all subtasks complete... "
INCOMPLETE_SUBTASKS=$(grep -c "^\s*- \[ \]" task_plan.md 2>/dev/null || echo "0")
if [ "$INCOMPLETE_SUBTASKS" -gt 0 ]; then
    echo -e "${YELLOW}WARNING${NC} ($INCOMPLETE_SUBTASKS unchecked items)"
else
    echo -e "${GREEN}OK${NC}"
fi

# 检查 4: findings.md 是否存在且有内容
echo -n "Checking findings.md... "
if [ -f "findings.md" ]; then
    FINDINGS_LINES=$(wc -l < findings.md)
    if [ "$FINDINGS_LINES" -lt 20 ]; then
        echo -e "${YELLOW}WARNING${NC} (minimal content)"
    else
        echo -e "${GREEN}OK${NC}"
    fi
else
    echo -e "${YELLOW}WARNING${NC} (not found)"
fi

# 检查 5: 是否有未解决的错误
echo -n "Checking for unresolved errors... "
if grep -q "| No |" task_plan.md 2>/dev/null || grep -q "|No|" task_plan.md 2>/dev/null; then
    echo -e "${YELLOW}WARNING${NC} (unresolved errors exist)"
else
    echo -e "${GREEN}OK${NC}"
fi

# 检查 6: progress.md 是否存在
echo -n "Checking progress.md... "
if [ -f "progress.md" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}WARNING${NC} (not found)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"

# 最终判断
if [ "$ERRORS" -gt 0 ]; then
    echo ""
    echo -e "${RED}CANNOT STOP: $ERRORS critical issue(s) found.${NC}"
    echo ""
    echo "Please complete all phases before stopping."
    echo "Use 'cat task_plan.md' to see what remains."
    echo ""
    exit 1
else
    echo ""
    echo -e "${GREEN}✓ All critical checks passed. OK to stop.${NC}"
    echo ""
    
    # 显示摘要
    if [ -f "task_plan.md" ]; then
        echo "Task completed. Planning files saved:"
        echo "  • task_plan.md  - Goals, decisions, errors"
        [ -f "findings.md" ] && echo "  • findings.md   - Research and notes"
        [ -f "progress.md" ] && echo "  • progress.md   - Session log"
        echo ""
        echo "These files can be used to resume or review later."
    fi
    
    exit 0
fi
