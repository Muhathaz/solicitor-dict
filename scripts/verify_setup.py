#!/usr/bin/env python3
"""
Setup Verification Script for UK Solicitors Data Processing Environment

This script verifies that the development environment is properly configured
and all dependencies are correctly installed.
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_status(item: str, status: bool, details: str = ""):
    """Print status with colored output"""
    if sys.platform != "win32":
        GREEN = '\033[92m'
        RED = '\033[91m'
        RESET = '\033[0m'
        YELLOW = '\033[93m'
    else:
        GREEN = RED = RESET = YELLOW = ''
    
    symbol = f"{GREEN}✓{RESET}" if status else f"{RED}✗{RESET}"
    status_text = f"{GREEN}PASS{RESET}" if status else f"{RED}FAIL{RESET}"
    
    print(f"{symbol} {item:<40} {status_text}")
    if details:
        print(f"  {YELLOW}└─{RESET} {details}")

def check_python_version() -> Tuple[bool, str]:
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)"

def check_virtual_environment() -> Tuple[bool, str]:
    """Check if running in virtual environment"""
    in_venv = (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        os.environ.get('VIRTUAL_ENV') is not None
    )
    
    if in_venv:
        venv_path = os.environ.get('VIRTUAL_ENV', sys.prefix)
        return True, f"Virtual environment active: {venv_path}"
    else:
        return False, "No virtual environment detected"

def check_required_packages() -> Tuple[bool, str]:
    """Check if all required packages are installed"""
    required_packages = [
        'requests', 'pandas', 'beautifulsoup4', 'playwright',
        'python-dotenv', 'PyYAML', 'colorama', 'tqdm',
        'jsonschema', 'fuzzywuzzy', 'openai', 'pytest',
        'structlog'
    ]
    
    missing_packages = []
    installed_packages = []
    
    for package in required_packages:
        try:
            # Handle package name variations
            import_name = package
            if package == 'python-dotenv':
                import_name = 'dotenv'
            elif package == 'PyYAML':
                import_name = 'yaml'
            elif package == 'beautifulsoup4':
                import_name = 'bs4'
            
            importlib.import_module(import_name)
            installed_packages.append(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        return False, f"Missing packages: {', '.join(missing_packages)}"
    else:
        return True, f"All {len(installed_packages)} packages installed"

def check_directory_structure() -> Tuple[bool, str]:
    """Check if project directory structure exists"""
    base_path = Path(__file__).parent.parent
    
    required_dirs = [
        "config",
        "src/collectors",
        "src/processors", 
        "src/utils",
        "data/raw",
        "data/processed",
        "data/output",
        "logs",
        "reports",
        "tests",
        "scripts"
    ]
    
    missing_dirs = []
    existing_dirs = []
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists() and full_path.is_dir():
            existing_dirs.append(dir_path)
        else:
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        return False, f"Missing directories: {', '.join(missing_dirs)}"
    else:
        return True, f"All {len(existing_dirs)} directories present"

def check_configuration_files() -> Tuple[bool, str]:
    """Check if configuration files exist"""
    base_path = Path(__file__).parent.parent
    
    required_files = [
        "config/settings.yaml",
        "config/.env.example",
        "requirements.txt",
        "README.md",
        ".gitignore"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists() and full_path.is_file():
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    if missing_files:
        return False, f"Missing files: {', '.join(missing_files)}"
    else:
        return True, f"All {len(existing_files)} config files present"

def check_utils_modules() -> Tuple[bool, str]:
    """Check if utility modules can be imported"""
    try:
        from utils import get_logger, FileManager, DataValidator
        return True, "Utils modules imported successfully"
    except ImportError as e:
        return False, f"Import error: {str(e)}"

def check_logging_setup() -> Tuple[bool, str]:
    """Check if logging setup works"""
    try:
        from utils.logger import setup_logging, get_logger
        
        # Test logging setup
        setup_logging()
        logger = get_logger("test")
        
        # Ensure logs directory exists
        logs_dir = Path(__file__).parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Test logging
        logger.info("Setup verification test log entry")
        
        return True, "Logging system initialized successfully"
    except Exception as e:
        return False, f"Logging setup failed: {str(e)}"

def check_playwright_browsers() -> Tuple[bool, str]:
    """Check if Playwright browsers are installed"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return True, "Playwright is ready (run 'playwright install' to install browsers)"
        else:
            return False, "Playwright command failed"
    except Exception as e:
        return False, f"Playwright check failed: {str(e)}"

def check_file_permissions() -> Tuple[bool, str]:
    """Check file permissions for key directories"""
    base_path = Path(__file__).parent.parent
    test_dirs = ["data", "logs", "reports"]
    
    permission_issues = []
    
    for dir_name in test_dirs:
        dir_path = base_path / dir_name
        if dir_path.exists():
            try:
                # Test write permission
                test_file = dir_path / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
            except Exception:
                permission_issues.append(dir_name)
    
    if permission_issues:
        return False, f"Write permission issues: {', '.join(permission_issues)}"
    else:
        return True, "File permissions OK"

def check_environment_variables() -> Tuple[bool, str]:
    """Check for environment variables"""
    base_path = Path(__file__).parent.parent
    env_file = base_path / "config" / ".env"
    
    if env_file.exists():
        # Count environment variables in .env file
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        env_vars = [line for line in lines if '=' in line and not line.strip().startswith('#')]
        
        if env_vars:
            return True, f".env file exists with {len(env_vars)} variables"
        else:
            return True, ".env file exists but no variables configured"
    else:
        return True, ".env file not found (optional - copy from .env.example)"

def run_comprehensive_check() -> Dict[str, Any]:
    """Run all verification checks"""
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Required Packages", check_required_packages),
        ("Directory Structure", check_directory_structure),
        ("Configuration Files", check_configuration_files),
        ("Utils Modules", check_utils_modules),
        ("Logging Setup", check_logging_setup),
        ("Playwright", check_playwright_browsers),
        ("File Permissions", check_file_permissions),
        ("Environment Variables", check_environment_variables),
    ]
    
    results = {}
    all_passed = True
    
    print_header("UK Solicitors Data Processing - Setup Verification")
    
    for check_name, check_function in checks:
        try:
            passed, details = check_function()
            print_status(check_name, passed, details)
            results[check_name] = {"passed": passed, "details": details}
            
            if not passed:
                all_passed = False
                
        except Exception as e:
            print_status(check_name, False, f"Check failed with error: {str(e)}")
            results[check_name] = {"passed": False, "details": f"Error: {str(e)}"}
            all_passed = False
    
    # Summary
    print_header("Verification Summary")
    
    passed_count = sum(1 for result in results.values() if result["passed"])
    total_count = len(results)
    
    if all_passed:
        print("🎉 All checks passed! Your environment is ready for data processing.")
        print("\nNext steps:")
        print("1. Copy config/.env.example to config/.env")
        print("2. Add your API keys to config/.env")
        print("3. Run 'playwright install' to install browsers for web scraping")
        print("4. Start collecting data with the provided scripts")
    else:
        print(f"⚠️  {passed_count}/{total_count} checks passed. Please fix the failing items above.")
        print("\nFor help:")
        print("1. Check the README.md for detailed setup instructions")
        print("2. Ensure all packages are installed: pip install -r requirements.txt")
        print("3. Verify you're in the correct virtual environment")
    
    results["summary"] = {
        "all_passed": all_passed,
        "passed_count": passed_count,
        "total_count": total_count,
        "success_rate": (passed_count / total_count) * 100
    }
    
    return results

def main():
    """Main verification function"""
    try:
        results = run_comprehensive_check()
        
        # Exit with appropriate code
        if results["summary"]["all_passed"]:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error during verification: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()