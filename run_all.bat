@echo off
echo ===========================================
echo 1. Installing Python Requirements...
echo ===========================================
C:\Users\ADMIN\AppData\Local\Python\bin\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error installing requirements.
    pause
    exit /b 1
)

echo.
echo ===========================================
echo 2. Training the Machine Learning Model...
echo ===========================================
C:\Users\ADMIN\AppData\Local\Python\bin\python.exe model\train_model.py
if errorlevel 1 (
    echo Error training model.
    pause
    exit /b 1
)

echo.
echo ===========================================
echo 3. Building the Windows Executable...
echo ===========================================
call build\build_exe.bat

echo.
echo All steps completed!
pause
