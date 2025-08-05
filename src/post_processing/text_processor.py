import re
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    def __init__(self):
        self.max_chunk_size = 10000  # Process text in chunks of ~10K characters
        
    def split_into_chunks(self, text: str) -> List[str]:
        """Split long text into manageable chunks at sentence boundaries."""
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            if current_length + sentence_length > self.max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(sentence)
            current_length += sentence_length
            
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def detect_formatting_break(self, text: str) -> Tuple[str, str]:
        """
        Enhanced detection of formatting breaks with better handling of edge cases.
        """
        # Split text into sentences (considering multiple punctuation types)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        unformatted_start_idx = None
        formatted_again_idx = None
        
        # Look for where formatting breaks
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            # More comprehensive formatting checks
            has_capital = sentence and sentence[0].isupper()
            has_punctuation = sentence and sentence[-1] in '.!?'
            has_proper_spacing = not re.search(r'\s{2,}', sentence)
            proper_length = len(sentence.split()) > 1  # Avoid single-word "sentences"
            
            # If we find significant formatting issues
            if not (has_capital and has_punctuation and has_proper_spacing and proper_length):
                if unformatted_start_idx is None:
                    unformatted_start_idx = i
            # If formatting appears again after a break
            elif unformatted_start_idx is not None and formatted_again_idx is None:
                formatted_again_idx = i
        
        if unformatted_start_idx is None:
            return text, ""
            
        # If we found a formatting break
        formatted_part = ' '.join(sentences[:unformatted_start_idx])
        unformatted_part = ' '.join(sentences[unformatted_start_idx:])
        
        return formatted_part, unformatted_part

    def format_text(self, text: str) -> str:
        """
        Enhanced text formatting with better sentence detection and punctuation handling.
        """
        # First clean up any obvious issues
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split into potential sentences (handle multiple cases)
        raw_sentences = re.split(r'([^.!?]+[.!?]*)', text)
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        
        formatted = []
        for sentence in sentences:
            if not sentence:
                continue
            
            # Remove extra spaces and handle other cleanup
            sentence = ' '.join(sentence.split())
            
            # Handle capitalization
            if sentence and not sentence[0].isupper():
                sentence = sentence[0].upper() + sentence[1:]
            
            # Handle punctuation
            if not sentence[-1] in '.!?':
                # Check if it's a question
                if any(q in sentence.lower() for q in ['what', 'why', 'how', 'when', 'where', 'who']):
                    sentence += '?'
                else:
                    sentence += '.'
            
            formatted.append(sentence)
        
        return ' '.join(formatted)

    def process_transcript(self, text: str) -> str:
        """
        Process the full transcript with enhanced handling of long texts.
        """
        logger.info("Starting transcript processing")
        
        # Split into manageable chunks
        chunks = self.split_into_chunks(text)
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            # Process each chunk
            formatted_part, unformatted_part = self.detect_formatting_break(chunk)
            
            if unformatted_part:
                fixed_part = self.format_text(unformatted_part)
                processed_chunks.append(formatted_part + ' ' + fixed_part)
            else:
                processed_chunks.append(formatted_part)
        
        # Combine processed chunks
        final_text = ' '.join(processed_chunks)
        
        # Final verification pass
        final_text = self.format_text(final_text)
        
        logger.info("Transcript processing completed")
        return final_text