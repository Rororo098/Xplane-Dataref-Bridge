# Simple Windows Release Script
# Copy only the essential files for the Windows release

$exePath = "build\exe.win-amd64-3.14\X-Plane Dataref Bridge.exe"
$destPath = "X-Plane Dataref Bridge-Windows"

# Create destination directory if it doesn't exist
if (-not (Test-Path $destPath)) {
    New-Item -ItemType Directory -Path $destPath -Force
}

Write-Host "Copying main executable..."
Copy-Item $exePath "$destPath\X-Plane Dataref Bridge.exe" -Force

Write-Host "Copying license file..."
Copy-Item "build\exe.win-amd64-3.14\frozen_application_license.txt" "$destPath\frozen_application_license.txt" -Force

Write-Host "Copying Python DLLs..."
Copy-Item "build\exe.win-amd64-3.14\python3*.dll" "$destPath\" -Force

Write-Host "Copying resources..."
Copy-Item "build\exe.win-amd64-3.14\resources" "$destPath\resources" -Recurse -Force

Write-Host "Windows release created successfully!" -ForegroundColor Green