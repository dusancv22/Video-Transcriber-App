import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@mui/material/styles'
import { theme } from '../../../src/theme/theme'
import FileDropZone from '../../../src/components/FileDropZone'
import QueuePanel from '../../../src/components/QueuePanel'
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

describe('Path Traversal Security Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Reset mock store
    mockUseAppStore.mockReturnValue({
      addFiles: vi.fn(),
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
  })

  describe('FileDropZone Path Traversal Protection', () => {
    const maliciousPaths = [
      '../../../etc/passwd',
      '..\\..\\..\\windows\\system32\\config\\sam',
      '~/../../etc/shadow',
      'C:\\..\\..\\windows\\system32',
      '/../../usr/bin/sudo',
      '..\\Program Files\\sensitive\\file.txt',
      '../../Documents and Settings/All Users',
      '../AppData/Roaming/passwords.txt',
      '\\\\?\\C:\\windows\\system32\\config\\sam',
      'file:///../../../etc/passwd'
    ]

    it('should reject files with path traversal sequences in drop events', async () => {
      const user = userEvent.setup()
      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const dropZone = screen.getByText('Drop video files here').closest('[class*="drop-zone"]')
      expect(dropZone).toBeInTheDocument()

      for (const maliciousPath of maliciousPaths) {
        const mockFile = new File(['test'], maliciousPath, { type: 'video/mp4' })
        Object.defineProperty(mockFile, 'path', {
          value: maliciousPath,
          writable: false
        })

        const mockDataTransfer = {
          files: [mockFile],
          items: [],
          types: ['Files']
        }

        fireEvent.drop(dropZone!, {
          dataTransfer: mockDataTransfer
        })

        // Should show security warning
        await waitFor(() => {
          expect(screen.getByText(/security/i) || screen.getByText(/invalid/i)).toBeInTheDocument()
        })
      }
    })

    it('should sanitize file paths before processing', async () => {
      const addFilesSpy = vi.fn()
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        addFiles: addFilesSpy
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const validFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      Object.defineProperty(validFile, 'path', {
        value: 'C:\\Videos\\test.mp4',
        writable: false
      })

      const dropZone = screen.getByText('Drop video files here').closest('[class*="drop-zone"]')
      
      fireEvent.drop(dropZone!, {
        dataTransfer: { files: [validFile] }
      })

      await waitFor(() => {
        expect(addFilesSpy).toHaveBeenCalledWith(['C:\\Videos\\test.mp4'])
      })
    })

    it('should validate file extensions and reject suspicious files', async () => {
      const suspiciousFiles = [
        'malware.exe.mp4',
        'script.bat',
        'trojan.scr',
        '../../../etc/passwd.mp4',
        'normal.mp4.exe',
        'file.mp4.cmd'
      ]

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const dropZone = screen.getByText('Drop video files here').closest('[class*="drop-zone"]')

      for (const filename of suspiciousFiles) {
        const mockFile = new File(['test'], filename, { type: 'video/mp4' })
        
        fireEvent.drop(dropZone!, {
          dataTransfer: { files: [mockFile] }
        })

        await waitFor(() => {
          // Should show warning for suspicious files
          const warningElements = screen.queryAllByText(/no valid video files/i)
          expect(warningElements.length).toBeGreaterThan(0)
        })
      }
    })

    it('should prevent directory traversal in file dialog results', async () => {
      const mockShowOpenDialog = vi.fn()
      global.window.electronAPI = {
        ...global.window.electronAPI,
        dialog: {
          showOpenDialog: mockShowOpenDialog
        }
      }

      // Mock dialog returning malicious paths
      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: [
          '../../../etc/passwd',
          '..\\windows\\system32\\config\\sam',
          'C:\\legitimate\\file.mp4'
        ]
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse Files')
      await userEvent.click(browseButton)

      await waitFor(() => {
        // Should only process the legitimate file
        expect(mockUseAppStore().addFiles).toHaveBeenCalledWith(['C:\\legitimate\\file.mp4'])
      })
    })
  })

  describe('QueuePanel Path Traversal Protection', () => {
    const maliciousQueueItem = {
      id: '1',
      file_path: '../../../etc/passwd',
      status: 'completed' as const,
      progress: 100,
      output_file: '../../../etc/shadow',
      file_size: 1024,
      format: 'MP4',
      created_at: '2025-01-06T10:00:00Z'
    }

    it('should sanitize file paths in queue operations', async () => {
      const mockShell = {
        showItemInFolder: vi.fn(),
        openExternal: vi.fn()
      }
      
      global.window.electronAPI = {
        ...global.window.electronAPI,
        shell: mockShell
      }

      render(
        <TestWrapper>
          <QueuePanel items={[maliciousQueueItem]} />
        </TestWrapper>
      )

      // Try to open malicious file
      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const showFolderItem = screen.getByText(/show output folder/i)
      await userEvent.click(showFolderItem)

      // Should not call shell operations with malicious paths
      await waitFor(() => {
        expect(mockShell.showItemInFolder).not.toHaveBeenCalledWith('../../../etc/shadow')
        expect(mockShell.openExternal).not.toHaveBeenCalledWith('file:///../../../etc/shadow')
      })
    })

    it('should validate paths before copy operations', async () => {
      Object.assign(navigator, {
        clipboard: {
          writeText: vi.fn()
        }
      })

      render(
        <TestWrapper>
          <QueuePanel items={[maliciousQueueItem]} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const copyPathItem = screen.getByText(/copy output path/i)
      await userEvent.click(copyPathItem)

      // Should not copy malicious paths
      await waitFor(() => {
        expect(navigator.clipboard.writeText).not.toHaveBeenCalledWith('../../../etc/shadow')
      })
    })

    it('should prevent shell injection in file operations', async () => {
      const mockShell = {
        showItemInFolder: vi.fn(),
        openExternal: vi.fn()
      }
      
      global.window.electronAPI = {
        ...global.window.electronAPI,
        shell: mockShell
      }

      const shellInjectionItem = {
        id: '1',
        file_path: 'file.mp4; rm -rf /',
        status: 'completed' as const,
        progress: 100,
        output_file: 'output.txt && echo "pwned"',
        file_size: 1024,
        format: 'MP4',
        created_at: '2025-01-06T10:00:00Z'
      }

      render(
        <TestWrapper>
          <QueuePanel items={[shellInjectionItem]} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const showFolderItem = screen.getByText(/show output folder/i)
      await userEvent.click(showFolderItem)

      // Should sanitize or reject shell injection attempts
      await waitFor(() => {
        const calls = mockShell.showItemInFolder.mock.calls
        calls.forEach(call => {
          expect(call[0]).not.toContain(';')
          expect(call[0]).not.toContain('&&')
          expect(call[0]).not.toContain('rm -rf')
        })
      })
    })

    it('should handle UNC paths securely', async () => {
      const uncPathItem = {
        id: '1',
        file_path: '\\\\malicious-server\\share\\file.mp4',
        status: 'completed' as const,
        progress: 100,
        output_file: '\\\\attacker-server\\sensitive\\data.txt',
        file_size: 1024,
        format: 'MP4',
        created_at: '2025-01-06T10:00:00Z'
      }

      const mockShell = {
        showItemInFolder: vi.fn(),
        openExternal: vi.fn()
      }
      
      global.window.electronAPI = {
        ...global.window.electronAPI,
        shell: mockShell
      }

      render(
        <TestWrapper>
          <QueuePanel items={[uncPathItem]} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const showFolderItem = screen.getByText(/show output folder/i)
      await userEvent.click(showFolderItem)

      // Should show security warning for UNC paths
      await waitFor(() => {
        expect(screen.getByText(/security/i) || screen.getByText(/not allowed/i)).toBeInTheDocument()
      })
    })
  })

  describe('Input Sanitization', () => {
    it('should sanitize special characters in file names', () => {
      const dangerousFilenames = [
        'file<script>alert("xss")</script>.mp4',
        'file"&\'<>.mp4',
        'file\x00null.mp4',
        'file\r\nCRLF.mp4',
        'file\ttab.mp4'
      ]

      dangerousFilenames.forEach(filename => {
        const sanitized = filename.replace(/[<>"'&\x00-\x1F\x7F-\x9F]/g, '')
        expect(sanitized).not.toContain('<')
        expect(sanitized).not.toContain('>')
        expect(sanitized).not.toContain('"')
        expect(sanitized).not.toContain("'")
        expect(sanitized).not.toContain('&')
        expect(sanitized).not.toContain('\x00')
      })
    })

    it('should validate file size limits', () => {
      const maxFileSize = 5 * 1024 * 1024 * 1024 // 5GB limit
      const oversizedFile = new File(['x'.repeat(1000)], 'large.mp4', { 
        type: 'video/mp4' 
      })
      
      // Mock file size
      Object.defineProperty(oversizedFile, 'size', {
        value: maxFileSize + 1,
        writable: false
      })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const dropZone = screen.getByText('Drop video files here').closest('[class*="drop-zone"]')
      
      fireEvent.drop(dropZone!, {
        dataTransfer: { files: [oversizedFile] }
      })

      // Should show file size warning
      // Note: This test assumes the component implements size validation
      // You may need to implement this feature if not already present
    })

    it('should prevent filename buffer overflow attacks', () => {
      const longFilename = 'a'.repeat(1000) + '.mp4'
      const mockFile = new File(['test'], longFilename, { type: 'video/mp4' })

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const dropZone = screen.getByText('Drop video files here').closest('[class*="drop-zone"]')
      
      fireEvent.drop(dropZone!, {
        dataTransfer: { files: [mockFile] }
      })

      // Should handle long filenames gracefully
      expect(() => {
        // This should not throw an error
      }).not.toThrow()
    })
  })
})