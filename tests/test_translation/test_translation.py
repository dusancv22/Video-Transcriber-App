"""
Tests for subtitle translation using the Helsinki-NLP translation engine wrapper.
"""

import re

import pytest

from src.translation.engines.helsinki_translator import HelsinkiTranslator


class FakeTranslationPipeline:
    """Small deterministic stand-in for the Hugging Face translation pipeline."""

    def __call__(self, text, max_length=None):
        if isinstance(text, list):
            return [{"translation_text": self._translate(item)} for item in text]
        return [{"translation_text": self._translate(text)}]

    def _translate(self, text):
        current_match = re.search(r"\[CURRENT\]\s*(.*?)\s*\[/CURRENT\]", text)
        if current_match:
            return f"[CURRENT] translated: {current_match.group(1)} [/CURRENT]"
        return f"translated: {text}"


def create_fake_translator():
    """Create a HelsinkiTranslator without loading external model files."""
    translator = HelsinkiTranslator.__new__(HelsinkiTranslator)
    translator.source_lang = "es"
    translator.target_lang = "en"
    translator.device = "cpu"
    translator.pipeline = FakeTranslationPipeline()
    translator.tokenizer = None
    translator.model_name = "fake-model"
    translator.max_length = 512
    return translator


def test_basic_translation():
    """Test basic translation delegates to the configured pipeline."""
    translator = create_fake_translator()

    translated = translator.translate("Hola, como estas?")

    assert translated == "translated: Hola, como estas?"


def test_subtitle_segments():
    """Test translation of subtitle-like segments."""
    translator = create_fake_translator()

    segments = [
        {"id": 0, "start": 0.0, "end": 2.5, "text": "Buenos dias."},
        {"id": 1, "start": 2.5, "end": 5.0, "text": "Bienvenidos."},
        {"id": 2, "start": 5.0, "end": 8.0, "text": ""},
    ]

    translated_segments = translator.translate_segments(segments)

    assert translated_segments[0]["translated_text"] == "translated: Buenos dias."
    assert translated_segments[0]["original_text"] == "Buenos dias."
    assert translated_segments[1]["translated_text"] == "translated: Bienvenidos."
    assert translated_segments[2]["translated_text"] == ""
    assert all("start" in segment and "end" in segment for segment in translated_segments)


def test_context_translation():
    """Test context-aware translation extracts the current segment from markers."""
    translator = create_fake_translator()

    segments = [
        {"id": 0, "start": 0.0, "end": 2.0, "text": "Mi hermana tiene un perro."},
        {"id": 1, "start": 2.0, "end": 4.0, "text": "Es muy grande."},
        {"id": 2, "start": 4.0, "end": 6.0, "text": "Le gusta correr."},
    ]

    translated_segments = translator.translate_with_context(segments, context_window=1)

    assert len(translated_segments) == len(segments)
    assert translated_segments[0]["translated_text"] == "translated: Mi hermana tiene un perro."
    assert translated_segments[1]["translated_text"] == "translated: Es muy grande."
    assert translated_segments[2]["translated_text"] == "translated: Le gusta correr."


pytestmark = [
    pytest.mark.unit,
    pytest.mark.translation,
]
