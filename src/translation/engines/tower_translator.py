"""
TowerInstruct translation engine for high-quality Portuguese to English translation.
GPU-only implementation using Unbabel/TowerInstruct model.
"""

import logging
import re
from typing import List, Dict, Optional

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class TowerTranslator:
    """
    Translator using Unbabel's TowerInstruct model for PT->EN translation.
    This is a GPU-only implementation for high-quality translation.
    """
    
    MODEL_NAME = "Unbabel/TowerInstruct-v0.1"
    MIN_VRAM_GB = 6.0  # Minimum VRAM required in GB
    
    def __init__(self):
        """
        Initialize the TowerInstruct translator.
        Requires GPU with sufficient VRAM.
        """
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.device = None
        
        # Check GPU availability first
        self._check_gpu_availability()
        
        # Initialize the model on GPU
        self._initialize_model()
    
    def _check_gpu_availability(self):
        """
        Check if GPU is available and has sufficient VRAM.
        Raises RuntimeError if requirements not met.
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "PyTorch is not installed. TowerInstruct requires PyTorch with CUDA support. "
                "Install with: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
            )
        
        if not torch.cuda.is_available():
            raise RuntimeError(
                "TowerInstruct requires an NVIDIA GPU with CUDA support. "
                "No GPU detected - falling back to standard translation."
            )
        
        # Check VRAM
        device_props = torch.cuda.get_device_properties(0)
        vram_gb = device_props.total_memory / (1024**3)
        
        logger.info(f"GPU detected: {device_props.name} with {vram_gb:.1f}GB VRAM")
        
        if vram_gb < self.MIN_VRAM_GB:
            raise RuntimeError(
                f"Insufficient GPU memory: {vram_gb:.1f}GB available, "
                f"but {self.MIN_VRAM_GB}GB required for TowerInstruct. "
                "Falling back to standard translation."
            )
        
        self.device = "cuda:0"
        logger.info(f"GPU requirements met. Using {device_props.name}")
    
    def _initialize_model(self):
        """
        Load the TowerInstruct model on GPU.
        """
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            
            logger.info(f"Loading TowerInstruct model on GPU...")
            print(f"Loading advanced PT->EN translation model (TowerInstruct)...")
            print(f"This may take a few minutes on first use (downloading ~14GB model)...")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.MODEL_NAME,
                trust_remote_code=True
            )
            
            # Load model with optimizations for GPU
            # When using accelerate, don't specify device_map
            self.model = AutoModelForCausalLM.from_pretrained(
                self.MODEL_NAME,
                torch_dtype=torch.bfloat16,  # Use bfloat16 for better performance
                device_map="auto",  # Let accelerate handle device placement
                trust_remote_code=True,
                low_cpu_mem_usage=True  # Optimize memory usage during loading
            )
            
            # Create pipeline for easier usage
            # Don't specify device when model is loaded with accelerate
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                torch_dtype=torch.bfloat16
            )
            
            logger.info("TowerInstruct model loaded successfully on GPU")
            print("Advanced translation model ready (GPU accelerated)")
            
        except ImportError as e:
            raise RuntimeError(
                "Required libraries not installed. Please install: "
                "pip install transformers torch accelerate"
            ) from e
        except Exception as e:
            logger.error(f"Failed to load TowerInstruct model: {e}")
            raise RuntimeError(f"Failed to load TowerInstruct model: {e}") from e
    
    def translate(self, text: str, variant: str = "brazilian") -> str:
        """
        Translate Portuguese text to English.
        
        Args:
            text: Portuguese text to translate
            variant: Portuguese variant ('brazilian' or 'european')
            
        Returns:
            Translated English text
        """
        if not self.pipeline:
            raise RuntimeError("Translation model not initialized")
        
        if not text or not text.strip():
            return text
        
        try:
            # Prepare the prompt for translation
            # TowerInstruct uses ChatML format
            variant_hint = "Brazilian Portuguese" if variant == "brazilian" else "European Portuguese"
            
            messages = [
                {
                    "role": "user",
                    "content": f"Translate the following {variant_hint} text to English. "
                              f"Provide only the translation, no explanations.\n\n"
                              f"Portuguese: {text}\n"
                              f"English:"
                }
            ]
            
            # Apply chat template
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Generate translation
            with torch.no_grad():  # Disable gradient computation for inference
                outputs = self.pipeline(
                    prompt,
                    max_new_tokens=256,
                    do_sample=False,  # Deterministic output
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Extract translation from output
            generated_text = outputs[0]['generated_text']
            
            # Extract only the English translation part
            if "English:" in generated_text:
                translation = generated_text.split("English:")[-1].strip()
                # Remove any potential continuation tokens or artifacts
                translation = translation.split("\n")[0].strip()
                # Remove any remaining instruction artifacts
                translation = re.sub(r'^["\']|["\']$', '', translation)
                return translation
            else:
                # Fallback: return the generated text after the prompt
                translation = generated_text[len(prompt):].strip()
                return translation
                
        except torch.cuda.OutOfMemoryError:
            logger.error("GPU out of memory. Try closing other applications.")
            raise RuntimeError("GPU out of memory. Please close other GPU applications and try again.")
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise RuntimeError(f"Translation failed: {e}")
    
    def translate_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Translate subtitle segments while preserving timestamps.
        
        Args:
            segments: List of subtitle segments with 'text', 'start', 'end' fields
            
        Returns:
            List of segments with added 'translated_text' field
        """
        if not self.pipeline:
            raise RuntimeError("Translation model not initialized")
        
        translated_segments = []
        total_segments = len(segments)
        
        # Detect Portuguese variant from the text
        variant = self._detect_portuguese_variant(segments)
        logger.info(f"Detected Portuguese variant: {variant}")
        
        for i, segment in enumerate(segments):
            # Progress logging
            if i % 10 == 0:
                logger.info(f"Translating segment {i+1}/{total_segments}")
                print(f"Translating (TowerInstruct GPU): {i+1}/{total_segments}")
            
            # Copy segment to preserve all original data
            translated_seg = segment.copy()
            
            # Translate the text
            original_text = segment.get('text', '').strip()
            if original_text:
                try:
                    translated_text = self.translate(original_text, variant)
                    translated_seg['translated_text'] = translated_text
                    translated_seg['original_text'] = original_text
                except Exception as e:
                    logger.error(f"Failed to translate segment {i}: {e}")
                    # Keep original text if translation fails
                    translated_seg['translated_text'] = original_text
                    translated_seg['translation_error'] = str(e)
            else:
                translated_seg['translated_text'] = ''
            
            translated_segments.append(translated_seg)
            
            # Clear GPU cache periodically to prevent OOM
            if i % 50 == 0 and i > 0:
                torch.cuda.empty_cache()
        
        logger.info(f"Translation complete: {total_segments} segments")
        print(f"TowerInstruct translation complete: {total_segments} segments")
        return translated_segments
    
    def translate_with_context(self, segments: List[Dict], context_window: int = 2) -> List[Dict]:
        """
        Translate segments with surrounding context for better accuracy.
        Uses smaller context window due to GPU memory constraints.
        
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
        variant = self._detect_portuguese_variant(segments)
        
        print(f"Translating {total_segments} segments with context (TowerInstruct GPU)...")
        
        for i, segment in enumerate(segments):
            # Progress logging
            if i % 10 == 0:
                logger.info(f"Translating with context: segment {i+1}/{total_segments}")
                print(f"  Progress (GPU): {i+1}/{total_segments} segments...")
            
            current_text = segment.get('text', '').strip()
            translated_seg = segment.copy()
            
            if current_text:
                # Build minimal context (smaller window for GPU memory efficiency)
                context_parts = []
                
                # Add 1-2 previous segments as context
                for j in range(max(0, i - min(context_window, 2)), i):
                    prev_text = segments[j].get('text', '').strip()
                    if prev_text:
                        context_parts.append(prev_text)
                
                # Add current segment
                context_parts.append(f"[CURRENT] {current_text}")
                
                # Add 1 following segment as context
                if i + 1 < total_segments:
                    next_text = segments[i + 1].get('text', '').strip()
                    if next_text:
                        context_parts.append(next_text)
                
                # Create context string
                context_text = ' '.join(context_parts)
                
                try:
                    # Translate with context
                    full_translation = self.translate(context_text, variant)
                    
                    # Extract the current segment
                    if "[CURRENT]" in full_translation:
                        # Try to extract marked segment
                        parts = full_translation.split("[CURRENT]")
                        if len(parts) > 1:
                            translated_text = parts[1].split('.')[0].strip()
                        else:
                            translated_text = full_translation
                    else:
                        # Fallback: use the middle portion
                        sentences = full_translation.split('. ')
                        if len(sentences) > 1:
                            # Take middle sentence(s)
                            mid_idx = len(sentences) // 2
                            translated_text = sentences[mid_idx].strip()
                        else:
                            translated_text = full_translation
                    
                    translated_seg['translated_text'] = translated_text
                    translated_seg['original_text'] = current_text
                    
                except Exception as e:
                    logger.error(f"Failed to translate segment {i} with context: {e}")
                    # Fall back to simple translation
                    try:
                        translated_text = self.translate(current_text, variant)
                        translated_seg['translated_text'] = translated_text
                        translated_seg['original_text'] = current_text
                    except:
                        translated_seg['translated_text'] = current_text
                        translated_seg['translation_error'] = str(e)
            else:
                translated_seg['translated_text'] = ''
            
            translated_segments.append(translated_seg)
            
            # Clear GPU cache periodically
            if i % 30 == 0 and i > 0:
                torch.cuda.empty_cache()
        
        logger.info(f"Context-aware translation complete: {total_segments} segments")
        print(f"TowerInstruct GPU translation complete: {total_segments} segments")
        return translated_segments
    
    def _detect_portuguese_variant(self, segments: List[Dict]) -> str:
        """
        Detect whether the Portuguese text is Brazilian or European.
        
        Args:
            segments: List of subtitle segments
            
        Returns:
            'brazilian' or 'european'
        """
        # Combine some text for analysis
        sample_text = ' '.join([seg.get('text', '') for seg in segments[:20]])
        sample_lower = sample_text.lower()
        
        # Brazilian Portuguese indicators
        brazilian_indicators = [
            'você', 'vocês',  # Brazilian pronouns
            'pra', 'pro',  # Brazilian contractions
            'tá', 'tô',  # Brazilian colloquialisms
            'gente',  # Common in "a gente" (we)
            'legal',  # Common Brazilian expression
            'ônibus',  # Brazilian spelling
            'celular',  # Brazilian for mobile phone
        ]
        
        # European Portuguese indicators
        european_indicators = [
            'tu', 'vós',  # European pronouns
            'para o', 'para a',  # Full forms more common in PT-PT
            'está', 'estou',  # Full forms
            'telemóvel',  # European for mobile phone
            'autocarro',  # European for bus
            'comboio',  # European for train
        ]
        
        brazilian_count = sum(1 for indicator in brazilian_indicators if indicator in sample_lower)
        european_count = sum(1 for indicator in european_indicators if indicator in sample_lower)
        
        # Default to Brazilian (more common in media)
        if brazilian_count > european_count:
            return 'brazilian'
        elif european_count > brazilian_count:
            return 'european'
        else:
            # Default to Brazilian Portuguese
            return 'brazilian'
    
    def batch_translate(self, texts: List[str], batch_size: int = 8) -> List[str]:
        """
        Translate multiple texts in batches for GPU efficiency.
        Smaller batch size due to model size.
        
        Args:
            texts: List of texts to translate
            batch_size: Number of texts to process at once
            
        Returns:
            List of translated texts
        """
        translated = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            for text in batch:
                try:
                    trans = self.translate(text)
                    translated.append(trans)
                except Exception as e:
                    logger.error(f"Failed to translate in batch: {e}")
                    translated.append(text)  # Keep original if failed
            
            # Clear GPU cache after each batch
            torch.cuda.empty_cache()
        
        return translated
    
    def cleanup(self):
        """Clean up GPU resources."""
        if self.model:
            del self.model
            self.model = None
        
        if self.pipeline:
            del self.pipeline
            self.pipeline = None
        
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None
        
        # Clear GPU cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("GPU memory cleared")
    
    @staticmethod
    def check_gpu_requirements() -> Dict[str, any]:
        """
        Check if system meets GPU requirements for TowerInstruct.
        
        Returns:
            Dictionary with GPU status information
        """
        if not TORCH_AVAILABLE:
            return {
                'gpu_available': False,
                'gpu_name': None,
                'vram_gb': 0,
                'meets_requirements': False,
                'message': 'PyTorch not installed - required for TowerInstruct'
            }
        
        info = {
            'gpu_available': torch.cuda.is_available(),
            'gpu_name': None,
            'vram_gb': 0,
            'meets_requirements': False,
            'message': ''
        }
        
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            vram_gb = props.total_memory / (1024**3)
            
            info['gpu_name'] = props.name
            info['vram_gb'] = round(vram_gb, 1)
            info['meets_requirements'] = vram_gb >= TowerTranslator.MIN_VRAM_GB
            
            if info['meets_requirements']:
                info['message'] = f"GPU ready: {props.name} ({vram_gb:.1f}GB)"
            else:
                info['message'] = f"Insufficient VRAM: {vram_gb:.1f}GB (need {TowerTranslator.MIN_VRAM_GB}GB)"
        else:
            info['message'] = "No NVIDIA GPU detected"
        
        return info