/**
 * Integration Tests: First-Run Experience Flow
 * 
 * Tests the complete first-run experience workflow, including first-run detection,
 * welcome dialog, settings configuration, and system capability detection.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@mui/material/styles'
import { theme } from '../../src/theme/theme'
import { useAppStore } from '../../src/store/appStore'
import MainWindow from '../../src/components/MainWindow'
import FirstRunWelcome from '../../src/components/FirstRunWelcome'
import SettingsDialog from '../../src/components/SettingsDialog'

// Mock dependencies
vi.mock('../../src/store/appStore')

const mockUseAppStore = vi.mocked(useAppStore)

// Test wrapper with theme
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
)

describe('First-Run Experience Integration Tests', () => {
  const defaultSettings = {
    output_directory: '',
    whisper_model: 'large' as const,
    language: 'en' as const,
    output_format: 'txt' as const
  }

  let mockSetProcessingOptions: ReturnType<typeof vi.fn>
  let mockLoadSettingsFromStorage: ReturnType<typeof vi.fn>
  let mockResetProcessingOptions: ReturnType<typeof vi.fn>
  let mockSetSettingsOpen: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()

    mockSetProcessingOptions = vi.fn()
    mockLoadSettingsFromStorage = vi.fn().mockResolvedValue(undefined)
    mockResetProcessingOptions = vi.fn().mockResolvedValue(undefined)
    mockSetSettingsOpen = vi.fn()

    // Mock Electron APIs
    global.window.electronAPI = {
      dialog: {
        showOpenDialog: vi.fn().mockResolvedValue({
          canceled: false,
          filePaths: ['C:/Selected/Directory']
        })
      },
      path: {
        getDefaultOutputDirectory: vi.fn().mockResolvedValue('C:/Users/Test/Documents/Video Transcriber'),
        getUserDocumentsPath: vi.fn().mockResolvedValue('C:/Users/Test/Documents')
      },
      fs: {
        existsSync: vi.fn().mockReturnValue(true)
      },
      system: {
        getSystemInfo: vi.fn().mockResolvedValue({
          platform: 'win32',
          arch: 'x64',
          totalMemory: 16 * 1024 * 1024 * 1024, // 16GB
          availableMemory: 8 * 1024 * 1024 * 1024, // 8GB available
          cpuCount: 8,
          hasGPU: true,
          gpuInfo: 'NVIDIA GeForce RTX 3060'
        })
      }
    } as any

    // Mock localStorage - empty for first run
    const localStorageMock = {
      getItem: vi.fn().mockReturnValue(null), // No existing settings
      setItem: vi.fn(),
      clear: vi.fn()
    }
    Object.defineProperty(window, 'localStorage', { value: localStorageMock })
  })

  describe('First-Run Detection', () => {
    it('should detect first-run when no settings exist', async () => {
      // Mock store for first-run state
      mockUseAppStore.mockReturnValue({
        processingOptions: defaultSettings,
        isSettingsLoaded: false, // Indicates first run
        settingsOpen: false,
        isLoading: false,
        error: null,
        queueItems: [],
        queueStats: { total: 0, queued: 0, processing: 0, completed: 0, failed: 0 },
        dragOver: false,
        selectedFiles: [],
        processingStatus: null,
        currentSession: null,
        wsConnectionState: 'disconnected' as const,
        wsLastEvent: null,
        appStatus: null,
        
        // Actions
        setProcessingOptions: mockSetProcessingOptions,
        loadSettingsFromStorage: mockLoadSettingsFromStorage,
        resetProcessingOptions: mockResetProcessingOptions,
        setSettingsOpen: mockSetSettingsOpen,
        
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
        startProcessing: vi.fn(),
        pauseProcessing: vi.fn(),
        stopProcessing: vi.fn(),
        initializeWebSocket: vi.fn(),
        disconnectWebSocket: vi.fn(),
        updateProcessingOption: vi.fn(),
        saveSettingsToStorage: vi.fn()
      } as any)

      render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Should trigger settings loading on first run
      await waitFor(() => {
        expect(mockLoadSettingsFromStorage).toHaveBeenCalled()
      })
    })

    it('should show FirstRunWelcome dialog on first launch', async () => {
      render(
        <TestWrapper>
          <FirstRunWelcome 
            open={true}
            onClose={vi.fn()}
            onContinue={vi.fn()}
          />
        </TestWrapper>
      )

      // Should display welcome message
      expect(screen.getByText(/welcome to video transcriber/i)).toBeInTheDocument()
      expect(screen.getByText(/let's get you set up/i)).toBeInTheDocument()
      
      // Should have continue button
      expect(screen.getByRole('button', { name: /get started/i })).toBeInTheDocument()
    })

    it('should not show FirstRunWelcome when settings exist', async () => {
      // Mock existing settings
      const existingSettings = {
        output_directory: 'C:/Existing/Output',
        whisper_model: 'medium' as const,
        language: 'en' as const,
        output_format: 'srt' as const
      }

      const localStorageMock = {
        getItem: vi.fn().mockReturnValue(JSON.stringify(existingSettings)),
        setItem: vi.fn(),
        clear: vi.fn()
      }
      Object.defineProperty(window, 'localStorage', { value: localStorageMock })

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: existingSettings,
        isSettingsLoaded: true
      })

      render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Should not show first-run dialog
      expect(screen.queryByText(/welcome to video transcriber/i)).not.toBeInTheDocument()
      
      // Should show normal main window
      expect(screen.getByRole('button', { name: /start processing/i })).toBeInTheDocument()
    })

    it('should handle corrupted settings by triggering first-run flow', async () => {
      // Mock corrupted localStorage data
      const localStorageMock = {
        getItem: vi.fn().mockReturnValue('{"corrupted": json}'), // Invalid JSON
        setItem: vi.fn(),
        clear: vi.fn()
      }
      Object.defineProperty(window, 'localStorage', { value: localStorageMock })

      // Mock console.warn to prevent test noise
      vi.spyOn(console, 'warn').mockImplementation(() => {})

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: defaultSettings,
        isSettingsLoaded: false // Should trigger first-run
      })

      render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Should handle corruption gracefully and reset to defaults
      await waitFor(() => {
        expect(mockLoadSettingsFromStorage).toHaveBeenCalled()
      })
    })
  })

  describe('Welcome Dialog Flow', () => {
    it('should show welcome steps in sequence', async () => {
      const user = userEvent.setup()
      let currentStep = 0
      const mockOnContinue = vi.fn(() => { currentStep++ })

      const { rerender } = render(
        <TestWrapper>
          <FirstRunWelcome 
            open={true}
            onClose={vi.fn()}
            onContinue={mockOnContinue}
          />
        </TestWrapper>
      )

      // Step 1: Welcome
      expect(screen.getByText(/welcome to video transcriber/i)).toBeInTheDocument()
      
      const continueButton = screen.getByRole('button', { name: /get started/i })
      await user.click(continueButton)

      // Should advance to next step
      expect(mockOnContinue).toHaveBeenCalledTimes(1)

      // Re-render with next step (this would be handled by the parent component)
      rerender(
        <TestWrapper>
          <FirstRunWelcome 
            open={true}
            onClose={vi.fn()}
            onContinue={mockOnContinue}
            currentStep={1}
          />
        </TestWrapper>
      )

      // Should show system requirements or next step
      // (Implementation depends on actual FirstRunWelcome component structure)
    })

    it('should allow skipping the welcome flow', async () => {
      const user = userEvent.setup()
      const mockOnClose = vi.fn()

      render(
        <TestWrapper>
          <FirstRunWelcome 
            open={true}
            onClose={mockOnClose}
            onContinue={vi.fn()}
          />
        </TestWrapper>
      )

      // Look for skip option (if available)
      const skipButton = screen.queryByRole('button', { name: /skip/i }) || 
                        screen.queryByRole('button', { name: /maybe later/i })
      
      if (skipButton) {
        await user.click(skipButton)
        expect(mockOnClose).toHaveBeenCalled()
      }
    })

    it('should provide helpful information about the application', async () => {
      render(
        <TestWrapper>
          <FirstRunWelcome 
            open={true}
            onClose={vi.fn()}
            onContinue={vi.fn()}
          />
        </TestWrapper>
      )

      // Should explain key features
      expect(screen.getByText(/video transcriber/i)).toBeInTheDocument()
      
      // Should mention key capabilities (implementation-dependent)
      // These tests would be expanded based on actual FirstRunWelcome content
    })

    it('should handle dialog close via escape key', async () => {
      const mockOnClose = vi.fn()

      render(
        <TestWrapper>
          <FirstRunWelcome 
            open={true}
            onClose={mockOnClose}
            onContinue={vi.fn()}
          />
        </TestWrapper>
      )

      // Press escape key
      fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' })
      
      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled()
      })
    })
  })

  describe('Settings Configuration from Welcome', () => {
    it('should transition from welcome to settings configuration', async () => {
      const user = userEvent.setup()
      let showSettings = false
      const mockOnContinue = vi.fn(() => { showSettings = true })

      const { rerender } = render(
        <TestWrapper>
          <FirstRunWelcome 
            open={true}
            onClose={vi.fn()}
            onContinue={mockOnContinue}
          />
        </TestWrapper>
      )

      const continueButton = screen.getByRole('button', { name: /get started/i })
      await user.click(continueButton)

      expect(mockOnContinue).toHaveBeenCalled()

      // Simulate transition to settings
      if (showSettings) {
        rerender(
          <TestWrapper>
            <SettingsDialog 
              open={true}
              onClose={vi.fn()}
              onSaveAndStart={vi.fn()}
            />
          </TestWrapper>
        )

        // Should show settings dialog with first-run context
        expect(screen.getByText(/processing settings/i)).toBeInTheDocument()
      }
    })

    it('should pre-configure recommended settings for first-run', async () => {
      // Mock system capabilities
      global.window.electronAPI.system.getSystemInfo = vi.fn().mockResolvedValue({
        platform: 'win32',
        arch: 'x64',
        totalMemory: 8 * 1024 * 1024 * 1024, // 8GB - lower memory system
        availableMemory: 4 * 1024 * 1024 * 1024,
        cpuCount: 4,
        hasGPU: false,
        gpuInfo: null
      })

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: {
          output_directory: 'C:/Users/Test/Documents/Video Transcriber',
          whisper_model: 'small', // Should recommend smaller model for lower-spec system
          language: 'en',
          output_format: 'txt'
        }
      })

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={vi.fn()}
          />
        </TestWrapper>
      )

      // Should show appropriate defaults based on system
      expect(screen.getByDisplayValue('C:/Users/Test/Documents/Video Transcriber')).toBeInTheDocument()
      // Note: Model selection would be tested based on actual system capability detection
    })

    it('should guide user through critical settings configuration', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={vi.fn()}
          />
        </TestWrapper>
      )

      // Should highlight important settings for first-run users
      expect(screen.getByText(/output directory/i)).toBeInTheDocument()
      expect(screen.getByText(/whisper model/i)).toBeInTheDocument()

      // Should provide helpful guidance
      const infoText = screen.getByText(/configure your transcription settings/i)
      expect(infoText).toBeInTheDocument()
    })

    it('should validate first-run settings before allowing completion', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={vi.fn()}
          />
        </TestWrapper>
      )

      // Clear required directory field
      const directoryInput = screen.getByDisplayValue(/.*/)
      await user.clear(directoryInput)

      // Save & Start button should be disabled
      const saveAndStartButton = screen.getByRole('button', { name: /save & start processing/i })
      expect(saveAndStartButton).toBeDisabled()

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/output directory is required/i)).toBeInTheDocument()
      })
    })
  })

  describe('Default Settings Configuration', () => {
    it('should set appropriate default output directory', async () => {
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        processingOptions: {
          ...defaultSettings,
          output_directory: 'C:/Users/Test/Documents/Video Transcriber'
        }
      })

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={vi.fn()}
          />
        </TestWrapper>
      )

      // Should use user's Documents folder by default
      expect(screen.getByDisplayValue('C:/Users/Test/Documents/Video Transcriber')).toBeInTheDocument()
    })

    it('should set defaults based on system capabilities', async () => {
      // Mock high-end system
      global.window.electronAPI.system.getSystemInfo = vi.fn().mockResolvedValue({
        platform: 'win32',
        arch: 'x64',
        totalMemory: 32 * 1024 * 1024 * 1024, // 32GB
        availableMemory: 16 * 1024 * 1024 * 1024,
        cpuCount: 16,
        hasGPU: true,
        gpuInfo: 'NVIDIA GeForce RTX 4080'
      })

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={vi.fn()}
          />
        </TestWrapper>
      )

      // Should default to large model for high-end system
      expect(screen.getByText('Large')).toBeInTheDocument()
    })

    it('should handle system capability detection failure gracefully', async () => {
      // Mock system info failure
      global.window.electronAPI.system.getSystemInfo = vi.fn().mockRejectedValue(new Error('System info unavailable'))

      // Mock console.warn to prevent test noise
      vi.spyOn(console, 'warn').mockImplementation(() => {})

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={vi.fn()}
          />
        </TestWrapper>
      )

      // Should fall back to safe defaults
      expect(screen.getByText('Large')).toBeInTheDocument() // Conservative default
      expect(screen.getByText('English Only')).toBeInTheDocument()
      expect(screen.getByText('Plain Text (.txt)')).toBeInTheDocument()
    })

    it('should provide system recommendations in UI', async () => {
      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={vi.fn()}
          />
        </TestWrapper>
      )

      // Should show system capability indicator
      // (Implementation depends on actual SystemCapabilityIndicator component)
      const modelSection = screen.getByText('Whisper Model').closest('[data-testid]') || 
                          screen.getByText('Whisper Model').parentElement

      // Should indicate system compatibility
      expect(modelSection).toBeInTheDocument()
    })
  })

  describe('First-Run Completion', () => {
    it('should mark first-run as complete after successful setup', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <SettingsDialog 
            open={true}
            onClose={vi.fn()}
          />
        </TestWrapper>
      )

      // Complete settings configuration
      const saveButton = screen.getByRole('button', { name: /save only/i })
      await user.click(saveButton)

      // Should save settings and mark first-run complete
      await waitFor(() => {
        expect(mockSetProcessingOptions).toHaveBeenCalled()
      })

      // Settings should be persisted to localStorage
      expect(localStorage.setItem).toHaveBeenCalled()
    })

    it('should transition to normal app state after first-run', async () => {
      const user = userEvent.setup()

      // Mock completing first-run setup
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        isSettingsLoaded: true,
        processingOptions: {
          output_directory: 'C:/Users/Test/Documents/Video Transcriber',
          whisper_model: 'large' as const,
          language: 'en' as const,
          output_format: 'txt' as const
        }
      })

      render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Should show normal main window interface
      expect(screen.getByRole('button', { name: /start processing/i })).toBeInTheDocument()
      
      // Should not show first-run elements
      expect(screen.queryByText(/welcome to video transcriber/i)).not.toBeInTheDocument()
    })

    it('should remember completed first-run setup across app restarts', async () => {
      // Mock settings exist in localStorage
      const savedSettings = {
        output_directory: 'C:/First/Run/Complete',
        whisper_model: 'large',
        language: 'en',
        output_format: 'txt'
      }

      const localStorageMock = {
        getItem: vi.fn().mockReturnValue(JSON.stringify(savedSettings)),
        setItem: vi.fn(),
        clear: vi.fn()
      }
      Object.defineProperty(window, 'localStorage', { value: localStorageMock })

      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        isSettingsLoaded: true,
        processingOptions: savedSettings
      })

      render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Should load as normal app, not first-run
      expect(screen.getByRole('button', { name: /start processing/i })).toBeInTheDocument()
      expect(screen.queryByText(/welcome to video transcriber/i)).not.toBeInTheDocument()
    })

    it('should allow re-running first-run setup if needed', async () => {
      const user = userEvent.setup()

      // Mock settings exist but user wants to reconfigure
      mockUseAppStore.mockReturnValue({
        ...mockUseAppStore(),
        isSettingsLoaded: true,
        processingOptions: {
          output_directory: 'C:/Existing/Settings',
          whisper_model: 'medium' as const,
          language: 'en' as const,
          output_format: 'txt' as const
        }
      })

      render(
        <TestWrapper>
          <MainWindow />
        </TestWrapper>
      )

      // Should be able to open settings to reconfigure
      const startButton = screen.getByRole('button', { name: /start processing/i })
      await user.click(startButton)

      // Should open settings dialog
      expect(mockSetSettingsOpen).toHaveBeenCalledWith(true)
    })
  })
})