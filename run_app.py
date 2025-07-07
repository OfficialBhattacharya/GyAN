#!/usr/bin/env python3
"""
Startup script for UPSC News Aggregator
Checks dependencies and provides helpful error messages
"""

import sys
import subprocess
import importlib

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        print("   Please upgrade Python and try again")
        return False
    else:
        print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = {
        'PyQt5': 'PyQt5==5.15.7',
        'bs4': 'beautifulsoup4==4.12.2', 
        'requests': 'requests==2.31.0',
        'apscheduler': 'APScheduler==3.10.4',
        'lxml': 'lxml==4.9.3'
    }
    
    missing_packages = []
    
    print("\n🔍 Checking dependencies...")
    
    for package_name, pip_name in required_packages.items():
        try:
            importlib.import_module(package_name)
            print(f"✅ {package_name}: Installed")
        except ImportError:
            print(f"❌ {package_name}: Missing")
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"\n❌ Missing {len(missing_packages)} required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        
        print("\n💡 To install missing packages, run:")
        print("   pip install -r requirements.txt")
        print("\n   Or install individually:")
        for package in missing_packages:
            print(f"   pip install {package}")
        
        return False
    else:
        print("✅ All dependencies are installed")
        return True

def check_config_file():
    """Check if config file exists, create default if not"""
    import os
    if not os.path.exists('config.json'):
        print("ℹ️  No config.json found - will create default configuration")
    else:
        print("✅ Configuration file found")

def run_application():
    """Run the main application"""
    try:
        print("\n🚀 Starting UPSC News Aggregator...")
        print("   If the application doesn't start, check the error messages above")
        print("   Press Ctrl+C to stop\n")
        
        # Import and run the main application
        from main import main
        main()
        
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("2. Try running from the project directory")
        print("3. Check if PyQt5 is properly installed: python -c 'import PyQt5.QtWidgets'")
        print("4. For more help, check the README.md file")
        sys.exit(1)

def main():
    """Main startup function"""
    print("=" * 50)
    print("🏛️  UPSC News Aggregator - Startup Check")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n💡 After installing dependencies, run this script again or use:")
        print("   python main.py")
        sys.exit(1)
    
    # Check config
    check_config_file()
    
    # Run application
    run_application()

if __name__ == '__main__':
    main() 