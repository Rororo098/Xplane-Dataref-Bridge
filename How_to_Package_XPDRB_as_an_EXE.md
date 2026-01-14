# How to Package XPDRB as an EXE  
  
This guide documents the process of creating a standalone executable for the X-Plane Dataref Bridge \(XPDRB\) application, including solutions for common dependency issues. 
  
## Overview  
  
The X-Plane Dataref Bridge application is a Python/PyQt6 application that requires special handling during packaging due to its dependencies on serial communication libraries, PyQt6, and qasync for asynchronous operations.  
  
## Common Issues Encountered  
  
### Missing Dependencies Error  
The most common issue during packaging is the \"No module named 'qasync'\" error, which occurs because packaging tools sometimes fail to detect all dependencies automatically. 
  
## Solutions Tried  
  
### Solution 1: PyInstaller  
  
1. Install PyInstaller:  
   \`\`\`bash  
   pip install pyinstaller  
   \`\`\`  
  
2. Create executable with proper hidden imports:  
   \`\`\`bash  
   pyinstaller --onefile --windowed --icon=resources/icon.ico --hidden-import=serial --hidden-import=serial.tools --hidden-import=serial.tools.list_ports --hidden-import=PyQt6 --hidden-import=PyQt6.QtCore --hidden-import=PyQt6.QtGui --hidden-import=PyQt6.QtWidgets --hidden-import=qasync main.py  
   \`\`\`  
  
### Solution 2: cx_Freeze \(Recommended\)  
  
1. Create a setup script \(\`setup_cx.py\`:  
   \`\`\`python  
   import sys  
   from cx_Freeze import setup, Executable  
  
   build_exe_options = {  
       "packages": [  
           'serial',  
           'serial.tools',  
           'serial.tools.list_ports',  
           'serial.serialwin32',  
           'serial.win32',  
           'serial.serialutil',  
           'serial.threaded',  
           'qasync',  
           'PyQt6',  
       ],  
       "includes": [  
           'serial.serialutil',  
           'serial.threaded',  
           'serial.urlhandler',  
           'serial.urlhandler.protocol_socket',  
           'serial.urlhandler.protocol_rfc2217',  
           'serial.urlhandler.protocol_loop',  
           'serial.urlhandler.protocol_alt',  
           'serial.urlhandler.protocol_cp2110',  
           'serial.urlhandler.protocol_hwgrep',  
           'serial.urlhandler.protocol_spy',  
       ],  
       "excludes": [],  
       "optimize": 0,  
   }  
  
   # For Windows GUI application without console  
   if sys.platform == "win32":  
       base = "Win32GUI"  # Use 'Win32GUI' for Windows GUI applications  
   else:  
       base = None  
  
   setup\(  
       name="X-Plane Dataref Bridge",  
       version="1.0",  
       description="X-Plane Dataref Bridge",  
       options={"build_exe": build_exe_options},  
       executables=[Executable("main.py", base=base, icon="resources/icon.ico",  
                             target_name="X-Plane Dataref Bridge.exe")]  
   \)  
   \`\`\`  
  
2. Install cx_Freeze:  
   \`\`\`bash  
   pip install cx_Freeze  
   \`\`\`  
  
3. Build the executable:  
   \`\`\`bash  
   python setup_cx.py build  
   \`\`\` 
## Successful Outcome 
  
Two executables were successfully created:  
  
1. **PyInstaller executable** \(main.exe\):  
   - Located in the dist folder  
   - Size: ~38MB  
   - Contains all dependencies in a single file 
  
2. **cx_Freeze executable** \(X-Plane Dataref Bridge.exe\):  
   - Located in the build\\\\exe.win-amd64-3.14 folder  
   - Size: ~29KB \(with supporting files in the lib directory\)  
   - Properly includes all required modules \(qasync, serial, PyQt6 components\)  
  
## Distribution  
  
For distribution, you can use either:  
  
- The PyInstaller version: Simply distribute the single main.exe file  
- The cx_Freeze version: Distribute the entire build\\\\exe.win-amd64-3.14 folder  
  
Both executables will run on Windows systems without requiring Python or any installed packages.  
  
## Troubleshooting Tips  
  
- If you encounter missing module errors, ensure all dependencies are listed in the setup script  
- For PyQt6 applications, make sure to include all relevant Qt modules  
- For serial communication, include all serial submodules and backends  
- Use the --windowed flag for GUI applications to prevent console window from appearing 
