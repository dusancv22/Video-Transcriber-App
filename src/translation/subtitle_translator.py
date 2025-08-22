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
        context_window: int = 3
    ):
        """
        Initialize the subtitle translator.
        
        Args:
            source_lang: Source language code or "auto" for detection
            target_lang: Target language code
            use_context: Whether to use surrounding segments for context
            context_window: Number of segments to use as context
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.use_context = use_context
        self.context_window = context_window
        self.translator = None
        
        # Initialize translator if source language is specified
        if source_lang != "auto":
            self._initialize_translator(source_lang, target_lang)
    
    def _initialize_translator(self, source_lang: str, target_lang: str):
        """Initialize the translation engine."""
        try:
            logger.info(f"Initializing translator: {source_lang} -> {target_lang}")
            self.translator = HelsinkiTranslator(source_lang, target_lang)
            self.source_lang = source_lang
            self.target_lang = target_lang
        except Exception as e:
            error_msg = f"Failed to initialize translator for {source_lang} -> {target_lang}: {e}"
            logger.error(error_msg)
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
        subtitle_path = Path(subtitle_path)
        
        if not subtitle_path.exists():
            raise FileNotFoundError(f"Subtitle file not found: {subtitle_path}")
        
        logger.info(f"Translating subtitle file: {subtitle_path}")
        
        # Parse the subtitle file
        segments = self.parse_subtitle_file(subtitle_path)
        
        if not segments:
            raise ValueError(f"No subtitles found in file: {subtitle_path}")
        
        # Auto-detect language if needed
        if self.source_lang == "auto":
            detected_lang = self._detect_language(segments)
            if detected_lang:
                logger.info(f"Detected source language: {detected_lang}")
                self._initialize_translator(detected_lang, self.target_lang)
            else:
                raise RuntimeError("Could not detect source language")
        
        # Translate segments
        translated_segments = self.translate_segments(segments)
        
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
        if not self.translator:
            raise RuntimeError("Translator not initialized")
        
        logger.info(f"Translating {len(segments)} segments...")
        
        # Use context-aware translation if enabled
        if self.use_context:
            return self.translator.translate_with_context(segments, self.context_window)
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