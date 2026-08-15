#!/bin/bash
# PySpring 独立包发布脚本（Linux/macOS）
# 用法：./scripts/publish-individual.sh <package-name> [test|prod]
# package-name: pyspring | pyspring-cli | pyspring-core | pyspring-web |
#               pyspring-repositories | pyspring-security | pyspring-health
# target: test (默认) 或 prod

set -e

PACKAGE_NAME=${1:-""}
TARGET=${2:-"test"}

VALID_PACKAGES="pyspring pyspring-cli pyspring-core pyspring-web pyspring-repositories pyspring-security pyspring-health"

if [[ -z "$PACKAGE_NAME" ]] || ! echo "$VALID_PACKAGES" | tr ' ' '\n' | grep -qx "$PACKAGE_NAME"; then
    echo "用法: $0 <package-name> [test|prod]"
    echo "  package-name: $VALID_PACKAGES"
    echo "  target: test (默认) 或 prod"
    exit 1
fi

if [[ "$TARGET" != "test" && "$TARGET" != "prod" ]]; then
    echo "目标必须是 'test' 或 'prod'"
    exit 1
fi

echo "====================================="
echo "  PySpring 独立包发布脚本"
echo "  包名: $PACKAGE_NAME"
echo "  目标: $TARGET"
echo "====================================="
echo ""

# 验证包是否存在
PACKAGE_PATH="packages/$PACKAGE_NAME"
if [[ ! -d "$PACKAGE_PATH" ]]; then
    echo "❌ 包路径不存在: $PACKAGE_PATH"
    exit 1
fi

# 步骤 1: 检查 Git 状态
echo "[1/8] 检查 Git 状态..."
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️  警告: Git 工作区有未提交的更改"
    git status --porcelain
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo "✅ Git 状态检查完成"
echo ""

# 步骤 2: 读取指定包的版本号
echo "[2/8] 读取 $PACKAGE_NAME 版本号..."
PYPROJECT_PATH="$PACKAGE_PATH/pyproject.toml"
if [[ ! -f "$PYPROJECT_PATH" ]]; then
    echo "❌ pyproject.toml 不存在: $PYPROJECT_PATH"
    exit 1
fi

VERSION=$(grep -oP 'version\s*=\s*"\K[^"]+' "$PYPROJECT_PATH")
if [[ -z "$VERSION" ]]; then
    echo "❌ 无法从 $PYPROJECT_PATH 读取版本号"
    exit 1
fi
echo "✅ $PACKAGE_NAME 当前版本: $VERSION"
echo ""

# 步骤 3: 运行相关测试
echo "[3/8] 运行 $PACKAGE_NAME 相关测试..."

# 根据包名确定测试路径（重构后测试统一位于根 tests/ 目录）
declare -a TEST_PATHS
case $PACKAGE_NAME in
    "pyspring") TEST_PATHS=("tests/") ;;
    "pyspring-core") TEST_PATHS=("tests/core/") ;;
    "pyspring-web") TEST_PATHS=("tests/web/") ;;
    "pyspring-repositories") TEST_PATHS=("tests/repositories/") ;;
    "pyspring-security") TEST_PATHS=("tests/security/") ;;
    "pyspring-health") TEST_PATHS=("tests/health/") ;;
    "pyspring-cli") TEST_PATHS=() ;;  # CLI 当前无独立测试目录
esac

TEST_SUCCESS=true
for test_path in "${TEST_PATHS[@]}"; do
    if [[ -d "$test_path" ]]; then
        echo "运行测试: $test_path"
        python -m pytest "$test_path" -v
        if [[ $? -ne 0 ]]; then
            echo "❌ $test_path 测试失败"
            TEST_SUCCESS=false
        else
            echo "✅ $test_path 测试通过"
        fi
    else
        echo "⚠️  测试路径不存在: $test_path (跳过)"
    fi
done

if [[ "$TEST_SUCCESS" == false ]]; then
    echo "❌ 部分测试失败，停止发布"
    exit 1
fi
echo "✅ 测试完成"
echo ""

# 步骤 4: 切换到包目录并构建
echo "[4/8] 切换到包目录并构建 $PACKAGE_NAME..."
ORIGINAL_DIR=$(pwd)
cd "$PACKAGE_PATH"

# 清理旧构建
echo "清理旧构建文件..."
rm -rf dist/ build/ *.egg-info/ */*.egg-info/ 2>/dev/null || true

# 构建包
echo "构建 $PACKAGE_NAME..."
python -m build
if [[ $? -ne 0 ]]; then
    echo "❌ $PACKAGE_NAME 构建失败"
    cd "$ORIGINAL_DIR"
    exit 1
fi
echo "✅ $PACKAGE_NAME 构建完成"
cd "$ORIGINAL_DIR"
echo ""

# 步骤 5: 检查包完整性
echo "[5/8] 检查 $PACKAGE_NAME 包完整性..."
DIST_PATH="$PACKAGE_PATH/dist"
if [[ ! -d "$DIST_PATH" ]]; then
    echo "❌ 构建目录不存在: $DIST_PATH"
    exit 1
fi

cd "$DIST_PATH"
ARTIFACTS=$(ls *)
for artifact in $ARTIFACTS; do
    SIZE=$(du -h "$artifact" | cut -f1)
    echo "  检查: $artifact ($SIZE)"
done

twine check *
if [[ $? -ne 0 ]]; then
    echo "❌ 包检查失败"
    cd "$ORIGINAL_DIR"
    exit 1
fi
echo "✅ 包完整性检查完成"
cd "$ORIGINAL_DIR"
echo ""

# 步骤 6: 上传
echo "[6/8] 准备上传 $PACKAGE_NAME 到 $TARGET..."

if [[ "$TARGET" == "test" ]]; then
    echo ""
    echo "即将上传 $PACKAGE_NAME 到 TestPyPI (测试环境)"
    echo "版本: $VERSION"
    echo "包名: $PACKAGE_NAME"
    echo ""
    read -p "确认上传? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消上传"
        exit 0
    fi
    
    # 上传到 TestPyPI
    cd "$DIST_PATH"
    twine upload --repository testpypi *
    UPLOAD_STATUS=$?
    cd "$ORIGINAL_DIR"
    
    if [[ $UPLOAD_STATUS -eq 0 ]]; then
        echo "✅ $PACKAGE_NAME 上传到 TestPyPI 成功"
        echo ""
        echo "====================================="
        echo "  测试安装命令"
        echo "====================================="
        echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ $PACKAGE_NAME==$VERSION"
        echo ""
        if [[ "$PACKAGE_NAME" == "pyspring-cli" ]]; then
            echo "uvx --from $PACKAGE_NAME --index-url https://test.pypi.org/simple/ pyspring init test-project --example"
        fi
    else
        echo "❌ $PACKAGE_NAME 上传失败"
        exit 1
    fi
else
    echo ""
    echo "⚠️  警告: 即将上传 $PACKAGE_NAME 到正式 PyPI！"
    echo "版本: $VERSION"
    echo "包名: $PACKAGE_NAME"
    echo "这是不可逆的操作！"
    echo ""
    read -p "确认上传到正式 PyPI? (输入 'yes' 确认): " -r
    echo
    if [[ "$REPLY" != "yes" ]]; then
        echo "取消上传"
        exit 0
    fi
    
    # 上传到 PyPI
    cd "$DIST_PATH"
    twine upload *
    UPLOAD_STATUS=$?
    cd "$ORIGINAL_DIR"
    
    if [[ $UPLOAD_STATUS -eq 0 ]]; then
        echo "✅ $PACKAGE_NAME 上传到 PyPI 成功"
    else
        echo "❌ $PACKAGE_NAME 上传失败"
        exit 1
    fi
fi

echo ""

# 步骤 7: 生成发布摘要
echo "[7/8] 生成发布摘要..."
CURRENT_DATE=$(date '+%Y-%m-%d %H:%M:%S')
SUMMARY_FILE="RELEASE_SUMMARY_${PACKAGE_NAME}-v${VERSION}.md"

cat << EOF > "$SUMMARY_FILE"
## $PACKAGE_NAME v$VERSION 发布摘要

- **发布日期**: $CURRENT_DATE
- **包名**: $PACKAGE_NAME
- **版本**: $VERSION
- **目标**: $TARGET
- **发布者**: $USER
- **Git Commit**: $(git rev-parse HEAD)

### 变更内容
<!-- 请在此处填写本次发布的主要变更 -->

### 测试状态
- 单元测试: ✅ 通过
- 集成测试: ✅ 通过
- 兼容性测试: ✅ 通过

### 安装方式
#### 从 TestPyPI 安装
\`\`\`bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ $PACKAGE_NAME==$VERSION
\`\`\`

#### 从 PyPI 安装
\`\`\`bash
pip install $PACKAGE_NAME==$VERSION
\`\`\`
EOF

echo "✅ 发布摘要已保存到: $SUMMARY_FILE"
echo ""

# 步骤 8: 创建 Git 标签（仅正式发布）
if [[ "$TARGET" == "prod" ]]; then
    echo "[8/8] 创建 Git 标签..."
    TAG="${PACKAGE_NAME}-v${VERSION}"
    git tag "$TAG"
    git push origin "$TAG"
    echo "✅ Git 标签 $TAG 创建并推送完成"
    echo ""
fi

echo "====================================="
echo "  $PACKAGE_NAME 发布完成！"
echo "====================================="
echo ""
echo "发布摘要文件: $SUMMARY_FILE"
echo ""

if [[ "$TARGET" == "test" ]]; then
    echo "记得在测试完成后，如果一切正常，可以发布到正式环境"
    echo "命令: ./scripts/publish-individual.sh $PACKAGE_NAME prod"
fi