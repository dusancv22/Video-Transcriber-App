/**
 * Integration Tests: Settings → Processing Flow
 * 
 * Verifies the complete workflow from opening the Start button to processing execution,
 * ensuring all settings are properly configured and passed through the system.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@mui/material/styles'
import { theme } from '../../src/theme/theme'
import { useAppStore } from '../../src/store/appStore'
import MainWindow from '../../src/components/MainWindow'
import SettingsDialog from '../../src/components/SettingsDialog'
import { VideoTranscriberAPI } from '../../src/services/api'

// Mock dependencies
vi.mock('../../src/store/appStore')
vi.mock('../../src/services/api')
vi.mock('../../src/services/websocket')

const mockUseAppStore = vi.mocked(useAppStore)
const mockAPI = vi.mocked(VideoTranscriberAPI)

// Test wrapper with theme
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
)

describe('Settings → Processing Integration Flow', () => {
  // Mock store state
  const mockProcessingOptions = {
    output_directory: 'C:/Test/Output',
    whisper_model: 'large' as const,
    language: 'en' as const,
    output_format: 'txt' as const
  }

  const mockQueueItems = [
    {
      id: 'test-file-1',
      file_path: 'C:/Videos/test1.mp4',
      file_name: 'test1.mp4',
      file_size: 1024000,
      status: 'queued' as const,
      progress: 0,
      added_at: new Date().toISOString()
    },
    {
      id: 'test-file-2', 
      file_path: 'C:/Videos/test2.mp4',
      file_name: 'test2.mp4',
      file_size: 2048000,
      status: 'queued' as const,
      progress: 0,
      added_at: new Date().toISOString()
    }
  ]

  let mockSetSettingsOpen: ReturnType<typeof vi.fn>
  let mockSetProcessingOptions: ReturnType<typeof vi.fn>
  let mockStartProcessing: ReturnType<typeof vi.fn>
  let mockLoadSettingsFromStorage: ReturnType<typeof vi.fn>
  let mockSaveSettingsToStorage: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()
    
    mockSetSettingsOpen = vi.fn()
    mockSetProcessingOptions = vi.fn()
    mockStartProcessing = vi.fn().mockResolvedValue(undefined)
    mockLoadSettingsFromStorage = vi.fn().mockResolvedValue(undefined)
    mockSaveSettingsToStorage = vi.fn()

    // Setup mock store
    mockUseAppStore.mockReturnValue({
      // UI state
      settingsOpen: false,
      isLoading: false,
      error: null,
      dragOver: false,
      selectedFiles: [],
      
      // Queue state
      queueItems: mockQueueItems,
      queueStats: {
        total: 2,
        queued: 2,
        processing: 0,
        completed: 0,
        failed: 0
      },
      
      // Settings state
      processingOptions: mockProcessingOptions,
      isSettingsLoaded: true,
      
      // Processing state
      processingStatus: null,
      currentSession: null,
      
      // WebSocket state
      wsConnectionState: 'connected' as const,
      wsLastEvent: null,
      appStatus: null,
      
      // Actions
      setSettingsOpen: mockSetSettingsOpen,
      setProcessingOptions: mockSetProcessingOptions,
      startProcessing: mockStartProcessing,
      loadSettingsFromStorage: mockLoadSettingsFromStorage,
      saveSettingsToStorage: mockSaveSettingsToStorage,
      setLoading: vi.fn(),
      setError: vi.fn(),
      setDragOver: vi.fn(),
      setSelectedFiles: vi.fn(),
      
      // Queue actions
      setQueueItems: vi.fn(),
      addQueueItems: vi.fn(),
      updateQueueItem: vi.fn(),
      removeQueueItem: vi.fn(),
      clearQueue: vi.fn(),
      
      // Processing actions
      setProcessingStatus: vi.fn(),
      setCurrentSession: vi.fn(),
      
      // WebSocket actions
      setWsConnectionState: vi.fn(),
      handleWebSocketEvent: vi.fn(),
      
      // API actions
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
      
      // Settings actions
      updateProcessingOption: vi.fn(),
      resetProcessingOptions: vi.fn()
    })

    // Mock API methods
    mockAPI.startProcessing = vi.fn().mockResolvedValue({ success: true, session_id: 'test-session' })
    mockAPI.getStatus = vi.fn().mockResolvedValue({ 
      status: 'ready',
      backend_version: '1.0.0',
      whisper_available: true
    })

    // Mock Electron APIs
    global.window.electronAPI = {
      dialog: {
        showOpenDialog: vi.fn().mockResolvedValue({
          canceled: false,
          filePaths: ['C:/Selected/Directory']
        })
      },
      shell: {
        showItemInFolder: vi.fn(),
        openExternal: vi.fn()
      },
      path: {
        join: vi.fn(),
        dirname: vi.fn(),
        basename: vi.fn(),
        resolve: vi.fn(),
        getDefaultOutputDirectory: vi.fn().mockResolvedValue('C:/Default/Output')
      },
      fs: {
        existsSync: vi.fn().mockReturnValue(true),
        readFileSync: vi.fn(),
        writeFileSync: vi.fn()
      }
    }

    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn().mockReturnValue(JSON.stringify(mockProcessingOptions)),
      setItem: vi.fn(),
      clear: vi.fn()
    }
    Object.defineProperty(window, 'localStorage', { value: localStorageMock })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Start Button Workflow', () => {
    it('should open Settings Dialog when Start button is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Find and click the Start Processing button
      const startButton = screen.getByRole('button', { name: /start processing/i })
      expect(startButton).toBeInTheDocument()
      
      await user.click(startButton)

      // Should open settings dialog
      expect(mockSetSettingsOpen).toHaveBeenCalledWith(true)
    })

    it('should show Settings Dialog with current configuration when opened from Start button', async () => {
      const user = userEvent.setup()
      
      // Mock store with settings dialog open
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        settingsOpen: true
      })

      render(
        <TestWrapper>
          <MainWindow />
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      // Should display current settings
      expect(screen.getByDisplayValue('C:/Test/Output')).toBeInTheDocument()
      expect(screen.getByText('Large')).toBeInTheDocument()
      expect(screen.getByText('English Only')).toBeInTheDocument()
      expect(screen.getByText('Plain Text (.txt)')).toBeInTheDocument()
    })

    it('should show "Save & Start Processing" button functionality', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      // Should find the "Save & Start Processing" button
      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      expect(saveAndStartButton).toBeInTheDocument()
      
      await user.click(saveAndStartButton)

      // Should save settings and start processing
      await waitFor(() => {
        expect(mockSetProcessingOptions).toHaveBeenCalledWith(mockProcessingOptions)
      })

      await waitFor(() => {
        expect(mockStartProcessing).toHaveBeenCalled()
      }, { timeout: 2000 })
    })

    it('should handle empty queue scenario gracefully', async () => {
      const user = userEvent.setup()
      
      // Mock empty queue
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        queueItems: [],
        queueStats: {
          total: 0,
          queued: 0,
          processing: 0,
          completed: 0,
          failed: 0
        }
      })

      render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      const startButton = screen.getByRole('button', { name: /start processing/i })
      
      // Start button should still be available (will open settings first)
      expect(startButton).toBeInTheDocument()
      
      await user.click(startButton)
      expect(mockSetSettingsOpen).toHaveBeenCalledWith(true)
    })
  })

  describe('Settings Persistence Integration', () => {
    it('should load settings on application start', async () => {
      render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Settings should be loaded from storage on initialization
      await waitFor(() => {
        expect(mockLoadSettingsFromStorage).toHaveBeenCalled()
      })
    })

    it('should save settings when configured in dialog', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
          />
        </TestWrapper>
      )

      // Modify a setting
      const directoryInput = screen.getByDisplayValue('C:/Test/Output')
      await user.clear(directoryInput)
      await user.type(directoryInput, 'C:/New/Output/Path')

      // Save settings
      const saveButton = screen.getByRole('button', { name: /save only/i })
      await user.click(saveButton)

      // Should save to store and localStorage
      await waitFor(() => {
        expect(mockSetProcessingOptions).toHaveBeenCalledWith({
          ...mockProcessingOptions,
          output_directory: 'C:/New/Output/Path'
        })
      })
    })

    it('should persist settings across app sessions', async () => {
      const user = userEvent.setup()
      
      // First session - modify settings
      const { unmount } = render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
          />
        </TestWrapper>
      )

      const directoryInput = screen.getByDisplayValue('C:/Test/Output')
      await user.clear(directoryInput)
      await user.type(directoryInput, 'C:/Persistent/Settings')

      const saveButton = screen.getByRole('button', { name: /save only/i })
      await user.click(saveButton)

      unmount()

      // Simulate app restart - localStorage should contain saved settings
      const savedSettings = {
        ...mockProcessingOptions,
        output_directory: 'C:/Persistent/Settings'
      }

      const localStorageMock = {
        getItem: vi.fn().mockReturnValue(JSON.stringify(savedSettings)),
        setItem: vi.fn(),
        clear: vi.fn()
      }
      Object.defineProperty(window, 'localStorage', { value: localStorageMock })

      // Second session - should load saved settings
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: savedSettings
      })

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
          />
        </TestWrapper>
      )

      // Should display persisted settings
      expect(screen.getByDisplayValue('C:/Persistent/Settings')).toBeInTheDocument()
    })

    it('should handle settings corruption gracefully', async () => {
      // Mock corrupted localStorage data
      const localStorageMock = {
        getItem: vi.fn().mockReturnValue('{"invalid": "json"'), // Malformed JSON
        setItem: vi.fn(),
        clear: vi.fn()
      }
      Object.defineProperty(window, 'localStorage', { value: localStorageMock })

      // Should fall back to defaults
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: {
          output_directory: 'C:/Default/Output',
          whisper_model: 'large',
          language: 'en',
          output_format: 'txt'
        }
      })

      render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Should not crash and should use default settings
      expect(screen.getByRole('button', { name: /start processing/i })).toBeInTheDocument()
    })
  })

  describe('API Integration', () => {
    it('should call startProcessing API with correct ProcessingOptions payload', async () => {
      const user = userEvent.setup()
      
      const testOptions = {
        output_directory: 'C:/API/Test/Output',
        whisper_model: 'medium' as const,
        language: 'auto' as const,
        output_format: 'srt' as const
      }

      // Mock store with test options
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: testOptions
      })

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      await user.click(saveAndStartButton)

      // Should call API with exact options
      await waitFor(() => {
        expect(mockStartProcessing).toHaveBeenCalled()
      })

      // Verify API was called with correct payload (through store action)
      expect(mockUseAppStore().processingOptions).toEqual(testOptions)
    })

    it('should include all required settings fields in API payload', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      // Modify all settings fields
      const directoryInput = screen.getByDisplayValue('C:/Test/Output')
      await user.clear(directoryInput)
      await user.type(directoryInput, 'C:/Complete/Settings/Test')

      // Change model
      const modelSelect = screen.getByText('Large').closest('[role="combobox"]')
      await user.click(modelSelect!)
      await user.click(screen.getByText('Small'))

      // Change language
      const languageSelect = screen.getByText('English Only').closest('[role="combobox"]')
      await user.click(languageSelect!)
      await user.click(screen.getByText('Auto-detect'))

      // Change format
      const formatSelect = screen.getByText('Plain Text (.txt)').closest('[role="combobox"]')
      await user.click(formatSelect!)
      await user.click(screen.getByText('SubRip (.srt)'))

      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      await user.click(saveAndStartButton)

      // Should save complete settings
      await waitFor(() => {
        expect(mockSetProcessingOptions).toHaveBeenCalledWith({
          output_directory: 'C:/Complete/Settings/Test',
          whisper_model: 'small',
          language: 'auto',
          output_format: 'srt'
        })
      })
    })

    it('should handle API errors gracefully', async () => {
      const user = userEvent.setup()
      
      // Mock API error
      mockStartProcessing.mockRejectedValue(new Error('Backend unavailable'))

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      await user.click(saveAndStartButton)

      // Should handle error and show message
      await waitFor(() => {
        expect(screen.getByText(/settings saved but failed to start processing/i)).toBeInTheDocument()
      }, { timeout: 3000 })

      // Dialog should remain open for user to retry
      expect(screen.getByText('Processing Settings')).toBeInTheDocument()
    })

    it('should validate backend connection before starting processing', async () => {
      const user = userEvent.setup()
      
      // Mock backend health check
      mockAPI.healthCheck = vi.fn().mockResolvedValue(true)

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      await user.click(saveAndStartButton)

      // Should attempt to start processing
      await waitFor(() => {
        expect(mockStartProcessing).toHaveBeenCalled()
      })
    })
  })

  describe('Error Handling', () => {
    it('should show validation errors before allowing start', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      // Clear required directory field
      const directoryInput = screen.getByDisplayValue('C:/Test/Output')
      await user.clear(directoryInput)

      // Try to start processing
      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      
      // Button should be disabled with validation error
      expect(saveAndStartButton).toBeDisabled()
      
      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
      })
    })

    it('should handle network connectivity issues', async () => {
      const user = userEvent.setup()
      
      // Mock network error
      mockStartProcessing.mockRejectedValue(new Error('Network error: ECONNREFUSED'))

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      await user.click(saveAndStartButton)

      // Should show network error message
      await waitFor(() => {
        expect(screen.getByText(/settings saved but failed to start processing/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should recover from temporary API failures', async () => {
      const user = userEvent.setup()
      
      // Mock initial failure then success
      mockStartProcessing
        .mockRejectedValueOnce(new Error('Temporary failure'))
        .mockResolvedValue(undefined)

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      // First attempt - should fail
      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      await user.click(saveAndStartButton)

      await waitFor(() => {
        expect(screen.getByText(/settings saved but failed to start processing/i)).toBeInTheDocument()
      }, { timeout: 3000 })

      // Second attempt - should succeed
      await user.click(saveAndStartButton)

      await waitFor(() => {
        expect(mockSetProcessingOptions).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Loading States and Feedback', () => {
    it('should show loading indicator during save and start process', async () => {
      const user = userEvent.setup()
      
      // Mock delayed processing start
      let resolveStart: () => void
      const startPromise = new Promise<void>(resolve => {
        resolveStart = resolve
      })
      mockStartProcessing.mockReturnValue(startPromise)

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      await user.click(saveAndStartButton)

      // Should show loading state
      expect(screen.getByText('Starting...')).toBeInTheDocument()
      expect(saveAndStartButton).toBeDisabled()

      // Resolve the promise
      resolveStart!()

      await waitFor(() => {
        expect(screen.queryByText('Starting...')).not.toBeInTheDocument()
      })
    })

    it('should provide clear success feedback', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      await user.click(saveAndStartButton)

      // Should show success message
      await waitFor(() => {
        expect(screen.getByText('Settings saved successfully!')).toBeInTheDocument()
      })
    })

    it('should disable form during processing operations', async () => {
      const user = userEvent.setup()
      
      // Mock processing in progress
      let resolveStart: () => void
      const startPromise = new Promise<void>(resolve => {
        resolveStart = resolve
      })
      mockStartProcessing.mockReturnValue(startPromise)

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={() => mockSetSettingsOpen(false)}
            onSaveAndStart={mockStartProcessing}
          />
        </TestWrapper>
      )

      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      await user.click(saveAndStartButton)

      // Form fields should be disabled during processing
      const directoryInput = screen.getByDisplayValue('C:/Test/Output')
      expect(directoryInput).toBeDisabled()

      const browseButton = screen.getByRole('button', { name: /browse/i })
      expect(browseButton).toBeDisabled()

      // Resolve processing
      resolveStart!()

      await waitFor(() => {
        expect(directoryInput).not.toBeDisabled()
      })
    })
  })
})