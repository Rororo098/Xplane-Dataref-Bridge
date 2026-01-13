import os
import subprocess
import sys
import shutil

def run_command(command):
    print(f"Running: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end='')
    process.wait()
    if process.returncode != 0:
        print(f"Error: Command failed with return code {process.returncode}")
        return False
    return True

def build():
    # 1. Install requirements
    print("Ensuring dependencies are installed...")
    if not run_command("pip install -r requirements.txt"):
        print("Failed to install requirements.")
        return

    # 2. Install PyInstaller if not present
    print("Checking for PyInstaller...")
    if not run_command("pip install pyinstaller"):
        print("Failed to install PyInstaller.")
        return

    # 2. Clean previous builds
    print("Cleaning previous builds...")
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # 3. Run PyInstaller
    print("Building executable...")
    if run_command("pyinstaller main.spec --clean --noconfirm"):
        print("\n" + "="*50)
        print("Success! Your executable is in the 'dist/X-Plane Dataref Bridge' folder.")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("Build failed. See errors above.")
        print("="*50)

if __name__ == "__main__":
    # Ensure we are in the root directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    build()
