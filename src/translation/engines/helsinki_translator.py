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
        # Portuguese: no dedicated pt-en model exists, but the ROMANCE-en
        # model (es/fr/it/pt/ro/... -> en) is far better than the generic
        # mul-en fallback that was used before.
        ('pt', 'en'): 'Helsinki-NLP/opus-mt-ROMANCE-en',
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
        self.model = None
        self.tokenizer = None
        self.model_name = None
        self.max_length = 512  # Maximum tokens for Helsinki models

        # Initialize the model
        self._initialize_model()

    def _initialize_model(self):
        """Load the appropriate Helsinki-NLP model.

        Uses the tokenizer + model directly (not transformers.pipeline):
        the "translation" pipeline task was removed in transformers 5.x.
        """
        try:
            # Import here to avoid loading if not needed
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            import torch

            # Find appropriate model
            model_name = self._get_model_name()
            if not model_name:
                raise ValueError(f"Unsupported language pair: {self.source_lang} -> {self.target_lang}")

            self.model_name = model_name
            logger.info(f"Loading translation model: {model_name}")
            print(f"Downloading/loading translation model: {model_name}", flush=True)
            print("This may take a few minutes on first use (200-500MB download)...", flush=True)

            # Determine device - prefer GPU if available. Record the choice so
            # cleanup() can free GPU memory correctly.
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using {self.device.upper()} for translation")
            print(f"Using {self.device.upper()} for translation", flush=True)

            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()

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

    def _translate_batch(self, texts: List[str]) -> List[str]:
        """Translate a list of texts in one model call."""
        import torch

        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_length=self.max_length)

        return self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
    
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
        if not self.model:
            raise RuntimeError("Translation model not initialized")

        if not text or not text.strip():
            return text

        try:
            return self._translate_batch([text])[0]
        except Exception as e:
            logger.error(f"Translation failed for text: {e}")
            raise RuntimeError(f"Translation failed: {e}")
    
    def translate_segments(self, segments: List[Dict], batch_size: int = 16) -> List[Dict]:
        """
        Translate subtitle segments while preserving timestamps and structure.

        Each segment is translated individually (in batches for throughput), so
        every subtitle receives exactly its own translation. This replaced a
        sliding-context approach that translated whole windows as paragraphs
        and heuristically extracted "the middle sentence" - which dropped,
        duplicated, or misassigned translations whenever sentence boundaries
        didn't line up with subtitle boundaries.

        Args:
            segments: List of subtitle segments with 'text', 'start', 'end' fields
            batch_size: Number of texts to send to the model at once

        Returns:
            List of segments with added 'translated_text' field
        """
        if not self.model:
            raise RuntimeError("Translation model not initialized")

        translated_segments = [segment.copy() for segment in segments]
        total_segments = len(segments)

        # Collect the non-empty texts (with their positions) for batching
        pending = [
            (i, seg.get('text', '').strip())
            for i, seg in enumerate(translated_segments)
        ]
        for i, text in pending:
            translated_segments[i]['translated_text'] = ''
            if text:
                translated_segments[i]['original_text'] = text

        to_translate = [(i, text) for i, text in pending if text]

        for batch_start in range(0, len(to_translate), batch_size):
            batch = to_translate[batch_start:batch_start + batch_size]
            done = min(batch_start + len(batch), len(to_translate))
            logger.info(f"Translating segments {done}/{len(to_translate)}")
            print(f"Translating subtitles: {done}/{len(to_translate)}")

            texts = [text for _, text in batch]
            try:
                results = self._translate_batch(texts)
                for (i, _text), translated_text in zip(batch, results):
                    translated_segments[i]['translated_text'] = translated_text
            except Exception as e:
                logger.error(f"Batch translation failed, falling back to per-item: {e}")
                # Fall back to one-at-a-time so a single bad text can't sink the batch
                for i, text in batch:
                    try:
                        translated_segments[i]['translated_text'] = self.translate(text)
                    except Exception as item_error:
                        logger.error(f"Failed to translate segment {i}: {item_error}")
                        translated_segments[i]['translated_text'] = text
                        translated_segments[i]['translation_error'] = str(item_error)

        logger.info(f"Translation complete: {total_segments} segments")
        print(f"Translation complete: {total_segments} segments translated")
        return translated_segments
    
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
        self.model = None
        self.tokenizer = None

        # Try to free GPU memory if using CUDA
        try:
            import torch
            if self.device == "cuda" and torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass