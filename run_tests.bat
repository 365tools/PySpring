@echo off
REM 运行 PySpring 全部测试（pytest）
python -m pytest tests/ %*
