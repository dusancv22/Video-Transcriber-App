from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QPushButton, QLabel, QFileDialog, QListWidget,
                            QHBoxLayout, QProgressBar)
from src.input_handling.file_handler import FileHandler
from src.audio_processing.converter import AudioConverter
from src.ui.main_window import MainWindow
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Transcriber")
        self.setGeometry(100, 100, 800, 600)

        # Initialize file handler and audio converter
        self.file_handler = FileHandler()
        self.audio_converter = AudioConverter()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        # Add file selection button
        self.select_button = QPushButton("Select Video Files")
        self.select_button.clicked.connect(self.select_files)
        button_layout.addWidget(self.select_button)
        
        # Add process button
        self.process_button = QPushButton("Start Processing")
        self.process_button.clicked.connect(self.start_processing)
        self.process_button.setEnabled(False)
        button_layout.addWidget(self.process_button)
        
        # Add clear button
        self.clear_button = QPushButton("Clear List")
        self.clear_button.clicked.connect(self.clear_files)
        button_layout.addWidget(self.clear_button)
        
        # Add button layout to main layout
        layout.addLayout(button_layout)
        
        # Add list widget to display selected files
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Add status label
        self.status_label = QLabel("Ready to process files")
        layout.addWidget(self.status_label)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video Files",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*.*)"
        )
        
        print(f"Selected files: {files}")  # Debug print
        
        files_added = 0
        for file_path in files:
            if self.file_handler.add_to_queue(file_path):
                self.file_list.addItem(file_path)
                files_added += 1
                print(f"Added to queue: {file_path}")  # Debug print
        
        if files_added > 0:
            self.process_button.setEnabled(True)
            self.status_label.setText(f"Added {files_added} files to queue")
            print(f"Total files in queue: {len(self.file_handler.queued_files)}")  # Debug print

    def clear_files(self):
        self.file_handler.clear_queue()
        self.file_list.clear()
        self.process_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ready to process files")

    def start_processing(self):
        # Debug print to check if we're entering the method
        print("Start processing called")
        
        # Check if there are any files in the queue
        if not self.file_handler.queued_files:
            self.status_label.setText("No files in queue to process")
            return
            
        print(f"Files in queue: {len(self.file_handler.queued_files)}")
        
        self.status_label.setText("Processing started...")
        self.progress_bar.setVisible(True)
        total_files = len(self.file_handler.queued_files)
        self.progress_bar.setMaximum(total_files * 100)
        self.process_button.setEnabled(False)
        self.select_button.setEnabled(False)
        
        current_file_index = 0
        for file_path in self.file_handler.queued_files:
            # Debug print for each file
            print(f"Processing file: {file_path}")
            
            file_name = Path(file_path).name
            self.status_label.setText(f"Converting {file_name}...")
            
            def update_progress(progress: float):
                total_progress = (current_file_index * 100) + progress
                self.progress_bar.setValue(int(total_progress))
                self.status_label.setText(f"Converting {file_name}: {progress:.1f}%")
                # Force the UI to update
                QApplication.processEvents()
            
            try:
                success, result = self.audio_converter.convert_video_to_audio(
                    str(file_path), 
                    progress_callback=update_progress
                )
                
                if success:
                    print(f"Successfully converted {file_name}")
                    self.status_label.setText(f"Successfully converted {file_name}")
                else:
                    print(f"Error converting {file_name}: {result}")
                    self.status_label.setText(f"Error converting {file_name}: {result}")
            except Exception as e:
                print(f"Exception during conversion: {str(e)}")
                self.status_label.setText(f"Error: {str(e)}")
            
            current_file_index += 1
        
        # Re-enable buttons after processing
        self.process_button.setEnabled(True)
        self.select_button.setEnabled(True)
        self.status_label.setText("All conversions completed")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()