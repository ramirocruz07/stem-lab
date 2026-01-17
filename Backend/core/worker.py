import os
import sys
import subprocess
from PyQt6.QtCore import QThread,QObject, pyqtSignal, pyqtSlot, QRunnable

class SplitterWorker(QThread):
    finished = pyqtSignal()
    progress_changed = pyqtSignal(int)
    eta = pyqtSignal(str)
    def __init__(self, file, stems, quality, audio_format, bitrate, device, output_dir):
        super().__init__()
        self.file = file
        self.stems = stems
        self.audio_format=audio_format
        self.quality=quality
        self.device = device
        self.output_dir = output_dir
        self.bitrate=bitrate
    

    def run(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        separator_path = os.path.join(base_dir, "core", "separator.py")

        process = subprocess.Popen(
            [
                sys.executable,
                separator_path,
                self.file,
                str(self.stems),
                self.quality,
                self.audio_format,
                self.bitrate,
                self.device,
                self.output_dir
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            line = line.strip()
            print(line)

            # Parse progress percentage
            if "%" in line:
                try:
                    percent = int(line.split("%")[0].split()[-1])
                    self.progress_changed.emit(percent)
                except:
                    pass

        process.wait()
        self.progress_changed.emit(100)
        self.finished.emit()
