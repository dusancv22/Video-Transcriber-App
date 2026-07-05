"""
Tests for subtitle translation using the Helsinki-NLP translation engine wrapper.
"""

import pytest
import pysubs2

from src.translation.engines.helsinki_translator import HelsinkiTranslator
from src.translation.subtitle_translator import SubtitleTranslator


def create_fake_translator():
    """Create a HelsinkiTranslator without loading external model files."""
    translator = HelsinkiTranslator.__new__(HelsinkiTranslator)
    translator.source_lang = "es"
    translator.target_lang = "en"
    translator.device = "cpu"
    translator.model = object()  # non-None: model "loaded"
    translator.tokenizer = None
    translator.model_name = "fake-model"
    translator.max_length = 512
    # Stub the single model-call seam with a deterministic fake
    translator._translate_batch = lambda texts: [f"translated: {t}" for t in texts]
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


def test_per_segment_translation_is_exact():
    """Every segment gets exactly its own translation - no window extraction."""
    translator = create_fake_translator()

    segments = [
        {"id": 0, "start": 0.0, "end": 2.0, "text": "Mi hermana tiene un perro."},
        {"id": 1, "start": 2.0, "end": 4.0, "text": "Es muy grande."},
        {"id": 2, "start": 4.0, "end": 6.0, "text": "Le gusta correr."},
    ]

    translated_segments = translator.translate_segments(segments, batch_size=2)

    assert len(translated_segments) == len(segments)
    for original, translated in zip(segments, translated_segments):
        # Timestamps must be preserved exactly
        assert translated["start"] == original["start"]
        assert translated["end"] == original["end"]
        # And each translation corresponds 1:1 to its own segment text
        assert translated["translated_text"] == f"translated: {original['text']}"
        assert translated["original_text"] == original["text"]


def test_pt_en_uses_romance_model():
    """pt->en must map to the ROMANCE-en model, not the generic mul-en fallback."""
    translator = HelsinkiTranslator.__new__(HelsinkiTranslator)
    translator.source_lang = "pt"
    translator.target_lang = "en"

    assert translator._get_model_name() == "Helsinki-NLP/opus-mt-ROMANCE-en"


def test_translated_ass_preserves_styles(tmp_path):
    """Translating an ASS file must carry over style definitions, not just names."""
    # Build an ASS file with a custom style
    subs = pysubs2.SSAFile()
    style = pysubs2.SSAStyle(fontname="Georgia", fontsize=28.0, bold=True)
    subs.styles["Narrator"] = style
    subs.events.append(pysubs2.SSAEvent(start=0, end=2000, text="Ola mundo.", style="Narrator"))
    subs.events.append(pysubs2.SSAEvent(start=2000, end=4000, text="Tudo bem?", style="Narrator"))
    original = tmp_path / "original.ass"
    subs.save(str(original), format_="ass")

    # Translate with a stubbed engine (no model download). Construct with
    # "auto" so __init__ doesn't try to load a real model, then inject the fake.
    translator = SubtitleTranslator(source_lang="auto", target_lang="en")
    translator.source_lang = "pt"
    translator.translator = create_fake_translator()

    output = tmp_path / "translated.en.ass"
    result_path = translator.translate_subtitle_file(original, output_path=output)

    translated = pysubs2.load(str(result_path))
    # Style definition preserved with its attributes
    assert "Narrator" in translated.styles
    assert translated.styles["Narrator"].fontname == "Georgia"
    assert translated.styles["Narrator"].bold is True
    # Events translated, timing intact, style reference intact
    assert len(translated.events) == 2
    assert translated.events[0].text == "translated: Ola mundo."
    assert translated.events[0].style == "Narrator"
    assert translated.events[0].start == 0 and translated.events[0].end == 2000


pytestmark = [
    pytest.mark.unit,
    pytest.mark.translation,
]
