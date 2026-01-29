import os
import sys
import subprocess
import re
import time
from PyQt6.QtCore import QThread, pyqtSignal

class SplitterWorker(QThread):
    finished = pyqtSignal()
    progress_changed = pyqtSignal(int)
    output_ready = pyqtSignal(str)
    gpu_memory_update = pyqtSignal(str)  # New signal for GPU memory updates
    current_file = pyqtSignal(str)

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
        self.running = True
        self.process = None
        self._cancel_requested = False

        

        
    def run(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        separator_path = os.path.join(base_dir, "core", "separator.py")

        cmd = [
            sys.executable,
            "-u", 
            separator_path,
            self.file,
            str(self.stems),
            self.quality,
            self.audio_format,
            self.bitrate,
            self.device,
            self.output_dir
        ]

        # Start GPU memory monitoring if using GPU
        if self.device == "cuda":
            self.start_gpu_monitor()
        
        print(f"\n🚀 Starting separation: {os.path.basename(self.file)}")
        print(f"📊 Settings: {self.stems} stems, {self.quality} quality, {self.audio_format} format, Device: {self.device}")
        filename = os.path.basename(self.file)
        self.current_file.emit(filename)
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        buffer = ""

        while True:
            # ✅ Cancel support
            if self._cancel_requested:
                break

            char = self.process.stdout.read(1)
            if not char:
                break

            if char in ("\r", "\n"):
                line = buffer.strip()
                buffer = ""

                if not line:
                    continue

                # Progress parsing
                percent = self.extract_percentage(line)
                if percent is not None and percent > self.last_progress:
                    self.progress_changed.emit(percent)
                    self.last_progress = percent

                # Output folder detection
                if 'writing to' in line.lower() or 'saved to' in line.lower():
                    folder_match = re.search(
                        r'writing to (.+)|saved to (.+)',
                        line,
                        re.IGNORECASE
                    )
                    if folder_match:
                        folder_path = folder_match.group(1) or folder_match.group(2)
                        if folder_path and os.path.exists(folder_path):
                            self.output_ready.emit(folder_path)

            else:
                buffer += char

        # Process ended or cancelled
        self.process.wait()
        self.running = False

        # Emit final progress only if not cancelled
        if not self._cancel_requested and self.last_progress < 100:
            self.progress_changed.emit(100)

        # Final output folder fallback
        if not self._cancel_requested:
            output_folder = self.get_output_folder()
            if output_folder:
                self.output_ready.emit(output_folder)

        self.finished.emit()
    
    def start_gpu_monitor(self):
        """Start monitoring GPU memory usage in a separate thread"""
        import threading
        
        def monitor_gpu():
            while self.running:
                try:
                    import torch
                    if torch.cuda.is_available():
                        memory_allocated = torch.cuda.memory_allocated() / 1e9
                        memory_reserved = torch.cuda.memory_reserved() / 1e9
                        memory_text = f"GPU: {memory_allocated:.2f}/{memory_reserved:.2f} GB"
                        self.gpu_memory_update.emit(memory_text)
                except:
                    pass
                time.sleep(2)  # Update every 2 seconds
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_gpu, daemon=True)
        monitor_thread.start()
    
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
    def cancel(self):
        self._cancel_requested = True

        if self.process:
            try:
                self.process.terminate()  # graceful stop
            except Exception:
                pass

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
        
        # Try multiple possible output locations
        
        # 1. User-specified output directory
        if self.output_dir:
            output_folder = os.path.join(self.output_dir, model_name, input_name)
            if os.path.exists(output_folder):
                return output_folder
        
        # 2. Demucs default locations
        default_locations = [
            os.path.join(os.path.expanduser("~"), "separated"),
            os.path.join(os.path.expanduser("~"), "Downloads", "Demucs"),
            os.path.join(os.path.expanduser("~"), "Desktop", "Demucs"),
            os.path.join(os.path.expanduser("~"), "Documents", "Demucs"),
            os.path.join(os.getcwd(), "separated"),
        ]
        
        for base_output in default_locations:
            output_folder = os.path.join(base_output, model_name, input_name)
            if os.path.exists(output_folder):
                return output_folder
        
        return None