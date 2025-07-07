#!/usr/bin/env python3
"""
Build script for creating UPSC News Aggregator executable using PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Clean spec files
    for spec_file in Path('.').glob('*.spec'):
        print(f"Removing {spec_file}...")
        spec_file.unlink()

def build_executable():
    """Build executable using PyInstaller"""
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',  # Create single executable file
        '--name=UPSC-News-Aggregator',
        '--icon=icon.ico' if os.path.exists('icon.ico') else '',
        '--add-data=frameworkArchitecture.txt;.',  # Include architecture doc
        # PyQt5 imports
        '--hidden-import=PyQt5.sip',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        # Email imports
        '--hidden-import=email.mime.text',
        '--hidden-import=email.mime.multipart',
        '--hidden-import=email.utils',
        '--hidden-import=smtplib',
        # APScheduler imports
        '--hidden-import=apscheduler',
        '--hidden-import=apscheduler.schedulers',
        '--hidden-import=apscheduler.schedulers.background',
        '--hidden-import=apscheduler.executors',
        '--hidden-import=apscheduler.executors.pool',
        '--hidden-import=apscheduler.job',
        '--hidden-import=apscheduler.triggers',
        '--hidden-import=apscheduler.triggers.cron',
        '--hidden-import=apscheduler.util',
        # Web scraping imports
        '--hidden-import=bs4',
        '--hidden-import=beautifulsoup4',
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--hidden-import=lxml',
        '--hidden-import=lxml.etree',
        '--hidden-import=lxml._elementpath',
        # Other imports
        '--hidden-import=json',
        '--hidden-import=logging',
        '--hidden-import=datetime',
        '--hidden-import=copy',
        '--hidden-import=re',
        '--hidden-import=os',
        '--hidden-import=sys',
        'main.py'
    ]
    
    # Remove empty icon parameter if no icon exists
    cmd = [arg for arg in cmd if arg]
    
    print("Building executable with PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(result.stdout)
        
        # Copy additional files to dist folder
        dist_dir = Path('dist')
        if dist_dir.exists():
            print("\nCopying additional files...")
            
            # Copy requirements.txt for reference
            if os.path.exists('requirements.txt'):
                shutil.copy2('requirements.txt', dist_dir / 'requirements.txt')
                print("- Copied requirements.txt")
            
            # Copy README if it exists
            if os.path.exists('README.md'):
                shutil.copy2('README.md', dist_dir / 'README.md')
                print("- Copied README.md")
            
            print(f"\nExecutable created in: {dist_dir.absolute()}")
            print("Files in dist folder:")
            for file in dist_dir.iterdir():
                print(f"  - {file.name}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("PyInstaller not found. Please install it with: pip install pyinstaller")
        return False

def create_installer_script():
    """Create a simple installer script for Windows"""
    installer_script = """@echo off
echo UPSC News Aggregator Installer
echo ================================

echo.
echo This will copy the UPSC News Aggregator to your Programs folder
echo and create a desktop shortcut.
echo.

pause

set "INSTALL_DIR=%PROGRAMFILES%\\UPSC News Aggregator"
set "DESKTOP=%USERPROFILE%\\Desktop"

echo Creating installation directory...
mkdir "%INSTALL_DIR%" 2>nul

echo Copying application files...
copy "UPSC-News-Aggregator.exe" "%INSTALL_DIR%\\" /Y
copy "requirements.txt" "%INSTALL_DIR%\\" /Y 2>nul
copy "README.md" "%INSTALL_DIR%\\" /Y 2>nul

echo Creating desktop shortcut...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\\UPSC News Aggregator.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\UPSC-News-Aggregator.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

echo.
echo Installation complete!
echo You can now run UPSC News Aggregator from your desktop shortcut.
echo.
pause
"""
    
    with open('dist/install.bat', 'w') as f:
        f.write(installer_script)
    
    print("Created installer script: dist/install.bat")

def main():
    print("UPSC News Aggregator Build Script")
    print("=================================")
    
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print("Error: main.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Clean previous builds
    clean_build()
    
    # Build executable
    if build_executable():
        print("\n✓ Build completed successfully!")
        
        # Create installer for Windows
        if sys.platform == 'win32':
            create_installer_script()
            print("✓ Windows installer script created!")
        
        print("\nNext steps:")
        print("1. Test the executable in the dist/ folder")
        print("2. On Windows, you can run install.bat to install the application")
        print("3. The application will run in the system tray")
        
    else:
        print("\n✗ Build failed!")
        sys.exit(1)

if __name__ == '__main__':
    main() 