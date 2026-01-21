#!/usr/bin/env pwsh
# IOC 核心测试运行脚本
# 运行Bean装饰器和Authentication IOC测试

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                        PySpring IOC 核心测试套件" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

Push-Location $projectRoot

try {
    # 清除Python缓存
    Write-Host "[1/3] 清除Python缓存..." -ForegroundColor Yellow
    Get-ChildItem -Path src -Filter __pycache__ -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Force -Recurse
    Write-Host "     ✅ 缓存已清除" -ForegroundColor Green
    Write-Host ""

    # 测试1：Bean装饰器灵活性
    Write-Host "[2/3] 测试Bean装饰器灵活性..." -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Gray
    python tests\ioc\test_bean_decorator_flexible.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ Bean装饰器测试失败！" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
    Write-Host ""

    # 测试2：Authentication IOC集成
    Write-Host "[3/3] 测试Authentication IOC集成..." -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Gray
    python tests\ioc\test_authentication_ioc.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ Authentication IOC测试失败！" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "                        ✅ 所有核心测试通过！" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "测试报告：" -ForegroundColor Cyan
    Write-Host "  [✅] Bean装饰器灵活性测试" -ForegroundColor Green
    Write-Host "  [✅] Authentication IOC集成测试" -ForegroundColor Green
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""

} finally {
    Pop-Location
}
