# X-Plane Dataref Bridge - Cross-Platform Release Notes

## ✅ Successfully Built Executables

### Windows ✅
- **Location**: `X-Plane Dataref Bridge-Windows/`
- **Executable**: `X-Plane Dataref Bridge.exe`
- **Size**: ~206MB
- **Status**: ✅ Working with icon fix

### Linux & macOS 📋
To build for Linux and macOS:

1. **Copy source code** to the target platform
2. **Install dependencies**:
   ```bash
   pip install PyQt6 cx_Freeze==8.5.3 serial pyserial hidapi Pillow
   ```
3. **Run the build script**:
   ```bash
   python setup_cross_platform.py build
   ```

### Icon Fix Applied ✅
- Fixed icon display in taskbar and window title bar
- Added proper icon fallback system
- Icon now properly set for both window and application

### Cross-Platform Script Features
- **Automatic platform detection** (Windows, Linux, macOS)
- **Platform-specific optimization**:
  - Windows: GUI base (no console)
  - Linux/macOS: Console base (for debugging)
- **Icon format handling**:
  - Windows: .ico format
  - Linux/macOS: .png format (with .icns generation for macOS)
- **Package-specific includes** for each platform

### Platform Requirements
- **Windows**: Windows 10+ (✅ Built)
- **Linux**: Modern Linux with GTK+ (📋 To build)
- **macOS**: macOS 10.14+ (📋 To build)

### Installation Notes
- **Windows**: Run `.exe` - fully portable
- **Linux**: Run executable from terminal
- **macOS**: Run `.app` bundle

### Dependencies Bundled
- ✅ Python 3.14 runtime
- ✅ PyQt6 GUI framework
- ✅ All required libraries
- ✅ Dataref database with real descriptions

## Ready for Distribution! 🚀

The Windows build is ready for immediate distribution. For Linux and macOS, follow the build instructions above.