"""
Flat, modern main window implementation for Video Transcriber App
This replaces the card-based design with a clean, efficient layout
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QListWidget, QListWidgetItem, QMessageBox, QComboBox,
    QCheckBox, QSpinBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
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
        self.setMinimumSize(840, 560)

        # Supported input formats (video + audio). Keep in sync with FileHandler.
        self.supported_media_suffixes = {'.mp4', '.avi', '.mkv', '.mov', '.webm', '.mp3'}
        self.supported_media_dialog_filter = (
            "Media Files (*.mp4 *.avi *.mkv *.mov *.webm *.mp3);;All Files (*)"
        )
        self._active_file_path = None
        
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
        self.selected_language_code = None  # Will be set based on language dropdown
        
        # Time tracking
        self.current_file_start_time = None
        self.processed_files_times = []
        self.is_paused = False

        # Native status bar (QMainWindow) message updates.
        self.statusBar().showMessage("Ready")
        
        # Initialize UI
        self.init_ui()
        logger.info("MainWindow initialized")
        
    def init_ui(self):
        """Initialize flat, modern UI layout"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(14, 12, 14, 8)
        layout.setSpacing(10)
        
        print("Initializing Video Transcriber interface...")
        
        # Toolbar - flat button layout
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Clean buttons without icons
        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_files_btn.setFixedSize(92, 36)
        toolbar.addWidget(self.add_files_btn)
        
        self.add_dir_btn = QPushButton("Add Directory") 
        self.add_dir_btn.clicked.connect(self.add_directory)
        self.add_dir_btn.setFixedSize(112, 36)
        toolbar.addWidget(self.add_dir_btn)
        
        self.output_dir_btn = QPushButton("Select Output")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        self.output_dir_btn.setProperty("class", "secondary")
        self.output_dir_btn.setFixedSize(116, 36)
        toolbar.addWidget(self.output_dir_btn)

        self.save_to_source_checkbox = QCheckBox("Save to source folder")
        self.save_to_source_checkbox.setToolTip(
            "Save each transcript next to its source file instead of a single output directory"
        )
        self.save_to_source_checkbox.setStyleSheet(f"""
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
        self.save_to_source_checkbox.stateChanged.connect(self.on_save_to_source_changed)
        self.save_to_source_checkbox.setFixedHeight(36)
        toolbar.addWidget(self.save_to_source_checkbox)

        self.clear_btn = QPushButton("Clear Queue")
        self.clear_btn.clicked.connect(self.clear_queue) 
        self.clear_btn.setProperty("class", "danger")
        self.clear_btn.setFixedSize(110, 36)
        toolbar.addWidget(self.clear_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Status line
        self.output_dir_label = QLabel("Output Directory: Not Selected")
        self.output_dir_label.setStyleSheet(f"""
            color: {ModernTheme.COLORS['text_secondary']};
            font-size: 12px;
            padding: 5px 9px;
            border: 1px solid {ModernTheme.COLORS['outline']};
            border-radius: {ModernTheme.RADIUS['md']};
            background-color: {ModernTheme.COLORS['surface_variant']};
            min-height: 22px;
        """)
        layout.addWidget(self.output_dir_label)
        
        # Model selection section
        model_section = QHBoxLayout()
        model_section.setSpacing(8)
        model_section.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Model status label
        self.model_status_label = QLabel("Whisper Model: Default")
        self.model_status_label.setStyleSheet(f"""
            color: {ModernTheme.COLORS['text_secondary']};
            font-size: 12px;
            padding: 4px 8px;
            border: 1px solid {ModernTheme.COLORS['outline']};
            border-radius: {ModernTheme.RADIUS['md']};
            background-color: {ModernTheme.COLORS['surface_variant']};
            min-width: 200px;
        """)
        self.model_status_label.setFixedHeight(36)
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
                border-radius: {ModernTheme.RADIUS['md']};
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
        self.model_size_combo.setFixedSize(116, 36)
        model_section.addWidget(self.model_size_combo)
        
        # Language selection dropdown
        self.language_label = QLabel("Language:")
        self.language_label.setStyleSheet(f"""
            color: {ModernTheme.COLORS['text_secondary']};
            font-size: 12px;
            padding: 0px 2px;
            border: none;
            background: transparent;
        """)
        self.language_label.setFixedHeight(36)
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
                border-radius: {ModernTheme.RADIUS['md']};
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
        self.language_combo.setFixedSize(156, 36)
        model_section.addWidget(self.language_combo)
        
        # Load model button
        self.load_model_btn = QPushButton("Load Model Folder")
        self.load_model_btn.clicked.connect(self.load_model_folder)
        self.load_model_btn.setProperty("class", "secondary")
        self.load_model_btn.setFixedSize(136, 36)
        model_section.addWidget(self.load_model_btn)
        
        model_section.addStretch()
        layout.addLayout(model_section)
        
        # Subtitle export section. Separate rows prevent hidden controls when
        # subtitle formats and translation options are both visible.
        subtitle_section = QVBoxLayout()
        subtitle_section.setSpacing(6)
        subtitle_header_row = QHBoxLayout()
        subtitle_header_row.setSpacing(8)
        subtitle_formats_row = QHBoxLayout()
        subtitle_formats_row.setSpacing(8)
        subtitle_translation_row = QHBoxLayout()
        subtitle_translation_row.setSpacing(8)
        
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
        self.subtitle_export_checkbox.setFixedHeight(28)
        subtitle_header_row.addWidget(self.subtitle_export_checkbox)
        
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
        self.use_faster_whisper_checkbox.setFixedHeight(28)
        subtitle_header_row.addWidget(self.use_faster_whisper_checkbox)
        subtitle_header_row.addStretch()
        
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
        subtitle_formats_row.addWidget(self.subtitle_formats_group)
        subtitle_formats_row.addStretch()
        
        # Translation options section (initially hidden)
        self.translation_group = QWidget()
        translation_layout = QHBoxLayout(self.translation_group)
        translation_layout.setContentsMargins(0, 0, 0, 0)
        translation_layout.setSpacing(8)
        
        # Translation checkbox
        self.translate_checkbox = QCheckBox("Translate")
        self.translate_checkbox.setToolTip(
            "Translate subtitles to another language while preserving timestamps.\n"
            "- PT to EN: Uses advanced TowerInstruct model (GPU required, best quality)\n"
            "- Other languages: Uses Helsinki-NLP models (CPU, no API keys needed)\n"
            "Falls back to standard translation if GPU not available."
        )
        self.translate_checkbox.setStyleSheet(f"""
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
                background: {ModernTheme.COLORS['surface']};
            }}
            QCheckBox::indicator:checked {{
                background: {ModernTheme.COLORS['primary']};
                border-color: {ModernTheme.COLORS['primary']};
            }}
        """)
        self.translate_checkbox.stateChanged.connect(self.on_translate_changed)
        translation_layout.addWidget(self.translate_checkbox)
        
        # Source language combo (initially hidden)
        self.source_lang_label = QLabel("From:")
        self.source_lang_label.setStyleSheet(f"color: {ModernTheme.COLORS['text_secondary']}; font-size: 12px;")
        self.source_lang_label.hide()
        translation_layout.addWidget(self.source_lang_label)
        
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems([
            "Auto-detect",
            "Portuguese (pt)",  # Move to top for easier access
            "Spanish (es)",
            "French (fr)",
            "German (de)",
            "Italian (it)",
            "Russian (ru)",
            "Chinese (zh)",
            "Japanese (ja)",
            "English (en)"
        ])
        self.source_lang_combo.currentTextChanged.connect(lambda: self.check_translation_engine())
        self.source_lang_combo.setStyleSheet(f"""
            QComboBox {{
                background: {ModernTheme.COLORS['surface']};
                border: 1px solid {ModernTheme.COLORS['outline']};
                border-radius: 6px;
                padding: 4px 8px;
                color: {ModernTheme.COLORS['text_primary']};
                font-size: 12px;
                min-width: 100px;
            }}
            QComboBox:hover {{
                border-color: {ModernTheme.COLORS['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 4px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {ModernTheme.COLORS['text_tertiary']};
                margin-right: 4px;
            }}
        """)
        self.source_lang_combo.hide()
        translation_layout.addWidget(self.source_lang_combo)
        
        # Target language combo (initially hidden)
        self.target_lang_label = QLabel("To:")
        self.target_lang_label.setStyleSheet(f"color: {ModernTheme.COLORS['text_secondary']}; font-size: 12px;")
        self.target_lang_label.hide()
        translation_layout.addWidget(self.target_lang_label)
        
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems([
            "English (en)",
            "Spanish (es)",
            "French (fr)",
            "German (de)",
            "Italian (it)",
            "Portuguese (pt)",
            "Russian (ru)",
            "Chinese (zh)",
            "Japanese (ja)"
        ])
        self.target_lang_combo.setCurrentIndex(0)  # Default to English
        self.target_lang_combo.currentTextChanged.connect(lambda: self.check_translation_engine())
        self.target_lang_combo.setStyleSheet(self.source_lang_combo.styleSheet())
        self.target_lang_combo.hide()
        translation_layout.addWidget(self.target_lang_combo)
        
        # Add translation engine status label
        self.translation_engine_label = QLabel("")
        self.translation_engine_label.setMaximumWidth(260)
        self.translation_engine_label.setToolTip("Translation engine selected for this language pair")
        self.translation_engine_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernTheme.COLORS['primary']};
                font-size: 11px;
                font-weight: bold;
                padding: 2px 8px;
                background: {ModernTheme.COLORS['primary']}20;
                border-radius: 4px;
            }}
        """)
        self.translation_engine_label.hide()
        translation_layout.addWidget(self.translation_engine_label)
        
        self.translation_group.hide()
        subtitle_translation_row.addWidget(self.translation_group)
        subtitle_translation_row.addStretch()
        
        subtitle_section.addLayout(subtitle_header_row)
        subtitle_section.addLayout(subtitle_formats_row)
        subtitle_section.addLayout(subtitle_translation_row)
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
        queue_header.setContentsMargins(0, 4, 0, 0)
        queue_header.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        queue_label = QLabel("Queue")
        queue_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {ModernTheme.COLORS['text_primary']};
            border: none;
            background: transparent;
            padding: 0px;
        """)
        queue_label.setFixedHeight(28)
        queue_header.addWidget(queue_label)
        queue_header.addStretch()
        
        # Pause button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setProperty("class", "warning")
        self.pause_btn.setFixedSize(86, 34)
        self.pause_btn.hide()
        queue_header.addWidget(self.pause_btn)
        layout.addLayout(queue_header)
        
        # Queue list
        self.queue_list = QListWidget()
        self.queue_list.setMinimumHeight(190)
        self.queue_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        self.start_btn.setFixedHeight(42)
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

    def closeEvent(self, event):
        """Handle application closure with proper thread cleanup."""
        logger.info("Application closing - starting cleanup")
        print("\nClosing application - cleaning up resources...")
        
        if self.worker and self.worker.isRunning():
            print("Active worker thread detected - cleaning up...")
            try:
                # stop() cancels the in-progress transcription (the whisper
                # manager checks a cancel flag between segments), so the worker
                # normally exits within a couple of seconds.
                self.worker.stop()
                if not self.worker.wait(10000):  # Give cancellation 10s to land
                    logger.error("Worker did not stop after cancellation - forcing termination")
                    print("Worker thread unresponsive - forcing termination (last resort)")
                    self.worker.terminate()
                    self.worker.wait(2000)
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
        remaining_files = self.queue_manager.count_by_status(FileStatus.QUEUED)
        
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

        # progress is normalized (0.0 -> 1.0)
        progress = max(0.0, min(1.0, float(progress)))
        percent = progress * 100.0

        self.status_label.setText(status)
        self.progress_bar.setValue(int(percent))
        
        # Update the queue list item's progress
        current_item = self.queue_manager.current_item
        if current_item:
            # Detect file change to reset per-file timer/label.
            if self._active_file_path != current_item.file_path:
                self._active_file_path = current_item.file_path
                self.current_file_start_time = time.time()

            total_files = self.queue_manager.queue_size
            done_files = self.queue_manager.count_by_status(
                FileStatus.COMPLETED, FileStatus.FAILED
            )
            current_index = min(done_files + 1, total_files) if total_files else 0
            self.current_file_label.setText(
                f"File {current_index}/{total_files}: {current_item.file_path.name}"
            )
            self.statusBar().showMessage(
                f"{current_item.file_path.name} | {status} ({percent:.1f}%)"
            )

            for i in range(self.queue_list.count()):
                item = self.queue_list.item(i)
                if str(current_item.file_path) == item.data(Qt.ItemDataRole.UserRole):
                    item.setText(f"🔄 In Progress ({percent:.1f}%): {current_item.file_path.name}")
                    item.setForeground(Qt.GlobalColor.blue)
                    break
        
        # Print progress to console (use newline to avoid overwriting debug output)
        print(f"Progress: {percent:.1f}% - {status}")

    def start_processing(self):
        """Start processing with enhanced error handling and status reporting."""
        if not self.queue_manager.queue_size:
            return

        # Reset run-specific state/UI.
        self.processed_files_times = []
        self.current_file_start_time = None
        self._active_file_path = None
        self.current_file_label.clear()
        self.status_label.clear()
        self.progress_bar.setValue(0)
        self.queue_manager.start_processing()
        
        print("\nStarting processing queue...")
        logger.info("Starting processing queue")
        
        # Lazy initialize pipeline if needed
        self.lazy_init_pipeline()
        
        # Disable buttons
        self.start_btn.setEnabled(False)
        self.add_files_btn.setEnabled(False)
        self.add_dir_btn.setEnabled(False)
        self.output_dir_btn.setEnabled(False)
        self.save_to_source_checkbox.setEnabled(False)
        self.clear_btn.setEnabled(False)

        # Enable pause button
        self.pause_btn.setEnabled(True)
        self.pause_btn.show()
        
        # Show progress section
        self.progress_group.show()
        
        try:
            # Get subtitle settings
            subtitle_formats = self.get_selected_subtitle_formats()
            max_chars_per_line = self.max_chars_spinbox.value() if subtitle_formats else 42
            
            # Get translation settings
            translation_settings = self.get_translation_settings()
            
            # Create and setup worker with language and subtitle preferences
            self.worker = TranscriptionWorker(
                self.pipeline,
                self.queue_manager,
                self.output_directory,
                language_code=self.selected_language_code,
                subtitle_formats=subtitle_formats,
                max_chars_per_line=max_chars_per_line,
                translation_settings=translation_settings,
                save_to_source=self.save_to_source_checkbox.isChecked()
            )
            
            # Connect signals
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.file_completed.connect(self.handle_file_completed)
            self.worker.all_completed.connect(self.handle_all_completed)
            self.worker.error_occurred.connect(self.handle_error)
            # Release our reference only after the thread has actually finished
            self.worker.finished.connect(self._on_worker_finished)
            
            # Start processing
            print("Worker thread started")
            self.worker.start()
            
        except Exception as e:
            logger.error(f"Error starting processing: {e}")
            print(f"\nError starting processing: {e}")
            # Startup failure: no completion dialog will follow, so a modal is
            # appropriate here (unlike per-file failures during a batch).
            QMessageBox.critical(self, "Error", f"Failed to start processing: {e}")
            self.handle_error("Processing", str(e))

    def handle_file_completed(self, result):
        """Handle completion of a single file with enhanced reporting."""
        file_path = Path(result['file_path'])
        
        if result['success']:
            self.queue_manager.mark_completed(file_path)
            print(f"\nCompleted processing: {file_path.name}")
            
            # Record processing time
            processing_time = result.get('processing_time')
            if processing_time is not None:
                self.processed_files_times.append(float(processing_time))
                print(f"Processing time: {float(processing_time):.2f} seconds")
            
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

        self.queue_manager.stop_processing()
        self.current_file_start_time = None
        self._active_file_path = None
        self.statusBar().showMessage("All files processed")

        # The worker's run() ends on its own after emitting all_completed;
        # _on_worker_finished (connected to QThread.finished) releases the
        # reference once the thread has actually exited. Dropping it here
        # risked "QThread destroyed while running".

        # Reset UI
        self.progress_group.hide()
        self.add_files_btn.setEnabled(True)
        self.add_dir_btn.setEnabled(True)
        self.output_dir_btn.setEnabled(not self.save_to_source_checkbox.isChecked())
        self.save_to_source_checkbox.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.hide()
        self.time_estimate_label.clear()
        
        # Show completion message with statistics (snapshot: thread-safe copy)
        queue_snapshot = self.queue_manager.get_items_snapshot()
        completed_count = len([
            item for item in queue_snapshot
            if item.status == FileStatus.COMPLETED
        ])
        failed_items = [
            item for item in queue_snapshot
            if item.status == FileStatus.FAILED
        ]
        failed_count = len(failed_items)
        
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

        if failed_items:
            failure_details = "\n".join(
                f"- {item.file_path.name}: {item.error or 'Unknown error'}"
                for item in failed_items[:5]
            )
            if len(failed_items) > 5:
                failure_details += f"\n- ...and {len(failed_items) - 5} more"
            completion_msg += (
                "\n\nFailed files:\n"
                f"{failure_details}\n\n"
                "Full details are saved in app_output.log."
            )
        
        print(f"\n{completion_msg}")
        title = "Complete" if failed_count == 0 else "Completed with Failures"
        QMessageBox.information(self, title, completion_msg)

    def _on_worker_finished(self):
        """Release the worker reference once its thread has fully exited."""
        worker = self.sender()
        if worker is not None:
            worker.deleteLater()
        if worker is self.worker:
            self.worker = None
        logger.info("Worker thread finished and released")

    def handle_error(self, file_path, error_msg):
        """Handle processing error with enhanced error reporting."""
        error_detail = f"Error processing {Path(file_path).name}: {error_msg}"
        logger.error(error_detail)
        print(f"\nError: {error_detail}")
        self.statusBar().showMessage(f"Error: {Path(file_path).name}")

        # If this error belongs to a queued file, mark it failed so the batch can continue cleanly.
        try:
            failed_path = Path(file_path)
            if self.queue_manager.contains(failed_path):
                self.queue_manager.mark_failed(failed_path, error_msg)
                for i in range(self.queue_list.count()):
                    item = self.queue_list.item(i)
                    if str(failed_path) == item.data(Qt.ItemDataRole.UserRole):
                        item.setText(f"❌ Failed: {failed_path.name}")
                        item.setForeground(Qt.GlobalColor.red)
                        break
        except Exception:
            # Best-effort; the failure is still logged and shown in the queue list.
            pass

        # No modal dialog here: with a batch of failing files, one dialog per
        # failure stacks modal windows while the worker keeps running. Failures
        # are marked in the queue list immediately and summarized in the
        # completion dialog (handle_all_completed).

    def add_files(self):
        """Add individual files to the queue with enhanced feedback."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Media Files",
            "",
            self.supported_media_dialog_filter
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
        """Add all supported media files from a directory with enhanced feedback."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory with Media Files"
        )
        
        if directory:
            directory_path = Path(directory)
            print(f"\nScanning directory: {directory_path}")
            
            # Track empty folders
            empty_folders = []
            media_files = []
            
            # Scan root + all subdirectories for supported media files (case-insensitive).
            print("Scanning for media files...")
            folders = [directory_path] + [x for x in directory_path.rglob('*') if x.is_dir()]
            for folder in folders:
                try:
                    folder_media = [
                        p for p in folder.iterdir()
                        if p.is_file() and p.suffix.lower() in self.supported_media_suffixes
                    ]
                except Exception as e:
                    logger.warning(f"Failed to scan folder {folder}: {e}")
                    continue

                if folder_media:
                    media_files.extend(folder_media)
                else:
                    empty_folders.append(folder)
            
            if not media_files:
                print("No media files found in directory")
                QMessageBox.warning(
                    self,
                    "No Media Files Found",
                    f"No supported media files found in {directory_path} or its subdirectories."
                )
                return
            
            # Stable order in queue.
            media_files = sorted(media_files, key=lambda p: str(p).lower())
            print(f"Found {len(media_files)} media files")
            
            # Add files to queue
            files_added = 0
            for file_path in media_files:
                if self.queue_manager.add_file(file_path):
                    item = QListWidgetItem(f"⏳ Queued: {file_path.name}")
                    item.setData(Qt.ItemDataRole.UserRole, str(file_path))
                    item.setForeground(Qt.GlobalColor.gray)
                    self.queue_list.addItem(item)
                    files_added += 1
                    print(f"Added to queue: {file_path.name}")
            
            # Create summary message
            summary_msg = f"Added {files_added} media files to the queue.\n\n"
            
            if empty_folders:
                print("\nEmpty folders found (no media files):")
                summary_msg += "The following folders contain no supported media files:\n"
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

    @staticmethod
    def _is_checked(state: int) -> bool:
        """Interpret a stateChanged signal value (int) as checked/unchecked."""
        return Qt.CheckState(state) == Qt.CheckState.Checked

    @staticmethod
    def _lang_code_from_combo_text(text: str, auto_value=None):
        """Extract the language code from a combo entry like "Spanish (es)".

        Returns auto_value for the "Auto-detect" entry or when no code is present.
        """
        if text == "Auto-detect" or '(' not in text:
            return auto_value
        return text.split('(')[-1].rstrip(')')

    def on_save_to_source_changed(self, state):
        """Handle save-to-source checkbox toggle."""
        if self._is_checked(state):
            self.output_dir_btn.setEnabled(False)
            self.output_dir_label.setText("Output: Saving to each file's source folder")
            print("Save to source folder enabled")
        else:
            self.output_dir_btn.setEnabled(True)
            if self.output_directory:
                self.output_dir_label.setText(f"Output Directory: {self.output_directory}")
            else:
                self.output_dir_label.setText("Output Directory: Not Selected")
            print("Save to source folder disabled")
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
            (self.output_directory is not None or self.save_to_source_checkbox.isChecked()) and
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
            self.is_paused = False
            self.pause_btn.setText("Pause")
            self.pause_btn.setProperty("class", "warning")
            self.pause_btn.setStyle(self.pause_btn.style())  # Force style refresh
            self.status_label.setText("Processing resumed")
            print("Processing resumed")
        else:
            # Pause processing (takes effect between transcription segments,
            # typically within a second or two)
            self.worker.pause()
            self.is_paused = True
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
        if self._is_checked(state):
            self.subtitle_formats_group.show()
            self.use_faster_whisper_checkbox.show()
            self.translation_group.show()  # Show translation options
            # Auto-check faster-whisper for better subtitle timing
            self.use_faster_whisper_checkbox.setChecked(True)
        else:
            self.subtitle_formats_group.hide()
            self.use_faster_whisper_checkbox.hide()
            self.translation_group.hide()  # Hide translation options
            self.translate_checkbox.setChecked(False)
    
    def on_faster_whisper_changed(self, state):
        """Handle faster-whisper checkbox toggle."""
        if self.pipeline:
            self.pipeline = None  # Force re-initialization with new setting
            if self._is_checked(state):
                print("Faster-whisper enabled for word-level timestamps (better subtitle timing)")
            else:
                print("Using standard Whisper (no word timestamps on Windows)")
    
    def on_translate_changed(self, state):
        """Handle translation checkbox toggle."""
        if self._is_checked(state):
            self.source_lang_label.show()
            self.source_lang_combo.show()
            self.target_lang_label.show()
            self.target_lang_combo.show()
            print("Translation enabled - subtitles will be translated after generation")
            self.check_translation_engine()
        else:
            self.source_lang_label.hide()
            self.source_lang_combo.hide()
            self.target_lang_label.hide()
            self.target_lang_combo.hide()
            self.translation_engine_label.hide()
    
    def check_translation_engine(self):
        """Display the translation engine that will be used.

        Helsinki-NLP is the only engine (TowerInstruct was removed - it was
        permanently disabled for being too slow, ~10+ minutes per file).
        """
        if not self.translate_checkbox.isChecked():
            self.translation_engine_label.hide()
            return

        self.translation_engine_label.setText("Helsinki-NLP Translation")
        self.translation_engine_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernTheme.COLORS['text_secondary']};
                font-size: 11px;
                padding: 2px 8px;
                background: {ModernTheme.COLORS['surface']};
                border-radius: 4px;
            }}
        """)
        self.translation_engine_label.show()
    
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
    
    def get_translation_settings(self):
        """Get translation settings if enabled."""
        if self.translate_checkbox.isChecked():
            return {
                'enabled': True,
                'source_lang': self._lang_code_from_combo_text(
                    self.source_lang_combo.currentText(), auto_value='auto'
                ),
                'target_lang': self._lang_code_from_combo_text(
                    self.target_lang_combo.currentText(), auto_value='en'
                )
            }
        return {'enabled': False}
    
    def on_language_changed(self, language_selection: str):
        """Handle language selection change."""
        # Save the language preference
        self.settings.set('transcription_language', language_selection)

        # Extract language code from selection (e.g., "Spanish (es)" -> "es");
        # None means auto-detect
        language_code = self._lang_code_from_combo_text(language_selection)

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
