@echo off
setlocal
chcp 65001 >nul
set "X2STOCK_APP=%~dp0desktop-runtime\win-x64\x2Stock.exe"
if not exist "%X2STOCK_APP%" (
  if exist "%~dp0desktop-runtime\.recovery\x2Stock.exe" (
    start "" /D "%~dp0desktop-runtime\.recovery" "%~dp0desktop-runtime\.recovery\x2Stock.exe" --x2stock-recover
    exit /b 0
  )
  echo 未找到 x2Stock 程序，请完整下载项目和 desktop-runtime 目录。
  echo x2Stock executable is missing. Download the complete project and runtime.
  pause
  exit /b 1
)
start "" /D "%~dp0desktop-runtime\win-x64" "%X2STOCK_APP%"
endlocal
exit /b 0
