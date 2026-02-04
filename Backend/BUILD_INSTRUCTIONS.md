# Building Stem Splitter Executable

This guide explains how to build a standalone `.exe` file that users can run without installing Python or dependencies.

## Prerequisites

- Windows 10/11 (64-bit)
- Python 3.9 or later installed
- At least 10 GB free disk space (PyTorch and dependencies are large)

## Quick Build (Recommended)

1. Open Command Prompt or PowerShell in the `Backend` folder
2. Run the build script:
   ```batch
   build.bat
   ```

The script will:
- Create/activate a virtual environment
- Install all dependencies
- Install PyInstaller
- Build the executable
- Place it in the `dist` folder as `StemSplitter.exe`

## Manual Build

If you prefer to build manually:

1. **Create and activate virtual environment:**
   ```batch
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```batch
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Run the build script:**
   ```batch
   python build_exe.py
   ```

## Build Output

After successful build:
- Executable folder: `dist\StemSplitter\` (contains StemSplitter.exe and supporting files)
- Executable: `dist\StemSplitter\StemSplitter.exe`
- Build files: `build\` folder (can be deleted)
- Spec file: `StemSplitter.spec` (can be kept for custom builds)

**Note:** The build uses `--onedir` mode which creates a folder with the executable and all supporting files. This is more reliable than `--onefile` mode for applications that use subprocess calls.

## Distributing the Executable

1. **Test the executable:**
   - Run `dist\StemSplitter\StemSplitter.exe` on your machine
   - Test with a sample audio file
   - Verify GPU detection works (if applicable)

2. **Create distribution package:**
   - Zip the entire `dist\StemSplitter` folder
   - Optionally include in the zip:
     - `DISTRIBUTION_README.md` (user instructions - rename to README.md)
     - `THIRD_PARTY_NOTICES.txt` (license information)
   - Users extract the zip and run `StemSplitter.exe` from the extracted folder

3. **File size:**
   - The distribution folder will be large (~2-3 GB) because it includes:
     - Python runtime
     - PyQt6 GUI framework
     - PyTorch (deep learning library)
     - Demucs models and dependencies
   - This is normal and expected
   - **Important:** All files in the folder must stay together - users cannot move just the .exe file

## Troubleshooting

### Build fails with "ModuleNotFoundError"
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Try: `pip install pyinstaller --upgrade`

### Executable is very large
- This is normal. PyTorch and dependencies are large
- You can use `--onedir` instead of `--onefile` in `build_exe.py` to create a folder with multiple files (smaller individual files)

### Executable doesn't run
- Check Windows Defender/antivirus isn't blocking it
- Try running from Command Prompt to see error messages
- Make sure you're on Windows 10/11 64-bit

### GPU not detected in executable
- GPU detection requires NVIDIA drivers and CUDA
- The executable includes CUDA support, but users still need NVIDIA drivers installed
- CPU mode will work without GPU

## Advanced: Custom Build

Edit `build_exe.py` to customize:
- Executable name
- Icon file
- Included/excluded modules
- Build options

Or create a custom `.spec` file:
```batch
pyinstaller --name=StemSplitter app.py
# Edit StemSplitter.spec
pyinstaller StemSplitter.spec
```

## Notes

- First run may be slower as Demucs downloads models
- Models are cached in user's home directory
- The executable folder is self-contained - no Python installation needed
- Users extract the zip and run `StemSplitter.exe` from the folder
- All files in the folder must stay together (don't move just the .exe)

