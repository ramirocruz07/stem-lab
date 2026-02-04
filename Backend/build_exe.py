"""
Build script for creating standalone .exe file using PyInstaller
Run this script to build the executable: python build_exe.py
"""

import PyInstaller.__main__
import os
import sys

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("=" * 60)
    print("Building Stem Splitter Executable")
    print("=" * 60)
    
    # PyInstaller arguments - SIMPLIFIED VERSION
    args = [
        'app.py',  # Main script
        '--name=StemSplitter',  # Name of the executable
        '--onedir',  # Create a folder with executable and supporting files (more reliable)
        '--windowed',  # No console window (GUI app)
        '--icon=assets/logo.ico' if os.path.exists('assets/logo.ico') else '',  # Icon if available
        '--add-data=assets;assets',  # Include assets folder
        '--add-data=core;core',  # Include core module (separator.py)
        '--add-data=THIRD_PARTY_NOTICES.txt;.',  # Include license file
        # Hidden imports for your app
        '--hidden-import=core.separator',
        '--hidden-import=core.worker',
        '--hidden-import=ui.main_window',
        # Critical imports to fix jaraco error
        '--hidden-import=pkg_resources',
        '--hidden-import=setuptools',
        '--hidden-import=jaraco.text',
        '--hidden-import=jaraco.functools',
        '--hidden-import=jaraco.collections',
        # Collect all for major packages
        '--collect-all=torch',
        '--collect-all=torchaudio',
        '--collect-all=demucs',
        '--collect-all=PyQt6',
        '--collect-all=numpy',
        '--collect-all=scipy',
        # Add these to your PyInstaller args:
        '--collect-all=demucs',
        '--hidden-import=demucs',
        '--hidden-import=demucs.api',
        '--hidden-import=demucs.pretrained',
        '--hidden-import=demucs.separate',
        '--hidden-import=demucs.audio',
        '--hidden-import=demucs.model',
        '--hidden-import=demucs.utils',
        '--hidden-import=demucs.apply',
        '--hidden-import=demucs.hdemucs',
        '--hidden-import=demucs.hdemucs_6s',
    ]
    
    # Remove empty strings
    args = [arg for arg in args if arg]
    
    # Remove icon if file doesn't exist
    if not os.path.exists('assets/logo.ico'):
        args = [arg for arg in args if not arg.startswith('--icon')]
    
    print("\nPyInstaller arguments:")
    for arg in args:
        print(f"  {arg}")
    
    print("\nStarting build process...")
    print("This may take several minutes...\n")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n" + "=" * 60)
        print("Build completed successfully!")
        print("=" * 60)
        exe_path = os.path.join(script_dir, 'dist', 'StemSplitter', 'StemSplitter.exe')
        if os.path.exists(exe_path):
            print(f"\nExecutable location: {exe_path}")
            print(f"\nDistribution folder: {os.path.join(script_dir, 'dist', 'StemSplitter')}")
            print("\nTo distribute:")
            print("  1. Zip the entire 'dist/StemSplitter' folder")
            print("  2. Users extract and run StemSplitter.exe")
        else:
            # Fallback for onefile mode
            exe_path = os.path.join(script_dir, 'dist', 'StemSplitter.exe')
            if os.path.exists(exe_path):
                print(f"\nExecutable location: {exe_path}")
                print("\nYou can now distribute the StemSplitter.exe file to users.")
            else:
                print("\n⚠️  Executable not found. Check build output for errors.")
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()