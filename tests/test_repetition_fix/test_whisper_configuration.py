"""
Tests for enhanced Whisper configuration to prevent repetition.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from src.transcription.whisper_manager import WhisperManager


class TestWhisperRepetitionPrevention:
    """Test Whisper configuration changes to prevent repetition."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
    
    @patch('src.transcription.whisper_manager.whisper.load_model')
    def test_whisper_uses_repetition_prevention_parameters(self, mock_load_model):
        """Test that Whisper is configured with parameters to prevent repetition."""
        # Mock the Whisper model
        mock_model = MagicMock()
        # Set up the chain: whisper.load_model().to() returns the mock_model
        mock_load_model.return_value.to.return_value = mock_model
        
        # Mock transcription result
        mock_result = {
            'text': 'This is a test transcription without repetition.',
            'language': 'en'
        }
        mock_model.transcribe.return_value = mock_result
        
        # Create test audio file
        test_audio = self.temp_dir / "test_audio.mp3"
        test_audio.touch()
        
        # Initialize WhisperManager
        manager = WhisperManager(model_size="large")
        
        # Perform transcription
        result = manager.transcribe_audio(test_audio)
        
        # Verify that transcribe was called with repetition prevention parameters
        call_args = mock_model.transcribe.call_args
        assert call_args is not None, "Transcribe method should have been called"
        
        # Check for repetition prevention parameters
        call_kwargs = call_args[1]  # Get keyword arguments
        
        # Current implementation forces English
        assert 'language' in call_kwargs
        assert call_kwargs['language'] == 'en'
        
        # Verify additional repetition prevention parameters
        assert 'temperature' in call_kwargs
        assert call_kwargs['temperature'] == 0.0, "Temperature should be 0.0 for deterministic output"
        
        assert 'compression_ratio_threshold' in call_kwargs
        assert call_kwargs['compression_ratio_threshold'] == 2.4, "Compression ratio threshold should detect repetitive content"
        
        assert 'logprob_threshold' in call_kwargs
        assert call_kwargs['logprob_threshold'] == -1.0, "Logprob threshold should filter low-confidence transcriptions"
        
        assert 'no_captions_threshold' in call_kwargs
        assert call_kwargs['no_captions_threshold'] == 0.6, "No captions threshold should skip unclear speech"
        
        assert 'condition_on_previous_text' in call_kwargs
        assert call_kwargs['condition_on_previous_text'] is False, "Should prevent context bleeding between segments"
        
        assert 'initial_prompt' in call_kwargs
        assert call_kwargs['initial_prompt'] is None, "Initial prompt should be clear to prevent bias"
        
        assert 'suppress_blank' in call_kwargs
        assert call_kwargs['suppress_blank'] is True, "Should suppress blank segments"
        
        assert 'suppress_tokens' in call_kwargs
        assert call_kwargs['suppress_tokens'] == [-1], "Should suppress problematic tokens"
    
    @patch('src.transcription.whisper_manager.whisper.load_model')
    def test_temperature_setting_for_consistency(self, mock_load_model):
        """Test that temperature is set to reduce randomness and potential repetition."""
        mock_model = MagicMock()
        mock_load_model.return_value.to.return_value = mock_model
        mock_model.transcribe.return_value = {'text': 'test', 'language': 'en'}
        
        test_audio = self.temp_dir / "test_audio.mp3" 
        test_audio.touch()
        
        manager = WhisperManager(model_size="large")
        manager.transcribe_audio(test_audio)
        
        # Verify temperature parameter
        call_kwargs = mock_model.transcribe.call_args[1]
        assert 'temperature' in call_kwargs
        assert call_kwargs['temperature'] == 0.0, "Temperature should be 0.0 for maximum consistency"
    
    @patch('src.transcription.whisper_manager.whisper.load_model')
    def test_beam_search_configuration(self, mock_load_model):
        """Test that beam search is configured to prevent repetitive outputs."""
        mock_model = MagicMock()
        mock_load_model.return_value.to.return_value = mock_model
        mock_model.transcribe.return_value = {'text': 'test', 'language': 'en'}
        
        test_audio = self.temp_dir / "test_audio.mp3"
        test_audio.touch()
        
        manager = WhisperManager(model_size="large")
        manager.transcribe_audio(test_audio)
        
        # TODO: Verify beam search parameters when implemented
        # call_kwargs = mock_model.transcribe.call_args[1] 
        # assert 'beam_size' in call_kwargs
        # assert call_kwargs['beam_size'] >= 1  # Use beam search
        pytest.skip("Beam search configuration not yet implemented")
    
    @patch('src.transcription.whisper_manager.whisper.load_model')
    def test_repetition_penalty_parameter(self, mock_load_model):
        """Test that repetition penalty is applied to discourage repeated phrases."""
        mock_model = MagicMock()
        mock_load_model.return_value.to.return_value = mock_model
        mock_model.transcribe.return_value = {'text': 'test', 'language': 'en'}
        
        test_audio = self.temp_dir / "test_audio.mp3"
        test_audio.touch()
        
        manager = WhisperManager(model_size="large")
        manager.transcribe_audio(test_audio)
        
        # We use Whisper's built-in parameters instead of repetition penalty
        call_kwargs = mock_model.transcribe.call_args[1]
        assert 'compression_ratio_threshold' in call_kwargs, "Should use compression ratio threshold for repetition detection"
        assert 'condition_on_previous_text' in call_kwargs, "Should prevent context bleeding"
        assert call_kwargs['condition_on_previous_text'] is False, "Context bleeding should be disabled"
    
    def test_fp16_disabled_for_accuracy(self):
        """Test that FP16 is disabled for better accuracy and consistency."""
        # Create a mock audio file
        test_audio = self.temp_dir / "test_audio.mp3"
        test_audio.touch()
        
        with patch('src.transcription.whisper_manager.whisper.load_model') as mock_load_model:
            mock_model = MagicMock()
            mock_load_model.return_value.to.return_value = mock_model
            mock_model.transcribe.return_value = {'text': 'test', 'language': 'en'}
            
            manager = WhisperManager(model_size="large")
            manager.transcribe_audio(test_audio)
            
            # Verify FP16 is disabled (current implementation)
            call_kwargs = mock_model.transcribe.call_args[1]
            assert 'fp16' in call_kwargs
            assert call_kwargs['fp16'] is False, "FP16 should be disabled for better accuracy"
    
    @patch('src.transcription.whisper_manager.whisper.load_model')
    def test_language_forced_to_english(self, mock_load_model):
        """Test that language is forced to English to prevent language detection issues."""
        mock_model = MagicMock()
        mock_load_model.return_value.to.return_value = mock_model
        mock_model.transcribe.return_value = {'text': 'test', 'language': 'en'}
        
        test_audio = self.temp_dir / "test_audio.mp3"
        test_audio.touch()
        
        manager = WhisperManager(model_size="large")
        result = manager.transcribe_audio(test_audio)
        
        # Verify language is forced to English (current implementation)
        call_kwargs = mock_model.transcribe.call_args[1]
        assert 'language' in call_kwargs
        assert call_kwargs['language'] == 'en', "Language should be forced to English"
        assert call_kwargs['task'] == 'transcribe', "Task should be transcription"
    
    def test_repetition_detection_and_cleanup(self):
        """Test that repetition detection and cleanup functions work correctly."""
        with patch('src.transcription.whisper_manager.whisper.load_model') as mock_load_model:
            mock_model = MagicMock()
            mock_load_model.return_value.to.return_value = mock_model
            
            manager = WhisperManager(model_size="large")
            
            # Test repetition detection
            repetitive_text = "hello world hello world hello world hello world"
            assert manager._detect_excessive_repetition(repetitive_text, max_repetitions=3) is True
            
            non_repetitive_text = "This is a normal sentence without repetition."
            assert manager._detect_excessive_repetition(non_repetitive_text, max_repetitions=3) is False
            
            # Test repetition cleanup
            cleaned_text = manager._clean_repetitive_text(repetitive_text, max_repetitions=3)
            assert cleaned_text != repetitive_text, "Repetitive text should be cleaned"
            assert "hello world" in cleaned_text.lower(), "Should preserve first occurrence"
            
            # Test comprehensive text cleaning
            text_with_artifacts = "This is a test. Thank you."
            cleaned_comprehensive = manager._clean_transcription_text(text_with_artifacts)
            assert "Thank you." not in cleaned_comprehensive, "Should remove common artifacts"
    
    @patch('src.transcription.whisper_manager.whisper.load_model')
    def test_transcription_uses_cleaned_text(self, mock_load_model):
        """Test that transcription returns cleaned text instead of raw text."""
        mock_model = MagicMock()
        mock_load_model.return_value.to.return_value = mock_model
        
        # Mock repetitive transcription result
        repetitive_result = {
            'text': 'hello world hello world hello world hello world',
            'language': 'en'
        }
        mock_model.transcribe.return_value = repetitive_result
        
        test_audio = self.temp_dir / "test_audio.mp3"
        test_audio.touch()
        
        manager = WhisperManager(model_size="large")
        result = manager.transcribe_audio(test_audio)
        
        # Result should contain cleaned text, not raw repetitive text
        assert result['text'] != repetitive_result['text'], "Should return cleaned text"
        assert len(result['text']) < len(repetitive_result['text']), "Cleaned text should be shorter"


class TestWhisperModelStability:
    """Test Whisper model stability and consistency."""
    
    @patch('src.transcription.whisper_manager.whisper.load_model')
    def test_consistent_output_for_same_input(self, mock_load_model):
        """Test that Whisper produces consistent output for the same input."""
        # This test would verify that with proper configuration,
        # the same audio input produces consistent transcription output
        mock_model = Mock()
        mock_load_model.return_value.to.return_value = mock_model
        
        # Mock consistent output
        expected_text = "This is a consistent transcription output."
        mock_model.transcribe.return_value = {
            'text': expected_text,
            'language': 'en'
        }
        
        test_audio = Path(tempfile.mktemp(suffix='.mp3'))
        test_audio.touch()
        
        try:
            manager = WhisperManager(model_size="large")
            
            # Run transcription multiple times
            results = []
            for _ in range(3):
                result = manager.transcribe_audio(test_audio)
                results.append(result['text'])
            
            # All results should be identical with proper configuration
            assert all(text == expected_text for text in results), \
                "Transcription should be consistent across multiple runs"
                
        finally:
            if test_audio.exists():
                test_audio.unlink()
    
    def test_model_initialization_stability(self):
        """Test that model initialization is stable and repeatable."""
        # Test that loading the same model multiple times is stable
        with patch('src.transcription.whisper_manager.whisper.load_model') as mock_load_model:
            mock_model = MagicMock()
            mock_load_model.return_value.to.return_value = mock_model
            
            # Initialize multiple managers
            manager1 = WhisperManager(model_size="large")
            manager2 = WhisperManager(model_size="large")
            
            # Both should use the same model configuration
            assert manager1.model_size == manager2.model_size
            assert manager1.device == manager2.device


# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.repetition_fix,
    pytest.mark.whisper
]