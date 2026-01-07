from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QListWidget, QFileDialog
)
from core.worker import SplitterWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stem Generator")
        self.resize(600, 400)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.list = QListWidget()
        layout.addWidget(self.list)

        self.add_btn = QPushButton("Add Audio")
        self.run_btn = QPushButton("Start")

        layout.addWidget(self.add_btn)
        layout.addWidget(self.run_btn)

        self.add_btn.clicked.connect(self.add_files)
        self.run_btn.clicked.connect(self.start)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio", "", "Audio (*.mp3 *.wav)"
        )
        self.list.addItems(files)

    def start(self):
        if self.list.count() == 0:
            return

        file = self.list.item(0).text()
        self.worker = SplitterWorker(file)
        self.worker.start()
