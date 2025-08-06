import React from 'react'
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Grid,
  Card,
  CardContent,
  useTheme,
  alpha,
  Chip
} from '@mui/material'
import {
  Speed,
  Schedule,
  Assessment,
  CheckCircle
} from '@mui/icons-material'

interface ProgressSectionProps {
  isProcessing: boolean
  isPaused: boolean
}

// Mock session data for development
const mockSession = {
  id: 'session-123',
  started_at: '2025-01-06T10:00:00Z',
  total_files: 8,
  completed_files: 3,
  failed_files: 1,
  total_processing_time: 420, // 7 minutes
  average_time_per_file: 140, // ~2.3 minutes
  output_directory: 'C:/Output/',
  is_paused: false
}

const ProgressSection: React.FC<ProgressSectionProps> = ({ isProcessing, isPaused }) => {
  const theme = useTheme()

  // Mock current processing stats
  const currentProgress = 65 // Overall progress percentage
  const estimatedTimeRemaining = 315 // 5.25 minutes remaining
  const processingSpeed = 2.3 // files per hour

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}h ${minutes}m`
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`
    } else {
      return `${secs}s`
    }
  }

  const getProcessingStatus = () => {
    if (!isProcessing) return 'Ready'
    if (isPaused) return 'Paused'
    return 'Processing'
  }

  const getStatusColor = () => {
    if (!isProcessing) return theme.palette.text.secondary
    if (isPaused) return theme.palette.warning.main
    return theme.palette.primary.main
  }

  return (
    <Paper
      elevation={1}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: theme.palette.background.elevation1
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Assessment color="primary" />
            Progress Overview
          </Typography>
          
          <Chip
            label={getProcessingStatus()}
            color={isProcessing ? (isPaused ? 'warning' : 'primary') : 'default'}
            variant={isProcessing ? 'filled' : 'outlined'}
            size="small"
          />
        </Box>
      </Box>

      <Box sx={{ p: 2, flexGrow: 1 }}>
        {/* Overall Progress */}
        {isProcessing && (
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" fontWeight={500}>
                Overall Progress
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {currentProgress}%
              </Typography>
            </Box>
            
            <LinearProgress
              variant="determinate"
              value={currentProgress}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: alpha(theme.palette.primary.main, 0.15),
                '& .MuiLinearProgress-bar': {
                  background: theme.palette.gradient.primary,
                  borderRadius: 4
                }
              }}
            />
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
              <Typography variant="caption" color="textSecondary">
                {mockSession.completed_files} of {mockSession.total_files} files completed
              </Typography>
              <Typography variant="caption" color="textSecondary">
                ~{formatTime(estimatedTimeRemaining)} remaining
              </Typography>
            </Box>
          </Box>
        )}

        {/* Statistics Cards */}
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Card
              sx={{
                background: alpha(theme.palette.success.main, 0.1),
                border: `1px solid ${alpha(theme.palette.success.main, 0.2)}`
              }}
            >
              <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckCircle sx={{ color: theme.palette.success.main, fontSize: 20 }} />
                  <Box>
                    <Typography variant="h6" color="success.main">
                      {mockSession.completed_files}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Completed
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={6}>
            <Card
              sx={{
                background: alpha(theme.palette.info.main, 0.1),
                border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`
              }}
            >
              <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Speed sx={{ color: theme.palette.info.main, fontSize: 20 }} />
                  <Box>
                    <Typography variant="h6" color="info.main">
                      {processingSpeed}x
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Speed
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={6}>
            <Card
              sx={{
                background: alpha(theme.palette.primary.main, 0.1),
                border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
              }}
            >
              <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Schedule sx={{ color: theme.palette.primary.main, fontSize: 20 }} />
                  <Box>
                    <Typography variant="h6" color="primary.main">
                      {formatTime(mockSession.total_processing_time)}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Total Time
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={6}>
            <Card
              sx={{
                background: alpha(theme.palette.secondary.main, 0.1),
                border: `1px solid ${alpha(theme.palette.secondary.main, 0.2)}`
              }}
            >
              <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Schedule sx={{ color: theme.palette.secondary.main, fontSize: 20 }} />
                  <Box>
                    <Typography variant="h6" color="secondary.main">
                      {formatTime(mockSession.average_time_per_file)}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Avg/File
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Current Processing Info */}
        {isProcessing && currentProcessingFile && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Current File
            </Typography>
            <Box
              sx={{
                p: 2,
                backgroundColor: isPaused 
                  ? alpha(theme.palette.warning.main, 0.05) 
                  : alpha(theme.palette.primary.main, 0.05),
                border: `1px solid ${alpha(
                  isPaused ? theme.palette.warning.main : theme.palette.primary.main, 0.15
                )}`,
                borderRadius: 1
              }}
            >
              <Typography variant="body2" fontWeight={500} gutterBottom>
                {currentProcessingFile.file_path.split(/[\\\/]/).pop() || currentProcessingFile.file_path}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {currentProcessingFile.current_step || 'Processing'} • {Math.round(currentProcessingFile.progress || 0)}% complete
              </Typography>
              
              {/* Individual file progress bar */}
              <LinearProgress
                variant="determinate"
                value={currentProcessingFile.progress || 0}
                sx={{
                  mt: 1,
                  height: 4,
                  borderRadius: 2,
                  backgroundColor: alpha(
                    isPaused ? theme.palette.warning.main : theme.palette.primary.main, 0.2
                  ),
                  '& .MuiLinearProgress-bar': {
                    background: isPaused 
                      ? theme.palette.warning.main 
                      : theme.palette.gradient?.primary || theme.palette.primary.main,
                    borderRadius: 2
                  }
                }}
              />
            </Box>
          </Box>
        )}
        
        {/* Show message when no files are processing */}
        {!isProcessing && totalFiles === 0 && (
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="textSecondary">
              No files in queue. Add video files to start transcription.
            </Typography>
          </Box>
        )}
        
        {!isProcessing && totalFiles > 0 && completedFiles === totalFiles && (
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="success.main" sx={{ fontWeight: 500 }}>
              All files processed successfully!
            </Typography>
          </Box>
        )}
      </Box>
    </Paper>
  )
}

export default ProgressSection