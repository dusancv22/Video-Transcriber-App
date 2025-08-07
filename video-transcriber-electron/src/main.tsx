import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Import global type definitions (only in development)
if (process.env.NODE_ENV === 'development') {
  try {
    import('./types/electron.d')
  } catch (e) {
    // Ignore if file doesn't exist
  }
}

// Remove loading screen once React is ready
const removeLoadingScreen = () => {
  const loadingScreen = document.querySelector('.loading-screen')
  if (loadingScreen) {
    loadingScreen.remove()
  }
}

// Initialize React app
ReactDOM.createRoot(document.getElementById('root')!).render(
  <App />
)

// Remove loading screen after React has mounted
setTimeout(removeLoadingScreen, 100)