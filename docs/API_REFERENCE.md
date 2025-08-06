# 📡 Video Transcriber App - API Reference

## Overview

The Video Transcriber App provides a comprehensive REST API with WebSocket support for real-time updates. The API is built with FastAPI and includes comprehensive validation, security features, and detailed error handling.

**Base URL:** `http://127.0.0.1:8000`
**WebSocket URL:** `ws://127.0.0.1:8000/ws`
**Interactive Documentation:** `http://127.0.0.1:8000/docs`

## 🔐 Authentication & Security

### Security Features
- **Path Validation**: All file paths validated against directory traversal attacks
- **Input Sanitization**: Comprehensive validation of all user inputs  
- **Permission Checking**: File system permissions verified before operations
- **Error Handling**: Secure error responses without information leakage

### Headers
```http
Content-Type: application/json
Accept: application/json
```

## 🏥 Health & Status Endpoints

### Health Check
```http
GET /health
```

Simple health check endpoint to verify service availability.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Application Status
```http
GET /api/status
```

Detailed application status including component health and system information.

**Response:**
```json
{
  "status": "running",
  "python_version": "3.10.12",
  "whisper_model": "large",
  "available_models": ["base", "small", "medium", "large"],
  "uptime": 3600,
  "backend_connected": true,
  "components": {
    "file_handler": true,
    "whisper_manager": true,
    "transcription_pipeline": true
  }
}
```

## 📁 File Management Endpoints

### Add Files to Queue
```http
POST /api/files/add
```

Add individual files to the processing queue with validation.

**Request Body:**
```json
{
  "files": [
    "C:/Videos/interview.mp4",
    "C:/Videos/lecture.avi",
    "C:/Videos/meeting.mkv"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "added_count": 2,
  "skipped_count": 1,
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "file_path": "C:/Videos/interview.mp4",
      "status": "queued",
      "progress": 0.0,
      "file_size": 25600000,
      "duration": null,
      "format": "MP4",
      "created_at": "2024-01-15T10:30:00.000Z"
    }
  ],
  "errors": [
    {
      "file": "C:/Videos/corrupt.mp4",
      "error": "File not accessible"
    }
  ]
}
```

**Error Responses:**
```json
// 400 Bad Request - Invalid input
{
  "detail": "No files provided"
}

// 500 Internal Server Error
{
  "detail": "File validation service unavailable"
}
```

### Add Directory to Queue
```http
POST /api/directory/add
```

Scan a directory for video files and add them to the queue.

**Request Body:**
```json
{
  "directory": "C:/Videos/Project",
  "recursive": true
}
```

**Response:**
```json
{
  "success": true,
  "added_count": 5,
  "skipped_count": 0,
  "empty_directories": [],
  "items": [
    // Array of queue items (same structure as add files)
  ],
  "errors": []
}
```

**Error Responses:**
```json
// 400 Bad Request - Directory not found
{
  "detail": "Directory not found"
}

// 403 Forbidden - No read permission
{
  "detail": "No read permission for directory"
}
```

## 🗃️ Queue Management Endpoints

### Get Queue Status
```http
GET /api/queue
```

Retrieve current queue status and all items.

**Response:**
```json
{
  "total_count": 10,
  "queued_count": 3,
  "processing_count": 1,
  "completed_count": 5,
  "failed_count": 1,
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "file_path": "C:/Videos/interview.mp4",
      "status": "processing",
      "progress": 45.5,
      "processing_time": 120.5,
      "estimated_time_remaining": 150.0,
      "current_step": "Transcribing audio segments...",
      "output_file": "C:/Output/interview.txt",
      "error": null,
      "error_code": null,
      "file_size": 25600000,
      "duration": 1800.0,
      "format": "MP4",
      "created_at": "2024-01-15T10:30:00.000Z",
      "started_at": "2024-01-15T10:35:00.000Z",
      "completed_at": null
    }
  ]
}
```

### Remove Item from Queue
```http
DELETE /api/queue/{file_id}
```

Remove a specific item from the processing queue.

**Path Parameters:**
- `file_id` (string): Unique identifier of the queue item

**Response:**
```json
{
  "success": true,
  "message": "File removed from queue"
}
```

**Error Responses:**
```json
// 404 Not Found
{
  "detail": "File not found in queue"
}
```

### Clear Queue
```http
DELETE /api/queue
```

Remove all items from the processing queue.

**Response:**
```json
{
  "success": true,
  "message": "Queue cleared"
}
```

## ⚙️ Processing Control Endpoints

### Start Processing
```http
POST /api/processing/start
```

Start processing the queue with specified options.

**Request Body:**
```json
{
  "output_directory": "C:/Output/Transcripts",
  "whisper_model": "large",
  "language": "en",
  "output_format": "txt"
}
```

**Field Validation:**

- **output_directory**: 
  - Must be valid directory path
  - Write permission required
  - Minimum 100MB free space
  - Protected against directory traversal

- **whisper_model**: 
  - Options: `"base"`, `"small"`, `"medium"`, `"large"`
  - Larger models = higher accuracy, slower processing

- **language**: 
  - Options: `"en"` (English only), `"auto"` (auto-detect)
  - English-only recommended for consistency

- **output_format**: 
  - Options: `"txt"`, `"srt"`, `"vtt"`
  - Determines transcript output format

**Response:**
```json
{
  "success": true,
  "message": "Processing started",
  "session_id": "session_550e8400-e29b-41d4-a716-446655440000",
  "total_files": 5,
  "output_directory": "C:/Output/Transcripts",
  "estimated_total_time": 450,
  "processing_options": {
    "output_directory": "C:/Output/Transcripts",
    "whisper_model": "large",
    "language": "en",
    "output_format": "txt"
  }
}
```

**Error Responses:**
```json
// 400 Bad Request - Already processing
{
  "detail": "Processing already in progress"
}

// 400 Bad Request - Empty queue
{
  "detail": "No files in queue to process"
}

// 400 Bad Request - Invalid options
{
  "detail": "Invalid processing options: Invalid output directory path"
}

// 403 Forbidden - Permission denied
{
  "detail": "Permission denied: Cannot access output directory '/restricted/path'"
}
```

### Pause/Resume Processing
```http
POST /api/processing/pause
```

Toggle pause/resume state of current processing.

**Response:**
```json
{
  "success": true,
  "message": "Processing paused",
  "is_paused": true
}
```

**Error Responses:**
```json
// 400 Bad Request
{
  "detail": "No processing in progress"
}
```

### Stop Processing
```http
POST /api/processing/stop
```

Stop all processing immediately.

**Response:**
```json
{
  "success": true,
  "message": "Processing stopped"
}
```

### Get Processing Status
```http
GET /api/processing/status
```

Get current processing status and details.

**Response:**
```json
{
  "is_processing": true,
  "is_paused": false,
  "current_file": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "file_path": "C:/Videos/interview.mp4",
    "progress": 67.5,
    "step": "Post-processing text...",
    "estimated_time_remaining": 45.0,
    "output_file": "C:/Output/interview.txt"
  },
  "session": {
    "id": "session_550e8400-e29b-41d4-a716-446655440000",
    "started_at": "2024-01-15T10:35:00.000Z",
    "options": {
      "output_directory": "C:/Output/Transcripts",
      "whisper_model": "large",
      "language": "en",
      "output_format": "txt"
    },
    "total_files": 5,
    "output_directory": "C:/Output/Transcripts"
  }
}
```

## 🛡️ Validation Endpoints

### Validate Output Path
```http
POST /api/validate-output-path
```

Validate an output directory path for security and accessibility.

**Request Body:**
```json
{
  "path": "C:/Output/MyTranscripts"
}
```

**Response:**
```json
{
  "is_valid": true,
  "message": "Path is valid and writable",
  "resolved_path": "C:\\Output\\MyTranscripts",
  "exists": false,
  "is_writable": true,
  "free_space_mb": 15360.5
}
```

**Error Response Examples:**
```json
// Invalid path
{
  "is_valid": false,
  "message": "Invalid path: directory traversal not allowed",
  "resolved_path": "C:\\Output\\..\\..\\Windows\\System32",
  "exists": false,
  "is_writable": false
}

// Insufficient permissions
{
  "is_valid": false,
  "message": "No write permission for directory",
  "resolved_path": "C:\\Windows\\System32",
  "exists": true,
  "is_writable": false
}

// Insufficient disk space
{
  "is_valid": false,
  "message": "Insufficient disk space (50.2MB free, minimum 100MB required)",
  "resolved_path": "D:\\Output",
  "exists": true,
  "is_writable": true,
  "free_space_mb": 50.2
}
```

### Get Default Output Directory
```http
GET /api/default-output-directory
```

Get default output directory and suggestions.

**Response:**
```json
{
  "default_path": "C:/video-transcriber-app/output",
  "resolved_path": "C:\\video-transcriber-app\\output",
  "exists": false,
  "parent_writable": true,
  "suggestions": {
    "documents": "C:/Users/UserName/Documents/Video Transcripts",
    "desktop": "C:/Users/UserName/Desktop/Transcripts",
    "current_dir": "C:/video-transcriber-app/transcripts",
    "temp": "C:/Users/UserName/AppData/Local/Temp/Transcripts"
  }
}
```

### Validate Processing Options
```http
GET /api/processing/options/validate?output_directory=C:/Output&whisper_model=large&language=en&output_format=txt
```

Validate processing options without starting processing.

**Query Parameters:**
- `output_directory` (string): Output directory path
- `whisper_model` (string): Whisper model size
- `language` (string): Language setting
- `output_format` (string): Output format

**Response:**
```json
{
  "is_valid": true,
  "validated_options": {
    "output_directory": "C:\\Output",
    "whisper_model": "large",
    "language": "en",
    "output_format": "txt"
  },
  "path_info": {
    "resolved_path": "C:\\Output",
    "exists": true,
    "is_writable": true,
    "can_create": false,
    "free_space_mb": 15360.5
  },
  "message": "Processing options are valid"
}
```

## 🔌 WebSocket Real-Time Updates

### Connection
```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/ws');

ws.onopen = (event) => {
  console.log('WebSocket connected');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  handleMessage(message);
};

ws.onclose = (event) => {
  console.log('WebSocket disconnected');
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

### Message Types

#### Queue Update
```json
{
  "type": "queue_update",
  "action": "files_added",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "data": {
    "added_count": 3,
    "items": [/* queue items */]
  }
}
```

#### Processing Status Change
```json
{
  "type": "processing_status_change",
  "status": "started",
  "session_id": "session_550e8400-e29b-41d4-a716-446655440000",
  "total_files": 5,
  "output_directory": "C:\\Output\\Transcripts",
  "whisper_model": "large",
  "language": "en",
  "output_format": "txt",
  "message": "Processing started",
  "timestamp": "2024-01-15T10:35:00.000Z"
}
```

#### Progress Update
```json
{
  "type": "progress_update",
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_path": "C:/Videos/interview.mp4",
  "progress": 45.5,
  "step": "Transcribing audio segments...",
  "output_file": "C:/Output/interview.txt",
  "estimated_time_remaining": 120.0,
  "timestamp": "2024-01-15T10:37:30.000Z"
}
```

#### Overall Progress Update
```json
{
  "type": "overall_progress_update",
  "processed_files": 3,
  "total_files": 5,
  "overall_progress": 60.0,
  "current_file": "C:/Videos/meeting.mp4",
  "timestamp": "2024-01-15T10:40:00.000Z"
}
```

#### File Completed
```json
{
  "type": "file_completed",
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_path": "C:/Videos/interview.mp4",
  "success": true,
  "output_file": "C:/Output/interview.txt",
  "processing_time": 180.5,
  "file_size": 2048,
  "timestamp": "2024-01-15T10:38:00.000Z"
}
```

#### File Failed
```json
{
  "type": "file_failed",
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_path": "C:/Videos/corrupt.mp4",
  "error": "Failed to extract audio from video file",
  "error_code": "AUDIO_EXTRACTION_ERROR",
  "timestamp": "2024-01-15T10:36:15.000Z"
}
```

## 📊 Data Models

### QueueItem
```typescript
interface QueueItem {
  id: string;                           // Unique identifier
  file_path: string;                    // Full path to video file
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;                     // 0-100 percentage
  processing_time?: number;             // Seconds taken to process
  estimated_time_remaining?: number;    // Estimated seconds remaining
  current_step?: string;               // Current processing step
  output_file?: string;                // Path to generated transcript
  error?: string;                      // Error message if failed
  error_code?: string;                 // Error code for programmatic handling
  file_size: number;                   // File size in bytes
  duration?: number;                   // Video duration in seconds
  format: string;                      // Video format (MP4, AVI, etc.)
  created_at: string;                  // ISO timestamp when added to queue
  started_at?: string;                 // ISO timestamp when processing started
  completed_at?: string;               // ISO timestamp when processing completed
}
```

### ProcessingOptions
```typescript
interface ProcessingOptions {
  output_directory: string;            // Output directory path
  whisper_model: 'base' | 'small' | 'medium' | 'large';
  language: 'en' | 'auto';            // Language processing option
  output_format: 'txt' | 'srt' | 'vtt';
}
```

### QueueStats
```typescript
interface QueueStats {
  total_count: number;                 // Total items in queue
  queued_count: number;               // Items waiting to be processed
  processing_count: number;           // Items currently being processed
  completed_count: number;            // Successfully completed items
  failed_count: number;               // Items that failed processing
}
```

## 🚨 Error Handling

### HTTP Status Codes

- **200 OK**: Successful operation
- **400 Bad Request**: Invalid input data or request
- **403 Forbidden**: Permission denied or access restricted
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

### Error Response Format
```json
{
  "detail": "Human readable error message",
  "error_code": "MACHINE_READABLE_ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "path": "/api/files/add",
  "suggestion": "Check file permissions and try again"
}
```

### Common Error Codes

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `VALIDATION_ERROR` | Input validation failed | Check request format and field values |
| `FILE_NOT_FOUND` | Specified file doesn't exist | Verify file path is correct |
| `PERMISSION_DENIED` | Insufficient file permissions | Check read/write permissions |
| `DISK_SPACE_ERROR` | Insufficient disk space | Free up disk space |
| `PROCESSING_ERROR` | Error during transcription | Check file format and integrity |
| `PATH_TRAVERSAL_BLOCKED` | Directory traversal attempt | Use valid, safe file paths |
| `INVALID_MODEL` | Unsupported Whisper model | Use supported model names |
| `QUEUE_EMPTY` | No files in processing queue | Add files before starting processing |
| `ALREADY_PROCESSING` | Processing already in progress | Wait for completion or stop current processing |

## 🛠️ SDK Examples

### Python Client Example
```python
import requests
import json

class VideoTranscriberClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def add_files(self, file_paths):
        """Add files to processing queue."""
        response = self.session.post(
            f"{self.base_url}/api/files/add",
            json={"files": file_paths}
        )
        return response.json()
    
    def start_processing(self, options):
        """Start processing with options."""
        response = self.session.post(
            f"{self.base_url}/api/processing/start",
            json=options
        )
        return response.json()
    
    def get_queue_status(self):
        """Get current queue status."""
        response = self.session.get(f"{self.base_url}/api/queue")
        return response.json()

# Usage example
client = VideoTranscriberClient()

# Add files
result = client.add_files([
    "C:/Videos/interview.mp4",
    "C:/Videos/lecture.avi"
])

# Start processing
options = {
    "output_directory": "C:/Output",
    "whisper_model": "large",
    "language": "en",
    "output_format": "txt"
}
result = client.start_processing(options)
```

### JavaScript/TypeScript Client Example
```typescript
class VideoTranscriberAPI {
  private baseUrl: string;
  
  constructor(baseUrl = 'http://127.0.0.1:8000') {
    this.baseUrl = baseUrl;
  }
  
  async addFiles(files: string[]): Promise<AddFilesResponse> {
    const response = await fetch(`${this.baseUrl}/api/files/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files })
    });
    return response.json();
  }
  
  async startProcessing(options: ProcessingOptions): Promise<StartProcessingResponse> {
    const response = await fetch(`${this.baseUrl}/api/processing/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options)
    });
    return response.json();
  }
  
  connectWebSocket(): WebSocket {
    const ws = new WebSocket(`ws://127.0.0.1:8000/ws`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleWebSocketMessage(message);
    };
    
    return ws;
  }
  
  private handleWebSocketMessage(message: any): void {
    switch (message.type) {
      case 'progress_update':
        this.onProgressUpdate(message);
        break;
      case 'file_completed':
        this.onFileCompleted(message);
        break;
      // Handle other message types
    }
  }
}

// Usage
const api = new VideoTranscriberAPI();
const ws = api.connectWebSocket();

// Add files and start processing
await api.addFiles(['C:/Videos/video1.mp4']);
await api.startProcessing({
  output_directory: 'C:/Output',
  whisper_model: 'large',
  language: 'en',
  output_format: 'txt'
});
```

## 🔧 Development & Testing

### API Testing with curl

```bash
# Health check
curl http://127.0.0.1:8000/health

# Add files to queue
curl -X POST http://127.0.0.1:8000/api/files/add \
  -H "Content-Type: application/json" \
  -d '{"files": ["C:/Videos/test.mp4"]}'

# Start processing
curl -X POST http://127.0.0.1:8000/api/processing/start \
  -H "Content-Type: application/json" \
  -d '{
    "output_directory": "C:/Output",
    "whisper_model": "large",
    "language": "en",
    "output_format": "txt"
  }'

# Get queue status
curl http://127.0.0.1:8000/api/queue

# Validate output path
curl -X POST http://127.0.0.1:8000/api/validate-output-path \
  -H "Content-Type: application/json" \
  -d '{"path": "C:/Output/MyTranscripts"}'
```

### WebSocket Testing

```javascript
// Browser console WebSocket test
const ws = new WebSocket('ws://127.0.0.1:8000/ws');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
ws.onopen = () => console.log('Connected');
```

## 📝 Rate Limiting & Performance

### Performance Considerations
- **Concurrent Connections**: WebSocket supports unlimited connections
- **File Processing**: One file processed at a time per session
- **Memory Usage**: Optimized for large file processing
- **Disk I/O**: Minimized with intelligent caching

### Best Practices
- Use WebSocket for real-time updates rather than polling
- Validate paths client-side before API calls
- Implement exponential backoff for retries
- Handle WebSocket reconnection gracefully
- Monitor processing progress to provide user feedback

---

This API reference provides complete documentation for integrating with the Video Transcriber App backend. For additional examples and advanced usage patterns, refer to the Developer Guide and source code.