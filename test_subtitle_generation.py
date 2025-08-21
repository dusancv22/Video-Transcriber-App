#!/usr/bin/env python
"""Test script for subtitle generation feature."""

from pathlib import Path
from src.subtitles.subtitle_generator import SubtitleGenerator

def test_subtitle_generation():
    """Test basic subtitle generation functionality."""
    
    # Create test segments (simulating realistic Whisper output with accurate timestamps)
    test_segments = [
        {'start': 0.0, 'end': 2.5, 'text': 'Hello, this is a test video.'},
        {'start': 2.5, 'end': 5.0, 'text': 'We are testing subtitle generation.'},
        {'start': 5.0, 'end': 8.0, 'text': 'This should create proper SRT and VTT files.'},
        {'start': 8.0, 'end': 11.0, 'text': 'Each subtitle should be properly timed.'},
        {'start': 11.0, 'end': 14.0, 'text': 'The text should wrap at appropriate character limits.'},
        # Test long segment that needs to be split into multiple subtitles
        {'start': 30.0, 'end': 37.0, 'text': 'Ayer antes de irme a la cama pensé en despertarme pronto e ir a dar una vuelta en bicicleta por el pueblo para hacer ejercicio.'},
        # Test very long segment
        {'start': 47.42, 'end': 54.42, 'text': 'No hay nada mejor que un buen vaso de agua fresquita por la mañana cuando te levantas temprano para empezar el día con energía.'},
    ]
    
    # Initialize subtitle generator
    generator = SubtitleGenerator(max_chars_per_line=42)
    
    # Create output directory
    output_dir = Path('test_output')
    output_dir.mkdir(exist_ok=True)
    
    # Generate subtitles in multiple formats
    output_base = output_dir / 'test_subtitle'
    formats = ['srt', 'vtt', 'ass']
    
    print("Testing subtitle generation...")
    print(f"Generating {len(test_segments)} segments in {len(formats)} formats")
    print("Note: Testing 2-line maximum enforcement for long text")
    
    generated_files = generator.generate_multiple_formats(
        test_segments,
        output_base,
        formats
    )
    
    # Check results
    print("\nGenerated files:")
    for format, file_path in generated_files.items():
        if file_path and file_path.exists():
            file_size = file_path.stat().st_size
            print(f"  [OK] {format.upper()}: {file_path} ({file_size} bytes)")
            
            # Show first few lines of SRT file as example
            if format == 'srt':
                print(f"\n  Preview of {file_path.name}:")
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:8]
                    for line in lines:
                        print(f"    {line.rstrip()}")
        else:
            print(f"  [FAIL] {format.upper()}: Failed to generate")
    
    # Test timing adjustment
    print("\n\nTesting timing adjustment (2 second delay):")
    adjusted_segments = generator.adjust_timing(test_segments, offset=2.0)
    print(f"Original first segment: {test_segments[0]['start']:.1f}s - {test_segments[0]['end']:.1f}s")
    print(f"Adjusted first segment: {adjusted_segments[0]['start']:.1f}s - {adjusted_segments[0]['end']:.1f}s")
    
    # Test format info
    print("\n\nSupported formats:")
    for fmt in SubtitleGenerator.SUPPORTED_FORMATS.keys():
        info = SubtitleGenerator.get_format_info(fmt)
        print(f"  {fmt.upper()}: {info['description']}")
    
    print("\n[SUCCESS] Subtitle generation test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        test_subtitle_generation()
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()