/**
 * Main application state store using Zustand
 */

import { create } from 'zustand'
import { devtools, subscribeWithSelector } from 'zustand/middleware'
import { 
  QueueItem, 
  ProcessingStatus, 
  ApplicationStatus, 
  WebSocketEvent,
  ProcessingSession
} from '../types/api'

// Processing options interface with strict typing
export interface ProcessingOptions {
  output_directory: string
  whisper_model: 'base' | 'small' | 'medium' | 'large'
  language: 'en' | 'auto'
  output_format: 'txt' | 'srt' | 'vtt'
}

// Default settings configuration
const DEFAULT_PROCESSING_OPTIONS: ProcessingOptions = {
  output_directory: '', // Will be set dynamically to user's Documents or Downloads folder
  whisper_model: 'large',
  language: 'en',
  output_format: 'txt'
}

// Settings validation functions
const isValidWhisperModel = (value: string): value is ProcessingOptions['whisper_model'] => {
  return ['base', 'small', 'medium', 'large'].includes(value)
}

const isValidLanguage = (value: string): value is ProcessingOptions['language'] => {
  return ['en', 'auto'].includes(value)
}

const isValidOutputFormat = (value: string): value is ProcessingOptions['output_format'] => {
  return ['txt', 'srt', 'vtt'].includes(value)
}

const isValidDirectory = (path: string): boolean => {
  // Basic path validation - not empty and reasonable length
  return typeof path === 'string' && path.length > 0 && path.length < 500
}

// Settings validation function
const validateProcessingOptions = (options: any): ProcessingOptions => {
  const validated: ProcessingOptions = { ...DEFAULT_PROCESSING_OPTIONS }
  
  if (options && typeof options === 'object') {
    // Validate output_directory
    if (typeof options.output_directory === 'string' && isValidDirectory(options.output_directory)) {
      validated.output_directory = options.output_directory
    }
    
    // Validate whisper_model
    if (isValidWhisperModel(options.whisper_model)) {
      validated.whisper_model = options.whisper_model
    }
    
    // Validate language
    if (isValidLanguage(options.language)) {
      validated.language = options.language
    }
    
    // Validate output_format
    if (isValidOutputFormat(options.output_format)) {
      validated.output_format = options.output_format
    }
  }
  
  return validated
}

// LocalStorage operations with error handling
const SETTINGS_STORAGE_KEY = 'video-transcriber-settings'

const loadSettingsFromLocalStorage = (): ProcessingOptions => {
  try {
    const stored = localStorage.getItem(SETTINGS_STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      return validateProcessingOptions(parsed)
    }
  } catch (error) {
    console.warn('Failed to load settings from localStorage:', error)
  }
  return { ...DEFAULT_PROCESSING_OPTIONS }
}

const saveSettingsToLocalStorage = (options: ProcessingOptions): void => {
  try {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(options))
  } catch (error) {
    console.error('Failed to save settings to localStorage:', error)
  }
}

// Initialize default output directory
const getDefaultOutputDirectory = (): string => {
  // Fallback to a reasonable default for cross-platform compatibility
  return 'C:/Output/Transcripts'
}
import { VideoTranscriberAPI } from '../services/api'
import { websocketService, WebSocketConnectionState } from '../services/websocket'

export interface AppState {
  // Application status
  appStatus: ApplicationStatus | null
  isLoading: boolean
  error: string | null

  // WebSocket connection
  wsConnectionState: WebSocketConnectionState
  wsLastEvent: WebSocketEvent | null

  // Queue management
  queueItems: QueueItem[]
  queueStats: {
    total: number
    queued: number
    processing: number
    completed: number
    failed: number
  }

  // Processing status
  processingStatus: ProcessingStatus | null
  currentSession: ProcessingSession | null

  // UI state
  selectedFiles: string[]
  dragOver: boolean
  settingsOpen: boolean
  
  // Processing options with proper typing
  processingOptions: ProcessingOptions
  isSettingsLoaded: boolean
}

export interface AppActions {
  // Application status actions
  setAppStatus: (status: ApplicationStatus) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  
  // WebSocket actions
  setWsConnectionState: (state: WebSocketConnectionState) => void
  handleWebSocketEvent: (event: WebSocketEvent) => void
  
  // Queue actions
  setQueueItems: (items: QueueItem[]) => void
  addQueueItems: (items: QueueItem[]) => void
  updateQueueItem: (id: string, updates: Partial<QueueItem>) => void
  removeQueueItem: (id: string) => void
  clearQueue: () => void
  
  // Processing actions
  setProcessingStatus: (status: ProcessingStatus) => void
  setCurrentSession: (session: ProcessingSession | null) => void
  
  // UI actions
  setSelectedFiles: (files: string[]) => void
  setDragOver: (dragOver: boolean) => void
  setSettingsOpen: (open: boolean) => void
  
  // Processing options actions
  setProcessingOptions: (options: ProcessingOptions) => void
  updateProcessingOption: <K extends keyof ProcessingOptions>(key: K, value: ProcessingOptions[K]) => void
  resetProcessingOptions: () => void
  loadSettingsFromStorage: () => void
  saveSettingsToStorage: () => void
  
  // API actions
  fetchAppStatus: () => Promise<void>
  fetchQueue: () => Promise<void>
  fetchProcessingStatus: () => Promise<void>
  addFiles: (files: string[]) => Promise<void>
  addDirectory: (directory: string, recursive?: boolean) => Promise<void>
  removeFromQueue: (id: string) => Promise<void>
  startProcessing: () => Promise<void>
  pauseProcessing: () => Promise<void>
  stopProcessing: () => Promise<void>
  
  // WebSocket actions
  initializeWebSocket: () => Promise<void>
  disconnectWebSocket: () => void
}

type AppStore = AppState & AppActions

// Initialize processing options with default output directory
const initializeProcessingOptions = (): ProcessingOptions => {
  const options = { ...DEFAULT_PROCESSING_OPTIONS }
  if (!options.output_directory) {
    options.output_directory = getDefaultOutputDirectory()
  }
  return options
}

const initialState: AppState = {
  // Application status
  appStatus: null,
  isLoading: false,
  error: null,

  // WebSocket connection
  wsConnectionState: 'disconnected',
  wsLastEvent: null,

  // Queue management
  queueItems: [],
  queueStats: {
    total: 0,
    queued: 0,
    processing: 0,
    completed: 0,
    failed: 0
  },

  // Processing status
  processingStatus: null,
  currentSession: null,

  // UI state
  selectedFiles: [],
  dragOver: false,
  settingsOpen: false,
  
  // Processing options with proper initialization
  processingOptions: initializeProcessingOptions(),
  isSettingsLoaded: false
}

export const useAppStore = create<AppStore>()(
  devtools(
    subscribeWithSelector(
      (set, get) => {
        const store = {
          ...initialState,

        // Application status actions
        setAppStatus: (status) => set({ appStatus: status }),
        setLoading: (loading) => set({ isLoading: loading }),
        setError: (error) => set({ error }),

        // WebSocket actions
        setWsConnectionState: (state) => set({ wsConnectionState: state }),
        handleWebSocketEvent: (event) => {
          set({ wsLastEvent: event })
          
          // Handle specific event types
          switch (event.type) {
            case 'queue_update':
              // Refresh queue when updates occur
              get().fetchQueue()
              break
              
            case 'progress_update':
              // Update specific queue item progress
              const progressEvent = event as any
              get().updateQueueItem(progressEvent.file_id, {
                progress: progressEvent.progress,
                current_step: progressEvent.step,
                estimated_time_remaining: progressEvent.estimated_time_remaining
              })
              break
              
            case 'processing_status_change':
              // Refresh processing status
              get().fetchProcessingStatus()
              break
              
            case 'file_completed':
              const completedEvent = event as any
              get().updateQueueItem(completedEvent.file_id, {
                status: 'completed',
                progress: 100,
                output_file: completedEvent.output_file,
                processing_time: completedEvent.processing_time,
                completed_at: event.timestamp
              })
              break
              
            case 'file_failed':
              const failedEvent = event as any
              get().updateQueueItem(failedEvent.file_id, {
                status: 'failed',
                error: failedEvent.error,
                error_code: failedEvent.error_code
              })
              break
          }
        },

        // Queue actions
        setQueueItems: (items) => {
          const stats = {
            total: items.length,
            queued: items.filter(i => i.status === 'queued').length,
            processing: items.filter(i => i.status === 'processing').length,
            completed: items.filter(i => i.status === 'completed').length,
            failed: items.filter(i => i.status === 'failed').length
          }
          set({ queueItems: items, queueStats: stats })
        },
        
        addQueueItems: (items) => {
          const currentItems = get().queueItems
          const newItems = [...currentItems, ...items]
          get().setQueueItems(newItems)
        },
        
        updateQueueItem: (id, updates) => {
          const items = get().queueItems.map(item =>
            item.id === id ? { ...item, ...updates } : item
          )
          get().setQueueItems(items)
        },
        
        removeQueueItem: (id) => {
          const items = get().queueItems.filter(item => item.id !== id)
          get().setQueueItems(items)
        },
        
        clearQueue: () => set({ queueItems: [], queueStats: initialState.queueStats }),

        // Processing actions
        setProcessingStatus: (status) => set({ processingStatus: status }),
        setCurrentSession: (session) => set({ currentSession: session }),

        // UI actions
        setSelectedFiles: (files) => set({ selectedFiles: files }),
        setDragOver: (dragOver) => set({ dragOver }),
        setSettingsOpen: (open) => set({ settingsOpen: open }),

        // Processing options actions
        setProcessingOptions: (options) => {
          set({ processingOptions: options })
          saveSettingsToLocalStorage(options)
        },
        
        updateProcessingOption: (key, value) => {
          const currentOptions = get().processingOptions
          const updatedOptions = { ...currentOptions, [key]: value }
          set({ processingOptions: updatedOptions })
          saveSettingsToLocalStorage(updatedOptions)
        },
        
        resetProcessingOptions: () => {
          const defaultOptions = initializeProcessingOptions()
          set({ processingOptions: defaultOptions })
          saveSettingsToLocalStorage(defaultOptions)
        },
        
        loadSettingsFromStorage: () => {
          try {
            const loadedOptions = loadSettingsFromLocalStorage()
            // Ensure output directory is set
            if (!loadedOptions.output_directory) {
              loadedOptions.output_directory = getDefaultOutputDirectory()
            }
            set({ 
              processingOptions: loadedOptions,
              isSettingsLoaded: true 
            })
          } catch (error) {
            console.error('Failed to load settings:', error)
            const defaultOptions = initializeProcessingOptions()
            set({ 
              processingOptions: defaultOptions,
              isSettingsLoaded: true 
            })
          }
        },
        
        saveSettingsToStorage: () => {
          const options = get().processingOptions
          saveSettingsToLocalStorage(options)
        },

        // API actions
        fetchAppStatus: async () => {
          try {
            set({ isLoading: true, error: null })
            const status = await VideoTranscriberAPI.getStatus()
            set({ appStatus: status })
          } catch (error) {
            set({ error: `Failed to fetch app status: ${error}` })
          } finally {
            set({ isLoading: false })
          }
        },

        fetchQueue: async () => {
          try {
            const response = await VideoTranscriberAPI.getQueue()
            get().setQueueItems(response.items)
          } catch (error) {
            set({ error: `Failed to fetch queue: ${error}` })
          }
        },

        fetchProcessingStatus: async () => {
          try {
            const status = await VideoTranscriberAPI.getProcessingStatus()
            set({ processingStatus: status })
          } catch (error) {
            set({ error: `Failed to fetch processing status: ${error}` })
          }
        },

        addFiles: async (files) => {
          try {
            set({ isLoading: true, error: null })
            const response = await VideoTranscriberAPI.addFiles(files)
            
            if (response.errors.length > 0) {
              const errorMessages = response.errors.map(e => `${e.file}: ${e.error}`).join('\n')
              set({ error: `Some files could not be added:\n${errorMessages}` })
            }
            
            // Queue will be updated via WebSocket event
          } catch (error) {
            set({ error: `Failed to add files: ${error}` })
          } finally {
            set({ isLoading: false })
          }
        },

        addDirectory: async (directory, recursive = true) => {
          try {
            set({ isLoading: true, error: null })
            const response = await VideoTranscriberAPI.addDirectory(directory, recursive)
            
            if (response.errors.length > 0) {
              const errorMessages = response.errors.map(e => `${e.file}: ${e.error}`).join('\n')
              set({ error: `Some files could not be added:\n${errorMessages}` })
            }
            
            // Queue will be updated via WebSocket event
          } catch (error) {
            set({ error: `Failed to add directory: ${error}` })
          } finally {
            set({ isLoading: false })
          }
        },

        removeFromQueue: async (id) => {
          try {
            await VideoTranscriberAPI.removeFromQueue(id)
            // Queue will be updated via WebSocket event
          } catch (error) {
            set({ error: `Failed to remove file: ${error}` })
          }
        },

        startProcessing: async () => {
          try {
            set({ isLoading: true, error: null })
            const options = get().processingOptions
            await VideoTranscriberAPI.startProcessing(options)
            // Status will be updated via WebSocket event
          } catch (error) {
            set({ error: `Failed to start processing: ${error}` })
          } finally {
            set({ isLoading: false })
          }
        },

        pauseProcessing: async () => {
          try {
            await VideoTranscriberAPI.pauseProcessing()
            // Status will be updated via WebSocket event
          } catch (error) {
            set({ error: `Failed to pause processing: ${error}` })
          }
        },

        stopProcessing: async () => {
          try {
            await VideoTranscriberAPI.stopProcessing()
            // Status will be updated via WebSocket event
          } catch (error) {
            set({ error: `Failed to stop processing: ${error}` })
          }
        },

        // WebSocket actions
        initializeWebSocket: async () => {
          try {
            // Set up connection state handler
            websocketService.on('connection', (event: any) => {
              get().setWsConnectionState(event.state)
            })
            
            // Set up event handlers for all event types
            const eventTypes = [
              'progress_update',
              'queue_update', 
              'processing_status_change',
              'file_completed',
              'file_failed',
              'session_complete',
              'error',
              'system_notification'
            ]
            
            eventTypes.forEach(eventType => {
              websocketService.on(eventType as any, (event) => {
                get().handleWebSocketEvent(event)
              })
            })
            
            // Connect to WebSocket
            await websocketService.connect()
            
          } catch (error) {
            set({ error: `Failed to initialize WebSocket: ${error}` })
          }
        },

        disconnectWebSocket: () => {
          websocketService.disconnect()
          set({ wsConnectionState: 'disconnected' })
        }
        }
        
        // Auto-load settings when store is created
        setTimeout(() => {
          store.loadSettingsFromStorage()
        }, 0)
        
        return store
      }
    ),
    {
      name: 'video-transcriber-store'
    }
  )
)

// Selector hooks for specific state slices
export const useQueueStats = () => useAppStore(state => state.queueStats)
export const useProcessingStatus = () => useAppStore(state => state.processingStatus)
export const useWebSocketState = () => useAppStore(state => state.wsConnectionState)
export const useAppError = () => useAppStore(state => state.error)
export const useIsLoading = () => useAppStore(state => state.isLoading)

// Settings-specific selector hooks
export const useProcessingOptions = () => useAppStore(state => state.processingOptions)
export const useIsSettingsLoaded = () => useAppStore(state => state.isSettingsLoaded)
export const useOutputDirectory = () => useAppStore(state => state.processingOptions.output_directory)
export const useWhisperModel = () => useAppStore(state => state.processingOptions.whisper_model)
export const useLanguage = () => useAppStore(state => state.processingOptions.language)
export const useOutputFormat = () => useAppStore(state => state.processingOptions.output_format)

// Settings action hooks for convenience
export const useSettingsActions = () => useAppStore(state => ({
  setProcessingOptions: state.setProcessingOptions,
  updateProcessingOption: state.updateProcessingOption,
  resetProcessingOptions: state.resetProcessingOptions,
  loadSettingsFromStorage: state.loadSettingsFromStorage,
  saveSettingsToStorage: state.saveSettingsToStorage
}))

// Export types and defaults for external use
export { DEFAULT_PROCESSING_OPTIONS }
export type { ProcessingOptions }