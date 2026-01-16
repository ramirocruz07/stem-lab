import os
import sys
import subprocess
from PyQt6.QtCore import QThread,QObject, pyqtSignal, pyqtSlot, QRunnable

class SplitterWorker(QThread,QObject):
    def __init__(self, file, stems, quality, export_mp3, device, output_dir):
        super().__init__()
        self.file = file
        self.stems = stems
        self.quality = quality
        self.export_mp3 = export_mp3
        self.device = device
        self.output_dir = output_dir
    

    def run(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        separator_path = os.path.join(base_dir, "core", "separator.py")

        subprocess.run([
            sys.executable,
            separator_path,
            self.file,
            str(self.stems),
            self.quality,
            str(int(self.export_mp3)),
            self.device,
            self.output_dir,
        ])
