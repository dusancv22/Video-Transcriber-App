import { createTheme, Theme, alpha } from '@mui/material/styles'

declare module '@mui/material/styles' {
  interface Palette {
    gradient: {
      primary: string
      secondary: string
      success: string
      error: string
    }
  }

  interface PaletteOptions {
    gradient?: {
      primary?: string
      secondary?: string
      success?: string
      error?: string
    }
  }

  interface TypeBackground {
    elevation1: string
    elevation2: string
    elevation3: string
  }
}

// Custom color palette inspired by modern design trends
const colors = {
  primary: {
    50: '#e3f2fd',
    100: '#bbdefb',
    200: '#90caf9',
    300: '#64b5f6',
    400: '#42a5f5',
    500: '#2196f3', // Main primary color
    600: '#1e88e5',
    700: '#1976d2',
    800: '#1565c0',
    900: '#0d47a1'
  },
  secondary: {
    50: '#f3e5f5',
    100: '#e1bee7',
    200: '#ce93d8',
    300: '#ba68c8',
    400: '#ab47bc',
    500: '#9c27b0', // Main secondary color
    600: '#8e24aa',
    700: '#7b1fa2',
    800: '#6a1b9a',
    900: '#4a148c'
  },
  success: {
    50: '#e8f5e8',
    100: '#c8e6c8',
    200: '#a5d6a5',
    300: '#81c784',
    400: '#66bb6a',
    500: '#4caf50', // Main success color
    600: '#43a047',
    700: '#388e3c',
    800: '#2e7d32',
    900: '#1b5e20'
  },
  error: {
    50: '#ffebee',
    100: '#ffcdd2',
    200: '#ef9a9a',
    300: '#e57373',
    400: '#ef5350',
    500: '#f44336', // Main error color
    600: '#e53935',
    700: '#d32f2f',
    800: '#c62828',
    900: '#b71c1c'
  },
  warning: {
    50: '#fff8e1',
    100: '#ffecb3',
    200: '#ffe082',
    300: '#ffd54f',
    400: '#ffca28',
    500: '#ffc107', // Main warning color
    600: '#ffb300',
    700: '#ffa000',
    800: '#ff8f00',
    900: '#ff6f00'
  },
  info: {
    50: '#e1f5fe',
    100: '#b3e5fc',
    200: '#81d4fa',
    300: '#4fc3f7',
    400: '#29b6f6',
    500: '#03a9f4', // Main info color
    600: '#039be5',
    700: '#0288d1',
    800: '#0277bd',
    900: '#01579b'
  },
  grey: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#eeeeee',
    300: '#e0e0e0',
    400: '#bdbdbd',
    500: '#9e9e9e',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121'
  }
}

// Create the base theme
const createCustomTheme = (mode: 'light' | 'dark'): Theme => {
  const isLight = mode === 'light'

  return createTheme({
    palette: {
      mode,
      primary: {
        ...colors.primary,
        main: colors.primary[500],
        contrastText: '#ffffff'
      },
      secondary: {
        ...colors.secondary,
        main: colors.secondary[500],
        contrastText: '#ffffff'
      },
      success: {
        ...colors.success,
        main: colors.success[500],
        contrastText: '#ffffff'
      },
      error: {
        ...colors.error,
        main: colors.error[500],
        contrastText: '#ffffff'
      },
      warning: {
        ...colors.warning,
        main: colors.warning[500],
        contrastText: '#ffffff'
      },
      info: {
        ...colors.info,
        main: colors.info[500],
        contrastText: '#ffffff'
      },
      grey: colors.grey,
      background: {
        default: isLight ? '#fafafa' : '#121212',
        paper: isLight ? '#ffffff' : '#1e1e1e',
        elevation1: isLight ? '#ffffff' : '#1e1e1e',
        elevation2: isLight ? '#f5f5f5' : '#2d2d2d',
        elevation3: isLight ? '#eeeeee' : '#3c3c3c'
      },
      text: {
        primary: isLight ? colors.grey[900] : '#ffffff',
        secondary: isLight ? colors.grey[700] : colors.grey[400],
        disabled: isLight ? colors.grey[500] : colors.grey[600]
      },
      divider: isLight ? alpha(colors.grey[900], 0.12) : alpha('#ffffff', 0.12),
      gradient: {
        primary: `linear-gradient(135deg, ${colors.primary[500]} 0%, ${colors.primary[700]} 100%)`,
        secondary: `linear-gradient(135deg, ${colors.secondary[500]} 0%, ${colors.secondary[700]} 100%)`,
        success: `linear-gradient(135deg, ${colors.success[500]} 0%, ${colors.success[700]} 100%)`,
        error: `linear-gradient(135deg, ${colors.error[500]} 0%, ${colors.error[700]} 100%)`
      }
    },
    typography: {
      fontFamily: [
        '-apple-system',
        'BlinkMacSystemFont',
        '"Segoe UI"',
        'Roboto',
        '"Helvetica Neue"',
        'Arial',
        'sans-serif',
        '"Apple Color Emoji"',
        '"Segoe UI Emoji"',
        '"Segoe UI Symbol"'
      ].join(','),
      h1: {
        fontSize: '2.5rem',
        fontWeight: 700,
        lineHeight: 1.2
      },
      h2: {
        fontSize: '2rem',
        fontWeight: 600,
        lineHeight: 1.3
      },
      h3: {
        fontSize: '1.75rem',
        fontWeight: 600,
        lineHeight: 1.4
      },
      h4: {
        fontSize: '1.5rem',
        fontWeight: 500,
        lineHeight: 1.4
      },
      h5: {
        fontSize: '1.25rem',
        fontWeight: 500,
        lineHeight: 1.5
      },
      h6: {
        fontSize: '1rem',
        fontWeight: 500,
        lineHeight: 1.5
      },
      body1: {
        fontSize: '1rem',
        fontWeight: 400,
        lineHeight: 1.6
      },
      body2: {
        fontSize: '0.875rem',
        fontWeight: 400,
        lineHeight: 1.6
      },
      button: {
        fontWeight: 500,
        textTransform: 'none' // Disable uppercase transformation
      },
      caption: {
        fontSize: '0.75rem',
        fontWeight: 400,
        lineHeight: 1.5
      }
    },
    shape: {
      borderRadius: 8
    },
    spacing: 8,
    components: {
      // Button component overrides
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: 8,
            fontWeight: 500,
            padding: '8px 16px',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-1px)',
              boxShadow: '0 4px 8px rgba(0, 0, 0, 0.12)'
            }
          },
          contained: {
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
            '&:hover': {
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
            }
          }
        }
      },
      
      // Paper component overrides
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            border: `1px solid ${isLight ? colors.grey[200] : alpha('#ffffff', 0.1)}`
          },
          elevation1: {
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1)'
          },
          elevation2: {
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05), 0 2px 4px rgba(0, 0, 0, 0.1)'
          },
          elevation3: {
            boxShadow: '0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)'
          }
        }
      },
      
      // Card component overrides
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            border: `1px solid ${isLight ? colors.grey[200] : alpha('#ffffff', 0.1)}`,
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: '0 8px 25px rgba(0, 0, 0, 0.1)'
            }
          }
        }
      },
      
      // TextField component overrides
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 8,
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                transform: 'translateY(-1px)'
              }
            }
          }
        }
      },
      
      // LinearProgress component overrides
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            borderRadius: 4,
            height: 6,
            backgroundColor: isLight ? colors.grey[200] : colors.grey[800]
          },
          bar: {
            borderRadius: 4
          }
        }
      },
      
      // AppBar component overrides
      MuiAppBar: {
        styleOverrides: {
          root: {
            borderRadius: 0,
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            borderBottom: `1px solid ${isLight ? colors.grey[200] : alpha('#ffffff', 0.1)}`
          }
        }
      },
      
      // Drawer component overrides
      MuiDrawer: {
        styleOverrides: {
          paper: {
            borderRadius: 0,
            borderRight: `1px solid ${isLight ? colors.grey[200] : alpha('#ffffff', 0.1)}`
          }
        }
      },
      
      // List component overrides
      MuiListItemButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            margin: '2px 8px',
            '&:hover': {
              backgroundColor: alpha(colors.primary[500], 0.08),
              transform: 'translateX(4px)'
            },
            '&.Mui-selected': {
              backgroundColor: alpha(colors.primary[500], 0.12),
              '&:hover': {
                backgroundColor: alpha(colors.primary[500], 0.16)
              }
            }
          }
        }
      },
      
      // Chip component overrides
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            fontWeight: 500
          }
        }
      },
      
      // Dialog component overrides
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: 16
          }
        }
      },
      
      // Menu component overrides
      MuiMenu: {
        styleOverrides: {
          paper: {
            borderRadius: 8,
            border: `1px solid ${isLight ? colors.grey[200] : alpha('#ffffff', 0.1)}`,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
          }
        }
      }
    }
  })
}

// Export light and dark themes
export const lightTheme = createCustomTheme('light')
export const darkTheme = createCustomTheme('dark')

// Custom theme utilities
export const getTheme = (mode: 'light' | 'dark') => mode === 'light' ? lightTheme : darkTheme

// Custom styling utilities
export const customStyles = {
  gradientButton: (theme: Theme) => ({
    background: theme.palette.gradient.primary,
    color: theme.palette.common.white,
    border: 'none',
    '&:hover': {
      background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
      transform: 'translateY(-1px)',
      boxShadow: '0 6px 16px rgba(33, 150, 243, 0.3)'
    }
  }),
  
  glassmorphism: (theme: Theme) => ({
    background: alpha(theme.palette.background.paper, 0.8),
    backdropFilter: 'blur(10px)',
    border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
    borderRadius: theme.shape.borderRadius * 2
  }),
  
  elevation: (theme: Theme, level: 1 | 2 | 3) => ({
    backgroundColor: theme.palette.background[`elevation${level}` as keyof typeof theme.palette.background],
    boxShadow: theme.shadows[level * 2],
    border: `1px solid ${theme.palette.divider}`
  })
}