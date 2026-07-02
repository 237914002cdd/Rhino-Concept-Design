@echo off
REM ========================================
REM AI 建筑概念顾问 - 一键方案生成
REM ========================================
echo.
echo ========================================
echo   AI Architectural Concept Design Engine
echo ========================================
echo.

REM 检查输入文件
if not exist "01_Brief\project_brief.txt" (
    echo [ERROR] Missing 01_Brief/project_brief.txt
    echo Please place the project brief in 01_Brief/ folder.
    pause
    exit /b 1
)

echo [1/4] Reading project brief...
echo  > 02_Intelligence\brief_parsed.txt

echo [2/4] Running area balance calculation...
REM Run balance.py with project parameters
"D:\claude code mode\Python312\python.exe" "D:\claude code mode\files\balance.py" > 02_Intelligence\area_balance_report.txt 2>&1
echo  Done.

echo [3/4] Running code compliance validation...
"D:\claude code mode\Python312\python.exe" "D:\claude code mode\files\validate.py" > 04_Report\code_compliance_report.txt 2>&1
echo  Done.

echo [4/4] Generating Rhino model...
REM This step invokes Claude + Rhino MCP to generate 3D massing
REM (requires Rhino running with MCP server active)
echo  Note: Open Rhino and ensure MCP server is running (mcpstart)
echo  Then run Claude to read .rhino-rules.md and generate schemes.

echo.
echo ========================================
echo   Generation complete!
echo   Output files:
echo     02_Intelligence/area_balance_report.txt
echo     04_Report/code_compliance_report.txt
echo     03_Geometry/ (Rhino model files)
echo ========================================
echo.
pause
