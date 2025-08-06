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
  useTheme
} from '@mui/material'
import {
  CloudUpload,
  VideoFile,
  FolderOpen
} from '@mui/icons-material'

interface FileDropZoneProps {
  onFilesAdded?: (files: File[]) => void
}

const FileDropZone: React.FC<FileDropZoneProps> = ({ onFilesAdded }) => {
  const { addFiles } = useAppStore()
  const theme = useTheme()
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])

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

    const files = Array.from(e.dataTransfer.files).filter(file => 
      file.type.startsWith('video/') || 
      ['.mp4', '.avi', '.mkv', '.mov'].some(ext => 
        file.name.toLowerCase().endsWith(ext)
      )
    )

    // Convert File objects to file paths for API
    const filePaths = files.map(file => (file as any).path || file.name)
    
    setSelectedFiles(prev => [...prev, ...files])
    onFilesAdded?.(files)
    
    // Add files to queue via API
    try {
      await addFiles(filePaths)
    } catch (error) {
      console.error('Failed to add files to queue:', error)
    }
  }, [onFilesAdded, addFiles])

  const handleFileSelect = useCallback(async () => {
    if (window.electronAPI?.dialog) {
      const result = await window.electronAPI.dialog.showOpenDialog({
        properties: ['openFile', 'multiSelections'],
        filters: [
          {
            name: 'Video Files',
            extensions: ['mp4', 'avi', 'mkv', 'mov']
          }
        ]
      })

      if (!result.canceled && result.filePaths.length > 0) {
        try {
          await addFiles(result.filePaths)
        } catch (error) {
          console.error('Failed to add selected files:', error)
        }
      }
    }
  }, [])

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
          border: `2px dashed ${isDragOver ? theme.palette.primary.main : theme.palette.divider}`,
          borderRadius: 2,
          p: 4,
          textAlign: 'center',
          backgroundColor: isDragOver 
            ? alpha(theme.palette.primary.main, 0.05)
            : alpha(theme.palette.background.default, 0.5),
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          minHeight: 200,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 2,
          '&:hover': {
            borderColor: theme.palette.primary.main,
            backgroundColor: alpha(theme.palette.primary.main, 0.03)
          }
        }}
        onClick={handleFileSelect}
      >
        <CloudUpload 
          sx={{ 
            fontSize: 48, 
            color: isDragOver ? theme.palette.primary.main : theme.palette.text.secondary,
            mb: 1
          }} 
        />
        
        <Typography variant="h6" color="textPrimary" gutterBottom>
          Drop video files here
        </Typography>
        
        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
          or click to browse files
        </Typography>
        
        <Button
          variant="outlined"
          startIcon={<FolderOpen />}
          onClick={(e) => {
            e.stopPropagation()
            handleFileSelect()
          }}
          sx={{
            '&:hover': {
              transform: 'translateY(-1px)',
              boxShadow: theme.shadows[4]
            }
          }}
        >
          Browse Files
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
    </Box>
  )
}

export default FileDropZone