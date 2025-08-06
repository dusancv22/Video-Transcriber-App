import React, { useState, useEffect, useCallback } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Box,
  IconButton,
  Typography,
  Alert,
  Tooltip,
  Divider,
  CircularProgress,
  Snackbar,
  Grid,
  Paper
} from '@mui/material'
import {
  Close as CloseIcon,
  FolderOpen as FolderOpenIcon,
  Settings as SettingsIcon,
  RestartAlt as RestartAltIcon,
  Save as SaveIcon,
  Info as InfoIcon
} from '@mui/icons-material'
import { useTheme, alpha } from '@mui/material/styles'
import { useAppStore } from '../store/appStore'

// TypeScript interfaces for processing options
export interface ProcessingOptions {
  output_directory: string
  whisper_model: 'base' | 'small' | 'medium' | 'large'
  language: 'en' | 'auto'
  output_format: 'txt' | 'srt' | 'vtt'
}

interface SettingsDialogProps {
  open: boolean
  onClose: () => void
}

// Default settings configuration
const DEFAULT_SETTINGS: ProcessingOptions = {
  output_directory: 'C:/Output/Transcripts',
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

export const SettingsDialog: React.FC<SettingsDialogProps> = ({ open, onClose }) => {
  const theme = useTheme()
  const { processingOptions, setProcessingOptions } = useAppStore()

  // Local state for form values
  const [formValues, setFormValues] = useState<ProcessingOptions>(processingOptions)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [directoryError, setDirectoryError] = useState<string | null>(null)
  const [isBrowsing, setIsBrowsing] = useState(false)

  // Initialize form values when dialog opens
  useEffect(() => {
    if (open) {
      setFormValues(processingOptions)
      setError(null)
      setSuccess(false)
      setDirectoryError(null)
    }
  }, [open, processingOptions])

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
      
      // Close dialog after a short delay
      setTimeout(() => {
        onClose()
      }, 1000)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save settings'
      setError(`Save failed: ${errorMessage}`)
    } finally {
      setIsLoading(false)
    }
  }, [formValues, validateDirectory, setProcessingOptions, onClose])

  // Handle cancel (discard changes)
  const handleCancel = useCallback(() => {
    setFormValues(processingOptions) // Reset to original values
    setError(null)
    setSuccess(false)
    setDirectoryError(null)
    onClose()
  }, [processingOptions, onClose])

  // Handle reset to defaults
  const handleReset = useCallback(() => {
    setFormValues(DEFAULT_SETTINGS)
    setError(null)
    setDirectoryError(null)
    setSuccess(false)
  }, [])

  // Check if form has changes
  const hasChanges = JSON.stringify(formValues) !== JSON.stringify(processingOptions)

  return (
    <>
      <Dialog
        open={open}
        onClose={handleCancel}
        maxWidth="md"
        fullWidth
        PaperProps={{
          elevation: 3,
          sx: {
            borderRadius: 3,
            minHeight: '600px',
            bgcolor: 'background.default'
          }
        }}
      >
        {/* Dialog Header */}
        <DialogTitle
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            bgcolor: alpha(theme.palette.primary.main, 0.1),
            color: 'primary.main',
            borderBottom: `1px solid ${theme.palette.divider}`,
            px: 3,
            py: 2
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <SettingsIcon />
            <Typography variant="h5" component="h1" fontWeight={600}>
              Processing Settings
            </Typography>
          </Box>
          
          <IconButton
            onClick={handleCancel}
            size="small"
            sx={{
              color: 'text.secondary',
              '&:hover': {
                bgcolor: alpha(theme.palette.error.main, 0.1),
                color: 'error.main'
              }
            }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        {/* Dialog Content */}
        <DialogContent sx={{ p: 3 }}>
          {/* Error Alert */}
          {error && (
            <Alert 
              severity="error" 
              sx={{ mb: 3 }}
              onClose={() => setError(null)}
            >
              {error}
            </Alert>
          )}

          {/* Success Alert */}
          {success && (
            <Alert severity="success" sx={{ mb: 3 }}>
              Settings saved successfully!
            </Alert>
          )}

          <Grid container spacing={3}>
            {/* Output Directory Section */}
            <Grid item xs={12}>
              <Paper 
                elevation={1} 
                sx={{ 
                  p: 3, 
                  bgcolor: alpha(theme.palette.background.paper, 0.7),
                  border: `1px solid ${theme.palette.divider}`
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <FolderOpenIcon color="primary" />
                  <Typography variant="h6" fontWeight={500}>
                    Output Directory
                  </Typography>
                  <Tooltip title="Directory where transcribed text files will be saved">
                    <InfoIcon color="action" fontSize="small" />
                  </Tooltip>
                </Box>
                
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <TextField
                    fullWidth
                    value={formValues.output_directory}
                    onChange={(e) => handleFieldChange('output_directory', e.target.value)}
                    error={!!directoryError}
                    helperText={directoryError || 'Choose where to save your transcribed files'}
                    placeholder="C:\Output\Transcripts"
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
                    onClick={handleBrowseDirectory}
                    disabled={isLoading || isBrowsing}
                    startIcon={isBrowsing ? <CircularProgress size={16} /> : <FolderOpenIcon />}
                    sx={{ minWidth: 120, height: 56 }}
                  >
                    {isBrowsing ? 'Browsing...' : 'Browse'}
                  </Button>
                </Box>
              </Paper>
            </Grid>

            {/* Whisper Model Section */}
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={1} 
                sx={{ 
                  p: 3, 
                  bgcolor: alpha(theme.palette.background.paper, 0.7),
                  border: `1px solid ${theme.palette.divider}`,
                  height: '100%'
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Typography variant="h6" fontWeight={500}>
                    Whisper Model
                  </Typography>
                  <Tooltip title="Choose the AI model for transcription. Larger models provide better accuracy but take longer to process.">
                    <InfoIcon color="action" fontSize="small" />
                  </Tooltip>
                </Box>
                
                <FormControl fullWidth>
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
                          <Typography variant="body1" fontWeight={500}>
                            {model.label}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {model.description}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Paper>
            </Grid>

            {/* Language Section */}
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={1} 
                sx={{ 
                  p: 3, 
                  bgcolor: alpha(theme.palette.background.paper, 0.7),
                  border: `1px solid ${theme.palette.divider}`,
                  height: '100%'
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Typography variant="h6" fontWeight={500}>
                    Language
                  </Typography>
                  <Tooltip title="Select the language for transcription processing">
                    <InfoIcon color="action" fontSize="small" />
                  </Tooltip>
                </Box>
                
                <FormControl fullWidth>
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
                          <Typography variant="body1" fontWeight={500}>
                            {language.label}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {language.description}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Paper>
            </Grid>

            {/* Output Format Section */}
            <Grid item xs={12}>
              <Paper 
                elevation={1} 
                sx={{ 
                  p: 3, 
                  bgcolor: alpha(theme.palette.background.paper, 0.7),
                  border: `1px solid ${theme.palette.divider}`
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Typography variant="h6" fontWeight={500}>
                    Output Format
                  </Typography>
                  <Tooltip title="Choose the format for the transcribed text output">
                    <InfoIcon color="action" fontSize="small" />
                  </Tooltip>
                </Box>
                
                <FormControl fullWidth>
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
                          <Typography variant="body1" fontWeight={500}>
                            {format.label}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
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
        </DialogContent>

        {/* Dialog Actions */}
        <DialogActions sx={{ p: 3, pt: 0 }}>
          <Box sx={{ display: 'flex', gap: 1, width: '100%', justifyContent: 'space-between' }}>
            {/* Reset Button */}
            <Button
              variant="outlined"
              color="warning"
              startIcon={<RestartAltIcon />}
              onClick={handleReset}
              disabled={isLoading}
              sx={{ minWidth: 120 }}
            >
              Reset to Defaults
            </Button>

            <Box sx={{ display: 'flex', gap: 1 }}>
              {/* Cancel Button */}
              <Button
                variant="outlined"
                onClick={handleCancel}
                disabled={isLoading}
                sx={{ minWidth: 100 }}
              >
                Cancel
              </Button>

              {/* Save Button */}
              <Button
                variant="contained"
                color="primary"
                startIcon={isLoading ? <CircularProgress size={16} color="inherit" /> : <SaveIcon />}
                onClick={handleSave}
                disabled={isLoading || !hasChanges || !!directoryError}
                sx={{ 
                  minWidth: 120,
                  background: theme.palette.gradient.primary,
                  '&:hover': {
                    background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
                  }
                }}
              >
                {isLoading ? 'Saving...' : 'Save Changes'}
              </Button>
            </Box>
          </Box>
        </DialogActions>
      </Dialog>

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
    </>
  )
}

export default SettingsDialog