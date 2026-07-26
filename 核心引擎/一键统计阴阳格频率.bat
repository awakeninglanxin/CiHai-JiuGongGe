@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   阴阳格频率统计工具
echo   日期范围: 见 config_grid_count.py
echo ============================================================
echo.
echo 正在计算阳格和阴格的数字组合出现频率...
echo.
python batch_grid_count.py
echo.
echo [DONE] 结果已保存到 ..\grid_frequency_data.json
echo        查看汇总: python view_grid_stats.py
echo.
pause
