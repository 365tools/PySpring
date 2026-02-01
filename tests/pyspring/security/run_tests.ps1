# PySpring Security 测试运行器 (PowerShell版本)
# 自动设置UTF-8编码以正确显示中文

# 设置Python IO编码为UTF-8
$env:PYTHONIOENCODING = 'utf-8'

# 设置控制台输出编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 切换到项目根目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptPath)
Push-Location $projectRoot

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "PySpring Security 测试套件" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# 运行所有测试
& python tests\security\run_all_tests.py

Write-Host ""
Write-Host "测试完成！" -ForegroundColor Green

Pop-Location

# 如果是双击运行，保持窗口打开
if ($Host.Name -eq "ConsoleHost") {
    Write-Host ""
    Write-Host "按任意键退出..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
