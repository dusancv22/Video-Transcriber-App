/**
 * API service for communicating with the FastAPI backend
 */

import axios, { AxiosResponse, AxiosError } from 'axios'
import {
  QueueItem,
  ProcessingOptions,
  ApiResponse,
  AddFilesResponse,
  AddDirectoryResponse,
  QueueResponse,
  StartProcessingResponse,
  ProcessingStatus,
  ApplicationStatus,
  FileUploadOptions
} from '../types/api'

// Base API configuration
const API_BASE_URL = 'http://127.0.0.1:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

/**
 * API Service Class
 */
export class VideoTranscriberAPI {
  
  /**
   * Get application status
   */
  static async getStatus(): Promise<ApplicationStatus> {
    try {
      const response = await api.get<ApplicationStatus>('/status')
      return response.data
    } catch (error) {
      throw new Error(`Failed to get application status: ${error}`)
    }
  }

  /**
   * Add files to processing queue
   */
  static async addFiles(files: string[]): Promise<AddFilesResponse> {
    try {
      const response = await api.post<AddFilesResponse>('/files/add', {
        files
      })
      return response.data
    } catch (error) {
      throw new Error(`Failed to add files: ${error}`)
    }
  }

  /**
   * Add directory to processing queue
   */
  static async addDirectory(directory: string, recursive: boolean = true): Promise<AddDirectoryResponse> {
    try {
      const response = await api.post<AddDirectoryResponse>('/directory/add', {
        directory,
        recursive
      })
      return response.data
    } catch (error) {
      throw new Error(`Failed to add directory: ${error}`)
    }
  }

  /**
   * Get current processing queue
   */
  static async getQueue(): Promise<QueueResponse> {
    try {
      const response = await api.get<QueueResponse>('/queue')
      return response.data
    } catch (error) {
      throw new Error(`Failed to get queue: ${error}`)
    }
  }

  /**
   * Remove file from processing queue
   */
  static async removeFromQueue(fileId: string): Promise<ApiResponse> {
    try {
      const response = await api.delete<ApiResponse>(`/queue/${fileId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to remove file from queue: ${error}`)
    }
  }

  /**
   * Clear all files from processing queue
   */
  static async clearQueue(): Promise<ApiResponse> {
    try {
      const response = await api.delete<ApiResponse>('/queue')
      return response.data
    } catch (error) {
      throw new Error(`Failed to clear queue: ${error}`)
    }
  }

  /**
   * Start processing queue
   */
  static async startProcessing(options: ProcessingOptions): Promise<StartProcessingResponse> {
    try {
      const response = await api.post<StartProcessingResponse>('/processing/start', options)
      return response.data
    } catch (error) {
      throw new Error(`Failed to start processing: ${error}`)
    }
  }

  /**
   * Pause/Resume processing
   */
  static async pauseProcessing(): Promise<ApiResponse> {
    try {
      const response = await api.post<ApiResponse>('/processing/pause')
      return response.data
    } catch (error) {
      throw new Error(`Failed to pause processing: ${error}`)
    }
  }

  /**
   * Stop processing
   */
  static async stopProcessing(): Promise<ApiResponse> {
    try {
      const response = await api.post<ApiResponse>('/processing/stop')
      return response.data
    } catch (error) {
      throw new Error(`Failed to stop processing: ${error}`)
    }
  }

  /**
   * Get processing status
   */
  static async getProcessingStatus(): Promise<ProcessingStatus> {
    try {
      const response = await api.get<ProcessingStatus>('/processing/status')
      return response.data
    } catch (error) {
      throw new Error(`Failed to get processing status: ${error}`)
    }
  }

  /**
   * Health check - test if backend is responsive
   */
  static async healthCheck(): Promise<boolean> {
    try {
      await api.get('/status')
      return true
    } catch (error) {
      return false
    }
  }

  /**
   * Get file transcript content
   */
  static async getTranscript(fileId: string): Promise<string> {
    try {
      const response = await api.get<{ transcript: string }>(`/transcript/${fileId}`)
      return response.data.transcript
    } catch (error) {
      throw new Error(`Failed to get transcript: ${error}`)
    }
  }
}

/**
 * Utility functions for API operations
 */
export class APIUtils {
  
  /**
   * Convert file paths from Electron file dialogs to API format
   */
  static formatFilePaths(filePaths: string[]): string[] {
    return filePaths.map(path => path.replace(/\\/g, '/'))
  }

  /**
   * Validate file upload options
   */
  static validateUploadOptions(options: FileUploadOptions): boolean {
    if (options.files && options.files.length === 0 && !options.directory) {
      return false
    }
    return true
  }

  /**
   * Estimate processing time based on file sizes and queue
   */
  static estimateProcessingTime(queueItems: QueueItem[]): number {
    const queuedItems = queueItems.filter(item => item.status === 'queued')
    const avgTimePerMB = 2 // seconds per MB (rough estimate)
    
    const totalSizeMB = queuedItems.reduce((total, item) => {
      return total + (item.file_size / (1024 * 1024))
    }, 0)
    
    return Math.ceil(totalSizeMB * avgTimePerMB)
  }

  /**
   * Format file size for display
   */
  static formatFileSize(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB']
    let size = bytes
    let unitIndex = 0

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024
      unitIndex++
    }

    return `${size.toFixed(unitIndex > 0 ? 1 : 0)} ${units[unitIndex]}`
  }

  /**
   * Format duration for display
   */
  static formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const remainingSeconds = seconds % 60

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
    } else {
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
    }
  }

  /**
   * Get file extension from path
   */
  static getFileExtension(filePath: string): string {
    return filePath.split('.').pop()?.toUpperCase() || ''
  }

  /**
   * Get filename from full path
   */
  static getFileName(filePath: string): string {
    return filePath.split(/[/\\]/).pop() || filePath
  }

  /**
   * Check if file type is supported
   */
  static isSupportedFileType(filePath: string): boolean {
    const supportedExtensions = ['.mp4', '.avi', '.mkv', '.mov']
    const extension = filePath.toLowerCase().substring(filePath.lastIndexOf('.'))
    return supportedExtensions.includes(extension)
  }
}

export default VideoTranscriberAPI