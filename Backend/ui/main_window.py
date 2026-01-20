import os
import subprocess
import platform
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QFileDialog, QListWidgetItem,
    QGroupBox, QComboBox, QCheckBox, QLabel, 
    QProgressBar, QApplication, QMessageBox, QFrame,
    QAbstractItemView
)
from PyQt6.QtGui import QFont

from core.worker import SplitterWorker

AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a")

class ModernProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setFixedHeight(6)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #2d2d2d;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)

class FileItemWidget(QWidget):
    """Custom widget for file items with delete button"""
    delete_requested = pyqtSignal(str)  # Signal to emit when delete is clicked
    
    def __init__(self, filename, filepath):
        super().__init__()
        
        self.filename = filename
        self.filepath = filepath
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # File icon (simulated with text)
        icon_label = QLabel("📁")
        icon_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(icon_label)
        
        # File name
        self.name_label = QLabel(filename)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
                padding: 3px 0;
            }
        """)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label, 1)  # Stretch factor 1
        
        # Delete button (trash can icon using text)
        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ff6b6b;
                border: 1px solid #ff6b6b;
                border-radius: 4px;
                font-size: 12px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #ff6b6b20;
                color: #ff4757;
                border-color: #ff4757;
            }
            QPushButton:pressed {
                background-color: #ff6b6b40;
            }
        """)
        self.delete_btn.setToolTip("Remove from queue")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        layout.addWidget(self.delete_btn)
        
        self.setLayout(layout)
    
    def on_delete_clicked(self):
        """Emit signal when delete button is clicked"""
        self.delete_requested.emit(self.filepath)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STEM SPLITTER")
        self.resize(900, 600)
        
        # Color scheme
        self.bg_dark = "#0f0f0f"
        self.bg_card = "#1a1a1a"
        self.bg_sidebar = "#141414"
        self.accent = "#4CAF50"
        self.text_primary = "#ffffff"
        self.text_secondary = "#b0b0b0"
        
        # Set window style
        self.setStyleSheet(f"background-color: {self.bg_dark}; color: {self.text_primary};")
        
        # Queue and state
        self.queue = []  # List of file paths
        self.current_index = 0
        self.worker = None
        self.output_dir = None
        
        self.init_ui()
        
    def init_ui(self):
        # Central widget with horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left Panel (Settings)
        left_panel = QFrame()
        left_panel.setFixedWidth(300)
        left_panel.setStyleSheet(f"background-color: {self.bg_sidebar};")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(20)
        
        # Title
        title = QLabel("STEM SPLITTER")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {self.accent}; margin-bottom: 20px;")
        left_layout.addWidget(title)
        
        # Device Selection
        device_group = self.create_option_group("Device", ["Auto (Recommended)", "Force CPU", "Force GPU"])
        left_layout.addWidget(device_group)
        
        # Stem Count Selection
        stem_count_group = self.create_stem_count_group()
        left_layout.addWidget(stem_count_group)
        
        # Processing Quality
        quality_group = self.create_option_group("Processing Quality", ["Fast", "Balanced", "Best"])
        left_layout.addWidget(quality_group)
        
        # Output Audio Quality
        output_group = self.create_output_group()
        left_layout.addWidget(output_group)
        
        # Output Folder
        folder_group = self.create_folder_group()
        left_layout.addWidget(folder_group)
        
        # Start Button
        self.start_btn = QPushButton("START PROCESSING")
        self.start_btn.setFixedHeight(45)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #45a049;
            }}
            QPushButton:disabled {{
                background-color: #2d2d2d;
                color: #666;
            }}
        """)
        self.start_btn.clicked.connect(self.start_processing)
        left_layout.addWidget(self.start_btn)
        
        # Spacer
        left_layout.addStretch()
        
        # Right Panel (Work Area)
        right_panel = QFrame()
        right_panel.setStyleSheet(f"background-color: {self.bg_dark};")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(30, 30, 30, 30)
        right_layout.setSpacing(20)
        
        # Queue Section
        queue_label = QLabel("File Queue")
        queue_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.accent};")
        right_layout.addWidget(queue_label)
        
        # Queue List with custom items
        self.queue_list = QListWidget()
        self.queue_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {self.bg_card};
                border: 1px solid #333;
                border-radius: 8px;
                padding: 5px;
                color: {self.text_primary};
                font-size: 14px;
                min-height: 200px;
            }}
            QListWidget::item {{
                border: none;
                padding: 0px;
                margin: 2px;
                background-color: transparent;
            }}
            QListWidget::item:hover {{
                background-color: transparent;
            }}
            QListWidget::item:selected {{
                background-color: transparent;
            }}
        """)
        self.queue_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        right_layout.addWidget(self.queue_list)
        
        # Add Files Button
        self.add_btn = QPushButton("+ Add Audio Files")
        self.add_btn.setFixedHeight(40)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.bg_card};
                color: {self.text_primary};
                border: 2px dashed #444;
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #2a2a2a;
                border-color: {self.accent};
            }}
        """)
        self.add_btn.clicked.connect(self.add_files)
        right_layout.addWidget(self.add_btn)
        
        # Progress Section
        progress_label = QLabel("Processing Progress")
        progress_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.accent}; margin-top: 10px;")
        right_layout.addWidget(progress_label)
        
        # Progress Container
        progress_container = QWidget()
        progress_container.setStyleSheet(f"background-color: {self.bg_card}; border-radius: 8px; padding: 6px;")
        progress_container_layout = QVBoxLayout(progress_container)
        progress_container_layout.setSpacing(10)
        
        # Progress Bar
        self.progress_bar = ModernProgressBar()
        progress_container_layout.addWidget(self.progress_bar)
        
        # Progress Percentage
        self.progress_label = QLabel("Ready")
        self.progress_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.accent}; text-align: center;")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_container_layout.addWidget(self.progress_label)
        
        # Current File Label
        self.current_file_label = QLabel("")
        self.current_file_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 12px; text-align: center;")
        self.current_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_container_layout.addWidget(self.current_file_label)
        
        right_layout.addWidget(progress_container)
        
        # Output Section
        output_label = QLabel("Output")
        output_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.accent}; margin-top: 10px;")
        right_layout.addWidget(output_label)
        
        # Output Container
        output_container = QWidget()
        output_container.setStyleSheet(f"background-color: {self.bg_card}; border-radius: 8px; padding: 15px;")
        output_layout = QVBoxLayout(output_container)
        output_layout.setSpacing(10)
        
        # Output Path Display
        self.output_path_label = QLabel("Output will appear here after processing")
        self.output_path_label.setStyleSheet(f"""
            color: {self.text_primary};
            font-size: 13px;
            padding: 8px;
            background-color: #2a2a2a;
            border-radius: 4px;
            border: 1px solid #333;
            min-height: 40px;
        """)
        self.output_path_label.setWordWrap(True)
        output_layout.addWidget(self.output_path_label)
        
        # Open Output Folder Button
        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2a2a2a;
                color: {self.text_primary};
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: #333;
                border-color: {self.accent};
            }}
            QPushButton:disabled {{
                background-color: #1a1a1a;
                color: #666;
                border-color: #333;
            }}
        """)
        self.open_output_btn.clicked.connect(self.open_output_folder)
        self.open_output_btn.setEnabled(False)
        output_layout.addWidget(self.open_output_btn)
        
        right_layout.addWidget(output_container)
        
        # Spacer
        right_layout.addStretch()
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        
        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("background-color: #333;")
        main_layout.addWidget(divider)
        
        main_layout.addWidget(right_panel)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
    def create_option_group(self, title, options):
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {self.text_primary};
                font-weight: bold;
                border: 1px solid #333;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: {self.bg_card};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {self.text_secondary};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        combo = QComboBox()
        combo.addItems(options)
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                color: {self.text_primary};
                min-height: 20px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {self.text_secondary};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #2a2a2a;
                border: 1px solid #444;
                color: {self.text_primary};
                selection-background-color: {self.accent};
            }}
        """)
        
        if title == "Device":
            self.device_box = combo
        elif title == "Processing Quality":
            self.quality_box = combo
        
        layout.addWidget(combo)
        group.setLayout(layout)
        return group
    
    def create_stem_count_group(self):
        group = QGroupBox("Stem Count")
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {self.text_primary};
                font-weight: bold;
                border: 1px solid #333;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: {self.bg_card};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {self.text_secondary};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Create radio buttons for stem count
        self.stem_count_combo = QComboBox()
        self.stem_count_combo.addItems(["2 Stems (Vocals + Instrumental)", "4 Stems (Default)", "6 Stems"])
        self.stem_count_combo.setCurrentIndex(1)  # Default to 4 stems
        self.stem_count_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                color: {self.text_primary};
                min-height: 20px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {self.text_secondary};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #2a2a2a;
                border: 1px solid #444;
                color: {self.text_primary};
                selection-background-color: {self.accent};
            }}
        """)
        
        layout.addWidget(self.stem_count_combo)
        group.setLayout(layout)
        return group
    
    def create_output_group(self):
        group = QGroupBox("Output Audio Quality")
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {self.text_primary};
                font-weight: bold;
                border: 1px solid #333;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: {self.bg_card};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {self.text_secondary};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        self.output_quality_box = QComboBox()
        self.output_quality_box.addItems(["WAV (Lossless)", "MP3 - 320 kbps", "MP3 - 192 kbps"])
        self.output_quality_box.setStyleSheet(f"""
            QComboBox {{
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                color: {self.text_primary};
                min-height: 20px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {self.text_secondary};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #2a2a2a;
                border: 1px solid #444;
                color: {self.text_primary};
                selection-background-color: {self.accent};
            }}
        """)
        layout.addWidget(self.output_quality_box)
        
        group.setLayout(layout)
        return group
    
    def create_folder_group(self):
        group = QFrame()
        group.setStyleSheet(f"background-color: {self.bg_card}; border-radius: 8px; padding: 15px;")
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Label
        label = QLabel("Output folder:")
        label.setStyleSheet(f"color: {self.text_secondary}; font-size: 14px;")
        layout.addWidget(label)
        
        # Folder path display
        self.folder_label = QLabel("Default (separated folder in Home)")
        self.folder_label.setStyleSheet(f"""
            color: {self.text_primary};
            font-size: 13px;
            padding: 8px;
            background-color: #2a2a2a;
            border-radius: 4px;
            border: 1px solid #333;
        """)
        self.folder_label.setWordWrap(True)
        layout.addWidget(self.folder_label)
        
        # Select folder button
        self.folder_btn = QPushButton("Select Output Folder")
        self.folder_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2a2a2a;
                color: {self.text_primary};
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: #333;
                border-color: {self.accent};
            }}
        """)
        self.folder_btn.clicked.connect(self.select_output_dir)
        layout.addWidget(self.folder_btn)
        
        return group
    
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "", 
            "Audio Files (*.mp3 *.wav *.flac *.aac *.ogg *.m4a);;All Files (*)"
        )
        self.add_audio_files(files)
    
    def add_audio_files(self, files):
        for f in files:
            if f.lower().endswith(AUDIO_EXTENSIONS) and f not in self.queue:
                self.queue.append(f)
                self.add_file_to_list(f)
    
    def add_file_to_list(self, file_path):
        """Add a file to the queue list with delete button"""
        filename = os.path.basename(file_path)
        
        # Create custom widget
        file_widget = FileItemWidget(filename, file_path)
        file_widget.delete_requested.connect(self.remove_file)
        
        # Create list item
        item = QListWidgetItem(self.queue_list)
        item.setSizeHint(QSize(0, 50))  # Set fixed height for the item
        
        # Add widget to list
        self.queue_list.addItem(item)
        self.queue_list.setItemWidget(item, file_widget)
    
    def remove_file(self, file_path):
        """Remove a file from the queue"""
        # Find and remove the item
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            widget = self.queue_list.itemWidget(item)
            if widget and hasattr(widget, 'filepath') and widget.filepath == file_path:
                self.queue_list.takeItem(i)
                break
        
        # Remove from internal queue
        if file_path in self.queue:
            self.queue.remove(file_path)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_audio_files(files)
        event.acceptProposedAction()
    
    def select_output_dir(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder"
        )
        if folder:
            self.output_dir = folder
            self.folder_label.setText(folder)
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        
        if value == 0:
            self.progress_label.setText("Starting...")
        elif value < 100:
            self.progress_label.setText(f"{value}%")
        else:
            self.progress_label.setText("Complete!")
        
        if value >= 100:
            # Hide progress bar after a short delay
            QTimer.singleShot(2000, self.reset_progress_display)
    
    def reset_progress_display(self):
        self.progress_bar.setValue(0)
        self.progress_label.setText("Ready")
        self.current_file_label.setText("")
    
    def show_output_folder(self, output_folder):
        """Display output folder path and enable open button"""
        if os.path.exists(output_folder):
            self.output_path_label.setText(output_folder)
            self.open_output_btn.setEnabled(True)
        else:
            self.output_path_label.setText("Output folder not found")
            self.open_output_btn.setEnabled(False)
    
    def open_output_folder(self):
        """Open the output folder in system file explorer"""
        output_path = self.output_path_label.text()
        if os.path.exists(output_path):
            system = platform.system()
            try:
                if system == "Windows":
                    os.startfile(output_path)
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", output_path])
                else:  # Linux
                    subprocess.run(["xdg-open", output_path])
            except Exception as e:
                QMessageBox.warning(self, "Open Failed", f"Cannot open folder: {str(e)}")
        else:
            QMessageBox.warning(self, "Folder Not Found", "The output folder does not exist.")
    
    def start_processing(self):
        if not self.queue:
            QMessageBox.warning(
                self,
                "No Audio Selected",
                "Please add at least one audio file to the queue."
            )
            return
        
        # Disable UI elements during processing
        self.start_btn.setEnabled(False)
        self.add_btn.setEnabled(False)
        self.folder_btn.setEnabled(False)
        self.queue_list.setEnabled(False)
        
        # Show progress
        self.progress_bar.show()
        self.progress_label.setText("0%")
        
        # Reset output display
        self.output_path_label.setText("Processing...")
        self.open_output_btn.setEnabled(False)
        
        self.current_index = 0
        self.process_next_file()
    
    def process_next_file(self):
        if self.current_index >= len(self.queue):
            self.on_all_jobs_finished()
            return
        
        # Get current file
        file_path = self.queue[self.current_index]
        file_name = os.path.basename(file_path)
        self.current_file_label.setText(f"Processing: {file_name}")
        
        # Get stem count from combo box
        stem_count_text = self.stem_count_combo.currentText()
        if "2 Stems" in stem_count_text:
            stems = 2
        elif "6 Stems" in stem_count_text:
            stems = 6
        else:
            stems = 4
        
        # Quality
        quality_text = self.quality_box.currentText()
        if quality_text == "Fast":
            quality = "fast"
        elif quality_text == "Best":
            quality = "best"
        else:
            quality = "balanced"
        
        # Output format
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
        
        # Create and start worker
        self.worker = SplitterWorker(
            file_path,
            stems,
            quality,
            audio_format,
            bitrate,
            device,
            output_dir
        )
        
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.output_ready.connect(self.show_output_folder)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
    
    def on_worker_finished(self):
        self.current_index += 1
        self.process_next_file()
    
    def on_all_jobs_finished(self):
        # Re-enable UI
        self.start_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.folder_btn.setEnabled(True)
        self.queue_list.setEnabled(True)
        
        # Show completion message
        QMessageBox.information(
            self,
            "Processing Complete",
            f"Successfully processed {len(self.queue)} file(s)."
        )
        
        # Clear queue
        self.queue.clear()
        self.queue_list.clear()