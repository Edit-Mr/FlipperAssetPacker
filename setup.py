#!/usr/bin/env python
import subprocess
import sys
import venv
import os
from pathlib import Path

def setup_project():
    # Create folders
    project_dir = Path.cwd()
    venv_dir = project_dir / "venv"
    
    print("1. Creating virtual environment...")
    venv.create(venv_dir, with_pip=True)
    
    # Get the correct python and pip executables
    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"

    print("2. Installing requirements...")
    subprocess.run([str(pip_exe), "install", "-r", "requirements.txt"])
    
    print("3. Creating executable...")
    subprocess.run([
        str(pip_exe), "install", "pyinstaller"
    ])
    
    subprocess.run([
        str(python_exe), "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", "main",
        "main.py"
    ])
    
    print("\nSetup complete! You can find the executable in the 'dist' folder.")
    print("\nTo run the program during development:")
    if sys.platform == "win32":
        print("venv\\Scripts\\python.exe main.py")
    else:
        print("./venv/bin/python main.py")

if __name__ == "__main__":
    setup_project()