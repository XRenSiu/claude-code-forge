# init-session.ps1 - 会话初始化和恢复脚本 (Windows)
# planning-with-files skill v2.0.0

$ErrorActionPreference = "Stop"

Write-Host "[planning-with-files] " -ForegroundColor Blue -NoNewline
Write-Host "Initializing..."

# 检查是否存在未同步的工作
$PlanExists = Test-Path "task_plan.md"
$FindingsExists = Test-Path "findings.md"
$ProgressExists = Test-Path "progress.md"

# 场景 1: 完全新的会话
if (-not $PlanExists -and -not $FindingsExists -and -not $ProgressExists) {
    Write-Host "Ready. " -ForegroundColor Green -NoNewline
    Write-Host "No existing plan found."
    Write-Host ""
    Write-Host "To start a new task:"
    Write-Host "  1. Determine task type (research/coding/debug/general)"
    Write-Host "  2. Copy appropriate template from skill's templates/ folder"
    Write-Host "  3. Fill in the Goal section"
    Write-Host ""
    Write-Host "Or invoke manually with: /planning-with-files"
    exit 0
}

# 场景 2: 存在之前的工作，需要恢复上下文
Write-Host "Found existing planning files - recovering context..." -ForegroundColor Yellow
Write-Host ""

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host "              5-QUESTION CONTEXT RECOVERY                  " -ForegroundColor Blue
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host ""

# Q1: 我在做什么？
Write-Host "Q1: What am I doing?" -ForegroundColor Green
if ($PlanExists) {
    Write-Host "    → Reading task_plan.md Goal section..."
    $content = Get-Content "task_plan.md" -Raw
    if ($content -match "## Goal\r?\n(.*?)(?=\r?\n## )") {
        $Matches[1].Trim().Split("`n") | Select-Object -First 3 | ForEach-Object { Write-Host "    $_" }
    }
}
Write-Host ""

# Q2: 我做到哪了？
Write-Host "Q2: Where did I leave off?" -ForegroundColor Green
if ($PlanExists) {
    Write-Host "    → Incomplete phases:"
    Select-String -Path "task_plan.md" -Pattern "^\s*- \[ \]" | Select-Object -First 5 | ForEach-Object {
        Write-Host "    $($_.Line)"
    }
}
Write-Host ""

# Q3: 我学到了什么？
Write-Host "Q3: What have I learned?" -ForegroundColor Green
if ($FindingsExists) {
    Write-Host "    → findings.md exists with discoveries"
} else {
    Write-Host "    → No findings.md found"
}
Write-Host ""

# Q4: 什么失败过？
Write-Host "Q4: What has failed?" -ForegroundColor Green
if ($PlanExists) {
    $errorSection = Select-String -Path "task_plan.md" -Pattern "## Errors" -Quiet
    if ($errorSection) {
        Write-Host "    → Error records found in task_plan.md"
        Write-Host "    → READ THESE to avoid repeating mistakes!"
    } else {
        Write-Host "    → No errors recorded yet"
    }
}
Write-Host ""

# Q5: 下一步是什么？
Write-Host "Q5: What's next?" -ForegroundColor Green
if ($PlanExists) {
    Write-Host "    → Next unchecked item:"
    $nextItem = Select-String -Path "task_plan.md" -Pattern "^\s*- \[ \]" | Select-Object -First 1
    if ($nextItem) {
        Write-Host "    $($nextItem.Line)"
    } else {
        Write-Host "    (All items complete!)"
    }
}
Write-Host ""

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host ""

# 提醒重新读取文件
Write-Host "IMPORTANT: " -ForegroundColor Yellow -NoNewline
Write-Host "Read these files to fully restore context:"
if ($PlanExists) { Write-Host "  • task_plan.md  - Goals, phases, errors, decisions" }
if ($FindingsExists) { Write-Host "  • findings.md   - Research and technical notes" }
if ($ProgressExists) { Write-Host "  • progress.md   - Session log and test results" }
Write-Host ""

# 检查是否有未完成的工作
if ($PlanExists) {
    $incomplete = (Select-String -Path "task_plan.md" -Pattern "- \[ \]" | Measure-Object).Count
    if ($incomplete -gt 0) {
        Write-Host "⚠ $incomplete unchecked items remain. Resume work!" -ForegroundColor Yellow
    } else {
        Write-Host "✓ All phases appear complete." -ForegroundColor Green
    }
}

exit 0
