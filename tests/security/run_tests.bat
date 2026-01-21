@echo off
REM PySpring Security 测试运行器
REM 自动设置UTF-8编码以正确显示中文

REM 设置Python IO编码为UTF-8
set PYTHONIOENCODING=utf-8

REM 切换控制台代码页到UTF-8
chcp 65001 > nul

cd /d %~dp0\..\..

echo.
echo ================================================================================
echo PySpring Security 测试套件
echo ================================================================================
echo.

REM 运行所有测试
python tests\security\run_all_tests.py

echo.
echo 按任意键退出...
pause > nul
