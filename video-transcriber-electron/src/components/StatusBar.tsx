import React from 'react'
import {
  Box,
  Typography,
  Chip,
  useTheme,
  alpha
} from '@mui/material'
import {
  Circle,
  Memory,
  Storage,
  Wifi
} from '@mui/icons-material'

const StatusBar: React.FC = () => {
  const theme = useTheme()

  // Mock system status data
  const systemStatus = {
    pythonBackend: 'connected',
    whisperModel: 'large',
    memoryUsage: 45, // percentage
    diskSpace: 78, // GB available
    processingMode: 'GPU'
  }

  const getConnectionStatus = () => {
    switch (systemStatus.pythonBackend) {
      case 'connected':
        return { color: theme.palette.success.main, label: 'Connected' }
      case 'connecting':
        return { color: theme.palette.warning.main, label: 'Connecting' }
      case 'disconnected':
        return { color: theme.palette.error.main, label: 'Disconnected' }
      default:
        return { color: theme.palette.text.secondary, label: 'Unknown' }
    }
  }

  const connectionStatus = getConnectionStatus()

  return (
    <Box
      sx={{
        height: 32,
        px: 2,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: theme.palette.background.elevation2,
        borderTop: `1px solid ${theme.palette.divider}`,
        fontSize: '0.75rem'
      }}
    >
      {/* Left side - Connection Status */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Circle 
            sx={{ 
              fontSize: 8, 
              color: connectionStatus.color,
              animation: systemStatus.pythonBackend === 'connecting' ? 'pulse 1.5s infinite' : 'none'
            }} 
          />
          <Typography variant="caption" color="textSecondary">
            Backend: {connectionStatus.label}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Wifi sx={{ fontSize: 14, color: theme.palette.text.secondary }} />
          <Typography variant="caption" color="textSecondary">
            Model: {systemStatus.whisperModel}
          </Typography>
        </Box>
      </Box>

      {/* Right side - System Info */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Memory sx={{ fontSize: 14, color: theme.palette.text.secondary }} />
          <Typography variant="caption" color="textSecondary">
            Memory: {systemStatus.memoryUsage}%
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Storage sx={{ fontSize: 14, color: theme.palette.text.secondary }} />
          <Typography variant="caption" color="textSecondary">
            Disk: {systemStatus.diskSpace}GB
          </Typography>
        </Box>

        <Chip
          label={systemStatus.processingMode}
          size="small"
          variant="outlined"
          sx={{
            height: 20,
            fontSize: '0.65rem',
            color: systemStatus.processingMode === 'GPU' ? theme.palette.success.main : theme.palette.text.secondary,
            borderColor: systemStatus.processingMode === 'GPU' ? theme.palette.success.main : theme.palette.divider
          }}
        />
      </Box>
    </Box>
  )
}

export default StatusBar