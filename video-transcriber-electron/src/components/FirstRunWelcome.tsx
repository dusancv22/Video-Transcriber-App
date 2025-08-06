import React, { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Button,
  Box,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material'
import {
  EmojiPeople as WelcomeIcon,
  Psychology as ModelIcon,
  FolderOpen as FolderIcon,
  Speed as SpeedIcon,
  Check as CheckIcon,
  ArrowForward as ArrowForwardIcon,
  Settings as SettingsIcon
} from '@mui/icons-material'
import { useTheme, alpha } from '@mui/material/styles'

interface FirstRunWelcomeProps {
  open: boolean
  onClose: () => void
  onOpenSettings: () => void
}

const FirstRunWelcome: React.FC<FirstRunWelcomeProps> = ({ 
  open, 
  onClose, 
  onOpenSettings 
}) => {
  const theme = useTheme()
  const [currentStep, setCurrentStep] = useState(0)

  const steps = [
    'Welcome',
    'Features',
    'Setup'
  ]

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      handleGetStarted()
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleGetStarted = () => {
    onClose()
    onOpenSettings()
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <WelcomeIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom fontWeight={600}>
              Welcome to Video Transcriber!
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 400, mx: 'auto' }}>
              Transform your video content into accurate text transcripts using advanced AI technology.
            </Typography>
            
            <Paper 
              elevation={1} 
              sx={{ 
                p: 2, 
                bgcolor: alpha(theme.palette.primary.main, 0.05),
                border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                mx: 'auto',
                maxWidth: 300
              }}
            >
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                Perfect for:
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Content creators & researchers<br/>
                • Meeting & interview transcription<br/>
                • Accessibility & documentation
              </Typography>
            </Paper>
          </Box>
        )

      case 1:
        return (
          <Box sx={{ py: 2 }}>
            <Typography variant="h5" gutterBottom fontWeight={600} textAlign="center" sx={{ mb: 3 }}>
              Powerful Features
            </Typography>
            
            <List sx={{ maxWidth: 500, mx: 'auto' }}>
              <ListItem>
                <ListItemIcon>
                  <ModelIcon sx={{ color: 'primary.main' }} />
                </ListItemIcon>
                <ListItemText 
                  primary="Advanced AI Models"
                  secondary="Choose from Base, Small, Medium, or Large Whisper models for optimal accuracy vs. speed balance"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <FolderIcon sx={{ color: 'success.main' }} />
                </ListItemIcon>
                <ListItemText 
                  primary="Batch Processing"
                  secondary="Process multiple video files at once with queue management and progress tracking"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <SpeedIcon sx={{ color: 'warning.main' }} />
                </ListItemIcon>
                <ListItemText 
                  primary="Multiple Output Formats"
                  secondary="Export as plain text (.txt), subtitles (.srt), or web captions (.vtt)"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <CheckIcon sx={{ color: 'info.main' }} />
                </ListItemIcon>
                <ListItemText 
                  primary="Smart File Handling"
                  secondary="Automatic large file splitting, format validation, and error recovery"
                />
              </ListItem>
            </List>
          </Box>
        )

      case 2:
        return (
          <Box sx={{ py: 2 }}>
            <Typography variant="h5" gutterBottom fontWeight={600} textAlign="center" sx={{ mb: 3 }}>
              Quick Setup
            </Typography>
            
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                Let's configure your settings to get you started with transcription!
              </Typography>
            </Alert>

            <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom fontWeight={500}>
                What you'll need to configure:
              </Typography>
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <FolderIcon sx={{ fontSize: 20, color: 'primary.main' }} />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Output Directory"
                    secondary="Where your transcribed files will be saved"
                  />
                </ListItem>
                
                <ListItem>
                  <ListItemIcon>
                    <ModelIcon sx={{ fontSize: 20, color: 'primary.main' }} />
                  </ListItemIcon>
                  <ListItemText 
                    primary="AI Model Selection"
                    secondary="Balance between accuracy and processing speed"
                  />
                </ListItem>
                
                <ListItem>
                  <ListItemIcon>
                    <SpeedIcon sx={{ fontSize: 20, color: 'primary.main' }} />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Output Format"
                    secondary="Choose your preferred transcript format"
                  />
                </ListItem>
              </List>
            </Paper>

            <Box 
              sx={{ 
                p: 2,
                bgcolor: alpha(theme.palette.success.main, 0.1),
                border: `1px solid ${alpha(theme.palette.success.main, 0.3)}`,
                borderRadius: 1,
                textAlign: 'center'
              }}
            >
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                💡 Recommended for first-time users:
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Large model for best accuracy • English language • Plain text format
              </Typography>
            </Box>
          </Box>
        )

      default:
        return null
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
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
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ width: '100%' }}>
          <Stepper activeStep={currentStep} alternativeLabel sx={{ mb: 2 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ px: 4, py: 2 }}>
        {renderStepContent()}
      </DialogContent>

      <Divider />

      <DialogActions sx={{ p: 3, justifyContent: 'space-between' }}>
        <Button 
          onClick={onClose} 
          color="inherit"
          sx={{ minWidth: 100 }}
        >
          Skip
        </Button>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          {currentStep > 0 && (
            <Button 
              onClick={handleBack}
              variant="outlined"
              sx={{ minWidth: 100 }}
            >
              Back
            </Button>
          )}
          
          <Button
            variant="contained"
            onClick={handleNext}
            startIcon={currentStep === steps.length - 1 ? <SettingsIcon /> : <ArrowForwardIcon />}
            sx={{ 
              minWidth: 140,
              background: theme.palette.gradient.primary
            }}
          >
            {currentStep === steps.length - 1 ? 'Configure Settings' : 'Next'}
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  )
}

export default FirstRunWelcome