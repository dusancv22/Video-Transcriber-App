"""
Language detection utility for automatic source language identification.
"""

import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class LanguageDetector:
    """
    Detects the language of text using various methods.
    """
    
    # Common language codes and their names
    LANGUAGE_CODES = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'nl': 'Dutch',
        'pl': 'Polish',
        'tr': 'Turkish',
        'sv': 'Swedish',
        'da': 'Danish',
        'no': 'Norwegian',
        'fi': 'Finnish'
    }
    
    def __init__(self):
        """Initialize the language detector."""
        self.detector = None
        self._initialize_detector()
    
    def _initialize_detector(self):
        """Initialize the detection backend."""
        try:
            # Try to use langdetect (lightweight and accurate)
            from langdetect import detect, detect_langs
            self.detect_func = detect
            self.detect_langs_func = detect_langs
            self.backend = 'langdetect'
            logger.info("Language detector initialized with langdetect")
        except ImportError:
            logger.warning("langdetect not installed, language detection limited")
            self.detect_func = None
            self.detect_langs_func = None
            self.backend = None
    
    def detect(self, text: str) -> Optional[str]:
        """
        Detect the language of the given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code (e.g., 'en', 'es') or None if detection fails
        """
        if not text or not text.strip():
            return None
        
        if self.detect_func:
            try:
                # Use langdetect
                lang = self.detect_func(text)
                logger.debug(f"Detected language: {lang}")
                return lang
            except Exception as e:
                logger.warning(f"Language detection failed: {e}")
                return None
        else:
            # Fallback: simple heuristic detection
            return self._heuristic_detection(text)
    
    def detect_with_confidence(self, text: str) -> List[Dict[str, float]]:
        """
        Detect language with confidence scores.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of dicts with 'lang' and 'confidence' keys
        """
        if not text or not text.strip():
            return []
        
        if self.detect_langs_func:
            try:
                # Use langdetect with probabilities
                results = self.detect_langs_func(text)
                return [{'lang': r.lang, 'confidence': r.prob} for r in results]
            except Exception as e:
                logger.warning(f"Language detection with confidence failed: {e}")
                return []
        else:
            # Fallback: return single detection with 1.0 confidence
            lang = self._heuristic_detection(text)
            if lang:
                return [{'lang': lang, 'confidence': 1.0}]
            return []
    
    def _heuristic_detection(self, text: str) -> Optional[str]:
        """
        Simple heuristic language detection based on character patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language code or None
        """
        text_lower = text.lower()
        
        # Check for Chinese characters
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return 'zh'
        
        # Check for Japanese characters (Hiragana/Katakana)
        if any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
            return 'ja'
        
        # Check for Korean characters
        if any('\uac00' <= char <= '\ud7af' for char in text):
            return 'ko'
        
        # Check for Arabic characters
        if any('\u0600' <= char <= '\u06ff' for char in text):
            return 'ar'
        
        # Check for Cyrillic (Russian, etc.)
        if any('\u0400' <= char <= '\u04ff' for char in text):
            return 'ru'
        
        # Check for common Spanish words/patterns
        spanish_indicators = ['que', 'de', 'la', 'el', 'en', 'y', 'los', 'las', 'por', 'con', 'para', 'está', 'ñ']
        spanish_count = sum(1 for word in spanish_indicators if word in text_lower)
        
        # Check for common French words/patterns
        french_indicators = ['le', 'de', 'un', 'être', 'et', 'à', 'il', 'avoir', 'ne', 'je', 'son', 'que', 'se', 'qui', 'ce', 'dans', 'elle', 'au', 'pour', 'pas']
        french_count = sum(1 for word in french_indicators if word in text_lower)
        
        # Check for common German words/patterns
        german_indicators = ['der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'und', 'ist', 'ich', 'nicht', 'sie', 'mit', 'auf', 'für', 'von', 'zu', 'ß', 'ü', 'ö', 'ä']
        german_count = sum(1 for word in german_indicators if word in text_lower)
        
        # Check for common English words/patterns
        english_indicators = ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at']
        english_count = sum(1 for word in english_indicators if word in text_lower)
        
        # Simple scoring
        scores = {
            'es': spanish_count,
            'fr': french_count,
            'de': german_count,
            'en': english_count
        }
        
        # Return language with highest score (if any)
        if max(scores.values()) > 2:  # At least 3 indicators
            return max(scores, key=scores.get)
        
        # Default to None if uncertain
        return None
    
    def is_supported(self, lang_code: str) -> bool:
        """
        Check if a language code is supported.
        
        Args:
            lang_code: Language code to check
            
        Returns:
            True if supported
        """
        return lang_code in self.LANGUAGE_CODES
    
    def get_language_name(self, lang_code: str) -> str:
        """
        Get the full name of a language from its code.
        
        Args:
            lang_code: Language code
            
        Returns:
            Language name or code if not found
        """
        return self.LANGUAGE_CODES.get(lang_code, lang_code)
    
    @staticmethod
    def get_supported_languages() -> Dict[str, str]:
        """Get dictionary of supported language codes and names."""
        return LanguageDetector.LANGUAGE_CODES.copy()