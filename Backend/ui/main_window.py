from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QListWidget, QFileDialog,
    QRadioButton, QGroupBox, QComboBox, QCheckBox, QLabel,QProgressBar,QApplication,QMessageBox,QPushButton
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
        layout.addWidget(QLabel("Output Audio Quality"))

        self.output_quality_box = QComboBox()
        self.output_quality_box.addItems([
            "WAV (Lossless)",
            "MP3 – High (320 kbps)",
            "MP3 – Medium (192 kbps)"
        ])

        layout.addWidget(self.output_quality_box)

        # -------- START BUTTON --------
        self.run_btn = QPushButton("Start")
        self.run_btn.clicked.connect(self.start)
        layout.addWidget(self.run_btn)
        
        #progress bar
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.progress.hide()
        layout.addWidget(self.progress)
    
        
        
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio", "", "Audio (*.mp3 *.wav)"
        )
        self.list.addItems(files)
        
    def update_progress(self, value):
        self.progress.setValue(value)
        if value >= 100:
        # Optional: hide after completion
            self.progress.hide()
        
    def select_output_dir(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder"
        )
        if folder:
            self.output_dir = folder
            self.output_label.setText(f"Output folder: {folder}")
    
    def on_worker_finished(self):
        self.output_quality_box.setEnabled(True)
        self.run_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.list.setEnabled(True)
        self.device_box.setEnabled(True)
        self.quality_box.setEnabled(True)
        
        self.output_btn.setEnabled(True)
        self.progress.hide()

    def start(self):
        if self.list.count() == 0:
            QMessageBox.warning(
            self,
            "No Audio Selected",
            "Please select at least one audio file before starting."
        )
            return
        self.run_btn.setEnabled(False)
        self.add_btn.setEnabled(False)
        self.list.setEnabled(False)
        self.device_box.setEnabled(False)
        self.quality_box.setEnabled(False)
        self.output_quality_box.setEnabled(False)


        self.output_btn.setEnabled(False)
        self.progress.setValue(0)
        
        self.progress.show()

        file = self.list.item(0).text()

        # Stem count
        if self.radio_2.isChecked():
            stems = 2
        elif self.radio_6.isChecked():
            stems = 6
        else:
            stems = 4
        quality=self.quality_box.currentText().lower()

        output_quality = self.output_quality_box.currentText()

        if "WAV" in output_quality:
            audio_format = "wav"
            bitrate = ""
        elif "320" in output_quality:
            audio_format = "mp3"
            bitrate = "320"
        else:
            audio_format = "mp3"
            bitrate = "192"
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
            audio_format,
            bitrate,
            device,
            output_dir
        )
        print(type(self.worker))

        self.worker.progress_changed.connect(self.update_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

