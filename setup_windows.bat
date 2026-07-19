@echo off
:: /setup_windows.bat
echo ====================================================
echo  Compiling Standalone ControlToKey Windows Package  
echo ====================================================

pip install pyinstaller

:: Compile the codebase into a single executable file, hiding the background command console windows
pyinstaller --noconsole --onefile --name="ControlToKey" --add-data "src/windows;src/windows" src/windows/main.py

echo ====================================================
echo  Compilation complete! Target is located inside: \dist\ControlToKey.exe
echo ====================================================
pause
