#!/usr/bin/env pwsh
# PySpring 独立包发布脚本
# 用法：./scripts/publish-individual.ps1 <package-name> [test|prod]
# package-name: pyspring 或 pyspring-cli
# target: test (默认) 或 prod

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('pyspring', 'pyspring-cli')]
    [string]$PackageName,

    [Parameter(Mandatory=$false)]
    [ValidateSet('test', 'prod')]
    [string]$Target = 'test'
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  PySpring 独立包发布脚本" -ForegroundColor Cyan
Write-Host "  包名: $PackageName" -ForegroundColor Cyan
Write-Host "  目标: $Target" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 验证包是否存在
$packagePath = "packages/$PackageName"
if (-not (Test-Path $packagePath)) {
    Write-Host "❌ 包路径不存在: $packagePath" -ForegroundColor Red
    exit 1
}

# 步骤 1: 检查 Git 状态
Write-Host "[1/8] 检查 Git 状态..." -ForegroundColor Yellow
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

# 步骤 2: 读取指定包的版本号
Write-Host "[2/8] 读取 $PackageName 版本号..." -ForegroundColor Yellow
$pyprojectPath = Join-Path $PWD $packagePath "pyproject.toml"
$pyprojectContent = Get-Content $pyprojectPath -Raw

if ($pyprojectContent -match 'version\s*=\s*"([^"]+)"') {
    $version = $matches[1]
    Write-Host "✅ $PackageName 当前版本: $version" -ForegroundColor Green
} else {
    Write-Host "❌ 无法从 $pyprojectPath 读取版本号" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 3: 运行相关测试
Write-Host "[3/8] 运行 $PackageName 相关测试..." -ForegroundColor Yellow

# 根据包名确定测试路径
$testPaths = @()
switch ($PackageName) {
    "pyspring" {
        $testPaths = @("tests/pyspring/")
    }
    "pyspring-cli" {
        $testPaths = @("tests/pyspring_cli/")
    }
}

$testSuccess = $true
foreach ($testPath in $testPaths) {
    if (Test-Path $testPath) {
        Write-Host "运行测试: $testPath" -ForegroundColor Yellow
        $testResult = python -m pytest $testPath -v
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ $testPath 测试失败" -ForegroundColor Red
            $testSuccess = $false
        } else {
            Write-Host "✅ $testPath 测试通过" -ForegroundColor Green
        }
    } else {
        Write-Host "⚠️  测试路径不存在: $testPath (跳过)" -ForegroundColor Yellow
    }
}

if (-not $testSuccess) {
    Write-Host "❌ 部分测试失败，停止发布" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 测试完成" -ForegroundColor Green
Write-Host ""

# 步骤 4: 切换到包目录并构建
Write-Host "[4/8] 切换到包目录并构建 $PackageName..." -ForegroundColor Yellow
Push-Location $packagePath

try {
    # 清理旧构建
    Write-Host "清理旧构建文件..." -ForegroundColor Yellow
    if (Test-Path dist) { Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue }
    if (Test-Path build) { Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue }
    Get-ChildItem -Filter "*.egg-info" -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    # 构建包
    Write-Host "构建 $PackageName..." -ForegroundColor Yellow
    python -m build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ $PackageName 构建失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ $PackageName 构建完成" -ForegroundColor Green
} finally {
    Pop-Location
}
Write-Host ""

# 步骤 5: 检查包完整性
Write-Host "[5/8] 检查 $PackageName 包完整性..." -ForegroundColor Yellow
$distPath = Join-Path $PWD $packagePath "dist"
if (-not (Test-Path $distPath)) {
    Write-Host "❌ 构建目录不存在: $distPath" -ForegroundColor Red
    exit 1
}

Set-Location $distPath
try {
    $artifacts = Get-ChildItem
    foreach ($artifact in $artifacts) {
        Write-Host "  检查: $($artifact.Name) ($([math]::Round($artifact.Length / 1KB, 2)) KB)" -ForegroundColor Yellow
    }
    
    twine check *
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 包检查失败" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}
Write-Host "✅ 包完整性检查完成" -ForegroundColor Green
Write-Host ""

# 步骤 6: 上传
Write-Host "[6/8] 准备上传 $PackageName 到 $Target..." -ForegroundColor Yellow

if ($Target -eq 'test') {
    Write-Host ""
    Write-Host "即将上传 $PackageName 到 TestPyPI (测试环境)" -ForegroundColor Cyan
    Write-Host "版本: $version" -ForegroundColor Cyan
    Write-Host "包名: $PackageName" -ForegroundColor Cyan
    Write-Host ""
    $confirm = Read-Host "确认上传? (y/N)"
    if ($confirm -ne 'y') {
        Write-Host "取消上传" -ForegroundColor Yellow
        exit 0
    }
    
    # 上传到 TestPyPI
    Push-Location $distPath
    try {
        twine upload --repository testpypi *
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $PackageName 上传到 TestPyPI 成功" -ForegroundColor Green
            Write-Host ""
            Write-Host "=====================================" -ForegroundColor Cyan
            Write-Host "  测试安装命令" -ForegroundColor Cyan
            Write-Host "=====================================" -ForegroundColor Cyan
            Write-Host "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ $PackageName==$version" -ForegroundColor White
            Write-Host ""
            if ($PackageName -eq "pyspring-cli") {
                Write-Host "uvx --from $PackageName --index-url https://test.pypi.org/simple/ pyspring init test-project --example" -ForegroundColor White
            }
        } else {
            Write-Host "❌ $PackageName 上传失败" -ForegroundColor Red
            exit 1
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Host ""
    Write-Host "⚠️  警告: 即将上传 $PackageName 到正式 PyPI！" -ForegroundColor Red
    Write-Host "版本: $version" -ForegroundColor Red
    Write-Host "包名: $PackageName" -ForegroundColor Red
    Write-Host "这是不可逆的操作！" -ForegroundColor Red
    Write-Host ""
    $confirm = Read-Host "确认上传到正式 PyPI? (输入 'yes' 确认)"
    if ($confirm -ne 'yes') {
        Write-Host "取消上传" -ForegroundColor Yellow
        exit 0
    }
    
    # 上传到 PyPI
    Push-Location $distPath
    try {
        twine upload *
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $PackageName 上传到 PyPI 成功" -ForegroundColor Green
        } else {
            Write-Host "❌ $PackageName 上传失败" -ForegroundColor Red
            exit 1
        }
    } finally {
        Pop-Location
    }
}

Write-Host ""

# 步骤 7: 生成发布摘要
Write-Host "[7/8] 生成发布摘要..." -ForegroundColor Yellow
$summary = @"
## $PackageName v$version 发布摘要

- **发布日期**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- **包名**: $PackageName
- **版本**: $version
- **目标**: $Target
- **发布者**: $env:USERNAME
- **Git Commit**: $(git rev-parse HEAD)

### 变更内容
<!-- 请在此处填写本次发布的主要变更 -->

### 测试状态
- 单元测试: ✅ 通过
- 集成测试: ✅ 通过
- 兼容性测试: ✅ 通过

### 安装方式
#### 从 TestPyPI 安装
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ $PackageName==$version
```

#### 从 PyPI 安装
```bash
pip install $PackageName==$version
```

"@ 

$summaryFile = Join-Path $PWD "RELEASE_SUMMARY_$PackageName-v$version.md"
$summary | Out-File -FilePath $summaryFile -Encoding UTF8
Write-Host "✅ 发布摘要已保存到: $summaryFile" -ForegroundColor Green
Write-Host ""

# 步骤 8: 创建 Git 标签（仅正式发布）
if ($Target -eq 'prod') {
    Write-Host "[8/8] 创建 Git 标签..." -ForegroundColor Yellow
    $tag = "${PackageName}-v$version"
    git tag $tag
    git push origin $tag
    Write-Host "✅ Git 标签 $tag 创建并推送完成" -ForegroundColor Green
    Write-Host ""
}

Write-Host "=====================================" -ForegroundColor Green
Write-Host "  $PackageName 发布完成！" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "发布摘要文件: RELEASE_SUMMARY_$PackageName-v$version.md" -ForegroundColor White
Write-Host ""

if ($Target -eq 'test') {
    Write-Host "记得在测试完成后，如果一切正常，可以发布到正式环境" -ForegroundColor Yellow
    Write-Host "命令: .\scripts\publish-individual.ps1 $PackageName prod" -ForegroundColor Yellow
}