# PySpring Example 项目修复脚本
# 解决 "function() argument 'code' must be code, not str" 错误

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "PySpring Example 项目修复脚本" -ForegroundColor Cyan  
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1：清理框架缓存
Write-Host "步骤 1/5: 清理 PySpring 框架缓存..." -ForegroundColor Yellow
Get-ChildItem -Path "src" -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Path "src" -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force
Write-Host "✅ 框架缓存已清理" -ForegroundColor Green
Write-Host ""

# 步骤2：清理构建产物
Write-Host "步骤 2/5: 清理构建产物..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "src/pyspring.egg-info") { Remove-Item -Recurse -Force "src/pyspring.egg-info" }
Write-Host "✅ 构建产物已清理" -ForegroundColor Green
Write-Host ""

# 步骤3：重新安装框架
Write-Host "步骤 3/5: 重新安装 PySpring 框架..." -ForegroundColor Yellow
pip uninstall -y pyspring
pip install -e .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 框架安装失败！" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 框架已重新安装" -ForegroundColor Green
Write-Host ""

# 步骤4：清理旧的 example 项目（可选）
$demoPath = "D:\Project\PycharmProjects\py-demo"
if (Test-Path $demoPath) {
    Write-Host "步骤 4/5: 发现旧的 py-demo 项目" -ForegroundColor Yellow
    $answer = Read-Host "是否删除并重新生成？(y/n)"
    if ($answer -eq "y" -or $answer -eq "Y") {
        Write-Host "正在清理 py-demo 项目缓存..." -ForegroundColor Yellow
        Get-ChildItem -Path $demoPath -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
        Get-ChildItem -Path $demoPath -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force
        
        Write-Host "正在删除 py-demo 项目..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $demoPath
        
        Write-Host "正在重新生成 py-demo 项目..." -ForegroundColor Yellow
        pyspring init py-demo
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ 项目生成失败！" -ForegroundColor Red
            exit 1
        }
        Write-Host "✅ py-demo 项目已重新生成" -ForegroundColor Green
    } else {
        Write-Host "⚠️  跳过重新生成，仅清理缓存" -ForegroundColor Yellow
        Get-ChildItem -Path $demoPath -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
        Get-ChildItem -Path $demoPath -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force
        Write-Host "✅ 缓存已清理" -ForegroundColor Green
    }
} else {
    Write-Host "步骤 4/5: 生成新的 py-demo 项目..." -ForegroundColor Yellow
    Set-Location "D:\Project\PycharmProjects"
    pyspring init py-demo
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 项目生成失败！" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ py-demo 项目已生成" -ForegroundColor Green
}
Write-Host ""

# 步骤5：验证修复
Write-Host "步骤 5/5: 验证修复..." -ForegroundColor Yellow
Write-Host "请手动运行以下命令测试：" -ForegroundColor Cyan
Write-Host "  cd D:\Project\PycharmProjects\py-demo" -ForegroundColor White
Write-Host "  pyspring db init" -ForegroundColor White
Write-Host "  pyspring run" -ForegroundColor White
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "修复完成！" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
