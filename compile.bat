@echo off
title RBWR Overlay Compiler
echo ==================================================
echo       RBWR OVERLAY EXECUTABLE COMPILER (NUITKA)
echo ==================================================
echo.

:: Step 1: Check and install compilation dependencies
echo [1/3] Ensuring required packages are installed...

if exist "venv\Scripts\activate.bat" (
    echo [INFO] Local virtual environment [venv] detected. Activating...
    call venv\Scripts\activate.bat
)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to install required Python packages!
    echo Please make sure Python is installed and added to PATH.
    pause
    exit /b %ERRORLEVEL%
)
echo.

:: Free file locks by terminating any running instances of rbwr_overlay
echo [1.5/3] Freeing file locks from any running overlay instances...
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*rbwr_overlay*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
if exist "rbwr_overlay.build" rmdir /s /q "rbwr_overlay.build" >nul 2>&1
if exist "rbwr_overlay.onefile-build" rmdir /s /q "rbwr_overlay.onefile-build" >nul 2>&1
echo [OK] All file locks freed successfully.
echo.

:: Step 2: Generate default icons programmatically before compiling
echo [2/3] Generating default custom icons...
python -c "import rbwr_overlay; rbwr_overlay.generate_default_icon()"
if not exist "icon.ico" (
    echo [WARN] Custom icon.ico not found, compilation will proceed with fallback icon.
) else (
    echo [OK] High-quality custom icons loaded successfully.
)
echo.

:: Step 3: Trigger Nuitka high-fidelity compilation
echo [3/3] Compiling to a high-speed, single-file GUI executable...
echo       - Mode: Standalone ^& One-File
echo       - Console: Attach (runs silently in GUI mode)
echo       - CPU cores: Utilizing ALL threads (--jobs=%NUMBER_OF_PROCESSORS%)
echo.

nuitka --standalone --onefile --windows-console-mode=attach --windows-icon-from-ico=icon.ico --jobs=%NUMBER_OF_PROCESSORS% --enable-plugin=tk-inter --include-package=rapidocr_onnxruntime --include-package-data=rapidocr_onnxruntime rbwr_overlay.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo [OK] Executable compiled successfully. Running automatic version updater and deployer...
    python update_version.py
    echo.
    echo ==================================================
    echo COMPILATION COMPLETED SUCCESSFULLY!
    echo The compiled executable is in: D:\workspace\rbwr_apr_overlay\rbwr_overlay.exe
    echo ==================================================
) else (
    echo.
    echo ==================================================
    echo COMPILATION FAILED!
    echo Please verify that a C/C++ compiler (e.g. MSVC or MinGW) is installed.
    echo ==================================================
)
pause
