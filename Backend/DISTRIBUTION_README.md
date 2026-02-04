# Stem Splitter - Standalone Application

Thank you for downloading Stem Splitter!

## Quick Start

1. **Double-click `StemSplitter.exe`** to launch the application
2. Add audio files using the "+ Add Audio Files" button or drag and drop
3. Configure settings (device, stem count, quality, output format)
4. Click "START PROCESSING"

That's it! No installation or setup required.

## System Requirements

- **Windows 10/11 (64-bit)**
- **Optional:** NVIDIA GPU with CUDA support for faster processing

## Features

- ✅ High-quality stem separation using Demucs AI
- ✅ GPU acceleration (NVIDIA CUDA supported)
- ✅ Queue-based batch processing
- ✅ Clean, modern desktop UI
- ✅ Works fully offline
- ✅ No Python installation required

## First Run

- The first time you run the application, Demucs will download AI models (~500 MB)
- This happens automatically and only needs to be done once
- Models are stored in your user folder and reused for future runs

## Output Location

Processed stems are saved to:
- **Custom folder:** If you selected one in the app
- **Default:** `C:\Users\YourUsername\separated\`

Each song creates a folder with separate stem files (vocals, drums, bass, other).

## Troubleshooting

### Application won't start
- Make sure you're running Windows 10/11 (64-bit)
- Check Windows Defender isn't blocking it
- Try running as Administrator

### GPU not detected
- Requires NVIDIA GPU with CUDA support
- Make sure NVIDIA drivers are installed
- The app will automatically use CPU if GPU isn't available

### Processing is slow
- GPU mode is much faster than CPU
- Try "Fast" quality setting for quicker processing
- Close other applications to free up resources

### Error messages
- Check that audio files are in supported formats (MP3, WAV, FLAC, etc.)
- Make sure you have enough disk space for output files
- Try processing one file at a time if batch processing fails

## Supported Audio Formats

- MP3
- WAV
- FLAC
- AAC
- OGG
- M4A

## Output Formats

- **WAV (Lossless)** - Best quality, larger files
- **MP3 - 320 kbps** - High quality, smaller files
- **MP3 - 192 kbps** - Good quality, smallest files

## Stem Options

- **2 Stems:** Vocals + Instrumental
- **4 Stems:** Vocals, Drums, Bass, Other (Default)
- **6 Stems:** More detailed separation

## License

This software is provided "as is", without warranty of any kind.
See LICENSE file and THIRD_PARTY_NOTICES.txt for details.

## Support

For issues or questions, please contact:
- Email: rohan.k.codersboutique@gmail.com
- GitHub: https://github.com/ramirocruz07

---

**Note:** This is a standalone executable. All dependencies are included.
The file size is large (~2-3 GB) because it includes Python, PyTorch, and AI models.







