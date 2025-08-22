"""
Helsinki-NLP translation engine using Hugging Face Transformers.
Free, open-source translation with good quality.
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class HelsinkiTranslator:
    """
    Translator using Helsinki-NLP OPUS-MT models from Hugging Face.
    These are completely free, open-source neural translation models.
    """
    
    # Supported language pairs (can be extended)
    SUPPORTED_PAIRS = {
        ('es', 'en'): 'Helsinki-NLP/opus-mt-es-en',
        ('en', 'es'): 'Helsinki-NLP/opus-mt-en-es',
        ('fr', 'en'): 'Helsinki-NLP/opus-mt-fr-en',
        ('en', 'fr'): 'Helsinki-NLP/opus-mt-en-fr',
        ('de', 'en'): 'Helsinki-NLP/opus-mt-de-en',
        ('en', 'de'): 'Helsinki-NLP/opus-mt-en-de',
        ('it', 'en'): 'Helsinki-NLP/opus-mt-it-en',
        ('en', 'it'): 'Helsinki-NLP/opus-mt-en-it',
        ('pt', 'en'): 'Helsinki-NLP/opus-mt-pt-en',
        ('en', 'pt'): 'Helsinki-NLP/opus-mt-en-pt',
        ('ru', 'en'): 'Helsinki-NLP/opus-mt-ru-en',
        ('en', 'ru'): 'Helsinki-NLP/opus-mt-en-ru',
        ('zh', 'en'): 'Helsinki-NLP/opus-mt-zh-en',
        ('en', 'zh'): 'Helsinki-NLP/opus-mt-en-zh',
        ('ja', 'en'): 'Helsinki-NLP/opus-mt-ja-en',
        ('en', 'ja'): 'Helsinki-NLP/opus-mt-en-ja',
        # Multi-language models for broader coverage
        ('mul', 'en'): 'Helsinki-NLP/opus-mt-mul-en',  # Multiple languages to English
        ('en', 'mul'): 'Helsinki-NLP/opus-mt-en-mul',  # English to multiple languages
    }
    
    def __init__(self, source_lang: str, target_lang: str, device: str = "cpu"):
        """
        Initialize the Helsinki translator.
        
        Args:
            source_lang: Source language code (e.g., 'es', 'fr')
            target_lang: Target language code (e.g., 'en')
            device: Device to run on ('cpu' or 'cuda')
        """
        self.source_lang = source_lang.lower()
        self.target_lang = target_lang.lower()
        self.device = device
        self.pipeline = None
        self.tokenizer = None
        self.model_name = None
        self.max_length = 512  # Maximum tokens for Helsinki models
        
        # Initialize the model
        self._initialize_model()
    
    def _initialize_model(self):
        """Load the appropriate Helsinki-NLP model."""
        print(f"DEBUG: _initialize_model() called", flush=True)
        print(f"DEBUG: source_lang={self.source_lang}, target_lang={self.target_lang}", flush=True)
        try:
            # Import here to avoid loading if not needed
            print(f"DEBUG: Importing transformers and torch...", flush=True)
            from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
            import torch
            print(f"DEBUG: Imports successful", flush=True)
            
            # Find appropriate model
            print(f"DEBUG: Getting model name...", flush=True)
            model_name = self._get_model_name()
            print(f"DEBUG: Model name: {model_name}", flush=True)
            if not model_name:
                raise ValueError(f"Unsupported language pair: {self.source_lang} -> {self.target_lang}")
            
            self.model_name = model_name
            logger.info(f"Loading translation model: {model_name}")
            print(f"Downloading/loading translation model: {model_name}", flush=True)
            print("This may take a few minutes on first use (200-500MB download)...", flush=True)
            
            # Determine device - prefer GPU if available
            if torch.cuda.is_available():
                device_id = 0  # Use GPU
                logger.info("Using GPU for translation")
                print(f"Using GPU for translation (CUDA available)", flush=True)
            else:
                device_id = -1  # CPU
                logger.info("Using CPU for translation")
                print(f"Using CPU for translation (CUDA not available)", flush=True)
            
            # Load tokenizer and model
            print(f"DEBUG: Loading tokenizer from {model_name}...", flush=True)
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            print(f"DEBUG: Tokenizer loaded", flush=True)
            
            # Create translation pipeline
            print(f"DEBUG: Creating translation pipeline...", flush=True)
            self.pipeline = pipeline(
                "translation",
                model=model_name,
                tokenizer=self.tokenizer,
                device=device_id,
                max_length=self.max_length
            )
            print(f"DEBUG: Pipeline created successfully", flush=True)
            
            logger.info(f"Translation model loaded successfully: {model_name}")
            print(f"Translation model ready: {model_name}", flush=True)
            
        except ImportError as e:
            error_msg = "transformers library not installed. Please install with: pip install transformers torch"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to load translation model: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def _get_model_name(self) -> Optional[str]:
        """Get the model name for the language pair."""
        # Direct match
        if (self.source_lang, self.target_lang) in self.SUPPORTED_PAIRS:
            return self.SUPPORTED_PAIRS[(self.source_lang, self.target_lang)]
        
        # Try multi-language models as fallback
        if self.target_lang == 'en' and (self.source_lang, 'en') not in self.SUPPORTED_PAIRS:
            logger.warning(f"Using multi-language model for {self.source_lang} -> en")
            return self.SUPPORTED_PAIRS[('mul', 'en')]
        
        if self.source_lang == 'en' and ('en', self.target_lang) not in self.SUPPORTED_PAIRS:
            logger.warning(f"Using multi-language model for en -> {self.target_lang}")
            return self.SUPPORTED_PAIRS[('en', 'mul')]
        
        return None
    
    def translate(self, text: str) -> str:
        """
        Translate a single text string.
        
        Args:
            text: Text to translate
            
        Returns:
            Translated text
        """
        if not self.pipeline:
            raise RuntimeError("Translation model not initialized")
        
        if not text or not text.strip():
            return text
        
        try:
            result = self.pipeline(text, max_length=self.max_length)
            return result[0]['translation_text']
        except Exception as e:
            logger.error(f"Translation failed for text: {e}")
            raise RuntimeError(f"Translation failed: {e}")
    
    def translate_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Translate subtitle segments while preserving timestamps and structure.
        
        Args:
            segments: List of subtitle segments with 'text', 'start', 'end' fields
            
        Returns:
            List of segments with added 'translated_text' field
        """
        if not self.pipeline:
            raise RuntimeError("Translation model not initialized")
        
        translated_segments = []
        total_segments = len(segments)
        
        for i, segment in enumerate(segments):
            # Progress logging
            if i % 10 == 0:
                logger.info(f"Translating segment {i+1}/{total_segments}")
                print(f"Translating subtitles: {i+1}/{total_segments}")
            
            # Copy segment to preserve all original data
            translated_seg = segment.copy()
            
            # Translate the text
            original_text = segment.get('text', '').strip()
            if original_text:
                try:
                    translated_text = self.translate(original_text)
                    translated_seg['translated_text'] = translated_text
                    translated_seg['original_text'] = original_text  # Keep original for reference
                except Exception as e:
                    logger.error(f"Failed to translate segment {i}: {e}")
                    # Keep original text if translation fails
                    translated_seg['translated_text'] = original_text
                    translated_seg['translation_error'] = str(e)
            else:
                translated_seg['translated_text'] = ''
            
            translated_segments.append(translated_seg)
        
        logger.info(f"Translation complete: {total_segments} segments")
        print(f"Translation complete: {total_segments} segments translated")
        return translated_segments
    
    def translate_with_context(self, segments: List[Dict], context_window: int = 3) -> List[Dict]:
        """
        Translate segments with surrounding context for better accuracy.
        
        This method provides context from surrounding segments to improve
        translation quality, especially for pronouns and references.
        
        Args:
            segments: List of subtitle segments
            context_window: Number of segments before/after to include as context
            
        Returns:
            List of translated segments
        """
        print(f"DEBUG: translate_with_context called with {len(segments)} segments", flush=True)
        print(f"DEBUG: self.pipeline = {self.pipeline is not None}", flush=True)
        
        if not self.pipeline:
            raise RuntimeError("Translation model not initialized")
        
        translated_segments = []
        total_segments = len(segments)
        
        print(f"DEBUG: Starting context translation loop...", flush=True)
        for i, segment in enumerate(segments):
            # Progress logging
            if i % 10 == 0:
                logger.info(f"Translating with context: segment {i+1}/{total_segments}")
                print(f"Translating with context: {i+1}/{total_segments}")
            
            # Build context from surrounding segments
            context_parts = []
            
            # Add previous segments as context
            for j in range(max(0, i - context_window), i):
                context_parts.append(segments[j].get('text', ''))
            
            # Add current segment with markers
            current_text = segment.get('text', '').strip()
            if current_text:
                # Mark the current segment so we can extract it
                marked_text = f"[CURRENT] {current_text} [/CURRENT]"
                context_parts.append(marked_text)
            else:
                context_parts.append('')
            
            # Add following segments as context
            for j in range(i + 1, min(total_segments, i + context_window + 1)):
                context_parts.append(segments[j].get('text', ''))
            
            # Create context string
            context_text = ' '.join(filter(None, context_parts))
            
            # Translate with context
            translated_seg = segment.copy()
            
            if current_text:
                try:
                    # Translate the full context
                    # Show progress every 10 segments
                    if (i + 1) % 10 == 0:
                        print(f"  Progress: {i+1}/{total_segments} segments translated...", flush=True)
                    translated_context = self.translate(context_text)
                    
                    # Extract the current segment from translated context
                    translated_text = self._extract_current_from_context(translated_context)
                    
                    translated_seg['translated_text'] = translated_text
                    translated_seg['original_text'] = current_text
                    
                except Exception as e:
                    logger.error(f"Failed to translate segment {i} with context: {e}")
                    # Fall back to simple translation without context
                    try:
                        translated_text = self.translate(current_text)
                        translated_seg['translated_text'] = translated_text
                        translated_seg['original_text'] = current_text
                    except:
                        translated_seg['translated_text'] = current_text
                        translated_seg['translation_error'] = str(e)
            else:
                translated_seg['translated_text'] = ''
            
            translated_segments.append(translated_seg)
        
        logger.info(f"Context-aware translation complete: {total_segments} segments")
        return translated_segments
    
    def _extract_current_from_context(self, translated_context: str) -> str:
        """
        Extract the current segment from translated context.
        
        Args:
            translated_context: Translated text with [CURRENT] markers
            
        Returns:
            Extracted current segment text
        """
        # Try multiple patterns as the model may corrupt the markers
        patterns = [
            r'\[CURRENT\](.*?)\[/CURRENT\]',  # Original markers
            r'\[Current\](.*?)\[/Current\]',  # Case variation
            r'\[COURRENT\](.*?)\[/COURRENT\]',  # Typo variation  
            r'\[CU?R+E?N?T\](.*?)\[/CU?R+E?N?T\]',  # General typos
            r'CURRENT(.*?)/?CURRENT',  # Without brackets
            r'Current(.*?)/?Current',  # Case variation without brackets
        ]
        
        for pattern in patterns:
            match = re.search(pattern, translated_context, re.DOTALL | re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Clean up any remaining marker fragments
                extracted = re.sub(r'\[/?(?:CURRENT|Current|COURRENT)\]', '', extracted, flags=re.IGNORECASE)
                return extracted
        
        # If no markers found, try a different approach
        # Remove any corrupted markers from the text first
        cleaned = re.sub(r'\[/?(?:CURRENT|Current|COURRENT|CU?R+E?N?T)\]', '', translated_context, flags=re.IGNORECASE)
        
        # Return the cleaned text (it's better than returning partial text)
        return cleaned.strip()
    
    def translate_with_context_fixed(self, segments: List[Dict], context_window: int = 3) -> List[Dict]:
        """
        Translate segments with context for better quality, but with proper extraction.
        Uses a unique separator approach to prevent text bleeding.
        
        Args:
            segments: List of subtitle segments
            context_window: Number of segments before/after to include as context
            
        Returns:
            List of translated segments
        """
        if not self.pipeline:
            raise RuntimeError("Translation model not initialized")
        
        translated_segments = []
        total_segments = len(segments)
        
        print(f"Translating {total_segments} segments with context (fixed extraction)...", flush=True)
        
        for i, segment in enumerate(segments):
            # Progress logging
            if i % 10 == 0:
                logger.info(f"Translating with context: segment {i+1}/{total_segments}")
                print(f"  Progress: {i+1}/{total_segments} segments...", flush=True)
            
            current_text = segment.get('text', '').strip()
            translated_seg = segment.copy()
            
            if current_text:
                # Build context with clear separators
                context_parts = []
                
                # Add previous segments as context (but limited)
                for j in range(max(0, i - context_window), i):
                    prev_text = segments[j].get('text', '').strip()
                    if prev_text:
                        # Add with separator that won't appear in normal text
                        context_parts.append(prev_text)
                
                # Add current segment with unique markers that are less likely to be corrupted
                # Use a combination that the model is unlikely to translate
                marked_current = f"<<<TRANSLATE_THIS>>> {current_text} <<<END_TRANSLATE>>>"
                context_parts.append(marked_current)
                
                # Add following segments as context (but limited)
                for j in range(i + 1, min(total_segments, i + context_window + 1)):
                    next_text = segments[j].get('text', '').strip()
                    if next_text:
                        context_parts.append(next_text)
                
                # Join with clear separator
                context_text = ' | '.join(context_parts)
                
                try:
                    # Translate the full context
                    translated_context = self.translate(context_text)
                    
                    # Extract the translated current segment
                    # Try multiple extraction patterns
                    translated_text = None
                    
                    # Pattern 1: Look for our markers (they might be translated)
                    patterns = [
                        r'<<<TRANSLATE_THIS>>>\s*(.*?)\s*<<<END_TRANSLATE>>>',
                        r'<<<TRANSLATE THIS>>>\s*(.*?)\s*<<<END TRANSLATE>>>',
                        r'TRANSLATE_THIS\s*(.*?)\s*END_TRANSLATE',
                        r'TRANSLATE THIS\s*(.*?)\s*END TRANSLATE',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, translated_context, re.IGNORECASE | re.DOTALL)
                        if match:
                            translated_text = match.group(1).strip()
                            break
                    
                    # Pattern 2: If markers failed, try to find text between separators
                    if not translated_text:
                        # Split by our separator and take the middle part
                        parts = translated_context.split(' | ')
                        if len(parts) > len(context_parts) // 2:
                            # Take the part that should correspond to current segment
                            idx = len([p for p in context_parts[:i+1] if p]) - 1
                            if 0 <= idx < len(parts):
                                translated_text = parts[idx].strip()
                    
                    # Pattern 3: If still no match, use a heuristic
                    if not translated_text:
                        # Remove any remaining marker fragments
                        cleaned = re.sub(r'<<<[^>]*>>>', '', translated_context)
                        cleaned = re.sub(r'TRANSLATE[_\s]THIS|END[_\s]TRANSLATE', '', cleaned, flags=re.IGNORECASE)
                        # Take the middle portion (rough approximation)
                        sentences = cleaned.split('. ')
                        if len(sentences) > 2 * context_window:
                            # Take sentences from the middle
                            start_idx = context_window
                            end_idx = len(sentences) - context_window
                            translated_text = '. '.join(sentences[start_idx:end_idx]).strip()
                        else:
                            # Fall back to just translating the segment alone
                            translated_text = self.translate(current_text)
                    
                    # Clean up any remaining artifacts
                    if translated_text:
                        translated_text = re.sub(r'<<<[^>]*>>>', '', translated_text).strip()
                        translated_text = re.sub(r'\|\s*\|', '', translated_text).strip()
                    
                    translated_seg['translated_text'] = translated_text or current_text
                    translated_seg['original_text'] = current_text
                    
                except Exception as e:
                    logger.error(f"Failed to translate segment {i} with context: {e}")
                    # Fall back to simple translation
                    try:
                        translated_text = self.translate(current_text)
                        translated_seg['translated_text'] = translated_text
                        translated_seg['original_text'] = current_text
                    except:
                        translated_seg['translated_text'] = current_text
                        translated_seg['translation_error'] = str(e)
            else:
                translated_seg['translated_text'] = ''
            
            translated_segments.append(translated_seg)
        
        logger.info(f"Context-aware translation complete: {total_segments} segments")
        print(f"Translation complete: {total_segments} segments translated")
        return translated_segments
    
    def translate_segments_with_smart_context(self, segments: List[Dict]) -> List[Dict]:
        """
        Translate segments with context but without text bleeding.
        Translates each segment individually but provides context for better quality.
        
        Args:
            segments: List of subtitle segments
            
        Returns:
            List of translated segments
        """
        if not self.pipeline:
            raise RuntimeError("Translation model not initialized")
        
        translated_segments = []
        total_segments = len(segments)
        
        print(f"Translating {total_segments} segments with smart context...", flush=True)
        
        for i, segment in enumerate(segments):
            # Progress logging
            if i % 10 == 0:
                logger.info(f"Translating: segment {i+1}/{total_segments}")
                print(f"  Progress: {i+1}/{total_segments} segments...", flush=True)
            
            # Get the current segment text
            current_text = segment.get('text', '').strip()
            translated_seg = segment.copy()
            
            if current_text:
                # Build a small context hint for better translation
                context_hint = ""
                if i > 0:
                    prev_text = segments[i-1].get('text', '').strip()
                    if prev_text:
                        # Only use last sentence of previous segment as hint
                        prev_sentences = prev_text.split('.')
                        if prev_sentences:
                            context_hint = prev_sentences[-1].strip() + ". "
                
                # Translate current segment with minimal context hint
                text_to_translate = context_hint + current_text
                
                try:
                    # Translate the text
                    full_translation = self.translate(text_to_translate)
                    
                    # Remove the context hint from translation if present
                    if context_hint:
                        # Try to remove the translated context hint
                        # This is approximate but better than including it
                        translated_parts = full_translation.split('. ', 1)
                        if len(translated_parts) > 1:
                            translated_text = translated_parts[1]
                        else:
                            translated_text = full_translation
                    else:
                        translated_text = full_translation
                    
                    translated_seg['translated_text'] = translated_text.strip()
                    translated_seg['original_text'] = current_text
                    
                except Exception as e:
                    logger.error(f"Failed to translate segment {i}: {e}")
                    # Fallback to original text
                    translated_seg['translated_text'] = current_text
                    translated_seg['translation_error'] = str(e)
            else:
                translated_seg['translated_text'] = ''
            
            translated_segments.append(translated_seg)
        
        logger.info(f"Smart context translation complete: {total_segments} segments")
        print(f"Translation complete: {total_segments} segments translated")
        return translated_segments
    
    def batch_translate(self, texts: List[str], batch_size: int = 32) -> List[str]:
        """
        Translate multiple texts in batches for efficiency.
        
        Args:
            texts: List of texts to translate
            batch_size: Number of texts to translate at once
            
        Returns:
            List of translated texts
        """
        if not self.pipeline:
            raise RuntimeError("Translation model not initialized")
        
        translated = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                # Pipeline can handle lists
                results = self.pipeline(batch, max_length=self.max_length)
                for result in results:
                    translated.append(result['translation_text'])
            except Exception as e:
                logger.error(f"Batch translation failed: {e}")
                # Fall back to individual translation
                for text in batch:
                    try:
                        trans = self.translate(text)
                        translated.append(trans)
                    except:
                        translated.append(text)  # Keep original if failed
        
        return translated
    
    @staticmethod
    def get_supported_languages() -> Dict[str, List[Tuple[str, str]]]:
        """
        Get list of supported language pairs.
        
        Returns:
            Dictionary with 'direct' pairs and 'multi' language support info
        """
        direct_pairs = []
        for (src, tgt), model in HelsinkiTranslator.SUPPORTED_PAIRS.items():
            if src != 'mul' and tgt != 'mul':
                direct_pairs.append((src, tgt))
        
        return {
            'direct': direct_pairs,
            'multi_to_en': 'Most languages to English via multi-language model',
            'en_to_multi': 'English to most languages via multi-language model'
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.pipeline = None
        self.tokenizer = None
        
        # Try to free GPU memory if using CUDA
        try:
            import torch
            if self.device == "cuda" and torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass