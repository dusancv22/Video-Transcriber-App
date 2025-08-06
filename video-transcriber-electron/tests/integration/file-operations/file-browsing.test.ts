import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@mui/material/styles'
import { theme } from '../../../src/theme/theme'
import FileDropZone from '../../../src/components/FileDropZone'
import { useAppStore } from '../../../src/store/appStore'

// Mock the store
vi.mock('../../../src/store/appStore')

const mockUseAppStore = vi.mocked(useAppStore)

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
)

describe('File Browsing Integration Tests', () => {
  let mockAddFiles: ReturnType<typeof vi.fn>
  let mockShowOpenDialog: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()
    
    mockAddFiles = vi.fn()
    mockShowOpenDialog = vi.fn()

    // Reset mock store
    mockUseAppStore.mockReturnValue({
      addFiles: mockAddFiles,
      queueItems: [],
      removeFromQueue: vi.fn(),
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
        showOpenDialog: mockShowOpenDialog
      },
      shell: {
        showItemInFolder: vi.fn(),
        openExternal: vi.fn()
      },
      path: {
        join: vi.fn(),
        dirname: vi.fn(),
        basename: vi.fn(),
        resolve: vi.fn()
      },
      fs: {
        existsSync: vi.fn(),
        readFileSync: vi.fn(),
        writeFileSync: vi.fn()
      }
    }
  })

  describe('File Dialog Integration', () => {
    it('should open file dialog with correct parameters', async () => {
      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ['C:/Videos/test.mp4']
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      expect(mockShowOpenDialog).toHaveBeenCalledWith({
        properties: ['openFile', 'multiSelections'],
        filters: [
          { name: 'Video Files', extensions: ['mp4', 'avi', 'mkv', 'mov'] },
          { name: 'All Files', extensions: ['*'] }
        ],
        title: 'Select Video Files to Transcribe'
      })
    })

    it('should handle successful file selection', async () => {
      const selectedFiles = [
        'C:/Videos/video1.mp4',
        'C:/Videos/video2.avi',
        'C:/Videos/video3.mkv'
      ]

      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: selectedFiles
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      await waitFor(() => {
        expect(mockAddFiles).toHaveBeenCalledWith(selectedFiles)
      })

      expect(screen.getByText(/successfully added 3 file/i)).toBeInTheDocument()
    })

    it('should handle canceled file selection', async () => {
      mockShowOpenDialog.mockResolvedValue({
        canceled: true,
        filePaths: []
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      await waitFor(() => {
        expect(screen.getByText(/file selection canceled/i)).toBeInTheDocument()
      })

      expect(mockAddFiles).not.toHaveBeenCalled()
    })

    it('should handle empty file selection', async () => {
      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: []
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      await waitFor(() => {
        expect(screen.getByText(/no files were selected/i)).toBeInTheDocument()
      })

      expect(mockAddFiles).not.toHaveBeenCalled()
    })
  })

  describe('File Validation During Browse', () => {
    it('should filter out invalid file types', async () => {
      const mixedFiles = [
        'C:/Videos/video1.mp4',  // Valid
        'C:/Downloads/document.pdf',  // Invalid
        'C:/Videos/video2.avi',  // Valid
        'C:/Programs/malware.exe',  // Invalid
        'C:/Videos/video3.mkv'   // Valid
      ]

      const validFiles = [
        'C:/Videos/video1.mp4',
        'C:/Videos/video2.avi',
        'C:/Videos/video3.mkv'
      ]

      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: mixedFiles
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      await waitFor(() => {
        expect(mockAddFiles).toHaveBeenCalledWith(validFiles)
      })

      expect(screen.getByText(/2 file.*skipped.*only video files/i)).toBeInTheDocument()
      expect(screen.getByText(/successfully added 3 file/i)).toBeInTheDocument()
    })

    it('should reject all files if none are valid', async () => {
      const invalidFiles = [
        'C:/Downloads/document.pdf',
        'C:/Programs/app.exe',
        'C:/Documents/text.txt'
      ]

      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: invalidFiles
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      await waitFor(() => {
        expect(screen.getByText(/no valid video files selected/i)).toBeInTheDocument()
      })

      expect(mockAddFiles).not.toHaveBeenCalled()
    })

    it('should validate file extensions case-insensitively', async () => {
      const mixedCaseFiles = [
        'C:/Videos/video1.MP4',
        'C:/Videos/video2.AVI',
        'C:/Videos/video3.mkV',
        'C:/Videos/video4.MoV'
      ]

      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: mixedCaseFiles
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      await waitFor(() => {
        expect(mockAddFiles).toHaveBeenCalledWith(mixedCaseFiles)
      })

      expect(screen.getByText(/successfully added 4 file/i)).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should handle dialog API unavailability', async () => {
      global.window.electronAPI = undefined

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      await waitFor(() => {
        expect(screen.getByText(/desktop features not available/i)).toBeInTheDocument()
      })
    })

    it('should handle missing dialog method', async () => {
      global.window.electronAPI = {
        // Missing dialog property
        shell: {
          showItemInFolder: vi.fn(),
          openExternal: vi.fn()
        }
      } as any

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      await waitFor(() => {
        expect(screen.getByText(/file dialog not available/i)).toBeInTheDocument()
      })
    })

    it('should handle dialog errors gracefully', async () => {
      mockShowOpenDialog.mockRejectedValue(new Error('Permission denied'))

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      await waitFor(() => {
        expect(screen.getByText(/failed to open file browser/i)).toBeInTheDocument()
      })
    })

    it('should handle addFiles errors', async () => {
      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ['C:/Videos/test.mp4']
      })

      mockAddFiles.mockRejectedValue(new Error('Storage full'))

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      await waitFor(() => {
        expect(screen.getByText(/failed to add files.*storage full/i)).toBeInTheDocument()
      })
    })

    it('should handle network drive files', async () => {
      const networkFiles = [
        '\\\\server\\share\\video1.mp4',
        '\\\\networkdrive\\videos\\video2.avi'
      ]

      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: networkFiles
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      // Should handle network paths (may show warning or process normally)
      await waitFor(() => {
        expect(
          screen.getByText(/successfully added/i) ||
          screen.getByText(/network.*not.*supported/i) ||
          screen.getByText(/unc.*path/i)
        ).toBeInTheDocument()
      })
    })
  })

  describe('User Experience', () => {
    it('should show loading state during file selection', async () => {
      let resolveDialog: (value: any) => void
      const dialogPromise = new Promise(resolve => {
        resolveDialog = resolve
      })
      
      mockShowOpenDialog.mockReturnValue(dialogPromise)

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      // Should show loading state
      expect(screen.getByText('Loading...')).toBeInTheDocument()
      expect(browseButton).toBeDisabled()

      // Resolve dialog
      resolveDialog!({
        canceled: false,
        filePaths: ['C:/Videos/test.mp4']
      })

      await waitFor(() => {
        expect(screen.getByText('Browse Files')).toBeInTheDocument()
        expect(browseButton).toBeEnabled()
      })
    })

    it('should prevent multiple concurrent browse operations', async () => {
      let resolveDialog: (value: any) => void
      const dialogPromise = new Promise(resolve => {
        resolveDialog = resolve
      })
      
      mockShowOpenDialog.mockReturnValue(dialogPromise)

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      
      // First click
      await userEvent.click(browseButton)
      expect(browseButton).toBeDisabled()

      // Second click should be ignored
      await userEvent.click(browseButton)
      expect(mockShowOpenDialog).toHaveBeenCalledTimes(1)

      // Third click should show warning
      await userEvent.click(browseButton)
      expect(screen.getByText(/please wait.*current operation/i)).toBeInTheDocument()

      // Resolve first operation
      resolveDialog!({
        canceled: false,
        filePaths: ['C:/Videos/test.mp4']
      })

      await waitFor(() => {
        expect(browseButton).toBeEnabled()
      })
    })

    it('should provide clear feedback for different scenarios', async () => {
      // Test various scenarios with appropriate feedback
      const scenarios = [
        {
          result: { canceled: true, filePaths: [] },
          expectedMessage: /file selection canceled/i
        },
        {
          result: { canceled: false, filePaths: [] },
          expectedMessage: /no files were selected/i
        },
        {
          result: { canceled: false, filePaths: ['C:/Videos/test.mp4'] },
          expectedMessage: /successfully added 1 file/i
        },
        {
          result: { canceled: false, filePaths: ['C:/Videos/test1.mp4', 'C:/Videos/test2.avi'] },
          expectedMessage: /successfully added 2 file/i
        }
      ]

      for (const scenario of scenarios) {
        mockShowOpenDialog.mockResolvedValue(scenario.result)

        const { rerender } = render(
          <TestWrapper>
            <FileDropZone />
          </TestWrapper>
        )

        const browseButton = screen.getByText('Browse Files')
        await userEvent.click(browseButton)

        await waitFor(() => {
          expect(screen.getByText(scenario.expectedMessage)).toBeInTheDocument()
        })

        // Clean up for next iteration
        rerender(<div />)
      }
    })

    it('should handle rapid user interactions gracefully', async () => {
      mockShowOpenDialog.mockImplementation(() => 
        Promise.resolve({
          canceled: false,
          filePaths: ['C:/Videos/test.mp4']
        })
      )

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')

      // Rapidly click browse button
      const clickPromises = Array.from({ length: 5 }, () => userEvent.click(browseButton))
      await Promise.all(clickPromises)

      // Should handle gracefully without crashing
      expect(() => {
        // Component should still be functional
        expect(browseButton).toBeInTheDocument()
      }).not.toThrow()
    })
  })

  describe('Accessibility', () => {
    it('should be keyboard accessible', async () => {
      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ['C:/Videos/test.mp4']
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      
      // Focus and activate with keyboard
      browseButton.focus()
      expect(browseButton).toHaveFocus()

      // Press Enter to activate
      await userEvent.keyboard('{Enter}')

      expect(mockShowOpenDialog).toHaveBeenCalled()
    })

    it('should have proper ARIA attributes', () => {
      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      expect(browseButton).toBeInTheDocument()
      
      // Check for accessibility attributes
      const dropZone = screen.getByText('Drop video files here').closest('[class*="drop-zone"]')
      expect(dropZone).toBeInTheDocument()
      
      // Should be focusable and have proper role
      expect(browseButton.tagName).toBe('BUTTON')
    })

    it('should announce status changes to screen readers', async () => {
      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ['C:/Videos/test.mp4']
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      await waitFor(() => {
        // Success message should be announced
        const successMessage = screen.getByText(/successfully added/i)
        expect(successMessage).toBeInTheDocument()
        
        // Should have role="alert" or similar for screen readers
        const alert = screen.getByRole('alert')
        expect(alert).toBeInTheDocument()
      })
    })
  })
})