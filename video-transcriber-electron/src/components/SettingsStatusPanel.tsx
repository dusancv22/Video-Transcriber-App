import React from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Chip,
  useTheme,
  alpha,
  Tooltip
} from '@mui/material'
import {
  Settings as SettingsIcon,
  FolderOpen as FolderIcon,
  Psychology as ModelIcon,
  Language as LanguageIcon,
  TextFields as FormatIcon,
  Info as InfoIcon
} from '@mui/icons-material'
import { useAppStore } from '../store/appStore'

interface SettingsStatusPanelProps {
  onOpenSettings: () => void
}

const SettingsStatusPanel: React.FC<SettingsStatusPanelProps> = ({ onOpenSettings }) => {
  const theme = useTheme()
  const { processingOptions, isSettingsLoaded } = useAppStore()

  // Helper function to truncate long paths
  const truncatePath = (path: string, maxLength: number = 40): string => {
    if (path.length <= maxLength) return path
    
    // Try to keep the drive and filename visible
    const parts = path.split(/[\\\/]/)
    if (parts.length > 2) {
      const drive = parts[0]
      const filename = parts[parts.length - 1]
      const remaining = maxLength - drive.length - filename.length - 6 // Account for "...\\" 
      
      if (remaining > 0) {
        return `${drive}\\...\\${filename}`
      }
    }
    
    // Fallback: truncate from the middle
    const start = path.slice(0, maxLength / 2 - 2)
    const end = path.slice(-(maxLength / 2 - 2))
    return `${start}...${end}`
  }

  // Get model display info
  const getModelInfo = (model: string) => {
    const modelMap = {
      'base': { label: 'Base', size: '~39 MB', color: 'info' },
      'small': { label: 'Small', size: '~244 MB', color: 'success' },
      'medium': { label: 'Medium', size: '~769 MB', color: 'warning' },
      'large': { label: 'Large', size: '~1550 MB', color: 'error' }
    }
    return modelMap[model as keyof typeof modelMap] || modelMap.large
  }

  // Get format display info
  const getFormatInfo = (format: string) => {
    const formatMap = {
      'txt': { label: 'Plain Text', ext: '.txt' },
      'srt': { label: 'SubRip', ext: '.srt' },
      'vtt': { label: 'WebVTT', ext: '.vtt' }
    }
    return formatMap[format as keyof typeof formatMap] || formatMap.txt
  }

  // Check if settings are at defaults (excluding output directory which is system-specific)
  const isUsingDefaults = processingOptions.whisper_model === 'large' && 
                         processingOptions.language === 'en' && 
                         processingOptions.output_format === 'txt'

  const modelInfo = getModelInfo(processingOptions.whisper_model)
  const formatInfo = getFormatInfo(processingOptions.output_format)

  if (!isSettingsLoaded) {
    return (
      <Paper
        elevation={1}
        sx={{
          p: 2,
          background: theme.palette.background.elevation1,
          border: `1px solid ${theme.palette.divider}`
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SettingsIcon color="action" />
          <Typography variant="body2" color="textSecondary">
            Loading settings...
          </Typography>
        </Box>
      </Paper>
    )
  }

  return (
    <Paper
      elevation={1}
      sx={{
        p: 2,
        background: alpha(theme.palette.primary.main, 0.02),
        border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
        borderRadius: 2
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SettingsIcon color="primary" />
          <Typography variant="h6" fontWeight={500} color="primary.main">
            Current Settings
          </Typography>
          
          {isUsingDefaults && (
            <Tooltip title="Using default settings - optimize for your needs">
              <Chip 
                label="Defaults" 
                size="small" 
                color="default" 
                variant="outlined"
                sx={{ fontSize: '0.7rem' }}
              />
            </Tooltip>
          )}
        </Box>
        
        <Button
          variant="outlined"
          size="small"
          startIcon={<SettingsIcon />}
          onClick={onOpenSettings}
          sx={{ minWidth: 120 }}
        >
          Configure
        </Button>
      </Box>

      <Grid container spacing={2}>
        {/* Output Directory */}
        <Grid item xs={12}>
          <Box sx={{ 
            p: 1.5, 
            backgroundColor: alpha(theme.palette.background.paper, 0.8),
            borderRadius: 1,
            border: `1px solid ${theme.palette.divider}`
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <FolderIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="caption" fontWeight={500} color="text.secondary" textTransform="uppercase">
                Output Directory
              </Typography>
            </Box>
            <Tooltip title={processingOptions.output_directory}>
              <Typography variant="body2" sx={{ 
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                color: 'text.primary',
                wordBreak: 'break-all'
              }}>
                {truncatePath(processingOptions.output_directory)}
              </Typography>
            </Tooltip>
          </Box>
        </Grid>

        {/* Whisper Model */}
        <Grid item xs={12} sm={4}>
          <Box sx={{ 
            p: 1.5, 
            backgroundColor: alpha(theme.palette.background.paper, 0.8),
            borderRadius: 1,
            border: `1px solid ${theme.palette.divider}`,
            height: '100%'
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <ModelIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="caption" fontWeight={500} color="text.secondary" textTransform="uppercase">
                Model
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" fontWeight={500}>
                {modelInfo.label}
              </Typography>
              <Chip 
                label={modelInfo.size}
                size="small"
                color={modelInfo.color as any}
                variant="outlined"
                sx={{ fontSize: '0.65rem', height: 20 }}
              />
            </Box>
          </Box>
        </Grid>

        {/* Language */}
        <Grid item xs={12} sm={4}>
          <Box sx={{ 
            p: 1.5, 
            backgroundColor: alpha(theme.palette.background.paper, 0.8),
            borderRadius: 1,
            border: `1px solid ${theme.palette.divider}`,
            height: '100%'
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <LanguageIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="caption" fontWeight={500} color="text.secondary" textTransform="uppercase">
                Language
              </Typography>
            </Box>
            <Typography variant="body2" fontWeight={500}>
              {processingOptions.language === 'en' ? 'English Only' : 'Auto-detect'}
            </Typography>
          </Box>
        </Grid>

        {/* Output Format */}
        <Grid item xs={12} sm={4}>
          <Box sx={{ 
            p: 1.5, 
            backgroundColor: alpha(theme.palette.background.paper, 0.8),
            borderRadius: 1,
            border: `1px solid ${theme.palette.divider}`,
            height: '100%'
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <FormatIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="caption" fontWeight={500} color="text.secondary" textTransform="uppercase">
                Format
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" fontWeight={500}>
                {formatInfo.label}
              </Typography>
              <Chip 
                label={formatInfo.ext}
                size="small"
                color="primary"
                variant="outlined"
                sx={{ fontSize: '0.65rem', height: 20 }}
              />
            </Box>
          </Box>
        </Grid>
      </Grid>

      {/* Quick Info */}
      {!processingOptions.output_directory && (
        <Box sx={{ 
          mt: 2, 
          p: 1.5,
          backgroundColor: alpha(theme.palette.warning.main, 0.1),
          border: `1px solid ${alpha(theme.palette.warning.main, 0.3)}`,
          borderRadius: 1,
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <InfoIcon sx={{ fontSize: 18, color: 'warning.main' }} />
          <Typography variant="caption" color="warning.main">
            Please configure your output directory before starting processing
          </Typography>
        </Box>
      )}
    </Paper>
  )
}

export default SettingsStatusPanel