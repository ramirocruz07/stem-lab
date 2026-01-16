import os
import sys
import subprocess
from PyQt6.QtCore import QThread,QObject, pyqtSignal, pyqtSlot, QRunnable

class SplitterWorker(QThread):
    finished = pyqtSignal()
    progress_changed = pyqtSignal(int)
    def __init__(self, file, stems, quality, export_mp3, device, output_dir, progress):
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

        process = subprocess.Popen(
            [
                sys.executable,
                separator_path,
                self.file,
                str(self.stems),
                self.quality,
                str(int(self.export_mp3)),
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
