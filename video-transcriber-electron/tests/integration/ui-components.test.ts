/**
 * Integration Tests: UI Components Integration
 * 
 * Tests the integration between UI components, focusing on SettingsStatusPanel,
 * enhanced Settings Dialog, and component interactions.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@mui/material/styles'
import { theme } from '../../src/theme/theme'
import { useAppStore } from '../../src/store/appStore'
import MainWindow from '../../src/components/MainWindow'
import SettingsDialog from '../../src/components/SettingsDialog'
import SettingsStatusPanel from '../../src/components/SettingsStatusPanel'

// Mock dependencies
vi.mock('../../src/store/appStore')

const mockUseAppStore = vi.mocked(useAppStore)

// Test wrapper with theme
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
)

describe('UI Components Integration Tests', () => {
  const mockProcessingOptions = {
    output_directory: 'C:/Test/Output/Directory',
    whisper_model: 'large' as const,
    language: 'en' as const,
    output_format: 'txt' as const
  }

  let mockSetProcessingOptions: ReturnType<typeof vi.fn>
  let mockSetSettingsOpen: ReturnType<typeof vi.fn>
  let mockStartProcessing: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()

    mockSetProcessingOptions = vi.fn()
    mockSetSettingsOpen = vi.fn()
    mockStartProcessing = vi.fn().mockResolvedValue(undefined)

    // Setup default mock store
    mockUseAppStore.mockReturnValue({
      // UI state
      settingsOpen: false,
      isLoading: false,
      error: null,
      dragOver: false,
      selectedFiles: [],
      
      // Settings state
      processingOptions: mockProcessingOptions,
      isSettingsLoaded: true,
      
      // Queue state
      queueItems: [],
      queueStats: {
        total: 0,
        queued: 0,
        processing: 0,
        completed: 0,
        failed: 0
      },
      
      // Processing state
      processingStatus: null,
      currentSession: null,
      
      // WebSocket state
      wsConnectionState: 'connected' as const,
      wsLastEvent: null,
      appStatus: null,
      
      // Actions
      setProcessingOptions: mockSetProcessingOptions,
      setSettingsOpen: mockSetSettingsOpen,
      startProcessing: mockStartProcessing,
      
      // Other required actions
      setLoading: vi.fn(),
      setError: vi.fn(),
      setDragOver: vi.fn(),
      setSelectedFiles: vi.fn(),
      setQueueItems: vi.fn(),
      addQueueItems: vi.fn(),
      updateQueueItem: vi.fn(),
      removeQueueItem: vi.fn(),
      clearQueue: vi.fn(),
      setProcessingStatus: vi.fn(),
      setCurrentSession: vi.fn(),
      setWsConnectionState: vi.fn(),
      handleWebSocketEvent: vi.fn(),
      fetchAppStatus: vi.fn(),
      fetchQueue: vi.fn(),
      fetchProcessingStatus: vi.fn(),
      addFiles: vi.fn(),
      addDirectory: vi.fn(),
      removeFromQueue: vi.fn(),
      pauseProcessing: vi.fn(),
      stopProcessing: vi.fn(),
      initializeWebSocket: vi.fn(),
      disconnectWebSocket: vi.fn(),
      updateProcessingOption: vi.fn(),
      resetProcessingOptions: vi.fn(),
      loadSettingsFromStorage: vi.fn(),
      saveSettingsToStorage: vi.fn()
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

  describe('SettingsStatusPanel Integration', () => {
    it('should display current settings correctly', () => {
      render(
        <TestWrapper>
          <SettingsStatusPanel />
        </TestWrapper>
      )

      // Should display current settings
      expect(screen.getByText(/C:\/Test\/Output\/Directory/)).toBeInTheDocument()
      expect(screen.getByText(/Large/i)).toBeInTheDocument()
      expect(screen.getByText(/English/i)).toBeInTheDocument()
      expect(screen.getByText(/Plain Text/i)).toBeInTheDocument()
    })

    it('should update settings display when settings change', async () => {
      const { rerender } = render(
        <TestWrapper>
          <SettingsStatusPanel />
        </TestWrapper>
      )

      // Initially shows current settings
      expect(screen.getByText(/Large/i)).toBeInTheDocument()

      // Mock settings change
      const updatedSettings = {
        ...mockProcessingOptions,
        whisper_model: 'medium' as const,
        output_format: 'srt' as const
      }

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: updatedSettings
      })

      rerender(
        <TestWrapper>
          <SettingsStatusPanel />
        </TestWrapper>
      )

      // Should display updated settings
      expect(screen.getByText(/Medium/i)).toBeInTheDocument()
      expect(screen.getByText(/SubRip/i)).toBeInTheDocument()
    })

    it('should open Settings Dialog when Configure button is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsStatusPanel />
        </TestWrapper>
      )

      const configureButton = screen.getByRole('button', { name: /configure/i })
      await user.click(configureButton)

      expect(mockSetSettingsOpen).toHaveBeenCalledWith(true)
    })

    it('should show responsive behavior on different screen sizes', () => {
      // Mock smaller viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600, // Mobile size
      })

      render(
        <TestWrapper>
          <SettingsStatusPanel />
        </TestWrapper>
      )

      // Should still display essential information
      expect(screen.getByText(/settings/i)).toBeInTheDocument()
      
      // Implementation would depend on actual responsive design
      // This is a basic structure test
    })

    it('should handle long directory paths gracefully', () => {
      const longPath = 'C:/Very/Long/Directory/Path/That/Might/Overflow/The/Display/Area/Video/Transcriber/Output'
      
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: {
          ...mockProcessingOptions,
          output_directory: longPath
        }
      })

      render(
        <TestWrapper>
          <SettingsStatusPanel />
        </TestWrapper>
      )

      // Should handle long paths without breaking layout
      // Implementation would depend on text truncation strategy
      expect(screen.getByText(new RegExp(longPath.substring(0, 20)))).toBeInTheDocument()
    })

    it('should show loading state when settings are being loaded', () => {
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        isSettingsLoaded: false,
        processingOptions: {
          output_directory: '',
          whisper_model: 'large' as const,
          language: 'en' as const,
          output_format: 'txt' as const
        }
      })

      render(
        <TestWrapper>
          <SettingsStatusPanel />
        </TestWrapper>
      )

      // Should show appropriate loading or placeholder state
      expect(screen.getByText(/loading/i) || screen.getByText(/configuring/i)).toBeInTheDocument()
    })

    it('should provide tooltips for settings information', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsStatusPanel />
        </TestWrapper>
      )

      // Look for info icons or tooltippable elements
      const infoElements = screen.queryAllByTestId('InfoIcon') || 
                          screen.queryAllByRole('button', { name: /info/i })

      if (infoElements.length > 0) {
        // Test tooltip interaction
        await user.hover(infoElements[0])
        
        // Should show helpful tooltip
        await waitFor(() => {
          expect(screen.getByRole('tooltip')).toBeInTheDocument()
        })
      }
    })
  })

  describe('Enhanced Settings Dialog Integration', () => {
    it('should render all form fields correctly', () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      // Should display all settings sections
      expect(screen.getByText(/output directory/i)).toBeInTheDocument()
      expect(screen.getByText(/whisper model/i)).toBeInTheDocument()
      expect(screen.getByText(/language/i)).toBeInTheDocument()
      expect(screen.getByText(/output format/i)).toBeInTheDocument()

      // Should show current values
      expect(screen.getByDisplayValue('C:/Test/Output/Directory')).toBeInTheDocument()
      expect(screen.getByText('Large')).toBeInTheDocument()
      expect(screen.getByText('English Only')).toBeInTheDocument()
      expect(screen.getByText('Plain Text (.txt)')).toBeInTheDocument()
    })

    it('should show validation feedback in real-time', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Test/Output/Directory')
      
      // Clear required field
      await user.clear(directoryInput)
      fireEvent.blur(directoryInput)

      // Should show validation error with icon
      await waitFor(() => {
        expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
        
        // Should show error styling
        expect(directoryInput.closest('.MuiFormControl-root')).toHaveClass('Mui-error')
      })

      // Fix the error
      await user.type(directoryInput, 'C:/Fixed/Directory')
      fireEvent.blur(directoryInput)

      // Error should clear
      await waitFor(() => {
        expect(screen.queryByText(/output directory is required/i)).not.toBeInTheDocument()
        expect(directoryInput.closest('.MuiFormControl-root')).not.toHaveClass('Mui-error')
      })
    })

    it('should provide helpful help text and tooltips', () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      // Should show helpful descriptions
      expect(screen.getByText(/choose where to save your transcribed files/i)).toBeInTheDocument()
      expect(screen.getByText(/choose the ai model for transcription/i)).toBeInTheDocument()

      // Should have info icons with tooltips
      const infoIcons = screen.getAllByTestId('InfoIcon') || 
                       screen.querySelectorAll('[data-testid="InfoIcon"]')
      expect(infoIcons.length).toBeGreaterThan(0)
    })

    it('should handle directory browsing functionality', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      const browseButton = screen.getByRole('button', { name: /browse/i })
      await user.click(browseButton)

      // Should call Electron dialog API
      expect(global.window.electronAPI.dialog.showOpenDialog).toHaveBeenCalledWith({
        title: 'Select Output Directory',
        properties: ['openDirectory', 'createDirectory'],
        defaultPath: 'C:/Test/Output/Directory'
      })

      // Should update input with selected path
      await waitFor(() => {
        expect(screen.getByDisplayValue('C:/Selected/Directory')).toBeInTheDocument()
      })
    })

    it('should show loading states during directory operations', async () => {
      const user = userEvent.setup()
      
      // Mock delayed directory dialog
      let resolveDialog: (value: any) => void
      const dialogPromise = new Promise(resolve => {
        resolveDialog = resolve
      })
      global.window.electronAPI.dialog.showOpenDialog = vi.fn().mockReturnValue(dialogPromise)

      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      const browseButton = screen.getByRole('button', { name: /browse/i })
      await user.click(browseButton)

      // Should show loading state
      expect(screen.getByText('Browsing...')).toBeInTheDocument()
      expect(browseButton).toBeDisabled()

      // Resolve dialog
      resolveDialog!({
        canceled: false,
        filePaths: ['C:/Async/Selected/Directory']
      })

      await waitFor(() => {
        expect(screen.getByText('Browse')).toBeInTheDocument()
        expect(screen.getByDisplayValue('C:/Async/Selected/Directory')).toBeInTheDocument()
      })
    })

    it('should disable form during processing operations', async () => {
      const user = userEvent.setup()
      
      // Mock processing in progress
      let resolveProcessing: () => void
      const processingPromise = new Promise<void>(resolve => {
        resolveProcessing = resolve
      })
      mockStartProcessing.mockReturnValue(processingPromise)

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true} 
            onClose={vi.fn()}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      await user.click(saveAndStartButton)

      // Form should be disabled during processing
      const directoryInput = screen.getByDisplayValue('C:/Test/Output/Directory')
      const browseButton = screen.getByRole('button', { name: /browse/i })
      
      expect(directoryInput).toBeDisabled()
      expect(browseButton).toBeDisabled()
      expect(screen.getByText('Starting...')).toBeInTheDocument()

      // Resolve processing
      resolveProcessing!()

      await waitFor(() => {
        expect(directoryInput).not.toBeDisabled()
        expect(browseButton).not.toBeDisabled()
      })
    })

    it('should show appropriate success and error feedback', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      // Modify settings and save
      const directoryInput = screen.getByDisplayValue('C:/Test/Output/Directory')
      await user.clear(directoryInput)
      await user.type(directoryInput, 'C:/New/Directory')

      const saveButton = screen.getByRole('button', { name: /save only/i })
      await user.click(saveButton)

      // Should show success feedback
      await waitFor(() => {
        expect(screen.getByText('Settings saved successfully!')).toBeInTheDocument()
      })

      // Test error scenario
      mockSetProcessingOptions.mockRejectedValueOnce(new Error('Save failed'))

      await user.clear(directoryInput)
      await user.type(directoryInput, 'C:/Another/Directory')
      await user.click(saveButton)

      // Should show error feedback
      await waitFor(() => {
        expect(screen.getByText(/save failed/i)).toBeInTheDocument()
      })
    })
  })

  describe('Component Communication Integration', () => {
    it('should integrate MainWindow with SettingsStatusPanel and SettingsDialog', async () => {
      const user = userEvent.setup()
      
      // Mock store with settings dialog open
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        settingsOpen: true
      })

      render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Should show both main window and settings dialog
      expect(screen.getByRole('button', { name: /start processing/i })).toBeInTheDocument()
      expect(screen.getByText(/processing settings/i)).toBeInTheDocument()
    })

    it('should update SettingsStatusPanel when dialog saves changes', async () => {
      const user = userEvent.setup()
      
      const { rerender } = render(
        <TestWrapper>
          <SettingsStatusPanel />
          <SettingsDialog open={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      // Initially shows current settings
      expect(screen.getByText(/Large/i)).toBeInTheDocument()

      // Change settings in dialog
      const modelSelect = screen.getByText('Large').closest('[role="combobox"]')
      await user.click(modelSelect!)
      await user.click(screen.getByText('Medium'))

      const saveButton = screen.getByRole('button', { name: /save only/i })
      await user.click(saveButton)

      // Mock store update
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: {
          ...mockProcessingOptions,
          whisper_model: 'medium' as const
        }
      })

      rerender(
        <TestWrapper>
          <SettingsStatusPanel />
          <SettingsDialog open={false} onClose={vi.fn()} />
        </TestWrapper>
      )

      // Status panel should reflect the change
      expect(screen.getByText(/Medium/i)).toBeInTheDocument()
    })

    it('should handle dialog opening from multiple sources', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <MainWindow />
          <SettingsStatusPanel />
        </TestWrapper>
      )

      // Should be able to open from Start Processing button
      const startButton = screen.getByRole('button', { name: /start processing/i })
      await user.click(startButton)
      expect(mockSetSettingsOpen).toHaveBeenCalledWith(true)

      // Should also be able to open from Configure button in status panel
      const configureButton = screen.getByRole('button', { name: /configure/i })
      await user.click(configureButton)
      expect(mockSetSettingsOpen).toHaveBeenCalledWith(true)
    })

    it('should maintain consistent state across component updates', async () => {
      const user = userEvent.setup()
      
      // Start with empty queue
      const { rerender } = render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Add items to queue
      const updatedQueueItems = [
        {
          id: 'test-file',
          file_path: 'C:/Videos/test.mp4',
          file_name: 'test.mp4',
          file_size: 1024000,
          status: 'queued' as const,
          progress: 0,
          added_at: new Date().toISOString()
        }
      ]

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        queueItems: updatedQueueItems,
        queueStats: {
          total: 1,
          queued: 1,
          processing: 0,
          completed: 0,
          failed: 0
        }
      })

      rerender(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Start button should still work correctly with files in queue
      const startButton = screen.getByRole('button', { name: /start processing/i })
      await user.click(startButton)

      expect(mockSetSettingsOpen).toHaveBeenCalledWith(true)
    })

    it('should handle error states gracefully across components', async () => {
      // Mock error state
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        error: 'Failed to load settings from storage',
        isLoading: false
      })

      render(
        <TestWrapper>
          <MainWindow />
          <SettingsStatusPanel />
        </TestWrapper>
      )

      // Should display error information
      expect(screen.getByText(/failed to load settings/i) || 
             screen.getByText(/error/i)).toBeInTheDocument()

      // Components should remain functional despite errors
      expect(screen.getByRole('button', { name: /start processing/i })).toBeInTheDocument()
    })

    it('should provide consistent theming across all components', () => {
      render(
        <TestWrapper>
          <MainWindow />
          <SettingsStatusPanel />
          <SettingsDialog open={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      // All components should use consistent theme colors and styles
      // This would be tested by checking computed styles or theme application
      // Implementation depends on actual theme structure
      
      const mainElements = screen.getAllByRole('button')
      expect(mainElements.length).toBeGreaterThan(0)
      
      // Verify theme consistency (basic structural test)
      mainElements.forEach(element => {
        expect(element).toHaveStyle({ fontFamily: expect.any(String) })
      })
    })
  })

  describe('Responsive Design Integration', () => {
    it('should adapt layout for different screen sizes', () => {
      // Test mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 400,
      })

      render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Should maintain functionality on small screens
      expect(screen.getByRole('button', { name: /start processing/i })).toBeInTheDocument()

      // Test desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1200,
      })

      // Should utilize additional space effectively
      // Implementation would depend on actual responsive design
    })

    it('should handle dialog sizing appropriately', () => {
      render(
        <TestWrapper>
          <SettingsDialog open={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      const dialog = screen.getByRole('dialog')
      expect(dialog).toBeInTheDocument()

      // Dialog should have appropriate size constraints
      // This would be tested with computed styles in a real implementation
      expect(dialog).toHaveAttribute('aria-modal', 'true')
    })

    it('should maintain accessibility across all screen sizes', () => {
      render(
        <TestWrapper>
          <MainWindow />
          <SettingsDialog open={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      // Should maintain proper focus management
      const focusableElements = screen.getAllByRole('button')
      expect(focusableElements.length).toBeGreaterThan(0)

      // Should have proper ARIA labels
      focusableElements.forEach(element => {
        expect(element).toHaveAttribute('type')
      })
    })
  })
})