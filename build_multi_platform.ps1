# Build script for X-Plane Dataref Bridge cross-platform executables

Write-Host "Building X-Plane Dataref Bridge for multiple platforms..." -ForegroundColor Green

# Build for Windows (current platform)
Write-Host "Building for Windows..." -ForegroundColor Yellow
python setup_cross_platform.py build
if ($LASTEXITCODE -eq 0) {
    Write-Host "Windows build successful!" -ForegroundColor Green
    
    # Copy to release folder
    if (Test-Path "build\exe.win-amd64-3.14") {
        if (Test-Path "X-Plane Dataref Bridge-Windows") {
            Remove-Item "X-Plane Dataref Bridge-Windows" -Recurse -Force
        }
        Copy-Item "build\exe.win-amd64-3.14" "X-Plane Dataref Bridge-Windows" -Recurse
        
        # Create README for Windows
        @"
X-Plane Dataref Bridge - Windows Release
====================================

Requirements:
- Windows 10 or later
- Administrative privileges for serial port access

Installation:
1. Unzip the folder
2. Run "X-Plane Dataref Bridge.exe"
3. No installation required - fully portable

Included:
- X-Plane Dataref Bridge.exe (main application)
- lib/ (Python libraries)
- resources/ (Dataref database)
- python3*.dll (Python runtime)

For support, check the documentation in resources folder.
"@ | Out-File -FilePath "X-Plane Dataref Bridge-Windows\README.txt" -Encoding UTF8
        
        Write-Host "Windows release created: X-Plane Dataref Bridge-Windows\" -ForegroundColor Green
    }
} else {
    Write-Host "Windows build failed!" -ForegroundColor Red
}

Write-Host ""
Write-Host "Cross-platform building notes:" -ForegroundColor Cyan
Write-Host "- For Linux: Run 'python setup_cross_platform.py build' on a Linux system"
Write-Host "- For macOS: Run 'python setup_cross_platform.py build' on a macOS system"
Write-Host "- The script automatically detects the platform and uses appropriate settings"
Write-Host ""
Write-Host "To build on other platforms:" -ForegroundColor Cyan
Write-Host "1. Copy the source code to the target platform"
Write-Host "2. Install dependencies: pip install PyQt6 cx_Freeze serial pyserial hidapi"
Write-Host "3. Run: python setup_cross_platform.py build"
Write-Host ""