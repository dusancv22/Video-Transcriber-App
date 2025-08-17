"""
Settings management for Video Transcriber App
Handles user preferences and model configuration
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Settings:
    """Manages application settings and configuration"""
    
    DEFAULT_SETTINGS = {
        'whisper_model_path': None,  # None means use default location
        'whisper_model_size': 'large',
        'use_advanced_processing': True,
        'remove_filler_words': True,
        'output_directory': None,
        'gpu_enabled': True,
        'custom_model_folder': None,  # For loading models from custom location
    }
    
    def __init__(self):
        """Initialize settings manager"""
        # Determine settings file location
        self.settings_dir = Path.home() / '.video_transcriber'
        self.settings_file = self.settings_dir / 'settings.json'
        
        # Create directory if it doesn't exist
        self.settings_dir.mkdir(exist_ok=True)
        
        # Load settings
        self.settings = self.load_settings()
        
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or create default"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to handle new settings
                    settings = self.DEFAULT_SETTINGS.copy()
                    settings.update(loaded_settings)
                    logger.info(f"Settings loaded from {self.settings_file}")
                    return settings
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                return self.DEFAULT_SETTINGS.copy()
        else:
            logger.info("No settings file found, using defaults")
            return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self) -> bool:
        """Save current settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            logger.info(f"Settings saved to {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value and save"""
        self.settings[key] = value
        self.save_settings()
    
    def get_whisper_model_path(self) -> Optional[Path]:
        """Get the path to the Whisper model file"""
        custom_folder = self.settings.get('custom_model_folder')
        model_size = self.settings.get('whisper_model_size', 'large')
        
        if custom_folder and Path(custom_folder).exists():
            # Look for model in custom folder
            custom_path = Path(custom_folder)
            
            # Try different naming conventions
            possible_names = [
                f"{model_size}.pt",
                f"{model_size}-v1.pt",
                f"{model_size}-v2.pt", 
                f"{model_size}-v3.pt",
                f"whisper-{model_size}.pt",
            ]
            
            for name in possible_names:
                model_file = custom_path / name
                if model_file.exists():
                    logger.info(f"Found model at: {model_file}")
                    return model_file
        
        # Check default Whisper cache location
        default_cache = Path.home() / '.cache' / 'whisper'
        if default_cache.exists():
            # Look for model in default location
            possible_names = [
                f"{model_size}.pt",
                f"{model_size}-v1.pt",
                f"{model_size}-v2.pt",
                f"{model_size}-v3.pt",
            ]
            
            for name in possible_names:
                model_file = default_cache / name
                if model_file.exists():
                    logger.info(f"Found model at default location: {model_file}")
                    return model_file
        
        # Check app's local models folder (for bundled distributions)
        app_models_dir = Path(__file__).parent.parent.parent / 'models'
        if app_models_dir.exists():
            possible_names = [
                f"{model_size}.pt",
                f"{model_size}-v1.pt",
                f"{model_size}-v2.pt",
                f"{model_size}-v3.pt",
            ]
            
            for name in possible_names:
                model_file = app_models_dir / name
                if model_file.exists():
                    logger.info(f"Found bundled model at: {model_file}")
                    return model_file
        
        # No local model found
        logger.info(f"No local model found for size: {model_size}")
        return None
    
    def detect_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Detect all available Whisper models on the system"""
        models = {}
        model_sizes = ['tiny', 'base', 'small', 'medium', 'large']
        
        # Check custom folder
        custom_folder = self.settings.get('custom_model_folder')
        if custom_folder and Path(custom_folder).exists():
            models.update(self._scan_folder_for_models(Path(custom_folder), "Custom"))
        
        # Check default cache
        default_cache = Path.home() / '.cache' / 'whisper'
        if default_cache.exists():
            models.update(self._scan_folder_for_models(default_cache, "Default"))
        
        # Check app models folder
        app_models_dir = Path(__file__).parent.parent.parent / 'models'
        if app_models_dir.exists():
            models.update(self._scan_folder_for_models(app_models_dir, "Bundled"))
        
        return models
    
    def _scan_folder_for_models(self, folder: Path, source: str) -> Dict[str, Dict[str, Any]]:
        """Scan a folder for Whisper model files"""
        models = {}
        model_patterns = ['tiny', 'base', 'small', 'medium', 'large']
        
        for file in folder.glob('*.pt'):
            # Check if filename contains a model size
            for size in model_patterns:
                if size in file.name.lower():
                    file_size_mb = file.stat().st_size / (1024 * 1024)
                    models[size] = {
                        'path': str(file),
                        'size_mb': round(file_size_mb, 1),
                        'source': source,
                        'filename': file.name
                    }
                    break
        
        return models
    
    def get_model_info(self, model_size: str) -> Dict[str, Any]:
        """Get information about a specific model size"""
        # Model size estimates and relative speeds
        model_info = {
            'tiny': {'params': '39M', 'speed': 'Very Fast', 'quality': 'Basic'},
            'base': {'params': '74M', 'speed': 'Fast', 'quality': 'Good'},
            'small': {'params': '244M', 'speed': 'Moderate', 'quality': 'Better'},
            'medium': {'params': '769M', 'speed': 'Slow', 'quality': 'Very Good'},
            'large': {'params': '1550M', 'speed': 'Very Slow', 'quality': 'Best'},
        }
        
        return model_info.get(model_size, {})