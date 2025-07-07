@echo off
echo UPSC News Aggregator Installer
echo ================================

echo.
echo This will copy the UPSC News Aggregator to your Programs folder
echo and create a desktop shortcut.
echo.

pause

set "INSTALL_DIR=%PROGRAMFILES%\UPSC News Aggregator"
set "DESKTOP=%USERPROFILE%\Desktop"

echo Creating installation directory...
mkdir "%INSTALL_DIR%" 2>nul

echo Copying application files...
copy "UPSC-News-Aggregator.exe" "%INSTALL_DIR%\" /Y
copy "requirements.txt" "%INSTALL_DIR%\" /Y 2>nul
copy "README.md" "%INSTALL_DIR%\" /Y 2>nul

echo Creating desktop shortcut...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\UPSC News Aggregator.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\UPSC-News-Aggregator.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

echo.
echo Installation complete!
echo You can now run UPSC News Aggregator from your desktop shortcut.
echo.
pause
