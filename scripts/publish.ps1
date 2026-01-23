# PySpring 发布脚本
# 用法：./scripts/publish.ps1 [test|prod]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('test', 'prod')]
    [string]$Target = 'test'
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  PySpring 发布脚本" -ForegroundColor Cyan
Write-Host "  目标: $Target" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 检查 Git 状态
Write-Host "[1/7] 检查 Git 状态..." -ForegroundColor Yellow
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "⚠️  警告: Git 工作区有未提交的更改" -ForegroundColor Red
    Write-Host $gitStatus
    $continue = Read-Host "是否继续? (y/N)"
    if ($continue -ne 'y') {
        exit 1
    }
}
Write-Host "✅ Git 状态检查完成" -ForegroundColor Green
Write-Host ""

# 步骤 2: 读取版本号
Write-Host "[2/7] 读取版本号..." -ForegroundColor Yellow
$pyprojectContent = Get-Content pyproject.toml -Raw
if ($pyprojectContent -match 'version\s*=\s*"([^"]+)"') {
    $version = $matches[1]
    Write-Host "✅ 当前版本: $version" -ForegroundColor Green
} else {
    Write-Host "❌ 无法读取版本号" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 3: 运行测试
Write-Host "[3/7] 运行测试..." -ForegroundColor Yellow
pytest tests/ -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 测试失败" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 测试通过" -ForegroundColor Green
Write-Host ""

# 步骤 4: 清理并构建
Write-Host "[4/7] 清理旧构建并重新构建..." -ForegroundColor Yellow
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }
Get-ChildItem -Filter "*.egg-info" -Recurse | Remove-Item -Recurse -Force

python -m build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 构建失败" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 构建完成" -ForegroundColor Green
Write-Host ""

# 步骤 5: 检查包
Write-Host "[5/7] 检查包完整性..." -ForegroundColor Yellow
twine check dist/*
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 包检查失败" -ForegroundColor Red
    exit 1
}

# 检查模板文件
Write-Host "检查模板文件是否包含..." -ForegroundColor Yellow
$wheelFile = Get-ChildItem dist/*.whl | Select-Object -First 1
if ($wheelFile) {
    $tempDir = New-Item -ItemType Directory -Path "temp_check" -Force
    Expand-Archive -Path $wheelFile.FullName -DestinationPath $tempDir -Force
    
    $hasTemplates = Test-Path "$tempDir/pyspring/templates/example"
    Remove-Item -Recurse -Force $tempDir
    
    if ($hasTemplates) {
        Write-Host "✅ 模板文件已包含" -ForegroundColor Green
    } else {
        Write-Host "❌ 模板文件未包含！请检查 pyproject.toml 配置" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ 未找到 wheel 文件" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 6: 上传
Write-Host "[6/7] 上传到 " -NoNewline -ForegroundColor Yellow
if ($Target -eq 'test') {
    Write-Host "TestPyPI" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "即将上传到 TestPyPI (测试环境)" -ForegroundColor Cyan
    Write-Host "版本: $version" -ForegroundColor Cyan
    Write-Host ""
    $confirm = Read-Host "确认上传? (y/N)"
    if ($confirm -ne 'y') {
        Write-Host "取消上传" -ForegroundColor Yellow
        exit 0
    }
    
    twine upload --repository testpypi dist/*
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 上传成功" -ForegroundColor Green
        Write-Host ""
        Write-Host "=====================================" -ForegroundColor Cyan
        Write-Host "  测试安装命令" -ForegroundColor Cyan
        Write-Host "=====================================" -ForegroundColor Cyan
        Write-Host "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyspring==$version" -ForegroundColor White
        Write-Host ""
        Write-Host "uvx --from pyspring --index-url https://test.pypi.org/simple/ pyspring init test-project --example" -ForegroundColor White
    }
    
} else {
    Write-Host "PyPI (正式环境)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "⚠️  警告: 即将上传到正式 PyPI！" -ForegroundColor Red
    Write-Host "版本: $version" -ForegroundColor Red
    Write-Host "这是不可逆的操作！" -ForegroundColor Red
    Write-Host ""
    $confirm = Read-Host "确认上传到正式 PyPI? (yes/N)"
    if ($confirm -ne 'yes') {
        Write-Host "取消上传" -ForegroundColor Yellow
        exit 0
    }
    
    twine upload dist/*
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 上传成功" -ForegroundColor Green
        Write-Host ""
        
        # 步骤 7: 创建 Git 标签
        Write-Host "[7/7] 创建 Git 标签..." -ForegroundColor Yellow
        git tag "v$version"
        git push origin "v$version"
        Write-Host "✅ Git 标签创建完成" -ForegroundColor Green
        Write-Host ""
        
        Write-Host "=====================================" -ForegroundColor Cyan
        Write-Host "  发布完成！" -ForegroundColor Cyan
        Write-Host "=====================================" -ForegroundColor Cyan
        Write-Host "包地址: https://pypi.org/project/pyspring/$version/" -ForegroundColor White
        Write-Host ""
        Write-Host "用户可以通过以下方式安装:" -ForegroundColor White
        Write-Host "  uvx --from pyspring pyspring init my-project --example" -ForegroundColor Cyan
        Write-Host "  pipx install pyspring" -ForegroundColor Cyan
        Write-Host "  pip install pyspring" -ForegroundColor Cyan
    }
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 上传失败" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 全部完成！" -ForegroundColor Green
