// API Types based on the REST API specification

export type FileStatus = 'queued' | 'processing' | 'completed' | 'failed'
export type WhisperModel = 'base' | 'small' | 'medium' | 'large'
export type OutputFormat = 'txt' | 'srt' | 'vtt'

export interface QueueItem {
  id: string
  file_path: string
  status: FileStatus
  progress: number // 0-100
  processing_time?: number // seconds
  estimated_time_remaining?: number // seconds
  current_step?: string
  output_file?: string
  error?: string
  error_code?: string
  file_size: number
  duration?: number
  format: string
  created_at: string // ISO 8601
  started_at?: string
  completed_at?: string
}

export interface ProcessingSession {
  id: string
  started_at: string
  completed_at?: string
  total_files: number
  completed_files: number
  failed_files: number
  total_processing_time: number
  average_time_per_file: number
  output_directory: string
  is_paused: boolean
}

export interface ApplicationSettings {
  whisper_model: WhisperModel
  language: string // 'auto' or language code
  output_format: OutputFormat
  max_parallel_jobs: number
  chunk_length: number
  temperature: number
  compression_ratio_threshold: number
}

export interface ApplicationStatus {
  status: string
  python_version: string
  whisper_model: string
  available_models: string[]
  uptime: number
}

export interface ProcessingStatus {
  is_processing: boolean
  is_paused: boolean
  current_file?: {
    id: string
    file_path: string
    progress: number
    step: string
    estimated_time_remaining: number
  }
  session?: ProcessingSession
}

// API Response Types

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: string
    timestamp: string
  }
}

export interface AddFilesResponse {
  success: true
  added_count: number
  skipped_count: number
  items: QueueItem[]
  errors: Array<{
    file: string
    error: string
  }>
}

export interface AddDirectoryResponse {
  success: true
  added_count: number
  skipped_count: number
  empty_directories: string[]
  items: QueueItem[]
  errors: Array<{
    file: string
    error: string
  }>
}

export interface QueueResponse {
  total_count: number
  queued_count: number
  processing_count: number
  completed_count: number
  failed_count: number
  items: QueueItem[]
}

export interface StartProcessingResponse {
  success: true
  message: string
  session_id: string
  total_files: number
  estimated_total_time: number
}

export interface ResultsResponse {
  total_count: number
  items: QueueItem[]
}

export interface TranscriptResponse {
  file_id: string
  file_path: string
  transcript: string
  format: string
  word_count: number
  created_at: string
}

// WebSocket Event Types

export type WebSocketEventType = 
  | 'progress_update'
  | 'queue_update'
  | 'processing_status_change'
  | 'file_completed'
  | 'file_failed'
  | 'session_complete'
  | 'overall_progress_update'
  | 'error'
  | 'system_notification'

export interface BaseWebSocketEvent {
  type: WebSocketEventType
  timestamp: string
}

export interface ProgressUpdateEvent extends BaseWebSocketEvent {
  type: 'progress_update'
  file_id: string
  file_path: string
  progress: number
  step: string
  estimated_time_remaining: number
}

export interface QueueUpdateEvent extends BaseWebSocketEvent {
  type: 'queue_update'
  action: 'file_added' | 'file_removed' | 'file_completed' | 'file_failed' | 'status_changed'
  file_id: string
  file_path: string
  new_status: FileStatus
  output_file?: string
  processing_time?: number
}

export interface ProcessingStatusChangeEvent extends BaseWebSocketEvent {
  type: 'processing_status_change'
  status: 'started' | 'paused' | 'resumed' | 'stopped'
  session_id?: string
  total_files?: number
  message: string
}

export interface FileCompletedEvent extends BaseWebSocketEvent {
  type: 'file_completed'
  file_id: string
  file_path: string
  success: boolean
  output_file?: string
  processing_time: number
  transcript_preview?: string
}

export interface FileFailedEvent extends BaseWebSocketEvent {
  type: 'file_failed'
  file_id: string
  file_path: string
  error: string
  error_code: string
}

export interface SessionCompleteEvent extends BaseWebSocketEvent {
  type: 'session_complete'
  session_id: string
  total_files: number
  completed_files: number
  failed_files: number
  total_processing_time: number
  average_time_per_file: number
  output_directory: string
}

export interface OverallProgressUpdateEvent extends BaseWebSocketEvent {
  type: 'overall_progress_update'
  processed_files: number
  total_files: number
  overall_progress: number
  current_file?: string
}

export interface ErrorEvent extends BaseWebSocketEvent {
  type: 'error'
  error: string
  error_code: string
  details?: string
}

export interface SystemNotificationEvent extends BaseWebSocketEvent {
  type: 'system_notification'
  title: string
  message: string
  priority: 'low' | 'normal' | 'high'
  actions?: Array<{
    label: string
    action: string
  }>
}

export type WebSocketEvent = 
  | ProgressUpdateEvent
  | QueueUpdateEvent
  | ProcessingStatusChangeEvent
  | FileCompletedEvent
  | FileFailedEvent
  | SessionCompleteEvent
  | OverallProgressUpdateEvent
  | ErrorEvent
  | SystemNotificationEvent

// API Error Codes
export const API_ERROR_CODES = {
  INVALID_FILE_PATH: 'INVALID_FILE_PATH',
  UNSUPPORTED_FORMAT: 'UNSUPPORTED_FORMAT',
  PROCESSING_IN_PROGRESS: 'PROCESSING_IN_PROGRESS',
  OUTPUT_DIRECTORY_INVALID: 'OUTPUT_DIRECTORY_INVALID',
  WHISPER_MODEL_ERROR: 'WHISPER_MODEL_ERROR',
  AUDIO_EXTRACTION_FAILED: 'AUDIO_EXTRACTION_FAILED',
  DISK_SPACE_LOW: 'DISK_SPACE_LOW',
  PERMISSION_DENIED: 'PERMISSION_DENIED'
} as const

export type ApiErrorCode = typeof API_ERROR_CODES[keyof typeof API_ERROR_CODES]

// Utility types for form handling
export interface FileUploadOptions {
  files?: string[]
  directory?: string
  recursive?: boolean
  file_types?: string[]
}

export interface ProcessingOptions {
  output_directory: string
  whisper_model: 'base' | 'small' | 'medium' | 'large'
  language: 'en' | 'auto'
  output_format: 'txt' | 'srt' | 'vtt'
}