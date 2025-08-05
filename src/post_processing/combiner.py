import re
import difflib
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TextCombiner:
    """
    Intelligently combines text segments with overlap removal to handle overlapping content
    from audio segments while preserving meaning and sentence structure.
    """
    
    def __init__(self, min_overlap_words: int = 3, similarity_threshold: float = 0.8):
        """
        Initialize the TextCombiner.
        
        Args:
            min_overlap_words: Minimum number of words to consider for overlap detection
            similarity_threshold: Similarity threshold for considering text as duplicate (0.0-1.0)
        """
        self.min_overlap_words = min_overlap_words
        self.similarity_threshold = similarity_threshold
        self.deduplication_stats = {
            'segments_processed': 0,
            'overlaps_detected': 0,
            'words_removed': 0,
            'total_overlap_duration': 0.0
        }
        
    def combine_overlapping_segments(
        self, 
        segments: List[str], 
        segment_metadata: Optional[List[Dict[str, Any]]] = None,
        overlap_seconds: float = 2.5
    ) -> str:
        """
        Intelligently combine text segments with overlap removal.
        
        Args:
            segments: List of text segments to combine
            segment_metadata: Optional metadata about segments including overlap information
            overlap_seconds: Expected overlap duration (for logging/stats)
            
        Returns:
            str: Combined text with overlapping content removed
        """
        if not segments:
            return ""
            
        if len(segments) == 1:
            return segments[0]
            
        logger.info(f"Starting text combination for {len(segments)} segments")
        print(f"\nCombining {len(segments)} text segments with overlap removal...")
        
        # Reset stats for this operation
        self.deduplication_stats = {
            'segments_processed': len(segments),
            'overlaps_detected': 0,
            'words_removed': 0,
            'total_overlap_duration': overlap_seconds * (len(segments) - 1) if segment_metadata else 0.0
        }
        
        combined_text = segments[0]
        
        for i in range(1, len(segments)):
            current_segment = segments[i]
            
            # Check if this segment should have overlap based on metadata
            has_expected_overlap = True
            if segment_metadata and i < len(segment_metadata):
                has_expected_overlap = segment_metadata[i].get('has_start_overlap', True)
            
            if has_expected_overlap:
                print(f"Processing segment {i+1}/{len(segments)} - checking for overlap...")
                merged_text = self._merge_segments_with_overlap_removal(
                    combined_text, 
                    current_segment,
                    segment_index=i
                )
                combined_text = merged_text
            else:
                print(f"Processing segment {i+1}/{len(segments)} - no overlap expected, appending...")
                combined_text = self._simple_append(combined_text, current_segment)
        
        # Log final statistics
        self._log_deduplication_stats()
        
        return combined_text
    
    def _merge_segments_with_overlap_removal(
        self, 
        text1: str, 
        text2: str,
        segment_index: int = 0
    ) -> str:
        """
        Merge two text segments by detecting and removing overlapping content.
        
        Args:
            text1: First text segment (already processed)
            text2: Second text segment (new segment to merge)
            segment_index: Index of the segment being processed (for logging)
            
        Returns:
            str: Merged text with overlap removed
        """
        # Get the tail of text1 and head of text2 for overlap detection
        text1_words = text1.split()
        text2_words = text2.split()
        
        # Look for overlap in the last portion of text1 and first portion of text2
        max_overlap_length = min(len(text1_words), len(text2_words), 50)  # Limit search to 50 words
        
        best_overlap_length = 0
        best_similarity = 0.0
        
        # Search for the best overlap match
        for overlap_length in range(self.min_overlap_words, max_overlap_length + 1):
            text1_tail = ' '.join(text1_words[-overlap_length:])
            text2_head = ' '.join(text2_words[:overlap_length])
            
            # Calculate similarity
            similarity = self._calculate_text_similarity(text1_tail, text2_head)
            
            if similarity > self.similarity_threshold and similarity > best_similarity:
                best_similarity = similarity
                best_overlap_length = overlap_length
        
        if best_overlap_length > 0:
            # Found overlap - merge by removing duplicate content
            print(f"  Overlap detected: {best_overlap_length} words ({best_similarity:.2f} similarity)")
            
            # Keep text1 as is, but skip the overlapping portion in text2
            remaining_text2 = ' '.join(text2_words[best_overlap_length:])
            
            # Update statistics
            self.deduplication_stats['overlaps_detected'] += 1
            self.deduplication_stats['words_removed'] += best_overlap_length
            
            # Merge with proper spacing
            merged_text = self._smart_concatenate(text1, remaining_text2)
            
            logger.info(f"Segment {segment_index}: Removed {best_overlap_length} overlapping words")
            
        else:
            # No significant overlap found - simple append
            print(f"  No significant overlap detected - appending segment")
            merged_text = self._simple_append(text1, text2)
        
        return merged_text
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text segments using sequence matching.
        
        Args:
            text1: First text segment
            text2: Second text segment
            
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts for comparison
        normalized1 = self._normalize_text_for_comparison(text1)
        normalized2 = self._normalize_text_for_comparison(text2)
        
        # Use difflib for sequence matching
        matcher = difflib.SequenceMatcher(None, normalized1, normalized2)
        return matcher.ratio()
    
    def _normalize_text_for_comparison(self, text: str) -> str:
        """
        Normalize text for comparison by removing punctuation and extra spaces.
        
        Args:
            text: Text to normalize
            
        Returns:
            str: Normalized text
        """
        # Convert to lowercase and remove extra whitespace
        text = re.sub(r'\s+', ' ', text.lower().strip())
        
        # Remove punctuation but keep word boundaries
        text = re.sub(r'[^\w\s]', '', text)
        
        return text
    
    def _smart_concatenate(self, text1: str, text2: str) -> str:
        """
        Intelligently concatenate two text segments with proper spacing and punctuation.
        
        Args:
            text1: First text segment
            text2: Second text segment
            
        Returns:
            str: Properly concatenated text
        """
        if not text1:
            return text2
        if not text2:
            return text1
        
        text1 = text1.rstrip()
        text2 = text2.lstrip()
        
        # For overlapping segments, we generally want a simple connection
        # without adding extra punctuation, as the overlap removal should
        # have created a natural flow
        
        if text1 and text2:
            # Simple space connection - let the text processor handle formatting later
            return f"{text1} {text2}"
        
        return f"{text1} {text2}"
    
    def _should_add_sentence_break(self, text1: str, text2: str) -> bool:
        """
        Determine if a sentence break should be added between two text segments.
        
        Args:
            text1: First text segment
            text2: Second text segment
            
        Returns:
            bool: True if a sentence break should be added
        """
        if not text1 or not text2:
            return False
        
        # Get last few words of text1 and first few words of text2
        text1_words = text1.split()
        text2_words = text2.split()
        
        if len(text1_words) < 3 or len(text2_words) < 3:
            return False
        
        # Check if they seem to be different topics/sentences
        last_words = ' '.join(text1_words[-3:]).lower()
        first_words = ' '.join(text2_words[:3]).lower()
        
        # Simple heuristic: if the segments don't share common words, likely different sentences
        last_word_set = set(last_words.split())
        first_word_set = set(first_words.split())
        
        common_words = last_word_set.intersection(first_word_set)
        return len(common_words) == 0
    
    def _simple_append(self, text1: str, text2: str) -> str:
        """
        Simple append operation with proper spacing.
        
        Args:
            text1: First text segment
            text2: Second text segment
            
        Returns:
            str: Combined text
        """
        if not text1:
            return text2
        if not text2:
            return text1
        
        return f"{text1.rstrip()} {text2.lstrip()}"
    
    def _log_deduplication_stats(self):
        """Log statistics about the deduplication process."""
        stats = self.deduplication_stats
        
        print(f"\nText combination completed:")
        print(f"  Segments processed: {stats['segments_processed']}")
        print(f"  Overlaps detected: {stats['overlaps_detected']}")
        print(f"  Words deduplicated: {stats['words_removed']}")
        if stats['total_overlap_duration'] > 0:
            print(f"  Total overlap duration: {stats['total_overlap_duration']:.1f}s")
        
        logger.info(
            f"Text deduplication completed: {stats['overlaps_detected']} overlaps detected, "
            f"{stats['words_removed']} words removed from {stats['segments_processed']} segments"
        )
    
    def get_deduplication_stats(self) -> Dict[str, Any]:
        """
        Get statistics from the last deduplication operation.
        
        Returns:
            Dict containing deduplication statistics
        """
        return self.deduplication_stats.copy()