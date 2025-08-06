import React from 'react'
import { ThemeProvider, CssBaseline } from '@mui/material'
import { Box } from '@mui/material'
import { lightTheme } from './theme/theme'
import MainWindow from './components/MainWindow'

function App() {
  return (
    <ThemeProvider theme={lightTheme}>
      <CssBaseline />
      <Box 
        sx={{ 
          width: '100vw', 
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
      >
        <MainWindow />
      </Box>
    </ThemeProvider>
  )
}

export default App