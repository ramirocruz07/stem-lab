# Stem Splitter

Stem Splitter is a free, offline desktop application that separates
songs into individual stems such as vocals, drums, bass, and others.
It is built using Python, PyQt6, and Demucs.

## Features
- High-quality stem separation using Demucs
- GPU acceleration (NVIDIA CUDA supported)
- Queue-based batch processing
- Clean, modern desktop UI
- Works fully offline

## Requirements
- Python 3.9 or later
- Windows 10/11 (64-bit)
- Optional: NVIDIA GPU with CUDA support

## Installation

1. Clone or download this repository
2. Navigate to the `Backend` directory
3. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python app.py
```

The application will open a graphical interface where you can:
- Add audio files to the processing queue
- Select device (Auto/CPU/GPU)
- Choose stem count (2, 4, or 6 stems)
- Set processing quality (Fast/Balanced/Best)
- Select output audio format and quality
- Choose output folder

## Disclaimer
This software is provided "as is", without warranty of any kind.
The author is not responsible for data loss, hardware damage,
or any other issues arising from the use of this application.

## License
This project is licensed under the MIT License.
See the LICENSE file for details.

## Third-Party Software
This application uses the following open-source projects:
- Demucs (MIT License)
- PyTorch (BSD-style License)
- Qt for Python / PyQt6 (LGPL v3)
- NumPy, TorchAudio, SoundFile

See THIRD_PARTY_NOTICES.txt for details.

## Affiliation Disclaimer
This project is not affiliated with, endorsed by, or sponsored by
Meta, Facebook, PyTorch, or the Demucs authors.
