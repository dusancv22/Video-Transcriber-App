import React, { useCallback, useState, useEffect } from 'react'
import { useAppStore } from '../store/appStore'
import { APIUtils } from '../services/api'
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

    // Note: Native drop handling is now managed by the main process
    // This React drop handler is kept for UI feedback only
    // The actual file processing happens via the native postMessage event
    console.log('📥 React drag-drop event (UI only - native handler will process files)')
    
    if (isLoading) {
      showNotification('Please wait for the current operation to complete', 'warning')
      return
    }
  }, [isLoading, showNotification])

  const handleFileSelect = useCallback(async () => {
    console.log('Browse Files clicked - checking Electron API availability...')
    
    if (isLoading) {
      showNotification('Please wait for the current operation to complete', 'warning')
      return
    }

    if (!window.electronAPI || !window.electronAPI.file) {
      console.warn('Electron API not available! Falling back to web file input...')
      // Create a hidden file input as fallback for web mode
      const fileInput = document.createElement('input')
      fileInput.type = 'file'
      fileInput.multiple = true
      fileInput.accept = '.mp4,.avi,.mkv,.mov'
      fileInput.style.display = 'none'
      
      fileInput.onchange = async (e) => {
        const files = Array.from((e.target as HTMLInputElement).files || [])
        if (files.length > 0) {
          try {
            setIsLoading(true)
            
            // Filter for video files
            const validFiles = files.filter(file => 
              file.type.startsWith('video/') || 
              ['.mp4', '.avi', '.mkv', '.mov'].some(ext => 
                file.name.toLowerCase().endsWith(ext)
              )
            )
            
            if (validFiles.length === 0) {
              showNotification('No valid video files selected. Please select MP4, AVI, MKV, or MOV files.', 'warning')
              return
            }
            
            // Use file names as paths since we can't get full paths in web mode
            // Note: This will cause backend validation errors - web mode limitation
            const rawPaths = validFiles.map(file => file.name)
            
            // Validate and format paths
            const pathValidation = APIUtils.validateFilePaths(rawPaths)
            const validPaths = APIUtils.formatFilePaths(pathValidation.valid)
            
            if (pathValidation.warnings.length > 0) {
              console.warn('⚠️ FileDropZone: Web mode path warnings:')
              pathValidation.warnings.forEach(warning => console.warn(`  - ${warning}`))
            }
            
            if (validPaths.length === 0) {
              showNotification('No valid file paths could be processed in web mode', 'error')
              return
            }
            
            setSelectedFiles(prev => [...prev, ...validFiles])
            
            console.log(`🚀 FileDropZone: Adding ${validFiles.length} web-selected files to queue...`)
            console.log('📝 FileDropZone: Calling addFiles from store (web fallback)...')
            await addFiles(validPaths)
            console.log('✅ FileDropZone: addFiles call completed successfully (web fallback)')
            
            showNotification(`Successfully added ${validFiles.length} file(s) to the queue`, 'success')
          } catch (error) {
            console.error('Error processing web file selection:', error)
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
            showNotification(`Failed to add files: ${errorMessage}`, 'error')
          } finally {
            setIsLoading(false)
          }
        }
        document.body.removeChild(fileInput)
      }
      
      document.body.appendChild(fileInput)
      fileInput.click()
      return
    }

    try {
      setIsLoading(true)
      console.log('Using IPC-based file selection...')
      
      const rawFilePaths = await window.electronAPI.file.selectVideoFiles()
      console.log('Selected file paths via IPC:', rawFilePaths)

      if (!rawFilePaths || rawFilePaths.length === 0) {
        console.log('No files were selected')
        showNotification('No files were selected', 'info')
        return
      }

      // Validate and format the selected file paths
      const pathValidation = APIUtils.validateFilePaths(rawFilePaths)
      const validPaths = APIUtils.formatFilePaths(pathValidation.valid)
      
      if (pathValidation.warnings.length > 0) {
        console.warn('⚠️ FileDropZone: Browse selection path warnings:')
        pathValidation.warnings.forEach(warning => console.warn(`  - ${warning}`))
      }
      
      if (pathValidation.invalid.length > 0) {
        showNotification(`Some selected files had invalid paths: ${pathValidation.invalid.length} files`, 'warning')
      }
      
      if (validPaths.length === 0) {
        showNotification('No valid file paths found in selection', 'error')
        return
      }

      console.log(`🚀 FileDropZone: Adding ${validPaths.length} selected files to queue...`)
      console.log('📝 FileDropZone: Calling addFiles from store (browse)...')
      await addFiles(validPaths)
      console.log('✅ FileDropZone: addFiles call completed successfully (browse)')
      
      showNotification(`Successfully added ${validPaths.length} file(s) to the queue`, 'success')
      console.log('📊 FileDropZone: Selected files successfully processed')

    } catch (error) {
      console.error('Error during file selection:', error)
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      showNotification(`Failed to open file browser: ${errorMessage}`, 'error')
    } finally {
      setIsLoading(false)
    }
  }, [addFiles, isLoading, showNotification])

  // Listen for native file drop events from the main process
  useEffect(() => {
    const handleNativeFileDrop = async (event: MessageEvent) => {
      if (event.data.type === 'native-file-drop') {
        const filePaths = event.data.filePaths as string[]
        console.log('🎯 Received native file drop event with paths:', filePaths)
        
        if (isLoading) {
          showNotification('Please wait for the current operation to complete', 'warning')
          return
        }

        try {
          setIsLoading(true)
          
          // Filter for video files by extension
          const videoExtensions = ['.mp4', '.avi', '.mkv', '.mov']
          const validFiles = filePaths.filter(path => {
            const ext = path.toLowerCase().split('.').pop()
            return ext && videoExtensions.includes(`.${ext}`)
          })

          console.log(`🔍 Filtered ${validFiles.length} valid video files from ${filePaths.length} dropped files`)

          if (validFiles.length === 0) {
            showNotification('No valid video files found. Supported formats: MP4, AVI, MKV, MOV', 'warning')
            return
          }

          if (validFiles.length < filePaths.length) {
            const skippedCount = filePaths.length - validFiles.length
            showNotification(`${skippedCount} file(s) skipped - only video files are supported`, 'warning')
          }

          // Validate and format the native dropped file paths
          const pathValidation = APIUtils.validateFilePaths(validFiles)
          const validPaths = APIUtils.formatFilePaths(pathValidation.valid)
          
          if (pathValidation.warnings.length > 0) {
            console.warn('⚠️ FileDropZone: Native drop path warnings:')
            pathValidation.warnings.forEach(warning => console.warn(`  - ${warning}`))
          }
          
          if (pathValidation.invalid.length > 0) {
            showNotification(`Some dropped files had invalid paths: ${pathValidation.invalid.length} files`, 'warning')
          }
          
          if (validPaths.length === 0) {
            showNotification('No valid file paths found in dropped files', 'error')
            return
          }

          console.log(`🚀 FileDropZone: Adding ${validPaths.length} native dropped files to queue...`)
          console.log('📝 FileDropZone: Validated paths:', validPaths)
          console.log('📝 FileDropZone: Calling addFiles from store (native drop)...')
          await addFiles(validPaths)
          console.log('✅ FileDropZone: addFiles call completed successfully (native drop)')
          
          showNotification(`Successfully added ${validPaths.length} file(s) to the queue`, 'success')
          console.log('🎉 FileDropZone: Native file drop processing completed successfully')
        } catch (error) {
          console.error('❌ Error processing native file drop:', error)
          const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
          showNotification(`Failed to add files: ${errorMessage}`, 'error')
        } finally {
          setIsLoading(false)
        }
      }
    }

    console.log('🔧 Setting up native file drop event listener')
    window.addEventListener('message', handleNativeFileDrop)
    return () => {
      console.log('🧹 Cleaning up native file drop event listener')
      window.removeEventListener('message', handleNativeFileDrop)
    }
  }, [addFiles, isLoading, showNotification])

  const supportedFormats = ['MP4', 'AVI', 'MKV', 'MOV']

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 1 }}>
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