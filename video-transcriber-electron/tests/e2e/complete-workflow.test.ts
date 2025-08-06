import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@mui/material/styles'
import { theme } from '../../src/theme/theme'
import FileDropZone from '../../src/components/FileDropZone'
import QueuePanel from '../../src/components/QueuePanel'
import SettingsDialog from '../../src/components/SettingsDialog'
import { useAppStore } from '../../src/store/appStore'
import { QueueItem } from '../../src/types/api'

// Mock the store
vi.mock('../../src/store/appStore')

const mockUseAppStore = vi.mocked(useAppStore)

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
)

// Mock WebSocket for real-time updates
const mockWebSocket = {
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  readyState: WebSocket.OPEN
}

// Mock backend API responses
const mockApiResponses = {
  validateOutputDirectory: vi.fn(),
  startProcessing: vi.fn(),
  getQueueStatus: vi.fn()
}

describe('End-to-End Complete Workflow Tests', () => {
  let mockAddFiles: ReturnType<typeof vi.fn>
  let mockRemoveFromQueue: ReturnType<typeof vi.fn>
  let mockSetProcessingOptions: ReturnType<typeof vi.fn>
  let mockShowOpenDialog: ReturnType<typeof vi.fn>
  let mockShell: {
    showItemInFolder: ReturnType<typeof vi.fn>
    openExternal: ReturnType<typeof vi.fn>
  }

  const initialProcessingOptions = {
    output_directory: 'C:/Output/Transcripts',
    whisper_model: 'large' as const,
    language: 'en' as const,
    output_format: 'txt' as const
  }

  beforeEach(() => {
    vi.clearAllMocks()
    
    mockAddFiles = vi.fn()
    mockRemoveFromQueue = vi.fn()
    mockSetProcessingOptions = vi.fn()
    mockShowOpenDialog = vi.fn()
    mockShell = {
      showItemInFolder: vi.fn(),
      openExternal: vi.fn()
    }

    // Reset mock store
    mockUseAppStore.mockReturnValue({
      addFiles: mockAddFiles,
      queueItems: [],
      removeFromQueue: mockRemoveFromQueue,
      processingOptions: initialProcessingOptions,
      setProcessingOptions: mockSetProcessingOptions
    })

    // Mock Electron APIs
    global.window.electronAPI = {
      dialog: {
        showOpenDialog: mockShowOpenDialog
      },
      shell: mockShell,
      path: {
        join: vi.fn(),
        dirname: vi.fn(),
        basename: vi.fn(),
        resolve: vi.fn()
      },
      fs: {
        existsSync: vi.fn().mockReturnValue(true),
        readFileSync: vi.fn(),
        writeFileSync: vi.fn()
      }
    }

    // Mock clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined)
      }
    })

    // Mock WebSocket
    global.WebSocket = vi.fn(() => mockWebSocket) as any

    // Mock fetch for API calls
    global.fetch = vi.fn()
  })

  describe('Complete Video Transcription Workflow', () => {
    it('should complete full workflow: configure settings -> add files -> process -> view results', async () => {
      const user = userEvent.setup()

      // Stage 1: Configure Settings
      const { rerender } = render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      // Modify output directory
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await user.clear(directoryInput)
      await user.type(directoryInput, 'C:/Custom/Transcripts')

      // Change whisper model for faster processing
      const modelSelect = screen.getByText('Large').closest('[role="combobox"]')
      await user.click(modelSelect!)
      await user.click(screen.getByText('Medium'))

      // Change output format to SRT
      const formatSelect = screen.getByText('Plain Text (.txt)').closest('[role="combobox"]')
      await user.click(formatSelect!)
      await user.click(screen.getByText('SubRip (.srt)'))

      // Save settings
      const saveButton = screen.getByText('Save Changes')
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockSetProcessingOptions).toHaveBeenCalledWith({
          output_directory: 'C:/Custom/Transcripts',
          whisper_model: 'medium',
          language: 'en',
          output_format: 'srt'
        })
      })

      // Update store to reflect saved settings
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: {
          output_directory: 'C:/Custom/Transcripts',
          whisper_model: 'medium' as const,
          language: 'en' as const,
          output_format: 'srt' as const
        }
      })

      // Stage 2: Add Files via File Browser
      rerender(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: [
          'C:/Videos/interview.mp4',
          'C:/Videos/presentation.avi',
          'C:/Videos/meeting.mkv'
        ]
      })

      const browseButton = screen.getByText('Browse Files')
      await user.click(browseButton)

      await waitFor(() => {
        expect(mockAddFiles).toHaveBeenCalledWith([
          'C:/Videos/interview.mp4',
          'C:/Videos/presentation.avi',
          'C:/Videos/meeting.mkv'
        ])
      })

      expect(screen.getByText(/successfully added 3 file/i)).toBeInTheDocument()

      // Stage 3: Monitor Processing Progress
      const queueItems: QueueItem[] = [
        {
          id: '1',
          file_path: 'C:/Videos/interview.mp4',
          status: 'processing',
          progress: 25,
          processing_time: 60,
          estimated_time_remaining: 180,
          current_step: 'Converting audio format',
          file_size: 156789012,
          duration: 1800, // 30 minutes
          format: 'MP4',
          created_at: '2025-01-06T10:00:00Z'
        },
        {
          id: '2',
          file_path: 'C:/Videos/presentation.avi',
          status: 'queued',
          progress: 0,
          file_size: 89456123,
          duration: 3600, // 1 hour
          format: 'AVI',
          created_at: '2025-01-06T10:01:00Z'
        },
        {
          id: '3',
          file_path: 'C:/Videos/meeting.mkv',
          status: 'queued',
          progress: 0,
          file_size: 234567890,
          duration: 2700, // 45 minutes
          format: 'MKV',
          created_at: '2025-01-06T10:02:00Z'
        }
      ]

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        queueItems
      })

      rerender(
        <TestWrapper>
          <QueuePanel />
        </TestWrapper>
      )

      // Verify processing status is shown
      expect(screen.getByText('Processing')).toBeInTheDocument()
      expect(screen.getByText('25%')).toBeInTheDocument()
      expect(screen.getByText('Converting audio format')).toBeInTheDocument()
      expect(screen.getByText(/3min left/)).toBeInTheDocument()

      // Verify queued items
      expect(screen.getAllByText('Queued')).toHaveLength(2)

      // Stage 4: Simulate Processing Completion
      const completedItems: QueueItem[] = [
        {
          id: '1',
          file_path: 'C:/Videos/interview.mp4',
          status: 'completed',
          progress: 100,
          processing_time: 420, // 7 minutes
          output_file: 'C:/Custom/Transcripts/interview.srt',
          file_size: 156789012,
          duration: 1800,
          format: 'MP4',
          created_at: '2025-01-06T10:00:00Z',
          completed_at: '2025-01-06T10:07:00Z'
        },
        {
          id: '2',
          file_path: 'C:/Videos/presentation.avi',
          status: 'processing',
          progress: 65,
          processing_time: 300,
          estimated_time_remaining: 160,
          current_step: 'Transcribing audio segments (chunk 3/5)',
          file_size: 89456123,
          duration: 3600,
          format: 'AVI',
          created_at: '2025-01-06T10:01:00Z'
        },
        {
          id: '3',
          file_path: 'C:/Videos/meeting.mkv',
          status: 'queued',
          progress: 0,
          file_size: 234567890,
          duration: 2700,
          format: 'MKV',
          created_at: '2025-01-06T10:02:00Z'
        }
      ]

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        queueItems: completedItems
      })

      rerender(
        <TestWrapper>
          <QueuePanel />
        </TestWrapper>
      )

      // Stage 5: View Results and Perform File Operations
      expect(screen.getByText('Completed')).toBeInTheDocument()
      expect(screen.getByText(/completed in.*minutes/i)).toBeInTheDocument()
      expect(screen.getByText('C:/Custom/Transcripts/interview.srt')).toBeInTheDocument()

      // Test quick actions for completed file
      const openTranscriptButton = screen.getByLabelText(/open transcript file/i)
      await user.click(openTranscriptButton)

      expect(mockShell.openExternal).toHaveBeenCalledWith('file://C:/Custom/Transcripts/interview.srt')

      const showFolderButton = screen.getByLabelText(/show transcript folder/i)
      await user.click(showFolderButton)

      expect(mockShell.showItemInFolder).toHaveBeenCalledWith('C:/Custom/Transcripts/interview.srt')

      // Test more actions menu
      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await user.click(moreButton)

      const copyPathAction = screen.getByText('Copy Output Path')
      await user.click(copyPathAction)

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('C:/Custom/Transcripts/interview.srt')

      // Verify success notification
      await waitFor(() => {
        expect(screen.getByText(/transcript file path copied/i)).toBeInTheDocument()
      })
    })

    it('should handle error recovery workflow', async () => {
      const user = userEvent.setup()

      // Start with a failed item
      const failedItem: QueueItem = {
        id: '1',
        file_path: 'C:/Videos/corrupted.mp4',
        status: 'failed',
        progress: 0,
        error: 'Audio extraction failed: Codec not supported',
        error_code: 'UNSUPPORTED_CODEC',
        file_size: 123456789,
        format: 'MP4',
        created_at: '2025-01-06T10:00:00Z'
      }

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        queueItems: [failedItem]
      })

      render(
        <TestWrapper>
          <QueuePanel />
        </TestWrapper>
      )

      // Verify error is displayed
      expect(screen.getByText('Failed')).toBeInTheDocument()
      expect(screen.getByText('Audio extraction failed: Codec not supported')).toBeInTheDocument()

      // Access error details
      const moreButton = screen.getByLabelText(/more actions/i)
      await user.click(moreButton)

      const showErrorAction = screen.getByText('Show Error Details')
      await user.click(showErrorAction)

      // Error dialog should appear
      expect(screen.getByText('Error Details')).toBeInTheDocument()
      expect(screen.getByText('Audio extraction failed: Codec not supported')).toBeInTheDocument()

      // Close error dialog
      const closeErrorButton = screen.getByText('Confirm')
      await user.click(closeErrorButton)

      // Try retry operation
      await user.click(moreButton)
      const retryAction = screen.getByText('Retry Processing')
      await user.click(retryAction)

      // Should show retry feedback
      expect(screen.getByText(/retry functionality/i)).toBeInTheDocument()

      // Remove failed file from queue
      await user.click(moreButton)
      const removeAction = screen.getByText('Remove from Queue')
      await user.click(removeAction)

      // Confirm removal
      expect(screen.getByText('Remove File')).toBeInTheDocument()
      expect(screen.getByText(/corrupted.mp4.*queue/i)).toBeInTheDocument()

      const confirmButton = screen.getByText('Confirm')
      await user.click(confirmButton)

      expect(mockRemoveFromQueue).toHaveBeenCalledWith('1')

      await waitFor(() => {
        expect(screen.getByText(/file removed from queue/i)).toBeInTheDocument()
      })
    })

    it('should handle batch processing workflow', async () => {
      const user = userEvent.setup()

      // Add multiple files via drag and drop
      const testFiles = [
        new File(['video1'], 'video1.mp4', { type: 'video/mp4' }),
        new File(['video2'], 'video2.avi', { type: 'video/x-msvideo' }),
        new File(['video3'], 'video3.mkv', { type: 'video/x-matroska' }),
        new File(['invalid'], 'document.pdf', { type: 'application/pdf' })
      ]

      // Set file paths for mock
      testFiles.forEach((file, index) => {
        if (index < 3) { // Only video files
          Object.defineProperty(file, 'path', {
            value: `C:/Videos/${file.name}`,
            writable: false
          })
        }
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const dropZone = screen.getByText('Drop video files here').closest('[class*="drop-zone"]')

      // Simulate drop
      const mockDataTransfer = {
        files: testFiles,
        items: [],
        types: ['Files']
      }

      await user.pointer([
        { target: dropZone },
        { keys: '[MouseLeft>]', target: dropZone },
        '[/MouseLeft]'
      ])

      // Mock the drop event since jsdom doesn't fully support drag/drop
      const dropEvent = new DragEvent('drop', {
        bubbles: true,
        cancelable: true,
        dataTransfer: mockDataTransfer as any
      })

      Object.defineProperty(dropEvent, 'dataTransfer', {
        value: mockDataTransfer,
        writable: false
      })

      dropZone!.dispatchEvent(dropEvent)

      await waitFor(() => {
        expect(mockAddFiles).toHaveBeenCalledWith([
          'C:/Videos/video1.mp4',
          'C:/Videos/video2.avi',
          'C:/Videos/video3.mkv'
        ])
      })

      // Should show feedback about valid/invalid files
      expect(screen.getByText(/1 file.*skipped.*only video files/i)).toBeInTheDocument()
      expect(screen.getByText(/successfully added 3 file/i)).toBeInTheDocument()

      // Simulate batch processing progress
      const batchItems: QueueItem[] = [
        {
          id: '1',
          file_path: 'C:/Videos/video1.mp4',
          status: 'completed',
          progress: 100,
          processing_time: 180,
          output_file: 'C:/Output/Transcripts/video1.txt',
          file_size: 50000000,
          duration: 600,
          format: 'MP4',
          created_at: '2025-01-06T10:00:00Z',
          completed_at: '2025-01-06T10:03:00Z'
        },
        {
          id: '2',
          file_path: 'C:/Videos/video2.avi',
          status: 'processing',
          progress: 80,
          processing_time: 240,
          estimated_time_remaining: 60,
          current_step: 'Finalizing transcript',
          file_size: 75000000,
          duration: 900,
          format: 'AVI',
          created_at: '2025-01-06T10:01:00Z'
        },
        {
          id: '3',
          file_path: 'C:/Videos/video3.mkv',
          status: 'queued',
          progress: 0,
          file_size: 100000000,
          duration: 1200,
          format: 'MKV',
          created_at: '2025-01-06T10:02:00Z'
        }
      ]

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        queueItems: batchItems
      })

      const { rerender } = render(
        <TestWrapper>
          <QueuePanel />
        </TestWrapper>
      )

      rerender(
        <TestWrapper>
          <QueuePanel />
        </TestWrapper>
      )

      // Verify batch status display
      expect(screen.getByText('Completed')).toBeInTheDocument()
      expect(screen.getByText('Processing')).toBeInTheDocument()
      expect(screen.getByText('Queued')).toBeInTheDocument()

      // Test batch operations
      const completedFileButton = screen.getByLabelText(/open transcript file/i)
      await user.click(completedFileButton)

      expect(mockShell.openExternal).toHaveBeenCalledWith('file://C:/Output/Transcripts/video1.txt')

      // Verify processing progress
      expect(screen.getByText('80%')).toBeInTheDocument()
      expect(screen.getByText('Finalizing transcript')).toBeInTheDocument()
      expect(screen.getByText(/1min left/)).toBeInTheDocument()
    })

    it('should handle settings persistence across sessions', async () => {
      const user = userEvent.setup()

      // First session - modify settings
      const { rerender } = render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      // Change multiple settings
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await user.clear(directoryInput)
      await user.type(directoryInput, 'D:/MyTranscripts')

      const languageSelect = screen.getByText('English Only').closest('[role="combobox"]')
      await user.click(languageSelect!)
      await user.click(screen.getByText('Auto-detect'))

      const formatSelect = screen.getByText('Plain Text (.txt)').closest('[role="combobox"]')
      await user.click(formatSelect!)
      await user.click(screen.getByText('WebVTT (.vtt)'))

      // Save settings
      const saveButton = screen.getByText('Save Changes')
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockSetProcessingOptions).toHaveBeenCalledWith({
          output_directory: 'D:/MyTranscripts',
          whisper_model: 'large',
          language: 'auto',
          output_format: 'vtt'
        })
      })

      // Simulate app restart - new session with persisted settings
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: {
          output_directory: 'D:/MyTranscripts',
          whisper_model: 'large' as const,
          language: 'auto' as const,
          output_format: 'vtt' as const
        }
      })

      rerender(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      // Verify settings are restored
      expect(screen.getByDisplayValue('D:/MyTranscripts')).toBeInTheDocument()
      expect(screen.getByText('Large')).toBeInTheDocument()
      expect(screen.getByText('Auto-detect')).toBeInTheDocument()
      expect(screen.getByText('WebVTT (.vtt)')).toBeInTheDocument()

      // Test reset functionality
      const resetButton = screen.getByText('Reset to Defaults')
      await user.click(resetButton)

      // Should show default values
      expect(screen.getByDisplayValue('C:/Output/Transcripts')).toBeInTheDocument()
      expect(screen.getByText('English Only')).toBeInTheDocument()
      expect(screen.getByText('Plain Text (.txt)')).toBeInTheDocument()

      // Save reset values
      const saveResetButton = screen.getByText('Save Changes')
      await user.click(saveResetButton)

      await waitFor(() => {
        expect(mockSetProcessingOptions).toHaveBeenLastCalledWith(initialProcessingOptions)
      })
    })
  })

  describe('Error Scenarios and Edge Cases', () => {
    it('should handle service unavailability gracefully', async () => {
      const user = userEvent.setup()

      // Mock service unavailable
      global.window.electronAPI = undefined

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await user.click(browseButton)

      await waitFor(() => {
        expect(screen.getByText(/desktop features not available/i)).toBeInTheDocument()
      })

      // App should still function with reduced capabilities
      expect(screen.getByText('Drop video files here')).toBeInTheDocument()
    })

    it('should handle storage full scenarios', async () => {
      const user = userEvent.setup()

      // Mock storage full error
      mockAddFiles.mockRejectedValue(new Error('Storage full - unable to add files'))
      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ['C:/Videos/large-file.mp4']
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await user.click(browseButton)

      await waitFor(() => {
        expect(screen.getByText(/storage full.*unable to add files/i)).toBeInTheDocument()
      })

      // User should be able to retry or take corrective action
      expect(browseButton).toBeEnabled() // Can try again
    })

    it('should handle network interruptions during processing', async () => {
      // Simulate WebSocket connection loss
      const mockWebSocketError = {
        ...mockWebSocket,
        readyState: WebSocket.CLOSED
      }

      global.WebSocket = vi.fn(() => mockWebSocketError) as any

      const processingItem: QueueItem = {
        id: '1',
        file_path: 'C:/Videos/test.mp4',
        status: 'processing',
        progress: 50,
        processing_time: 120,
        estimated_time_remaining: 120,
        current_step: 'Processing audio...',
        file_size: 100000000,
        format: 'MP4',
        created_at: '2025-01-06T10:00:00Z'
      }

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        queueItems: [processingItem]
      })

      render(
        <TestWrapper>
          <QueuePanel />
        </TestWrapper>
      )

      // Should show processing state even with connection issues
      expect(screen.getByText('Processing')).toBeInTheDocument()
      expect(screen.getByText('50%')).toBeInTheDocument()

      // User should be able to interact with available features
      const moreButton = screen.getByLabelText(/more actions/i)
      await userEvent.click(moreButton)

      expect(screen.getByText('Show Input File')).toBeInTheDocument()
    })

    it('should handle concurrent user operations', async () => {
      const user = userEvent.setup()

      // Set up multiple operations happening simultaneously
      const testItems: QueueItem[] = [
        {
          id: '1',
          file_path: 'C:/Videos/video1.mp4',
          status: 'completed',
          progress: 100,
          output_file: 'C:/Output/video1.txt',
          file_size: 50000000,
          format: 'MP4',
          created_at: '2025-01-06T10:00:00Z'
        },
        {
          id: '2',
          file_path: 'C:/Videos/video2.avi',
          status: 'completed',
          progress: 100,
          output_file: 'C:/Output/video2.txt',
          file_size: 60000000,
          format: 'AVI',
          created_at: '2025-01-06T10:01:00Z'
        }
      ]

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        queueItems: testItems
      })

      render(
        <TestWrapper>
          <QueuePanel />
        </TestWrapper>
      )

      // Perform multiple concurrent operations
      const moreButtons = screen.getAllByLabelText(/more actions/i)
      
      // Click multiple more buttons simultaneously
      const clickPromises = moreButtons.map(button => user.click(button))
      await Promise.allSettled(clickPromises)

      // Should handle gracefully without crashes
      expect(() => {
        expect(screen.getByText('Copy Output Path')).toBeInTheDocument()
      }).not.toThrow()

      // Perform file operations on multiple items
      const copyActions = screen.getAllByText('Copy Output Path')
      const copyPromises = copyActions.slice(0, 2).map(action => user.click(action))
      
      await Promise.allSettled(copyPromises)

      // Should handle concurrent clipboard operations
      expect(navigator.clipboard.writeText).toHaveBeenCalledTimes(2)
    })
  })
})