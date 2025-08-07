import React, { useState, useEffect } from 'react'
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
import { useAppStore } from '../store/appStore'

interface SystemMetrics {
  memory: { total: number; used: number; free: number; usedPercentage: number }
  disk: { total: number; free: number; used: number }
  cpu: { cores: number; model: string; hasGPU: boolean; processingMode: string }
  backend: { status: string; timestamp: number }
}

const StatusBar: React.FC = () => {
  const theme = useTheme()
  const { processingOptions } = useAppStore()
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    memory: { total: 0, used: 0, free: 0, usedPercentage: 0 },
    disk: { total: 0, free: 0, used: 0 },
    cpu: { cores: 0, model: 'Unknown', hasGPU: false, processingMode: 'CPU' },
    backend: { status: 'disconnected', timestamp: 0 }
  })

  useEffect(() => {
    const updateSystemMetrics = async () => {
      if (!window.electronAPI) return

      try {
        const [memory, disk, cpu, backend] = await Promise.all([
          window.electronAPI.system.getMemoryUsage(),
          window.electronAPI.system.getDiskSpace(),
          window.electronAPI.system.getCPUInfo(),
          window.electronAPI.backend.healthCheck()
        ])

        setSystemMetrics({ memory, disk, cpu, backend })
      } catch (error) {
        console.error('Failed to update system metrics:', error)
      }
    }

    // Update immediately
    updateSystemMetrics()

    // Update every 5 seconds
    const interval = setInterval(updateSystemMetrics, 5000)
    return () => clearInterval(interval)
  }, [])

  const getConnectionStatus = () => {
    switch (systemMetrics.backend.status) {
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
              animation: systemMetrics.backend.status === 'connecting' ? 'pulse 1.5s infinite' : 'none'
            }} 
          />
          <Typography variant="caption" color="textSecondary">
            Backend: {connectionStatus.label}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Wifi sx={{ fontSize: 14, color: theme.palette.text.secondary }} />
          <Typography variant="caption" color="textSecondary">
            Model: {processingOptions?.whisper_model || 'base'}
          </Typography>
        </Box>
      </Box>

      {/* Right side - System Info */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Memory sx={{ fontSize: 14, color: theme.palette.text.secondary }} />
          <Typography variant="caption" color="textSecondary">
            Memory: {systemMetrics.memory.usedPercentage}%
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Storage sx={{ fontSize: 14, color: theme.palette.text.secondary }} />
          <Typography variant="caption" color="textSecondary">
            Disk: {systemMetrics.disk.free}GB
          </Typography>
        </Box>

        <Chip
          label={systemMetrics.cpu.processingMode}
          size="small"
          variant="outlined"
          sx={{
            height: 20,
            fontSize: '0.65rem',
            color: systemMetrics.cpu.processingMode === 'GPU' ? theme.palette.success.main : theme.palette.text.secondary,
            borderColor: systemMetrics.cpu.processingMode === 'GPU' ? theme.palette.success.main : theme.palette.divider
          }}
        />
      </Box>
    </Box>
  )
}

export default StatusBar