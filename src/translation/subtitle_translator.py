"""
Main subtitle translator that orchestrates translation of subtitle files.
Preserves all timestamps while translating text content.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import pysubs2
import json
import re

from .engines.helsinki_translator import HelsinkiTranslator

logger = logging.getLogger(__name__)

# Try to import TowerTranslator (GPU-only)
try:
    from .engines.tower_translator import TowerTranslator
    TOWER_AVAILABLE = True
except ImportError:
    TOWER_AVAILABLE = False
    logger.info("TowerTranslator not available (missing dependencies)")


class SubtitleTranslator:
    """
    Orchestrates subtitle translation while preserving timestamps.
    Works with SRT, VTT, ASS, and other subtitle formats.
    """
    
    def __init__(
        self, 
        source_lang: str = "auto", 
        target_lang: str = "en",
        use_context: bool = True,
        context_window: int = 3,
        prefer_tower: bool = True
    ):
        """
        Initialize the subtitle translator.
        
        Args:
            source_lang: Source language code or "auto" for detection
            target_lang: Target language code
            use_context: Whether to use surrounding segments for context
            context_window: Number of segments to use as context
            prefer_tower: Whether to prefer TowerInstruct for PT->EN (GPU required)
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.use_context = use_context
        self.context_window = context_window
        self.prefer_tower = prefer_tower
        self.translator = None
        self.using_tower = False  # Track which engine is active
        
        # Initialize translator if source language is specified
        if source_lang != "auto":
            self._initialize_translator(source_lang, target_lang)
    
    def _initialize_translator(self, source_lang: str, target_lang: str):
        """Initialize the translation engine with smart selection for PT->EN."""
        print(f"DEBUG: _initialize_translator called with {source_lang} -> {target_lang}", flush=True)
        
        # Check if this is Portuguese to English translation
        # TowerInstruct disabled - too slow for practical use (takes 10+ minutes for 87 segments)
        if False and source_lang == 'pt' and target_lang == 'en' and self.prefer_tower and TOWER_AVAILABLE:
            # Try TowerInstruct first for PT->EN
            try:
                logger.info(f"Attempting to use TowerInstruct (GPU) for PT->EN translation")
                print(f"Checking GPU availability for advanced PT->EN translation...", flush=True)
                
                # Check GPU requirements first
                gpu_info = TowerTranslator.check_gpu_requirements()
                print(f"GPU Status: {gpu_info['message']}", flush=True)
                
                if gpu_info['meets_requirements']:
                    print(f"Initializing TowerInstruct on {gpu_info['gpu_name']}...", flush=True)
                    self.translator = TowerTranslator()
                    self.using_tower = True
                    self.source_lang = source_lang
                    self.target_lang = target_lang
                    logger.info("Successfully initialized TowerInstruct for PT->EN")
                    print(f"[OK] Using advanced TowerInstruct translation (GPU accelerated)", flush=True)
                    return
                else:
                    print(f"GPU requirements not met: {gpu_info['message']}", flush=True)
                    print(f"Falling back to standard translation (CPU)", flush=True)
                    
            except RuntimeError as e:
                logger.info(f"TowerInstruct not available: {e}")
                print(f"TowerInstruct unavailable: {e}", flush=True)
                print(f"Using standard translation instead", flush=True)
            except Exception as e:
                logger.error(f"Unexpected error initializing TowerInstruct: {e}")
                print(f"Error with TowerInstruct: {e}", flush=True)
        
        # Fall back to Helsinki translator for all other cases
        try:
            logger.info(f"Initializing Helsinki translator: {source_lang} -> {target_lang}")
            print(f"Initializing standard translator ({source_lang} -> {target_lang})...", flush=True)
            self.translator = HelsinkiTranslator(source_lang, target_lang)
            self.using_tower = False
            self.source_lang = source_lang
            self.target_lang = target_lang
            print(f"[OK] Standard translator ready", flush=True)
        except Exception as e:
            error_msg = f"Failed to initialize translator for {source_lang} -> {target_lang}: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}", flush=True)
            raise RuntimeError(error_msg)
    
    def translate_subtitle_file(
        self, 
        subtitle_path: Path,
        output_path: Optional[Path] = None,
        preserve_original: bool = True
    ) -> Path:
        """
        Translate a subtitle file preserving all timestamps.
        
        Args:
            subtitle_path: Path to the subtitle file to translate
            output_path: Optional output path (auto-generated if not provided)
            preserve_original: Whether to keep original file
            
        Returns:
            Path to the translated subtitle file
        """
        print(f"DEBUG: translate_subtitle_file() ENTERED", flush=True)
        print(f"DEBUG: subtitle_path type = {type(subtitle_path)}", flush=True)
        print(f"DEBUG: subtitle_path = {subtitle_path}", flush=True)
        print(f"DEBUG: Translator state: source={self.source_lang}, target={self.target_lang}", flush=True)
        print(f"DEBUG: self.translator = {self.translator}", flush=True)
        
        subtitle_path = Path(subtitle_path)
        print(f"DEBUG: After Path conversion: {subtitle_path}", flush=True)
        
        if not subtitle_path.exists():
            print(f"DEBUG: File does not exist: {subtitle_path}", flush=True)
            raise FileNotFoundError(f"Subtitle file not found: {subtitle_path}")
        
        logger.info(f"Translating subtitle file: {subtitle_path}")
        print(f"DEBUG: About to parse subtitle file", flush=True)
        
        # Parse the subtitle file
        segments = self.parse_subtitle_file(subtitle_path)
        print(f"DEBUG: Parsed {len(segments) if segments else 0} segments", flush=True)
        
        if not segments:
            raise ValueError(f"No subtitles found in file: {subtitle_path}")
        
        # Auto-detect language if needed
        if self.source_lang == "auto":
            print(f"DEBUG: Auto-detecting language...", flush=True)
            detected_lang = self._detect_language(segments)
            print(f"DEBUG: Detected language: {detected_lang}", flush=True)
            if detected_lang:
                logger.info(f"Detected source language: {detected_lang}")
                print(f"DEBUG: Initializing translator for {detected_lang} -> {self.target_lang}", flush=True)
                self._initialize_translator(detected_lang, self.target_lang)
                print(f"DEBUG: Translator initialized", flush=True)
            else:
                raise RuntimeError("Could not detect source language")
        
        # Translate segments
        print(f"DEBUG: Starting segment translation...", flush=True)
        translated_segments = self.translate_segments(segments)
        print(f"DEBUG: Translated {len(translated_segments)} segments", flush=True)
        
        # Generate output path if not provided
        if output_path is None:
            output_path = self._generate_output_path(subtitle_path)
        
        # Create translated subtitle file
        self.create_translated_subtitle(
            translated_segments,
            subtitle_path,
            output_path
        )
        
        logger.info(f"Translation complete. Output: {output_path}")
        return output_path
    
    def parse_subtitle_file(self, subtitle_path: Path) -> List[Dict]:
        """
        Parse a subtitle file into segments.
        
        Args:
            subtitle_path: Path to subtitle file
            
        Returns:
            List of segments with text, start, end times
        """
        try:
            # Use pysubs2 to parse various subtitle formats
            subs = pysubs2.load(str(subtitle_path))
            
            segments = []
            for i, event in enumerate(subs.events):
                segment = {
                    'id': i,
                    'start': event.start / 1000.0,  # Convert to seconds
                    'end': event.end / 1000.0,
                    'text': event.text.replace('\\N', '\n').strip(),  # Handle line breaks
                    'style': event.style if hasattr(event, 'style') else None
                }
                segments.append(segment)
            
            logger.info(f"Parsed {len(segments)} segments from {subtitle_path}")
            return segments
            
        except Exception as e:
            logger.error(f"Failed to parse subtitle file: {e}")
            raise RuntimeError(f"Failed to parse subtitle file: {e}")
    
    def translate_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Translate subtitle segments.
        
        Args:
            segments: List of parsed subtitle segments
            
        Returns:
            List of segments with translated text
        """
        print(f"DEBUG: translate_segments called with {len(segments)} segments", flush=True)
        print(f"DEBUG: Using {'TowerInstruct (GPU)' if self.using_tower else 'Helsinki'} translator", flush=True)
        
        if not self.translator:
            print(f"DEBUG: ERROR - Translator not initialized!", flush=True)
            raise RuntimeError("Translator not initialized")
        
        logger.info(f"Translating {len(segments)} segments with {'TowerInstruct' if self.using_tower else 'Helsinki'}...")
        
        # Use appropriate method based on the engine
        if self.using_tower:
            # TowerInstruct has its own context method optimized for GPU
            if self.use_context:
                return self.translator.translate_with_context(segments, context_window=2)  # Smaller window for GPU
            else:
                return self.translator.translate_segments(segments)
        else:
            # Helsinki translator with sliding context window
            if self.use_context:
                return self.translator.translate_with_sliding_context(segments, self.context_window)
            else:
                return self.translator.translate_segments(segments)
    
    def create_translated_subtitle(
        self,
        translated_segments: List[Dict],
        original_path: Path,
        output_path: Path
    ):
        """
        Create a translated subtitle file with preserved timestamps.
        
        Args:
            translated_segments: Segments with translated text
            original_path: Path to original subtitle (for format detection)
            output_path: Path for output file
        """
        try:
            # Detect format from original file
            original_ext = original_path.suffix.lower()
            
            # Create new subtitle file
            subs = pysubs2.SSAFile()
            
            for segment in translated_segments:
                # Use translated text if available, otherwise keep original
                text = segment.get('translated_text', segment.get('text', ''))
                
                # Convert line breaks back to subtitle format
                text = text.replace('\n', '\\N')
                
                event = pysubs2.SSAEvent(
                    start=int(segment['start'] * 1000),  # Convert to milliseconds
                    end=int(segment['end'] * 1000),
                    text=text
                )
                
                # Preserve style if available
                if segment.get('style'):
                    event.style = segment['style']
                
                subs.events.append(event)
            
            # Save in the same format as original
            if original_ext == '.srt':
                subs.save(str(output_path), format_='srt')
            elif original_ext == '.vtt':
                subs.save(str(output_path), format_='vtt')
            elif original_ext == '.ass' or original_ext == '.ssa':
                subs.save(str(output_path), format_='ass')
            else:
                # Default to SRT if unknown
                subs.save(str(output_path), format_='srt')
            
            logger.info(f"Created translated subtitle: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to create translated subtitle: {e}")
            raise RuntimeError(f"Failed to create translated subtitle: {e}")
    
    def translate_from_segments_data(
        self,
        segments: List[Dict],
        output_path: Path,
        subtitle_format: str = 'srt'
    ) -> Path:
        """
        Translate segments data directly (from transcription pipeline).
        
        This method is used when translating during subtitle generation,
        not from existing subtitle files.
        
        Args:
            segments: List of segments from transcription
            output_path: Base output path (without extension)
            subtitle_format: Format for output subtitle
            
        Returns:
            Path to translated subtitle file
        """
        # Auto-detect language if needed
        if self.source_lang == "auto":
            detected_lang = self._detect_language(segments)
            if detected_lang:
                logger.info(f"Detected source language: {detected_lang}")
                self._initialize_translator(detected_lang, self.target_lang)
            else:
                # Default to Spanish if detection fails (common use case)
                logger.warning("Could not detect language, defaulting to Spanish")
                self._initialize_translator('es', self.target_lang)
        elif not self.translator:
            self._initialize_translator(self.source_lang, self.target_lang)
        
        # Translate the segments
        translated_segments = self.translate_segments(segments)
        
        # Create subtitle file with translated text
        output_file = output_path.with_suffix(f'.{self.target_lang}.{subtitle_format}')
        
        # Create subtitle file
        subs = pysubs2.SSAFile()
        
        for segment in translated_segments:
            text = segment.get('translated_text', segment.get('text', ''))
            
            # Handle multi-line subtitles
            if '\n' not in text and len(text) > 42:
                # Split long lines
                words = text.split()
                mid = len(words) // 2
                text = ' '.join(words[:mid]) + '\\N' + ' '.join(words[mid:])
            else:
                text = text.replace('\n', '\\N')
            
            event = pysubs2.SSAEvent(
                start=int(segment['start'] * 1000),
                end=int(segment['end'] * 1000),
                text=text
            )
            subs.events.append(event)
        
        # Save in requested format
        if subtitle_format == 'srt':
            subs.save(str(output_file), format_='srt')
        elif subtitle_format == 'vtt':
            subs.save(str(output_file), format_='vtt')
        elif subtitle_format == 'ass':
            subs.save(str(output_file), format_='ass')
        else:
            subs.save(str(output_file))
        
        logger.info(f"Created translated subtitle: {output_file}")
        return output_file
    
    def _detect_language(self, segments: List[Dict]) -> Optional[str]:
        """
        Detect the language of subtitle segments.
        
        Args:
            segments: List of subtitle segments
            
        Returns:
            Detected language code or None
        """
        try:
            # Try to import langdetect
            from langdetect import detect
            
            # Combine some text for detection
            sample_text = ' '.join([seg.get('text', '') for seg in segments[:10]])
            
            if sample_text:
                detected = detect(sample_text)
                logger.info(f"Detected language: {detected}")
                return detected
                
        except ImportError:
            logger.warning("langdetect not installed, cannot auto-detect language")
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
        
        return None
    
    def _generate_output_path(self, input_path: Path) -> Path:
        """
        Generate output path for translated subtitle.
        
        Args:
            input_path: Original subtitle path
            
        Returns:
            Generated output path
        """
        # Add target language code to filename
        stem = input_path.stem
        suffix = input_path.suffix
        
        # Remove existing language codes if present
        # Common patterns: file.en.srt, file_en.srt
        stem = re.sub(r'[._]([a-z]{2})$', '', stem, flags=re.IGNORECASE)
        
        # Add target language
        output_name = f"{stem}.{self.target_lang}{suffix}"
        output_path = input_path.parent / output_name
        
        return output_path
    
    def get_supported_languages(self) -> Dict:
        """Get list of supported language pairs."""
        return HelsinkiTranslator.get_supported_languages()
    
    def cleanup(self):
        """Clean up resources."""
        if self.translator:
            self.translator.cleanup()
            self.translator = None
            self.using_tower = False
    
    def get_translator_info(self) -> Dict[str, any]:
        """
        Get information about the current translator.
        
        Returns:
            Dictionary with translator information
        """
        info = {
            'source_lang': self.source_lang,
            'target_lang': self.target_lang,
            'engine': 'TowerInstruct (GPU)' if self.using_tower else 'Helsinki (CPU)',
            'using_tower': self.using_tower,
            'context_enabled': self.use_context,
            'context_window': self.context_window
        }
        
        # Add GPU info if TowerInstruct is available
        if TOWER_AVAILABLE:
            gpu_info = TowerTranslator.check_gpu_requirements()
            info['gpu_status'] = gpu_info
        else:
            info['gpu_status'] = {'gpu_available': False, 'message': 'TowerInstruct not installed'}
        
        return info