@echo off
setlocal enabledelayedexpansion

echo ====================================================
echo Checking for any existing instance of app.py...
echo ====================================================
rem Use WMIC to look for processes whose CommandLine contains "app.py"
for /f "skip=1 tokens=1" %%p in ('wmic process where "CommandLine like '%%app.py%%'" get ProcessId ^| findstr /r "[0-9]"') do (
    echo Terminating existing app.py process with PID %%p...
    taskkill /PID %%p /F >nul 2>&1
)

echo ====================================================
echo Checking for Python installation...
echo ====================================================

:: First, try to run "python --version" to see if Python is on PATH
python --version >nul 2>&1
if %errorlevel%==0 (
    echo Python is available on PATH.
    goto :checkPip
) else (
    echo Python not found on PATH. Checking common installation paths...
)

:: Initialize variable to hold found installation path
set "PYTHON_PATH="

:: Search common user installation directory (e.g., from the Python.org installer)
for /d %%a in ("%LocalAppData%\Programs\Python\*") do (
    if exist "%%a\python.exe" (
        set "PYTHON_PATH=%%a"
        goto :foundPython
    )
)

:: Optionally, search Program Files (if installed for all users)
for /d %%a in ("%ProgramFiles%\Python*") do (
    if exist "%%a\python.exe" (
        set "PYTHON_PATH=%%a"
        goto :foundPython
    )
)

:foundPython
if defined PYTHON_PATH (
    echo Found Python at: %PYTHON_PATH%
    echo Adding this directory to PATH.
    set "PATH=%PYTHON_PATH%;%PATH%"
    goto :checkPip
)

:: If no Python installation was found in common locations, ask the user to download/install it.
echo No Python installation found in common locations.
set /p USER_CHOICE="Do you want to download and install Python? (y/n): "
if /i "%USER_CHOICE%"=="y" (
    echo Downloading Python installer...
    rem Define a temporary location for the installer.
    set "PYTHON_INSTALLER=%TEMP%\python_installer.exe"
    rem Download the latest Python installer (update URL as needed)
    curl -L -o "%PYTHON_INSTALLER%" https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe
    if %errorlevel% neq 0 (
        echo Error downloading Python installer.
        goto :end
    )
    echo Installing Python for the current user...
    rem Install quietly for the current user and add to PATH (no admin rights)
    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1
    if %errorlevel% neq 0 (
        echo Error during Python installation.
        goto :end
    )
    del "%PYTHON_INSTALLER%"
    echo Python installation completed.
    rem Pause briefly to allow the installation to finalize
    timeout /t 5 /nobreak >nul
) else (
    echo Python is required to run this script. Exiting.
    goto :end
)

:checkPip
echo ====================================================
echo Checking for pip...
echo ====================================================
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Pip is not available. Attempting to install pip...
    python -m ensurepip --default-pip
    if %errorlevel% neq 0 (
        echo Failed to install pip. Exiting.
        goto :end
    )
)

:: Decide which python interpreter to use (system python or virtual environment)
set "PYTHON_INTERPRETER=python"

echo ====================================================
echo Setting up python virtual environment...
echo ====================================================
if exist ".venv\Scripts\python.exe" (
    echo Virtual environment already exists. Using it.
    set "PYTHON_INTERPRETER=.venv\Scripts\python.exe"
) else (
    echo Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment.
        goto :end
    )
    set "PYTHON_INTERPRETER=.venv\Scripts\python.exe"
)

echo ====================================================
echo Upgrading pip in the python virtual environment...
echo ====================================================
"%PYTHON_INTERPRETER%" -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo Failed to upgrade pip.
    goto :end
)

echo ====================================================
echo Installing required packages in the python virtual environment...
echo ====================================================
"%PYTHON_INTERPRETER%" -m pip install --upgrade -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install required packages.
    goto :end
)

echo ====================================================
echo Configuring Semester Organizer web application environment...
echo ====================================================
rem Set environment variables for Flask
set "FLASK_APP=app.py"
set "FLASK_ENV=development"

echo ====================================================
echo Starting the Semester Organizer web application...
echo ====================================================
rem Start the Flask server in a new minimized window so the script continues.
set FLASK_APP=app.py
set FLASK_ENV=development
start "" /min "%PYTHON_INTERPRETER%" -m flask --app app.py --debug run
rem Wait a couple of seconds for the server to start up
timeout /t 2 /nobreak >nul

echo ====================================================
echo Opening your default web browser at http://localhost:5000...
echo ====================================================
rem Search for supported browsers in common installation locations.
set BROWSER=""
set BROWSER_PATH=""
set URL="http://localhost:5000"

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "BROWSER=chrome"
    set "BROWSER_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "BROWSER=chrome"
    set "BROWSER_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    set "BROWSER=edge"
    set "BROWSER_PATH=C:\Program Files\Microsoft\Edge\Application\msedge.exe"
) else if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    set "BROWSER=edge"
    set "BROWSER_PATH=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
) else if exist "C:\Program Files\Mozilla Firefox\firefox.exe" (
    set "BROWSER=firefox"
    set "BROWSER_PATH=C:\Program Files\Mozilla Firefox\firefox.exe"
) else if exist "C:\Program Files (x86)\Mozilla Firefox\firefox.exe" (
    set "BROWSER=firefox"
    set "BROWSER_PATH=C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
)

if defined BROWSER (
    if /i "%BROWSER%"=="chrome" (
        echo Launching Chrome in incognito mode with cache disabled.
        start "" "%BROWSER_PATH%" --incognito --disable-application-cache --new-window "%URL%"
    ) else if /i "%BROWSER%"=="edge" (
        echo Launching Edge in inprivate mode with cache disabled.
        start "" "%BROWSER_PATH%" --inprivate --disable-application-cache --new-window "%URL%"
    ) else if /i "%BROWSER%"=="firefox" (
        echo Launching Firefox in private mode.
        start "" "%BROWSER_PATH%" -private-window "%URL%"
    ) else (
        echo Browser type not recognized, opening default browser.
        start "" "%URL%"
    )
) else (
    echo No supported browser found.
    echo Opening default browser...
    start "" "%URL%"
)
echo.
echo Press any key to terminate the Flask application and exit...
pause >nul

if defined PID (
    echo Terminating Flask application with PID %PID%...
    taskkill /PID %PID% /F >nul 2>&1
)

:end
echo "Script finished."
endlocal
