"""Tests for repetition collapse and degenerate-cue detection."""

import pytest

from src.post_processing.text_processor import TextProcessor


class TestCollapseRepetitions:
    def test_collapses_word_runs(self):
        text = "ai ai ai ai ai ai ai ai que delicia"
        assert TextProcessor.collapse_repetitions(text) == "ai ai ai que delicia"

    def test_collapses_phrase_runs(self):
        text = "52, 53, 59, 52, 53, 59, 52, 53, 59, 52, 53, 59, fim"
        assert TextProcessor.collapse_repetitions(text) == "52, 53, 59, 52, 53, 59, fim"

    def test_leaves_normal_text_untouched(self):
        text = "hoje vamos falar sobre inteligencia artificial e o futuro"
        assert TextProcessor.collapse_repetitions(text) == text


class TestDegenerateSubtitleDetection:
    """Patterns taken from real hallucinated output (translated porn video SRT)."""

    def test_repetition_wall_single_word(self):
        # 43x "whoa" in one cue
        text = ', '.join(['whoa'] * 43) + '.'
        assert TextProcessor.is_degenerate_subtitle_text(text)

    def test_repetition_wall_two_word_phrase(self):
        # 38x "come on" / 40x "fuck it"
        text = ', '.join(['come on'] * 38) + '.'
        assert TextProcessor.is_degenerate_subtitle_text(text)

    def test_char_loop_mega_token(self):
        # "O-o-o-o-o-..." as a single token
        text = 'O' + '-o' * 120
        assert TextProcessor.is_degenerate_subtitle_text(text)

    def test_char_run_token(self):
        assert TextProcessor.is_degenerate_subtitle_text('Aaaaaaaaaaaaaaaaaaaaaa!')

    def test_impossible_density(self):
        # 20 distinct words crammed into 0.9 seconds
        text = ' '.join(f'word{i}' for i in range(20))
        assert TextProcessor.is_degenerate_subtitle_text(text, duration=0.9)
        # Same text over 8 seconds is plausible speech
        assert not TextProcessor.is_degenerate_subtitle_text(text, duration=8.0)

    def test_natural_short_repetition_kept(self):
        assert not TextProcessor.is_degenerate_subtitle_text('No, no, no!')
        assert not TextProcessor.is_degenerate_subtitle_text('Whoa, whoa, easy there.')

    def test_normal_dialogue_kept(self):
        assert not TextProcessor.is_degenerate_subtitle_text(
            "Let go of that bitch's ass. Let go of it.", duration=4.2
        )
        assert not TextProcessor.is_degenerate_subtitle_text(
            'Good morning, everyone, and welcome to our channel.', duration=2.5
        )


class TestLanguageAwareFormatting:
    def test_portuguese_keeps_eu_lowercase(self):
        tp = TextProcessor()
        out = tp.process_transcript('eu queria fazer isso. eu fico feliz.', language='pt')
        assert ' EU ' not in f' {out} '

    def test_english_capitalizes_i(self):
        tp = TextProcessor()
        out = tp.process_transcript('yesterday i went home. i was tired.', language='en')
        assert ' I ' in f' {out} '


pytestmark = [pytest.mark.unit]
