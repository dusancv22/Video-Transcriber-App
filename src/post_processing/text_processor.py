import re
from typing import List, Tuple, Set
import logging

logger = logging.getLogger(__name__)

class EnhancedTextProcessor:
    def __init__(self):
        self.max_chunk_size = 10000  # Process text in chunks of ~10K characters
        
        # Comprehensive proper noun databases
        self.COUNTRIES = {
            'colombia', 'venezuela', 'brazil', 'argentina', 'mexico', 'spain', 'peru', 'chile',
            'ecuador', 'bolivia', 'paraguay', 'uruguay', 'guyana', 'suriname', 'panama',
            'costa rica', 'nicaragua', 'honduras', 'guatemala', 'belize', 'el salvador',
            'united states', 'usa', 'america', 'canada', 'germany', 'france', 'italy', 'china',
            'japan', 'australia', 'india', 'south africa', 'south america', 'north america', 'russia', 'ukraine', 'poland',
            'netherlands', 'belgium', 'switzerland', 'austria', 'portugal', 'greece', 'turkey',
            'egypt', 'morocco', 'nigeria', 'kenya', 'ghana', 'ethiopia', 'south korea',
            'thailand', 'vietnam', 'philippines', 'indonesia', 'malaysia', 'singapore',
            'united kingdom', 'england', 'scotland', 'wales', 'ireland', 'norway', 'sweden',
            'denmark', 'finland', 'iceland', 'czechia', 'hungary', 'romania', 'bulgaria',
            'croatia', 'serbia', 'bosnia', 'albania', 'montenegro', 'macedonia', 'slovenia'
        }
        
        self.CITIES = {
            'bogotá', 'medellín', 'cali', 'barranquilla', 'cartagena', 'bucaramanga', 'pereira',
            'ibagué', 'santa marta', 'villavicencio', 'manizales', 'neiva', 'soledad',
            'madrid', 'barcelona', 'valencia', 'seville', 'bilbao', 'málaga', 'zaragoza',
            'mexico city', 'guadalajara', 'monterrey', 'puebla', 'tijuana', 'león', 'juárez',
            'buenos aires', 'córdoba', 'rosario', 'mendoza', 'la plata', 'mar del plata',
            'lima', 'arequipa', 'trujillo', 'chiclayo', 'piura', 'iquitos', 'cusco',
            'santiago', 'valparaíso', 'concepción', 'la serena', 'antofagasta', 'temuco',
            'quito', 'guayaquil', 'cuenca', 'ambato', 'manta', 'portoviejo', 'machala',
            'new york', 'los angeles', 'chicago', 'houston', 'phoenix', 'philadelphia',
            'san antonio', 'san diego', 'dallas', 'san jose', 'austin', 'jacksonville',
            'london', 'manchester', 'birmingham', 'glasgow', 'liverpool', 'bristol', 'leeds',
            'paris', 'marseille', 'lyon', 'toulouse', 'nice', 'nantes', 'strasbourg',
            'berlin', 'hamburg', 'munich', 'cologne', 'frankfurt', 'stuttgart', 'düsseldorf',
            'rome', 'milan', 'naples', 'turin', 'palermo', 'genoa', 'bologna', 'florence',
            'tokyo', 'osaka', 'yokohama', 'nagoya', 'sapporo', 'kobe', 'kyoto', 'fukuoka',
            'beijing', 'shanghai', 'guangzhou', 'shenzhen', 'tianjin', 'wuhan', 'chengdu',
            'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide', 'canberra', 'darwin',
            'mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai', 'kolkata', 'pune',
            'toronto', 'montreal', 'vancouver', 'calgary', 'edmonton', 'ottawa', 'winnipeg'
        }
        
        self.PERSONAL_NAMES = {
            'miguel', 'carlos', 'jose', 'maría', 'ana', 'luis', 'pedro', 'juan', 'diego',
            'sofia', 'alejandro', 'roberto', 'fernando', 'daniel', 'david', 'francisco',
            'javier', 'rafael', 'antonio', 'manuel', 'ricardo', 'andrés', 'gabriel',
            'santiago', 'sebastián', 'nicolás', 'camilo', 'pablo', 'jorge', 'eduardo',
            'adriana', 'carolina', 'natalia', 'andrea', 'paola', 'laura', 'claudia',
            'martha', 'lucía', 'isabel', 'patricia', 'mónica', 'beatriz', 'gloria',
            'cristina', 'alejandra', 'verónica', 'teresa', 'silvia', 'rosa', 'elena',
            'john', 'michael', 'william', 'james', 'robert', 'david', 'richard', 'thomas',
            'christopher', 'daniel', 'matthew', 'anthony', 'mark', 'donald', 'steven',
            'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan',
            'jessica', 'sarah', 'karen', 'nancy', 'lisa', 'betty', 'helen', 'sandra',
            'pierre', 'jean', 'michel', 'philippe', 'alain', 'patrick', 'nicolas',
            'marie', 'nathalie', 'isabelle', 'sylvie', 'catherine', 'françoise',
            'antonio', 'francesco', 'giuseppe', 'marco', 'alessandro', 'matteo',
            'anna', 'giulia', 'francesca', 'chiara', 'sara', 'valentina', 'elena'
        }
        
        # Multi-word proper nouns that need special handling
        self.MULTI_WORD_PROPER_NOUNS = {
            'united states': 'United States',
            'united kingdom': 'United Kingdom',
            'new york': 'New York',
            'los angeles': 'Los Angeles',
            'san francisco': 'San Francisco',
            'costa rica': 'Costa Rica',
            'puerto rico': 'Puerto Rico',
            'south africa': 'South Africa',
            'south america': 'South America',
            'north america': 'North America',
            'south korea': 'South Korea',
            'north korea': 'North Korea',
            'new zealand': 'New Zealand',
            'saudi arabia': 'Saudi Arabia',
            'buenos aires': 'Buenos Aires',
            'mexico city': 'Mexico City',
            'río de janeiro': 'Río de Janeiro',
            'são paulo': 'São Paulo',
            'santa fe': 'Santa Fe',
            'mar del plata': 'Mar del Plata',
            'la paz': 'La Paz',
            'la plata': 'La Plata'
        }
        
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
    
    def enhance_proper_nouns(self, text: str) -> str:
        """
        Enhance proper noun capitalization throughout the text.
        This is critical for fixing issues like 'colombia' -> 'Colombia'.
        """
        if not text:
            return text
            
        # First handle multi-word proper nouns (they take priority)
        enhanced_text = text
        for original, proper in self.MULTI_WORD_PROPER_NOUNS.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(original.lower()) + r'\b'
            enhanced_text = re.sub(pattern, proper, enhanced_text, flags=re.IGNORECASE)
        
        # Split into words for individual processing
        words = enhanced_text.split()
        enhanced_words = []
        
        for word in words:
            # Clean the word of punctuation for checking
            clean_word = re.sub(r'[^\w\u00c0-\u017f]', '', word).lower()
            
            if not clean_word:
                enhanced_words.append(word)
                continue
            
            # Check if it's a proper noun that needs capitalization
            is_proper_noun = (clean_word in self.COUNTRIES or 
                            clean_word in self.CITIES or 
                            clean_word in self.PERSONAL_NAMES)
            
            if is_proper_noun:
                # Preserve the original punctuation but capitalize the word
                if clean_word in self.PERSONAL_NAMES:
                    # For names, capitalize first letter
                    enhanced_word = word[0].upper() + word[1:] if word else word
                else:
                    # For countries and cities, handle special characters properly
                    enhanced_word = self._capitalize_preserving_punctuation(word)
                enhanced_words.append(enhanced_word)
            else:
                enhanced_words.append(word)
        
        return ' '.join(enhanced_words)
    
    def _capitalize_preserving_punctuation(self, word: str) -> str:
        """Capitalize a word while preserving punctuation and special characters."""
        if not word:
            return word
            
        # Find the first alphabetic character
        for i, char in enumerate(word):
            if char.isalpha():
                return word[:i] + char.upper() + word[i+1:]
        
        return word

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
    
    def advanced_sentence_splitting(self, text: str) -> List[str]:
        """
        Advanced sentence boundary detection for speech-to-text processing.
        Handles run-on sentences and natural speech patterns.
        """
        if not text or not text.strip():
            return []
            
        # If text already has proper punctuation, use it
        if re.search(r'[.!?]', text):
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return [s.strip() for s in sentences if s.strip()]
        
        # For raw speech-to-text without punctuation, use advanced heuristics
        words = text.split()
        if len(words) <= 12:
            # Short segments, treat as single sentence
            return [text]
        
        sentences = []
        current_sentence = []
        
        # Enhanced sentence boundary indicators
        strong_sentence_starters = {
            'and then', 'but then', 'so then', 'now', 'then', 'meanwhile', 'however',
            'therefore', 'furthermore', 'additionally', 'moreover', 'nevertheless',
            'consequently', 'thus', 'hence', 'accordingly', 'similarly', 'likewise'
        }
        
        strong_single_starters = {
            'and', 'but', 'so', 'then', 'however', 'therefore', 'furthermore',
            'meanwhile', 'additionally', 'moreover', 'nevertheless', 'consequently'
        }
        
        topic_change_indicators = {
            'anyway', 'speaking of', 'by the way', 'incidentally', 'moving on',
            'getting back to', 'as i was saying', 'another thing', 'also'
        }
        
        question_starters = {
            'what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose',
            'is', 'are', 'do', 'does', 'did', 'can', 'could', 'would', 'should',
            'will', 'have', 'has', 'had'
        }
        
        for i, word in enumerate(words):
            current_sentence.append(word)
            
            # Check for natural sentence boundaries
            is_boundary = False
            
            # Check for multi-word starters
            if i < len(words) - 1:
                two_word_phrase = f"{word.lower()} {words[i+1].lower()}"
                if two_word_phrase in strong_sentence_starters and len(current_sentence) >= 8:
                    is_boundary = True
            
            if not is_boundary and i < len(words) - 1:
                next_word = words[i + 1].lower()
                
                # Strong single-word boundary indicators
                if (len(current_sentence) >= 10 and next_word in strong_single_starters):
                    is_boundary = True
                
                # Topic change indicators
                elif (len(current_sentence) >= 8 and next_word in topic_change_indicators):
                    is_boundary = True
                
                # Question boundaries - when we detect question patterns
                elif (len(current_sentence) >= 6 and next_word in question_starters):
                    is_boundary = True
                
                # Natural pause indicators - speech patterns that suggest boundaries
                elif (len(current_sentence) >= 15 and 
                      next_word in {'well', 'actually', 'basically', 'essentially', 'you know'}):
                    is_boundary = True
            
            # Force boundary for very long sentences
            if len(current_sentence) >= 25:
                is_boundary = True
            
            # Create sentence boundary
            if is_boundary and len(current_sentence) >= 6:  # Minimum sentence length
                sentences.append(' '.join(current_sentence))
                current_sentence = []
        
        # Add remaining words
        if current_sentence:
            sentences.append(' '.join(current_sentence))
        
        return sentences
    
    def comprehensive_format(self, text: str) -> str:
        """
        Comprehensive text formatting using all enhancement techniques.
        This is the main formatting method that combines all improvements.
        """
        if not text or not text.strip():
            return text
            
        logger.info("Applying comprehensive text formatting...")
        
        # Step 1: Basic cleanup and normalization
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        
        # Step 2: Advanced sentence boundary detection
        sentences = self.advanced_sentence_splitting(cleaned_text)
        
        # Step 3: Process each sentence individually
        formatted_sentences = []
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # Clean spacing within sentence
            sentence = ' '.join(sentence.split())
            
            # Step 4: Proper noun capitalization (CRITICAL)
            sentence = self.enhance_proper_nouns(sentence)
            
            # Step 5: Sentence capitalization
            if sentence:
                # Always capitalize the first letter of each sentence
                first_char_idx = 0
                # Find the first alphabetic character
                for i, char in enumerate(sentence):
                    if char.isalpha():
                        first_char_idx = i
                        break
                
                if first_char_idx < len(sentence) and not sentence[first_char_idx].isupper():
                    sentence = sentence[:first_char_idx] + sentence[first_char_idx].upper() + sentence[first_char_idx+1:]
            
            # Step 6: Intelligent punctuation
            sentence = self._add_enhanced_punctuation(sentence)
            
            formatted_sentences.append(sentence)
        
        # Step 7: Final combination and validation
        result = ' '.join(formatted_sentences)
        
        # Step 8: Final polishing
        result = self._final_polish(result)
        
        logger.info("Comprehensive formatting completed")
        return result
    
    def _add_enhanced_punctuation(self, sentence: str) -> str:
        """
        Enhanced punctuation addition with better question and statement detection.
        """
        if not sentence:
            return sentence
            
        sentence = sentence.strip()
        
        # If already has punctuation, keep it
        if sentence and sentence[-1] in '.!?':
            return sentence
        
        # Enhanced question detection
        sentence_lower = sentence.lower()
        words = sentence_lower.split()
        
        # Direct question words at the beginning
        question_starters = ['what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose']
        if words and words[0] in question_starters:
            return sentence + '?'
        
        # Question auxiliary verbs at the beginning
        question_aux = ['is', 'are', 'do', 'does', 'did', 'can', 'could', 'would', 
                       'should', 'will', 'have', 'has', 'had', 'may', 'might']
        if words and words[0] in question_aux:
            return sentence + '?'
        
        # Question phrases that indicate interrogative sentences
        question_patterns = [
            'is it', 'are you', 'do you', 'did you', 'can you', 'will you',
            'would you', 'have you', 'could you', 'should you', 'are we',
            'do we', 'can we', 'how do', 'how are', 'what do', 'what are'
        ]
        
        for pattern in question_patterns:
            if pattern in sentence_lower:
                return sentence + '?'
        
        # Exclamatory indicators
        exclamatory_words = ['wow', 'amazing', 'incredible', 'unbelievable', 
                           'fantastic', 'great', 'excellent', 'wonderful', 
                           'terrible', 'awful', 'horrible']
        if any(word in sentence_lower for word in exclamatory_words):
            return sentence + '!'
        
        # Emphatic statements
        if any(word in sentence_lower for word in ['very', 'really', 'extremely', 'absolutely']):
            # Check if it feels like an emphatic statement
            emphatic_contexts = ['very good', 'really good', 'extremely important', 
                               'absolutely right', 'very important', 'really important']
            if any(context in sentence_lower for context in emphatic_contexts):
                return sentence + '!'
        
        # Default to period
        return sentence + '.'
    
    def _final_polish(self, text: str) -> str:
        """
        Final polishing of the formatted text.
        """
        if not text:
            return text
        
        # Fix multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.!?])', r'\1', text)
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
        
        # Ensure proper spacing after sentences
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        return text.strip()

    def format_segment_text(self, text: str) -> str:
        """
        Format a single segment of raw transcribed text before combination.
        This is crucial for handling raw Whisper output which often lacks formatting.
        Uses comprehensive formatting to fix proper nouns and sentence structure.
        """
        if not text or not text.strip():
            return text
        
        logger.info("Formatting segment text with comprehensive processor...")
        
        # Use the comprehensive formatter for segment-level processing
        return self.comprehensive_format(text)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split raw text into sentences based on natural speech patterns.
        Handles common speech patterns where Whisper doesn't add punctuation.
        """
        # First, try to split on existing punctuation
        if re.search(r'[.!?]', text):
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return [s.strip() for s in sentences if s.strip()]
        
        # If no punctuation, split on speech pattern indicators
        words = text.split()
        if len(words) <= 15:
            # Short segment, treat as one sentence
            return [text]
        
        sentences = []
        current_sentence = []
        
        # Strong sentence boundary indicators - these strongly suggest a new sentence
        strong_starters = {
            'and', 'but', 'so', 'now', 'then', 'however', 'therefore',
            'meanwhile', 'furthermore', 'additionally', 'moreover'
        }
        
        # Weaker indicators that might suggest a boundary in longer sentences
        weak_starters = {
            'well', 'actually', 'basically', 'essentially', 'obviously', 
            'clearly', 'definitely', 'i', 'you', 'we', 'they', 'he', 'she', 'it'
        }
        
        for i, word in enumerate(words):
            current_sentence.append(word)
            
            # Check for sentence boundary indicators
            is_potential_boundary = False
            
            # Strong boundary: Long sentences with strong connectors
            if (len(current_sentence) >= 12 and 
                i < len(words) - 1 and 
                words[i + 1].lower() in strong_starters):
                is_potential_boundary = True
            
            # Medium boundary: Very long sentences with weak indicators  
            elif (len(current_sentence) >= 20 and 
                  i < len(words) - 1 and
                  words[i + 1].lower() in weak_starters):
                is_potential_boundary = True
            
            # Force split for extremely long sentences
            elif len(current_sentence) >= 30:
                is_potential_boundary = True
            
            # Natural question boundary - look for question patterns
            elif (len(current_sentence) >= 8 and 
                  i < len(words) - 2 and
                  words[i + 1].lower() in {'what', 'why', 'how', 'when', 'where', 'who', 'which'}):
                is_potential_boundary = True
            
            if is_potential_boundary and len(current_sentence) >= 8:
                sentences.append(' '.join(current_sentence))
                current_sentence = []
        
        # Add remaining words as final sentence
        if current_sentence:
            sentences.append(' '.join(current_sentence))
        
        return sentences
    
    def _add_punctuation(self, sentence: str) -> str:
        """
        Add appropriate punctuation to a sentence based on content and structure.
        """
        if not sentence:
            return sentence
            
        sentence = sentence.strip()
        
        # If already has punctuation, keep it
        if sentence and sentence[-1] in '.!?':
            return sentence
        
        # Check for question indicators
        question_words = ['what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose']
        question_phrases = [
            'is it', 'are you', 'do you', 'did you', 'can you', 'will you', 'would you',
            'have you', 'could you', 'should you', 'are we', 'do we', 'can we'
        ]
        
        sentence_lower = sentence.lower()
        words = sentence_lower.split()
        
        # Strong question indicators - starts with question word
        if words and words[0] in question_words:
            return sentence + '?'
        
        # Question phrases anywhere in the sentence
        if any(phrase in sentence_lower for phrase in question_phrases):
            return sentence + '?'
        
        # Question pattern: ends with personal pronouns (common in questions)
        if len(words) >= 3 and words[-1] in ['you', 'we', 'they', 'it']:
            # Check if it might be a question based on structure
            if any(qw in words for qw in ['do', 'can', 'will', 'would', 'should', 'could']):
                return sentence + '?'
        
        # Check for exclamatory content
        exclamatory_words = ['wow', 'amazing', 'incredible', 'unbelievable', 'fantastic', 'great', 'excellent']
        if any(word in sentence_lower for word in exclamatory_words):
            return sentence + '!'
        
        # Default to period
        return sentence + '.'

    def format_text(self, text: str) -> str:
        """
        Enhanced text formatting with better sentence detection and punctuation handling.
        This method is used for final cleanup of combined text and uses comprehensive formatting.
        """
        if not text or not text.strip():
            return text
            
        logger.info("Applying final text formatting with comprehensive processor...")
        
        # Use comprehensive formatting for final cleanup as well
        return self.comprehensive_format(text)

    def process_transcript(self, text: str) -> str:
        """
        Process the full transcript with enhanced handling of long texts.
        Uses comprehensive formatting for consistent quality throughout.
        """
        logger.info("Starting comprehensive transcript processing")
        
        # For comprehensive processing, we can handle the full text more intelligently
        if len(text) <= self.max_chunk_size:
            # Small enough to process as a whole
            logger.info("Processing transcript as single unit")
            return self.comprehensive_format(text)
        
        # Split into manageable chunks for very large texts
        chunks = self.split_into_chunks(text)
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} with comprehensive formatting")
            
            # Apply comprehensive formatting to each chunk
            processed_chunk = self.comprehensive_format(chunk)
            processed_chunks.append(processed_chunk)
        
        # Combine processed chunks
        final_text = ' '.join(processed_chunks)
        
        # Final polishing pass to ensure consistency across chunk boundaries
        final_text = self._final_polish(final_text)
        
        logger.info("Comprehensive transcript processing completed")
        return final_text


# Maintain backward compatibility
TextProcessor = EnhancedTextProcessor