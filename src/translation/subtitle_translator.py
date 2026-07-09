"""
Main subtitle translator that orchestrates translation of subtitle files.
Preserves all timestamps while translating text content.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import pysubs2
import re

from .engines.helsinki_translator import HelsinkiTranslator
from src.post_processing.text_processor import TextProcessor

logger = logging.getLogger(__name__)


class SubtitleTranslator:
    """
    Orchestrates subtitle translation while preserving timestamps.
    Works with SRT, VTT, ASS, and other subtitle formats.
    """

    def __init__(
        self,
        source_lang: str = "auto",
        target_lang: str = "en"
    ):
        """
        Initialize the subtitle translator.

        Args:
            source_lang: Source language code or "auto" for detection
            target_lang: Target language code
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = None

        # Initialize translator if source language is specified
        if source_lang != "auto":
            self._initialize_translator(source_lang, target_lang)

    def _initialize_translator(self, source_lang: str, target_lang: str):
        """Initialize the Helsinki translation engine."""
        try:
            logger.info(f"Initializing Helsinki translator: {source_lang} -> {target_lang}")
            print(f"Initializing translator ({source_lang} -> {target_lang})...", flush=True)
            self.translator = HelsinkiTranslator(source_lang, target_lang)
            self.source_lang = source_lang
            self.target_lang = target_lang
            print(f"[OK] Translator ready", flush=True)
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

        # Per-segment translation (batched internally): every subtitle gets
        # exactly its own translation - no window/extraction heuristics.
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
            # Load the ORIGINAL file and replace only the event texts. This
            # preserves everything else - style definitions, script info,
            # positioning - which matters for ASS/SSA output (previously a
            # fresh file was built that referenced style names without their
            # definitions).
            subs = pysubs2.load(str(original_path))

            translated_by_id = {
                segment['id']: segment for segment in translated_segments
                if 'id' in segment
            }

            kept_events = []
            dropped = 0
            for i, event in enumerate(subs.events):
                segment = translated_by_id.get(i)
                if segment is not None:
                    # Use translated text if available, otherwise keep original
                    text = segment.get('translated_text') or segment.get('text', '')

                    # The translation model can hallucinate repetition walls
                    # ("whoa, whoa, whoa..." x40) from degenerate inputs. Drop
                    # cues whose source OR translation is degenerate;
                    # timestamps of the rest are absolute so no re-sync needed.
                    duration = (event.end - event.start) / 1000.0
                    source_text = segment.get('text', '')
                    if (TextProcessor.is_degenerate_subtitle_text(text, duration=duration)
                            or TextProcessor.is_degenerate_subtitle_text(source_text, duration=duration)):
                        dropped += 1
                        continue

                    # Collapse any milder repetition that slipped through
                    text = TextProcessor.collapse_repetitions(text)
                    # Convert line breaks back to subtitle escape format
                    event.text = text.replace('\n', '\\N')
                kept_events.append(event)

            if dropped:
                logger.info(f"Dropped {dropped} hallucinated translated cues")
                print(f"Removed {dropped} hallucinated subtitle cues during translation")
            subs.events = kept_events

            # Save in the same format as original
            original_ext = original_path.suffix.lower()
            if original_ext == '.vtt':
                subs.save(str(output_path), encoding='utf-8-sig', format_='vtt')
            elif original_ext in ('.ass', '.ssa'):
                subs.save(str(output_path), encoding='utf-8-sig', format_='ass')
            else:
                # SRT and anything unknown
                subs.save(str(output_path), encoding='utf-8-sig', format_='srt')

            logger.info(f"Created translated subtitle: {output_path}")

        except Exception as e:
            logger.error(f"Failed to create translated subtitle: {e}")
            raise RuntimeError(f"Failed to create translated subtitle: {e}")
    
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

    def get_translator_info(self) -> Dict[str, any]:
        """
        Get information about the current translator.

        Returns:
            Dictionary with translator information
        """
        return {
            'source_lang': self.source_lang,
            'target_lang': self.target_lang,
            'engine': 'Helsinki (CPU)',
            'mode': 'per-segment (batched)'
        }