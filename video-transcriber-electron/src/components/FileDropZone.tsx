import React, { useCallback, useState } from 'react'
import { useAppStore } from '../store/appStore'
import {
  Box,
  Typography,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  alpha,
  useTheme,
  Snackbar,
  Alert,
  CircularProgress,
  Backdrop
} from '@mui/material'
import {
  CloudUpload,
  VideoFile,
  FolderOpen,
  CheckCircle,
  Error as ErrorIcon
} from '@mui/icons-material'

interface FileDropZoneProps {
  onFilesAdded?: (files: File[]) => void
}

interface NotificationState {
  open: boolean
  message: string
  severity: 'success' | 'error' | 'warning' | 'info'
}

const FileDropZone: React.FC<FileDropZoneProps> = ({ onFilesAdded }) => {
  const { addFiles } = useAppStore()
  const theme = useTheme()
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [notification, setNotification] = useState<NotificationState>({
    open: false,
    message: '',
    severity: 'info'
  })

  // Utility function to show notifications
  const showNotification = useCallback((message: string, severity: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    setNotification({
      open: true,
      message,
      severity
    })
  }, [])

  // Utility function to close notifications
  const closeNotification = useCallback(() => {
    setNotification(prev => ({ ...prev, open: false }))
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    if (isLoading) {
      showNotification('Please wait for the current operation to complete', 'warning')
      return
    }

    try {
      setIsLoading(true)
      console.log('Processing dropped files...')

      const droppedFiles = Array.from(e.dataTransfer.files)
      const validFiles = droppedFiles.filter(file => 
        file.type.startsWith('video/') || 
        ['.mp4', '.avi', '.mkv', '.mov'].some(ext => 
          file.name.toLowerCase().endsWith(ext)
        )
      )

      if (validFiles.length === 0) {
        showNotification('No valid video files found. Please drop MP4, AVI, MKV, or MOV files.', 'warning')
        return
      }

      if (validFiles.length < droppedFiles.length) {
        const skippedCount = droppedFiles.length - validFiles.length
        showNotification(`${skippedCount} file(s) skipped - only video files are supported`, 'warning')
      }

      // Convert File objects to file paths for API
      const filePaths = validFiles.map(file => (file as any).path || file.name)
      
      setSelectedFiles(prev => [...prev, ...validFiles])
      onFilesAdded?.(validFiles)
      
      console.log(`Adding ${validFiles.length} files to queue...`)
      await addFiles(filePaths)
      
      showNotification(`Successfully added ${validFiles.length} file(s) to the queue`, 'success')
      console.log('Files successfully added to queue')

    } catch (error) {
      console.error('Failed to add dropped files to queue:', error)
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      showNotification(`Failed to add files: ${errorMessage}`, 'error')
    } finally {
      setIsLoading(false)
    }
  }, [onFilesAdded, addFiles, isLoading, showNotification])

  const handleFileSelect = useCallback(async () => {
    console.log('Browse Files clicked - checking Electron API availability...')
    
    if (isLoading) {
      showNotification('Please wait for the current operation to complete', 'warning')
      return
    }

    if (!window.electronAPI) {
      console.error('Electron API not available!')
      showNotification('Desktop features not available. Please restart the application.', 'error')
      return
    }

    if (!window.electronAPI.dialog) {
      console.error('Dialog API not available!')
      showNotification('File dialog not available. Please check your installation.', 'error')
      return
    }

    try {
      setIsLoading(true)
      console.log('Opening file dialog...')
      
      const result = await window.electronAPI.dialog.showOpenDialog({
        properties: ['openFile', 'multiSelections'],
        filters: [
          { name: 'Video Files', extensions: ['mp4', 'avi', 'mkv', 'mov'] },
          { name: 'All Files', extensions: ['*'] }
        ],
        title: 'Select Video Files to Transcribe'
      })

      console.log('File dialog result:', { canceled: result.canceled, fileCount: result.filePaths?.length || 0 })

      if (result.canceled) {
        console.log('File selection was canceled by user')
        showNotification('File selection canceled', 'info')
        return
      }

      if (!result.filePaths || result.filePaths.length === 0) {
        console.log('No files were selected')
        showNotification('No files were selected', 'warning')
        return
      }

      // Validate file extensions
      const validFiles = result.filePaths.filter(filePath => {
        const isValid = ['.mp4', '.avi', '.mkv', '.mov'].some(ext => 
          filePath.toLowerCase().endsWith(ext)
        )
        if (!isValid) {
          console.warn(`Invalid file type: ${filePath}`)
        }
        return isValid
      })

      if (validFiles.length === 0) {
        showNotification('No valid video files selected. Please select MP4, AVI, MKV, or MOV files.', 'warning')
        return
      }

      if (validFiles.length < result.filePaths.length) {
        const skippedCount = result.filePaths.length - validFiles.length
        showNotification(`${skippedCount} file(s) skipped - only video files are supported`, 'warning')
      }

      console.log(`Adding ${validFiles.length} selected files to queue...`)
      await addFiles(validFiles)
      
      showNotification(`Successfully added ${validFiles.length} file(s) to the queue`, 'success')
      console.log('Selected files successfully added to queue')

    } catch (error) {
      console.error('Error during file selection:', error)
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      showNotification(`Failed to open file browser: ${errorMessage}`, 'error')
    } finally {
      setIsLoading(false)
    }
  }, [addFiles, isLoading, showNotification])

  const supportedFormats = ['MP4', 'AVI', 'MKV', 'MOV']

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Drop Zone */}
      <Box
        className={`drop-zone ${isDragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        sx={{
          border: `2px dashed ${isDragOver && !isLoading ? theme.palette.primary.main : theme.palette.divider}`,
          borderRadius: 2,
          p: 4,
          textAlign: 'center',
          backgroundColor: isDragOver && !isLoading
            ? alpha(theme.palette.primary.main, 0.05)
            : alpha(theme.palette.background.default, 0.5),
          cursor: isLoading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease-in-out',
          minHeight: 200,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 2,
          opacity: isLoading ? 0.7 : 1,
          position: 'relative',
          '&:hover': {
            borderColor: isLoading ? theme.palette.divider : theme.palette.primary.main,
            backgroundColor: isLoading 
              ? alpha(theme.palette.background.default, 0.5)
              : alpha(theme.palette.primary.main, 0.03)
          }
        }}
        onClick={handleFileSelect}
      >
        <CloudUpload 
          sx={{ 
            fontSize: 48, 
            color: isDragOver && !isLoading 
              ? theme.palette.primary.main 
              : isLoading 
                ? theme.palette.action.disabled
                : theme.palette.text.secondary,
            mb: 1
          }} 
        />
        
        <Typography variant="h6" color="textPrimary" gutterBottom>
          {isLoading ? 'Processing files...' : 'Drop video files here'}
        </Typography>
        
        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
          {isLoading ? 'Please wait while files are being processed' : 'or click to browse files'}
        </Typography>
        
        <Button
          variant="outlined"
          startIcon={isLoading ? <CircularProgress size={20} /> : <FolderOpen />}
          onClick={(e) => {
            e.stopPropagation()
            handleFileSelect()
          }}
          disabled={isLoading}
          sx={{
            '&:hover': {
              transform: isLoading ? 'none' : 'translateY(-1px)',
              boxShadow: isLoading ? 'none' : theme.shadows[4]
            },
            '&:disabled': {
              backgroundColor: alpha(theme.palette.action.disabled, 0.05),
              borderColor: theme.palette.action.disabled,
              color: theme.palette.action.disabled
            }
          }}
        >
          {isLoading ? 'Loading...' : 'Browse Files'}
        </Button>
      </Box>

      {/* Supported Formats */}
      <Box sx={{ mt: 2 }}>
        <Typography variant="caption" color="textSecondary" gutterBottom>
          Supported formats:
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
          {supportedFormats.map((format) => (
            <Box
              key={format}
              sx={{
                px: 1.5,
                py: 0.5,
                backgroundColor: alpha(theme.palette.primary.main, 0.1),
                color: theme.palette.primary.main,
                borderRadius: 1,
                fontSize: '0.75rem',
                fontWeight: 500
              }}
            >
              {format}
            </Box>
          ))}
        </Box>
      </Box>

      {/* Selected Files List */}
      {selectedFiles.length > 0 && (
        <Box sx={{ mt: 2, flexGrow: 1, overflow: 'auto' }}>
          <Typography variant="subtitle2" gutterBottom>
            Selected Files ({selectedFiles.length})
          </Typography>
          <List dense>
            {selectedFiles.map((file, index) => (
              <ListItem key={index} sx={{ px: 0 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <VideoFile color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary={file.name}
                  secondary={`${(file.size / (1024 * 1024)).toFixed(1)} MB`}
                  primaryTypographyProps={{
                    variant: 'body2',
                    sx: { 
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }
                  }}
                  secondaryTypographyProps={{
                    variant: 'caption'
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {/* Loading Backdrop */}
      <Backdrop
        sx={{
          color: theme.palette.primary.main,
          zIndex: theme.zIndex.drawer + 1,
          position: 'absolute',
          borderRadius: 2,
          backgroundColor: alpha(theme.palette.background.default, 0.8)
        }}
        open={isLoading}
      >
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 2
          }}
        >
          <CircularProgress color="primary" size={40} />
          <Typography variant="body2" color="primary">
            Processing files...
          </Typography>
        </Box>
      </Backdrop>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={closeNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={closeNotification}
          severity={notification.severity}
          variant="filled"
          sx={{
            width: '100%',
            alignItems: 'center'
          }}
          iconMapping={{
            success: <CheckCircle fontSize="inherit" />,
            error: <ErrorIcon fontSize="inherit" />
          }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default FileDropZone