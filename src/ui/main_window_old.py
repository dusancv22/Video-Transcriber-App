from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QListWidget, QListWidgetItem, QMessageBox, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QThread
from PyQt6.QtGui import QIcon, QFont
from pathlib import Path
from src.transcription.transcription_pipeline import TranscriptionPipeline
from src.input_handling.queue_manager import QueueManager, FileStatus
from src.ui.worker import TranscriptionWorker
from src.ui.styles.modern_theme import ModernTheme
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Transcriber")
        self.setMinimumSize(900, 650)  # Reduced height for more compact design
        
        # Set application icon
        icon_path = Path(__file__).parent.parent.parent / "assets" / "icons" / "app_icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Apply modern theme
        self.setStyleSheet(ModernTheme.get_stylesheet())
        
        # Initialize components
        self.pipeline = None  # Lazy initialization
        self.queue_manager = QueueManager()
        self.output_directory = None
        self.worker = None
        
        # Time tracking
        self.current_file_start_time = None
        self.processed_files_times = []
        self.is_paused = False
        
        # Initialize UI
        self.init_ui()
        logger.info("MainWindow initialized")
        
    def init_ui(self):
        """Initialize the user interface with modern Material Design."""
        # Create central widget with modern styling
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        
        # Main layout with compact spacing
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Title section
        title_label = QLabel("Video Transcriber")
        title_label.setObjectName("appTitle")
        title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 600;
            color: {ModernTheme.COLORS['text_primary']};
            margin-bottom: 4px;
        """)
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Transform videos into accurate text transcripts")
        subtitle_label.setStyleSheet(f"""
            font-size: 13px;
            color: {ModernTheme.COLORS['text_secondary']};
            margin-bottom: 12px;
        """)
        main_layout.addWidget(subtitle_label)
        
        # Status message for initialization
        print("Initializing Video Transcriber interface...")
        
        # Create controls card
        controls_card = QFrame()
        controls_card.setObjectName("controlsCard")
        controls_card.setStyleSheet(f"""
            QFrame#controlsCard {{
                background-color: {ModernTheme.COLORS['surface']};
                border: 1px solid {ModernTheme.COLORS['outline']};
                border-radius: {ModernTheme.RADIUS['lg']};
                padding: 16px;
            }}
        """)
        
        # Add shadow effect to card
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(Qt.GlobalColor.gray)
        controls_card.setGraphicsEffect(shadow)
        
        controls_layout = QHBoxLayout(controls_card)
        controls_layout.setSpacing(8)
        
        # Add Files button with icon
        self.add_files_btn = QPushButton("📁 Add Files")
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_files_btn.setObjectName("primaryButton")
        controls_layout.addWidget(self.add_files_btn)

        # Add Directory button with icon
        self.add_dir_btn = QPushButton("📂 Add Directory")
        self.add_dir_btn.clicked.connect(self.add_directory)
        self.add_dir_btn.setObjectName("primaryButton")
        controls_layout.addWidget(self.add_dir_btn)
        
        # Output Directory button with icon
        self.output_dir_btn = QPushButton("💾 Output Directory")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        self.output_dir_btn.setProperty("class", "secondary")
        controls_layout.addWidget(self.output_dir_btn)

        # Clear Queue button with icon
        self.clear_btn = QPushButton("🗑️ Clear Queue")
        self.clear_btn.clicked.connect(self.clear_queue)
        self.clear_btn.setProperty("class", "danger")
        controls_layout.addWidget(self.clear_btn)
        
        controls_layout.addStretch()
        main_layout.addWidget(controls_card)
        
        # Output directory info card
        output_card = QFrame()
        output_card.setStyleSheet(f"""
            background-color: {ModernTheme.COLORS['primary_light']};
            border: 1px solid {ModernTheme.COLORS['primary']};
            border-radius: {ModernTheme.RADIUS['md']};
            padding: 8px 12px;
        """)
        output_layout = QHBoxLayout(output_card)
        
        self.output_dir_label = QLabel("📍 Output Directory: Not Selected")
        self.output_dir_label.setStyleSheet(f"""
            color: {ModernTheme.COLORS['primary']};
            font-weight: 500;
        """)
        output_layout.addWidget(self.output_dir_label)
        output_layout.addStretch()
        
        main_layout.addWidget(output_card)
        
        # Progress section card
        self.progress_group = QFrame()
        self.progress_group.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernTheme.COLORS['surface']};
                border: 1px solid {ModernTheme.COLORS['outline']};
                border-radius: {ModernTheme.RADIUS['lg']};
                padding: 16px;
            }}
        """)
        progress_layout = QVBoxLayout(self.progress_group)
        progress_layout.setSpacing(8)
        
        # Add progress info layout
        progress_info_layout = QHBoxLayout()
        
        self.current_file_label = QLabel("")
        self.current_file_label.setStyleSheet("font-weight: bold;")
        progress_info_layout.addWidget(self.current_file_label)
        
        self.time_estimate_label = QLabel("")
        self.time_estimate_label.setStyleSheet("color: #6b7280;")
        progress_info_layout.addWidget(self.time_estimate_label)
        
        progress_layout.addLayout(progress_info_layout)
        
        # Modern progress bar with gradient
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        progress_layout.addWidget(self.progress_bar)
        
        # Enhanced status label
        self.status_label = QLabel("")
        self.status_label.setProperty("class", "caption")
        progress_layout.addWidget(self.status_label)
        
        self.progress_group.hide()
        main_layout.addWidget(self.progress_group)
        
        # Queue section with modern card
        queue_card = QFrame()
        queue_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernTheme.COLORS['surface']};
                border: 1px solid {ModernTheme.COLORS['outline']};
                border-radius: {ModernTheme.RADIUS['lg']};
                padding: 16px;
            }}
        """)
        queue_layout = QVBoxLayout(queue_card)
        
        # Queue header
        queue_header_layout = QHBoxLayout()
        queue_label = QLabel("📋 Queue")
        queue_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {ModernTheme.COLORS['text_primary']};
        """)
        queue_header_layout.addWidget(queue_label)
        
        # Pause/Resume button with modern styling
        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setProperty("class", "warning")
        queue_header_layout.addWidget(self.pause_btn)
        queue_header_layout.addStretch()
        
        queue_layout.addLayout(queue_header_layout)
        
        # Modern queue list
        self.queue_list = QListWidget()
        self.queue_list.setMinimumHeight(200)
        queue_layout.addWidget(self.queue_list)
        
        main_layout.addWidget(queue_card)
        
        # Start button with modern styling
        self.start_btn = QPushButton("▶️ Start Processing")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ModernTheme.COLORS['success']},
                    stop:1 #059669
                );
                color: white;
                padding: 12px;
                border-radius: {ModernTheme.RADIUS['md']};
                font-weight: 600;
                font-size: 15px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669,
                    stop:1 {ModernTheme.COLORS['success']}
                );
            }}
            QPushButton:disabled {{
                background-color: {ModernTheme.COLORS['outline']};
                color: {ModernTheme.COLORS['text_disabled']};
            }}
        """)
        main_layout.addWidget(self.start_btn)

        # Timer for updating time estimates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_time_estimate)
        self.update_timer.start(1000)  # Update every second
        
        print("Interface initialization complete")
        logger.info("UI initialization completed")

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
            self.pipeline = TranscriptionPipeline()
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
            # Create and setup worker
            self.worker = TranscriptionWorker(
                self.pipeline,
                self.queue_manager,
                self.output_directory
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
            self.output_dir_label.setText(f"📍 Output Directory: {directory}")
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
            self.pause_btn.setText("⏸️ Pause")
            self.pause_btn.setProperty("class", "warning")
            self.pause_btn.setStyle(self.pause_btn.style())  # Force style refresh
            self.status_label.setText("Processing resumed")
            print("Processing resumed")
        else:
            # Pause processing
            self.worker.pause()
            self.pause_btn.setText("▶️ Resume")
            self.pause_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ModernTheme.COLORS['success']};
                    color: white;
                    padding: 12px 20px;
                    border-radius: {ModernTheme.RADIUS['md']};
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: #15803d;
                }}
            """)
            self.status_label.setText("Processing paused")
            print("Processing paused")
            
        logger.info(f"Processing {'resumed' if not self.worker.is_paused else 'paused'}")