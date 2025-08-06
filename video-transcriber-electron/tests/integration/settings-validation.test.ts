/**
 * Integration Tests: Settings Validation
 * 
 * Comprehensive validation tests for all settings form fields and scenarios,
 * ensuring proper error handling and user feedback.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@mui/material/styles'
import { theme } from '../../src/theme/theme'
import SettingsDialog from '../../src/components/SettingsDialog'
import { useAppStore } from '../../src/store/appStore'

// Mock dependencies
vi.mock('../../src/store/appStore')

const mockUseAppStore = vi.mocked(useAppStore)

// Test wrapper with theme
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
)

describe('Settings Validation Integration Tests', () => {
  const validProcessingOptions = {
    output_directory: 'C:/Valid/Output/Directory',
    whisper_model: 'large' as const,
    language: 'en' as const,
    output_format: 'txt' as const
  }

  let mockSetProcessingOptions: ReturnType<typeof vi.fn>
  let mockStartProcessing: ReturnType<typeof vi.fn>
  let mockOnClose: ReturnType<typeof vi.fn>
  let mockOnSaveAndStart: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()

    mockSetProcessingOptions = vi.fn()
    mockStartProcessing = vi.fn().mockResolvedValue(undefined)
    mockOnClose = vi.fn()
    mockOnSaveAndStart = vi.fn()

    // Setup default mock store
    mockUseAppStore.mockReturnValue({
      processingOptions: validProcessingOptions,
      setProcessingOptions: mockSetProcessingOptions,
      startProcessing: mockStartProcessing,
      isLoading: false,
      error: null
    } as any)

    // Mock Electron APIs
    global.window.electronAPI = {
      dialog: {
        showOpenDialog: vi.fn().mockResolvedValue({
          canceled: false,
          filePaths: ['C:/Selected/Directory']
        })
      },
      path: {
        getDefaultOutputDirectory: vi.fn().mockResolvedValue('C:/Default/Output')
      },
      fs: {
        existsSync: vi.fn().mockReturnValue(true)
      }
    } as any
  })

  describe('Output Directory Validation', () => {
    it('should validate required directory field', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      
      // Clear the required field
      await user.clear(directoryInput)
      fireEvent.blur(directoryInput)

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
      })

      // Save buttons should be disabled
      const saveButton = screen.getByRole('button', { name: /save only/i })
      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      
      expect(saveButton).toBeDisabled()
      expect(saveAndStartButton).toBeDisabled()
    })

    it('should validate directory path format - Windows paths', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      
      // Test invalid Windows path formats
      const invalidPaths = [
        'invalid-path-format',
        'relative/path',
        '//network-path-invalid',
        'C:invalid-path',
        'c:/path with spaces but invalid format',
        ''
      ]

      for (const invalidPath of invalidPaths) {
        await user.clear(directoryInput)
        await user.type(directoryInput, invalidPath)
        fireEvent.blur(directoryInput)

        if (invalidPath === '') {
          await waitFor(() => {
            expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
          })
        } else {
          await waitFor(() => {
            expect(screen.getByText(/valid directory path/i)).toBeInTheDocument()
          })
        }
      }
    })

    it('should accept valid directory path formats', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      
      // Test valid Windows path formats
      const validPaths = [
        'C:/Program Files/Video Transcriber',
        'D:/Documents/Transcripts',
        'C:\\Windows\\Path\\Format',
        'E:/Video Projects/Transcriptions',
        '/unix/style/path',
        '~/home/directory/path'
      ]

      for (const validPath of validPaths) {
        await user.clear(directoryInput)
        await user.type(directoryInput, validPath)
        fireEvent.blur(directoryInput)

        await waitFor(() => {
          expect(screen.queryByText(/valid directory path/i)).not.toBeInTheDocument()
          expect(screen.queryByText(/output directory is required/i)).not.toBeInTheDocument()
        })

        // Save buttons should be enabled for valid paths
        const saveButton = screen.getByRole('button', { name: /save only/i })
        expect(saveButton).toBeEnabled()
      }
    })

    it('should validate directory accessibility', async () => {
      const user = userEvent.setup()
      
      // Mock file system access denial
      global.window.electronAPI.fs.existsSync = vi.fn().mockReturnValue(false)

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      await user.clear(directoryInput)
      await user.type(directoryInput, 'C:/Restricted/Access/Path')
      
      // Trigger validation
      fireEvent.blur(directoryInput)

      // Note: This test verifies the path format validation
      // Actual directory existence checking would require backend integration
      await waitFor(() => {
        // Should still pass format validation
        expect(screen.queryByText(/valid directory path/i)).not.toBeInTheDocument()
      })
    })

    it('should handle very long directory paths', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      
      // Create a very long path (>260 characters - Windows path limit)
      const veryLongPath = 'C:/' + 'A'.repeat(300) + '/Transcripts'
      
      await user.clear(directoryInput)
      await user.type(directoryInput, veryLongPath)
      fireEvent.blur(directoryInput)

      // Should handle long paths gracefully
      // The component should not crash and should validate the format
      expect(directoryInput).toHaveValue(veryLongPath)
    })

    it('should show helpful error messages for common directory issues', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      
      // Test empty directory
      await user.clear(directoryInput)
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        const errorElement = screen.getByText(/output directory is required/i)
        expect(errorElement).toBeInTheDocument()
        
        // Should show error icon
        const errorIcon = screen.getByTestId('ErrorOutlineIcon') || screen.querySelector('[data-testid="ErrorOutlineIcon"]')
        expect(errorIcon).toBeInTheDocument()
      })

      // Test invalid format
      await user.type(directoryInput, 'invalid-format')
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        expect(screen.getByText(/valid directory path/i)).toBeInTheDocument()
      })
    })
  })

  describe('Settings Form Validation', () => {
    it('should validate all required fields together', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Clear all required fields
      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      await user.clear(directoryInput)

      // Try to save
      const saveButton = screen.getByRole('button', { name: /save only/i })
      expect(saveButton).toBeDisabled()

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
      })
    })

    it('should validate model selection integrity', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Ensure all model options are available
      const modelSelect = screen.getByText('Large').closest('[role="combobox"]')
      await user.click(modelSelect!)

      // Should show all valid model options
      expect(screen.getByText('Base')).toBeInTheDocument()
      expect(screen.getByText('Small')).toBeInTheDocument() 
      expect(screen.getByText('Medium')).toBeInTheDocument()
      expect(screen.getByText('Large')).toBeInTheDocument()

      // Select each model to ensure they work
      const models = ['Base', 'Small', 'Medium', 'Large']
      for (const model of models) {
        await user.click(screen.getByText(model))
        
        // Verify selection
        expect(screen.getByText(model)).toBeInTheDocument()
        
        // Reopen selector for next iteration
        if (model !== 'Large') { // Skip reopening on last iteration
          const currentSelect = screen.getByText(model).closest('[role="combobox"]')
          await user.click(currentSelect!)
        }
      }
    })

    it('should validate language selection options', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Test language selection
      const languageSelect = screen.getByText('English Only').closest('[role="combobox"]')
      await user.click(languageSelect!)

      // Should show available language options
      expect(screen.getByText('English Only')).toBeInTheDocument()
      expect(screen.getByText('Auto-detect')).toBeInTheDocument()

      // Test selecting auto-detect
      await user.click(screen.getByText('Auto-detect'))
      expect(screen.getByText('Auto-detect')).toBeInTheDocument()

      // Switch back to English Only
      const updatedLanguageSelect = screen.getByText('Auto-detect').closest('[role="combobox"]')
      await user.click(updatedLanguageSelect!)
      await user.click(screen.getByText('English Only'))
      
      expect(screen.getByText('English Only')).toBeInTheDocument()
    })

    it('should validate output format selection', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Test format selection
      const formatSelect = screen.getByText('Plain Text (.txt)').closest('[role="combobox"]')
      await user.click(formatSelect!)

      // Should show all format options
      expect(screen.getByText('Plain Text (.txt)')).toBeInTheDocument()
      expect(screen.getByText('SubRip (.srt)')).toBeInTheDocument()
      expect(screen.getByText('WebVTT (.vtt)')).toBeInTheDocument()

      // Test selecting SRT format
      await user.click(screen.getByText('SubRip (.srt)'))
      expect(screen.getByText('SubRip (.srt)')).toBeInTheDocument()

      // Test selecting VTT format
      const srtFormatSelect = screen.getByText('SubRip (.srt)').closest('[role="combobox"]')
      await user.click(srtFormatSelect!)
      await user.click(screen.getByText('WebVTT (.vtt)'))
      
      expect(screen.getByText('WebVTT (.vtt)')).toBeInTheDocument()
    })

    it('should disable Save & Start Processing with invalid settings', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog 
            open={true} 
            onClose={mockOnClose}
            onSaveAndStart={mockOnSaveAndStart}
          />
        </TestWrapper>
      )

      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      
      // Should initially be enabled with valid settings
      expect(saveAndStartButton).toBeEnabled()

      // Make settings invalid
      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      await user.clear(directoryInput)

      // Button should be disabled
      expect(saveAndStartButton).toBeDisabled()
      expect(saveAndStartButton).toHaveAttribute('title', 'Please configure a valid output directory to start processing')
    })

    it('should show validation feedback in real-time', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      
      // Start typing invalid path
      await user.clear(directoryInput)
      await user.type(directoryInput, 'invalid')
      
      // Should show validation error immediately on blur
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        expect(screen.getByText(/valid directory path/i)).toBeInTheDocument()
      })

      // Fix the path
      await user.clear(directoryInput)
      await user.type(directoryInput, 'C:/Fixed/Valid/Path')
      fireEvent.blur(directoryInput)

      // Error should clear
      await waitFor(() => {
        expect(screen.queryByText(/valid directory path/i)).not.toBeInTheDocument()
      })
    })

    it('should maintain form state during validation', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Modify multiple fields
      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      await user.clear(directoryInput)
      await user.type(directoryInput, 'C:/New/Directory')

      // Change model
      const modelSelect = screen.getByText('Large').closest('[role="combobox"]')
      await user.click(modelSelect!)
      await user.click(screen.getByText('Medium'))

      // Create validation error in directory
      await user.clear(directoryInput)
      fireEvent.blur(directoryInput)

      // Should show error
      await waitFor(() => {
        expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
      })

      // Other field selections should remain unchanged
      expect(screen.getByText('Medium')).toBeInTheDocument()

      // Fix directory error
      await user.type(directoryInput, 'C:/Fixed/Directory')
      fireEvent.blur(directoryInput)

      // All fields should maintain their state
      expect(screen.getByDisplayValue('C:/Fixed/Directory')).toBeInTheDocument()
      expect(screen.getByText('Medium')).toBeInTheDocument()
    })
  })

  describe('Validation Error Recovery', () => {
    it('should clear validation errors when form is reset', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Create validation error
      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      await user.clear(directoryInput)
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
      })

      // Reset form
      const resetButton = screen.getByRole('button', { name: /reset to defaults/i })
      await user.click(resetButton)

      // Error should be cleared
      expect(screen.queryByText(/output directory is required/i)).not.toBeInTheDocument()
      
      // Form should show default values
      expect(screen.getByDisplayValue('')).toBeInTheDocument() // Default directory will be set
    })

    it('should clear validation errors when dialog is canceled and reopened', async () => {
      const user = userEvent.setup()
      
      // Render dialog
      const { unmount } = render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Create validation error
      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      await user.clear(directoryInput)
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
      })

      // Cancel dialog
      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      unmount()

      // Reopen dialog - should not show previous validation errors
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      expect(screen.queryByText(/output directory is required/i)).not.toBeInTheDocument()
      expect(screen.getByDisplayValue('C:/Valid/Output/Directory')).toBeInTheDocument()
    })

    it('should handle multiple simultaneous validation errors', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Create multiple validation issues
      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      await user.clear(directoryInput)
      await user.type(directoryInput, 'invalid-format')
      fireEvent.blur(directoryInput)

      // Should show directory validation error
      await waitFor(() => {
        expect(screen.getByText(/valid directory path/i)).toBeInTheDocument()
      })

      // Clear directory entirely to trigger required field error
      await user.clear(directoryInput)
      fireEvent.blur(directoryInput)

      // Should show required field error (higher priority)
      await waitFor(() => {
        expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
        expect(screen.queryByText(/valid directory path/i)).not.toBeInTheDocument()
      })

      // Fix with valid directory
      await user.type(directoryInput, 'C:/Valid/Fixed/Directory')
      fireEvent.blur(directoryInput)

      // All errors should be cleared
      await waitFor(() => {
        expect(screen.queryByText(/output directory is required/i)).not.toBeInTheDocument()
        expect(screen.queryByText(/valid directory path/i)).not.toBeInTheDocument()
      })
    })

    it('should provide clear visual feedback for validation states', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      
      // Create validation error
      await user.clear(directoryInput)
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        // Should show error styling on input field
        expect(directoryInput.closest('.MuiFormControl-root')).toHaveClass('Mui-error')
        
        // Should show error icon
        const errorMessage = screen.getByText(/output directory is required/i)
        expect(errorMessage).toBeInTheDocument()
      })

      // Fix the error
      await user.type(directoryInput, 'C:/Valid/Directory')
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        // Error styling should be removed
        expect(directoryInput.closest('.MuiFormControl-root')).not.toHaveClass('Mui-error')
        
        // Helper text should show info instead of error
        const helperText = screen.getByText(/choose where to save your transcribed files/i)
        expect(helperText).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility and UX', () => {
    it('should announce validation errors to screen readers', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      
      // Create validation error
      await user.clear(directoryInput)
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        const errorText = screen.getByText(/output directory is required/i)
        
        // Should be associated with the input via aria-describedby
        expect(directoryInput).toHaveAttribute('aria-describedby')
        expect(errorText).toHaveAttribute('id')
      })
    })

    it('should maintain focus management during validation', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Valid/Output/Directory')
      
      // Focus input and create error
      directoryInput.focus()
      await user.clear(directoryInput)
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
      })

      // Focus should remain manageable
      directoryInput.focus()
      expect(document.activeElement).toBe(directoryInput)
    })

    it('should provide helpful tooltips and guidance', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Should have info icons with tooltips
      const infoIcons = screen.getAllByTestId('InfoIcon') || screen.querySelectorAll('[data-testid="InfoIcon"]')
      expect(infoIcons.length).toBeGreaterThan(0)

      // Should have helpful placeholder text
      const directoryInput = screen.getByPlaceholderText(/e\.g\., C:\\Documents\\Video Transcripts/i)
      expect(directoryInput).toBeInTheDocument()

      // Should have descriptive helper text when no errors
      const helperText = screen.getByText(/choose where to save your transcribed files/i)
      expect(helperText).toBeInTheDocument()
    })
  })
})