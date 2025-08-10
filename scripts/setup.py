#!/usr/bin/env python3
"""
Automated Setup Script for UK Solicitors Data Processing Environment

This script automates the initial setup of the development environment.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def run_command(command: list, description: str) -> bool:
    """Run a system command and return success status"""
    print(f"📋 {description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {' '.join(command)}")
        return False

def setup_virtual_environment():
    """Set up Python virtual environment"""
    print_header("Setting up Virtual Environment")
    
    venv_name = "uk-solicitors-data"
    
    # Check if virtual environment already exists
    if Path(venv_name).exists():
        print(f"📁 Virtual environment '{venv_name}' already exists")
        return True
    
    # Try different methods to create virtual environment
    methods = [
        ([sys.executable, "-m", "venv", venv_name], "Creating virtual environment with venv"),
        (["python3", "-m", "venv", venv_name], "Creating virtual environment with python3 venv"),
        (["virtualenv", venv_name], "Creating virtual environment with virtualenv")
    ]
    
    for command, description in methods:
        if run_command(command, description):
            return True
    
    print("❌ Failed to create virtual environment with all methods")
    return False

def install_packages():
    """Install required packages"""
    print_header("Installing Python Packages")
    
    # Determine pip executable
    pip_executables = [
        "uk-solicitors-data/bin/pip",  # Linux/macOS
        "uk-solicitors-data/Scripts/pip.exe",  # Windows
        "pip",  # Fallback
    ]
    
    pip_exe = None
    for exe in pip_executables:
        if Path(exe).exists() or shutil.which(exe):
            pip_exe = exe
            break
    
    if not pip_exe:
        print("❌ Could not find pip executable")
        return False
    
    # Install packages
    commands = [
        ([pip_exe, "install", "--upgrade", "pip"], "Upgrading pip"),
        ([pip_exe, "install", "-r", "requirements.txt"], "Installing project dependencies"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def setup_playwright():
    """Set up Playwright browsers"""
    print_header("Setting up Playwright")
    
    # Determine python executable in virtual environment
    python_executables = [
        "uk-solicitors-data/bin/python",  # Linux/macOS
        "uk-solicitors-data/Scripts/python.exe",  # Windows
        sys.executable,  # Fallback
    ]
    
    python_exe = None
    for exe in python_executables:
        if Path(exe).exists() or shutil.which(exe):
            python_exe = exe
            break
    
    if not python_exe:
        print("❌ Could not find Python executable")
        return False
    
    return run_command(
        [python_exe, "-m", "playwright", "install"],
        "Installing Playwright browsers"
    )

def create_env_file():
    """Create .env file from template"""
    print_header("Setting up Environment Configuration")
    
    env_template = Path("config/.env.example")
    env_file = Path("config/.env")
    
    if env_file.exists():
        print("📁 .env file already exists")
        return True
    
    if not env_template.exists():
        print("❌ .env.example template not found")
        return False
    
    try:
        shutil.copy(env_template, env_file)
        print("✅ Created .env file from template")
        print("📝 Please edit config/.env and add your API keys")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print_header("Setup Complete - Next Steps")
    
    print("🎉 Environment setup completed successfully!")
    print("\nTo activate your environment:")
    
    if sys.platform == "win32":
        print("   uk-solicitors-data\\Scripts\\activate")
    else:
        print("   source uk-solicitors-data/bin/activate")
    
    print("\nNext steps:")
    print("1. Activate the virtual environment (command above)")
    print("2. Edit config/.env and add your API keys")
    print("3. Run verification: python scripts/verify_setup.py")
    print("4. Start data collection: python scripts/run_collection.py")
    
    print("\nFor help:")
    print("- Read README.md for detailed documentation")
    print("- Run verification script to check your setup")
    print("- Check logs/ directory for application logs")

def main():
    """Main setup function"""
    print_header("UK Solicitors Data Processing - Automated Setup")
    
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    print(f"📂 Working directory: {project_dir}")
    
    setup_steps = [
        ("Virtual Environment", setup_virtual_environment),
        ("Python Packages", install_packages), 
        ("Playwright Browsers", setup_playwright),
        ("Environment File", create_env_file),
    ]
    
    failed_steps = []
    
    for step_name, step_function in setup_steps:
        try:
            if not step_function():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} failed with error: {e}")
            failed_steps.append(step_name)
    
    if failed_steps:
        print_header("Setup Issues")
        print(f"⚠️  Some setup steps failed: {', '.join(failed_steps)}")
        print("\nManual setup may be required. Please check the README.md for instructions.")
        sys.exit(1)
    else:
        print_next_steps()
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error during setup: {e}")
        sys.exit(1)