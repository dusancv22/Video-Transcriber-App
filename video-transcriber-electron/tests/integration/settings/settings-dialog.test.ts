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

describe('Settings Dialog Integration Tests', () => {
  const mockProcessingOptions = {
    output_directory: 'C:/Output/Transcripts',
    whisper_model: 'large' as const,
    language: 'en' as const,
    output_format: 'txt' as const
  }

  let mockSetProcessingOptions: ReturnType<typeof vi.fn>
  let mockShowOpenDialog: ReturnType<typeof vi.fn>
  let mockOnClose: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()
    
    mockSetProcessingOptions = vi.fn()
    mockShowOpenDialog = vi.fn()
    mockOnClose = vi.fn()

    // Reset mock store
    mockUseAppStore.mockReturnValue({
      addFiles: vi.fn(),
      queueItems: [],
      removeFromQueue: vi.fn(),
      processingOptions: mockProcessingOptions,
      setProcessingOptions: mockSetProcessingOptions
    })

    // Mock Electron dialog API
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

  describe('Dialog Lifecycle', () => {
    it('should open and initialize with current settings', () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      expect(screen.getByText('Processing Settings')).toBeInTheDocument()
      expect(screen.getByDisplayValue('C:/Output/Transcripts')).toBeInTheDocument()
      expect(screen.getByText('Large')).toBeInTheDocument()
      expect(screen.getByText('English Only')).toBeInTheDocument()
      expect(screen.getByText('Plain Text (.txt)')).toBeInTheDocument()
    })

    it('should close dialog on cancel', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const cancelButton = screen.getByText('Cancel')
      await userEvent.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should close dialog on close icon click', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const closeIcon = screen.getByRole('button', { name: /close/i })
      await userEvent.click(closeIcon)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should reset form values on cancel', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Modify a field
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/New/Path')

      // Cancel
      const cancelButton = screen.getByText('Cancel')
      await userEvent.click(cancelButton)

      // Reopen dialog - should show original values
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      expect(screen.getByDisplayValue('C:/Output/Transcripts')).toBeInTheDocument()
    })
  })

  describe('Form Interactions', () => {
    it('should update directory path input', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/New/Output/Directory')

      expect(directoryInput).toHaveValue('C:/New/Output/Directory')
    })

    it('should update whisper model selection', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Open model selector
      const modelSelect = screen.getByText('Large').closest('[role="combobox"]')
      await userEvent.click(modelSelect!)

      // Select different model
      const smallModel = screen.getByText('Small')
      await userEvent.click(smallModel)

      // Verify selection
      expect(screen.getByText('Small')).toBeInTheDocument()
    })

    it('should update language selection', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Open language selector
      const languageSelect = screen.getByText('English Only').closest('[role="combobox"]')
      await userEvent.click(languageSelect!)

      // Select auto-detect
      const autoDetect = screen.getByText('Auto-detect')
      await userEvent.click(autoDetect)

      expect(screen.getByText('Auto-detect')).toBeInTheDocument()
    })

    it('should update output format selection', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Open format selector
      const formatSelect = screen.getByText('Plain Text (.txt)').closest('[role="combobox"]')
      await userEvent.click(formatSelect!)

      // Select SRT format
      const srtFormat = screen.getByText('SubRip (.srt)')
      await userEvent.click(srtFormat)

      expect(screen.getByText('SubRip (.srt)')).toBeInTheDocument()
    })

    it('should enable save button when changes are made', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const saveButton = screen.getByText('Save Changes')
      expect(saveButton).toBeDisabled() // Initially disabled - no changes

      // Make a change
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/Modified/Path')

      expect(saveButton).toBeEnabled()
    })
  })

  describe('Directory Browse Functionality', () => {
    it('should open directory dialog when browse button clicked', async () => {
      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ['C:/Selected/Directory']
      })

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse')
      await userEvent.click(browseButton)

      expect(mockShowOpenDialog).toHaveBeenCalledWith({
        title: 'Select Output Directory',
        properties: ['openDirectory', 'createDirectory'],
        defaultPath: 'C:/Output/Transcripts'
      })
    })

    it('should update directory input when directory selected', async () => {
      mockShowOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ['C:/Selected/Directory']
      })

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse')
      await userEvent.click(browseButton)

      await waitFor(() => {
        const directoryInput = screen.getByDisplayValue('C:/Selected/Directory')
        expect(directoryInput).toBeInTheDocument()
      })
    })

    it('should handle canceled directory selection', async () => {
      mockShowOpenDialog.mockResolvedValue({
        canceled: true,
        filePaths: []
      })

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const originalValue = 'C:/Output/Transcripts'
      const browseButton = screen.getByText('Browse')
      await userEvent.click(browseButton)

      // Value should remain unchanged
      expect(screen.getByDisplayValue(originalValue)).toBeInTheDocument()
    })

    it('should show loading state during directory browse', async () => {
      let resolvePromise: (value: any) => void
      const browsePromise = new Promise(resolve => {
        resolvePromise = resolve
      })
      mockShowOpenDialog.mockReturnValue(browsePromise)

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse')
      await userEvent.click(browseButton)

      // Should show loading state
      expect(screen.getByText('Browsing...')).toBeInTheDocument()
      
      // Resolve the promise
      resolvePromise!({
        canceled: false,
        filePaths: ['C:/Test/Path']
      })

      await waitFor(() => {
        expect(screen.getByText('Browse')).toBeInTheDocument()
      })
    })

    it('should handle browse errors gracefully', async () => {
      mockShowOpenDialog.mockRejectedValue(new Error('Permission denied'))

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const browseButton = screen.getByText('Browse')
      await userEvent.click(browseButton)

      await waitFor(() => {
        expect(screen.getByText(/directory selection failed/i)).toBeInTheDocument()
      })
    })
  })

  describe('Form Validation', () => {
    it('should validate required directory field', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
      })

      const saveButton = screen.getByText('Save Changes')
      expect(saveButton).toBeDisabled()
    })

    it('should validate directory path format', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'invalid-path-format')
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        expect(screen.getByText(/valid directory path/i)).toBeInTheDocument()
      })

      const saveButton = screen.getByText('Save Changes')
      expect(saveButton).toBeDisabled()
    })

    it('should clear validation errors when valid input provided', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      
      // Make invalid input
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'invalid')
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        expect(screen.getByText(/valid directory path/i)).toBeInTheDocument()
      })

      // Fix the input
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/Valid/Path')
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        expect(screen.queryByText(/valid directory path/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Save Functionality', () => {
    it('should save settings and close dialog', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Make changes
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/New/Directory')

      const saveButton = screen.getByText('Save Changes')
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(mockSetProcessingOptions).toHaveBeenCalledWith({
          output_directory: 'C:/New/Directory',
          whisper_model: 'large',
          language: 'en',
          output_format: 'txt'
        })
      })

      // Should show success message
      expect(screen.getByText('Settings saved successfully!')).toBeInTheDocument()

      // Should close after delay
      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled()
      }, { timeout: 2000 })
    })

    it('should show loading state during save', async () => {
      let resolveSave: (value: any) => void
      const savePromise = new Promise(resolve => {
        resolveSave = resolve
      })
      
      mockSetProcessingOptions.mockImplementation(() => savePromise)

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Make changes
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/New/Directory')

      const saveButton = screen.getByText('Save Changes')
      await userEvent.click(saveButton)

      // Should show loading
      expect(screen.getByText('Saving...')).toBeInTheDocument()
      expect(saveButton).toBeDisabled()

      // Resolve save
      resolveSave!(undefined)

      await waitFor(() => {
        expect(screen.getByText('Save Changes')).toBeInTheDocument()
      })
    })

    it('should handle save errors', async () => {
      mockSetProcessingOptions.mockRejectedValue(new Error('Save failed'))

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Make changes
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/New/Directory')

      const saveButton = screen.getByText('Save Changes')
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText(/save failed/i)).toBeInTheDocument()
      })

      // Dialog should remain open
      expect(mockOnClose).not.toHaveBeenCalled()
    })
  })

  describe('Reset Functionality', () => {
    it('should reset all fields to default values', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Make changes to all fields
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/Modified/Directory')

      // Change whisper model
      const modelSelect = screen.getByText('Large').closest('[role="combobox"]')
      await userEvent.click(modelSelect!)
      await userEvent.click(screen.getByText('Small'))

      // Reset to defaults
      const resetButton = screen.getByText('Reset to Defaults')
      await userEvent.click(resetButton)

      // Should show default values
      expect(screen.getByDisplayValue('C:/Output/Transcripts')).toBeInTheDocument()
      expect(screen.getByText('Large')).toBeInTheDocument()
    })

    it('should clear validation errors on reset', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      // Create validation error
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      fireEvent.blur(directoryInput)

      await waitFor(() => {
        expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
      })

      // Reset
      const resetButton = screen.getByText('Reset to Defaults')
      await userEvent.click(resetButton)

      // Error should be cleared
      expect(screen.queryByText(/output directory is required/i)).not.toBeInTheDocument()
    })
  })

  describe('Keyboard Navigation', () => {
    it('should support tab navigation between form fields', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      directoryInput.focus()

      // Tab should move to browse button
      await userEvent.tab()
      expect(screen.getByText('Browse')).toHaveFocus()

      // Continue tabbing through form
      await userEvent.tab()
      // Should reach next focusable element
    })

    it('should support escape key to close dialog', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' })

      expect(mockOnClose).toHaveBeenCalled()
    })
  })
})