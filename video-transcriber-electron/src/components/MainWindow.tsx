import React, { useState, useEffect } from 'react'
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Paper,
  Button,
  IconButton,
  useTheme,
  alpha
} from '@mui/material'
import {
  Stop,
  FolderOpen,
  Clear,
  Queue as QueueIcon,
  ErrorOutline,
  CheckCircle,
  Close,
  Minimize,
  CropSquare,
  PlayArrow,
  Pause
} from '@mui/icons-material'
import FileDropZone from './FileDropZone'
import QueuePanel from './QueuePanel'
import StatusBar from './StatusBar'
import SettingsPanel from './SettingsPanel'
// import ProgressSection from './ProgressSection' // Removed per user request
import FirstRunWelcome from './FirstRunWelcome'
import { useAppStore } from '../store/appStore'

const MainWindow: React.FC = () => {
  const theme = useTheme()
  
  // Local state for dialogs
  const [firstRunOpen, setFirstRunOpen] = useState(false)
  
  // Get state and actions from store
  const {
    processingStatus,
    queueStats,
    error,
    isLoading,
    wsConnectionState,
    processingOptions,
    isSettingsLoaded,
    fetchAppStatus,
    fetchQueue,
    fetchProcessingStatus,
    initializeWebSocket,
    startProcessing,
    stopProcessing,
    pauseProcessing,
    clearQueue,
    addDirectory,
    setError
  } = useAppStore()

  // Initialize app on mount
  useEffect(() => {
    const initializeApp = async () => {
      try {
        await Promise.all([
          fetchAppStatus(),
          fetchQueue(),
          fetchProcessingStatus(),
          initializeWebSocket()
        ])
      } catch (error) {
        console.error('Failed to initialize app:', error)
      }
    }

    initializeApp()
  }, [fetchAppStatus, fetchQueue, fetchProcessingStatus, initializeWebSocket])

  // Check for first-run experience
  useEffect(() => {
    if (isSettingsLoaded) {
      const hasSeenWelcome = localStorage.getItem('video-transcriber-welcome-seen')
      const hasValidSettings = processingOptions.output_directory && processingOptions.output_directory.trim().length > 0
      
      // Show welcome if user hasn't seen it and doesn't have valid settings
      if (!hasSeenWelcome && !hasValidSettings) {
        setFirstRunOpen(true)
      }
    }
  }, [isSettingsLoaded, processingOptions])

  // Derived state
  const isProcessing = processingStatus?.is_processing || false
  const isPaused = processingStatus?.is_paused || false

  const handleStart = async () => {
    try {
      await startProcessing()
    } catch (error) {
      console.error('Failed to start processing:', error)
    }
  }

  const handlePause = async () => {
    try {
      await pauseProcessing()
    } catch (error) {
      console.error('Failed to pause processing:', error)
    }
  }

  const handleStop = async () => {
    try {
      await stopProcessing()
    } catch (error) {
      console.error('Failed to stop processing:', error)
    }
  }

  const handleClear = async () => {
    try {
      await clearQueue()
    } catch (error) {
      console.error('Failed to clear queue:', error)
    }
  }

  const handleOpenFolder = async () => {
    if (window.electronAPI?.dialog) {
      const result = await window.electronAPI.dialog.showOpenDialog({
        properties: ['openDirectory']
      })
      
      if (!result.canceled && result.filePaths.length > 0) {
        try {
          await addDirectory(result.filePaths[0])
        } catch (error) {
          console.error('Failed to add directory:', error)
        }
      }
    }
  }

  const handleCloseWindow = async () => {
    try {
      if (window.electronAPI?.window?.close) {
        console.log('Closing window via Electron API...')
        await window.electronAPI.window.close()
      } else {
        console.warn('Window close API not available, attempting fallback')
        // Fallback for non-Electron environments
        if (typeof window !== 'undefined' && window.close) {
          window.close()
        }
      }
    } catch (error) {
      console.error('Failed to close window:', error)
      // Show user feedback that close failed
      setError('Failed to close window. Please try Alt+F4 or close from taskbar.')
    }
  }

  const handleMinimizeWindow = async () => {
    try {
      if (window.electronAPI?.window?.minimize) {
        console.log('Minimizing window via Electron API...')
        await window.electronAPI.window.minimize()
      } else {
        console.warn('Window minimize API not available')
      }
    } catch (error) {
      console.error('Failed to minimize window:', error)
    }
  }

  const handleMaximizeWindow = async () => {
    try {
      if (window.electronAPI?.window?.maximize) {
        console.log('Maximizing/restoring window via Electron API...')
        await window.electronAPI.window.maximize()
      } else {
        console.warn('Window maximize API not available')
      }
    } catch (error) {
      console.error('Failed to maximize window:', error)
    }
  }


  const handleCloseFirstRun = () => {
    setFirstRunOpen(false)
    // Mark welcome as seen
    localStorage.setItem('video-transcriber-welcome-seen', 'true')
  }

  const handleFirstRunOpenSettings = () => {
    handleCloseFirstRun()
    // Settings are now always visible in the panel
  }


  // Clear error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError(null)
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [error, setError])


  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Clean Professional Title Bar */}
      <AppBar 
        position="static" 
        elevation={0}
        sx={{ 
          background: theme.palette.gradient.primary,
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          WebkitAppRegion: 'drag'
        }}
      >
        <Toolbar sx={{ 
          minHeight: '48px !important', 
          px: 2, 
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          {/* Left Zone: App Identity & Status */}
          <Box 
            className="electron-drag" 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2,
              minWidth: 0,
              flex: '1 1 auto'
            }}
          >
            <Typography variant="h6" sx={{ 
              fontWeight: 600, 
              color: 'white', 
              whiteSpace: 'nowrap',
              letterSpacing: '0.5px'
            }}>
              Video Transcriber
            </Typography>
            
            {/* Connection Status Indicator */}
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 0.5,
              backgroundColor: alpha(theme.palette.common.white, 0.1),
              borderRadius: 12,
              px: 1.5,
              py: 0.5,
              ml: 1
            }}>
              {wsConnectionState === 'connected' ? (
                <CheckCircle sx={{ fontSize: 14, color: '#4caf50' }} />
              ) : (
                <ErrorOutline sx={{ fontSize: 14, color: '#ff9800' }} />
              )}
              <Typography variant="caption" sx={{ 
                color: 'white', 
                fontWeight: 500,
                fontSize: '0.75rem'
              }}>
                {wsConnectionState === 'connected' ? 'Connected' : 'Connecting...'}
              </Typography>
            </Box>
          </Box>
          
          {/* Center Zone: Empty */}
          <Box sx={{ flex: 1 }} />
          
          {/* Right Zone: Window Controls Only */}
          <Box 
            className="electron-no-drag" 
            sx={{ 
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              flex: '1 1 auto',
              justifyContent: 'flex-end'
            }}
          >
            <IconButton
              onClick={handleMinimizeWindow}
              sx={{ 
                color: 'white',
                width: 46,
                height: 32,
                borderRadius: 0,
                '&:hover': {
                  backgroundColor: alpha(theme.palette.common.white, 0.1)
                },
                transition: 'background-color 0.15s ease'
              }}
              title="Minimize"
            >
              <Minimize sx={{ fontSize: 14 }} />
            </IconButton>
            
            <IconButton
              onClick={handleMaximizeWindow}
              sx={{ 
                color: 'white',
                width: 46,
                height: 32,
                borderRadius: 0,
                '&:hover': {
                  backgroundColor: alpha(theme.palette.common.white, 0.1)
                },
                transition: 'background-color 0.15s ease'
              }}
              title="Maximize/Restore"
            >
              <CropSquare sx={{ fontSize: 12 }} />
            </IconButton>
            
            <IconButton
              onClick={handleCloseWindow}
              sx={{ 
                color: 'white',
                width: 46,
                height: 32,
                borderRadius: 0,
                '&:hover': {
                  backgroundColor: '#e81123',
                  color: 'white'
                },
                transition: 'background-color 0.15s ease'
              }}
              title="Close Application"
            >
              <Close sx={{ fontSize: 14 }} />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth={false} sx={{ flexGrow: 1, py: 2, px: 2, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
        {/* Top Section - File Drop Zone and Queue */}
        <Grid container spacing={2} sx={{ minHeight: '280px', mb: 2, flexShrink: 0 }}>
          {/* Left Panel - File Drop Zone */}
          <Grid item xs={12} sm={12} md={5} lg={5} sx={{ width: '100%' }}>
            <Paper 
              elevation={1}
              sx={{ 
                height: '100%', 
                minHeight: '280px',
                width: '100%',
                display: 'flex', 
                flexDirection: 'column',
                background: theme.palette.background.elevation1,
                p: 2,
                overflow: 'hidden'
              }}
            >
              <FileDropZone />
            </Paper>
          </Grid>

          {/* Right Panel - Queue */}
          <Grid item xs={12} sm={12} md={7} lg={7} sx={{ width: '100%' }}>
            <Paper 
              elevation={1}
              sx={{ 
                height: '100%',
                minHeight: '280px',
                width: '100%',
                display: 'flex',
                flexDirection: 'column',
                background: theme.palette.background.elevation1,
                overflow: 'auto'
              }}
            >
              <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}`, flexShrink: 0 }}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <QueueIcon color="primary" />
                  Processing Queue
                </Typography>
              </Box>
              
              <Box sx={{ flexGrow: 1, overflow: 'auto', minHeight: 0, width: '100%' }}>
                <QueuePanel />
              </Box>
            </Paper>
          </Grid>
        </Grid>

        {/* Bottom Section - Settings Panel (Full Width) */}
        <Paper 
          elevation={1}
          sx={{ 
            flexGrow: 1,
            minHeight: 0,
            display: 'flex',
            flexDirection: 'column',
            background: theme.palette.background.elevation1,
            overflow: 'auto'
          }}
        >
          <SettingsPanel />
        </Paper>
      </Container>

      {/* Status Bar */}
      <StatusBar />
      

      {/* First Run Welcome Dialog */}
      <FirstRunWelcome
        open={firstRunOpen}
        onClose={handleCloseFirstRun}
        onOpenSettings={handleFirstRunOpenSettings}
      />
    </Box>
  )
}

export default MainWindow