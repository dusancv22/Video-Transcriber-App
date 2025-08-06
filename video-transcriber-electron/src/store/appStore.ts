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
  whisper_model: 'large', // Default to highest accuracy
  language: 'en', // English-only for consistency based on project notes
  output_format: 'txt' // Simple text format as default
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
const getDefaultOutputDirectory = async (): Promise<string> => {
  // Use safe default path to avoid "B:/" or invalid drive errors
  try {
    // Check if running in Electron environment with API available
    if (typeof window !== 'undefined' && (window as any)?.electronAPI?.path?.getDefaultOutputDirectory) {
      const path = await (window as any).electronAPI.path.getDefaultOutputDirectory()
      return path
    }
    
    // Safe fallback that uses relative path to avoid drive access issues
    // This will resolve relative to the application's working directory
    return './Video Transcriber Output'
  } catch (error) {
    console.warn('Failed to determine default output directory, using safe fallback:', error)
    // Absolute safe fallback - relative to current working directory
    return './transcripts'
  }
}
import { VideoTranscriberAPI, APIUtils } from '../services/api'
import { websocketService, WebSocketConnectionState } from '../services/websocket'

// Debounce utility for queue updates
class QueueUpdateManager {
  private debounceTimer: NodeJS.Timeout | null = null
  private pendingUpdate = false
  private isWebSocketUpdateActive = false
  private lastUpdateTimestamp = 0
  
  // Debounce queue fetches to prevent rapid successive calls
  debounceFetchQueue(fetchFn: () => Promise<void>, delay: number = 500) {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer)
    }
    
    this.pendingUpdate = true
    this.debounceTimer = setTimeout(async () => {
      if (this.pendingUpdate) {
        this.pendingUpdate = false
        await fetchFn()
      }
      this.debounceTimer = null
    }, delay)
  }
  
  // Track WebSocket updates to prevent duplicate fetches
  markWebSocketUpdate() {
    this.isWebSocketUpdateActive = true
    this.lastUpdateTimestamp = Date.now()
    // Clear WebSocket update flag after short period
    setTimeout(() => {
      this.isWebSocketUpdateActive = false
    }, 1000)
  }
  
  // Check if we should skip manual fetch due to recent WebSocket update
  shouldSkipManualFetch(): boolean {
    const timeSinceWebSocketUpdate = Date.now() - this.lastUpdateTimestamp
    return this.isWebSocketUpdateActive && timeSinceWebSocketUpdate < 1000
  }
  
  // Cancel any pending updates
  cancelPending() {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = null
    }
    this.pendingUpdate = false
  }
}

// Global queue update manager instance
const queueUpdateManager = new QueueUpdateManager()

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
  resetProcessingOptions: () => Promise<void>
  loadSettingsFromStorage: () => Promise<void>
  saveSettingsToStorage: () => void
  
  // API actions
  fetchAppStatus: () => Promise<void>
  fetchQueue: () => Promise<void>
  fetchQueueInternal: (isWebSocketTriggered?: boolean) => Promise<void>
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
const initializeProcessingOptions = async (): Promise<ProcessingOptions> => {
  const options = { ...DEFAULT_PROCESSING_OPTIONS }
  if (!options.output_directory) {
    options.output_directory = await getDefaultOutputDirectory()
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
  processingOptions: { ...DEFAULT_PROCESSING_OPTIONS },
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
              // Mark WebSocket update as active to prevent duplicate fetches
              queueUpdateManager.markWebSocketUpdate()
              // Use debounced queue refresh for WebSocket updates
              queueUpdateManager.debounceFetchQueue(async () => {
                console.log('🔄 WebSocket: Debounced queue update triggered')
                await get().fetchQueueInternal(true) // Skip duplication check for WebSocket updates
              }, 300)
              break
              
            case 'progress_update':
              // Update specific queue item progress without full queue refresh
              const progressEvent = event as any
              if (progressEvent.file_id) {
                get().updateQueueItem(progressEvent.file_id, {
                  progress: progressEvent.progress || 0,
                  current_step: progressEvent.step || '',
                  estimated_time_remaining: progressEvent.estimated_time_remaining,
                  status: 'processing' // Ensure status is set to processing during progress updates
                })
                console.log(`📈 WebSocket: Progress update for ${progressEvent.file_id}: ${progressEvent.progress}% - ${progressEvent.step}`)
              }
              break
              
            case 'processing_status_change':
              // Debounce processing status updates as well
              queueUpdateManager.debounceFetchQueue(async () => {
                await get().fetchProcessingStatus()
              }, 200)
              break
              
            case 'file_completed':
              const completedEvent = event as any
              if (completedEvent.file_id) {
                get().updateQueueItem(completedEvent.file_id, {
                  status: 'completed',
                  progress: 100,
                  output_file: completedEvent.output_file,
                  processing_time: completedEvent.processing_time,
                  completed_at: event.timestamp,
                  current_step: 'Completed',
                  estimated_time_remaining: 0
                })
                console.log(`✅ WebSocket: File completed - ${completedEvent.file_id}`)
                // Also update queue stats immediately for visual feedback
                queueUpdateManager.debounceFetchQueue(async () => {
                  await get().fetchQueueInternal(true)
                }, 100) // Quick update for completion
              }
              break
              
            case 'file_failed':
              const failedEvent = event as any
              if (failedEvent.file_id) {
                get().updateQueueItem(failedEvent.file_id, {
                  status: 'failed',
                  error: failedEvent.error,
                  error_code: failedEvent.error_code,
                  progress: 0,
                  current_step: 'Failed',
                  completed_at: event.timestamp,
                  estimated_time_remaining: 0
                })
                console.log(`❌ WebSocket: File failed - ${failedEvent.file_id}: ${failedEvent.error}`)
              }
              break
              
            case 'overall_progress_update':
              // Handle overall processing progress for session tracking
              const overallEvent = event as any
              if (overallEvent.processed_files !== undefined && overallEvent.total_files !== undefined) {
                // Update session progress if we have a current session
                const currentSession = get().currentSession
                if (currentSession) {
                  get().setCurrentSession({
                    ...currentSession,
                    completed_files: overallEvent.processed_files,
                    total_files: overallEvent.total_files
                  })
                }
                console.log(`📊 WebSocket: Overall progress ${overallEvent.processed_files}/${overallEvent.total_files} files (${overallEvent.overall_progress}%)`)
              }
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
        
        resetProcessingOptions: async () => {
          const defaultOptions = await initializeProcessingOptions()
          set({ processingOptions: defaultOptions })
          saveSettingsToLocalStorage(defaultOptions)
        },
        
        loadSettingsFromStorage: async () => {
          try {
            const loadedOptions = loadSettingsFromLocalStorage()
            // Ensure output directory is set
            if (!loadedOptions.output_directory) {
              loadedOptions.output_directory = await getDefaultOutputDirectory()
            }
            set({ 
              processingOptions: loadedOptions,
              isSettingsLoaded: true 
            })
          } catch (error) {
            console.error('Failed to load settings:', error)
            const defaultOptions = await initializeProcessingOptions()
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
          // Check if we should skip due to recent WebSocket update
          if (queueUpdateManager.shouldSkipManualFetch()) {
            console.log('⏭️ Store: Skipping manual queue fetch due to recent WebSocket update')
            return
          }
          
          await get().fetchQueueInternal(false)
        },
        
        fetchQueueInternal: async (isWebSocketTriggered: boolean = false) => {
          try {
            const source = isWebSocketTriggered ? 'WebSocket' : 'Manual'
            console.log(`📥 Store: Fetching queue from API (${source})...`)
            const response = await VideoTranscriberAPI.getQueue()
            console.log(`✅ Store: Queue response received (${source}):`, response)
            console.log(`📊 Store: Queue items count (${source}):`, response.items?.length || 0)
            get().setQueueItems(response.items)
            console.log(`🔄 Store: Queue items updated in store (${source})`)
          } catch (error) {
            console.error('❌ Store: Failed to fetch queue:', error)
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
            console.log('🗃️ Store: addFiles called with:', files)
            set({ isLoading: true, error: null })
            
            // Validate and format file paths for current environment
            const pathValidation = APIUtils.validateFilePaths(files)
            const formattedPaths = APIUtils.formatFilePaths(pathValidation.valid)
            
            // Log any warnings about path handling
            if (pathValidation.warnings.length > 0) {
              console.warn('⚠️ Store: Path validation warnings:')
              pathValidation.warnings.forEach(warning => console.warn(`  - ${warning}`))
            }
            
            // Report invalid paths
            if (pathValidation.invalid.length > 0) {
              console.error('❌ Store: Invalid file paths detected:', pathValidation.invalid)
              set({ error: `Some file paths were invalid and skipped: ${pathValidation.invalid.join(', ')}` })
            }
            
            // Skip API call if no valid files
            if (formattedPaths.length === 0) {
              console.error('❌ Store: No valid file paths to process')
              set({ error: 'No valid file paths were provided. Please check the selected files.' })
              return
            }
            
            console.log('🌐 Store: Making API call to add files...')
            console.log('📁 Store: Formatted paths:', formattedPaths)
            const response = await VideoTranscriberAPI.addFiles(formattedPaths)
            console.log('✅ Store: API response received:', response)
            
            if (response.errors.length > 0) {
              const errorMessages = response.errors.map(e => `${e.file}: ${e.error}`).join('\n')
              console.warn('⚠️ Store: Some files had errors:', errorMessages)
              set({ error: `Some files could not be added:\n${errorMessages}` })
            }
            
            console.log('📡 Store: Queue will be updated via WebSocket event...')
            // Use debounced update in case WebSocket event doesn't arrive quickly
            // This provides a fallback while preventing duplicate fetches if WebSocket works
            queueUpdateManager.debounceFetchQueue(async () => {
              console.log('🔄 Store: Fallback queue update after addFiles')
              await get().fetchQueueInternal(false)
            }, 1000) // Longer delay to allow WebSocket update to happen first
            
          } catch (error) {
            console.error('❌ Store: Failed to add files:', error)
            set({ error: `Failed to add files: ${error}` })
          } finally {
            set({ isLoading: false })
          }
        },

        addDirectory: async (directory, recursive = true) => {
          try {
            console.log('📁 Store: addDirectory called with:', directory, 'recursive:', recursive)
            set({ isLoading: true, error: null })
            const response = await VideoTranscriberAPI.addDirectory(directory, recursive)
            console.log('✅ Store: Directory API response received:', response)
            
            if (response.errors.length > 0) {
              const errorMessages = response.errors.map(e => `${e.file}: ${e.error}`).join('\n')
              console.warn('⚠️ Store: Some files had errors:', errorMessages)
              set({ error: `Some files could not be added:\n${errorMessages}` })
            }
            
            console.log('📡 Store: Queue will be updated via WebSocket event...')
            // Use debounced update for directory addition as well
            queueUpdateManager.debounceFetchQueue(async () => {
              console.log('🔄 Store: Fallback queue update after addDirectory')
              await get().fetchQueueInternal(false)
            }, 1000)
            
          } catch (error) {
            console.error('❌ Store: Failed to add directory:', error)
            set({ error: `Failed to add directory: ${error}` })
          } finally {
            set({ isLoading: false })
          }
        },

        removeFromQueue: async (id) => {
          try {
            console.log('🗑️ Store: removeFromQueue called with ID:', id)
            await VideoTranscriberAPI.removeFromQueue(id)
            console.log('✅ Store: File removal API call successful')
            
            // Use debounced queue update for removal as well
            queueUpdateManager.debounceFetchQueue(async () => {
              console.log('🔄 Store: Queue update after removeFromQueue')
              await get().fetchQueueInternal(false)
            }, 300) // Shorter delay for removals
            
          } catch (error) {
            console.error('❌ Store: Failed to remove file:', error)
            set({ error: `Failed to remove file: ${error}` })
          }
        },

        startProcessing: async () => {
          console.log('🎬 AppStore: startProcessing called')
          try {
            set({ isLoading: true, error: null })
            const options = get().processingOptions
            console.log('📝 Processing options from store:', options)
            console.log('🔍 Store state at startProcessing:', {
              queueItemsLength: get().queueItems.length,
              queueStats: get().queueStats
            })
            
            // Check if there are files in queue
            const queueItems = get().queueItems
            console.log('📋 Current queue items:', queueItems)
            
            if (!queueItems || queueItems.length === 0) {
              console.error('❌ No files in queue to process')
              throw new Error('No files in queue. Please add video files before starting processing.')
            }
            
            const queuedFiles = queueItems.filter(item => item.status === 'queued')
            console.log(`📊 Found ${queuedFiles.length} queued files out of ${queueItems.length} total`)
            
            if (queuedFiles.length === 0) {
              console.error('❌ No queued files found')
              throw new Error('No files are queued for processing. Please add video files first.')
            }
            
            console.log('🌐 Making API call to start processing...')
            const result = await VideoTranscriberAPI.startProcessing(options)
            console.log('✅ API call successful:', result)
            
            console.log('📡 Status will be updated via WebSocket event')
            // Status will be updated via WebSocket event
            
          } catch (error) {
            console.error('❌ Error in startProcessing:', error)
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
            console.error('Error details:', {
              message: errorMessage,
              stack: error instanceof Error ? error.stack : undefined,
              type: typeof error,
              error
            })
            set({ error: `Failed to start processing: ${errorMessage}` })
            throw error // Re-throw to be caught by settings dialog
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
              'overall_progress_update',
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
          // Cancel any pending queue updates before disconnecting
          queueUpdateManager.cancelPending()
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