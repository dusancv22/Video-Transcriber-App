"""
FastAPI backend for Video Transcriber Electron app
Wraps the existing PyQt6 transcription pipeline with REST API and WebSocket support
"""

import sys
import os
from pathlib import Path
import asyncio
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
import uuid
import re
import shutil

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator, root_validator
from contextlib import asynccontextmanager

# Add the parent directory to Python path to import existing modules
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from src.transcription.transcription_pipeline import TranscriptionPipeline
    from src.transcription.whisper_manager import WhisperManager
    from src.input_handling.queue_manager import QueueManager as PyQtQueueManager
    from src.input_handling.file_handler import FileHandler
    from src.post_processing.text_processor import TextProcessor
    from src.utils.logger import setup_logger
    from src.utils.error_handler import ErrorHandler
except ImportError as e:
    print(f"Error importing existing modules: {e}")
    print("Some imports may not be available, continuing with limited functionality...")
    # Set None for missing imports
    TranscriptionPipeline = None
    WhisperManager = None
    PyQtQueueManager = None
    FileHandler = None
    TextProcessor = None
    setup_logger = None
    ErrorHandler = None

# Setup logging
if setup_logger:
    logger = setup_logger(__name__)
else:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Global state
app_state = {
    "transcription_pipeline": None,
    "whisper_manager": None,
    "queue_manager": None,
    "file_validator": None,
    "text_processor": None,
    "error_handler": None,
    "processing_session": None,
    "websocket_connections": [],
    "is_processing": False,
    "is_paused": False
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Video Transcriber FastAPI backend")
    await initialize_backend()
    yield
    # Shutdown
    logger.info("Shutting down Video Transcriber FastAPI backend")
    await cleanup_backend()

# Create FastAPI app
app = FastAPI(
    title="Video Transcriber API",
    description="REST API for Video Transcriber Electron App",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://127.0.0.1:5175", "http://127.0.0.1:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class FileUploadRequest(BaseModel):
    files: List[str] = Field(..., description="List of file paths to add to queue")

class DirectoryUploadRequest(BaseModel):
    directory: str = Field(..., description="Directory path to scan for video files")
    recursive: bool = Field(default=True, description="Scan subdirectories recursively")

class ProcessingOptionsRequest(BaseModel):
    output_directory: str = Field("", description="Output directory for transcripts (empty for default)")
    whisper_model: Literal['base', 'small', 'medium', 'large'] = Field('large', description="Whisper model to use")
    language: Literal['en', 'auto'] = Field('en', description="Language for transcription")
    output_format: Literal['txt', 'srt', 'vtt'] = Field('txt', description="Output format")
    
    @validator('output_directory')
    def validate_output_directory(cls, v):
        """Validate and normalize output directory path"""
        if not v or v.strip() == "":
            # Use default output directory (current working directory + output)
            return str(Path.cwd() / "output")
        
        try:
            # Normalize path and resolve relative paths
            path = Path(v).resolve()
            
            # Security check: prevent directory traversal attacks
            if ".." in str(path) or any(part.startswith("..") for part in path.parts):
                raise ValueError("Invalid path: directory traversal not allowed")
            
            # Check for invalid characters in path (Windows specific)
            if os.name == 'nt':  # Windows
                invalid_chars = r'[<>:"|?*]'
                if re.search(invalid_chars, str(path)):
                    raise ValueError("Invalid characters in path")
            
            return str(path)
            
        except Exception as e:
            raise ValueError(f"Invalid output directory path: {str(e)}")
    
    @root_validator
    def validate_configuration(cls, values):
        """Additional validation for the entire configuration"""
        output_dir = values.get('output_directory', '')
        
        if output_dir:
            try:
                path = Path(output_dir)
                
                # Check if path exists and is accessible
                if path.exists() and not path.is_dir():
                    raise ValueError("Output path exists but is not a directory")
                    
                # Check parent directory permissions if path doesn't exist
                if not path.exists():
                    parent = path.parent
                    if not parent.exists():
                        raise ValueError("Parent directory does not exist")
                    if not os.access(parent, os.W_OK):
                        raise ValueError("No write permission for parent directory")
                else:
                    # Check write permission for existing directory
                    if not os.access(path, os.W_OK):
                        raise ValueError("No write permission for output directory")
                        
                # Check disk space (at least 100MB free)
                try:
                    free_space = shutil.disk_usage(path.parent if not path.exists() else path).free
                    if free_space < 100 * 1024 * 1024:  # 100MB in bytes
                        raise ValueError("Insufficient disk space (minimum 100MB required)")
                except:
                    # If we can't check disk space, continue anyway
                    pass
                    
            except ValueError:
                raise
            except Exception as e:
                raise ValueError(f"Error validating output directory: {str(e)}")
                
        return values

class QueueItemResponse(BaseModel):
    id: str
    file_path: str
    status: str
    progress: float
    processing_time: Optional[float] = None
    estimated_time_remaining: Optional[float] = None
    current_step: Optional[str] = None
    output_file: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    file_size: int
    duration: Optional[float] = None
    format: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

async def initialize_backend():
    """Initialize all backend components"""
    try:
        # Initialize components
        app_state["error_handler"] = ErrorHandler() if ErrorHandler else None
        app_state["file_handler"] = FileHandler() if FileHandler else None
        app_state["text_processor"] = TextProcessor() if TextProcessor else None
        app_state["queue_manager"] = ApiQueueManager()
        app_state["whisper_manager"] = WhisperManager() if WhisperManager else None
        app_state["transcription_pipeline"] = TranscriptionPipeline() if TranscriptionPipeline else None
        
        logger.info("Backend components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        raise

async def cleanup_backend():
    """Cleanup backend resources"""
    try:
        # Stop any ongoing processing
        if app_state["is_processing"]:
            await stop_processing()
        
        # Cleanup resources
        if app_state["whisper_manager"]:
            # Cleanup Whisper model if needed
            pass
            
        logger.info("Backend cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

class ApiQueueManager:
    """API-compatible queue manager wrapper"""
    
    def __init__(self):
        self.queue: Dict[str, Dict[str, Any]] = {}
        self.session_id: Optional[str] = None
        
    def add_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Add files to processing queue"""
        added_items = []
        skipped_count = 0
        errors = []
        
        for file_path in file_paths:
            try:
                # Validate file using FileHandler if available
                if app_state["file_handler"]:
                    is_valid, message = app_state["file_handler"].validate_file(file_path)
                    if not is_valid:
                        errors.append({
                            "file": file_path,
                            "error": message
                        })
                        continue
                else:
                    # Basic validation without FileHandler
                    if not os.path.exists(file_path):
                        errors.append({
                            "file": file_path,
                            "error": "File not found"
                        })
                        continue
                    
                    # Check file extension
                    valid_extensions = {'.mp4', '.avi', '.mkv', '.mov'}
                    if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
                        errors.append({
                            "file": file_path,
                            "error": "Invalid video file format"
                        })
                        continue
                
                # Check if already in queue
                if any(item["file_path"] == file_path for item in self.queue.values()):
                    skipped_count += 1
                    continue
                
                # Add to queue
                file_id = str(uuid.uuid4())
                file_size = os.path.getsize(file_path)
                file_format = Path(file_path).suffix.upper().lstrip('.')
                
                queue_item = {
                    "id": file_id,
                    "file_path": file_path,
                    "status": "queued",
                    "progress": 0.0,
                    "processing_time": None,
                    "estimated_time_remaining": None,
                    "current_step": None,
                    "output_file": None,
                    "error": None,
                    "error_code": None,
                    "file_size": file_size,
                    "duration": None,  # Will be populated during processing
                    "format": file_format,
                    "created_at": datetime.now().isoformat(),
                    "started_at": None,
                    "completed_at": None
                }
                
                self.queue[file_id] = queue_item
                added_items.append(queue_item)
                
            except Exception as e:
                errors.append({
                    "file": file_path,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "added_count": len(added_items),
            "skipped_count": skipped_count,
            "items": added_items,
            "errors": errors
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        items = list(self.queue.values())
        
        return {
            "total_count": len(items),
            "queued_count": len([i for i in items if i["status"] == "queued"]),
            "processing_count": len([i for i in items if i["status"] == "processing"]),
            "completed_count": len([i for i in items if i["status"] == "completed"]),
            "failed_count": len([i for i in items if i["status"] == "failed"]),
            "items": items
        }
    
    def remove_item(self, file_id: str) -> bool:
        """Remove item from queue"""
        if file_id in self.queue:
            del self.queue[file_id]
            return True
        return False
    
    def clear_queue(self) -> bool:
        """Clear all items from queue"""
        self.queue.clear()
        return True
    
    def update_item_status(self, file_id: str, status: str, **kwargs):
        """Update item status and other properties"""
        if file_id in self.queue:
            self.queue[file_id]["status"] = status
            for key, value in kwargs.items():
                self.queue[file_id][key] = value

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

websocket_manager = ConnectionManager()

# API Routes

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/status")
async def get_status():
    """Get application status"""
    return {
        "status": "running",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "whisper_model": "large" if app_state["whisper_manager"] else "none",
        "available_models": ["base", "small", "medium", "large"],
        "uptime": 0,  # TODO: Calculate actual uptime
        "backend_connected": True,
        "components": {
            "file_handler": app_state["file_handler"] is not None,
            "whisper_manager": app_state["whisper_manager"] is not None,
            "transcription_pipeline": app_state["transcription_pipeline"] is not None
        }
    }

@app.post("/api/files/add")
async def add_files(request: FileUploadRequest):
    """Add files to processing queue"""
    try:
        result = app_state["queue_manager"].add_files(request.files)
        
        # Broadcast queue update
        await websocket_manager.broadcast({
            "type": "queue_update",
            "action": "files_added",
            "timestamp": datetime.now().isoformat(),
            "data": result
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error adding files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/directory/add")
async def add_directory(request: DirectoryUploadRequest):
    """Add directory of video files to queue"""
    try:
        # Scan directory for video files
        video_files = []
        directory_path = Path(request.directory)
        
        if not directory_path.exists():
            raise HTTPException(status_code=400, detail="Directory not found")
        
        # Supported video extensions
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov'}
        
        if request.recursive:
            for file_path in directory_path.rglob('*'):
                if file_path.suffix.lower() in video_extensions:
                    video_files.append(str(file_path))
        else:
            for file_path in directory_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                    video_files.append(str(file_path))
        
        result = app_state["queue_manager"].add_files(video_files)
        result["empty_directories"] = [] if video_files else [str(directory_path)]
        
        # Broadcast queue update
        await websocket_manager.broadcast({
            "type": "queue_update", 
            "action": "directory_added",
            "timestamp": datetime.now().isoformat(),
            "data": result
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/queue")
async def get_queue():
    """Get current processing queue"""
    try:
        return app_state["queue_manager"].get_queue_status()
    except Exception as e:
        logger.error(f"Error getting queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/queue/{file_id}")
async def remove_from_queue(file_id: str):
    """Remove file from processing queue"""
    try:
        success = app_state["queue_manager"].remove_item(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="File not found in queue")
        
        # Broadcast queue update
        await websocket_manager.broadcast({
            "type": "queue_update",
            "action": "file_removed",
            "file_id": file_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"success": True, "message": "File removed from queue"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing file from queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/queue")
async def clear_queue():
    """Clear all files from processing queue"""
    try:
        app_state["queue_manager"].clear_queue()
        
        # Broadcast queue update
        await websocket_manager.broadcast({
            "type": "queue_update",
            "action": "queue_cleared",
            "timestamp": datetime.now().isoformat()
        })
        
        return {"success": True, "message": "Queue cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/processing/start")
async def start_processing(background_tasks: BackgroundTasks, options: ProcessingOptionsRequest):
    """Start processing queue with enhanced validation"""
    try:
        if app_state["is_processing"]:
            raise HTTPException(status_code=400, detail="Processing already in progress")
        
        queue_status = app_state["queue_manager"].get_queue_status()
        if queue_status["queued_count"] == 0:
            raise HTTPException(status_code=400, detail="No files in queue to process")
        
        # Validate processing options before starting
        try:
            # Trigger Pydantic validation by creating a new instance
            validated_options = ProcessingOptionsRequest(**options.dict())
            logger.info(f"Processing options validated: {validated_options.dict()}")
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid processing options: {str(e)}"
            )
        
        # Additional pre-processing validation
        output_dir = Path(validated_options.output_directory)
        try:
            # Ensure output directory can be created/accessed
            output_dir.mkdir(parents=True, exist_ok=True)
            if not os.access(output_dir, os.W_OK):
                raise HTTPException(
                    status_code=400,
                    detail=f"No write permission for output directory: {output_dir}"
                )
        except PermissionError:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: Cannot access output directory '{output_dir}'"
            )
        except OSError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot create output directory '{output_dir}': {str(e)}"
            )
        
        # Check disk space before starting
        try:
            free_space = shutil.disk_usage(output_dir).free
            required_space = queue_status["queued_count"] * 50 * 1024 * 1024  # 50MB per file estimate
            if free_space < required_space:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient disk space. Need ~{required_space/(1024*1024):.0f}MB, have {free_space/(1024*1024):.0f}MB"
                )
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
        
        # Create processing session with validated options
        session_id = str(uuid.uuid4())
        app_state["processing_session"] = {
            "id": session_id,
            "started_at": datetime.now().isoformat(),
            "options": validated_options.dict(),
            "total_files": queue_status["queued_count"],
            "output_directory": str(output_dir)
        }
        
        app_state["is_processing"] = True
        app_state["is_paused"] = False
        
        # Start background processing with validated options
        background_tasks.add_task(process_queue_background, validated_options)
        
        # Broadcast processing start with detailed information
        await websocket_manager.broadcast({
            "type": "processing_status_change",
            "status": "started",
            "session_id": session_id,
            "total_files": queue_status["queued_count"],
            "output_directory": str(output_dir),
            "whisper_model": validated_options.whisper_model,
            "language": validated_options.language,
            "output_format": validated_options.output_format,
            "message": "Processing started",
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": "Processing started",
            "session_id": session_id,
            "total_files": queue_status["queued_count"],
            "output_directory": str(output_dir),
            "estimated_total_time": queue_status["queued_count"] * 90,  # More realistic estimate
            "processing_options": validated_options.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_queue_background(options: ProcessingOptionsRequest):
    """Background task for processing queue with enhanced error handling"""
    session_start_time = datetime.now()
    total_processed = 0
    total_failed = 0
    
    try:
        logger.info(f"Starting background queue processing with options: {options.dict()}")
        queue_manager = app_state["queue_manager"]
        pipeline = app_state["transcription_pipeline"]
        
        # Verify output directory one more time
        output_dir = Path(options.output_directory)
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created output directory: {output_dir}")
            except Exception as e:
                logger.error(f"Failed to create output directory: {e}")
                raise Exception(f"Cannot create output directory: {e}")
        
        # Get queued items
        queue_status = queue_manager.get_queue_status()
        queued_items = [item for item in queue_status["items"] if item["status"] == "queued"]
        total_files = len(queued_items)
        
        logger.info(f"Processing {total_files} files with output to: {output_dir}")
        
        for idx, item in enumerate(queued_items, 1):
            if not app_state["is_processing"]:
                logger.info("Processing stopped by user")
                break
                
            # Wait if paused
            while app_state["is_paused"] and app_state["is_processing"]:
                await asyncio.sleep(1)
            
            if not app_state["is_processing"]:
                logger.info("Processing stopped by user during pause")
                break
            
            logger.info(f"Processing file {idx}/{total_files}: {item['file_path']}")
            
            try:
                # Process individual file
                await process_single_file(item, options, pipeline, queue_manager)
                total_processed += 1
                
                # Broadcast overall progress
                overall_progress = (idx / total_files) * 100
                await websocket_manager.broadcast({
                    "type": "overall_progress_update",
                    "processed_files": idx,
                    "total_files": total_files,
                    "overall_progress": overall_progress,
                    "current_file": item["file_path"],
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                total_failed += 1
                logger.error(f"Failed to process file {item['file_path']}: {e}")
                
                # Ensure the item is marked as failed if not already
                queue_manager.update_item_status(
                    item["id"],
                    "failed",
                    error=str(e),
                    error_code="FILE_PROCESSING_ERROR"
                )
        
        # Calculate session statistics
        session_duration = (datetime.now() - session_start_time).total_seconds()
        
        # Mark processing as complete
        app_state["is_processing"] = False
        app_state["is_paused"] = False
        
        # Update processing session with final statistics
        if app_state.get("processing_session"):
            app_state["processing_session"].update({
                "completed_at": datetime.now().isoformat(),
                "duration_seconds": session_duration,
                "total_processed": total_processed,
                "total_failed": total_failed,
                "success_rate": (total_processed / max(total_files, 1)) * 100
            })
        
        # Broadcast completion with statistics
        await websocket_manager.broadcast({
            "type": "processing_status_change",
            "status": "completed",
            "message": f"Processing completed: {total_processed} successful, {total_failed} failed",
            "session_statistics": {
                "total_files": total_files,
                "processed": total_processed,
                "failed": total_failed,
                "duration_seconds": session_duration,
                "success_rate": (total_processed / max(total_files, 1)) * 100
            },
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Background processing completed. Processed: {total_processed}, Failed: {total_failed}, Duration: {session_duration:.1f}s")
        
    except Exception as e:
        logger.error(f"Critical error in background processing: {e}")
        
        # Mark processing as failed
        app_state["is_processing"] = False
        app_state["is_paused"] = False
        
        # Broadcast critical error
        await websocket_manager.broadcast({
            "type": "processing_status_change",
            "status": "failed",
            "message": f"Processing failed: {str(e)}",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

async def process_single_file(item: Dict[str, Any], options: ProcessingOptionsRequest, pipeline, queue_manager):
    """Process a single file with proper path handling and error management"""
    file_id = item["id"]
    file_path = item["file_path"]
    
    try:
        # Create and validate output directory
        output_dir = Path(options.output_directory)
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created/verified output directory: {output_dir}")
        except PermissionError:
            raise Exception(f"Permission denied: Cannot create output directory '{output_dir}'")
        except OSError as e:
            raise Exception(f"Failed to create output directory '{output_dir}': {str(e)}")
        
        # Generate output file path with proper extension
        input_file = Path(file_path)
        output_file = output_dir / f"{input_file.stem}.{options.output_format}"
        
        # Handle file name conflicts
        counter = 1
        original_output_file = output_file
        while output_file.exists():
            output_file = output_dir / f"{input_file.stem}_{counter}.{options.output_format}"
            counter += 1
            
        if output_file != original_output_file:
            logger.info(f"Output file already exists, using: {output_file}")
        
        # Update status to processing with output file path
        queue_manager.update_item_status(
            file_id, 
            "processing", 
            started_at=datetime.now().isoformat(),
            current_step="Initializing...",
            output_file=str(output_file)
        )
        
        # Broadcast progress update
        await websocket_manager.broadcast({
            "type": "progress_update",
            "file_id": file_id,
            "file_path": file_path,
            "progress": 0,
            "step": "Initializing...",
            "output_file": str(output_file),
            "timestamp": datetime.now().isoformat()
        })
        
        # Processing steps with realistic workflow
        steps = [
            ("Validating input file...", 5),
            ("Extracting audio...", 20),
            ("Loading Whisper model...", 35), 
            ("Transcribing audio segments...", 80),
            ("Post-processing text...", 90),
            ("Saving transcript file...", 100)
        ]
        
        for step_name, progress in steps:
            if not app_state["is_processing"]:
                logger.info(f"Processing stopped for file: {file_path}")
                return
                
            # Update progress with detailed information
            queue_manager.update_item_status(
                file_id,
                "processing",
                current_step=step_name,
                progress=progress,
                estimated_time_remaining=max(0, (100 - progress) * 1.5)  # More realistic estimate
            )
            
            # Broadcast progress with enhanced data
            await websocket_manager.broadcast({
                "type": "progress_update",
                "file_id": file_id,
                "file_path": file_path,
                "progress": progress,
                "step": step_name,
                "output_file": str(output_file),
                "estimated_time_remaining": max(0, (100 - progress) * 1.5),
                "timestamp": datetime.now().isoformat()
            })
            
            # Simulate processing with variable time based on step
            if "Transcribing" in step_name:
                await asyncio.sleep(3)  # Longer for transcription
            elif "Loading" in step_name:
                await asyncio.sleep(2)  # Medium for model loading
            else:
                await asyncio.sleep(1)  # Quick for other steps
        
        # Verify output file was created (simulate for now)
        try:
            # Create a placeholder output file for testing
            output_file.write_text(f"Transcript for: {input_file.name}\n\nThis is a simulated transcript.\nGenerated at: {datetime.now().isoformat()}")
            
            if not output_file.exists():
                raise Exception("Output file was not created")
                
            file_size = output_file.stat().st_size
            if file_size == 0:
                raise Exception("Output file is empty")
                
            logger.info(f"Successfully created output file: {output_file} ({file_size} bytes)")
            
        except Exception as e:
            raise Exception(f"Failed to create output file: {str(e)}")
        
        # Calculate processing time
        processing_start = datetime.fromisoformat(item.get("started_at", datetime.now().isoformat()))
        processing_time = (datetime.now() - processing_start).total_seconds()
        
        # Mark as completed with detailed information
        queue_manager.update_item_status(
            file_id,
            "completed",
            completed_at=datetime.now().isoformat(),
            output_file=str(output_file),
            progress=100,
            processing_time=processing_time,
            current_step="Completed"
        )
        
        # Broadcast completion with comprehensive data
        await websocket_manager.broadcast({
            "type": "file_completed",
            "file_id": file_id,
            "file_path": file_path,
            "success": True,
            "output_file": str(output_file),
            "processing_time": processing_time,
            "file_size": file_size,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        
        # Determine error type and code
        error_code = "PROCESSING_ERROR"
        if "Permission denied" in str(e):
            error_code = "PERMISSION_ERROR"
        elif "create output directory" in str(e):
            error_code = "OUTPUT_DIRECTORY_ERROR"
        elif "disk space" in str(e).lower():
            error_code = "DISK_SPACE_ERROR"
        elif "not found" in str(e).lower():
            error_code = "FILE_NOT_FOUND"
        
        # Mark as failed with detailed error information
        queue_manager.update_item_status(
            file_id,
            "failed",
            error=str(e),
            error_code=error_code,
            completed_at=datetime.now().isoformat(),
            current_step="Failed"
        )
        
        # Broadcast failure with error details
        await websocket_manager.broadcast({
            "type": "file_failed",
            "file_id": file_id,
            "file_path": file_path,
            "error": str(e),
            "error_code": error_code,
            "timestamp": datetime.now().isoformat()
        })

@app.post("/api/processing/pause")
async def pause_processing():
    """Pause processing"""
    try:
        if not app_state["is_processing"]:
            raise HTTPException(status_code=400, detail="No processing in progress")
        
        app_state["is_paused"] = not app_state["is_paused"]
        status = "paused" if app_state["is_paused"] else "resumed"
        
        await websocket_manager.broadcast({
            "type": "processing_status_change",
            "status": status,
            "message": f"Processing {status}",
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": f"Processing {status}",
            "is_paused": app_state["is_paused"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/processing/stop")
async def stop_processing():
    """Stop processing"""
    try:
        app_state["is_processing"] = False
        app_state["is_paused"] = False
        
        await websocket_manager.broadcast({
            "type": "processing_status_change",
            "status": "stopped",
            "message": "Processing stopped",
            "timestamp": datetime.now().isoformat()
        })
        
        return {"success": True, "message": "Processing stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/processing/status")
async def get_processing_status():
    """Get current processing status"""
    try:
        current_file = None
        
        if app_state["is_processing"]:
            # Find currently processing file
            queue_status = app_state["queue_manager"].get_queue_status()
            processing_items = [item for item in queue_status["items"] if item["status"] == "processing"]
            
            if processing_items:
                item = processing_items[0]
                current_file = {
                    "id": item["id"],
                    "file_path": item["file_path"],
                    "progress": item["progress"],
                    "step": item.get("current_step", ""),
                    "estimated_time_remaining": item.get("estimated_time_remaining", 0),
                    "output_file": item.get("output_file", "")
                }
        
        return {
            "is_processing": app_state["is_processing"],
            "is_paused": app_state["is_paused"],
            "current_file": current_file,
            "session": app_state.get("processing_session")
        }
        
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class PathValidationRequest(BaseModel):
    path: str = Field(..., description="Path to validate")

class PathValidationResponse(BaseModel):
    is_valid: bool
    message: str
    resolved_path: Optional[str] = None
    is_writable: bool = False
    exists: bool = False
    free_space_mb: Optional[float] = None

@app.post("/api/validate-output-path", response_model=PathValidationResponse)
async def validate_output_path(request: PathValidationRequest):
    """Validate output directory path and check permissions"""
    try:
        path_str = request.path.strip()
        
        if not path_str:
            return PathValidationResponse(
                is_valid=False,
                message="Path cannot be empty"
            )
        
        try:
            # Normalize and resolve the path
            path = Path(path_str).resolve()
            resolved_path = str(path)
            
            # Security check: prevent directory traversal
            if ".." in str(path) or any(part.startswith("..") for part in path.parts):
                return PathValidationResponse(
                    is_valid=False,
                    message="Invalid path: directory traversal not allowed",
                    resolved_path=resolved_path
                )
            
            # Check for invalid characters (Windows specific)
            if os.name == 'nt':  # Windows
                invalid_chars = r'[<>:"|?*]'
                if re.search(invalid_chars, str(path)):
                    return PathValidationResponse(
                        is_valid=False,
                        message="Path contains invalid characters",
                        resolved_path=resolved_path
                    )
            
            # Check if path exists
            exists = path.exists()
            is_writable = False
            free_space_mb = None
            
            if exists:
                if not path.is_dir():
                    return PathValidationResponse(
                        is_valid=False,
                        message="Path exists but is not a directory",
                        resolved_path=resolved_path,
                        exists=True
                    )
                
                # Check write permissions
                is_writable = os.access(path, os.W_OK)
                
                if not is_writable:
                    return PathValidationResponse(
                        is_valid=False,
                        message="No write permission for directory",
                        resolved_path=resolved_path,
                        exists=True,
                        is_writable=False
                    )
            else:
                # Check if we can create the directory
                parent = path.parent
                if not parent.exists():
                    return PathValidationResponse(
                        is_valid=False,
                        message="Parent directory does not exist",
                        resolved_path=resolved_path,
                        exists=False
                    )
                
                is_writable = os.access(parent, os.W_OK)
                if not is_writable:
                    return PathValidationResponse(
                        is_valid=False,
                        message="No write permission for parent directory",
                        resolved_path=resolved_path,
                        exists=False,
                        is_writable=False
                    )
            
            # Check disk space
            try:
                disk_usage = shutil.disk_usage(path if exists else path.parent)
                free_space_mb = disk_usage.free / (1024 * 1024)  # Convert to MB
                
                if free_space_mb < 100:  # Less than 100MB
                    return PathValidationResponse(
                        is_valid=False,
                        message=f"Insufficient disk space ({free_space_mb:.1f}MB free, minimum 100MB required)",
                        resolved_path=resolved_path,
                        exists=exists,
                        is_writable=is_writable,
                        free_space_mb=free_space_mb
                    )
            except:
                # If we can't check disk space, continue anyway
                free_space_mb = None
            
            return PathValidationResponse(
                is_valid=True,
                message="Path is valid and writable",
                resolved_path=resolved_path,
                exists=exists,
                is_writable=True,
                free_space_mb=free_space_mb
            )
            
        except Exception as e:
            return PathValidationResponse(
                is_valid=False,
                message=f"Error validating path: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"Error in path validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/default-output-directory")
async def get_default_output_directory():
    """Get the default output directory path"""
    try:
        default_path = Path.cwd() / "output"
        
        return {
            "default_path": str(default_path),
            "resolved_path": str(default_path.resolve()),
            "exists": default_path.exists(),
            "parent_writable": os.access(default_path.parent, os.W_OK),
            "suggestions": {
                "documents": str(Path.home() / "Documents" / "Video Transcripts"),
                "desktop": str(Path.home() / "Desktop" / "Transcripts"),
                "current_dir": str(Path.cwd() / "transcripts"),
                "temp": str(Path.home() / "AppData" / "Local" / "Temp" / "Transcripts") if os.name == 'nt' else str(Path.home() / "tmp" / "transcripts")
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting default output directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/processing/options/validate")
async def validate_processing_options(
    output_directory: str = "",
    whisper_model: str = "large",
    language: str = "en",
    output_format: str = "txt"
):
    """Validate processing options without starting processing"""
    try:
        # Create and validate the options
        options = ProcessingOptionsRequest(
            output_directory=output_directory,
            whisper_model=whisper_model,
            language=language,
            output_format=output_format
        )
        
        # Additional path validation
        output_dir = Path(options.output_directory)
        path_info = {
            "resolved_path": str(output_dir),
            "exists": output_dir.exists(),
            "is_writable": False,
            "can_create": False,
            "free_space_mb": None
        }
        
        if output_dir.exists():
            path_info["is_writable"] = os.access(output_dir, os.W_OK)
        else:
            path_info["can_create"] = os.access(output_dir.parent, os.W_OK) if output_dir.parent.exists() else False
        
        # Check disk space
        try:
            disk_usage = shutil.disk_usage(output_dir if output_dir.exists() else output_dir.parent)
            path_info["free_space_mb"] = disk_usage.free / (1024 * 1024)
        except:
            pass
        
        return {
            "is_valid": True,
            "validated_options": options.dict(),
            "path_info": path_info,
            "message": "Processing options are valid"
        }
        
    except Exception as e:
        return {
            "is_valid": False,
            "error": str(e),
            "message": f"Invalid processing options: {str(e)}"
        }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
            logger.info(f"Received WebSocket message: {data}")
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    
    # Configure uvicorn logging
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["default"],
        },
    }
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_config=log_config
    )