# check-complete.ps1 - 完成验证脚本 (Windows)
# planning-with-files skill v2.0.0

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════"
Write-Host "           COMPLETION VERIFICATION CHECK                    "
Write-Host "═══════════════════════════════════════════════════════════"
Write-Host ""

$Errors = 0

# 检查 1: task_plan.md 是否存在
Write-Host "Checking task_plan.md exists... " -NoNewline
if (-not (Test-Path "task_plan.md")) {
    Write-Host "SKIP" -ForegroundColor Yellow -NoNewline
    Write-Host " (no planning files found)"
    Write-Host ""
    Write-Host "No planning-with-files session detected. OK to stop."
    exit 0
}
Write-Host "OK" -ForegroundColor Green

# 检查 2: 所有阶段是否完成
Write-Host "Checking all phases complete... " -NoNewline
$incompletePhases = Select-String -Path "task_plan.md" -Pattern "^\s*- \[ \] \*\*Phase" -AllMatches
if ($incompletePhases) {
    Write-Host "FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Uncompleted phases found:"
    $incompletePhases | ForEach-Object { Write-Host "  $($_.Line)" }
    Write-Host ""
    $Errors++
} else {
    Write-Host "OK" -ForegroundColor Green
}

# 检查 3: 所有子任务是否完成
Write-Host "Checking all subtasks complete... " -NoNewline
$incompleteSubtasks = (Select-String -Path "task_plan.md" -Pattern "^\s*- \[ \]" | Measure-Object).Count
if ($incompleteSubtasks -gt 0) {
    Write-Host "WARNING" -ForegroundColor Yellow -NoNewline
    Write-Host " ($incompleteSubtasks unchecked items)"
} else {
    Write-Host "OK" -ForegroundColor Green
}

# 检查 4: findings.md 是否存在且有内容
Write-Host "Checking findings.md... " -NoNewline
if (Test-Path "findings.md") {
    $findingsLines = (Get-Content "findings.md" | Measure-Object -Line).Lines
    if ($findingsLines -lt 20) {
        Write-Host "WARNING" -ForegroundColor Yellow -NoNewline
        Write-Host " (minimal content)"
    } else {
        Write-Host "OK" -ForegroundColor Green
    }
} else {
    Write-Host "WARNING" -ForegroundColor Yellow -NoNewline
    Write-Host " (not found)"
}

# 检查 5: 是否有未解决的错误
Write-Host "Checking for unresolved errors... " -NoNewline
$unresolvedErrors = Select-String -Path "task_plan.md" -Pattern "\| No \||\|No\|" -Quiet
if ($unresolvedErrors) {
    Write-Host "WARNING" -ForegroundColor Yellow -NoNewline
    Write-Host " (unresolved errors exist)"
} else {
    Write-Host "OK" -ForegroundColor Green
}

# 检查 6: progress.md 是否存在
Write-Host "Checking progress.md... " -NoNewline
if (Test-Path "progress.md") {
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "WARNING" -ForegroundColor Yellow -NoNewline
    Write-Host " (not found)"
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════"

# 最终判断
if ($Errors -gt 0) {
    Write-Host ""
    Write-Host "CANNOT STOP: $Errors critical issue(s) found." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please complete all phases before stopping."
    Write-Host "Use 'Get-Content task_plan.md' to see what remains."
    Write-Host ""
    exit 1
} else {
    Write-Host ""
    Write-Host "✓ All critical checks passed. OK to stop." -ForegroundColor Green
    Write-Host ""
    
    # 显示摘要
    if (Test-Path "task_plan.md") {
        Write-Host "Task completed. Planning files saved:"
        Write-Host "  • task_plan.md  - Goals, decisions, errors"
        if (Test-Path "findings.md") { Write-Host "  • findings.md   - Research and notes" }
        if (Test-Path "progress.md") { Write-Host "  • progress.md   - Session log" }
        Write-Host ""
        Write-Host "These files can be used to resume or review later."
    }
    
    exit 0
}
