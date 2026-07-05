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

    @staticmethod
    def collapse_repetitions(text: str, max_word_repeats: int = 3, max_phrase_repeats: int = 2) -> str:
        """Collapse pathological repetition runs (Whisper hallucination loops).

        Non-speech audio (music, moaning, noise) makes Whisper emit walls of
        the same word or phrase ("yes yes yes yes...", "52, 53, 59, 52, 53,
        59..."). Keep the first few occurrences and drop the rest.

        Args:
            text: Input text
            max_word_repeats: Keep at most this many consecutive identical words
            max_phrase_repeats: Keep at most this many consecutive identical
                multi-word phrases (2-5 words)

        Returns:
            Text with repetition runs collapsed
        """
        words = text.split()
        n = len(words)
        if n < 4:
            return text

        def norm(w: str) -> str:
            return w.lower().strip('.,!?;:¡¿')

        result = []
        i = 0
        while i < n:
            collapsed = False
            # Longer phrases first so "a b a b a b" collapses as the phrase "a b"
            for plen in range(5, 0, -1):
                if i + plen * 2 > n:
                    continue
                phrase = [norm(w) for w in words[i:i + plen]]
                if not all(phrase):
                    continue
                # A run of one identical word must be handled by the plen=1
                # rule, not treated as a repeating multi-word phrase.
                if plen > 1 and len(set(phrase)) == 1:
                    continue
                count = 1
                j = i + plen
                while j + plen <= n and [norm(w) for w in words[j:j + plen]] == phrase:
                    count += 1
                    j += plen
                limit = max_word_repeats if plen == 1 else max_phrase_repeats
                if count > limit:
                    result.extend(words[i:i + plen * limit])
                    i += plen * count
                    collapsed = True
                    break
            if not collapsed:
                result.append(words[i])
                i += 1

        if len(result) < n:
            logger.info(f"Collapsed repetition runs: {n} -> {len(result)} words")
        return ' '.join(result)

    def format_text(self, text: str, language: str = 'en') -> str:
        """
        Enhanced text formatting with better sentence detection and punctuation handling.

        Args:
            text: Text to format
            language: ISO language code; English-specific rules are skipped
                for other languages
        """
        is_english = (language or 'en').lower().startswith('en')

        # First clean up any obvious issues
        text = re.sub(r'\s+', ' ', text).strip()

        # Handle empty or very short text
        if len(text) < 10:
            if text and not text[0].isupper():
                text = text[0].upper() + text[1:]
            if text and text[-1] not in '.!?':
                text += '.'
            return text

        # Split into potential sentences with improved regex
        # This regex better handles abbreviations and decimals
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

        formatted = []
        for sentence in sentences:
            if not sentence or len(sentence.strip()) < 2:
                continue

            # Remove extra spaces
            sentence = ' '.join(sentence.split())

            # Capitalize first letter
            if sentence and not sentence[0].isupper():
                sentence = sentence[0].upper() + sentence[1:]

            if is_english:
                # Capitalize 'I' anywhere in the sentence (English-only rule)
                sentence = re.sub(r'\bi\b', 'I', sentence)

            # Add ending punctuation if missing
            if sentence and sentence[-1] not in '.!?':
                if is_english:
                    # Question detection uses English question starters
                    question_starters = ['what', 'why', 'how', 'when', 'where', 'who', 'which',
                                       'can', 'could', 'would', 'should', 'will', 'do', 'does',
                                       'did', 'is', 'are', 'was', 'were', 'have', 'has']
                    first_word = sentence.split()[0].lower() if sentence.split() else ''

                    if first_word in question_starters:
                        sentence += '?'
                    elif any(word in sentence.lower() for word in ['amazing', 'awesome', 'fantastic', 'terrible']):
                        sentence += '!'
                    else:
                        sentence += '.'
                else:
                    sentence += '.'

            formatted.append(sentence)

        return ' '.join(formatted)

    def process_transcript(self, text: str, language: str = 'en') -> str:
        """
        Process the full transcript with enhanced handling of long texts.

        Args:
            text: Raw transcript text
            language: ISO language code of the transcript; English-specific
                formatting rules are skipped for other languages
        """
        logger.info(f"Starting transcript processing (language: {language})")

        # Collapse Whisper hallucination loops before any formatting
        text = self.collapse_repetitions(text)

        # Split into manageable chunks
        chunks = self.split_into_chunks(text)
        processed_chunks = []

        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")

            # Process each chunk
            formatted_part, unformatted_part = self.detect_formatting_break(chunk)

            if unformatted_part:
                fixed_part = self.format_text(unformatted_part, language=language)
                processed_chunks.append(formatted_part + ' ' + fixed_part)
            else:
                processed_chunks.append(formatted_part)

        # Combine processed chunks
        final_text = ' '.join(processed_chunks)

        # Final verification pass
        final_text = self.format_text(final_text, language=language)

        logger.info("Transcript processing completed")
        return final_text