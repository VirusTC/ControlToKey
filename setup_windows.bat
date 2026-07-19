@echo off
:: /setup_windows.bat
echo ====================================================
echo  Compiling Standalone ControlToKey Windows Package  
echo ====================================================

pip install pyinstaller

:: Update your pyinstaller execution target line in /setup_windows.bat to handle the new files
pyinstaller --noconsole --onefile --name="ControlToKey" --add-data "src/windows/profiles;profiles" src/windows/main.py

echo ====================================================
echo  Compilation complete! Target is located inside: \dist\ControlToKey.exe
echo ====================================================
pause
