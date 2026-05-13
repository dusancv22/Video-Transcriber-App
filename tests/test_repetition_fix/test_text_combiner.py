"""
Tests for TextCombiner class for intelligent segment merging.
"""

import time

import pytest

from src.post_processing.combiner import TextCombiner


class TestTextCombiner:
    """Test TextCombiner functionality for intelligent segment merging."""

    def setup_method(self):
        """Set up test environment."""
        self.combiner = TextCombiner()

    def test_combines_segments_without_repetition(self):
        """Test that segments are combined without creating repetition."""
        segments = [
            "Hello everyone and welcome to our presentation today.",
            "welcome to our presentation today. We'll be discussing",
            "We'll be discussing the latest developments in technology."
        ]

        result = self.combiner.combine_overlapping_segments(segments)

        assert result == (
            "Hello everyone and welcome to our presentation today. "
            "We'll be discussing the latest developments in technology."
        )
        assert self.combiner.get_deduplication_stats()["overlaps_detected"] == 2

    def test_identifies_overlap_regions(self):
        """Test that overlapping regions between segments are removed."""
        segments = [
            "The quick brown fox jumps over the lazy dog.",
            "fox jumps over the lazy dog. The end of the story.",
            "The end of the story. Thank you for listening."
        ]

        result = self.combiner.combine_overlapping_segments(segments)

        assert result == (
            "The quick brown fox jumps over the lazy dog. "
            "The end of the story. Thank you for listening."
        )
        assert self.combiner.get_deduplication_stats()["words_removed"] == 11

    def test_preserves_punctuation_during_merge(self):
        """Test that punctuation is preserved correctly during segment merging."""
        segments = [
            "Hello, how are you today?",
            "how are you today? I'm doing well, thank you.",
            "doing well, thank you. Have a great day!"
        ]

        result = self.combiner.combine_overlapping_segments(segments)

        assert result == "Hello, how are you today? I'm doing well, thank you. Have a great day!"

    def test_handles_no_overlap_segments(self):
        """Test handling of segments with no overlap."""
        segments = [
            "First sentence is complete.",
            "Second sentence starts fresh.",
            "Third sentence is independent."
        ]

        result = self.combiner.combine_overlapping_segments(segments)

        assert result == (
            "First sentence is complete. "
            "Second sentence starts fresh. "
            "Third sentence is independent."
        )
        assert self.combiner.get_deduplication_stats()["overlaps_detected"] == 0

    def test_similarity_threshold_configuration(self):
        """Test that similarity threshold controls fuzzy overlap detection."""
        segments = [
            "Thank you for watching this video.",
            "Thanks for watching this video today."
        ]

        strict_combiner = TextCombiner(similarity_threshold=0.95)
        lenient_combiner = TextCombiner(similarity_threshold=0.7)

        strict_combiner.combine_overlapping_segments(segments)
        lenient_combiner.combine_overlapping_segments(segments)

        assert strict_combiner.get_deduplication_stats()["overlaps_detected"] == 0
        assert lenient_combiner.get_deduplication_stats()["overlaps_detected"] == 1

    def test_minimum_overlap_length_configuration(self):
        """Test that minimum overlap length controls which overlaps are removed."""
        segments = [
            "Hello world and good morning.",
            "and good morning everyone here today.",
            "everyone here today for this special event."
        ]

        strict_combiner = TextCombiner(min_overlap_words=4)
        lenient_combiner = TextCombiner(min_overlap_words=3)

        strict_combiner.combine_overlapping_segments(segments)
        lenient_combiner.combine_overlapping_segments(segments)

        assert strict_combiner.get_deduplication_stats()["overlaps_detected"] == 0
        assert lenient_combiner.get_deduplication_stats()["overlaps_detected"] == 2


class TestTextCombinerAlgorithms:
    """Test text combination behavior at word boundaries."""

    def setup_method(self):
        """Set up test environment."""
        self.combiner = TextCombiner()

    def test_word_level_overlap_detection(self):
        """Test overlap detection at word boundaries."""
        segments = [
            "The meeting will start at nine",
            "start at nine o'clock sharp",
            "at nine o'clock sharp this morning"
        ]

        result = self.combiner.combine_overlapping_segments(segments)

        assert result == "The meeting will start at nine o'clock sharp this morning"
        assert self.combiner.get_deduplication_stats()["overlaps_detected"] == 2


class TestTextCombinerErrorHandling:
    """Test error handling in TextCombiner."""

    def setup_method(self):
        """Set up test environment."""
        self.combiner = TextCombiner()

    def test_empty_segments_list(self):
        """Test handling of empty segments list."""
        result = self.combiner.combine_overlapping_segments([])
        assert result == ""

    def test_single_segment(self):
        """Test handling of single segment."""
        result = self.combiner.combine_overlapping_segments(["This is the only segment."])
        assert result == "This is the only segment."


class TestTextCombinerIntegration:
    """Integration tests for TextCombiner with segment metadata."""

    def setup_method(self):
        """Set up test environment."""
        self.combiner = TextCombiner()

    def test_integration_with_audio_splitter_overlaps(self):
        """Test integration with audio splitter overlap metadata."""
        segments = [
            "In this video, we will explore the fascinating world of machine learning",
            "explore the fascinating world of machine learning and its applications in modern technology.",
            "and its applications in modern technology. Let's start with the basics."
        ]

        result = self.combiner.combine_overlapping_segments(
            segments,
            segment_metadata=[
                {"has_start_overlap": False},
                {"has_start_overlap": True},
                {"has_start_overlap": True},
            ],
            overlap_seconds=2.5
        )

        assert result == (
            "In this video, we will explore the fascinating world of machine learning "
            "and its applications in modern technology. Let's start with the basics."
        )
        assert self.combiner.get_deduplication_stats()["overlaps_detected"] == 2

    def test_performance_with_large_segment_count(self):
        """Test performance with many segments from long audio files."""
        segments = [f"This is segment number {i} of the transcription." for i in range(100)]

        start_time = time.time()
        result = self.combiner.combine_overlapping_segments(segments)
        processing_time = time.time() - start_time

        assert len(result) > 0
        assert processing_time < 5.0


# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.repetition_fix,
    pytest.mark.text_combining
]
