import React, { useState, useEffect, useCallback } from 'react'
import {
  Box,
  TextField,
  FormControl,
  Select,
  MenuItem,
  Button,
  Typography,
  Alert,
  Tooltip,
  CircularProgress,
  Snackbar,
  Grid,
  Paper,
  Divider
} from '@mui/material'
import {
  FolderOpen as FolderOpenIcon,
  Settings as SettingsIcon,
  RestartAlt as RestartAltIcon,
  Save as SaveIcon,
  Info as InfoIcon,
  PlayArrow,
  ErrorOutline
} from '@mui/icons-material'
import { useTheme, alpha } from '@mui/material/styles'
import { useAppStore } from '../store/appStore'
import { SystemCapabilityIndicator } from './SystemCapabilityHelper'

// TypeScript interfaces for processing options
export interface ProcessingOptions {
  output_directory: string
  whisper_model: 'base' | 'small' | 'medium' | 'large'
  language: 'en' | 'auto'
  output_format: 'txt' | 'srt' | 'vtt'
}

// Get default output directory dynamically
const getDefaultOutputDirectory = async (): Promise<string> => {
  try {
    if (typeof window !== 'undefined' && (window as any)?.electronAPI?.path?.getDefaultOutputDirectory) {
      return await (window as any).electronAPI.path.getDefaultOutputDirectory()
    }
    return './Video Transcriber Output'
  } catch (error) {
    console.warn('Failed to get default output directory:', error)
    return './transcripts'
  }
}

// Default settings configuration with better system integration
const DEFAULT_SETTINGS: ProcessingOptions = {
  output_directory: '',  // Will be set dynamically
  whisper_model: 'large',
  language: 'en',
  output_format: 'txt'
}

// Whisper model options with descriptions
const WHISPER_MODELS = [
  { 
    value: 'base' as const, 
    label: 'Base', 
    description: 'Fastest processing, basic accuracy (~39 MB)'
  },
  { 
    value: 'small' as const, 
    label: 'Small', 
    description: 'Good balance of speed and accuracy (~244 MB)'
  },
  { 
    value: 'medium' as const, 
    label: 'Medium', 
    description: 'Better accuracy, moderate speed (~769 MB)'
  },
  { 
    value: 'large' as const, 
    label: 'Large', 
    description: 'Highest accuracy, slower processing (~1550 MB)'
  }
]

// Language options
const LANGUAGE_OPTIONS = [
  { value: 'en' as const, label: 'English Only', description: 'Process audio as English (recommended)' },
  { value: 'auto' as const, label: 'Auto-detect', description: 'Automatically detect language' }
]

// Output format options
const OUTPUT_FORMATS = [
  { 
    value: 'txt' as const, 
    label: 'Plain Text (.txt)', 
    description: 'Simple text file with the transcription'
  },
  { 
    value: 'srt' as const, 
    label: 'SubRip (.srt)', 
    description: 'Subtitle format with timestamps'
  },
  { 
    value: 'vtt' as const, 
    label: 'WebVTT (.vtt)', 
    description: 'Web Video Text Tracks format'
  }
]

export const SettingsPanel: React.FC = () => {
  const theme = useTheme()
  const { processingOptions, setProcessingOptions, startProcessing } = useAppStore()

  // Local state for form values
  const [formValues, setFormValues] = useState<ProcessingOptions>(processingOptions)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [directoryError, setDirectoryError] = useState<string | null>(null)
  const [isBrowsing, setIsBrowsing] = useState(false)

  // Validate directory path
  const validateDirectory = useCallback((path: string): boolean => {
    if (!path || path.trim().length === 0) {
      setDirectoryError('Output directory is required')
      return false
    }
    
    // Basic path validation (Windows and Unix-like paths)
    const pathRegex = /^[a-zA-Z]:[\\\/]|^[\/~]/
    if (!pathRegex.test(path)) {
      setDirectoryError('Please enter a valid directory path')
      return false
    }
    
    setDirectoryError(null)
    return true
  }, [])

  // Initialize form values when component mounts or processingOptions change
  useEffect(() => {
    const initializeSettings = async () => {
      let settingsToUse = { ...processingOptions }
      
      // If output directory is empty, set a default
      if (!settingsToUse.output_directory) {
        settingsToUse.output_directory = await getDefaultOutputDirectory()
      }
      
      setFormValues(settingsToUse)
      setError(null)
      setSuccess(false)
      setDirectoryError(null)
      
      // Validate initial settings
      validateDirectory(settingsToUse.output_directory)
    }
    
    initializeSettings()
  }, [processingOptions, validateDirectory])

  // Handle form field changes
  const handleFieldChange = useCallback((field: keyof ProcessingOptions, value: string) => {
    setFormValues(prev => ({ ...prev, [field]: value }))
    
    // Validate directory field immediately
    if (field === 'output_directory') {
      validateDirectory(value)
    }
  }, [validateDirectory])

  // Handle directory browse
  const handleBrowseDirectory = useCallback(async () => {
    try {
      setIsBrowsing(true)
      setError(null)
      
      // Check if electronAPI is available
      if (!window.electronAPI?.dialog?.showOpenDialog) {
        throw new Error('Directory browsing is not available. Please enter the path manually.')
      }
      
      const result = await window.electronAPI.dialog.showOpenDialog({
        title: 'Select Output Directory',
        properties: ['openDirectory', 'createDirectory'],
        defaultPath: formValues.output_directory || DEFAULT_SETTINGS.output_directory
      })
      
      if (!result.canceled && result.filePaths.length > 0) {
        const selectedPath = result.filePaths[0]
        handleFieldChange('output_directory', selectedPath)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to open directory dialog'
      setError(`Directory selection failed: ${errorMessage}`)
      console.error('Directory browse error:', err)
    } finally {
      setIsBrowsing(false)
    }
  }, [formValues.output_directory, handleFieldChange])

  // Handle form submission (Save)
  const handleSave = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      // Validate all fields
      if (!validateDirectory(formValues.output_directory)) {
        return
      }
      
      // Save settings to store
      setProcessingOptions(formValues)
      
      // Show success feedback
      setSuccess(true)
      
      // Hide success after delay
      setTimeout(() => {
        setSuccess(false)
      }, 3000)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save settings'
      setError(`Save failed: ${errorMessage}`)
    } finally {
      setIsLoading(false)
    }
  }, [formValues, validateDirectory, setProcessingOptions])

  // Handle save and start processing
  const handleSaveAndStart = useCallback(async () => {
    console.log('🚀 Settings Panel: Save & Start Processing clicked')
    console.log('📋 Form values:', formValues)
    
    try {
      setIsLoading(true)
      setError(null)
      
      // Validate all fields
      console.log('🔍 Validating directory:', formValues.output_directory)
      if (!validateDirectory(formValues.output_directory)) {
        console.error('❌ Directory validation failed')
        return
      }
      console.log('✅ Directory validation passed')
      
      // Save settings to store
      console.log('💾 Saving settings to store...')
      setProcessingOptions(formValues)
      console.log('✅ Settings saved to store')
      
      // Show success feedback briefly
      setSuccess(true)
      
      // Start processing after a short delay
      console.log('⏳ Starting processing in 500ms...')
      setTimeout(async () => {
        try {
          console.log('🎬 Calling startProcessing()...')
          console.log('📝 Processing options being used:', formValues)
          
          await startProcessing()
          
          console.log('✅ startProcessing() completed successfully')
          
          // Hide success after delay
          setTimeout(() => {
            setSuccess(false)
          }, 3000)
          
        } catch (error) {
          console.error('❌ Failed to start processing:', error)
          console.error('Error details:', {
            message: error instanceof Error ? error.message : 'Unknown error',
            stack: error instanceof Error ? error.stack : undefined,
            type: typeof error,
            error
          })
          setError(`Failed to start processing: ${error instanceof Error ? error.message : 'Unknown error'}`)
        }
      }, 500)
      
    } catch (err) {
      console.error('❌ Error in handleSaveAndStart:', err)
      const errorMessage = err instanceof Error ? err.message : 'Failed to save settings'
      setError(`Save failed: ${errorMessage}`)
    } finally {
      setIsLoading(false)
    }
  }, [formValues, validateDirectory, setProcessingOptions, startProcessing])

  // Handle reset to defaults
  const handleReset = useCallback(async () => {
    const defaultDir = await getDefaultOutputDirectory()
    const resetSettings = { ...DEFAULT_SETTINGS, output_directory: defaultDir }
    setFormValues(resetSettings)
    setError(null)
    setDirectoryError(null)
    setSuccess(false)
    validateDirectory(defaultDir)
  }, [validateDirectory])

  // Check if form has changes
  const hasChanges = JSON.stringify(formValues) !== JSON.stringify(processingOptions)
  
  // Check if settings are valid for processing
  const canStartProcessing = !directoryError && formValues.output_directory.trim().length > 0
  
  // Check if directory browsing is available
  const canBrowseDirectory = typeof window !== 'undefined' && window.electronAPI?.dialog?.showOpenDialog

  // Clear error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError(null)
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [error])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SettingsIcon color="primary" />
          Processing Settings
        </Typography>
      </Box>

      {/* Content */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
        {/* Info Alert */}
        <Alert 
          severity="info" 
          sx={{ 
            mb: 2,
            fontSize: '0.85rem',
            '& .MuiAlert-message': {
              width: '100%'
            }
          }}
        >
          <Typography variant="body2" sx={{ fontSize: '0.85rem', fontWeight: 500 }}>
            Configure transcription settings
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
            Choose output directory, AI model, and format. Click "Start Processing" when ready.
          </Typography>
        </Alert>

        {/* Error Alert */}
        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: 2, fontSize: '0.85rem' }}
            onClose={() => setError(null)}
          >
            {error}
          </Alert>
        )}

        {/* Success Alert */}
        {success && (
          <Alert severity="success" sx={{ mb: 2, fontSize: '0.85rem' }}>
            Settings saved successfully!
          </Alert>
        )}

        <Grid container spacing={2}>
          {/* Output Directory Section */}
          <Grid item xs={12}>
            <Paper 
              elevation={0} 
              sx={{ 
                p: 2, 
                bgcolor: alpha(theme.palette.background.paper, 0.7),
                border: `1px solid ${theme.palette.divider}`
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                <FolderOpenIcon color="primary" sx={{ fontSize: 18 }} />
                <Typography variant="subtitle2" fontWeight={500}>
                  Output Directory
                </Typography>
                <Tooltip title="Directory where transcribed text files will be saved">
                  <InfoIcon color="action" sx={{ fontSize: 14 }} />
                </Tooltip>
              </Box>
              
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  size="small"
                  value={formValues.output_directory}
                  onChange={(e) => handleFieldChange('output_directory', e.target.value)}
                  error={!!directoryError}
                  helperText={
                    directoryError ? (
                      <Box component="span" sx={{ color: 'error.main', display: 'flex', alignItems: 'center', gap: 0.5, fontSize: '0.75rem' }}>
                        <ErrorOutline sx={{ fontSize: 12 }} />
                        {directoryError}
                      </Box>
                    ) : (
                      <Typography variant="caption" sx={{ fontSize: '0.7rem', color: 'text.secondary' }}>
                        Choose where to save transcribed files
                      </Typography>
                    )
                  }
                  placeholder="e.g., C:\Documents\Video Transcripts"
                  variant="outlined"
                  disabled={isLoading || isBrowsing}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'background.paper'
                    }
                  }}
                />
                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleBrowseDirectory}
                  disabled={isLoading || isBrowsing || !canBrowseDirectory}
                  startIcon={isBrowsing ? <CircularProgress size={12} /> : <FolderOpenIcon />}
                  sx={{ minWidth: 80 }}
                  title={!canBrowseDirectory ? 'Directory browsing not available. Please enter path manually.' : ''}
                >
                  {isBrowsing ? 'Browse...' : 'Browse'}
                </Button>
              </Box>
            </Paper>
          </Grid>

          {/* Whisper Model Section */}
          <Grid item xs={12}>
            <Paper 
              elevation={0} 
              sx={{ 
                p: 2, 
                bgcolor: alpha(theme.palette.background.paper, 0.7),
                border: `1px solid ${theme.palette.divider}`
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                <Typography variant="subtitle2" fontWeight={500}>
                  Whisper Model
                </Typography>
                <Tooltip title="Choose the AI model for transcription. Larger models provide better accuracy but take longer to process.">
                  <InfoIcon color="action" sx={{ fontSize: 14 }} />
                </Tooltip>
              </Box>
              
              <FormControl fullWidth size="small">
                <Select
                  value={formValues.whisper_model}
                  onChange={(e) => handleFieldChange('whisper_model', e.target.value)}
                  disabled={isLoading}
                  sx={{
                    bgcolor: 'background.paper'
                  }}
                >
                  {WHISPER_MODELS.map((model) => (
                    <MenuItem key={model.value} value={model.value}>
                      <Box>
                        <Typography variant="body2" fontWeight={500}>
                          {model.label}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                          {model.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              {/* System Capability Indicator */}
              <SystemCapabilityIndicator currentModel={formValues.whisper_model} />
            </Paper>
          </Grid>

          {/* Language & Format Row */}
          <Grid item xs={6}>
            <Paper 
              elevation={0} 
              sx={{ 
                p: 2, 
                bgcolor: alpha(theme.palette.background.paper, 0.7),
                border: `1px solid ${theme.palette.divider}`,
                height: '100%'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                <Typography variant="subtitle2" fontWeight={500}>
                  Language
                </Typography>
                <Tooltip title="Select the language for transcription processing">
                  <InfoIcon color="action" sx={{ fontSize: 14 }} />
                </Tooltip>
              </Box>
              
              <FormControl fullWidth size="small">
                <Select
                  value={formValues.language}
                  onChange={(e) => handleFieldChange('language', e.target.value)}
                  disabled={isLoading}
                  sx={{
                    bgcolor: 'background.paper'
                  }}
                >
                  {LANGUAGE_OPTIONS.map((language) => (
                    <MenuItem key={language.value} value={language.value}>
                      <Box>
                        <Typography variant="body2" fontWeight={500}>
                          {language.label}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                          {language.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Paper>
          </Grid>

          <Grid item xs={6}>
            <Paper 
              elevation={0} 
              sx={{ 
                p: 2, 
                bgcolor: alpha(theme.palette.background.paper, 0.7),
                border: `1px solid ${theme.palette.divider}`,
                height: '100%'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                <Typography variant="subtitle2" fontWeight={500}>
                  Output Format
                </Typography>
                <Tooltip title="Choose the format for the transcribed text output">
                  <InfoIcon color="action" sx={{ fontSize: 14 }} />
                </Tooltip>
              </Box>
              
              <FormControl fullWidth size="small">
                <Select
                  value={formValues.output_format}
                  onChange={(e) => handleFieldChange('output_format', e.target.value)}
                  disabled={isLoading}
                  sx={{
                    bgcolor: 'background.paper'
                  }}
                >
                  {OUTPUT_FORMATS.map((format) => (
                    <MenuItem key={format.value} value={format.value}>
                      <Box>
                        <Typography variant="body2" fontWeight={500}>
                          {format.label}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                          {format.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Paper>
          </Grid>
        </Grid>
      </Box>

      {/* Actions */}
      <Box sx={{ p: 2, borderTop: `1px solid ${theme.palette.divider}` }}>
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          {/* Reset Button */}
          <Button
            variant="outlined"
            color="warning"
            size="small"
            startIcon={<RestartAltIcon />}
            onClick={handleReset}
            disabled={isLoading}
            sx={{ flex: 1 }}
          >
            Reset
          </Button>

          {/* Save Button */}
          <Button
            variant="outlined"
            color="primary"
            size="small"
            startIcon={isLoading ? <CircularProgress size={12} color="inherit" /> : <SaveIcon />}
            onClick={handleSave}
            disabled={isLoading || !hasChanges || !!directoryError}
            sx={{ flex: 1 }}
          >
            {isLoading ? 'Saving...' : 'Save'}
          </Button>
        </Box>

        {/* Start Processing Button */}
        <Button
          variant="contained"
          color="primary"
          fullWidth
          startIcon={isLoading ? <CircularProgress size={16} color="inherit" /> : <PlayArrow />}
          onClick={handleSaveAndStart}
          disabled={isLoading || !canStartProcessing}
          sx={{ 
            background: theme.palette.gradient?.primary || theme.palette.primary.main,
            '&:hover': {
              background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
            }
          }}
          title={!canStartProcessing ? 'Please configure a valid output directory to start processing' : ''}
        >
          {isLoading ? 'Starting...' : 'Start Processing'}
        </Button>
      </Box>

      {/* Success Snackbar */}
      <Snackbar
        open={success}
        autoHideDuration={3000}
        onClose={() => setSuccess(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSuccess(false)} 
          severity="success" 
          variant="filled"
          sx={{ width: '100%' }}
        >
          Settings saved successfully!
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default SettingsPanel