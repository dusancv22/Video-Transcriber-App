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
import { useAppStore } from '../store/appStore'

interface ProgressSectionProps {
  isProcessing: boolean
  isPaused: boolean
}

const ProgressSection: React.FC<ProgressSectionProps> = ({ isProcessing, isPaused }) => {
  const theme = useTheme()

  // Get real data from store
  const currentSession = useAppStore(state => state.currentSession)
  const queueStats = useAppStore(state => state.queueStats)
  const processingStatus = useAppStore(state => state.processingStatus)
  
  // Calculate real progress data
  const totalFiles = queueStats.total
  const completedFiles = queueStats.completed
  const currentProcessingFile = processingStatus?.current_file || null
  
  // Debug logging for session state
  console.log('📊 ProgressSection: currentSession:', currentSession)
  console.log('📊 ProgressSection: isProcessing:', isProcessing)
  console.log('📊 ProgressSection: queueStats:', queueStats)
  
  // Calculate overall progress percentage with better handling for different states
  const currentProgress = totalFiles > 0 ? Math.round((completedFiles / totalFiles) * 100) : 0
  
  // If processing, add partial progress for current file
  const adjustedProgress = isProcessing && currentProcessingFile && totalFiles > 0
    ? Math.round(((completedFiles + (currentProcessingFile.progress / 100)) / totalFiles) * 100)
    : currentProgress
  
  // Calculate processing speed (files per hour) based on session data or fallback to basic calculation
  const processingSpeed = currentSession && currentSession.total_processing_time > 0 
    ? Math.round((currentSession.completed_files / (currentSession.total_processing_time / 3600)) * 10) / 10 
    : (isProcessing && completedFiles > 0 ? 0.5 : 0) // Fallback speed when no session data
  
  // Estimate remaining time based on current speed and remaining files
  const remainingFiles = totalFiles - completedFiles
  const averageTimePerFile = currentSession?.average_time_per_file || (isProcessing ? 120 : 0) // 2 minutes default per file
  const estimatedTimeRemaining = remainingFiles * averageTimePerFile

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
                {adjustedProgress}%
              </Typography>
            </Box>
            
            {/* Show session status for debugging */}
            {!currentSession && (
              <Typography variant="caption" color="warning.main" sx={{ display: 'block', mb: 1 }}>
                Session initializing... Progress based on queue status.
              </Typography>
            )}
            
            <LinearProgress
              variant="determinate"
              value={adjustedProgress}
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
                {completedFiles} of {totalFiles} files completed
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
                      {completedFiles}
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
                      {formatTime(currentSession?.total_processing_time || 0)}
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
                      {formatTime(currentSession?.average_time_per_file || 0)}
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
                {currentProcessingFile.step || 'Processing'} • {Math.round(currentProcessingFile.progress || 0)}% complete
                {currentProcessingFile.estimated_time_remaining > 0 && ` • ~${formatTime(currentProcessingFile.estimated_time_remaining)} remaining`}
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