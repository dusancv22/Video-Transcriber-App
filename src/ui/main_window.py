"""
Flat, modern main window implementation for Video Transcriber App
This replaces the card-based design with a clean, efficient layout
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QListWidget, QListWidgetItem, QMessageBox, QComboBox,
    QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, QThread
from PyQt6.QtGui import QIcon, QFont
from pathlib import Path
from src.transcription.transcription_pipeline import TranscriptionPipeline
from src.input_handling.queue_manager import QueueManager, FileStatus
from src.ui.worker import TranscriptionWorker
from src.ui.styles.modern_theme import ModernTheme
from src.config.settings import Settings
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Transcriber")
        self.setMinimumSize(800, 500)  # More compact size
        
        # Set application icon
        icon_path = Path(__file__).parent.parent.parent / "assets" / "icons" / "app_icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Apply modern theme
        self.setStyleSheet(ModernTheme.get_stylesheet())
        
        # Initialize components
        self.settings = Settings()
        self.pipeline = None  # Lazy initialization
        self.queue_manager = QueueManager()
        self.output_directory = None
        self.worker = None
        self.custom_model_path = None
        self.selected_language_code = None  # Will be set based on language dropdown
        
        # Time tracking
        self.current_file_start_time = None
        self.processed_files_times = []
        self.is_paused = False
        
        # Initialize UI
        self.init_ui()
        logger.info("MainWindow initialized")
        
    def init_ui(self):
        """Initialize flat, modern UI layout"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout - minimal spacing
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        print("Initializing Video Transcriber interface...")
        
        # Toolbar - flat button layout
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        
        # Clean buttons without icons
        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.clicked.connect(self.add_files)
        toolbar.addWidget(self.add_files_btn)
        
        self.add_dir_btn = QPushButton("Add Directory") 
        self.add_dir_btn.clicked.connect(self.add_directory)
        toolbar.addWidget(self.add_dir_btn)
        
        self.output_dir_btn = QPushButton("Select Output")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        self.output_dir_btn.setProperty("class", "secondary")
        toolbar.addWidget(self.output_dir_btn)
        
        self.clear_btn = QPushButton("Clear Queue")
        self.clear_btn.clicked.connect(self.clear_queue) 
        self.clear_btn.setProperty("class", "danger")
        toolbar.addWidget(self.clear_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Status line
        self.output_dir_label = QLabel("Output Directory: Not Selected")
        self.output_dir_label.setStyleSheet(f"""
            color: {ModernTheme.COLORS['text_secondary']};
            font-size: 12px;
            padding: 4px 8px;
            border: 1px solid {ModernTheme.COLORS['outline']};
            border-radius: {ModernTheme.RADIUS['sm']};
            background-color: {ModernTheme.COLORS['surface_variant']};
        """)
        layout.addWidget(self.output_dir_label)
        
        # Model selection section
        model_section = QHBoxLayout()
        model_section.setSpacing(8)
        
        # Model status label
        self.model_status_label = QLabel("Whisper Model: Default")
        self.model_status_label.setStyleSheet(f"""
            color: {ModernTheme.COLORS['text_secondary']};
            font-size: 12px;
            padding: 4px 8px;
            border: 1px solid {ModernTheme.COLORS['outline']};
            border-radius: {ModernTheme.RADIUS['sm']};
            background-color: {ModernTheme.COLORS['surface_variant']};
            min-width: 200px;
        """)
        model_section.addWidget(self.model_status_label)
        
        # Model size dropdown
        self.model_size_combo = QComboBox()
        self.model_size_combo.addItems(['tiny', 'base', 'small', 'medium', 'large'])
        self.model_size_combo.setCurrentText(self.settings.get('whisper_model_size', 'large'))
        self.model_size_combo.currentTextChanged.connect(self.on_model_size_changed)
        self.model_size_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ModernTheme.COLORS['surface']};
                border: 1px solid {ModernTheme.COLORS['outline']};
                border-radius: {ModernTheme.RADIUS['sm']};
                padding: 4px 8px;
                font-size: 12px;
                min-width: 80px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {ModernTheme.COLORS['text_secondary']};
            }}
        """)
        model_section.addWidget(self.model_size_combo)
        
        # Language selection dropdown
        self.language_label = QLabel("Language:")
        self.language_label.setStyleSheet(f"""
            color: {ModernTheme.COLORS['text_secondary']};
            font-size: 12px;
            padding: 4px 8px;
        """)
        model_section.addWidget(self.language_label)
        
        self.language_combo = QComboBox()
        # Add common languages with their codes
        # Format: "Display Name (code)"
        languages = [
            "Auto-detect",
            "English (en)",
            "Spanish (es)",
            "French (fr)",
            "German (de)",
            "Italian (it)",
            "Portuguese (pt)",
            "Dutch (nl)",
            "Polish (pl)",
            "Russian (ru)",
            "Chinese (zh)",
            "Japanese (ja)",
            "Korean (ko)",
            "Arabic (ar)",
            "Hindi (hi)",
            "Turkish (tr)",
            "Swedish (sv)",
            "Norwegian (no)",
            "Danish (da)",
            "Finnish (fi)",
            "Greek (el)",
            "Hebrew (he)",
            "Indonesian (id)",
            "Malay (ms)",
            "Thai (th)",
            "Vietnamese (vi)",
            "Czech (cs)",
            "Hungarian (hu)",
            "Romanian (ro)",
            "Ukrainian (uk)",
            "Croatian (hr)",
            "Bulgarian (bg)",
            "Serbian (sr)",
            "Slovak (sk)",
            "Slovenian (sl)",
            "Estonian (et)",
            "Latvian (lv)",
            "Lithuanian (lt)",
            "Persian (fa)",
            "Urdu (ur)",
            "Swahili (sw)",
            "Filipino (tl)",
            "Catalan (ca)",
            "Welsh (cy)",
            "Basque (eu)",
            "Galician (gl)"
        ]
        self.language_combo.addItems(languages)
        self.language_combo.setCurrentText(self.settings.get('transcription_language', 'Auto-detect'))
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        self.language_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ModernTheme.COLORS['surface']};
                border: 1px solid {ModernTheme.COLORS['outline']};
                border-radius: {ModernTheme.RADIUS['sm']};
                padding: 4px 8px;
                font-size: 12px;
                min-width: 120px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {ModernTheme.COLORS['text_secondary']};
            }}
        """)
        model_section.addWidget(self.language_combo)
        
        # Load model button
        self.load_model_btn = QPushButton("Load Model Folder")
        self.load_model_btn.clicked.connect(self.load_model_folder)
        self.load_model_btn.setProperty("class", "secondary")
        self.load_model_btn.setMaximumWidth(150)
        model_section.addWidget(self.load_model_btn)
        
        model_section.addStretch()
        layout.addLayout(model_section)
        
        # Subtitle export section
        subtitle_section = QHBoxLayout()
        subtitle_section.setSpacing(8)
        
        # Subtitle export checkbox
        self.subtitle_export_checkbox = QCheckBox("Export Subtitles")
        self.subtitle_export_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {ModernTheme.COLORS['text_primary']};
                font-size: 12px;
                padding: 4px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {ModernTheme.COLORS['outline']};
                border-radius: 3px;
                background-color: {ModernTheme.COLORS['surface']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ModernTheme.COLORS['success']};
                border-color: {ModernTheme.COLORS['success']};
            }}
        """)
        self.subtitle_export_checkbox.stateChanged.connect(self.on_subtitle_export_changed)
        subtitle_section.addWidget(self.subtitle_export_checkbox)
        
        # Faster-whisper checkbox for word-level timestamps
        self.use_faster_whisper_checkbox = QCheckBox("Use Faster-Whisper (Word Timestamps)")
        self.use_faster_whisper_checkbox.setToolTip(
            "Enable this for subtitle generation with accurate word-level timestamps.\n"
            "Works on Windows! Recommended when exporting subtitles."
        )
        self.use_faster_whisper_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {ModernTheme.COLORS['text_primary']};
                font-size: 12px;
                padding: 4px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {ModernTheme.COLORS['outline']};
                border-radius: 3px;
                background-color: {ModernTheme.COLORS['surface']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ModernTheme.COLORS['primary']};
                border-color: {ModernTheme.COLORS['primary']};
            }}
        """)
        # Auto-enable faster-whisper when subtitles are enabled
        self.use_faster_whisper_checkbox.setVisible(False)  # Initially hidden
        self.use_faster_whisper_checkbox.stateChanged.connect(self.on_faster_whisper_changed)
        subtitle_section.addWidget(self.use_faster_whisper_checkbox)
        
        # Subtitle format checkboxes (initially hidden)
        self.subtitle_formats_group = QWidget()
        subtitle_formats_layout = QHBoxLayout(self.subtitle_formats_group)
        subtitle_formats_layout.setContentsMargins(0, 0, 0, 0)
        subtitle_formats_layout.setSpacing(8)
        
        format_label = QLabel("Formats:")
        format_label.setStyleSheet(f"""
            color: {ModernTheme.COLORS['text_secondary']};
            font-size: 12px;
        """)
        subtitle_formats_layout.addWidget(format_label)
        
        # Format checkboxes
        self.srt_checkbox = QCheckBox("SRT")
        self.srt_checkbox.setChecked(True)
        self.vtt_checkbox = QCheckBox("VTT")
        self.ass_checkbox = QCheckBox("ASS")
        
        for checkbox in [self.srt_checkbox, self.vtt_checkbox, self.ass_checkbox]:
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {ModernTheme.COLORS['text_secondary']};
                    font-size: 11px;
                }}
                QCheckBox::indicator {{
                    width: 14px;
                    height: 14px;
                }}
            """)
            subtitle_formats_layout.addWidget(checkbox)
        
        # Max chars per line spinbox
        self.max_chars_label = QLabel("Max chars/line:")
        self.max_chars_label.setStyleSheet(f"""
            color: {ModernTheme.COLORS['text_secondary']};
            font-size: 12px;
            margin-left: 12px;
        """)
        subtitle_formats_layout.addWidget(self.max_chars_label)
        
        self.max_chars_spinbox = QSpinBox()
        self.max_chars_spinbox.setRange(20, 80)
        self.max_chars_spinbox.setValue(42)
        self.max_chars_spinbox.setStyleSheet(f"""
            QSpinBox {{
                background-color: {ModernTheme.COLORS['surface']};
                border: 1px solid {ModernTheme.COLORS['outline']};
                border-radius: {ModernTheme.RADIUS['sm']};
                padding: 2px 4px;
                font-size: 11px;
                max-width: 60px;
            }}
        """)
        subtitle_formats_layout.addWidget(self.max_chars_spinbox)
        
        self.subtitle_formats_group.hide()
        subtitle_section.addWidget(self.subtitle_formats_group)
        
        subtitle_section.addStretch()
        layout.addLayout(subtitle_section)
        
        # Update model status based on detected models
        self.update_model_status()
        
        # Progress section (initially hidden)
        self.progress_group = QWidget()
        progress_layout = QVBoxLayout(self.progress_group)
        progress_layout.setContentsMargins(0, 4, 0, 4)
        progress_layout.setSpacing(4)
        
        # Progress info
        progress_info_layout = QHBoxLayout()
        self.current_file_label = QLabel("")
        self.current_file_label.setStyleSheet("font-weight: 500;")
        progress_info_layout.addWidget(self.current_file_label)
        
        self.time_estimate_label = QLabel("")
        self.time_estimate_label.setStyleSheet(f"color: {ModernTheme.COLORS['text_tertiary']};")
        progress_info_layout.addWidget(self.time_estimate_label)
        progress_layout.addLayout(progress_info_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {ModernTheme.COLORS['text_tertiary']}; font-size: 11px;")
        progress_layout.addWidget(self.status_label)
        
        self.progress_group.hide()
        layout.addWidget(self.progress_group)
        
        # Queue section
        queue_header = QHBoxLayout()
        queue_label = QLabel("Queue")
        queue_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {ModernTheme.COLORS['text_primary']};
        """)
        queue_header.addWidget(queue_label)
        queue_header.addStretch()
        
        # Pause button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setProperty("class", "warning")
        self.pause_btn.setMaximumWidth(100)
        queue_header.addWidget(self.pause_btn)
        layout.addLayout(queue_header)
        
        # Queue list
        self.queue_list = QListWidget()
        self.queue_list.setMinimumHeight(150)
        self.queue_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {ModernTheme.COLORS['outline']};
                background-color: {ModernTheme.COLORS['surface']};
                border-radius: {ModernTheme.RADIUS['sm']};
            }}
            QListWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {ModernTheme.COLORS['outline']};
            }}
            QListWidget::item:last {{
                border-bottom: none;
            }}
        """)
        layout.addWidget(self.queue_list)
        
        # Start button
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernTheme.COLORS['success']};
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: {ModernTheme.RADIUS['md']};
                font-weight: 700;
                font-size: 13px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
            QPushButton:disabled {{
                background-color: {ModernTheme.COLORS['outline']};
                color: {ModernTheme.COLORS['text_disabled']};
            }}
        """)
        layout.addWidget(self.start_btn)

        # Timer for updating time estimates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_time_estimate)
        self.update_timer.start(1000)  # Update every second
        
        # Initialize language code based on current selection
        self.on_language_changed(self.language_combo.currentText())
        
        print("Interface initialization complete")
        logger.info("UI initialization completed")

    # All other methods remain the same from the original file
    def closeEvent(self, event):
        """Handle application closure with proper thread cleanup."""
        logger.info("Application closing - starting cleanup")
        print("\nClosing application - cleaning up resources...")
        
        if self.worker and self.worker.isRunning():
            print("Active worker thread detected - cleaning up...")
            try:
                # Stop the worker
                self.worker.stop()
                # Give the worker a chance to clean up
                if not self.worker.wait(3000):  # Wait up to 3 seconds
                    print("Worker thread taking too long to stop - forcing cleanup")
                    self.worker.terminate()
                print("Worker thread cleaned up successfully")
            except Exception as e:
                logger.error(f"Error during worker cleanup: {e}")
                print(f"Error during cleanup: {e}")
        
        # Cleanup pipeline resources if initialized
        if self.pipeline:
            try:
                self.pipeline.converter.cleanup_temp_files()
                print("Temporary files cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {e}")
        
        # Stop the update timer
        self.update_timer.stop()
        print("Cleanup completed - closing application")
        event.accept()

    def lazy_init_pipeline(self):
        """Lazily initialize the transcription pipeline when needed."""
        if self.pipeline is None:
            print("\nInitializing transcription pipeline...")
            # Get model settings from configuration
            model_size = self.settings.get('whisper_model_size', 'large')
            model_path = self.settings.get_whisper_model_path()
            
            # Check if faster-whisper should be used
            use_faster_whisper = self.use_faster_whisper_checkbox.isChecked()
            
            self.pipeline = TranscriptionPipeline(
                use_advanced_processing=self.settings.get('use_advanced_processing', True),
                model_size=model_size,
                model_path=str(model_path) if model_path else None,
                use_faster_whisper=use_faster_whisper,
                use_vad_enhancement=False  # Disable VAD to avoid onnxruntime issues
            )
            print("Pipeline initialized successfully")

    def update_time_estimate(self):
        """Update the estimated time remaining with enhanced accuracy."""
        if not self.current_file_start_time or not self.queue_manager.is_processing or self.is_paused:
            return
            
        current_time = time.time()
        elapsed_time = current_time - self.current_file_start_time
        
        # Calculate average time per file from completed files
        if self.processed_files_times:
            avg_time_per_file = sum(self.processed_files_times) / len(self.processed_files_times)
        else:
            avg_time_per_file = elapsed_time
        
        # Calculate remaining files
        remaining_files = len([
            item for item in self.queue_manager._queue 
            if item.status == FileStatus.QUEUED
        ])
        
        # Estimate total remaining time
        estimated_remaining = (avg_time_per_file * remaining_files) + (avg_time_per_file - elapsed_time)
        
        if estimated_remaining > 0:
            eta = datetime.now() + timedelta(seconds=int(estimated_remaining))
            eta_str = eta.strftime("%H:%M:%S")
            
            # Enhanced time formatting
            if estimated_remaining < 60:
                time_str = f"{int(estimated_remaining)} seconds"
            elif estimated_remaining < 3600:
                minutes = int(estimated_remaining / 60)
                time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
            else:
                hours = int(estimated_remaining / 3600)
                minutes = int((estimated_remaining % 3600) / 60)
                time_str = f"{hours}h {minutes}m"
            
            estimate_text = f"ETA: {eta_str} ({time_str} remaining)"
            self.time_estimate_label.setText(estimate_text)
            print(f"Updated time estimate: {estimate_text}")

    def update_progress(self, progress: float, status: str):
        """Update progress with enhanced status reporting."""
        if self.is_paused:
            return
            
        self.status_label.setText(status)
        self.progress_bar.setValue(int(progress * 100))
        
        # Update the queue list item's progress
        current_item = self.queue_manager.current_item
        if current_item:
            for i in range(self.queue_list.count()):
                item = self.queue_list.item(i)
                if str(current_item.file_path) == item.data(Qt.ItemDataRole.UserRole):
                    item.setText(f"🔄 In Progress ({progress:.1f}%): {current_item.file_path.name}")
                    item.setForeground(Qt.GlobalColor.blue)
                    break
        
        # Print progress to console
        print(f"\rProgress: {progress:.1f}% - {status}", end="", flush=True)

    def start_processing(self):
        """Start processing with enhanced error handling and status reporting."""
        if not self.queue_manager.queue_size:
            return
        
        print("\nStarting processing queue...")
        logger.info("Starting processing queue")
        
        # Lazy initialize pipeline if needed
        self.lazy_init_pipeline()
        
        # Disable buttons
        self.start_btn.setEnabled(False)
        self.add_files_btn.setEnabled(False)
        self.add_dir_btn.setEnabled(False)
        self.output_dir_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        
        # Enable pause button
        self.pause_btn.setEnabled(True)
        
        # Show progress section
        self.progress_group.show()
        
        try:
            # Get subtitle settings
            subtitle_formats = self.get_selected_subtitle_formats()
            max_chars_per_line = self.max_chars_spinbox.value() if subtitle_formats else 42
            
            # Create and setup worker with language and subtitle preferences
            self.worker = TranscriptionWorker(
                self.pipeline,
                self.queue_manager,
                self.output_directory,
                language_code=self.selected_language_code,
                subtitle_formats=subtitle_formats,
                max_chars_per_line=max_chars_per_line
            )
            
            # Connect signals
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.file_completed.connect(self.handle_file_completed)
            self.worker.all_completed.connect(self.handle_all_completed)
            self.worker.error_occurred.connect(self.handle_error)
            
            # Start processing
            print("Worker thread started")
            self.worker.start()
            
        except Exception as e:
            logger.error(f"Error starting processing: {e}")
            print(f"\nError starting processing: {e}")
            self.handle_error("Processing", str(e))

    def handle_file_completed(self, result):
        """Handle completion of a single file with enhanced reporting."""
        file_path = Path(result['file_path'])
        
        if result['success']:
            self.queue_manager.mark_completed(file_path)
            print(f"\nCompleted processing: {file_path.name}")
            
            # Record processing time
            if self.current_file_start_time:
                processing_time = time.time() - self.current_file_start_time
                self.processed_files_times.append(processing_time)
                print(f"Processing time: {processing_time:.2f} seconds")
            
            # Update queue list item
            for i in range(self.queue_list.count()):
                item = self.queue_list.item(i)
                if str(file_path) == item.data(Qt.ItemDataRole.UserRole):
                    item.setText(f"✓ Completed: {file_path.name}")
                    item.setForeground(Qt.GlobalColor.darkGreen)
                    break
        else:
            error_msg = result.get('error', 'Unknown error')
            self.queue_manager.mark_failed(file_path, error_msg)
            print(f"\nFailed to process {file_path.name}: {error_msg}")
            
            # Update queue list item
            for i in range(self.queue_list.count()):
                item = self.queue_list.item(i)
                if str(file_path) == item.data(Qt.ItemDataRole.UserRole):
                    item.setText(f"❌ Failed: {file_path.name}")
                    item.setForeground(Qt.GlobalColor.red)
                    break

    def handle_all_completed(self):
        """Handle completion of all files with final cleanup."""
        print("\nAll files processed - cleaning up...")
        logger.info("All files processed")
        
        # Clean up worker
        if self.worker:
            self.worker.stop()
            self.worker = None
        
        # Reset UI
        self.progress_group.hide()
        self.add_files_btn.setEnabled(True)
        self.add_dir_btn.setEnabled(True)
        self.output_dir_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.time_estimate_label.clear()
        
        # Show completion message with statistics
        completed_count = len([
            item for item in self.queue_manager._queue 
            if item.status == FileStatus.COMPLETED
        ])
        failed_count = len([
            item for item in self.queue_manager._queue 
            if item.status == FileStatus.FAILED
        ])
        
        total_time = sum(self.processed_files_times)
        avg_time = total_time / len(self.processed_files_times) if self.processed_files_times else 0
        
        completion_msg = (
            f"Processing completed!\n\n"
            f"Files processed: {completed_count + failed_count}\n"
            f"Successfully completed: {completed_count}\n"
            f"Failed: {failed_count}\n"
            f"Total processing time: {total_time:.1f} seconds\n"
            f"Average time per file: {avg_time:.1f} seconds"
        )
        
        print(f"\n{completion_msg}")
        QMessageBox.information(self, "Complete", completion_msg)

    def handle_error(self, file_path, error_msg):
        """Handle processing error with enhanced error reporting."""
        error_detail = f"Error processing {Path(file_path).name}: {error_msg}"
        logger.error(error_detail)
        print(f"\nError: {error_detail}")
        QMessageBox.critical(self, "Error", error_detail)

    def add_files(self):
        """Add individual files to the queue with enhanced feedback."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video Files",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov)"
        )
        
        if files:
            print(f"\nAdding {len(files)} files to queue...")
        
        files_added = 0
        for file_path in files:
            if self.queue_manager.add_file(file_path):
                item = QListWidgetItem(f"⏳ Queued: {Path(file_path).name}")
                item.setData(Qt.ItemDataRole.UserRole, str(file_path))
                item.setForeground(Qt.GlobalColor.gray)
                self.queue_list.addItem(item)
                files_added += 1
                print(f"Added to queue: {Path(file_path).name}")
        
        if files_added > 0:
            logger.info(f"Added {files_added} files to queue")
            print(f"Successfully added {files_added} files to queue")
            self.update_start_button()

    def add_directory(self):
        """Add all video files from a directory with enhanced feedback."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory with Videos"
        )
        
        if directory:
            directory_path = Path(directory)
            print(f"\nScanning directory: {directory_path}")
            
            # Track empty folders
            empty_folders = []
            video_files = []
            
            # Scan all subdirectories
            print("Scanning for video files...")
            for folder in [x for x in directory_path.rglob('*') if x.is_dir()]:
                video_count = 0
                for ext in ['.mp4', '.MP4', '.avi', '.mkv', '.mov']:
                    files = list(folder.glob(f"*{ext}"))
                    video_count += len(files)
                    video_files.extend(files)
                
                if video_count == 0:
                    empty_folders.append(folder)
            
            # Check root directory
            root_video_count = 0
            for ext in ['.mp4', '.MP4', '.avi', '.mkv', '.mov']:
                files = list(directory_path.glob(f"*{ext}"))
                root_video_count += len(files)
                for file in files:
                    if file not in video_files:
                        video_files.append(file)
                        
            if root_video_count == 0:
                empty_folders.append(directory_path)
            
            if not video_files:
                print("No video files found in directory")
                QMessageBox.warning(
                    self,
                    "No Videos Found",
                    f"No video files found in {directory_path} or its subdirectories."
                )
                return
            
            print(f"Found {len(video_files)} video files")
            
            # Add files to queue
            files_added = 0
            for file_path in video_files:
                if self.queue_manager.add_file(file_path):
                    item = QListWidgetItem(f"⏳ Queued: {file_path.name}")
                    item.setData(Qt.ItemDataRole.UserRole, str(file_path))
                    item.setForeground(Qt.GlobalColor.gray)
                    self.queue_list.addItem(item)
                    files_added += 1
                    print(f"Added to queue: {file_path.name}")
            
            # Create summary message
            summary_msg = f"Added {files_added} video files to the queue.\n\n"
            
            if empty_folders:
                print("\nEmpty folders found (no video files):")
                summary_msg += "The following folders contain no video files:\n"
                for folder in empty_folders:
                    try:
                        rel_path = folder.relative_to(directory_path)
                        folder_str = str(rel_path) if str(rel_path) != '.' else 'Root directory'
                    except ValueError:
                        folder_str = str(folder)
                    summary_msg += f"• {folder_str}\n"
                    print(f"• {folder_str}")
            
            QMessageBox.information(
                self,
                "Files Added",
                summary_msg
            )
            
            if files_added > 0:
                self.update_start_button()

    def select_output_dir(self):
        """Select output directory for transcripts."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory"
        )
        
        if directory:
            self.output_directory = Path(directory)
            self.output_dir_label.setText(f"Output Directory: {directory}")
            print(f"\nOutput directory set to: {directory}")
            self.update_start_button()

    def clear_queue(self):
        """Clear the processing queue with confirmation."""
        if self.queue_manager.is_processing:
            print("\nCannot clear queue while processing")
            QMessageBox.warning(
                self,
                "Cannot Clear Queue",
                "Cannot clear queue while processing files. Wait for current processing to finish."
            )
            return
            
        reply = QMessageBox.question(
            self,
            "Clear Queue",
            "Are you sure you want to clear all items from the queue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            print("\nClearing queue...")
            self.queue_manager.clear_queue()
            self.queue_list.clear()
            self.update_start_button()
            self.progress_bar.setValue(0)
            self.current_file_label.clear()
            self.status_label.setText("Queue cleared")
            self.time_estimate_label.clear()
            print("Queue cleared successfully")

    def update_start_button(self):
        """Update start button state based on queue and output directory."""
        enabled = (
            self.queue_manager.queue_size > 0 and 
            self.output_directory is not None and
            not self.queue_manager.is_processing
        )
        self.start_btn.setEnabled(enabled)
        
        if enabled:
            print("\nReady to start processing")
            self.status_label.setText("Ready to process files")

    def toggle_pause(self):
        """Pause or resume processing with enhanced status reporting."""
        if not self.worker:
            return
            
        print("\nToggling pause state...")
        
        if self.worker.is_paused:
            # Resume processing
            self.worker.resume()
            self.pause_btn.setText("Pause")
            self.pause_btn.setProperty("class", "warning")
            self.pause_btn.setStyle(self.pause_btn.style())  # Force style refresh
            self.status_label.setText("Processing resumed")
            print("Processing resumed")
        else:
            # Pause processing
            self.worker.pause()
            self.pause_btn.setText("Resume")
            self.pause_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ModernTheme.COLORS['success']};
                    color: white;
                    padding: 6px 16px;
                    border-radius: {ModernTheme.RADIUS['md']};
                    font-weight: 700;
                    font-size: 12px;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: #15803d;
                }}
            """)
            self.status_label.setText("Processing paused")
            print("Processing paused")
            
        logger.info(f"Processing {'resumed' if not self.worker.is_paused else 'paused'}")
    
    def load_model_folder(self):
        """Open dialog to select a folder containing Whisper models."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Whisper Model Folder",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            # Save the custom model folder
            self.settings.set('custom_model_folder', folder)
            
            # Update the model status
            self.update_model_status()
            
            # Check if we found any models
            available_models = self.settings.detect_available_models()
            model_size = self.settings.get('whisper_model_size', 'large')
            
            if model_size in available_models:
                QMessageBox.information(
                    self, 
                    "Model Found", 
                    f"Found {model_size} model in {folder}\n"
                    f"File: {available_models[model_size]['filename']}\n"
                    f"Size: {available_models[model_size]['size_mb']} MB"
                )
            else:
                QMessageBox.warning(
                    self,
                    "No Model Found",
                    f"No {model_size} model found in {folder}\n\n"
                    "Please ensure the folder contains Whisper model files (.pt)\n"
                    "Model files should be named like: tiny.pt, base.pt, small.pt, medium.pt, or large.pt"
                )
    
    def on_model_size_changed(self, model_size: str):
        """Handle model size selection change."""
        # Save the new model size preference
        self.settings.set('whisper_model_size', model_size)
        
        # Update the model status
        self.update_model_status()
        
        # If pipeline is already initialized, we'll need to reload it next time
        if self.pipeline:
            self.pipeline = None  # Force re-initialization with new model
            print(f"Model size changed to {model_size}. Will reload on next use.")
    
    def on_subtitle_export_changed(self, state):
        """Handle subtitle export checkbox toggle."""
        if state == 2:  # Checked
            self.subtitle_formats_group.show()
            self.use_faster_whisper_checkbox.show()
            # Auto-check faster-whisper for better subtitle timing
            self.use_faster_whisper_checkbox.setChecked(True)
        else:
            self.subtitle_formats_group.hide()
            self.use_faster_whisper_checkbox.hide()
    
    def on_faster_whisper_changed(self, state):
        """Handle faster-whisper checkbox toggle."""
        if self.pipeline:
            self.pipeline = None  # Force re-initialization with new setting
            if state == 2:  # Checked
                print("Faster-whisper enabled for word-level timestamps (better subtitle timing)")
            else:
                print("Using standard Whisper (no word timestamps on Windows)")
    
    def get_selected_subtitle_formats(self):
        """Get list of selected subtitle formats."""
        formats = []
        if self.subtitle_export_checkbox.isChecked():
            if self.srt_checkbox.isChecked():
                formats.append('srt')
            if self.vtt_checkbox.isChecked():
                formats.append('vtt')
            if self.ass_checkbox.isChecked():
                formats.append('ass')
        return formats
    
    def on_language_changed(self, language_selection: str):
        """Handle language selection change."""
        # Save the language preference
        self.settings.set('transcription_language', language_selection)
        
        # Extract language code from selection (e.g., "Spanish (es)" -> "es")
        if language_selection == "Auto-detect":
            language_code = None
        else:
            # Extract code from format "Language (code)"
            try:
                language_code = language_selection.split('(')[1].rstrip(')')
            except IndexError:
                language_code = None
        
        # Store the language code for use during transcription
        self.selected_language_code = language_code
        logger.info(f"Language changed to {language_selection} (code: {language_code})")
        print(f"Transcription language set to: {language_selection}")
    
    def update_model_status(self):
        """Update the model status label based on available models."""
        model_size = self.settings.get('whisper_model_size', 'large')
        model_path = self.settings.get_whisper_model_path()
        
        if model_path:
            # Model found locally
            self.model_status_label.setText(f"Model: {model_size} (Local)")
            self.model_status_label.setStyleSheet(f"""
                color: {ModernTheme.COLORS['success']};
                font-size: 12px;
                padding: 4px 8px;
                border: 1px solid {ModernTheme.COLORS['success']};
                border-radius: {ModernTheme.RADIUS['sm']};
                background-color: {ModernTheme.COLORS['surface_variant']};
                min-width: 200px;
            """)
        else:
            # Model will be downloaded
            self.model_status_label.setText(f"Model: {model_size} (Will download)")
            self.model_status_label.setStyleSheet(f"""
                color: {ModernTheme.COLORS['warning']};
                font-size: 12px;
                padding: 4px 8px;
                border: 1px solid {ModernTheme.COLORS['warning']};
                border-radius: {ModernTheme.RADIUS['sm']};
                background-color: {ModernTheme.COLORS['surface_variant']};
                min-width: 200px;
            """)