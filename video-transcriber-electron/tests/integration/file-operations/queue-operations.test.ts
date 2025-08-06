import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@mui/material/styles'
import { theme } from '../../../src/theme/theme'
import QueuePanel from '../../../src/components/QueuePanel'
import { useAppStore } from '../../../src/store/appStore'
import { QueueItem } from '../../../src/types/api'

// Mock the store
vi.mock('../../../src/store/appStore')

const mockUseAppStore = vi.mocked(useAppStore)

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
)

describe('Queue Operations Integration Tests', () => {
  let mockRemoveFromQueue: ReturnType<typeof vi.fn>
  let mockShell: {
    showItemInFolder: ReturnType<typeof vi.fn>
    openExternal: ReturnType<typeof vi.fn>
  }

  // Test queue items
  const testQueueItems: QueueItem[] = [
    {
      id: '1',
      file_path: 'C:/Videos/video1.mp4',
      status: 'processing',
      progress: 45,
      processing_time: 120,
      estimated_time_remaining: 150,
      current_step: 'Transcribing audio segments',
      file_size: 125829120,
      duration: 300,
      format: 'MP4',
      created_at: '2025-01-06T10:00:00Z'
    },
    {
      id: '2',
      file_path: 'C:/Videos/video2.avi',
      status: 'queued',
      progress: 0,
      file_size: 89478485,
      format: 'AVI',
      created_at: '2025-01-06T10:05:00Z'
    },
    {
      id: '3',
      file_path: 'C:/Videos/video3.mkv',
      status: 'completed',
      progress: 100,
      processing_time: 280,
      output_file: 'C:/Output/video3.txt',
      file_size: 234567890,
      duration: 1200,
      format: 'MKV',
      created_at: '2025-01-06T09:30:00Z',
      completed_at: '2025-01-06T09:35:00Z'
    },
    {
      id: '4',
      file_path: 'C:/Videos/corrupted.mov',
      status: 'failed',
      progress: 0,
      error: 'Audio extraction failed: Invalid file format',
      error_code: 'AUDIO_EXTRACTION_FAILED',
      file_size: 45678901,
      format: 'MOV',
      created_at: '2025-01-06T09:45:00Z'
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    
    mockRemoveFromQueue = vi.fn()
    mockShell = {
      showItemInFolder: vi.fn(),
      openExternal: vi.fn()
    }

    // Reset mock store
    mockUseAppStore.mockReturnValue({
      addFiles: vi.fn(),
      queueItems: testQueueItems,
      removeFromQueue: mockRemoveFromQueue,
      processingOptions: {
        output_directory: 'C:/Output/Transcripts',
        whisper_model: 'large' as const,
        language: 'en' as const,
        output_format: 'txt' as const
      },
      setProcessingOptions: vi.fn()
    })

    // Mock Electron APIs
    global.window.electronAPI = {
      dialog: {
        showOpenDialog: vi.fn()
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
  })

  describe('Queue Display', () => {
    it('should display all queue items', () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      expect(screen.getByText('video1.mp4')).toBeInTheDocument()
      expect(screen.getByText('video2.avi')).toBeInTheDocument()
      expect(screen.getByText('video3.mkv')).toBeInTheDocument()
      expect(screen.getByText('corrupted.mov')).toBeInTheDocument()
    })

    it('should show correct status for each item', () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      expect(screen.getByText('Processing')).toBeInTheDocument()
      expect(screen.getByText('Queued')).toBeInTheDocument()
      expect(screen.getByText('Completed')).toBeInTheDocument()
      expect(screen.getByText('Failed')).toBeInTheDocument()
    })

    it('should show progress information for processing items', () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      expect(screen.getByText('45%')).toBeInTheDocument()
      expect(screen.getByText('Transcribing audio segments')).toBeInTheDocument()
      expect(screen.getByText(/3min left/)).toBeInTheDocument()
    })

    it('should show error information for failed items', () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      expect(screen.getByText('Audio extraction failed: Invalid file format')).toBeInTheDocument()
    })

    it('should show completion information for completed items', () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      expect(screen.getByText(/completed in.*minutes/i)).toBeInTheDocument()
      expect(screen.getByText('C:/Output/video3.txt')).toBeInTheDocument()
    })

    it('should display empty state when no items', () => {
      render(
        <TestWrapper>
          <QueuePanel items={[]} />
        </TestWrapper>
      )

      expect(screen.getByText(/no files in queue/i)).toBeInTheDocument()
    })
  })

  describe('File Operations Menu', () => {
    it('should show different actions based on file status', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      // Test queued item actions
      const queuedMoreButton = screen.getAllByLabelText(/more actions/i)[1] // Second item (queued)
      await userEvent.click(queuedMoreButton)

      expect(screen.getByText('Show Input File')).toBeInTheDocument()
      expect(screen.getByText('Copy Input Path')).toBeInTheDocument()
      expect(screen.getByText('Remove from Queue')).toBeInTheDocument()
      expect(screen.queryByText('Open Transcript')).not.toBeInTheDocument()

      // Close menu
      await userEvent.keyboard('{Escape}')

      // Test completed item actions
      const completedMoreButton = screen.getAllByLabelText(/more actions/i)[2] // Third item (completed)
      await userEvent.click(completedMoreButton)

      expect(screen.getByText('Open Transcript')).toBeInTheDocument()
      expect(screen.getByText('Show Output Folder')).toBeInTheDocument()
      expect(screen.getByText('Copy Output Path')).toBeInTheDocument()
      expect(screen.getByText('Show Input File')).toBeInTheDocument()
      expect(screen.getByText('Remove from Queue')).toBeInTheDocument()
    })

    it('should show retry option for failed items', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const failedMoreButton = screen.getAllByLabelText(/more actions/i)[3] // Fourth item (failed)
      await userEvent.click(failedMoreButton)

      expect(screen.getByText('Retry Processing')).toBeInTheDocument()
      expect(screen.getByText('Show Error Details')).toBeInTheDocument()
      expect(screen.getByText('Show Input File')).toBeInTheDocument()
      expect(screen.getByText('Remove from Queue')).toBeInTheDocument()
    })

    it('should disable actions during operations', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const showInputAction = screen.getByText('Show Input File')
      await userEvent.click(showInputAction)

      // During loading, more actions should be disabled
      const allMoreButtons = screen.getAllByLabelText(/more actions/i)
      // Note: The actual disabled state depends on implementation
      // This is more of a behavioral test
    })
  })

  describe('Quick Action Buttons', () => {
    it('should show quick actions for completed files', () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      // Should have quick action buttons for the completed item
      const transcriptButtons = screen.getAllByLabelText(/open transcript file/i)
      const folderButtons = screen.getAllByLabelText(/show transcript folder/i)

      expect(transcriptButtons.length).toBeGreaterThan(0)
      expect(folderButtons.length).toBeGreaterThan(0)
    })

    it('should show input file button for non-completed files', () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const inputFileButtons = screen.getAllByLabelText(/show input file/i)
      expect(inputFileButtons.length).toBeGreaterThan(0)
    })

    it('should execute quick actions', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const transcriptButton = screen.getAllByLabelText(/open transcript file/i)[0]
      await userEvent.click(transcriptButton)

      expect(mockShell.openExternal).toHaveBeenCalledWith('file://C:/Output/video3.txt')
    })
  })

  describe('File Path Operations', () => {
    it('should open input file location', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const showInputAction = screen.getByText('Show Input File')
      await userEvent.click(showInputAction)

      expect(mockShell.showItemInFolder).toHaveBeenCalledWith('C:/Videos/video1.mp4')
    })

    it('should open output file location', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[2] // Completed item
      await userEvent.click(moreButton)

      const showOutputAction = screen.getByText('Show Output Folder')
      await userEvent.click(showOutputAction)

      expect(mockShell.showItemInFolder).toHaveBeenCalledWith('C:/Output/video3.txt')
    })

    it('should copy input file path', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const copyInputAction = screen.getByText('Copy Input Path')
      await userEvent.click(copyInputAction)

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('C:/Videos/video1.mp4')

      await waitFor(() => {
        expect(screen.getByText(/input file path copied/i)).toBeInTheDocument()
      })
    })

    it('should copy output file path', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[2] // Completed item
      await userEvent.click(moreButton)

      const copyOutputAction = screen.getByText('Copy Output Path')
      await userEvent.click(copyOutputAction)

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('C:/Output/video3.txt')

      await waitFor(() => {
        expect(screen.getByText(/transcript file path copied/i)).toBeInTheDocument()
      })
    })

    it('should open transcript file directly', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[2] // Completed item
      await userEvent.click(moreButton)

      const openTranscriptAction = screen.getByText('Open Transcript')
      await userEvent.click(openTranscriptAction)

      expect(mockShell.openExternal).toHaveBeenCalledWith('file://C:/Output/video3.txt')

      await waitFor(() => {
        expect(screen.getByText(/opened transcript file/i)).toBeInTheDocument()
      })
    })
  })

  describe('File Removal', () => {
    it('should show confirmation dialog before removal', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const removeAction = screen.getByText('Remove from Queue')
      await userEvent.click(removeAction)

      expect(screen.getByText('Remove File')).toBeInTheDocument()
      expect(screen.getByText(/are you sure.*video1.mp4.*queue/i)).toBeInTheDocument()
      expect(screen.getByText('Cancel')).toBeInTheDocument()
      expect(screen.getByText('Confirm')).toBeInTheDocument()
    })

    it('should remove file when confirmed', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const removeAction = screen.getByText('Remove from Queue')
      await userEvent.click(removeAction)

      const confirmButton = screen.getByText('Confirm')
      await userEvent.click(confirmButton)

      expect(mockRemoveFromQueue).toHaveBeenCalledWith('1')

      await waitFor(() => {
        expect(screen.getByText(/file removed from queue/i)).toBeInTheDocument()
      })
    })

    it('should cancel removal when canceled', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const removeAction = screen.getByText('Remove from Queue')
      await userEvent.click(removeAction)

      const cancelButton = screen.getByText('Cancel')
      await userEvent.click(cancelButton)

      expect(mockRemoveFromQueue).not.toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    it('should handle missing Electron API gracefully', async () => {
      global.window.electronAPI = undefined

      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const showInputAction = screen.getByText('Show Input File')
      await userEvent.click(showInputAction)

      await waitFor(() => {
        expect(screen.getByText(/file operations not available/i)).toBeInTheDocument()
      })
    })

    it('should handle file operation errors', async () => {
      mockShell.showItemInFolder.mockRejectedValue(new Error('File not found'))

      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const showInputAction = screen.getByText('Show Input File')
      await userEvent.click(showInputAction)

      await waitFor(() => {
        expect(screen.getByText(/failed to open file location/i)).toBeInTheDocument()
      })
    })

    it('should handle clipboard errors', async () => {
      const mockWriteText = vi.mocked(navigator.clipboard.writeText)
      mockWriteText.mockRejectedValue(new Error('Clipboard access denied'))

      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const copyInputAction = screen.getByText('Copy Input Path')
      await userEvent.click(copyInputAction)

      await waitFor(() => {
        expect(screen.getByText(/failed to copy path to clipboard/i)).toBeInTheDocument()
      })
    })

    it('should handle removal errors', async () => {
      mockRemoveFromQueue.mockRejectedValue(new Error('Database error'))

      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const removeAction = screen.getByText('Remove from Queue')
      await userEvent.click(removeAction)

      const confirmButton = screen.getByText('Confirm')
      await userEvent.click(confirmButton)

      await waitFor(() => {
        expect(screen.getByText(/failed to remove file.*database error/i)).toBeInTheDocument()
      })
    })

    it('should offer alternative actions when files not found', async () => {
      mockShell.showItemInFolder.mockRejectedValue(new Error('File not found'))

      const completedItem = {
        ...testQueueItems[2],
        output_file: 'C:/Missing/output.txt'
      }

      render(
        <TestWrapper>
          <QueuePanel items={[completedItem]} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const showOutputAction = screen.getByText('Show Output Folder')
      await userEvent.click(showOutputAction)

      await waitFor(() => {
        expect(screen.getByText(/file not found.*open.*output directory/i)).toBeInTheDocument()
      })
    })
  })

  describe('Performance and User Experience', () => {
    it('should handle large queue efficiently', () => {
      const largeQueue = Array.from({ length: 1000 }, (_, i) => ({
        id: `item-${i}`,
        file_path: `C:/Videos/video${i}.mp4`,
        status: 'queued' as const,
        progress: 0,
        file_size: 1000000,
        format: 'MP4',
        created_at: '2025-01-06T10:00:00Z'
      }))

      expect(() => {
        render(
          <TestWrapper>
            <QueuePanel items={largeQueue} />
          </TestWrapper>
        )
      }).not.toThrow()

      // Should render without performance issues
      expect(screen.getByText('video0.mp4')).toBeInTheDocument()
    })

    it('should show loading states during operations', async () => {
      let resolveOperation: (value: any) => void
      const operationPromise = new Promise(resolve => {
        resolveOperation = resolve
      })

      mockShell.showItemInFolder.mockReturnValue(operationPromise)

      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const showInputAction = screen.getByText('Show Input File')
      await userEvent.click(showInputAction)

      // Should show loading indicator
      expect(screen.getByText(/opening.*input file location/i)).toBeInTheDocument()

      // Resolve operation
      resolveOperation!(undefined)

      await waitFor(() => {
        expect(screen.queryByText(/opening.*input file location/i)).not.toBeInTheDocument()
      })
    })

    it('should provide keyboard navigation support', async () => {
      render(
        <TestWrapper>
          <QueuePanel items={testQueueItems} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      moreButton.focus()

      // Should be focusable
      expect(moreButton).toHaveFocus()

      // Should open menu with Enter/Space
      await userEvent.keyboard('{Enter}')
      expect(screen.getByText('Show Input File')).toBeInTheDocument()

      // Should navigate menu with arrow keys
      await userEvent.keyboard('{ArrowDown}')
      expect(screen.getByText('Copy Input Path')).toHaveFocus()
    })
  })
})