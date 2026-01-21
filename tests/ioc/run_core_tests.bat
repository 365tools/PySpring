@echo off
REM IOC 核心测试运行脚本
REM 运行Bean装饰器和Authentication IOC测试

cd /d %~dp0..\..

echo.
echo ================================================================================
echo                         PySpring IOC 核心测试套件
echo ================================================================================
echo.

REM 清除Python缓存
echo [1/3] 清除Python缓存...
for /d /r src %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo      ✅ 缓存已清除
echo.

REM 测试1：Bean装饰器灵活性
echo [2/3] 测试Bean装饰器灵活性...
echo ================================================================================
python tests\ioc\test_bean_decorator_flexible.py
if errorlevel 1 (
    echo.
    echo ❌ Bean装饰器测试失败！
    pause
    exit /b 1
)
echo.
echo.

REM 测试2：Authentication IOC集成
echo [3/3] 测试Authentication IOC集成...
echo ================================================================================
python tests\ioc\test_authentication_ioc.py
if errorlevel 1 (
    echo.
    echo ❌ Authentication IOC测试失败！
    pause
    exit /b 1
)

echo.
echo.
echo ================================================================================
echo                         ✅ 所有核心测试通过！
echo ================================================================================
echo.
echo 测试报告：
echo   [✅] Bean装饰器灵活性测试
echo   [✅] Authentication IOC集成测试
echo.
echo ================================================================================
echo.

pause
