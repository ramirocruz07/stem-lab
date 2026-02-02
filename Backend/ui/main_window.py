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
    QAbstractItemView, QSplitter, QSizePolicy, QScrollArea
)
from PyQt6.QtGui import QFont, QIcon, QPixmap

from core.worker import SplitterWorker

AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".aacc", ".ogg", ".m4a")

class ModernProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setFixedHeight(10)
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #c3ae86;
                background-color: #f2e4c7;
                border-radius: 5px;
                padding: 0px;
            }
            QProgressBar::chunk {
                background-color: #2f6f6d;
                border-radius: 5px;
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
        
        # File icon using SVG from assets folder
        icon_label = QLabel()
        # Get the base directory (Backend folder)
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Backend/ui/
        base_dir = os.path.dirname(script_dir)  # Backend/
        assets_dir = os.path.join(base_dir, "assets")  # Backend/assets/
        icon_path = os.path.join(assets_dir, "music-folder.svg")
        
        try:
            if os.path.exists(icon_path):
                icon_pixmap = QPixmap(icon_path)
                if not icon_pixmap.isNull():
                    icon_pixmap = icon_pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    icon_label.setPixmap(icon_pixmap)
                    icon_label.setFixedSize(20, 20)
                else:
                    # Fallback if pixmap is null
                    icon_label.setText("📁")
                    icon_label.setStyleSheet("font-size: 14px;")
                    icon_label.setFixedSize(20, 20)
            else:
                # Fallback to text icon if SVG not found
                icon_label.setText("📁")
                icon_label.setStyleSheet("font-size: 14px;")
                icon_label.setFixedSize(20, 20)
        except Exception:
            # Fallback on any error
            icon_label.setText("📁")
            icon_label.setStyleSheet("font-size: 14px;")
            icon_label.setFixedSize(20, 20)
        layout.addWidget(icon_label)
        
        # File name
        self.name_label = QLabel(filename)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #3c2f26;
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
        
        # Set application icon/logo
        self.set_app_icon()
        
        self.adjustSize()
        self.setMinimumSize(820, 520)
        
        # Color palette (warm parchment theme)
        self.bg_dark = "#f5ecd8"        # main background (paper)
        self.bg_card = "#f2e4c7"        # cards / panels
        self.bg_sidebar = "#f2e4c7"     # left sidebar
        self.accent = "#c45525"         # primary accent (warm orange/red)
        self.accent_soft = "#2f6f6d"    # secondary accent (muted teal)
        self.accent_hover = "#d9642b"   # hover state
        self.text_primary = "#3c2f26"
        self.text_secondary = "#7a5f4b"
        self.border_color = "#d4c4a3"
        
        # Set window style with scrollbar styling
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.bg_dark};
                color: {self.text_primary};
            }}
            QScrollBar:vertical {{
                background: #f2e4c7;
                width: 10px;
                margin: 4px 0 4px 0;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: #c3ae86;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #b09568;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                background: none;
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background: #f2e4c7;
                height: 10px;
                margin: 0 4px 0 4px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal {{
                background: #c3ae86;
                min-width: 20px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: #b09568;
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                background: none;
                width: 0px;
            }}
        """)
        self.setStyleSheet(self.styleSheet() + f"""
    QMenuBar {{
        background-color: {self.bg_card};
        color: {self.text_primary};
    }}

    QMenuBar::item {{
        background: transparent;
        padding: 6px 12px;
        color: {self.text_primary};
    }}

    QMenuBar::item:selected {{
        background-color: {self.accent};
        color: white;
    }}

    QMenu {{
        background-color: {self.bg_card};
        color: {self.text_primary};
        border: 1px solid {self.border_color};
    }}

    QMenu::item {{
        padding: 6px 16px;
        color: {self.text_primary};
    }}

    QMenu::item:selected {{
        background-color: {self.accent};
        color: white;
    }}
""")

        
        # Queue and state
        self.queue = []  # List of file paths
        self.current_index = 0
        self.worker = None
        self.output_dir = None
        self.gpu_available = self.check_gpu_availability()
        
        self.init_ui()
        menubar = self.menuBar()
        help_menu = menubar.addMenu("Help")

        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)

        contact_action = help_menu.addAction("Contact")
        contact_action.triggered.connect(self.show_contact_dialog)
    
    def set_app_icon(self):
        """Set the application window icon"""
        # Get the base directory (Backend folder)
        # __file__ is Backend/ui/main_window.py, so go up one level to Backend/
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Backend/ui/
        base_dir = os.path.dirname(script_dir)  # Backend/
        assets_dir = os.path.join(base_dir, "assets")  # Backend/assets/
        
        # Try logo file locations in assets folder
        logo_paths = [
            os.path.join(assets_dir, "logo.png"),
            os.path.join(assets_dir, "logo.ico"),
            os.path.join(assets_dir, "logo.svg"),
            os.path.join(assets_dir, "stem-splitter-logo.png"),
            os.path.join(assets_dir, "stem-splitter-logo.ico"),
            os.path.join(assets_dir, "stem-splitter-logo.svg"),
        ]
        
        icon_set = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    icon = QIcon(logo_path)
                    if not icon.isNull():
                        self.setWindowIcon(icon)
                        # Also set for the application
                        QApplication.setWindowIcon(icon)
                        icon_set = True
                        print(f"✅ Application icon set from: {logo_path}")
                        break
                except Exception as e:
                    print(f"⚠️  Error loading icon from {logo_path}: {e}")
                    continue
        
        if not icon_set:
            print(f"⚠️  Logo file not found in assets folder.")
            print(f"   Looking in: {assets_dir}")
            print(f"   Tried paths:")
            for lp in logo_paths:
                exists = "✓" if os.path.exists(lp) else "✗"
                print(f"     {exists} {lp}")
            print("   Using default icon.")
    
    def check_gpu_availability(self):
        """Check if CUDA GPU is available"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
                print(f"✅ GPU Available: {gpu_name} ({gpu_memory:.1f} GB)")
                return True
            else:
                print("⚠️  No GPU available, using CPU only")
                return False
        except Exception as e:
            print(f"⚠️  Error checking GPU: {e}")
            return False
        
    def init_ui(self):
        # Central widget with horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left Panel (Settings) - no scroll area, ensure everything fits
        left_panel = QFrame()
        left_panel.setFixedWidth(420)
        left_panel.setStyleSheet(
            f"background-color: {self.bg_sidebar}; border-radius: 20px; "
            f"border: 1px solid {self.border_color};"
        )
        left_panel.setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Expanding
            )
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 18, 20, 18)
        left_layout.setSpacing(14)
        
        # Title
        title = QLabel("STEM SPLITTER")
        title.setStyleSheet(
            f"font-size: 24px; font-weight: bold; letter-spacing: 0.05em; "
            f"color: {self.accent}; margin: 0px; padding: 0px;"
        )
        left_layout.addWidget(title)
        
        # Device Selection with GPU status
        device_group = self.create_device_group()
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
        
        # Output Folder - FIXED: Only create this once
        folder_group = self.create_folder_group()
        left_layout.addWidget(folder_group)
    
        
        # Add spacer to push buttons to the bottom
        left_layout.addStretch()
        
        # Start Button
        self.start_btn = QPushButton("START PROCESSING")
        self.start_btn.setFixedHeight(44)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent};
                color: #fdf7ec;
                border: 1px solid #a24822;
                border-radius: 16px;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 0.06em;
            }}
            QPushButton:hover {{
                background-color: {self.accent_hover};
            }}
            QPushButton:disabled {{
                background-color: #e2d4ba;
                color: #a58a70;
                border-color: #d0c3a8;
            }}
        """)
        self.start_btn.clicked.connect(self.start_processing)
        left_layout.addWidget(self.start_btn)
      
        
        # Stop Button
        self.cancel_btn = QPushButton("STOP")
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #b03b2b;
                color: #fdf7ec;
                border: 1px solid #8c2f22;
                border-radius: 16px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #c94a38;
            }}
            QPushButton:disabled {{
                background-color: #e2d4ba;
                color: #a58a70;
                border-color: #d0c3a8;
            }}
        """)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_processing)
        left_layout.addWidget(self.cancel_btn)
        
        # Right Panel (Work Area)
        right_panel = QFrame()
        right_panel.setMinimumWidth(500)
        right_panel.setStyleSheet(
            f"background-color: {self.bg_card}; border-radius: 20px; "
            f"border: 1px solid {self.border_color};"
        )
        right_panel.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding
            )
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(24, 20, 24, 20)
        right_layout.setSpacing(16)
        
        # Queue Section
        queue_label = QLabel("File Queue")
        queue_label.setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {self.accent}; "
            f"margin: 0px; padding: 0px;"
        )
        right_layout.addWidget(queue_label)
        
        # Add Files Button (moved before queue list)
        self.add_btn = QPushButton("+ Add Audio Files")
        self.add_btn.setFixedHeight(48)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f7ebd2;
                color: {self.text_primary};
                border: 2px dashed #c3ae86;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #f3e2c2;
                border-color: {self.accent};
                color: {self.accent};
            }}
        """)
        self.add_btn.clicked.connect(self.add_files)
        right_layout.addWidget(self.add_btn)
        
        # Queue List with custom items
        self.queue_list = QListWidget()
        self.queue_list.setStyleSheet(f"""
            QListWidget {{
                background-color: #f7ebd2;
                border: 1px solid #d4c4a3;
                border-radius: 12px;
                padding: 8px;
                color: {self.text_primary};
                font-size: 13px;
                min-height: 200px;
            }}
            QListWidget::item {{
                border-radius: 8px;
                margin: 2px;
            }}
        """)
        self.queue_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.queue_list.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        right_layout.addWidget(self.queue_list)
        
        # Progress Section
        progress_label = QLabel("Processing Progress")
        progress_label.setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {self.accent}; "
            f"margin: 0px; padding: 0px;"
        )
        right_layout.addWidget(progress_label)
        
        # Progress Container (no border, clean look)
        progress_container = QWidget()
        progress_container.setStyleSheet(
            f"background-color: #f7ebd2; border-radius: 16px;"
        )
        progress_container_layout = QVBoxLayout(progress_container)
        progress_container_layout.setContentsMargins(20, 20, 20, 20)
        progress_container_layout.setSpacing(14)
        
        # Progress Bar (with proper padding to align with rounded corners)
        self.progress_bar = ModernProgressBar()
        progress_container_layout.addWidget(self.progress_bar)
        
        # Progress Percentage (no border, clean look)
        self.progress_label = QLabel("Ready")
        self.progress_label.setStyleSheet(
            f"font-size: 18px; font-weight: 600; color: {self.accent_soft}; "
            f"text-align: center; background: transparent; border: none;"
        )
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_container_layout.addWidget(self.progress_label)
        
        # Current file being processed (no border)
        self.current_file_label = QLabel("")
        self.current_file_label.setStyleSheet(
            f"color: {self.text_secondary}; font-size: 13px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        self.current_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_container_layout.addWidget(self.current_file_label)
        
        # Hardware Usage Label (no border)
        self.hardware_label = QLabel("")
        self.hardware_label.setStyleSheet(
            f"color: {self.text_secondary}; font-size: 11px; text-align: center; "
            f"background: transparent; border: none;"
        )
        self.hardware_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_container_layout.addWidget(self.hardware_label)
        
        right_layout.addWidget(progress_container)
        
        # Hidden output widgets (for logic only, not displayed)
        # self.output_path_label = QLabel("", self)
        # self.open_output_btn = QPushButton("Open Output Folder", self)
        # self.open_output_btn.setEnabled(False)
        # self.open_output_btn.clicked.connect(self.open_output_folder)
        
        # # Spacer
        right_layout.addStretch()
        
        # Create splitter for panels (no scroll area - ensure everything fits)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)  # sidebar
        splitter.setStretchFactor(1, 1)  # content
        splitter.setChildrenCollapsible(False)
        # Style the splitter handle to match theme
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: #d4c4a3;
                width: 2px;
            }}
            QSplitter::handle:hover {{
                background-color: {self.accent};
            }}
        """)
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Set window size - ensure everything fits without scrolling
        self.resize(1200, 750) 
        self.setMinimumSize(1100, 700)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
    
    # REMOVE THE DUPLICATE create_folder_group() METHOD
    # There was a duplicate method at the end of the class that was causing the issue
    
    def create_device_group(self):
        group = QGroupBox("Device Selection")
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {self.text_primary};
                font-weight: 600;
                border: 1px solid {self.border_color};
                border-radius: 12px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: {self.bg_card};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                left: 0px;
                right: 0px;
                padding: 0 5px 0 5px;
                color: {self.text_secondary};
                font-size: 13px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 6, 12, 8)
        layout.setSpacing(8)
        
        # Device combo box
        self.device_box = QComboBox()
        self.device_box.setEditable(True)              # 👈 MUST come first

        self.device_box.lineEdit().setReadOnly(True)
        self.device_box.lineEdit().setFrame(False)
        reason = self.get_gpu_unavailable_reason()
        if reason:
            self.device_box.setToolTip(reason)
            self.device_box.setStyleSheet(f"""
    QComboBox QLineEdit {{
        color: {self.text_secondary};
        background: transparent;
    }}
""")
      
        if self.gpu_available:
            try:
                import torch
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
                self.device_box.addItems([
                    f"Auto (GPU Recommended) - {gpu_name}",
                    "Force CPU",
                    f"Force GPU - {gpu_name} ({gpu_memory:.1f}GB)"
                ])
            except:
                self.device_box.addItems(["Auto (Recommended)", "Force CPU", "Force GPU"])
        else:
            self.device_box.addItems(["Auto (CPU Only)", "Force CPU"])
            # Disable GPU option
            for i in range(self.device_box.count()):
                if "GPU" in self.device_box.itemText(i):
                    self.device_box.model().item(i).setEnabled(False)
        
        self.device_box.setStyleSheet(f"""
            QComboBox {{
                background-color: #f7ebd2;
                border: 1px solid {self.border_color};
                border-radius: 8px;
                padding: 10px 12px;
                color: {self.text_primary};
                min-height: 28px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                width:28px
            }}
            QComboBox::down-arrow {{
                image: url(assets/dropdown-svgrepo-com.svg);
                width: 32px;
                height: 32px;
              
                margin-right: 10px;
            }}
            QComboBox:hover {{
                border-color: {self.accent};
            }}
            QComboBox QAbstractItemView {{
                background-color: #f7ebd2;
                border: 1px solid {self.border_color};
                border-radius: 8px;
                color: {self.text_primary};
                selection-background-color: {self.accent};
                selection-color: white;
                padding: 4px;
            }}
        """)
        
        layout.addWidget(self.device_box)
        group.setLayout(layout)
        return group
    def show_about_dialog(self):
        QMessageBox.information(
            self,
            "About Stem Splitter",
            (
                "<div style='color:#7a5f4b; font-size:13px;'>"
                "<b style='color:#c45525; font-size:16px;'>STEM SPLITTER</b><br>"
                "<span style='color:#7a5f4b;'>Version 1.0.0</span><br><br>"

                "© 2026 <b>Rohan Kadiyal</b><br><br>"

                "<b style='color:#2f6f6d;'>License:</b> MIT License<br><br>"

                "<span style='color:#5f4b3a;'>"
                "This software is provided <i>\"as is\"</i>, without warranty of any kind. "
                "The author is not responsible for data loss, hardware damage, or any issues "
                "arising from its use."
                "</span><br><br>"

                "<b style='color:#2f6f6d;'>Third-party software:</b><br>"
                "• Demucs (MIT)<br>"
                "• PyTorch (BSD-style)<br>"
                "• Qt / PyQt6 (LGPL v3)<br><br>"

                "<span style='font-size:11px; color:#7a5f4b;'>"
                "Not affiliated with or endorsed by Meta, Facebook, or the Demucs authors."
                "</span>"
                "</div>"
            )
        )
    def show_contact_dialog(self):
        QMessageBox.information(
            self,
            "Contact",
            (
                "<div style='color:#7a5f4b; font-size:13px;'>"
                "<b style='color:#c45525; font-size:15px;'>Contact</b><br><br>"

                "For feedback, bugs, or collaboration:<br><br>"

                "<b>Email:</b> "
                "<span style='color:#2f6f6d;'>rohan.k.codersboutique@gmail.com</span><br><br>"

                "<b>GitHub:</b> "
                "<span style='color:#2f6f6d;'>https://github.com/ramirocruz07</span><br><br>"

                "<span style='font-size:11px; color:#7a5f4b;'>"
                "Please include your OS and GPU details when reporting issues."
                "</span>"
                "</div>"
            )
        )

    
    def create_status_group(self):
        group = QFrame()
        group.setStyleSheet(f"background-color: {self.bg_card}; border-radius: 8px; padding: 15px;")
        
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Status label
        status_label = QLabel("Hardware Status")
        status_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 14px; font-weight: bold;")
        layout.addWidget(status_label)
        
        # GPU/CPU status
        if self.gpu_available:
            try:
                import torch
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
                status_text = f"✅ GPU Available\n{gpu_name}\n{gpu_memory:.1f} GB VRAM"
                color = "#4CAF50"
            except:
                status_text = "✅ GPU Available"
                color = "#4CAF50"
        else:
            status_text = "⚠️  CPU Only Mode"
            color = "#FF9800"
        
        self.status_label = QLabel(status_text)
        self.status_label.setStyleSheet(f"""
            color: {color};
            font-size: 12px;
            padding: 8px;
            background-color: #2a2a2a;
            border-radius: 4px;
            border: 1px solid #333;
        """)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        return group
    
    def create_option_group(self, title, options):
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {self.text_primary};
                font-weight: 600;
                border: 1px solid {self.border_color};
                border-radius: 12px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: {self.bg_card};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                left: 0px;
                right: 0px;
                padding: 0 5px 0 5px;
                color: {self.text_secondary};
                font-size: 13px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 6, 12, 8)
        layout.setSpacing(8)
        
        combo = QComboBox()
        combo.addItems(options)
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.bg_dark};
                border: 1px solid {self.border_color};
                border-radius: 8px;
                padding: 10px 14px;
                color: {self.text_primary};
                min-height: 32px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: url(assets/dropdown-svgrepo-com.svg);
                width: 32px;
                height: 32px;
         
                margin-right: 8px;
            }}
            QComboBox:hover {{
                border-color: {self.accent};
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.bg_dark};
                border: 1px solid {self.border_color};
                color: {self.text_primary};
                selection-background-color: {self.accent};
                selection-color: white;
                padding: 4px;
            }}
        """)
        
        if title == "Processing Quality":
            self.quality_box = combo
        
        layout.addWidget(combo)
        group.setLayout(layout)
        
        
        return group
    
    def create_stem_count_group(self):
        group = QGroupBox("Stem Count")
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {self.text_primary};
                font-weight: 600;
                border: 1px solid {self.border_color};
                border-radius: 12px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: {self.bg_card};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                left: 0px;
                right: 0px;
                padding: 0 5px 0 5px;
                color: {self.text_secondary};
                font-size: 13px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 6, 12, 8)
        layout.setSpacing(8)
        
        # Create radio buttons for stem count
        self.stem_count_combo = QComboBox()
        self.stem_count_combo.addItems(["2 Stems (Vocals + Instrumental)", "4 Stems (Default)", "6 Stems"])
        self.stem_count_combo.setCurrentIndex(1)  # Default to 4 stems
        self.stem_count_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.bg_dark};
                border: 1px solid {self.border_color};
                border-radius: 8px;
                padding: 10px 14px;
                color: {self.text_primary};
                min-height: 32px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: url(assets/dropdown-svgrepo-com.svg);
                width: 32px;
                height: 32px;
          
                margin-right: 8px;
            }}
            QComboBox:hover {{
                border-color: {self.accent};
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.bg_dark};
                border: 1px solid {self.border_color};
                color: {self.text_primary};
                selection-background-color: {self.accent};
                selection-color: white;
                padding: 4px;
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
                font-weight: 600;
                border: 1px solid {self.border_color};
                border-radius: 12px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: {self.bg_card};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                left: 0px;
                right: 0px;
                padding: 0 5px 0 5px;
                color: {self.text_secondary};
                font-size: 13px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 6, 12, 8)
        layout.setSpacing(8)
        
        self.output_quality_box = QComboBox()
        self.output_quality_box.addItems(["WAV (Lossless)", "MP3 - 320 kbps", "MP3 - 192 kbps"])
        self.output_quality_box.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.bg_dark};
                border: 1px solid {self.border_color};
                border-radius: 8px;
                padding: 10px 14px;
                color: {self.text_primary};
                min-height: 32px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                width:30px;
                
            }}
            QComboBox::down-arrow {{
                image: url(assets/dropdown-svgrepo-com.svg);
                width: 32px;
                height: 32px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
            
                margin-right: 8px;
            }}
            QComboBox:hover {{
                border-color: {self.accent};
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.bg_dark};
                border: 1px solid {self.border_color};
                color: {self.text_primary};
                selection-background-color: {self.accent};
                selection-color: white;
                padding: 4px;
            }}
        """)
        layout.addWidget(self.output_quality_box)
        
        group.setLayout(layout)
        return group
    
    
    def get_gpu_unavailable_reason(self):
        import torch, platform

        return (
        "GPU acceleration is unavailable.\n\n"
        "• Test mode\n"
        "• CUDA disabled intentionally\n"
        "• App will run on CPU"
    )

        system = platform.system()

        if system == "Windows":
            return (
                "GPU acceleration is unavailable.\n\n"
                "Possible reasons:\n"
                "• No NVIDIA GPU detected\n"
                "• AMD GPUs are not supported (CUDA is NVIDIA-only)\n"
                "• NVIDIA drivers are missing or outdated\n\n"
                "The app will run using CPU instead."
            )

        return (
            "GPU acceleration is unavailable.\n\n"
            "CUDA requires an NVIDIA GPU.\n"
            "The app will run using CPU instead."
        )

    
    def create_folder_group(self):
        group = QGroupBox("Output folder")
        group.setMaximumHeight(110)  # Limit maximum height
        group.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {self.text_primary};
                font-weight: 600;
                border: 1px solid {self.border_color};
                border-radius: 12px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: {self.bg_card};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                left: 0px;
                right: 0px;
                padding: 0 5px 0 5px;
                color: {self.text_secondary};
                font-size: 13px;
            }}
        """)

        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 6, 12, 8)
        layout.setSpacing(6)

        # Container for path with fixed height (no border, just background)
        path_container = QFrame()
        path_container.setFixedHeight(40)  # Fixed height
        path_container.setStyleSheet(f"""
            QFrame {{
                background-color: #f7ebd2;
                border-radius: 8px;
            }}
        """)
        path_layout = QVBoxLayout(path_container)
        path_layout.setContentsMargins(8, 0, 8, 0)
        
        self.folder_label = QLabel("C:\\Users\\username\\Documents\\STEM SPLITTER")
        self.folder_label.setWordWrap(True)
        self.folder_label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_primary};
                font-size: 11px;
                font-family: "Consolas", "Monospace";
                qproperty-alignment: 'AlignVCenter | AlignLeft';
            }}
        """)
        self.folder_label.setMaximumHeight(40)  # Limit height
        path_layout.addWidget(self.folder_label)
        
        layout.addWidget(path_container)
        
        # Select folder button (make it look like a proper button)
        self.folder_btn = QPushButton("Select Output Folder")
        self.folder_btn.setFixedHeight(36)
        self.folder_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent};
                color: #fdf7ec;
                border: 1px solid #a24822;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: {self.accent_hover};
            }}
            QPushButton:pressed {{
                background-color: #a24822;
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
        item.setSizeHint(QSize(0, 56))  # Set fixed height for the item
        
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
        self.hardware_label.setText("")
    
    def update_hardware_usage(self, device_type):
        """Update hardware usage display"""
        if device_type == "cuda":
            try:
                import torch
                if torch.cuda.is_available():
                    print(self.get_gpu_unavailable_reason())

                    memory_allocated = torch.cuda.memory_allocated() / 1e9
                    memory_reserved = torch.cuda.memory_reserved() / 1e9
                    self.hardware_label.setText(f"GPU Memory: {memory_allocated:.2f}/{memory_reserved:.2f} GB")
            except:
                self.hardware_label.setText("Using GPU")
        else:
            self.hardware_label.setText("Using CPU")
    
    def show_output_folder(self, output_folder):
        """Display output folder path and enable open button"""
        # If these widgets are not present (current UI hides them), just skip
        if not hasattr(self, "output_path_label") or not hasattr(self, "open_output_btn"):
            return

        if output_folder and os.path.exists(output_folder):
            self.output_path_label.setText(output_folder)
            self.open_output_btn.setEnabled(True)
            
            # Count how many stem files were created
            stem_files = [f for f in os.listdir(output_folder) if f.endswith(('.wav', '.mp3', '.flac'))]
            if stem_files:
                self.output_path_label.setText(f"{output_folder}\n\nCreated {len(stem_files)} stem files")
        else:
            # Try to find output in default locations
            default_paths = [
                os.path.join(os.path.expanduser("~"), "separated"),
                os.path.join(os.path.expanduser("~"), "Downloads", "Demucs"),
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    self.output_path_label.setText(f"Output might be in: {path}\n\nPlease check this folder manually")
                    self.open_output_btn.setEnabled(True)
                    return
            
            self.output_path_label.setText("Output folder not found. Check console for details.")
            self.open_output_btn.setEnabled(False)
    
    def open_output_folder(self):
        """Open the output folder in system file explorer"""
        if not hasattr(self, "output_path_label"):
            return

        output_path = self.output_path_label.text().split('\n')[0]  # Get first line
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
    
    def cancel_processing(self):
        if self.worker:
            self.worker.cancel()
    
    def start_processing(self):
        if not self.queue:
            QMessageBox.warning(
                self,
                "No Audio Selected",
                "Please add at least one audio file to the queue."
            )
            return
        
        print(f"DEBUG: Starting processing for {len(self.queue)} files")
        
        # Reset state
        self.current_index = 0
        
        # Disable UI elements during processing
        self.start_btn.setEnabled(False)
        self.add_btn.setEnabled(False)
        self.folder_btn.setEnabled(False)
        self.queue_list.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        
        # Show progress
        self.progress_bar.show()
        self.progress_label.setText("0%")
        
        # Reset progress display
        self.current_file_label.setText("")
        self.hardware_label.setText("")
        
        # Clean up any existing worker
        if self.worker:
            try:
                self.worker.disconnect()
                self.worker.deleteLater()
            except:
                pass
            self.worker = None
        
        # Start processing first file
        self.process_next_file()
    
    def update_current_file(self, filename):
        """Update the current file being processed"""
        if filename:
            self.current_file_label.setText(f"Processing: {filename}")
            self.current_file_label.show()
        else:
            self.current_file_label.setText("")
            self.current_file_label.hide()
    
    def process_next_file(self):
        print(f"DEBUG: process_next_file called, index: {self.current_index}")
        self.progress_bar.setValue(0)

        if self.current_index >= len(self.queue):
            print(f"DEBUG: No more files to process. Index: {self.current_index}, Queue length: {len(self.queue)}")
            self.on_all_jobs_finished()
            return
        
        # Get current file
        file_path = self.queue[self.current_index]
        file_name = os.path.basename(file_path)
        print(f"DEBUG: Processing file {self.current_index + 1}/{len(self.queue)}: {file_name}")
    
    # Update current file display
        self.update_current_file(file_name)
     
        
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
        
        # Device - parse from combo box text
        device_text = self.device_box.currentText()
        if "CPU" in device_text:
            device = "cpu"
            self.update_hardware_usage("cpu")
        elif "GPU" in device_text:
            device = "cuda"
            self.update_hardware_usage("cuda")
        else:
            device = "auto"
            # Auto-detect based on availability
            if self.gpu_available:
                self.update_hardware_usage("cuda")
            else:
                self.update_hardware_usage("cpu")
        
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
        self.worker.current_file.connect(self.update_current_file)
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.output_ready.connect(self.show_output_folder)
        self.worker.gpu_memory_update.connect(self.update_hardware_label)  # NEW
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
    
    def on_worker_finished(self):
        """Called when a worker finishes processing one file"""
        print(f"DEBUG: Worker finished for file {self.current_index + 1} of {len(self.queue)}")
        
        # Check if worker was cancelled
        if self.worker and getattr(self.worker, "_cancel_requested", False):
            print("DEBUG: Worker was cancelled")
            self.on_cancelled()
            return
        
        # Move to next file
        self.current_index += 1
        
        # Process next file if any remaining
        if self.current_index < len(self.queue):
            print(f"DEBUG: Processing next file {self.current_index + 1}/{len(self.queue)}")
            # Clean up the worker before starting next one
            if self.worker:
                try:
                    self.worker.disconnect()
                    self.worker.deleteLater()
                except:
                    pass
                self.worker = None
            
            # Add a small delay before starting next file
            QTimer.singleShot(500, self.process_next_file)
        else:
            print("DEBUG: All files processed, finishing up")
            # Clean up worker
            if self.worker:
                try:
                    self.worker.disconnect()
                    self.worker.deleteLater()
                except:
                    pass
                self.worker = None
            
            # Show completion
            QTimer.singleShot(1000, self.on_all_jobs_finished)
                
    def on_cancelled(self):
        self.queue.clear()
        self.queue_list.clear()

        self.progress_bar.setValue(0)
        self.progress_label.setText("Cancelled")
        self.current_file_label.setText("")

        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.add_btn.setEnabled(True)
        self.folder_btn.setEnabled(True)
        self.queue_list.setEnabled(True)

            
    def update_hardware_label(self, text):
        """Update hardware label with GPU memory info"""
        self.hardware_label.setText(text)

    
    def on_all_jobs_finished(self):
        """Called when all files are processed"""
        print("DEBUG: on_all_jobs_finished called")
        
        # Re-enable UI
        self.start_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.folder_btn.setEnabled(True)
        self.queue_list.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        # Update progress display
        self.progress_label.setText("Completed!")
        self.current_file_label.setText("")
        self.hardware_label.setText("")
        
        # Show completion message if we processed any files
        if len(self.queue) > 0:
            QMessageBox.information(
                self,
                "Processing Complete",
                f"Successfully processed {len(self.queue)} file(s)."
            )
        
        # Clear queue and reset index
        self.queue.clear()
        self.queue_list.clear()
        self.current_index = 0  # Reset index for next batch
        
        # Reset progress bar after delay
        QTimer.singleShot(2000, self.reset_progress_display)
