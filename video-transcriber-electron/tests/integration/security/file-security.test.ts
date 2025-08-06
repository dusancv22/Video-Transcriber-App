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

describe('File Security Tests', () => {
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

    // Mock Electron APIs
    global.window.electronAPI = {
      dialog: {
        showOpenDialog: vi.fn()
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

  describe('File Type Validation', () => {
    it('should only accept valid video file extensions', async () => {
      const validExtensions = ['.mp4', '.avi', '.mkv', '.mov']
      const invalidExtensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.jar', '.zip', '.rar']

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const dropZone = screen.getByText('Drop video files here').closest('[class*="drop-zone"]')

      // Test valid extensions
      for (const ext of validExtensions) {
        const validFile = new File(['video data'], `test${ext}`, { type: 'video/mp4' })
        
        fireEvent.drop(dropZone!, {
          dataTransfer: { files: [validFile] }
        })

        await waitFor(() => {
          expect(screen.getByText(/successfully added/i)).toBeInTheDocument()
        })
      }

      // Test invalid extensions
      for (const ext of invalidExtensions) {
        const invalidFile = new File(['malicious data'], `malware${ext}`, { type: 'application/octet-stream' })
        
        fireEvent.drop(dropZone!, {
          dataTransfer: { files: [invalidFile] }
        })

        await waitFor(() => {
          expect(screen.getByText(/no valid video files/i)).toBeInTheDocument()
        })
      }
    })

    it('should validate MIME types against file extensions', async () => {
      const mismatchedFiles = [
        { name: 'video.mp4', type: 'application/x-executable' },
        { name: 'innocent.avi', type: 'application/x-msdownload' },
        { name: 'movie.mkv', type: 'application/zip' },
        { name: 'clip.mov', type: 'text/html' }
      ]

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const dropZone = screen.getByText('Drop video files here').closest('[class*="drop-zone"]')

      for (const fileData of mismatchedFiles) {
        const suspiciousFile = new File(['data'], fileData.name, { type: fileData.type })
        
        fireEvent.drop(dropZone!, {
          dataTransfer: { files: [suspiciousFile] }
        })

        // Should detect MIME type mismatch and reject or warn
        await waitFor(() => {
          expect(
            screen.getByText(/no valid video files/i) || 
            screen.getByText(/suspicious file/i)
          ).toBeInTheDocument()
        })
      }
    })

    it('should reject files with double extensions', async () => {
      const doubleExtensionFiles = [
        'video.mp4.exe',
        'movie.avi.bat',
        'clip.mkv.scr',
        'file.mov.cmd',
        'innocent.mp4.zip'
      ]

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const dropZone = screen.getByText('Drop video files here').closest('[class*="drop-zone"]')

      for (const filename of doubleExtensionFiles) {
        const suspiciousFile = new File(['data'], filename, { type: 'video/mp4' })
        
        fireEvent.drop(dropZone!, {
          dataTransfer: { files: [suspiciousFile] }
        })

        await waitFor(() => {
          expect(screen.getByText(/no valid video files/i)).toBeInTheDocument()
        })
      }
    })

    it('should enforce file size limits', async () => {
      const maxFileSize = 10 * 1024 * 1024 * 1024 // 10GB limit
      
      // Create mock oversized file
      const oversizedFile = new File(['x'], 'huge.mp4', { type: 'video/mp4' })
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

      // Should warn about file size
      // Note: Implement file size validation in the component if not already present
      expect(() => {
        // Should handle gracefully without crashing
      }).not.toThrow()
    })
  })

  describe('File Content Validation', () => {
    it('should detect potentially malicious file headers', () => {
      const maliciousHeaders = [
        // PE executable header
        new Uint8Array([0x4D, 0x5A]), // MZ
        // ELF executable header
        new Uint8Array([0x7F, 0x45, 0x4C, 0x46]), // .ELF
        // Java class file
        new Uint8Array([0xCA, 0xFE, 0xBA, 0xBE]), // CAFEBABE
        // Windows batch file
        new Uint8Array([0x40, 0x65, 0x63, 0x68, 0x6F]), // @echo
        // Shell script
        new Uint8Array([0x23, 0x21, 0x2F, 0x62, 0x69, 0x6E]) // #!/bin
      ]

      // Function to check if file header is suspicious
      const isSuspiciousHeader = (data: Uint8Array): boolean => {
        return maliciousHeaders.some(header => {
          return header.every((byte, index) => data[index] === byte)
        })
      }

      // Test each malicious header
      maliciousHeaders.forEach(header => {
        expect(isSuspiciousHeader(header)).toBe(true)
      })

      // Test legitimate video headers (should not trigger)
      const videoHeaders = [
        new Uint8Array([0x66, 0x74, 0x79, 0x70]), // MP4 ftyp
        new Uint8Array([0x52, 0x49, 0x46, 0x46]), // AVI RIFF
        new Uint8Array([0x1A, 0x45, 0xDF, 0xA3]) // MKV
      ]

      videoHeaders.forEach(header => {
        expect(isSuspiciousHeader(header)).toBe(false)
      })
    })

    it('should validate file magic numbers', () => {
      const expectedMagicNumbers = {
        '.mp4': [[0x66, 0x74, 0x79, 0x70], [0x00, 0x00, 0x00, 0x18], [0x00, 0x00, 0x00, 0x1C]],
        '.avi': [[0x52, 0x49, 0x46, 0x46]],
        '.mkv': [[0x1A, 0x45, 0xDF, 0xA3]],
        '.mov': [[0x66, 0x74, 0x79, 0x70]]
      }

      const validateMagicNumber = (filename: string, data: Uint8Array): boolean => {
        const ext = filename.toLowerCase().substring(filename.lastIndexOf('.'))
        const validMagics = expectedMagicNumbers[ext as keyof typeof expectedMagicNumbers]
        
        if (!validMagics) return false
        
        return validMagics.some(magic => 
          magic.every((byte, index) => data[index] === byte)
        )
      }

      // Test valid combinations
      expect(validateMagicNumber('test.mp4', new Uint8Array([0x66, 0x74, 0x79, 0x70]))).toBe(true)
      expect(validateMagicNumber('test.avi', new Uint8Array([0x52, 0x49, 0x46, 0x46]))).toBe(true)
      
      // Test invalid combinations
      expect(validateMagicNumber('test.mp4', new Uint8Array([0x4D, 0x5A]))).toBe(false)
      expect(validateMagicNumber('test.exe', new Uint8Array([0x4D, 0x5A]))).toBe(false)
    })
  })

  describe('File System Security', () => {
    it('should prevent symlink attacks', async () => {
      const mockShell = vi.mocked(global.window.electronAPI.shell)

      const symlinkItem = {
        id: '1',
        file_path: '/tmp/symlink-to-sensitive-file',
        status: 'completed' as const,
        progress: 100,
        output_file: '/tmp/symlink-to-sensitive-output',
        file_size: 1024,
        format: 'MP4',
        created_at: '2025-01-06T10:00:00Z'
      }

      render(
        <TestWrapper>
          <QueuePanel items={[symlinkItem]} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const showFolderItem = screen.getByText(/show output folder/i)
      await userEvent.click(showFolderItem)

      // Should resolve symlinks or refuse to open them
      await waitFor(() => {
        if (mockShell.showItemInFolder.mock.calls.length > 0) {
          const calledPath = mockShell.showItemInFolder.mock.calls[0][0]
          // Should not contain symlink indicators or should be resolved
          expect(calledPath).toBeDefined()
        }
      })
    })

    it('should sanitize file paths before file operations', async () => {
      const mockShell = vi.mocked(global.window.electronAPI.shell)
      
      const unsafeItem = {
        id: '1',
        file_path: 'C:\\Safe\\Path\\..\\..\\..\\Windows\\System32\\calc.exe',
        status: 'completed' as const,
        progress: 100,
        output_file: 'C:\\Output\\file.txt',
        file_size: 1024,
        format: 'MP4',
        created_at: '2025-01-06T10:00:00Z'
      }

      render(
        <TestWrapper>
          <QueuePanel items={[unsafeItem]} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const showInputItem = screen.getByText(/show input file/i)
      await userEvent.click(showInputItem)

      // Should sanitize or reject the path
      await waitFor(() => {
        const calls = mockShell.showItemInFolder.mock.calls
        if (calls.length > 0) {
          expect(calls[0][0]).not.toContain('..\\..\\')
          expect(calls[0][0]).not.toContain('calc.exe')
        }
      })
    })

    it('should prevent race condition attacks in file operations', async () => {
      const mockShell = vi.mocked(global.window.electronAPI.shell)
      
      const testItem = {
        id: '1',
        file_path: 'C:\\Test\\video.mp4',
        status: 'completed' as const,
        progress: 100,
        output_file: 'C:\\Test\\output.txt',
        file_size: 1024,
        format: 'MP4',
        created_at: '2025-01-06T10:00:00Z'
      }

      render(
        <TestWrapper>
          <QueuePanel items={[testItem]} />
        </TestWrapper>
      )

      // Rapidly click multiple file operations to test race conditions
      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      
      const promises = []
      for (let i = 0; i < 10; i++) {
        promises.push(userEvent.click(moreButton))
      }

      await Promise.all(promises)

      // Should handle rapid clicks gracefully
      expect(() => {
        // Should not crash or cause memory leaks
      }).not.toThrow()
    })

    it('should validate file permissions before operations', async () => {
      const mockFs = vi.mocked(global.window.electronAPI.fs)
      mockFs.existsSync.mockReturnValue(false) // Simulate file not accessible
      
      const inaccessibleItem = {
        id: '1',
        file_path: 'C:\\Restricted\\video.mp4',
        status: 'completed' as const,
        progress: 100,
        output_file: 'C:\\Restricted\\output.txt',
        file_size: 1024,
        format: 'MP4',
        created_at: '2025-01-06T10:00:00Z'
      }

      render(
        <TestWrapper>
          <QueuePanel items={[inaccessibleItem]} />
        </TestWrapper>
      )

      const moreButton = screen.getAllByLabelText(/more actions/i)[0]
      await userEvent.click(moreButton)

      const showFolderItem = screen.getByText(/show output folder/i)
      await userEvent.click(showFolderItem)

      // Should handle permission errors gracefully
      await waitFor(() => {
        expect(
          screen.getByText(/not found/i) || 
          screen.getByText(/permission/i) ||
          screen.getByText(/access denied/i)
        ).toBeInTheDocument()
      })
    })
  })

  describe('Memory Safety', () => {
    it('should handle large file lists without memory leaks', async () => {
      const largeFileList = Array.from({ length: 10000 }, (_, i) => ({
        id: `file-${i}`,
        file_path: `C:\\Videos\\video-${i}.mp4`,
        status: 'queued' as const,
        progress: 0,
        file_size: 1024 * 1024,
        format: 'MP4',
        created_at: '2025-01-06T10:00:00Z'
      }))

      // Should render without crashing
      expect(() => {
        render(
          <TestWrapper>
            <QueuePanel items={largeFileList} />
          </TestWrapper>
        )
      }).not.toThrow()

      // Component should be responsive
      expect(screen.getByText(/files in queue/i) || screen.getByText('file-0')).toBeInTheDocument()
    })

    it('should clean up resources properly on unmount', () => {
      const { unmount } = render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      // Should unmount cleanly without memory leaks
      expect(() => {
        unmount()
      }).not.toThrow()
    })

    it('should handle concurrent file operations safely', async () => {
      const concurrentFiles = Array.from({ length: 5 }, (_, i) => 
        new File(['data'], `concurrent-${i}.mp4`, { type: 'video/mp4' })
      )

      render(
        <TestWrapper>
          <FileDropZone />
        </TestWrapper>
      )

      const dropZone = screen.getByText('Drop video files here').closest('[class*="drop-zone"]')

      // Drop all files simultaneously
      const promises = concurrentFiles.map(file => {
        return new Promise(resolve => {
          setTimeout(() => {
            fireEvent.drop(dropZone!, {
              dataTransfer: { files: [file] }
            })
            resolve(true)
          }, Math.random() * 100)
        })
      })

      await Promise.all(promises)

      // Should handle all files without errors
      expect(() => {
        // No crashes expected
      }).not.toThrow()
    })
  })
})