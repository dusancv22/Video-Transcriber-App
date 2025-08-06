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
  PlayArrow,
  Pause,
  Stop,
  Settings,
  FolderOpen,
  Clear,
  Queue as QueueIcon,
  ErrorOutline,
  CheckCircle,
  Minimize,
  CropSquare,
  Close
} from '@mui/icons-material'
import FileDropZone from './FileDropZone'
import QueuePanel from './QueuePanel'
import StatusBar from './StatusBar'
import SettingsDialog from './SettingsDialog'
import SettingsStatusPanel from './SettingsStatusPanel'
import FirstRunWelcome from './FirstRunWelcome'
import { useAppStore } from '../store/appStore'

const MainWindow: React.FC = () => {
  const theme = useTheme()
  
  // Local state for dialogs
  const [settingsOpen, setSettingsOpen] = useState(false)
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
    pauseProcessing,
    stopProcessing,
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
    // Open settings dialog first to allow user to configure options
    setSettingsOpen(true)
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

  const handleOpenSettings = () => {
    setSettingsOpen(true)
  }

  const handleCloseSettings = () => {
    setSettingsOpen(false)
  }

  const handleCloseFirstRun = () => {
    setFirstRunOpen(false)
    // Mark welcome as seen
    localStorage.setItem('video-transcriber-welcome-seen', 'true')
  }

  const handleFirstRunOpenSettings = () => {
    handleCloseFirstRun()
    setSettingsOpen(true)
  }

  // Window control handlers
  const handleWindowClose = () => {
    if (window.electronAPI?.window?.close) {
      window.electronAPI.window.close()
    }
  }

  const handleWindowMinimize = () => {
    if (window.electronAPI?.window?.minimize) {
      window.electronAPI.window.minimize()
    }
  }

  const handleWindowMaximize = () => {
    if (window.electronAPI?.window?.maximize) {
      window.electronAPI.window.maximize()
    }
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

  // Keyboard shortcut for settings (Ctrl+, or Cmd+,)
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === ',') {
        event.preventDefault()
        handleOpenSettings()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Title Bar */}
      <AppBar 
        position="static" 
        elevation={0}
        sx={{ 
          background: theme.palette.gradient.primary,
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`
        }}
      >
        <Toolbar sx={{ minHeight: '48px !important' }}>
          <Box className="electron-drag" sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: 'white' }}>
              Video Transcriber
            </Typography>
            
            {/* Connection Status Indicator */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {wsConnectionState === 'connected' ? (
                <CheckCircle sx={{ fontSize: 16, color: '#4caf50' }} />
              ) : (
                <ErrorOutline sx={{ fontSize: 16, color: '#ff9800' }} />
              )}
              <Typography variant="caption" sx={{ color: 'white', opacity: 0.8 }}>
                {wsConnectionState === 'connected' ? 'Connected' : 'Connecting...'}
              </Typography>
            </Box>
          </Box>
          
          {/* Control Buttons */}
          <Box className="electron-no-drag" sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              startIcon={isProcessing && !isPaused ? <Pause /> : <PlayArrow />}
              onClick={isProcessing && !isPaused ? handlePause : handleStart}
              sx={{
                backgroundColor: alpha(theme.palette.common.white, 0.15),
                color: 'white',
                '&:hover': {
                  backgroundColor: alpha(theme.palette.common.white, 0.25)
                }
              }}
              size="small"
            >
              {isProcessing && !isPaused ? 'Pause' : isPaused ? 'Resume' : 'Start'}
            </Button>
            
            {isProcessing && (
              <Button
                variant="outlined"
                startIcon={<Stop />}
                onClick={handleStop}
                sx={{
                  borderColor: alpha(theme.palette.common.white, 0.3),
                  color: 'white',
                  '&:hover': {
                    borderColor: alpha(theme.palette.common.white, 0.5),
                    backgroundColor: alpha(theme.palette.common.white, 0.1)
                  }
                }}
                size="small"
              >
                Stop
              </Button>
            )}
            
            <IconButton
              onClick={handleOpenFolder}
              sx={{ 
                color: 'white',
                '&:hover': {
                  backgroundColor: alpha(theme.palette.common.white, 0.1)
                }
              }}
              size="small"
            >
              <FolderOpen />
            </IconButton>
            
            <IconButton
              onClick={handleClear}
              sx={{ 
                color: 'white',
                '&:hover': {
                  backgroundColor: alpha(theme.palette.common.white, 0.1)
                }
              }}
              size="small"
            >
              <Clear />
            </IconButton>
            
            <IconButton
              onClick={handleOpenSettings}
              sx={{ 
                color: 'white',
                '&:hover': {
                  backgroundColor: alpha(theme.palette.common.white, 0.1)
                }
              }}
              size="small"
              aria-label="Open settings"
              title="Settings (Ctrl+,)"
            >
              <Settings />
            </IconButton>
            
            {/* Window Controls */}
            <Box sx={{ ml: 2, display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <IconButton
                onClick={handleWindowMinimize}
                sx={{ 
                  color: 'white',
                  width: 32,
                  height: 32,
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.common.white, 0.1)
                  }
                }}
                size="small"
                aria-label="Minimize window"
                title="Minimize"
              >
                <Minimize sx={{ fontSize: 16 }} />
              </IconButton>
              
              <IconButton
                onClick={handleWindowMaximize}
                sx={{ 
                  color: 'white',
                  width: 32,
                  height: 32,
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.common.white, 0.1)
                  }
                }}
                size="small"
                aria-label="Maximize window"
                title="Maximize/Restore"
              >
                <CropSquare sx={{ fontSize: 14 }} />
              </IconButton>
              
              <IconButton
                onClick={handleWindowClose}
                sx={{ 
                  color: 'white',
                  width: 32,
                  height: 32,
                  '&:hover': {
                    backgroundColor: '#e53e3e'
                  }
                }}
                size="small"
                aria-label="Close window"
                title="Close"
              >
                <Close sx={{ fontSize: 16 }} />
              </IconButton>
            </Box>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth={false} sx={{ flexGrow: 1, py: 2, px: 2 }}>
        <Grid container spacing={2} sx={{ height: '100%' }}>
          {/* Left Panel - File Drop Zone */}
          <Grid item xs={12} md={5}>
            <Paper 
              elevation={1}
              sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                background: theme.palette.background.elevation1
              }}
            >
              <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <FolderOpen color="primary" />
                  Add Files
                </Typography>
              </Box>
              
              <Box sx={{ flexGrow: 1, p: 2 }}>
                <FileDropZone />
              </Box>
            </Paper>
          </Grid>

          {/* Right Panel - Queue, Settings, and Progress */}
          <Grid item xs={12} md={7}>
            <Grid container spacing={2} sx={{ height: '100%' }}>
              {/* Queue Panel */}
              <Grid item xs={12} sx={{ height: '60%' }}>
                <Paper 
                  elevation={1}
                  sx={{ 
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    background: theme.palette.background.elevation1
                  }}
                >
                  <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <QueueIcon color="primary" />
                      Processing Queue
                    </Typography>
                  </Box>
                  
                  <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
                    <QueuePanel />
                  </Box>
                </Paper>
              </Grid>

              {/* Settings Status Panel */}
              <Grid item xs={12} sx={{ height: '40%' }}>
                <SettingsStatusPanel onOpenSettings={handleOpenSettings} />
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Container>

      {/* Status Bar */}
      <StatusBar />
      
      {/* Settings Dialog */}
      <SettingsDialog 
        open={settingsOpen} 
        onClose={handleCloseSettings}
        onSaveAndStart={() => {
          // Optional callback when processing starts from settings
          console.log('Processing started from settings dialog')
        }}
      />

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