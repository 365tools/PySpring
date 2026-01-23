#!/bin/bash
# PySpring 发布脚本（Linux/macOS）
# 用法：./scripts/publish.sh [test|prod]

set -e

TARGET=${1:-test}

if [[ "$TARGET" != "test" && "$TARGET" != "prod" ]]; then
    echo "用法: $0 [test|prod]"
    exit 1
fi

echo "====================================="
echo "  PySpring 发布脚本"
echo "  目标: $TARGET"
echo "====================================="
echo ""

# 步骤 1: 检查 Git 状态
echo "[1/7] 检查 Git 状态..."
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

# 步骤 2: 读取版本号
echo "[2/7] 读取版本号..."
VERSION=$(grep -oP 'version\s*=\s*"\K[^"]+' pyproject.toml)
if [[ -z "$VERSION" ]]; then
    echo "❌ 无法读取版本号"
    exit 1
fi
echo "✅ 当前版本: $VERSION"
echo ""

# 步骤 3: 运行测试
echo "[3/7] 运行测试..."
pytest tests/ -v || {
    echo "❌ 测试失败"
    exit 1
}
echo "✅ 测试通过"
echo ""

# 步骤 4: 清理并构建
echo "[4/7] 清理旧构建并重新构建..."
rm -rf dist/ build/ *.egg-info
python -m build || {
    echo "❌ 构建失败"
    exit 1
}
echo "✅ 构建完成"
echo ""

# 步骤 5: 检查包
echo "[5/7] 检查包完整性..."
twine check dist/* || {
    echo "❌ 包检查失败"
    exit 1
}

# 检查模板文件
echo "检查模板文件是否包含..."
WHEEL_FILE=$(ls dist/*.whl | head -n 1)
if [[ -n "$WHEEL_FILE" ]]; then
    unzip -l "$WHEEL_FILE" | grep "templates/example" > /dev/null
    if [[ $? -eq 0 ]]; then
        echo "✅ 模板文件已包含"
    else
        echo "❌ 模板文件未包含！请检查 pyproject.toml 配置"
        exit 1
    fi
else
    echo "❌ 未找到 wheel 文件"
    exit 1
fi
echo ""

# 步骤 6: 上传
if [[ "$TARGET" == "test" ]]; then
    echo "[6/7] 上传到 TestPyPI"
    echo ""
    echo "即将上传到 TestPyPI (测试环境)"
    echo "版本: $VERSION"
    echo ""
    read -p "确认上传? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消上传"
        exit 0
    fi
    
    twine upload --repository testpypi dist/* || {
        echo "❌ 上传失败"
        exit 1
    }
    
    echo "✅ 上传成功"
    echo ""
    echo "====================================="
    echo "  测试安装命令"
    echo "====================================="
    echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyspring==$VERSION"
    echo ""
    echo "uvx --from pyspring --index-url https://test.pypi.org/simple/ pyspring init test-project --example"
    
else
    echo "[6/7] 上传到 PyPI (正式环境)"
    echo ""
    echo "⚠️  警告: 即将上传到正式 PyPI！"
    echo "版本: $VERSION"
    echo "这是不可逆的操作！"
    echo ""
    read -p "确认上传到正式 PyPI? (输入 'yes' 确认): " -r
    echo
    if [[ "$REPLY" != "yes" ]]; then
        echo "取消上传"
        exit 0
    fi
    
    twine upload dist/* || {
        echo "❌ 上传失败"
        exit 1
    }
    
    echo "✅ 上传成功"
    echo ""
    
    # 步骤 7: 创建 Git 标签
    echo "[7/7] 创建 Git 标签..."
    git tag "v$VERSION"
    git push origin "v$VERSION"
    echo "✅ Git 标签创建完成"
    echo ""
    
    echo "====================================="
    echo "  发布完成！"
    echo "====================================="
    echo "包地址: https://pypi.org/project/pyspring/$VERSION/"
    echo ""
    echo "用户可以通过以下方式安装:"
    echo "  uvx --from pyspring pyspring init my-project --example"
    echo "  pipx install pyspring"
    echo "  pip install pyspring"
fi

echo ""
echo "🎉 全部完成！"
