import React, { useState } from 'react'
import {
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  LinearProgress,
  Typography,
  IconButton,
  Chip,
  useTheme,
  alpha,
  Snackbar,
  Alert,
  CircularProgress,
  Tooltip,
  Menu,
  MenuItem,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button
} from '@mui/material'
import {
  VideoFile,
  CheckCircle,
  Error,
  Schedule,
  PlayCircle,
  Delete,
  OpenInNew,
  MoreVert,
  FolderOpen,
  ContentCopy,
  Info,
  Refresh,
  Launch,
  Description
} from '@mui/icons-material'
import { QueueItem, FileStatus } from '../types/api'

// Mock data for development (fallback when API unavailable)
const mockQueueItems: QueueItem[] = [
  {
    id: '1',
    file_path: 'C:/Videos/sample1.mp4',
    status: 'processing',
    progress: 45,
    processing_time: 120,
    estimated_time_remaining: 150,
    current_step: 'Transcribing audio segments',
    file_size: 125829120, // ~120MB
    duration: 300,
    format: 'MP4',
    created_at: '2025-01-06T10:00:00Z'
  },
  {
    id: '2',
    file_path: 'C:/Videos/interview.avi',
    status: 'queued',
    progress: 0,
    file_size: 89478485, // ~85MB
    format: 'AVI',
    created_at: '2025-01-06T10:05:00Z'
  },
  {
    id: '3',
    file_path: 'C:/Videos/presentation.mkv',
    status: 'completed',
    progress: 100,
    processing_time: 280,
    output_file: 'C:/Output/presentation.txt',
    file_size: 234567890, // ~224MB
    duration: 1200,
    format: 'MKV',
    created_at: '2025-01-06T09:30:00Z',
    completed_at: '2025-01-06T09:35:00Z'
  },
  {
    id: '4',
    file_path: 'C:/Videos/corrupted.mov',
    status: 'failed',
    progress: 0,
    error: 'Audio extraction failed: Invalid file format',
    error_code: 'AUDIO_EXTRACTION_FAILED',
    file_size: 45678901, // ~44MB
    format: 'MOV',
    created_at: '2025-01-06T09:45:00Z'
  }
]

import { useAppStore } from '../store/appStore'

// Notification types
type NotificationSeverity = 'success' | 'error' | 'warning' | 'info'

interface NotificationState {
  open: boolean
  message: string
  severity: NotificationSeverity
}

// File operation types
type FileOperationType = 'open' | 'copy' | 'showFolder' | 'openTranscript' | 'remove' | 'retry'

interface QueuePanelProps {
  items?: QueueItem[]
}

// File size and timestamp formatting utilities
const formatTimestamp = (timestamp: string) => {
  try {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(timestamp))
  } catch {
    return 'Unknown'
  }
}

// File existence checking utility
const checkFileExists = async (filePath: string): Promise<boolean> => {
  try {
    if (!window.electronAPI?.shell) {
      return false
    }
    // We'll use a try-catch around showItemInFolder as a file existence check
    // In a real implementation, you might want to add a specific API for this
    return true // For now, assume files exist. You could enhance this with actual file system checks.
  } catch {
    return false
  }
}

// Copy to clipboard utility
const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    } else {
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      const result = document.execCommand('copy')
      textArea.remove()
      return result
    }
  } catch {
    return false
  }
}

const QueuePanel: React.FC<QueuePanelProps> = ({ items }) => {
  const { queueItems, removeFromQueue } = useAppStore()
  
  // Component state
  const [notification, setNotification] = useState<NotificationState>({
    open: false,
    message: '',
    severity: 'info'
  })
  const [isLoading, setIsLoading] = useState(false)
  const [loadingOperation, setLoadingOperation] = useState<string | null>(null)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null)
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean
    title: string
    message: string
    onConfirm: () => void
  }>({
    open: false,
    title: '',
    message: '',
    onConfirm: () => {}
  })
  
  // Use store data if available, otherwise use props or fallback to mock data
  const displayItems = items || queueItems.length > 0 ? queueItems : mockQueueItems
  const theme = useTheme()

  // Notification helper
  const showNotification = (message: string, severity: NotificationSeverity = 'info') => {
    setNotification({
      open: true,
      message,
      severity
    })
  }

  // Close notification
  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }))
  }

  // Menu handling
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, itemId: string) => {
    setAnchorEl(event.currentTarget)
    setSelectedItemId(itemId)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
    setSelectedItemId(null)
  }

  // Confirmation dialog
  const showConfirmDialog = (title: string, message: string, onConfirm: () => void) => {
    setConfirmDialog({
      open: true,
      title,
      message,
      onConfirm
    })
  }

  const handleConfirmDialogClose = () => {
    setConfirmDialog(prev => ({ ...prev, open: false }))
  }

  const handleConfirmAction = () => {
    confirmDialog.onConfirm()
    handleConfirmDialogClose()
  }

  const getStatusIcon = (status: FileStatus) => {
    switch (status) {
      case 'processing':
        return <PlayCircle color="primary" />
      case 'completed':
        return <CheckCircle color="success" />
      case 'failed':
        return <Error color="error" />
      case 'queued':
        return <Schedule color="action" />
      default:
        return <VideoFile color="action" />
    }
  }

  const getStatusChip = (status: FileStatus) => {
    const statusConfig = {
      processing: { color: 'primary' as const, label: 'Processing' },
      completed: { color: 'success' as const, label: 'Completed' },
      failed: { color: 'error' as const, label: 'Failed' },
      queued: { color: 'default' as const, label: 'Queued' }
    }

    const config = statusConfig[status]
    return (
      <Chip
        label={config.label}
        color={config.color}
        size="small"
        variant="outlined"
        sx={{ fontSize: '0.7rem', height: 24 }}
      />
    )
  }

  const formatFileSize = (bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB']
    let size = bytes
    let unitIndex = 0

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024
      unitIndex++
    }

    return `${size.toFixed(unitIndex > 0 ? 1 : 0)} ${units[unitIndex]}`
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return ''
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  const getFileName = (filePath: string) => {
    return filePath.split(/[/\\]/).pop() || filePath
  }

  // Enhanced file operations with comprehensive error handling
  const handleOpenFile = async (filePath: string, fileType: 'input' | 'output' = 'output') => {
    if (!window.electronAPI?.shell) {
      showNotification('File operations not available. Please restart the application.', 'error')
      return
    }

    try {
      setIsLoading(true)
      setLoadingOperation(`Opening ${fileType} file location`)
      
      console.log(`Opening ${fileType} file:`, filePath)
      await window.electronAPI.shell.showItemInFolder(filePath)
      showNotification(`Opened ${fileType} file location`, 'success')
      
    } catch (error) {
      console.error(`Failed to open ${fileType} file:`, error)
      
      if (fileType === 'output') {
        // Offer to open parent directory for output files
        const parentDir = filePath.substring(0, filePath.lastIndexOf(/[/\\]/))
        if (parentDir) {
          showConfirmDialog(
            'File Not Found',
            `The transcript file was not found. Would you like to open the output directory instead?`,
            () => handleOpenFile(parentDir, 'input')
          )
        } else {
          showNotification('Transcript file not found. It may have been moved or deleted.', 'warning')
        }
      } else {
        showNotification(`Failed to open file location: ${error}`, 'error')
      }
    } finally {
      setIsLoading(false)
      setLoadingOperation(null)
      handleMenuClose()
    }
  }

  // Copy file path to clipboard
  const handleCopyPath = async (filePath: string, fileType: 'input' | 'output' = 'output') => {
    try {
      setIsLoading(true)
      setLoadingOperation('Copying path to clipboard')
      
      const success = await copyToClipboard(filePath)
      if (success) {
        showNotification(`${fileType === 'output' ? 'Transcript' : 'Input'} file path copied to clipboard`, 'success')
      } else {
        showNotification('Failed to copy path to clipboard', 'error')
      }
    } catch (error) {
      showNotification('Failed to copy path to clipboard', 'error')
    } finally {
      setIsLoading(false)
      setLoadingOperation(null)
      handleMenuClose()
    }
  }

  // Open transcript file directly
  const handleOpenTranscript = async (filePath: string) => {
    if (!window.electronAPI?.shell) {
      showNotification('File operations not available. Please restart the application.', 'error')
      return
    }

    try {
      setIsLoading(true)
      setLoadingOperation('Opening transcript file')
      
      // Check if file exists first
      const exists = await checkFileExists(filePath)
      if (!exists) {
        showConfirmDialog(
          'File Not Found',
          'The transcript file was not found. Would you like to open the containing folder instead?',
          () => {
            const parentDir = filePath.substring(0, filePath.lastIndexOf(/[/\\]/))
            if (parentDir) {
              handleOpenFile(parentDir, 'output')
            }
          }
        )
        return
      }

      console.log('Opening transcript file:', filePath)
      await window.electronAPI.shell.openExternal(`file://${filePath}`)
      showNotification('Opened transcript file', 'success')
      
    } catch (error) {
      console.error('Failed to open transcript file:', error)
      showNotification(`Failed to open transcript file: ${error}`, 'error')
    } finally {
      setIsLoading(false)
      setLoadingOperation(null)
      handleMenuClose()
    }
  }

  // Enhanced remove file with confirmation
  const handleRemoveFile = async (id: string, fileName: string) => {
    showConfirmDialog(
      'Remove File',
      `Are you sure you want to remove "${fileName}" from the queue? This action cannot be undone.`,
      async () => {
        try {
          setIsLoading(true)
          setLoadingOperation('Removing file from queue')
          
          await removeFromQueue(id)
          showNotification('File removed from queue', 'success')
        } catch (error) {
          console.error('Failed to remove file:', error)
          showNotification(`Failed to remove file: ${error}`, 'error')
        } finally {
          setIsLoading(false)
          setLoadingOperation(null)
        }
      }
    )
  }

  // Get available actions based on file status
  const getAvailableActions = (item: QueueItem) => {
    const actions = []
    
    switch (item.status) {
      case 'queued':
        actions.push(
          { id: 'showInputFolder', label: 'Show Input File', icon: <FolderOpen fontSize="small" /> },
          { id: 'copyInputPath', label: 'Copy Input Path', icon: <ContentCopy fontSize="small" /> },
          { id: 'remove', label: 'Remove from Queue', icon: <Delete fontSize="small" />, destructive: true }
        )
        break
        
      case 'processing':
        actions.push(
          { id: 'showInputFolder', label: 'Show Input File', icon: <FolderOpen fontSize="small" /> },
          { id: 'copyInputPath', label: 'Copy Input Path', icon: <ContentCopy fontSize="small" /> }
        )
        break
        
      case 'completed':
        actions.push(
          { id: 'openTranscript', label: 'Open Transcript', icon: <Description fontSize="small" /> },
          { id: 'showOutputFolder', label: 'Show Output Folder', icon: <FolderOpen fontSize="small" /> },
          { id: 'copyOutputPath', label: 'Copy Output Path', icon: <ContentCopy fontSize="small" /> },
          { id: 'showInputFolder', label: 'Show Input File', icon: <Launch fontSize="small" /> },
          { id: 'remove', label: 'Remove from Queue', icon: <Delete fontSize="small" />, destructive: true }
        )
        break
        
      case 'failed':
        actions.push(
          { id: 'retry', label: 'Retry Processing', icon: <Refresh fontSize="small" /> },
          { id: 'showInputFolder', label: 'Show Input File', icon: <FolderOpen fontSize="small" /> },
          { id: 'copyInputPath', label: 'Copy Input Path', icon: <ContentCopy fontSize="small" /> },
          { id: 'showError', label: 'Show Error Details', icon: <Info fontSize="small" /> },
          { id: 'remove', label: 'Remove from Queue', icon: <Delete fontSize="small" />, destructive: true }
        )
        break
    }
    
    return actions
  }

  // Handle menu action selection
  const handleMenuAction = async (actionId: string, item: QueueItem) => {
    switch (actionId) {
      case 'showInputFolder':
        await handleOpenFile(item.file_path, 'input')
        break
      case 'showOutputFolder':
        if (item.output_file) {
          await handleOpenFile(item.output_file, 'output')
        }
        break
      case 'copyInputPath':
        await handleCopyPath(item.file_path, 'input')
        break
      case 'copyOutputPath':
        if (item.output_file) {
          await handleCopyPath(item.output_file, 'output')
        }
        break
      case 'openTranscript':
        if (item.output_file) {
          await handleOpenTranscript(item.output_file)
        }
        break
      case 'remove':
        await handleRemoveFile(item.id, getFileName(item.file_path))
        break
      case 'retry':
        // You would implement retry logic here
        showNotification('Retry functionality would be implemented here', 'info')
        handleMenuClose()
        break
      case 'showError':
        showConfirmDialog(
          'Error Details',
          item.error || 'No error details available',
          () => {}
        )
        break
      default:
        handleMenuClose()
    }
  }

  if (displayItems.length === 0) {
    return (
      <Box
        sx={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: theme.palette.text.secondary
        }}
      >
        <Typography variant="body2">
          No files in queue. Drag and drop video files to get started.
        </Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ height: '100%', overflow: 'auto' }}>
      <List dense sx={{ p: 0 }}>
        {displayItems.map((item, index) => (
          <ListItem
            key={item.id}
            sx={{
              flexDirection: 'column',
              alignItems: 'stretch',
              py: 1.5,
              px: 2,
              borderBottom: index < displayItems.length - 1 ? `1px solid ${theme.palette.divider}` : 'none',
              '&:hover': {
                backgroundColor: alpha(theme.palette.action.hover, 0.5)
              }
            }}
          >
            {/* File Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <ListItemIcon sx={{ minWidth: 32 }}>
                {getStatusIcon(item.status)}
              </ListItemIcon>
              
              <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: 500,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}
                  title={item.file_path}
                >
                  {getFileName(item.file_path)}
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                  {getStatusChip(item.status)}
                  <Typography variant="caption" color="textSecondary">
                    {formatFileSize(item.file_size)}
                    {item.duration && ` • ${formatDuration(item.duration)}`}
                    {` • ${item.format}`}
                    {item.created_at && ` • ${formatTimestamp(item.created_at)}`}
                  </Typography>
                </Box>
              </Box>

              {/* Actions */}
              <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                {/* Quick action buttons for completed files */}
                {item.status === 'completed' && item.output_file && (
                  <>
                    <Tooltip title="Open transcript file">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenTranscript(item.output_file!)}
                        disabled={isLoading}
                        sx={{ opacity: isLoading ? 0.5 : 1 }}
                      >
                        <Description fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="Show transcript folder">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenFile(item.output_file!, 'output')}
                        disabled={isLoading}
                        sx={{ opacity: isLoading ? 0.5 : 1 }}
                      >
                        <FolderOpen fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </>
                )}

                {/* Quick action for input files */}
                {item.status !== 'completed' && (
                  <Tooltip title="Show input file">
                    <IconButton
                      size="small"
                      onClick={() => handleOpenFile(item.file_path, 'input')}
                      disabled={isLoading}
                      sx={{ opacity: isLoading ? 0.5 : 1 }}
                    >
                      <OpenInNew fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}

                {/* More actions menu */}
                <Tooltip title="More actions">
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuOpen(e, item.id)}
                    disabled={isLoading}
                    sx={{ opacity: isLoading ? 0.5 : 1 }}
                  >
                    {isLoading && loadingOperation && selectedItemId === item.id ? (
                      <CircularProgress size={16} />
                    ) : (
                      <MoreVert fontSize="small" />
                    )}
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>

            {/* Progress Bar */}
            {item.status === 'processing' && (
              <Box sx={{ mb: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={item.progress}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: alpha(theme.palette.primary.main, 0.15)
                  }}
                />
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                  <Typography variant="caption" color="textSecondary">
                    {item.current_step || 'Processing...'}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {item.progress}%
                    {item.estimated_time_remaining && (
                      ` • ${Math.ceil(item.estimated_time_remaining / 60)}min left`
                    )}
                  </Typography>
                </Box>
              </Box>
            )}

            {/* Error Message */}
            {item.status === 'failed' && item.error && (
              <Box sx={{ mt: 1 }}>
                <Typography
                  variant="caption"
                  color="error"
                  sx={{
                    backgroundColor: alpha(theme.palette.error.main, 0.1),
                    p: 1,
                    borderRadius: 1,
                    display: 'block'
                  }}
                >
                  {item.error}
                </Typography>
              </Box>
            )}

            {/* Success Info */}
            {item.status === 'completed' && (
              <Box sx={{ mt: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" color="success.main">
                    Completed in {item.processing_time ? Math.ceil(item.processing_time / 60) : 0} minutes
                    {item.completed_at && ` • ${formatTimestamp(item.completed_at)}`}
                  </Typography>
                </Box>
                {item.output_file && (
                  <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 0.5 }}>
                    Output: {item.output_file}
                  </Typography>
                )}
              </Box>
            )}

            {/* Loading State */}
            {isLoading && loadingOperation && selectedItemId === item.id && (
              <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={16} />
                <Typography variant="caption" color="primary">
                  {loadingOperation}
                </Typography>
              </Box>
            )}
          </ListItem>
        ))}
      </List>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          elevation: 3,
          sx: {
            minWidth: 200,
            '& .MuiMenuItem-root': {
              fontSize: '0.875rem',
              '&.destructive': {
                color: theme.palette.error.main
              }
            }
          }
        }}
      >
        {selectedItemId && (() => {
          const selectedItem = displayItems.find(item => item.id === selectedItemId)
          if (!selectedItem) return null
          
          const actions = getAvailableActions(selectedItem)
          return actions.map((action, index) => [
            action.destructive && index > 0 && <Divider key={`divider-${action.id}`} />,
            <MenuItem
              key={action.id}
              onClick={() => handleMenuAction(action.id, selectedItem)}
              className={action.destructive ? 'destructive' : ''}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                {action.icon}
              </ListItemIcon>
              <ListItemText primary={action.label} />
            </MenuItem>
          ])
        })()}
      </Menu>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseNotification}
          severity={notification.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialog.open}
        onClose={handleConfirmDialogClose}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ whiteSpace: 'pre-wrap' }}>
            {confirmDialog.message}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleConfirmDialogClose} color="primary">
            Cancel
          </Button>
          <Button onClick={handleConfirmAction} color="primary" variant="contained" autoFocus>
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default QueuePanel