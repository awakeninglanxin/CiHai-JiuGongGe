@echo off
chcp 65001 > nul
set NAME=TEST1
set BIRTH=2002/02/11
set SHICHEN=子时
set GENDER=男
echo Config: %NAME% %BIRTH% %SHICHEN% %GENDER%
if "%SHICHEN%"=="子时" (
    echo Generating both reports...
    python 完整综合命理报告v3.9.py "%BIRTH%" "前子时" "%GENDER%" -n "%NAME%"
    python 食疗动功生成器v3.3.py "%BIRTH%" -s "前子时" -g "%GENDER%" -n "%NAME%"
    python 倪海厦中医建议生成器.py -n "%NAME%" -b "%BIRTH%" -t "前子时" -g "%GENDER%" -l "未知"
    python 完整综合命理报告v3.9.py "%BIRTH%" "后子时" "%GENDER%" -n "%NAME%"
    python 食疗动功生成器v3.3.py "%BIRTH%" -s "后子时" -g "%GENDER%" -n "%NAME%"
    python 倪海厦中医建议生成器.py -n "%NAME%" -b "%BIRTH%" -t "后子时" -g "%GENDER%" -l "未知"
) else (
    echo Generating single report...
    python 完整综合命理报告v3.9.py "%BIRTH%" "%SHICHEN%" "%GENDER%" -n "%NAME%"
)
echo Done
