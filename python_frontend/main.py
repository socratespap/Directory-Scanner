#!/usr/bin/env python3
"""
Directory Scanner - Python Frontend
A modern GUI application for scanning and analyzing large files on disk.
"""

import sys
import json
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import threading
import time
try:
    from send2trash import send2trash
except ImportError:
    send2trash = None

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QFileDialog,
    QProgressBar, QTextEdit, QSplitter, QHeaderView, QMessageBox,
    QComboBox, QLineEdit, QGroupBox, QGridLayout, QFrame, QDialog,
    QRadioButton, QButtonGroup, QScrollArea, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QDesktopServices


class NumericTableWidgetItem(QTableWidgetItem):
    """Custom QTableWidgetItem that sorts numerically"""
    def __init__(self, text, numeric_value):
        super().__init__(text)
        self.numeric_value = numeric_value
    
    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.numeric_value < other.numeric_value
        return super().__lt__(other)


class SortableTableWidgetItem(QTableWidgetItem):
    """Custom QTableWidgetItem that sorts by a custom sort key"""
    def __init__(self, text, sort_key):
        super().__init__(text)
        self.sort_key = sort_key
    
    def __lt__(self, other):
        if isinstance(other, SortableTableWidgetItem):
            return self.sort_key < other.sort_key
        return super().__lt__(other)


class DirectorySelectionDialog(QDialog):
    """Dialog for selecting which directory level to delete"""
    
    def __init__(self, file_paths, scanned_directory, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.scanned_directory = os.path.normpath(scanned_directory)
        self.selected_directory = None
        self.directory_options = []
        
        self.setWindowTitle("Select Directory to Delete")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
        self.analyze_directories()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel("Choose which directory level to delete:")
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Scroll area for directory options
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        
        # Button group for radio buttons
        self.button_group = QButtonGroup()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Info label
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("QLabel { color: #666; font-size: 9pt; }")
        layout.addWidget(self.info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.delete_button = QPushButton("Delete Selected Directory")
        self.delete_button.clicked.connect(self.accept)
        self.delete_button.setEnabled(False)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
    
    def analyze_directories(self):
        """Analyze file paths and create directory options"""
        directory_levels = set()
        
        for file_path in self.file_paths:
            normalized_path = os.path.normpath(file_path)
            relative_path = os.path.relpath(normalized_path, self.scanned_directory)
            
            if not relative_path.startswith('..'):
                path_parts = relative_path.split(os.sep)
                
                # Add all directory levels from scanned directory to file
                for i in range(len(path_parts) - 1):  # Exclude the file itself
                    if i == 0:
                        # First level subdirectory
                        dir_path = os.path.join(self.scanned_directory, path_parts[0])
                        relative_display = path_parts[0]
                    else:
                        # Deeper subdirectories
                        dir_path = os.path.join(self.scanned_directory, *path_parts[:i+1])
                        relative_display = os.sep.join(path_parts[:i+1])
                    
                    if os.path.exists(dir_path):
                        directory_levels.add((dir_path, relative_display, i))
        
        # Sort by depth (shallowest first)
        sorted_directories = sorted(directory_levels, key=lambda x: x[2])
        
        if not sorted_directories:
            self.info_label.setText("No valid directories found for deletion.")
            return
        
        # Create radio buttons for each directory option
        for i, (dir_path, relative_display, depth) in enumerate(sorted_directories):
            self.directory_options.append(dir_path)
            
            # Create radio button
            radio = QRadioButton()
            self.button_group.addButton(radio, i)
            
            # Create description
            dir_name = os.path.basename(dir_path)
            file_count = self.count_files_in_directory(dir_path)
            
            description = f"{relative_display}/"
            details = f"Directory: {dir_name} | Files: {file_count} | Path: {dir_path}"
            
            # Layout for this option
            option_layout = QVBoxLayout()
            
            # Main option layout
            main_layout = QHBoxLayout()
            main_layout.addWidget(radio)
            
            option_label = QLabel(description)
            option_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            main_layout.addWidget(option_label)
            main_layout.addStretch()
            
            option_layout.addLayout(main_layout)
            
            # Details label
            details_label = QLabel(details)
            details_label.setStyleSheet("QLabel { color: #666; font-size: 8pt; margin-left: 20px; }")
            option_layout.addWidget(details_label)
            
            # Add separator
            if i < len(sorted_directories) - 1:
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                option_layout.addWidget(separator)
            
            self.scroll_layout.addLayout(option_layout)
        
        # Connect button group signal
        self.button_group.buttonClicked.connect(self.on_selection_changed)
        
        # Update info label
        self.info_label.setText(f"Found {len(sorted_directories)} directory levels available for deletion. Select one to proceed.")
    
    def count_files_in_directory(self, directory):
        """Count files in a directory (approximate)"""
        try:
            count = 0
            for root, dirs, files in os.walk(directory):
                count += len(files)
                if count > 1000:  # Limit counting for performance
                    return "1000+"
            return str(count)
        except (OSError, PermissionError):
            return "Unknown"
    
    def on_selection_changed(self, button):
        """Handle radio button selection change"""
        button_id = self.button_group.id(button)
        if 0 <= button_id < len(self.directory_options):
            self.selected_directory = self.directory_options[button_id]
            self.delete_button.setEnabled(True)
            
            # Update info label with selection details
            dir_name = os.path.basename(self.selected_directory)
            relative_path = os.path.relpath(self.selected_directory, self.scanned_directory)
            self.info_label.setText(f"Selected: {relative_path}/ ({dir_name}) - This will delete the entire directory and all its contents.")
    
    def get_selected_directory(self):
        """Get the selected directory path"""
        return self.selected_directory


class ScanWorker(QThread):
    """Worker thread for directory scanning"""
    progress = pyqtSignal(str)
    progress_percentage = pyqtSignal(int)  # New signal for percentage updates
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, directory_path: str, limit: int = 1000, file_extensions: List[str] = None):
        super().__init__()
        self.directory_path = directory_path
        self.limit = limit if limit is not None else float('inf')
        self.file_extensions = file_extensions  # None means all files
        self.cancelled = False
    
    def run(self):
        try:
            self.progress.emit("Starting directory scan...")
            
            # Try to use Rust backend first, fallback to Python implementation
            try:
                result = self.scan_with_rust()
            except Exception as e:
                self.progress.emit(f"Rust backend unavailable: {e}")
                self.progress.emit("Falling back to Python implementation...")
                result = self.scan_with_python()
            
            if not self.cancelled:
                self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    def scan_with_rust(self) -> List[Dict[str, Any]]:
        """Scan using Rust backend"""
        # Try to import the Rust module
        try:
            import rust_backend
            self.progress.emit("Using Rust backend for high-performance scanning...")
            self.progress_percentage.emit(10)
            
            # Use a very large number for unlimited instead of infinity
            rust_limit = 999999999 if self.limit == float('inf') else int(self.limit)
            
            self.progress.emit("Scanning directory with Rust backend...")
            self.progress_percentage.emit(50)
            
            json_result = rust_backend.scan_dir(self.directory_path, rust_limit)
            
            self.progress_percentage.emit(90)
            results = json.loads(json_result)
            
            self.progress.emit(f"Rust scan completed. Found {len(results)} files.")
            self.progress_percentage.emit(100)
            
            return results
        except ImportError:
            # Try to call the Rust executable
            rust_exe = Path("../rust_backend/target/release/scanner.exe")
            if not rust_exe.exists():
                rust_exe = Path("../rust_backend/target/debug/scanner.exe")
            
            if rust_exe.exists():
                self.progress.emit("Using Rust executable for scanning...")
                self.progress_percentage.emit(10)
                
                # Use a very large number for unlimited instead of infinity
                rust_limit = 999999999 if self.limit == float('inf') else int(self.limit)
                
                self.progress_percentage.emit(30)
                result = subprocess.run(
                    [str(rust_exe), self.directory_path, str(rust_limit)],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                self.progress_percentage.emit(80)
                
                if result.returncode == 0:
                    # Parse JSON from stdout
                    lines = result.stdout.strip().split('\n')
                    json_line = None
                    for line in lines:
                        if line.startswith('[') or line.startswith('{'):
                            json_line = line
                            break
                    
                    if json_line:
                        results = json.loads(json_line)
                        
                        # Apply file extension filtering if needed
                        if self.file_extensions is not None:
                            filtered_results = []
                            for file_info in results:
                                file_path = file_info.get('path', '')
                                file_ext = Path(file_path).suffix.lower()
                                if file_ext in self.file_extensions:
                                    filtered_results.append(file_info)
                            results = filtered_results
                        
                        self.progress.emit(f"Rust executable scan completed. Found {len(results)} files.")
                        self.progress_percentage.emit(100)
                        return results
                    else:
                        raise Exception("No JSON output from Rust executable")
                else:
                    raise Exception(f"Rust executable failed: {result.stderr}")
            else:
                raise Exception("Rust executable not found")
    
    def scan_with_python(self) -> List[Dict[str, Any]]:
        """Fallback Python implementation"""
        files = []
        total_files = 0
        processed_files = 0
        
        # First pass: count files
        self.progress.emit("Counting files...")
        self.progress_percentage.emit(0)
        for root, dirs, filenames in os.walk(self.directory_path):
            if self.cancelled:
                return []
            total_files += len(filenames)
        
        if total_files == 0:
            self.progress.emit("No files found in directory.")
            self.progress_percentage.emit(100)
            return []
        
        self.progress.emit(f"Found {total_files} files. Analyzing...")
        self.progress_percentage.emit(5)  # 5% for counting phase
        
        # Second pass: collect file info
        for root, dirs, filenames in os.walk(self.directory_path):
            if self.cancelled:
                return []
            
            for filename in filenames:
                if self.cancelled:
                    return []
                
                filepath = os.path.join(root, filename)
                try:
                    stat = os.stat(filepath)
                    size = stat.st_size
                    modified = datetime.fromtimestamp(stat.st_mtime).isoformat() + 'Z'
                    extension = Path(filename).suffix.lstrip('.') or 'no extension'
                    
                    # Apply file extension filtering
                    if self.file_extensions is not None:  # If specific filters are selected
                        file_ext = Path(filename).suffix.lower()
                        if file_ext not in self.file_extensions:
                            processed_files += 1
                            continue  # Skip files that don't match the filter
                    
                    files.append({
                        'path': filepath,
                        'size': size,
                        'modified': modified,
                        'extension': extension
                    })
                    
                    processed_files += 1
                    
                    # Update progress every 50 files or at significant milestones
                    if processed_files % 50 == 0 or processed_files == total_files:
                        # Progress from 5% to 90% for file processing
                        progress_pct = 5 + int((processed_files / total_files) * 85)
                        self.progress_percentage.emit(progress_pct)
                        self.progress.emit(f"Processed {processed_files}/{total_files} files ({progress_pct}%)")
                
                except (OSError, IOError):
                    processed_files += 1  # Count skipped files too
                    continue  # Skip files we can't access
        
        # Sorting phase
        self.progress.emit("Sorting files by size...")
        self.progress_percentage.emit(95)
        
        # Sort by size (largest first) and limit
        files.sort(key=lambda x: x['size'], reverse=True)
        
        self.progress_percentage.emit(100)
        
        if self.limit == float('inf'):
            return files
        return files[:self.limit]
    
    def cancel(self):
        self.cancelled = True


class DirectoryScannerApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.scan_worker = None
        self.current_results = []
        self.init_ui()
        self.apply_modern_style()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Directory Scanner - Find Largest Files")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header section
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("Directory Scanner")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Find and analyze the largest files on your system")
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        main_layout.addWidget(header_frame)
        
        # Controls section
        controls_group = QGroupBox("Scan Configuration")
        controls_layout = QGridLayout(controls_group)
        
        # Directory selection
        controls_layout.addWidget(QLabel("Directory:"), 0, 0)
        self.directory_input = QLineEdit()
        self.directory_input.setPlaceholderText("Select a directory to scan...")
        controls_layout.addWidget(self.directory_input, 0, 1)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_directory)
        controls_layout.addWidget(self.browse_button, 0, 2)
        
        # Limit selection
        controls_layout.addWidget(QLabel("Max Results:"), 1, 0)
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["100", "500", "1000", "5000", "10000", "Unlimited"])
        self.limit_combo.setCurrentText("1000")
        controls_layout.addWidget(self.limit_combo, 1, 1)
        
        # File type filters
        controls_layout.addWidget(QLabel("File Types:"), 2, 0)
        
        # Create horizontal layout for checkboxes
        filter_layout = QHBoxLayout()
        
        # All Files checkbox (pre-selected)
        self.all_files_checkbox = QCheckBox("All Files")
        self.all_files_checkbox.setChecked(True)
        self.all_files_checkbox.stateChanged.connect(self.on_all_files_changed)
        filter_layout.addWidget(self.all_files_checkbox)
        
        # Specific file type checkboxes
        self.images_checkbox = QCheckBox("Images")
        self.images_checkbox.stateChanged.connect(self.on_specific_filter_changed)
        filter_layout.addWidget(self.images_checkbox)
        
        self.videos_checkbox = QCheckBox("Videos")
        self.videos_checkbox.stateChanged.connect(self.on_specific_filter_changed)
        filter_layout.addWidget(self.videos_checkbox)
        
        self.archives_checkbox = QCheckBox("Archives")
        self.archives_checkbox.stateChanged.connect(self.on_specific_filter_changed)
        filter_layout.addWidget(self.archives_checkbox)
        
        self.executables_checkbox = QCheckBox("Executables")
        self.executables_checkbox.stateChanged.connect(self.on_specific_filter_changed)
        filter_layout.addWidget(self.executables_checkbox)
        
        filter_layout.addStretch()  # Add stretch to push checkboxes to the left
        
        # Create a widget to hold the filter layout
        filter_widget = QWidget()
        filter_widget.setLayout(filter_layout)
        controls_layout.addWidget(filter_widget, 2, 1, 1, 2)  # Span 2 columns
        
        # Scan button
        self.scan_button = QPushButton("Start Scan")
        self.scan_button.clicked.connect(self.start_scan)
        self.scan_button.setMinimumHeight(40)
        controls_layout.addWidget(self.scan_button, 3, 2)
        
        main_layout.addWidget(controls_group)
        
        # Progress section
        self.progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to scan")
        progress_layout.addWidget(self.status_label)
        
        # Initially hide the progress section
        self.progress_group.setVisible(False)
        
        main_layout.addWidget(self.progress_group)
        
        # Results section
        results_group = QGroupBox("Scan Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["File Path", "Size", "Modified", "Extension"])
        
        # Configure table
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable sorting and disable editing
        self.results_table.setSortingEnabled(True)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        results_layout.addWidget(self.results_table)
        main_layout.addWidget(results_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.delete_button = QPushButton("Delete Selected Files")
        self.delete_button.clicked.connect(self.delete_selected_files)
        self.delete_button.setEnabled(False)
        action_layout.addWidget(self.delete_button)
        
        self.delete_directory_button = QPushButton("Delete Whole Directory")
        self.delete_directory_button.clicked.connect(self.delete_selected_directories)
        self.delete_directory_button.setEnabled(False)
        action_layout.addWidget(self.delete_directory_button)
        
        self.open_directory_button = QPushButton("Open File Directory")
        self.open_directory_button.clicked.connect(self.open_selected_directories)
        self.open_directory_button.setEnabled(False)
        action_layout.addWidget(self.open_directory_button)
        
        self.export_button = QPushButton("Export Results")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        action_layout.addWidget(self.export_button)
        
        main_layout.addLayout(action_layout)
        
        # Footer section with creator link
        footer_layout = QHBoxLayout()
        
        # Create clickable label for creator link
        self.creator_label = QLabel('<a href="https://socratisp.com" style="color: #4fc3f7; text-decoration: none;">This app is created by https://socratisp.com</a>')
        self.creator_label.setOpenExternalLinks(True)
        self.creator_label.setFont(QFont("Arial", 9))
        self.creator_label.setStyleSheet("QLabel { color: #888888; } QLabel a { color: #4fc3f7; }")
        
        footer_layout.addWidget(self.creator_label)
        footer_layout.addStretch()  # Push the label to the left
        
        main_layout.addLayout(footer_layout)
    
    def apply_modern_style(self):
        """Apply modern dark theme styling to the application"""
        self.setStyleSheet("""
            /* Main Window */
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            /* Group Boxes */
            QGroupBox {
                font-weight: bold;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #2d2d2d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #4fc3f7;
                font-size: 12px;
                font-weight: bold;
            }
            
            /* Labels */
            QLabel {
                color: #ffffff;
                font-size: 11px;
            }
            
            /* Input Fields */
            QLineEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
                font-size: 11px;
                selection-background-color: #4fc3f7;
            }
            QLineEdit:focus {
                border-color: #4fc3f7;
                background-color: #404040;
            }
            
            /* Combo Boxes */
            QComboBox {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
                font-size: 11px;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: #4fc3f7;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                selection-background-color: #4fc3f7;
                color: #ffffff;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #4fc3f7;
                color: #000000;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #29b6f6;
            }
            QPushButton:pressed {
                background-color: #0288d1;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 6px;
                background-color: #3c3c3c;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4fc3f7;
                border-radius: 4px;
            }
            
            /* Table Widget */
            QTableWidget {
                gridline-color: #555555;
                background-color: #2d2d2d;
                alternate-background-color: #353535;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 6px;
                selection-background-color: #4fc3f7;
                selection-color: #000000;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #404040;
            }
            QTableWidget::item:selected {
                background-color: #4fc3f7;
                color: #000000;
            }
            QTableWidget::item:hover {
                background-color: #404040;
            }
            
            /* Table Headers */
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 10px;
                border: 1px solid #555555;
                font-weight: bold;
                font-size: 11px;
            }
            QHeaderView::section:hover {
                background-color: #4fc3f7;
                color: #000000;
            }
            
            /* Text Edit (Preview) */
            QTextEdit {
                background-color: #2d2d2d;
                border: 2px solid #555555;
                border-radius: 6px;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                selection-background-color: #4fc3f7;
                selection-color: #000000;
            }
            QTextEdit:focus {
                border-color: #4fc3f7;
            }
            
            /* Splitter */
            QSplitter::handle {
                background-color: #555555;
                width: 3px;
                height: 3px;
            }
            QSplitter::handle:hover {
                background-color: #4fc3f7;
            }
            
            /* Scroll Bars */
            QScrollBar:vertical {
                background-color: #3c3c3c;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4fc3f7;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #3c3c3c;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #555555;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #4fc3f7;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* Message Boxes */
            QMessageBox {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QMessageBox QPushButton {
                min-width: 80px;
                padding: 8px 16px;
            }
        """)
    
    def browse_directory(self):
        """Open directory selection dialog"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory to Scan", 
            self.directory_input.text() or os.path.expanduser("~")
        )
        if directory:
            self.directory_input.setText(directory)
    
    def on_all_files_changed(self, state):
        """Handle All Files checkbox state change"""
        if state == Qt.CheckState.Checked.value:
            # Disable and uncheck all specific file type filters
            self.images_checkbox.setChecked(False)
            self.images_checkbox.setEnabled(False)
            self.videos_checkbox.setChecked(False)
            self.videos_checkbox.setEnabled(False)
            self.archives_checkbox.setChecked(False)
            self.archives_checkbox.setEnabled(False)
            self.executables_checkbox.setChecked(False)
            self.executables_checkbox.setEnabled(False)
        else:
            # Enable all specific file type filters
            self.images_checkbox.setEnabled(True)
            self.videos_checkbox.setEnabled(True)
            self.archives_checkbox.setEnabled(True)
            self.executables_checkbox.setEnabled(True)
    
    def on_specific_filter_changed(self, state):
        """Handle specific file type checkbox state change"""
        if state == Qt.CheckState.Checked.value:
            # If any specific filter is checked, uncheck All Files
            self.all_files_checkbox.setChecked(False)
    
    def get_selected_file_extensions(self):
        """Get list of file extensions based on selected filters"""
        if self.all_files_checkbox.isChecked():
            return None  # Return None to indicate all files
        
        extensions = set()
        
        if self.images_checkbox.isChecked():
            extensions.update([
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
                '.webp', '.svg', '.ico', '.raw', '.psd', '.ai', '.eps'
            ])
        
        if self.videos_checkbox.isChecked():
            extensions.update([
                '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm',
                '.m4v', '.mpg', '.mpeg', '.3gp', '.ogv'
            ])
        
        if self.archives_checkbox.isChecked():
            extensions.update([
                '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
                '.iso', '.dmg', '.cab', '.deb', '.rpm', '.pkg'
            ])
        
        if self.executables_checkbox.isChecked():
            extensions.update([
                '.exe', '.dll', '.msi', '.bat', '.cmd', '.sh', '.bin',
                '.app', '.deb', '.rpm', '.pkg', '.dmg', '.run'
            ])
        
        return list(extensions) if extensions else None
    
    def start_scan(self):
        """Start the directory scanning process"""
        directory = self.directory_input.text().strip()
        if not directory:
            QMessageBox.warning(self, "Warning", "Please select a directory to scan.")
            return
        
        if not os.path.exists(directory):
            QMessageBox.warning(self, "Warning", "Selected directory does not exist.")
            return
        
        limit_text = self.limit_combo.currentText()
        limit = None if limit_text == "Unlimited" else int(limit_text)
        
        # Disable controls
        self.scan_button.setText("Cancel Scan")
        self.scan_button.clicked.disconnect()
        self.scan_button.clicked.connect(self.cancel_scan)
        self.browse_button.setEnabled(False)
        self.limit_combo.setEnabled(False)
        
        # Show progress section and progress bar
        self.progress_group.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)  # Determinate progress (0-100%)
        self.progress_bar.setValue(0)
        
        # Clear previous results
        self.results_table.setRowCount(0)
        self.current_results = []
        self.export_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.delete_directory_button.setEnabled(False)
        self.open_directory_button.setEnabled(False)
        
        # Get selected file extensions
        file_extensions = self.get_selected_file_extensions()
        
        # Start worker thread
        self.scan_worker = ScanWorker(directory, limit, file_extensions)
        self.scan_worker.progress.connect(self.update_progress)
        self.scan_worker.progress_percentage.connect(self.update_progress_percentage)
        self.scan_worker.finished.connect(self.scan_finished)
        self.scan_worker.error.connect(self.scan_error)
        self.scan_worker.start()
    
    def cancel_scan(self):
        """Cancel the current scan"""
        if self.scan_worker:
            self.scan_worker.cancel()
            self.scan_worker.wait()
        self.reset_ui_after_scan()
        self.status_label.setText("Scan cancelled")
        
        # Hide progress section after cancellation
        self.progress_group.setVisible(False)
    
    def update_progress(self, message: str):
        """Update progress status"""
        self.status_label.setText(message)
    
    def update_progress_percentage(self, percentage: int):
        """Update progress bar percentage"""
        if percentage >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percentage)
        else:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
    
    def scan_finished(self, results: List[Dict[str, Any]]):
        """Handle scan completion"""
        self.current_results = results
        self.populate_results_table(results)
        self.reset_ui_after_scan()
        limit_text = "unlimited" if self.limit_combo.currentText() == "Unlimited" else self.limit_combo.currentText()
        self.status_label.setText(f"Scan completed. Found {len(results)} files (limit: {limit_text}).")
        self.export_button.setEnabled(len(results) > 0)
        self.delete_button.setEnabled(len(results) > 0)
        self.delete_directory_button.setEnabled(len(results) > 0)
        self.open_directory_button.setEnabled(len(results) > 0)
        
        # Hide progress section after scan completion
        self.progress_group.setVisible(False)
    
    def scan_error(self, error_message: str):
        """Handle scan error"""
        self.reset_ui_after_scan()
        self.status_label.setText(f"Scan failed: {error_message}")
        QMessageBox.critical(self, "Scan Error", f"An error occurred during scanning:\n{error_message}")
        
        # Hide progress section after error
        self.progress_group.setVisible(False)
    
    def reset_ui_after_scan(self):
        """Reset UI controls after scan completion"""
        self.scan_button.setText("Start Scan")
        self.scan_button.clicked.disconnect()
        self.scan_button.clicked.connect(self.start_scan)
        self.browse_button.setEnabled(True)
        self.limit_combo.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def populate_results_table(self, results: List[Dict[str, Any]]):
        """Populate the results table with scan data"""
        self.results_table.setRowCount(len(results))
        
        for row, file_info in enumerate(results):
            # File path - display full path but sort by filename
            filename = os.path.basename(file_info['path'])
            path_item = SortableTableWidgetItem(file_info['path'], filename.lower())
            path_item.setToolTip(file_info['path'])
            self.results_table.setItem(row, 0, path_item)
            
            # File size (formatted) - use custom numeric item for proper sorting
            size_bytes = file_info['size']
            size_formatted = self.format_file_size(size_bytes)
            size_item = NumericTableWidgetItem(size_formatted, size_bytes)
            self.results_table.setItem(row, 1, size_item)
            
            # Modified date - use timestamp for proper chronological sorting
            modified_str = file_info['modified'][:19]  # Remove timezone
            try:
                from datetime import datetime
                timestamp = datetime.fromisoformat(modified_str.replace('T', ' '))
                modified_item = NumericTableWidgetItem(modified_str, timestamp.timestamp())
            except:
                modified_item = SortableTableWidgetItem(modified_str, modified_str)
            self.results_table.setItem(row, 2, modified_item)
            
            # Extension - sort alphabetically (case-insensitive)
            extension_item = SortableTableWidgetItem(file_info['extension'], file_info['extension'].lower())
            self.results_table.setItem(row, 3, extension_item)
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    

    

    
    def delete_selected_files(self):
        """Delete selected files and send them to recycle bin"""
        if not self.current_results:
            return
        
        # Check if send2trash is available
        if send2trash is None:
            QMessageBox.critical(
                self, "Missing Dependency", 
                "The 'send2trash' library is required for safe file deletion.\n\n"
                "Please install it using: pip install send2trash"
            )
            return
        
        # Get selected rows
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.information(
                self, "No Selection", 
                "Please select one or more files to delete."
            )
            return
        
        # Get selected file paths from table items (not from current_results index)
        selected_files = []
        for row in selected_rows:
            # Get the file path directly from the table item (column 0)
            path_item = self.results_table.item(row, 0)
            if path_item:
                file_path = path_item.text()  # This contains the full file path
                # Normalize the file path to handle mixed slashes
                normalized_path = os.path.normpath(file_path)
                selected_files.append(normalized_path)
        
        if not selected_files:
            return
        
        # Confirmation dialog
        file_count = len(selected_files)
        if file_count == 1:
            message = f"Are you sure you want to move this file to the recycle bin?\n\n{os.path.basename(selected_files[0])}"
        else:
            message = f"Are you sure you want to move {file_count} selected files to the recycle bin?"
        
        reply = QMessageBox.question(
            self, "Confirm Deletion", message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Delete files
        deleted_count = 0
        failed_files = []
        
        for file_path in selected_files:
            try:
                if os.path.exists(file_path):
                    send2trash(file_path)
                    deleted_count += 1
                else:
                    failed_files.append(f"{os.path.basename(file_path)} (file not found)")
            except Exception as e:
                failed_files.append(f"{os.path.basename(file_path)} ({str(e)})")
        
        # Show results
        if deleted_count > 0:
            if failed_files:
                message = f"Successfully moved {deleted_count} file(s) to recycle bin.\n\nFailed to delete:\n" + "\n".join(failed_files)
                QMessageBox.warning(self, "Partial Success", message)
            else:
                QMessageBox.information(self, "Success", f"Successfully moved {deleted_count} file(s) to recycle bin.")
            
            # Remove deleted files from results and refresh table
            remaining_results = []
            failed_file_paths = [f.split(' (')[0] for f in failed_files]
            
            for result in self.current_results:
                file_path = os.path.normpath(result['path'])  # Normalize for comparison
                # Keep files that were either:
                # 1. Not selected for deletion, OR
                # 2. Selected but failed to delete
                if file_path not in selected_files or file_path in failed_file_paths:
                    remaining_results.append(result)
            
            self.current_results = remaining_results
            self.populate_results_table(self.current_results)
            
            # Update button states
            has_results = len(self.current_results) > 0
            self.export_button.setEnabled(has_results)
            self.delete_button.setEnabled(has_results)
            self.delete_directory_button.setEnabled(has_results)
            self.open_directory_button.setEnabled(has_results)
            
        else:
            message = "Failed to delete any files:\n" + "\n".join(failed_files)
            QMessageBox.critical(self, "Deletion Failed", message)
    
    def delete_selected_directories(self):
        """Show directory selection dialog and delete the chosen directory"""
        if not self.current_results:
            return
        
        # Check if send2trash is available
        if send2trash is None:
            QMessageBox.critical(
                self, "Missing Dependency", 
                "The 'send2trash' library is required for safe directory deletion.\n\n"
                "Please install it using: pip install send2trash"
            )
            return
        
        # Get selected rows
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.information(
                self, "No Selection", 
                "Please select one or more files to choose directories for deletion."
            )
            return
        
        # Get unique file paths from selected items
        file_paths = set()
        for row in selected_rows:
            path_item = self.results_table.item(row, 0)
            if path_item:
                file_path = path_item.text()  # Full path column
                file_paths.add(file_path)
        
        if not file_paths:
            return
        
        # Get the scanned directory path
        scanned_directory = os.path.normpath(self.directory_input.text().strip())
        
        # Show directory selection dialog
        dialog = DirectorySelectionDialog(file_paths, scanned_directory, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_directory = dialog.get_selected_directory()
            
            if not selected_directory:
                QMessageBox.warning(self, "Warning", "No directory was selected.")
                return
            
            # Confirm deletion
            dir_name = os.path.basename(selected_directory)
            relative_path = os.path.relpath(selected_directory, scanned_directory)
            
            # Count files in directory
            try:
                file_count = 0
                for root, dirs, files in os.walk(selected_directory):
                    file_count += len(files)
                    if file_count > 1000:  # Limit for performance
                        file_count_text = "1000+"
                        break
                else:
                    file_count_text = str(file_count)
            except (OSError, PermissionError):
                file_count_text = "Unknown"
            
            message = f"""Are you sure you want to delete this directory?

Directory: {relative_path}/
Full path: {selected_directory}
Estimated files: {file_count_text}

This action will move the directory to the Recycle Bin and cannot be easily undone."""
            
            reply = QMessageBox.question(
                self, "Confirm Directory Deletion", message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Delete the directory
            try:
                send2trash(selected_directory)
                self.status_label.setText(f"Deleted directory: {dir_name}")
                
                # Remove files from deleted directory from results and refresh table
                remaining_results = []
                
                for result in self.current_results:
                    file_path = os.path.normpath(result['path'])
                    # Keep files that are not in the deleted directory or its subdirectories
                    if not (file_path == selected_directory or file_path.startswith(selected_directory + os.sep)):
                        remaining_results.append(result)
                
                self.current_results = remaining_results
                self.populate_results_table(self.current_results)
                
                # Update button states
                has_results = len(self.current_results) > 0
                self.export_button.setEnabled(has_results)
                self.delete_button.setEnabled(has_results)
                self.delete_directory_button.setEnabled(has_results)
                self.open_directory_button.setEnabled(has_results)
                
                QMessageBox.information(self, "Deletion Complete", 
                                       f"Successfully deleted directory: {relative_path}/")
                
                self.status_label.setText(f"Directory deletion complete: {dir_name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Deletion Failed", 
                                   f"Failed to delete directory: {dir_name}\n\nError: {str(e)}")
                self.status_label.setText(f"Failed to delete: {dir_name}")
    
    def open_selected_directories(self):
        """Open file explorer with selected files highlighted"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select files to open their directories.")
            return
        
        # Get unique directories to avoid opening the same directory multiple times
        directories_opened = set()
        
        for row in selected_rows:
            # Get the file path directly from the table item (column 0)
            path_item = self.results_table.item(row, 0)
            if path_item:
                file_path = path_item.text()  # This contains the full file path
                normalized_path = os.path.normpath(file_path)
                
                # Check if file exists
                if not os.path.exists(normalized_path):
                    continue
                
                directory = os.path.dirname(normalized_path)
                
                # Skip if we already opened this directory
                if directory in directories_opened:
                    continue
                
                directories_opened.add(directory)
                
                try:
                    # Platform-specific file explorer opening
                    if sys.platform == "win32":
                        # Windows: Use explorer with /select to highlight the file
                        subprocess.run(["explorer", "/select,", normalized_path], check=False)
                    elif sys.platform == "darwin":
                        # macOS: Use Finder to reveal the file
                        subprocess.run(["open", "-R", normalized_path], check=False)
                    else:
                        # Linux: Try different file managers
                        # First try to highlight the file if possible
                        file_managers = [
                            ["nautilus", "--select", normalized_path],  # GNOME
                            ["dolphin", "--select", normalized_path],   # KDE
                            ["thunar", normalized_path],                # XFCE
                            ["pcmanfm", directory],                     # LXDE
                            ["nemo", directory],                        # Cinnamon
                            ["xdg-open", directory]                     # Fallback
                        ]
                        
                        opened = False
                        for cmd in file_managers:
                            try:
                                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                opened = True
                                break
                            except (subprocess.CalledProcessError, FileNotFoundError):
                                continue
                        
                        if not opened:
                            # Final fallback: try to open directory with default application
                            try:
                                subprocess.run(["xdg-open", directory], check=True)
                            except (subprocess.CalledProcessError, FileNotFoundError):
                                QMessageBox.warning(self, "Error", f"Could not open directory: {directory}")
                                continue
                
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to open directory for {os.path.basename(normalized_path)}: {e}")
        
        if directories_opened:
            count = len(directories_opened)
            QMessageBox.information(self, "Directories Opened", f"Opened {count} director{'y' if count == 1 else 'ies'} in file explorer.")
    
    def export_results(self):
        """Export scan results to JSON file"""
        if not self.current_results:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "scan_results.json", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_results, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Export Successful", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export results: {e}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Directory Scanner")
    app.setApplicationVersion("1.0")
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = DirectoryScannerApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()