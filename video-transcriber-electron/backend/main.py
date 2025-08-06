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
from typing import Optional, List, Dict, Any
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
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
    output_directory: str = Field(..., description="Output directory for transcripts")
    whisper_model: Optional[str] = Field("large", description="Whisper model to use")
    language: Optional[str] = Field("en", description="Language for transcription")
    output_format: Optional[str] = Field("txt", description="Output format (txt, srt, vtt)")

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
                if key in self.queue[file_id]:
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
    """Start processing queue"""
    try:
        if app_state["is_processing"]:
            raise HTTPException(status_code=400, detail="Processing already in progress")
        
        queue_status = app_state["queue_manager"].get_queue_status()
        if queue_status["queued_count"] == 0:
            raise HTTPException(status_code=400, detail="No files in queue to process")
        
        # Create processing session
        session_id = str(uuid.uuid4())
        app_state["processing_session"] = {
            "id": session_id,
            "started_at": datetime.now().isoformat(),
            "options": options.dict(),
            "total_files": queue_status["queued_count"]
        }
        
        app_state["is_processing"] = True
        app_state["is_paused"] = False
        
        # Start background processing
        background_tasks.add_task(process_queue_background, options)
        
        # Broadcast processing start
        await websocket_manager.broadcast({
            "type": "processing_status_change",
            "status": "started",
            "session_id": session_id,
            "total_files": queue_status["queued_count"],
            "message": "Processing started",
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": "Processing started",
            "session_id": session_id,
            "total_files": queue_status["queued_count"],
            "estimated_total_time": queue_status["queued_count"] * 120  # Rough estimate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_queue_background(options: ProcessingOptionsRequest):
    """Background task for processing queue"""
    try:
        logger.info("Starting background queue processing")
        queue_manager = app_state["queue_manager"]
        pipeline = app_state["transcription_pipeline"]
        
        # Get queued items
        queue_status = queue_manager.get_queue_status()
        queued_items = [item for item in queue_status["items"] if item["status"] == "queued"]
        
        for item in queued_items:
            if not app_state["is_processing"]:
                break
                
            # Wait if paused
            while app_state["is_paused"] and app_state["is_processing"]:
                await asyncio.sleep(1)
            
            if not app_state["is_processing"]:
                break
            
            # Process file
            await process_single_file(item, options, pipeline, queue_manager)
        
        # Mark processing as complete
        app_state["is_processing"] = False
        app_state["is_paused"] = False
        
        # Broadcast completion
        await websocket_manager.broadcast({
            "type": "processing_status_change",
            "status": "completed",
            "message": "All files processed",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in background processing: {e}")
        app_state["is_processing"] = False
        app_state["is_paused"] = False

async def process_single_file(item: Dict[str, Any], options: ProcessingOptionsRequest, pipeline, queue_manager):
    """Process a single file"""
    file_id = item["id"]
    file_path = item["file_path"]
    
    try:
        # Update status to processing
        queue_manager.update_item_status(
            file_id, 
            "processing", 
            started_at=datetime.now().isoformat(),
            current_step="Initializing..."
        )
        
        # Broadcast progress update
        await websocket_manager.broadcast({
            "type": "progress_update",
            "file_id": file_id,
            "file_path": file_path,
            "progress": 0,
            "step": "Initializing...",
            "timestamp": datetime.now().isoformat()
        })
        
        # TODO: Integrate with actual transcription pipeline
        # For now, simulate processing with progress updates
        steps = [
            ("Extracting audio...", 20),
            ("Loading AI model...", 40), 
            ("Transcribing segments...", 80),
            ("Post-processing text...", 95),
            ("Saving transcript...", 100)
        ]
        
        for step_name, progress in steps:
            if not app_state["is_processing"]:
                return
                
            # Update progress
            queue_manager.update_item_status(
                file_id,
                "processing",
                current_step=step_name,
                progress=progress
            )
            
            # Broadcast progress
            await websocket_manager.broadcast({
                "type": "progress_update",
                "file_id": file_id,
                "file_path": file_path,
                "progress": progress,
                "step": step_name,
                "estimated_time_remaining": max(0, (100 - progress) * 2),  # Rough estimate
                "timestamp": datetime.now().isoformat()
            })
            
            # Simulate processing time
            await asyncio.sleep(2)
        
        # Mark as completed
        output_file = os.path.join(options.output_directory, Path(file_path).stem + ".txt")
        queue_manager.update_item_status(
            file_id,
            "completed",
            completed_at=datetime.now().isoformat(),
            output_file=output_file,
            progress=100
        )
        
        # Broadcast completion
        await websocket_manager.broadcast({
            "type": "file_completed",
            "file_id": file_id,
            "file_path": file_path,
            "success": True,
            "output_file": output_file,
            "processing_time": 10,  # Simulated
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        
        # Mark as failed
        queue_manager.update_item_status(
            file_id,
            "failed",
            error=str(e),
            error_code="PROCESSING_ERROR"
        )
        
        # Broadcast failure
        await websocket_manager.broadcast({
            "type": "file_failed",
            "file_id": file_id,
            "file_path": file_path,
            "error": str(e),
            "error_code": "PROCESSING_ERROR",
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
                    "estimated_time_remaining": item.get("estimated_time_remaining", 0)
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