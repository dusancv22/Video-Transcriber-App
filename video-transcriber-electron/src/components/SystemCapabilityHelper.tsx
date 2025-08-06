import React from 'react'
import { 
  Box, 
  Chip, 
  Tooltip, 
  Typography 
} from '@mui/material'
import {
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Computer as ComputerIcon
} from '@mui/icons-material'

// System capability detection utility
export const detectSystemCapabilities = () => {
  // Basic system detection (in a real app, this would query actual system info)
  const hasGPU = navigator.hardwareConcurrency > 8 // Rough heuristic
  const hasHighMemory = navigator.deviceMemory ? navigator.deviceMemory > 4 : true
  
  return {
    hasGPU,
    hasHighMemory,
    cpuCores: navigator.hardwareConcurrency || 4,
    recommendedModel: getRecommendedModel(hasGPU, hasHighMemory)
  }
}

const getRecommendedModel = (hasGPU: boolean, hasHighMemory: boolean): 'base' | 'small' | 'medium' | 'large' => {
  if (hasGPU && hasHighMemory) {
    return 'large'  // Best performance with GPU acceleration
  } else if (hasHighMemory) {
    return 'medium'  // Good balance for high-memory systems
  } else {
    return 'small'   // Conservative choice for limited systems
  }
}

interface SystemCapabilityIndicatorProps {
  currentModel: 'base' | 'small' | 'medium' | 'large'
}

export const SystemCapabilityIndicator: React.FC<SystemCapabilityIndicatorProps> = ({ 
  currentModel 
}) => {
  const capabilities = detectSystemCapabilities()
  const isOptimal = currentModel === capabilities.recommendedModel
  const isOverspec = ['large', 'medium', 'small', 'base'].indexOf(currentModel) > 
                    ['large', 'medium', 'small', 'base'].indexOf(capabilities.recommendedModel)

  return (
    <Box sx={{ mt: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <ComputerIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
        <Typography variant="caption" color="text.secondary">
          System Compatibility
        </Typography>
      </Box>
      
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Tooltip title={`Detected ${capabilities.cpuCores} CPU cores`}>
          <Chip
            size="small"
            icon={<SpeedIcon />}
            label={`${capabilities.cpuCores} cores`}
            variant="outlined"
            color="default"
            sx={{ fontSize: '0.65rem' }}
          />
        </Tooltip>
        
        {capabilities.hasHighMemory && (
          <Tooltip title="High memory system detected">
            <Chip
              size="small"
              icon={<MemoryIcon />}
              label="High RAM"
              variant="outlined"
              color="success"
              sx={{ fontSize: '0.65rem' }}
            />
          </Tooltip>
        )}
        
        {isOptimal && (
          <Tooltip title="This model is optimized for your system">
            <Chip
              size="small"
              label="✓ Optimal"
              color="success"
              sx={{ fontSize: '0.65rem' }}
            />
          </Tooltip>
        )}
        
        {isOverspec && (
          <Tooltip title="This model may be slower than optimal for your system">
            <Chip
              size="small"
              label="⚠ May be slow"
              color="warning"
              sx={{ fontSize: '0.65rem' }}
            />
          </Tooltip>
        )}
      </Box>
      
      {!isOptimal && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
          Recommended: <strong>{capabilities.recommendedModel}</strong> model for your system
        </Typography>
      )}
    </Box>
  )
}