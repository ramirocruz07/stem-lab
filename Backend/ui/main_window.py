from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QListWidget, QFileDialog,
    QRadioButton, QGroupBox, QComboBox, QCheckBox, QLabel
)

from core.worker import SplitterWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stem Splitter")
        self.resize(600, 500)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        self.device_box = QComboBox()
        self.device_box.addItems([
            "Auto (Recommended)",
            "Force CPU",
            "Force GPU",
        ])
        layout.addWidget(self.device_box)

        # -------- FILE LIST --------
        self.list = QListWidget()
        layout.addWidget(self.list)

        # -------- ADD FILE BUTTON --------
        self.add_btn = QPushButton("Add Audio")
        self.add_btn.clicked.connect(self.add_files)
        layout.addWidget(self.add_btn)

        # -------- STEM OPTIONS --------
        stem_group = QGroupBox("Stem Count")
        stem_layout = QVBoxLayout()

        self.radio_2 = QRadioButton("2 Stems (Vocals + Instrumental)")
        self.radio_4 = QRadioButton("4 Stems (Default)")
        self.radio_6 = QRadioButton("6 Stems")

        self.radio_4.setChecked(True)

        stem_layout.addWidget(self.radio_2)
        stem_layout.addWidget(self.radio_4)
        stem_layout.addWidget(self.radio_6)
        stem_group.setLayout(stem_layout)

        layout.addWidget(stem_group)

        # -------- QUALITY --------
        self.quality_box = QComboBox()
        self.quality_box.addItems(["Fast", "Balanced", "Best"])
        layout.addWidget(self.quality_box)
        
        #output directory
        self.output_dir = None
        self.output_label = QLabel("Output folder: Default (Demucs)")
        layout.addWidget(self.output_label)

        self.output_btn = QPushButton("Select Output Folder")
        self.output_btn.clicked.connect(self.select_output_dir)
        layout.addWidget(self.output_btn)
        
        
        # -------- OUTPUT --------
        self.chk_mp3 = QCheckBox("Export MP3")
        layout.addWidget(self.chk_mp3)

        # -------- START BUTTON --------
        self.run_btn = QPushButton("Start")
        self.run_btn.clicked.connect(self.start)
        layout.addWidget(self.run_btn)
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio", "", "Audio (*.mp3 *.wav)"
        )
        self.list.addItems(files)
    def select_output_dir(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder"
        )
        if folder:
            self.output_dir = folder
            self.output_label.setText(f"Output folder: {folder}")

    def start(self):
        if self.list.count() == 0:
            return

        file = self.list.item(0).text()

        # Stem count
        if self.radio_2.isChecked():
            stems = 2
        elif self.radio_6.isChecked():
            stems = 6
        else:
            stems = 4

        quality = self.quality_box.currentText().lower()
        export_mp3 = self.chk_mp3.isChecked()

        # Device
        device_text = self.device_box.currentText()
        if "CPU" in device_text:
            device = "cpu"
        elif "GPU" in device_text:
            device = "cuda"
        else:
            device = "auto"
        
        output_dir = self.output_dir or ""


        self.worker = SplitterWorker(
            file,
            stems,
            quality,
            export_mp3,
            device,
            output_dir
        )
        self.worker.start()

