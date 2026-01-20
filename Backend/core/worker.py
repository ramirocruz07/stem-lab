import os
import sys
import subprocess
import re
from PyQt6.QtCore import QThread, pyqtSignal

class SplitterWorker(QThread):
    finished = pyqtSignal()
    progress_changed = pyqtSignal(int)
    output_ready = pyqtSignal(str)
    
    def __init__(self, file, stems, quality, audio_format, bitrate, device, output_dir):
        super().__init__()
        self.file = file
        self.stems = stems
        self.audio_format = audio_format
        self.quality = quality
        self.device = device
        self.output_dir = output_dir
        self.bitrate = bitrate
        self.last_progress = 0
    
    def run(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        separator_path = os.path.join(base_dir, "core", "separator.py")

        cmd = [
            sys.executable,
            separator_path,
            self.file,
            str(self.stems),
            self.quality,
            self.audio_format,
            self.bitrate,
            self.device,
            self.output_dir
        ]

        print(f"\n🚀 Starting separation: {os.path.basename(self.file)}")
        print(f"📊 Settings: {self.stems} stems, {self.quality} quality, {self.audio_format} format")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Track progress
        for line in process.stdout:
            line = line.strip()
            
            # Look for percentage in various formats
            if '%' in line:
                # Try to extract percentage from the line
                percent = self.extract_percentage(line)
                if percent is not None and percent >= 0 and percent <= 100:
                    # Only update if progress increased (avoid going backwards)
                    if percent > self.last_progress:
                        self.progress_changed.emit(percent)
                        self.last_progress = percent
            
            # Check for completion indicators
            if any(word in line.lower() for word in ['done', 'finished', 'saved', 'complete']):
                if self.last_progress < 100:
                    self.progress_changed.emit(100)
                    self.last_progress = 100

        process.wait()
        
        # Ensure we end at 100%
        if self.last_progress < 100:
            self.progress_changed.emit(100)
        
        # Get output folder
        output_folder = self.get_output_folder()
        if output_folder:
            print(f"✅ Success! Output saved to: {output_folder}")
            self.output_ready.emit(output_folder)
        else:
            print("⚠️  Output folder not found!")
        
        self.finished.emit()
    
    def extract_percentage(self, line):
        """Extract percentage from various Demucs output formats"""
        try:
            # Format 1: "14%|########2 | 23.4/169.65"
            if '|' in line and '%' in line:
                parts = line.split('|')
                if parts and '%' in parts[0]:
                    percent_str = parts[0].replace('%', '').strip()
                    return int(percent_str)
            
            # Format 2: Just "14%" at the beginning
            if line.startswith(('0%', '1%', '2%', '3%', '4%', '5%', '6%', '7%', '8%', '9%')):
                percent_str = line.split('%')[0].strip()
                return int(percent_str)
            
            # Format 3: Contains " X% " somewhere
            match = re.search(r'(\d+)%', line)
            if match:
                return int(match.group(1))
                
        except (ValueError, IndexError):
            pass
        
        return None
    
    def get_output_folder(self):
        """Get the actual output folder where stems are saved"""
        import os
        from pathlib import Path
        
        # Determine model name based on stem count
        model_name = "htdemucs"
        if self.stems == 2:
            model_name = "htdemucs_ft"
        elif self.stems == 6:
            model_name = "htdemucs_6s"
        
        # Get input file name without extension
        input_name = Path(self.file).stem
        
        # Determine output directory
        if self.output_dir:
            base_output = self.output_dir
        else:
            # Demucs default output location
            base_output = os.path.join(os.path.expanduser("~"), "separated")
        
        # Construct full output path
        output_folder = os.path.join(base_output, model_name, input_name)
        
        if os.path.exists(output_folder):
            return output_folder
        
        # Try alternative location (Demucs might use different default)
        alt_base = os.path.join(os.path.expanduser("~"), "Downloads", "Demucs")
        alt_folder = os.path.join(alt_base, model_name, input_name)
        if os.path.exists(alt_folder):
            return alt_folder
            
        return None