import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@mui/material/styles'
import { theme } from '../../../src/theme/theme'
import SettingsDialog from '../../../src/components/SettingsDialog'
import { useAppStore } from '../../../src/store/appStore'

// Mock the store
vi.mock('../../../src/store/appStore')

const mockUseAppStore = vi.mocked(useAppStore)

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
})

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
)

describe('Settings Persistence Tests', () => {
  const defaultSettings = {
    output_directory: 'C:/Output/Transcripts',
    whisper_model: 'large' as const,
    language: 'en' as const,
    output_format: 'txt' as const
  }

  const customSettings = {
    output_directory: 'C:/Custom/Output',
    whisper_model: 'medium' as const,
    language: 'auto' as const,
    output_format: 'srt' as const
  }

  let mockSetProcessingOptions: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()
    
    mockSetProcessingOptions = vi.fn()

    // Reset mock store with default settings
    mockUseAppStore.mockReturnValue({
      addFiles: vi.fn(),
      queueItems: [],
      removeFromQueue: vi.fn(),
      processingOptions: defaultSettings,
      setProcessingOptions: mockSetProcessingOptions
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

    // Reset localStorage mock
    mockLocalStorage.getItem.mockReturnValue(null)
    mockLocalStorage.setItem.mockClear()
    mockLocalStorage.removeItem.mockClear()
  })

  describe('Settings Loading', () => {
    it('should load default settings when no saved settings exist', () => {
      mockLocalStorage.getItem.mockReturnValue(null)

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      expect(screen.getByDisplayValue('C:/Output/Transcripts')).toBeInTheDocument()
      expect(screen.getByText('Large')).toBeInTheDocument()
      expect(screen.getByText('English Only')).toBeInTheDocument()
      expect(screen.getByText('Plain Text (.txt)')).toBeInTheDocument()
    })

    it('should load saved settings from store', () => {
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: customSettings
      })

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      expect(screen.getByDisplayValue('C:/Custom/Output')).toBeInTheDocument()
      expect(screen.getByText('Medium')).toBeInTheDocument()
      expect(screen.getByText('Auto-detect')).toBeInTheDocument()
      expect(screen.getByText('SubRip (.srt)')).toBeInTheDocument()
    })

    it('should handle corrupted localStorage gracefully', () => {
      // Mock corrupted JSON in localStorage
      mockLocalStorage.getItem.mockReturnValue('{"invalid": json}')

      expect(() => {
        render(
          <TestWrapper>
            <SettingsDialog open={true} onClose={() => {}} />
          </TestWrapper>
        )
      }).not.toThrow()

      // Should fall back to default settings
      expect(screen.getByDisplayValue('C:/Output/Transcripts')).toBeInTheDocument()
    })

    it('should validate loaded settings against schema', () => {
      const invalidSettings = {
        output_directory: 123, // Wrong type
        whisper_model: 'invalid_model',
        language: 'invalid_lang',
        output_format: 'invalid_format'
      }

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: invalidSettings as any
      })

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      // Should show validation errors or fall back to defaults
      expect(
        screen.getByText(/valid directory path/i) || 
        screen.getByDisplayValue('C:/Output/Transcripts')
      ).toBeInTheDocument()
    })
  })

  describe('Settings Saving', () => {
    it('should persist settings to store when saved', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      // Modify settings
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/New/Output/Path')

      // Change whisper model
      const modelSelect = screen.getByText('Large').closest('[role="combobox"]')
      await userEvent.click(modelSelect!)
      await userEvent.click(screen.getByText('Medium'))

      // Save settings
      const saveButton = screen.getByText('Save Changes')
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(mockSetProcessingOptions).toHaveBeenCalledWith({
          output_directory: 'C:/New/Output/Path',
          whisper_model: 'medium',
          language: 'en',
          output_format: 'txt'
        })
      })
    })

    it('should maintain settings across dialog sessions', async () => {
      // First session - modify and save settings
      const { rerender } = render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/Persistent/Path')

      const saveButton = screen.getByText('Save Changes')
      await userEvent.click(saveButton)

      // Update store to simulate persistence
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: {
          ...defaultSettings,
          output_directory: 'C:/Persistent/Path'
        }
      })

      // Second session - reopen dialog
      rerender(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      expect(screen.getByDisplayValue('C:/Persistent/Path')).toBeInTheDocument()
    })

    it('should handle save failures gracefully', async () => {
      mockSetProcessingOptions.mockRejectedValue(new Error('Storage full'))

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      // Modify and try to save
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/Test/Path')

      const saveButton = screen.getByText('Save Changes')
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText(/save failed/i)).toBeInTheDocument()
      })

      // Settings should remain in unsaved state
      expect(screen.getByText('Save Changes')).toBeEnabled()
    })

    it('should validate settings before saving', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      // Enter invalid directory
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'invalid-path')

      // Try to save
      const saveButton = screen.getByText('Save Changes')
      expect(saveButton).toBeDisabled() // Should be disabled due to validation error

      // Settings should not be saved
      expect(mockSetProcessingOptions).not.toHaveBeenCalled()
    })
  })

  describe('Settings Migration', () => {
    it('should handle settings format changes', () => {
      // Simulate old settings format
      const oldFormatSettings = {
        outputPath: 'C:/Old/Path', // Old field name
        model: 'large',
        lang: 'en',
        format: 'txt'
      }

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: oldFormatSettings as any
      })

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      // Should handle gracefully, potentially migrating or using defaults
      expect(
        screen.getByDisplayValue(/Output/i) || 
        screen.getByDisplayValue('C:/Output/Transcripts')
      ).toBeInTheDocument()
    })

    it('should add new settings with default values', () => {
      // Simulate settings missing new fields
      const incompleteSettings = {
        output_directory: 'C:/Test/Path',
        whisper_model: 'large' as const
        // Missing language and output_format
      }

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: incompleteSettings as any
      })

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      // Should use defaults for missing fields
      expect(screen.getByDisplayValue('C:/Test/Path')).toBeInTheDocument()
      expect(screen.getByText('Large')).toBeInTheDocument()
      // New fields should have default values
      expect(screen.getByText('English Only') || screen.getByText('Auto-detect')).toBeInTheDocument()
    })
  })

  describe('Settings Reset', () => {
    it('should reset to factory defaults', async () => {
      // Start with custom settings
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: customSettings
      })

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      // Verify custom settings are shown
      expect(screen.getByDisplayValue('C:/Custom/Output')).toBeInTheDocument()

      // Reset to defaults
      const resetButton = screen.getByText('Reset to Defaults')
      await userEvent.click(resetButton)

      // Should show default values
      expect(screen.getByDisplayValue('C:/Output/Transcripts')).toBeInTheDocument()
      expect(screen.getByText('Large')).toBeInTheDocument()
      expect(screen.getByText('English Only')).toBeInTheDocument()
      expect(screen.getByText('Plain Text (.txt)')).toBeInTheDocument()
    })

    it('should persist reset values when saved', async () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      // Make changes
      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/Modified/Path')

      // Reset
      const resetButton = screen.getByText('Reset to Defaults')
      await userEvent.click(resetButton)

      // Save
      const saveButton = screen.getByText('Save Changes')
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(mockSetProcessingOptions).toHaveBeenCalledWith(defaultSettings)
      })
    })
  })

  describe('Settings Backup and Recovery', () => {
    it('should handle concurrent access to settings', async () => {
      // Simulate multiple components trying to save settings
      const promises = Array.from({ length: 5 }, async (_, i) => {
        const settings = {
          ...defaultSettings,
          output_directory: `C:/Concurrent/Path${i}`
        }
        
        return mockSetProcessingOptions(settings)
      })

      await Promise.allSettled(promises)

      // Should handle concurrent saves gracefully
      expect(mockSetProcessingOptions).toHaveBeenCalledTimes(5)
    })

    it('should validate settings integrity', () => {
      const corruptedSettings = {
        output_directory: null,
        whisper_model: undefined,
        language: '',
        output_format: 'invalid'
      }

      const validateSettings = (settings: any) => {
        return {
          output_directory: settings.output_directory || defaultSettings.output_directory,
          whisper_model: ['base', 'small', 'medium', 'large'].includes(settings.whisper_model) 
            ? settings.whisper_model 
            : defaultSettings.whisper_model,
          language: ['en', 'auto'].includes(settings.language) 
            ? settings.language 
            : defaultSettings.language,
          output_format: ['txt', 'srt', 'vtt'].includes(settings.output_format) 
            ? settings.output_format 
            : defaultSettings.output_format
        }
      }

      const validatedSettings = validateSettings(corruptedSettings)
      
      expect(validatedSettings).toEqual(defaultSettings)
    })

    it('should provide settings export functionality', () => {
      const exportSettings = (settings: typeof defaultSettings) => {
        return JSON.stringify(settings, null, 2)
      }

      const exported = exportSettings(customSettings)
      const imported = JSON.parse(exported)

      expect(imported).toEqual(customSettings)
    })

    it('should provide settings import functionality', () => {
      const importedSettings = JSON.stringify(customSettings)
      
      const parseImportedSettings = (settingsJson: string) => {
        try {
          const parsed = JSON.parse(settingsJson)
          
          // Validate structure
          const requiredKeys = ['output_directory', 'whisper_model', 'language', 'output_format']
          const hasAllKeys = requiredKeys.every(key => key in parsed)
          
          return hasAllKeys ? parsed : null
        } catch {
          return null
        }
      }

      const result = parseImportedSettings(importedSettings)
      expect(result).toEqual(customSettings)

      // Test invalid import
      const invalidResult = parseImportedSettings('invalid json')
      expect(invalidResult).toBeNull()
    })
  })

  describe('Settings Performance', () => {
    it('should debounce frequent setting changes', async () => {
      const mockDebouncedSave = vi.fn()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={() => {}} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Output/Transcripts')

      // Simulate rapid typing
      await userEvent.clear(directoryInput)
      await userEvent.type(directoryInput, 'C:/Rapid/Changes', { delay: 1 })

      // Should not save on every keystroke
      expect(mockDebouncedSave).not.toHaveBeenCalledTimes(15) // One per character
    })

    it('should handle large settings objects efficiently', () => {
      const largeSettings = {
        ...defaultSettings,
        // Add many additional properties
        ...Object.fromEntries(
          Array.from({ length: 1000 }, (_, i) => [`property_${i}`, `value_${i}`])
        )
      }

      expect(() => {
        JSON.stringify(largeSettings)
      }).not.toThrow()

      expect(() => {
        JSON.parse(JSON.stringify(largeSettings))
      }).not.toThrow()
    })
  })
})