"""
Advanced Text Processor for Transcript Post-Processing
This module provides comprehensive text cleaning and formatting for transcribed audio.
"""

import re
from typing import List, Tuple, Set, Optional
import logging

logger = logging.getLogger(__name__)


class AdvancedTextProcessor:
    """
    Advanced text processor that removes filler words, adds proper punctuation,
    formats paragraphs, and improves overall readability of transcripts.
    """
    
    def __init__(self, remove_fillers: bool = True, aggressive_cleaning: bool = True):
        """
        Initialize the advanced text processor.
        
        Args:
            remove_fillers: Whether to remove filler words
            aggressive_cleaning: Whether to apply aggressive text cleaning
        """
        self.remove_fillers = remove_fillers
        self.aggressive_cleaning = aggressive_cleaning
        
        # Common filler words and phrases to remove
        self.filler_words = {
            'um', 'uh', 'umm', 'uhh', 'er', 'ah', 'eh', 'mm', 'hmm',
            'you know', 'i mean', 'you see', 'sort of', 'kind of', 
            'basically', 'actually', 'literally', 'like i said',
            'to be honest', 'honestly', 'i guess', 'i suppose',
            'or something', 'or whatever', 'and stuff', 'and things',
            'you know what i mean', 'know what i mean', 'if you will'
        }
        
        # Words that should always be capitalized
        self.proper_nouns = {
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
            'september', 'october', 'november', 'december',
            'america', 'american', 'english', 'british', 'chinese', 'google', 'microsoft',
            'apple', 'amazon', 'facebook', 'twitter', 'youtube', 'instagram'
        }
        
        # Common abbreviations that should be uppercase
        # Note: Removed 'it' as it's commonly used as a pronoun
        self.abbreviations = {
            'usa', 'uk', 'eu', 'ai', 'ml', 'api', 'url', 'html', 'css', 'js',
            'pdf', 'jpg', 'png', 'mp3', 'mp4', 'cpu', 'gpu', 'ram', 'ssd',
            'ceo', 'cto', 'cfo', 'hr', 'pr', 'faq', 'diy', 'eta', 'fyi', 'asap'
        }
        
    def process_transcript(self, text: str) -> str:
        """
        Main processing function that applies all improvements to the transcript.
        
        Args:
            text: Raw transcript text
            
        Returns:
            Cleaned and formatted transcript
        """
        logger.info("Starting advanced transcript processing")
        print("\nApplying advanced post-processing...")
        
        # Step 1: Basic cleaning
        text = self._basic_cleaning(text)
        
        # Step 2: Remove filler words if enabled
        if self.remove_fillers:
            text = self._remove_filler_words(text)
        
        # Step 3: Fix sentence structure
        text = self._fix_sentence_structure(text)
        
        # Step 4: Add proper punctuation
        text = self._add_smart_punctuation(text)
        
        # Step 5: Fix capitalization
        text = self._fix_capitalization(text)
        
        # Step 6: Create paragraphs
        text = self._create_paragraphs(text)
        
        # Step 7: Final polish
        text = self._final_polish(text)
        
        logger.info("Advanced transcript processing completed")
        return text
    
    def _basic_cleaning(self, text: str) -> str:
        """
        Perform basic text cleaning.
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Fix common transcription artifacts
        text = re.sub(r'\[.*?\]', '', text)  # Remove brackets content
        text = re.sub(r'\(.*?\)', '', text)  # Remove parentheses content
        
        return text
    
    def _remove_filler_words(self, text: str) -> str:
        """
        Remove common filler words while preserving sentence meaning.
        """
        logger.info("Removing filler words")
        
        # Convert to lowercase for comparison
        words = text.split()
        cleaned_words = []
        i = 0
        
        while i < len(words):
            # Check for multi-word fillers
            found_filler = False
            
            # Check 4-word phrases
            if i <= len(words) - 4:
                four_word = ' '.join(words[i:i+4]).lower().strip('.,!?')
                if four_word in self.filler_words:
                    i += 4
                    found_filler = True
            
            # Check 3-word phrases
            if not found_filler and i <= len(words) - 3:
                three_word = ' '.join(words[i:i+3]).lower().strip('.,!?')
                if three_word in self.filler_words:
                    i += 3
                    found_filler = True
            
            # Check 2-word phrases
            if not found_filler and i <= len(words) - 2:
                two_word = ' '.join(words[i:i+2]).lower().strip('.,!?')
                if two_word in self.filler_words:
                    i += 2
                    found_filler = True
            
            # Check single words
            if not found_filler:
                single_word = words[i].lower().strip('.,!?')
                if single_word in self.filler_words:
                    # Special case: keep "like" if it's used as a verb
                    if single_word == 'like' and i > 0:
                        prev_word = words[i-1].lower()
                        if prev_word in ['i', 'you', 'we', 'they', 'would', 'could', 'should']:
                            cleaned_words.append(words[i])
                    i += 1
                    found_filler = True
                else:
                    cleaned_words.append(words[i])
                    i += 1
        
        # Reconstruct text
        text = ' '.join(cleaned_words)
        
        # Clean up any double spaces created by removal
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _fix_sentence_structure(self, text: str) -> str:
        """
        Fix sentence structure and remove repetitions.
        """
        # Remove word repetitions (e.g., "the the" -> "the")
        text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
        
        # Fix common transcription errors
        text = re.sub(r'\bgonna\b', 'going to', text, flags=re.IGNORECASE)
        text = re.sub(r'\bwanna\b', 'want to', text, flags=re.IGNORECASE)
        text = re.sub(r'\bgotta\b', 'got to', text, flags=re.IGNORECASE)
        text = re.sub(r'\bkinda\b', 'kind of', text, flags=re.IGNORECASE)
        text = re.sub(r'\bcause\b', 'because', text, flags=re.IGNORECASE)
        
        return text
    
    def _add_smart_punctuation(self, text: str) -> str:
        """
        Add intelligent punctuation based on sentence patterns.
        """
        # Split into potential sentences (rough split)
        words = text.split()
        sentences = []
        current_sentence = []
        
        for i, word in enumerate(words):
            current_sentence.append(word)
            
            # Check if we should end the sentence
            should_end = False
            
            # End if we have enough words and find a natural break
            if len(current_sentence) > 8:  # Increased minimum from 5 to 8
                # Check for conjunctions that often start new sentences
                if i < len(words) - 1:
                    next_word = words[i + 1].lower()
                    if next_word in ['but', 'however', 'therefore', 'moreover', 'furthermore',
                                     'meanwhile', 'nevertheless', 'consequently', 'thus']:
                        should_end = True
                
                # Check for words that typically start sentences
                if i < len(words) - 1:
                    next_word = words[i + 1].lower()
                    # Be more conservative about breaking on pronouns
                    if next_word in ['he', 'she', 'we', 'they']:
                        # Only break if current sentence is quite long
                        if len(current_sentence) > 15:
                            should_end = True
                
                # End very long sentences
                if len(current_sentence) > 25:  # Increased from 20 to 25
                    should_end = True
            
            if should_end:
                sentence_text = ' '.join(current_sentence)
                
                # Add appropriate ending punctuation
                if not sentence_text[-1] in '.!?':
                    # Check if it's a question
                    first_word = current_sentence[0].lower() if current_sentence else ''
                    if first_word in ['what', 'why', 'how', 'when', 'where', 'who', 'which',
                                      'can', 'could', 'would', 'should', 'will', 'do', 'does',
                                      'did', 'is', 'are', 'was', 'were', 'have', 'has', 'had']:
                        sentence_text += '?'
                    else:
                        sentence_text += '.'
                
                sentences.append(sentence_text)
                current_sentence = []
        
        # Add remaining words as last sentence
        if current_sentence:
            sentence_text = ' '.join(current_sentence)
            if not sentence_text[-1] in '.!?':
                sentence_text += '.'
            sentences.append(sentence_text)
        
        # Join sentences
        text = ' '.join(sentences)
        
        # Add commas for better readability
        text = self._add_commas(text)
        
        return text
    
    def _add_commas(self, text: str) -> str:
        """
        Add commas for lists and natural pauses.
        """
        # Add commas before conjunctions in compound sentences
        text = re.sub(r'\s+(and|but|or|yet|so)\s+', r', \1 ', text)
        
        # Add commas after introductory phrases
        text = re.sub(r'^(However|Therefore|Moreover|Furthermore|Meanwhile|Nevertheless|Consequently|Thus)',
                      r'\1,', text, flags=re.MULTILINE)
        
        # Add commas in lists (simplified approach)
        # This is complex to do perfectly, so we'll be conservative
        
        # Fix any double commas
        text = re.sub(r',\s*,', ',', text)
        
        # Remove commas before periods
        text = re.sub(r',\.', '.', text)
        
        return text
    
    def _fix_capitalization(self, text: str) -> str:
        """
        Fix capitalization throughout the text.
        """
        sentences = re.split(r'([.!?]\s+)', text)
        result = []
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            
            # Capitalize first letter of sentence
            if sentence and not sentence[0].isupper():
                sentence = sentence[0].upper() + sentence[1:]
            
            # Capitalize 'I'
            sentence = re.sub(r'\bi\b', 'I', sentence)
            
            # Capitalize proper nouns
            words = sentence.split()
            for j, word in enumerate(words):
                word_lower = word.lower().strip('.,!?')
                
                # Check if it's a proper noun
                if word_lower in self.proper_nouns:
                    # Preserve punctuation
                    punctuation = ''
                    if word[-1] in '.,!?':
                        punctuation = word[-1]
                        word = word[:-1]
                    words[j] = word.capitalize() + punctuation
                
                # Check if it's an abbreviation (but be careful with context)
                if word_lower in self.abbreviations:
                    # Special handling for potential context-sensitive abbreviations
                    # For now, just uppercase known abbreviations
                    punctuation = ''
                    if word[-1] in '.,!?':
                        punctuation = word[-1]
                        word = word[:-1]
                    words[j] = word.upper() + punctuation
            
            sentence = ' '.join(words)
            result.append(sentence)
        
        return ''.join(result)
    
    def _create_paragraphs(self, text: str) -> str:
        """
        Create logical paragraphs from the text.
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if len(sentences) <= 3:
            return text
        
        paragraphs = []
        current_paragraph = []
        
        for i, sentence in enumerate(sentences):
            current_paragraph.append(sentence)
            
            # Create new paragraph every 3-5 sentences
            if len(current_paragraph) >= 3:
                # Look for natural paragraph breaks
                should_break = False
                
                # Check if next sentence starts with a transition word
                if i < len(sentences) - 1:
                    next_sentence = sentences[i + 1]
                    transition_words = ['However', 'Therefore', 'Moreover', 'Furthermore',
                                        'Meanwhile', 'In addition', 'On the other hand',
                                        'In conclusion', 'To summarize', 'First', 'Second',
                                        'Finally', 'Next', 'Then']
                    for word in transition_words:
                        if next_sentence.startswith(word):
                            should_break = True
                            break
                
                # Break after 5 sentences regardless
                if len(current_paragraph) >= 5:
                    should_break = True
                
                if should_break:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
        
        # Add remaining sentences
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        # Join paragraphs with double newline
        return '\n\n'.join(paragraphs)
    
    def _final_polish(self, text: str) -> str:
        """
        Final cleanup and polishing of the text.
        """
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        text = re.sub(r'([.,!?])([A-Z])', r'\1 \2', text)
        
        # Ensure single space after punctuation
        text = re.sub(r'([.,!?])\s+', r'\1 ', text)
        
        # Fix quotes if present
        text = re.sub(r'"\s+', '"', text)
        text = re.sub(r'\s+"', '"', text)
        
        # Remove any remaining double spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Ensure paragraphs are properly spaced
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()