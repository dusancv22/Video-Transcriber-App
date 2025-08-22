# Subtitle Synchronization Architecture

## Overview

This document explains the technical architecture of the subtitle synchronization system in the Video Transcriber App, specifically how word-level timestamps are generated and used to create perfectly synchronized subtitles.

## The Problem

Standard OpenAI Whisper on Windows cannot generate word-level timestamps due to missing Triton support. This causes subtitles to be cut off mid-word when using segment-level timestamps, resulting in poor user experience with text like:
- "voy a ponerme mi" → "riñonera" (word split across subtitles)
- "ir a dar una vuelta en" → "bicicleta." (unnatural breaks)

## The Solution

We implemented a dual-engine approach allowing users to choose between:
1. **Standard Whisper** - Faster processing, segment-level timestamps only
2. **Faster-whisper** - Word-level timestamps that work on Windows

## Architecture Components

### 1. Enhanced Whisper Manager (`src/transcription/enhanced_whisper_manager.py`)

The `EnhancedWhisperManager` class uses the faster-whisper library instead of standard Whisper:

```python
from faster_whisper import WhisperModel

class EnhancedWhisperManager:
    def __init__(self, model_size: str = "large-v2", ...):
        # Uses CTranslate2 models optimized for inference
        self.model = WhisperModel(
            model_size,
            device="cuda" if available else "cpu",
            compute_type="float16" or "int8"
        )
```

**Key Features:**
- Handles Windows symlink issues with environment variables
- Supports both VAD-enhanced and simple transcription modes
- Generates word-level timestamps with confidence scores
- Falls back gracefully if initialization fails

**Word Timestamp Generation:**
```python
transcribe_params = {
    'word_timestamps': True,  # CRITICAL: Works on Windows!
    'vad_filter': False,      # Avoid onnxruntime issues
    'beam_size': 5,
    'temperature': 0.0
}
```

### 2. Word-Based Subtitle Generator (`src/subtitles/word_based_subtitle_generator.py`)

A simplified subtitle generator that directly uses word timestamps:

```python
class WordBasedSubtitleGenerator:
    def generate_from_segments(self, segments, output_path, format):
        # Extract ALL words with timestamps
        all_words = []
        for segment in segments:
            if 'words' in segment:
                for word_data in segment['words']:
                    all_words.append({
                        'word': word_data['word'],
                        'start': word_data['start'],
                        'end': word_data['end']
                    })
        
        # Group words into subtitles based on:
        # - Natural pauses (gaps > 0.3s)
        # - Maximum duration (7s)
        # - Maximum words (10)
        # - Character limits (42 chars/line)
```

**Grouping Algorithm:**
1. Iterates through words sequentially
2. Starts new subtitle when:
   - Word count exceeds limit (10 words)
   - Duration exceeds maximum (7 seconds)
   - Character count exceeds 2-line limit (84 chars)
   - Natural pause detected (gap > 0.3 seconds between words)
3. Ensures minimum subtitle duration (1 second)

### 3. Transcription Pipeline Integration (`src/transcription/transcription_pipeline.py`)

The pipeline now preserves word timestamps throughout processing:

```python
# CRITICAL BUG FIX: Preserve word timestamps when adjusting segments
if 'words' in segment and segment['words']:
    adjusted_words = []
    for word in segment['words']:
        adjusted_words.append({
            'word': word['word'],
            'start': word['start'] + current_time_offset,
            'end': word['end'] + current_time_offset,
            'probability': word.get('probability', 1.0)
        })
    adjusted_segment['words'] = adjusted_words
```

**Pipeline Flow:**
1. User selects "Use Faster-Whisper" in UI
2. Pipeline initializes `EnhancedWhisperManager` instead of standard `WhisperManager`
3. Audio is transcribed with `word_timestamps=True`
4. Word timestamps are preserved when segments are collected
5. Subtitle generator detects word timestamps and uses `WordBasedSubtitleGenerator`

### 4. UI Integration (`src/ui/main_window.py`)

Added checkbox that appears when subtitle export is enabled:

```python
self.use_faster_whisper_checkbox = QCheckBox("Use Faster-Whisper (Word Timestamps)")
self.use_faster_whisper_checkbox.setToolTip(
    "Enable this for subtitle generation with accurate word-level timestamps.\n"
    "Works on Windows! Recommended when exporting subtitles."
)
```

**Behavior:**
- Checkbox only visible when "Export Subtitles" is checked
- Auto-enables when subtitles are selected (recommended)
- Forces pipeline reinitialization when toggled

## Data Flow

### Standard Whisper Flow:
```
Video → Audio → Whisper → Segments (no words) → Estimation-based splitting → Subtitles
```

### Faster-Whisper Flow:
```
Video → Audio → Faster-whisper → Segments with words → Word-based grouping → Accurate Subtitles
```

## Segment Data Structure

### Without Word Timestamps (Standard Whisper):
```json
{
    "start": 19.1,
    "end": 26.1,
    "text": "No hay nada mejor que un buen vaso de agua fresquita por la mañana."
}
```

### With Word Timestamps (Faster-whisper):
```json
{
    "start": 19.1,
    "end": 26.1,
    "text": "No hay nada mejor que un buen vaso de agua fresquita por la mañana.",
    "words": [
        {"word": "No", "start": 19.1, "end": 19.3, "probability": 0.99},
        {"word": "hay", "start": 19.3, "end": 19.5, "probability": 0.98},
        {"word": "nada", "start": 19.5, "end": 19.8, "probability": 0.99},
        // ... more words with precise timing
    ]
}
```

## Windows-Specific Considerations

### 1. Symlink Issues
Hugging Face hub uses symlinks by default, which require admin privileges on Windows:

```python
# Solution: Disable symlinks
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'
```

### 2. Model Format Differences
- Standard Whisper: Uses `.pt` PyTorch model files
- Faster-whisper: Uses CTranslate2 optimized models
- Cannot mix model formats between engines

### 3. ONNX Runtime Issues
VAD filter in faster-whisper requires onnxruntime which can have DLL issues on Windows:

```python
# Solution: Disable VAD filter
'vad_filter': False  # Avoid onnxruntime dependency issues
```

## Performance Characteristics

### Standard Whisper
- **Speed**: Faster initial processing
- **Memory**: Higher GPU memory usage
- **Accuracy**: Good transcription accuracy
- **Timing**: Segment-level only on Windows

### Faster-whisper
- **Speed**: Slower initial model loading, faster inference
- **Memory**: Lower memory usage (CTranslate2 optimizations)
- **Accuracy**: Comparable transcription accuracy
- **Timing**: Precise word-level timestamps

## Testing & Validation

To verify word timestamps are working:

1. Check logs for: `"Using word-based subtitle generator with actual word timestamps"`
2. Verify segments contain 'words' field in debug output
3. Inspect generated subtitles for natural word boundaries
4. No mid-word cuts should occur

## Common Issues & Solutions

### Issue 1: Word timestamps not appearing
**Cause**: Pipeline stripping 'words' field when adjusting timestamps
**Solution**: Fixed in `transcription_pipeline.py` lines 410-421

### Issue 2: Model compatibility errors
**Cause**: Trying to load .pt files with faster-whisper
**Solution**: Auto-detect and ignore .pt files, download appropriate model

### Issue 3: Subtitles still cutting mid-word
**Cause**: Subtitle generator not using word timestamps even when available
**Solution**: Implemented `WordBasedSubtitleGenerator` with direct word timestamp usage

## Future Improvements

1. **Caching**: Cache word timestamp data to avoid reprocessing
2. **Fine-tuning**: Allow users to adjust grouping parameters (pause threshold, max words)
3. **Language-specific**: Adjust reading speeds based on detected language
4. **Confidence filtering**: Use probability scores to handle uncertain words
5. **Punctuation awareness**: Use punctuation for more natural subtitle breaks

## Dependencies

Required packages for word-level timestamps:
```
faster-whisper>=1.2.0
ctranslate2>=4.0
tokenizers>=0.13
onnxruntime>=1.14 (optional, for VAD)
pydub>=0.25.1
```

## Configuration

Key configuration parameters:

```python
# Word-based subtitle generation
max_chars_per_line = 42
max_words_per_subtitle = 10
min_subtitle_duration = 1.0
max_subtitle_duration = 7.0
natural_pause_threshold = 0.3  # seconds

# Faster-whisper settings
beam_size = 5
temperature = 0.0
word_timestamps = True
vad_filter = False  # Disabled on Windows
```

## Conclusion

The subtitle synchronization system now provides accurate, word-level timing for subtitles on Windows by leveraging faster-whisper's CTranslate2-based implementation. This ensures subtitles appear and disappear in sync with actual speech, never cutting off mid-word, providing a professional viewing experience.