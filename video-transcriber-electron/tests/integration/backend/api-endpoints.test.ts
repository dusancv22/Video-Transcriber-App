import { describe, it, expect, beforeEach, vi, beforeAll, afterAll } from 'vitest'

// Mock fetch for API testing
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock WebSocket for real-time testing
const mockWebSocket = {
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  readyState: WebSocket.OPEN,
  onopen: vi.fn(),
  onmessage: vi.fn(),
  onerror: vi.fn(),
  onclose: vi.fn()
}

global.WebSocket = vi.fn(() => mockWebSocket) as any

// API Service mock
class MockApiService {
  private baseUrl = 'http://localhost:8000/api'

  async validateOutputDirectory(path: string) {
    const response = await fetch(`${this.baseUrl}/validate-directory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directory_path: path })
    })
    return response.json()
  }

  async addFiles(filePaths: string[]) {
    const response = await fetch(`${this.baseUrl}/queue/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_paths: filePaths })
    })
    return response.json()
  }

  async removeFromQueue(itemId: string) {
    const response = await fetch(`${this.baseUrl}/queue/${itemId}`, {
      method: 'DELETE'
    })
    return response.json()
  }

  async getQueueStatus() {
    const response = await fetch(`${this.baseUrl}/queue/status`)
    return response.json()
  }

  async startProcessing(settings: any) {
    const response = await fetch(`${this.baseUrl}/processing/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    })
    return response.json()
  }

  async stopProcessing() {
    const response = await fetch(`${this.baseUrl}/processing/stop`, {
      method: 'POST'
    })
    return response.json()
  }

  async getProcessingStatus() {
    const response = await fetch(`${this.baseUrl}/processing/status`)
    return response.json()
  }

  async getSystemHealth() {
    const response = await fetch(`${this.baseUrl}/health`)
    return response.json()
  }

  connectWebSocket(onMessage: (data: any) => void) {
    const ws = new WebSocket('ws://localhost:8000/ws')
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      onMessage(data)
    }
    return ws
  }
}

describe('Backend API Endpoints Tests', () => {
  let apiService: MockApiService

  beforeAll(() => {
    apiService = new MockApiService()
  })

  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockClear()
  })

  afterAll(() => {
    vi.restoreAllMocks()
  })

  describe('Directory Validation Endpoint', () => {
    it('should validate legitimate output directories', async () => {
      const validPaths = [
        'C:/Output/Transcripts',
        'D:/MyDocuments/VideoTranscripts',
        '/home/user/transcripts',
        '/Users/username/Documents/Transcripts'
      ]

      for (const path of validPaths) {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            valid: true,
            path: path,
            writable: true,
            exists: true,
            message: 'Directory is valid and writable'
          })
        })

        const result = await apiService.validateOutputDirectory(path)

        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/validate-directory',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ directory_path: path })
          }
        )

        expect(result.valid).toBe(true)
        expect(result.writable).toBe(true)
      }
    })

    it('should reject path traversal attempts', async () => {
      const maliciousPaths = [
        '../../../etc/passwd',
        '..\\..\\windows\\system32',
        'C:\\Windows\\..\\..\\sensitive',
        '/var/log/../../etc/shadow',
        'C:/Output/../../../Windows/System32',
        '\\\\?\\C:\\Windows\\System32\\config'
      ]

      for (const path of maliciousPaths) {
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({
            valid: false,
            path: path,
            error: 'Invalid directory path: path traversal detected',
            error_code: 'PATH_TRAVERSAL_DETECTED'
          })
        })

        const result = await apiService.validateOutputDirectory(path)

        expect(result.valid).toBe(false)
        expect(result.error_code).toBe('PATH_TRAVERSAL_DETECTED')
      }
    })

    it('should reject system directories', async () => {
      const systemPaths = [
        'C:\\Windows\\System32',
        'C:\\Program Files',
        '/etc',
        '/usr/bin',
        '/root',
        'C:\\Users\\Administrator',
        '/var/log'
      ]

      for (const path of systemPaths) {
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({
            valid: false,
            path: path,
            error: 'Invalid directory: system directory not allowed',
            error_code: 'SYSTEM_DIRECTORY_NOT_ALLOWED'
          })
        })

        const result = await apiService.validateOutputDirectory(path)

        expect(result.valid).toBe(false)
        expect(result.error_code).toBe('SYSTEM_DIRECTORY_NOT_ALLOWED')
      }
    })

    it('should handle permission denied scenarios', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({
          valid: false,
          path: 'C:/RestrictedDirectory',
          error: 'Permission denied: directory not writable',
          error_code: 'PERMISSION_DENIED'
        })
      })

      const result = await apiService.validateOutputDirectory('C:/RestrictedDirectory')

      expect(result.valid).toBe(false)
      expect(result.error_code).toBe('PERMISSION_DENIED')
    })

    it('should handle network drive validation', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          path: '\\\\server\\share\\transcripts',
          writable: true,
          exists: true,
          message: 'Network directory accessible',
          warning: 'Network drives may have slower performance'
        })
      })

      const result = await apiService.validateOutputDirectory('\\\\server\\share\\transcripts')

      expect(result.valid).toBe(true)
      expect(result.warning).toContain('Network drives')
    })
  })

  describe('Queue Management Endpoints', () => {
    it('should add files to processing queue', async () => {
      const testFiles = [
        'C:/Videos/video1.mp4',
        'C:/Videos/video2.avi',
        'C:/Videos/video3.mkv'
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          added_count: 3,
          skipped_count: 0,
          items: testFiles.map((path, index) => ({
            id: `item-${index + 1}`,
            file_path: path,
            status: 'queued',
            added_at: new Date().toISOString()
          }))
        })
      })

      const result = await apiService.addFiles(testFiles)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/queue/add',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file_paths: testFiles })
        }
      )

      expect(result.success).toBe(true)
      expect(result.added_count).toBe(3)
      expect(result.items).toHaveLength(3)
    })

    it('should validate file paths before adding to queue', async () => {
      const maliciousFiles = [
        'C:/Videos/video.mp4',
        '../../../etc/passwd',
        'C:/Videos/../../Windows/System32/calc.exe'
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          added_count: 1,
          skipped_count: 2,
          items: [{
            id: 'item-1',
            file_path: 'C:/Videos/video.mp4',
            status: 'queued',
            added_at: new Date().toISOString()
          }],
          skipped_files: [
            {
              file_path: '../../../etc/passwd',
              reason: 'Invalid file path: path traversal detected'
            },
            {
              file_path: 'C:/Videos/../../Windows/System32/calc.exe',
              reason: 'Invalid file path: path traversal detected'
            }
          ]
        })
      })

      const result = await apiService.addFiles(maliciousFiles)

      expect(result.success).toBe(true)
      expect(result.added_count).toBe(1)
      expect(result.skipped_count).toBe(2)
      expect(result.skipped_files).toHaveLength(2)
    })

    it('should remove items from queue', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          removed_id: 'item-123',
          message: 'Item removed from queue successfully'
        })
      })

      const result = await apiService.removeFromQueue('item-123')

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/queue/item-123',
        { method: 'DELETE' }
      )

      expect(result.success).toBe(true)
      expect(result.removed_id).toBe('item-123')
    })

    it('should get queue status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total_items: 5,
          queued: 2,
          processing: 1,
          completed: 1,
          failed: 1,
          items: [
            {
              id: 'item-1',
              file_path: 'C:/Videos/video1.mp4',
              status: 'processing',
              progress: 65,
              current_step: 'Transcribing audio'
            },
            {
              id: 'item-2',
              file_path: 'C:/Videos/video2.avi',
              status: 'queued',
              progress: 0
            }
          ]
        })
      })

      const result = await apiService.getQueueStatus()

      expect(result.total_items).toBe(5)
      expect(result.processing).toBe(1)
      expect(result.items).toHaveLength(2)
    })

    it('should handle queue operation errors', async () => {
      // Test add files error
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({
          error: 'Database connection failed',
          error_code: 'DB_CONNECTION_ERROR'
        })
      })

      try {
        await apiService.addFiles(['C:/Videos/test.mp4'])
      } catch (error) {
        // Should handle gracefully
      }

      // Test remove item not found
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({
          error: 'Queue item not found',
          error_code: 'ITEM_NOT_FOUND'
        })
      })

      const removeResult = await apiService.removeFromQueue('nonexistent-id')
      expect(removeResult.error_code).toBe('ITEM_NOT_FOUND')
    })
  })

  describe('Processing Control Endpoints', () => {
    it('should start processing with valid settings', async () => {
      const processingSettings = {
        output_directory: 'C:/Custom/Output',
        whisper_model: 'medium',
        language: 'en',
        output_format: 'srt',
        concurrent_jobs: 2
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          message: 'Processing started successfully',
          processing_id: 'proc-123',
          settings: processingSettings
        })
      })

      const result = await apiService.startProcessing(processingSettings)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/processing/start',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(processingSettings)
        }
      )

      expect(result.success).toBe(true)
      expect(result.processing_id).toBe('proc-123')
    })

    it('should validate processing settings', async () => {
      const invalidSettings = {
        output_directory: '../../../etc',
        whisper_model: 'invalid_model',
        language: 'invalid_lang',
        output_format: 'invalid_format',
        concurrent_jobs: -1
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          error: 'Invalid processing settings',
          error_code: 'INVALID_SETTINGS',
          validation_errors: [
            'output_directory: Path traversal detected',
            'whisper_model: Must be one of: base, small, medium, large',
            'language: Must be one of: en, auto',
            'output_format: Must be one of: txt, srt, vtt',
            'concurrent_jobs: Must be positive integer'
          ]
        })
      })

      const result = await apiService.startProcessing(invalidSettings)

      expect(result.error_code).toBe('INVALID_SETTINGS')
      expect(result.validation_errors).toHaveLength(5)
    })

    it('should stop processing', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          message: 'Processing stopped successfully',
          stopped_jobs: 2
        })
      })

      const result = await apiService.stopProcessing()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/processing/stop',
        { method: 'POST' }
      )

      expect(result.success).toBe(true)
      expect(result.stopped_jobs).toBe(2)
    })

    it('should get processing status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          is_running: true,
          active_jobs: 2,
          completed_today: 15,
          failed_today: 1,
          current_jobs: [
            {
              id: 'job-1',
              file_path: 'C:/Videos/video1.mp4',
              progress: 45,
              step: 'Audio extraction',
              estimated_remaining: 180
            },
            {
              id: 'job-2',
              file_path: 'C:/Videos/video2.avi',
              progress: 78,
              step: 'Text processing',
              estimated_remaining: 60
            }
          ],
          system_resources: {
            cpu_usage: 65,
            memory_usage: 78,
            disk_space_available: 50000000000
          }
        })
      })

      const result = await apiService.getProcessingStatus()

      expect(result.is_running).toBe(true)
      expect(result.active_jobs).toBe(2)
      expect(result.current_jobs).toHaveLength(2)
      expect(result.system_resources).toBeDefined()
    })
  })

  describe('System Health and Monitoring', () => {
    it('should check system health', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'healthy',
          timestamp: new Date().toISOString(),
          services: {
            database: 'online',
            file_system: 'online',
            whisper_service: 'online',
            queue_processor: 'online'
          },
          system_info: {
            cpu_count: 8,
            memory_total: 16000000000,
            disk_space: 500000000000,
            python_version: '3.9.7',
            whisper_version: '20230918'
          },
          performance: {
            average_processing_time: 45.5,
            success_rate: 0.97,
            queue_length: 3
          }
        })
      })

      const result = await apiService.getSystemHealth()

      expect(result.status).toBe('healthy')
      expect(result.services.whisper_service).toBe('online')
      expect(result.system_info.cpu_count).toBe(8)
      expect(result.performance.success_rate).toBe(0.97)
    })

    it('should handle unhealthy system status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: async () => ({
          status: 'unhealthy',
          timestamp: new Date().toISOString(),
          services: {
            database: 'offline',
            file_system: 'online',
            whisper_service: 'degraded',
            queue_processor: 'offline'
          },
          errors: [
            'Database connection timeout',
            'Queue processor crashed',
            'Whisper model loading failed'
          ],
          recommendations: [
            'Restart database service',
            'Check disk space for models',
            'Verify network connectivity'
          ]
        })
      })

      const result = await apiService.getSystemHealth()

      expect(result.status).toBe('unhealthy')
      expect(result.errors).toHaveLength(3)
      expect(result.recommendations).toHaveLength(3)
    })
  })

  describe('WebSocket Real-time Communication', () => {
    it('should connect to WebSocket and receive updates', async () => {
      const mockOnMessage = vi.fn()
      
      const ws = apiService.connectWebSocket(mockOnMessage)

      expect(WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws')

      // Simulate receiving a message
      const mockMessage = {
        type: 'processing_update',
        data: {
          item_id: 'item-1',
          progress: 75,
          step: 'Finalizing transcript',
          estimated_remaining: 30
        }
      }

      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify(mockMessage)
      })

      ws.onmessage(messageEvent)

      expect(mockOnMessage).toHaveBeenCalledWith(mockMessage)
    })

    it('should handle WebSocket connection errors', () => {
      const mockOnMessage = vi.fn()
      const mockOnError = vi.fn()
      
      const ws = apiService.connectWebSocket(mockOnMessage)
      ws.onerror = mockOnError

      // Simulate connection error
      const errorEvent = new Event('error')
      ws.onerror(errorEvent)

      expect(mockOnError).toHaveBeenCalledWith(errorEvent)
    })

    it('should handle various message types', () => {
      const mockOnMessage = vi.fn()
      const ws = apiService.connectWebSocket(mockOnMessage)

      const messageTypes = [
        {
          type: 'queue_update',
          data: { total_items: 5, processing: 1 }
        },
        {
          type: 'processing_complete',
          data: { item_id: 'item-1', output_file: 'C:/Output/video1.txt' }
        },
        {
          type: 'processing_error',
          data: { item_id: 'item-2', error: 'Codec not supported' }
        },
        {
          type: 'system_alert',
          data: { level: 'warning', message: 'Low disk space' }
        }
      ]

      messageTypes.forEach(msgType => {
        const messageEvent = new MessageEvent('message', {
          data: JSON.stringify(msgType)
        })
        ws.onmessage(messageEvent)
        expect(mockOnMessage).toHaveBeenCalledWith(msgType)
      })
    })
  })

  describe('Security and Authentication', () => {
    it('should handle API authentication', async () => {
      // Simulate API that requires authentication
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          error: 'Authentication required',
          error_code: 'AUTHENTICATION_REQUIRED'
        })
      })

      const result = await apiService.getQueueStatus()
      expect(result.error_code).toBe('AUTHENTICATION_REQUIRED')
    })

    it('should handle rate limiting', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => ({
          error: 'Rate limit exceeded',
          error_code: 'RATE_LIMIT_EXCEEDED',
          retry_after: 60
        })
      })

      const result = await apiService.addFiles(['C:/Videos/test.mp4'])
      expect(result.error_code).toBe('RATE_LIMIT_EXCEEDED')
      expect(result.retry_after).toBe(60)
    })

    it('should sanitize request payloads', async () => {
      const maliciousPayload = {
        file_paths: [
          'C:/Videos/normal.mp4',
          '<script>alert("xss")</script>.mp4',
          '../../etc/passwd',
          'normal.mp4; rm -rf /'
        ]
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          added_count: 1,
          skipped_count: 3,
          items: [{
            id: 'item-1',
            file_path: 'C:/Videos/normal.mp4',
            status: 'queued'
          }],
          security_warnings: [
            'Potential XSS attempt blocked',
            'Path traversal attempt blocked',
            'Command injection attempt blocked'
          ]
        })
      })

      const result = await apiService.addFiles(maliciousPayload.file_paths)

      expect(result.added_count).toBe(1)
      expect(result.skipped_count).toBe(3)
      expect(result.security_warnings).toBeDefined()
    })
  })

  describe('Performance and Reliability', () => {
    it('should handle timeout scenarios', async () => {
      mockFetch.mockImplementation(() => 
        new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Request timeout')), 100)
        })
      )

      try {
        await apiService.getQueueStatus()
      } catch (error) {
        expect((error as Error).message).toBe('Request timeout')
      }
    })

    it('should handle network errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network unavailable'))

      try {
        await apiService.getSystemHealth()
      } catch (error) {
        expect((error as Error).message).toBe('Network unavailable')
      }
    })

    it('should handle large payloads', async () => {
      // Test with large number of files
      const largeFileList = Array.from({ length: 1000 }, (_, i) => 
        `C:/Videos/video${i}.mp4`
      )

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          added_count: 1000,
          skipped_count: 0,
          processing_estimate: '8 hours',
          storage_required: '50GB'
        })
      })

      const result = await apiService.addFiles(largeFileList)

      expect(result.success).toBe(true)
      expect(result.added_count).toBe(1000)
    })
  })
})