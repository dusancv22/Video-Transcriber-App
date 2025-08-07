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
    // Processing is now handled directly by SettingsPanel
    // This button is no longer needed as settings are always visible
    console.log('Start button clicked - processing handled by settings panel')
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


  const handleCloseFirstRun = () => {
    setFirstRunOpen(false)
    // Mark welcome as seen
    localStorage.setItem('video-transcriber-welcome-seen', 'true')
  }

  const handleFirstRunOpenSettings = () => {
    handleCloseFirstRun()
    // Settings are now always visible in the panel
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
            
            
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth={false} sx={{ flexGrow: 1, py: 2, px: 2, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
        {/* Top Section - File Drop Zone and Queue */}
        <Grid container spacing={2} sx={{ minHeight: '250px', maxHeight: '35%', mb: 2 }}>
          {/* Left Panel - File Drop Zone */}
          <Grid item xs={12} md={5}>
            <Paper 
              elevation={1}
              sx={{ 
                height: '100%', 
                minHeight: '250px',
                display: 'flex', 
                flexDirection: 'column',
                background: theme.palette.background.elevation1,
                p: 2,
                overflow: 'auto'
              }}
            >
              <FileDropZone />
            </Paper>
          </Grid>

          {/* Right Panel - Queue */}
          <Grid item xs={12} md={7}>
            <Paper 
              elevation={1}
              sx={{ 
                height: '100%',
                minHeight: '250px',
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
              
              <Box sx={{ flexGrow: 1, overflow: 'auto', minHeight: 0 }}>
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
            minHeight: '400px',
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