@echo off
setlocal
echo ==============================================
echo   GaloonBoardLite Build Script
echo ==============================================

set CSC=C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe
if not exist "%CSC%" (
    set CSC=C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe
)

if not exist "%CSC%" (
    echo [ERROR] csc.exe was not found.
    pause
    exit /b 1
)

echo Compiling GaloonBoardLite.exe ...
"%CSC%" /target:winexe /optimize /win32manifest:app.manifest /win32icon:icon.ico /out:GaloonBoardLite.exe Program.cs

if %errorlevel% equ 0 (
    echo [SUCCESS] GaloonBoardLite.exe generated successfully!
) else (
    echo [ERROR] Build failed.
)

echo.
pause
