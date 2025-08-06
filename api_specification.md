# Video Transcriber App - REST API & WebSocket Specification

## Overview
This document defines the complete API specification for the Electron frontend to communicate with the Python backend, preserving all existing PyQt6 functionality while enabling real-time updates.

## Base Configuration
- **Base URL**: `http://localhost:8765`
- **WebSocket URL**: `ws://localhost:8765/ws`
- **API Version**: `v1`
- **Content-Type**: `application/json`

## Authentication
- Local application - no authentication required
- Future: API key for security if needed

---

## REST API Endpoints

### 1. Application Status

#### GET `/api/v1/status`
Get current application status and health check.

**Response:**
```json
{
  "status": "ready",
  "python_version": "3.11.0",
  "whisper_model": "large",
  "available_models": ["base", "small", "medium", "large"],
  "uptime": 3600
}
```

---

### 2. File Management

#### POST `/api/v1/files/add`
Add individual files to the processing queue.

**Request:**
```json
{
  "files": [
    "/path/to/video1.mp4",
    "/path/to/video2.avi"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "added_count": 2,
  "skipped_count": 0,
  "items": [
    {
      "id": "uuid-1",
      "file_path": "/path/to/video1.mp4",
      "status": "queued",
      "file_size": 1048576,
      "duration": 300.5,
      "format": "mp4"
    },
    {
      "id": "uuid-2", 
      "file_path": "/path/to/video2.avi",
      "status": "queued",
      "file_size": 2097152,
      "duration": 150.2,
      "format": "avi"
    }
  ],
  "errors": []
}
```

#### POST `/api/v1/files/add-directory`
Add all video files from a directory (recursive).

**Request:**
```json
{
  "directory": "/path/to/videos",
  "recursive": true,
  "file_types": ["mp4", "avi", "mkv", "mov"]
}
```

**Response:**
```json
{
  "success": true,
  "added_count": 15,
  "skipped_count": 2,
  "empty_directories": [
    "/path/to/videos/empty_folder"
  ],
  "items": [...],
  "errors": [
    {
      "file": "/path/to/videos/corrupted.mp4",
      "error": "File is corrupted or unreadable"
    }
  ]
}
```

#### DELETE `/api/v1/files/{file_id}`
Remove a specific file from the queue.

**Response:**
```json
{
  "success": true,
  "message": "File removed from queue"
}
```

#### GET `/api/v1/files/queue`
Get current queue status with all files.

**Response:**
```json
{
  "total_count": 5,
  "queued_count": 3,
  "processing_count": 1,
  "completed_count": 1,
  "failed_count": 0,
  "items": [
    {
      "id": "uuid-1",
      "file_path": "/path/to/video1.mp4",
      "status": "completed",
      "progress": 100.0,
      "processing_time": 45.2,
      "output_file": "/output/video1.txt",
      "created_at": "2025-01-15T10:30:00Z",
      "completed_at": "2025-01-15T10:30:45Z"
    },
    {
      "id": "uuid-2",
      "file_path": "/path/to/video2.avi", 
      "status": "processing",
      "progress": 65.5,
      "estimated_time_remaining": 120,
      "current_step": "Transcribing audio segment 3/5"
    }
  ]
}
```

#### POST `/api/v1/files/clear`
Clear all files from the queue.

**Request:**
```json
{
  "force": false  // true to clear even during processing
}
```

**Response:**
```json
{
  "success": true,
  "message": "Queue cleared",
  "removed_count": 5
}
```

---

### 3. Processing Control

#### POST `/api/v1/process/start`
Start processing the queue.

**Request:**
```json
{
  "output_directory": "/path/to/output"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Processing started",
  "session_id": "session-uuid",
  "total_files": 5,
  "estimated_total_time": 900
}
```

#### POST `/api/v1/process/pause`
Pause current processing.

**Response:**
```json
{
  "success": true,
  "message": "Processing paused",
  "current_file": "video2.avi",
  "progress": 45.2
}
```

#### POST `/api/v1/process/resume`
Resume paused processing.

**Response:**
```json
{
  "success": true,
  "message": "Processing resumed"
}
```

#### POST `/api/v1/process/stop`
Stop all processing and reset.

**Response:**
```json
{
  "success": true,
  "message": "Processing stopped",
  "completed_files": 2,
  "remaining_files": 3
}
```

#### GET `/api/v1/process/status`
Get detailed processing status.

**Response:**
```json
{
  "is_processing": true,
  "is_paused": false,
  "current_file": {
    "id": "uuid-2",
    "file_path": "/path/to/video2.avi",
    "progress": 65.5,
    "step": "Transcribing audio segment 3/5",
    "estimated_time_remaining": 120
  },
  "session": {
    "id": "session-uuid",
    "started_at": "2025-01-15T10:30:00Z",
    "total_files": 5,
    "completed_files": 2,
    "failed_files": 0,
    "total_processing_time": 180,
    "average_time_per_file": 90
  }
}
```

---

### 4. Configuration & Settings

#### GET `/api/v1/settings`
Get current application settings.

**Response:**
```json
{
  "whisper_model": "large",
  "language": "auto",
  "output_format": "txt",
  "max_parallel_jobs": 1,
  "chunk_length": 30,
  "temperature": 0.0,
  "compression_ratio_threshold": 2.4
}
```

#### PUT `/api/v1/settings`
Update application settings.

**Request:**
```json
{
  "whisper_model": "medium",
  "language": "en",
  "output_format": "srt"
}
```

#### GET `/api/v1/settings/output-directory`
Get current output directory.

**Response:**
```json
{
  "output_directory": "/path/to/output",
  "writable": true,
  "free_space": 1073741824
}
```

#### POST `/api/v1/settings/output-directory`
Set output directory.

**Request:**
```json
{
  "directory": "/new/path/to/output"
}
```

---

### 5. Results & History

#### GET `/api/v1/results`
Get processing results and history.

**Query Parameters:**
- `limit`: number (default: 50)
- `offset`: number (default: 0)
- `status`: string (completed|failed|all)

**Response:**
```json
{
  "total_count": 150,
  "items": [
    {
      "id": "uuid-1",
      "file_path": "/path/to/video1.mp4",
      "output_file": "/output/video1.txt",
      "status": "completed",
      "processing_time": 45.2,
      "file_size": 1048576,
      "transcript_length": 2500,
      "created_at": "2025-01-15T10:30:00Z",
      "completed_at": "2025-01-15T10:30:45Z"
    }
  ]
}
```

#### GET `/api/v1/results/{file_id}/transcript`
Get transcript content for a specific file.

**Response:**
```json
{
  "file_id": "uuid-1",
  "file_path": "/path/to/video1.mp4",
  "transcript": "Hello everyone, welcome to this video...",
  "format": "txt",
  "word_count": 350,
  "created_at": "2025-01-15T10:30:45Z"
}
```

---

## WebSocket Events

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8765/ws');
```

### Client to Server Events

#### `subscribe`
Subscribe to specific event types.
```json
{
  "type": "subscribe",
  "events": ["progress", "queue_update", "processing_complete"]
}
```

#### `unsubscribe`
Unsubscribe from event types.
```json
{
  "type": "unsubscribe", 
  "events": ["progress"]
}
```

### Server to Client Events

#### `progress_update`
Real-time progress updates during processing.
```json
{
  "type": "progress_update",
  "file_id": "uuid-2",
  "file_path": "/path/to/video2.avi",
  "progress": 65.5,
  "step": "Transcribing audio segment 3/5",
  "estimated_time_remaining": 120,
  "timestamp": "2025-01-15T10:35:30Z"
}
```

#### `queue_update`
Queue status changes (file added, removed, status changed).
```json
{
  "type": "queue_update",
  "action": "file_completed",
  "file_id": "uuid-1",
  "file_path": "/path/to/video1.mp4",
  "new_status": "completed",
  "output_file": "/output/video1.txt",
  "processing_time": 45.2,
  "timestamp": "2025-01-15T10:30:45Z"
}
```

#### `processing_status_change`
Processing state changes (started, paused, resumed, stopped).
```json
{
  "type": "processing_status_change",
  "status": "started",
  "session_id": "session-uuid",
  "total_files": 5,
  "message": "Processing started with 5 files in queue",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### `file_completed`
Individual file processing completion.
```json
{
  "type": "file_completed",
  "file_id": "uuid-1",
  "file_path": "/path/to/video1.mp4",
  "success": true,
  "output_file": "/output/video1.txt",
  "processing_time": 45.2,
  "transcript_preview": "Hello everyone, welcome to...",
  "timestamp": "2025-01-15T10:30:45Z"
}
```

#### `file_failed`
Individual file processing failure.
```json
{
  "type": "file_failed",
  "file_id": "uuid-3",
  "file_path": "/path/to/corrupted.mp4",
  "error": "Audio extraction failed: Unsupported codec",
  "error_code": "AUDIO_EXTRACTION_FAILED",
  "timestamp": "2025-01-15T10:32:15Z"
}
```

#### `session_complete`
All files in session completed.
```json
{
  "type": "session_complete",
  "session_id": "session-uuid",
  "total_files": 5,
  "completed_files": 4,
  "failed_files": 1,
  "total_processing_time": 250.5,
  "average_time_per_file": 62.6,
  "output_directory": "/path/to/output",
  "timestamp": "2025-01-15T10:35:00Z"
}
```

#### `error`
General application errors.
```json
{
  "type": "error",
  "error": "Whisper model failed to load",
  "error_code": "MODEL_LOAD_FAILED",
  "details": "CUDA out of memory",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### `system_notification`
System-level notifications for desktop alerts.
```json
{
  "type": "system_notification",
  "title": "Transcription Complete",
  "message": "Successfully processed 4 out of 5 files",
  "priority": "normal",
  "actions": [
    {
      "label": "Open Output Folder",
      "action": "open_output_folder"
    }
  ],
  "timestamp": "2025-01-15T10:35:00Z"
}
```

---

## Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "INVALID_FILE_PATH",
    "message": "The specified file path is invalid or inaccessible",
    "details": "/path/to/nonexistent.mp4 does not exist",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

### Common Error Codes
- `INVALID_FILE_PATH`: File path is invalid or inaccessible
- `UNSUPPORTED_FORMAT`: File format not supported
- `PROCESSING_IN_PROGRESS`: Cannot perform action while processing
- `OUTPUT_DIRECTORY_INVALID`: Output directory is not writable
- `WHISPER_MODEL_ERROR`: Error loading or using Whisper model
- `AUDIO_EXTRACTION_FAILED`: Failed to extract audio from video
- `DISK_SPACE_LOW`: Insufficient disk space for processing
- `PERMISSION_DENIED`: Insufficient permissions for operation

---

## Data Models

### QueueItem
```typescript
interface QueueItem {
  id: string;
  file_path: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number; // 0-100
  processing_time?: number; // seconds
  estimated_time_remaining?: number; // seconds
  current_step?: string;
  output_file?: string;
  error?: string;
  error_code?: string;
  file_size: number;
  duration?: number;
  format: string;
  created_at: string; // ISO 8601
  started_at?: string;
  completed_at?: string;
}
```

### ProcessingSession
```typescript
interface ProcessingSession {
  id: string;
  started_at: string;
  completed_at?: string;
  total_files: number;
  completed_files: number;
  failed_files: number;
  total_processing_time: number;
  average_time_per_file: number;
  output_directory: string;
  is_paused: boolean;
}
```

### ApplicationSettings
```typescript
interface ApplicationSettings {
  whisper_model: 'base' | 'small' | 'medium' | 'large';
  language: string; // 'auto' or language code
  output_format: 'txt' | 'srt' | 'vtt';
  max_parallel_jobs: number;
  chunk_length: number;
  temperature: number;
  compression_ratio_threshold: number;
}
```

This API specification provides complete coverage of all existing PyQt6 functionality while enabling modern real-time web application development patterns.