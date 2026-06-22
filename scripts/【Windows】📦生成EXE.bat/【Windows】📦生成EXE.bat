@echo off
rem 脚本自述：双击检查 Windows Python 构建环境，按需安装依赖，并使用 PyInstaller 生成自包含 JobsAppTrafficMonitor.exe。
setlocal EnableExtensions
chcp 65001 >nul

rem 定位脚本目录与项目根目录。
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%\..\..") do set "PROJECT_ROOT=%%~fI"
set "BUILD_VENV=%PROJECT_ROOT%\build\windows-venv"
set "DIST_DIR=%PROJECT_ROOT%\dist\windows"

rem 打印写死在脚本内部的自述，避免依赖外部 README。
echo ============================== Script Intro ==============================
echo Script: %~f0
echo Purpose: Build a self-contained JobsAppTrafficMonitor.exe for Windows.
echo Impact: May install Python with winget and download PySide6/PyInstaller into build\windows-venv.
echo Output: dist\windows\JobsAppTrafficMonitor.exe
echo Cancel: Close this window before continuing if you do not accept these changes.
echo ========================================================================
echo.
pause

rem 优先使用 Python Launcher，其次使用 PATH 内的 python。
where py >nul 2>nul
if not errorlevel 1 (
  set "PYTHON_LAUNCHER=py -3"
)
if not defined PYTHON_LAUNCHER (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_LAUNCHER=python"
)

rem 缺少 Python 时通过 winget 安装官方 Python 3.13。
if not defined PYTHON_LAUNCHER (
  echo [INFO] Python missing. Installing with winget...
  where winget >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] winget is unavailable. Install Python 3.11+ and run this script again.
    pause
    exit /b 1
  )
  winget install --id Python.Python.3.13 --exact --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (
    echo [ERROR] Python installation failed.
    pause
    exit /b 1
  )
  set "PYTHON_LAUNCHER=py -3"
)

rem 自动创建内部构建环境，用户无需手动执行 Python 安装命令。
if not exist "%BUILD_VENV%\Scripts\python.exe" (
  call %PYTHON_LAUNCHER% -m venv "%BUILD_VENV%"
  if not %errorlevel%==0 goto :build_failed
)

rem 安装或更新构建环境中的 PySide6 与 PyInstaller。
call "%BUILD_VENV%\Scripts\python.exe" -m pip install --upgrade pip PySide6 pyinstaller
if not %errorlevel%==0 goto :build_failed

rem 使用 PyInstaller 生成单文件 Windows EXE。
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
if not exist "%PROJECT_ROOT%\build\pyinstaller-windows" mkdir "%PROJECT_ROOT%\build\pyinstaller-windows"
if not exist "%PROJECT_ROOT%\build\pyinstaller-spec-windows" mkdir "%PROJECT_ROOT%\build\pyinstaller-spec-windows"
call "%BUILD_VENV%\Scripts\python.exe" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name JobsAppTrafficMonitor ^
  --paths "%PROJECT_ROOT%\src" ^
  --workpath "%PROJECT_ROOT%\build\pyinstaller-windows" ^
  --specpath "%PROJECT_ROOT%\build\pyinstaller-spec-windows" ^
  --distpath "%DIST_DIR%" ^
  "%PROJECT_ROOT%\src\jobs_app_traffic_monitor\__main__.py"
if not %errorlevel%==0 goto :build_failed

echo [OK] EXE generated: %DIST_DIR%\JobsAppTrafficMonitor.exe
explorer /select,"%DIST_DIR%\JobsAppTrafficMonitor.exe"
pause
exit /b 0

:build_failed
echo [ERROR] Build failed. Review the terminal output above.
pause
exit /b 1
