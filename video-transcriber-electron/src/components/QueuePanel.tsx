import React from 'react'
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
  alpha
} from '@mui/material'
import {
  VideoFile,
  CheckCircle,
  Error,
  Schedule,
  PlayCircle,
  Delete,
  OpenInNew
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

interface QueuePanelProps {
  items?: QueueItem[]
}

const QueuePanel: React.FC<QueuePanelProps> = ({ items }) => {
  const { queueItems, removeFromQueue } = useAppStore()
  
  // Use store data if available, otherwise use props or fallback to mock data
  const displayItems = items || queueItems.length > 0 ? queueItems : mockQueueItems
  const theme = useTheme()

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

  const handleOpenFile = async (filePath: string) => {
    if (window.electronAPI?.shell) {
      await window.electronAPI.shell.showItemInFolder(filePath)
    }
  }

  const handleRemoveFile = async (id: string) => {
    try {
      await removeFromQueue(id)
    } catch (error) {
      console.error('Failed to remove file:', error)
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
                  </Typography>
                </Box>
              </Box>

              {/* Actions */}
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                <IconButton
                  size="small"
                  onClick={() => handleOpenFile(item.file_path)}
                  title="Show in folder"
                >
                  <OpenInNew fontSize="small" />
                </IconButton>
                
                {item.status !== 'processing' && (
                  <IconButton
                    size="small"
                    onClick={() => handleRemoveFile(item.id)}
                    title="Remove from queue"
                  >
                    <Delete fontSize="small" />
                  </IconButton>
                )}
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
                <Typography variant="caption" color="success.main">
                  Completed in {item.processing_time ? Math.ceil(item.processing_time / 60) : 0} minutes
                  {item.output_file && (
                    <IconButton
                      size="small"
                      onClick={() => item.output_file && handleOpenFile(item.output_file)}
                      sx={{ ml: 1, p: 0.25 }}
                      title="Open output file"
                    >
                      <OpenInNew fontSize="inherit" />
                    </IconButton>
                  )}
                </Typography>
              </Box>
            )}
          </ListItem>
        ))}
      </List>
    </Box>
  )
}

export default QueuePanel