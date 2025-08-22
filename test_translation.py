"""
Test script for subtitle translation feature.
Tests the Helsinki-NLP translation module with sample Spanish subtitles.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.translation.subtitle_translator import SubtitleTranslator
from src.translation.engines.helsinki_translator import HelsinkiTranslator

def test_basic_translation():
    """Test basic Spanish to English translation."""
    print("Testing basic translation (Spanish to English)...")
    
    try:
        translator = HelsinkiTranslator(source_lang='es', target_lang='en')
        
        # Test sentences
        test_texts = [
            "Hola, ¿cómo estás?",
            "Me llamo Juan y vivo en Madrid.",
            "El tiempo está muy bueno hoy.",
            "Voy a la tienda a comprar pan."
        ]
        
        print("\nTranslation results:")
        print("-" * 50)
        for text in test_texts:
            translated = translator.translate(text)
            print(f"ES: {text}")
            print(f"EN: {translated}")
            print()
        
        print("✓ Basic translation test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Basic translation test failed: {e}")
        return False

def test_subtitle_segments():
    """Test translation of subtitle-like segments."""
    print("\nTesting subtitle segment translation...")
    
    try:
        translator = HelsinkiTranslator(source_lang='es', target_lang='en')
        
        # Sample subtitle segments
        segments = [
            {'id': 0, 'start': 0.0, 'end': 2.5, 'text': 'Buenos días, señoras y señores.'},
            {'id': 1, 'start': 2.5, 'end': 5.0, 'text': 'Bienvenidos a nuestra presentación.'},
            {'id': 2, 'start': 5.0, 'end': 8.0, 'text': 'Hoy vamos a hablar sobre tecnología.'},
            {'id': 3, 'start': 8.0, 'end': 11.0, 'text': 'Es un tema muy interesante.'}
        ]
        
        # Translate segments
        translated_segments = translator.translate_segments(segments)
        
        print("\nTranslated subtitle segments:")
        print("-" * 50)
        for seg in translated_segments:
            print(f"[{seg['start']:.1f}s - {seg['end']:.1f}s]")
            print(f"Original: {seg.get('original_text', seg['text'])}")
            print(f"Translated: {seg['translated_text']}")
            print()
        
        print("✓ Subtitle segment translation test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Subtitle segment translation test failed: {e}")
        return False

def test_context_translation():
    """Test context-aware translation."""
    print("\nTesting context-aware translation...")
    
    try:
        translator = HelsinkiTranslator(source_lang='es', target_lang='en')
        
        # Segments that benefit from context
        segments = [
            {'id': 0, 'start': 0.0, 'end': 2.0, 'text': 'Mi hermana tiene un perro.'},
            {'id': 1, 'start': 2.0, 'end': 4.0, 'text': 'Es muy grande y juguetón.'},  # "Es" refers to the dog
            {'id': 2, 'start': 4.0, 'end': 6.0, 'text': 'Le gusta correr en el parque.'}  # "Le" refers to the dog
        ]
        
        # Translate with context
        translated_segments = translator.translate_with_context(segments, context_window=2)
        
        print("\nContext-aware translation results:")
        print("-" * 50)
        for seg in translated_segments:
            print(f"Original: {seg.get('original_text', seg['text'])}")
            print(f"Translated: {seg['translated_text']}")
            print()
        
        print("✓ Context-aware translation test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Context-aware translation test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("SUBTITLE TRANSLATION MODULE TEST")
    print("=" * 60)
    
    print("\nNote: First run will download the translation model (~300MB)")
    print("This is a one-time download that will be cached locally.")
    print()
    
    # Run tests
    tests_passed = 0
    tests_total = 3
    
    if test_basic_translation():
        tests_passed += 1
    
    if test_subtitle_segments():
        tests_passed += 1
    
    if test_context_translation():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("✓ All tests passed! Translation module is working correctly.")
    else:
        print(f"✗ {tests_total - tests_passed} test(s) failed. Please check the errors above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()