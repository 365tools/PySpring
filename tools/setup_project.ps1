# PySpring 项目设置脚本（PowerShell）
# 自动创建虚拟环境并安装 PySpring

param(
    [string]$ProjectPath = ".",
    [switch]$DevMode = $false
)

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "PySpring 项目自动设置" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# 1. 检查项目路径
$ProjectPath = Resolve-Path $ProjectPath -ErrorAction SilentlyContinue
if (-not $ProjectPath) {
    Write-Host "❌ 项目路径不存在" -ForegroundColor Red
    exit 1
}

Write-Host "📁 项目路径: $ProjectPath" -ForegroundColor Cyan
Set-Location $ProjectPath

# 2. 检查 Python
Write-Host "`n🔍 检查 Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python 已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未找到 Python，请先安装 Python 3.12+" -ForegroundColor Red
    exit 1
}

# 3. 创建虚拟环境
Write-Host "`n🏗️  创建虚拟环境..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "⚠️  虚拟环境已存在，跳过创建" -ForegroundColor Yellow
} else {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 虚拟环境创建成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 虚拟环境创建失败" -ForegroundColor Red
        exit 1
    }
}

# 4. 激活虚拟环境
Write-Host "`n🚀 激活虚拟环境..." -ForegroundColor Yellow
& "$ProjectPath\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green
} else {
    Write-Host "❌ 虚拟环境激活失败" -ForegroundColor Red
    Write-Host "💡 提示: 如果遇到权限问题，请以管理员身份运行:" -ForegroundColor Yellow
    Write-Host "   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
    exit 1
}

# 5. 升级 pip
Write-Host "`n📦 升级 pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip -q
Write-Host "✅ pip 已升级" -ForegroundColor Green

# 6. 安装 PySpring
Write-Host "`n📥 安装 PySpring..." -ForegroundColor Yellow
if ($DevMode) {
    Write-Host "   模式: 开发模式（可编辑）" -ForegroundColor Cyan
    $pyspringPath = "D:\Project\PycharmProjects\PySpring"
    if (Test-Path $pyspringPath) {
        pip install -e $pyspringPath
    } else {
        Write-Host "⚠️  PySpring 源码路径不存在: $pyspringPath" -ForegroundColor Yellow
        Write-Host "   改为从 PyPI 安装..." -ForegroundColor Cyan
        pip install pyspring
    }
} else {
    Write-Host "   模式: 生产模式" -ForegroundColor Cyan
    pip install pyspring
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PySpring 安装成功" -ForegroundColor Green
} else {
    Write-Host "❌ PySpring 安装失败" -ForegroundColor Red
    exit 1
}

# 7. 运行诊断
Write-Host "`n🔍 运行诊断..." -ForegroundColor Yellow
Write-Host ""
pyspring diagnose

# 8. 总结
Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "✅ 设置完成！" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 后续步骤:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. 在 VS Code 中:" -ForegroundColor Cyan
Write-Host "   - Ctrl+Shift+P → 'Python: Select Interpreter'" -ForegroundColor White
Write-Host "   - 选择: .\venv\Scripts\python.exe" -ForegroundColor White
Write-Host "   - Ctrl+Shift+P → 'Developer: Reload Window'" -ForegroundColor White
Write-Host ""
Write-Host "2. 在 PyCharm 中:" -ForegroundColor Cyan
Write-Host "   - File → Settings → Project → Python Interpreter" -ForegroundColor White
Write-Host "   - 选择虚拟环境: $ProjectPath\venv\Scripts\python.exe" -ForegroundColor White
Write-Host "   - File → Invalidate Caches / Restart" -ForegroundColor White
Write-Host ""
Write-Host "3. 测试导入:" -ForegroundColor Cyan
Write-Host "   python -c `"from pyspring.log.loguru.ins import logger; print('✅ 成功!')`"" -ForegroundColor White
Write-Host ""
Write-Host "4. 初始化项目配置:" -ForegroundColor Cyan
Write-Host "   pyspring init" -ForegroundColor White
Write-Host ""
Write-Host "💡 提示: 虚拟环境已激活，现在可以开始开发了！" -ForegroundColor Green
Write-Host ""
