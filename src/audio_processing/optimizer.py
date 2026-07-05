"""Audio quality pass: measure loudness and normalize quiet audio before transcription.

Quiet audio is the enemy of the whole downstream chain: the VAD misses speech
regions entirely, Whisper's 30-second language detection misfires (especially
noticeable on Spanish/Portuguese content), and recognition accuracy drops.

This module implements a conditional two-pass EBU R128 loudness normalization:
  1. Analysis pass: measure integrated loudness with ffmpeg's ``loudnorm`` filter.
  2. Only if the audio is quieter than a threshold, apply a gentle highpass
     (removes low-frequency rumble that confuses the VAD) plus loudness
     normalization using the measured values (accurate linear normalization).

Audio that is already loud enough is left untouched, so the pass adds a single
fast analysis decode in the common case.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AudioQualityOptimizer:
    """Measures loudness and boosts quiet audio so VAD/Whisper get a usable signal."""

    def __init__(
        self,
        quiet_threshold_lufs: float = -24.0,
        target_lufs: float = -16.0,
        true_peak_db: float = -1.5,
        loudness_range: float = 11.0,
        highpass_hz: int = 80,
    ):
        """Initialize the optimizer.

        Args:
            quiet_threshold_lufs: Integrated loudness below which enhancement kicks in.
            target_lufs: Normalization target (EBU R128 integrated loudness).
            true_peak_db: Maximum true peak after normalization.
            loudness_range: Target loudness range (LRA) for loudnorm.
            highpass_hz: Highpass cutoff applied during enhancement (0 disables).
        """
        self.quiet_threshold_lufs = quiet_threshold_lufs
        self.target_lufs = target_lufs
        self.true_peak_db = true_peak_db
        self.loudness_range = loudness_range
        self.highpass_hz = highpass_hz

    def analyze_loudness(self, audio_path: str | Path) -> Optional[Dict[str, Any]]:
        """Run the loudnorm analysis pass and return measured loudness stats.

        Args:
            audio_path: Path to the audio file to analyze.

        Returns:
            Dict with loudnorm's measured values (keys like ``input_i``,
            ``input_tp``, ``input_lra``, ``input_thresh``, ``target_offset``),
            or None if analysis failed.
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            logger.error(f"Cannot analyze loudness, file not found: {audio_path}")
            return None

        loudnorm_args = (
            f"loudnorm=I={self.target_lufs}:TP={self.true_peak_db}:"
            f"LRA={self.loudness_range}:print_format=json"
        )
        cmd = [
            "ffmpeg", "-hide_banner", "-nostats",
            "-i", str(audio_path),
            "-af", loudnorm_args,
            "-f", "null", "-",
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600
            )
            measured = self._parse_loudnorm_json(result.stderr)
            if measured is None:
                logger.error(f"Could not parse loudnorm output for {audio_path.name}")
                return None

            logger.info(
                f"Loudness analysis for {audio_path.name}: "
                f"I={measured.get('input_i')} LUFS, TP={measured.get('input_tp')} dBTP"
            )
            return measured
        except (subprocess.SubprocessError, OSError) as e:
            logger.error(f"Loudness analysis failed for {audio_path.name}: {e}")
            return None

    @staticmethod
    def _parse_loudnorm_json(stderr_text: str) -> Optional[Dict[str, Any]]:
        """Extract the JSON block loudnorm prints at the end of ffmpeg's stderr."""
        # loudnorm prints a { ... } block after "[Parsed_loudnorm..." near the end.
        start = stderr_text.rfind("{")
        end = stderr_text.rfind("}")
        if start == -1 or end == -1 or end < start:
            return None
        try:
            return json.loads(stderr_text[start:end + 1])
        except json.JSONDecodeError:
            return None

    def needs_enhancement(self, measured: Dict[str, Any]) -> bool:
        """Return True when measured integrated loudness is below the quiet threshold."""
        try:
            input_i = float(measured["input_i"])
        except (KeyError, TypeError, ValueError):
            return False
        # loudnorm reports -inf as "-inf" for silence; treat pure silence as
        # not enhanceable (nothing to boost).
        if input_i == float("-inf"):
            return False
        return input_i < self.quiet_threshold_lufs

    def enhance_audio(
        self,
        audio_path: str | Path,
        measured: Dict[str, Any],
        output_path: Optional[str | Path] = None,
    ) -> Optional[Path]:
        """Apply highpass + measured two-pass loudness normalization.

        Args:
            audio_path: Path to the quiet audio file.
            measured: Values returned by :meth:`analyze_loudness`.
            output_path: Destination path. When omitted, the source file is
                replaced in-place (via a temporary sibling file).

        Returns:
            Path to the enhanced file, or None on failure.
        """
        audio_path = Path(audio_path)
        in_place = output_path is None
        if in_place:
            output_path = audio_path.with_name(f"{audio_path.stem}_normalized{audio_path.suffix}")
        output_path = Path(output_path)

        filters = []
        if self.highpass_hz > 0:
            filters.append(f"highpass=f={self.highpass_hz}")
        filters.append(
            f"loudnorm=I={self.target_lufs}:TP={self.true_peak_db}:LRA={self.loudness_range}:"
            f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
            f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
            f"offset={measured.get('target_offset', 0.0)}:linear=true"
        )

        cmd = [
            "ffmpeg", "-hide_banner", "-nostats", "-y",
            "-i", str(audio_path),
            "-af", ",".join(filters),
        ]
        # Keep transcription-friendly output parameters for WAV; otherwise let
        # ffmpeg pick codec defaults from the extension.
        if output_path.suffix.lower() == ".wav":
            cmd += ["-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1"]
        cmd.append(str(output_path))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            if result.returncode != 0 or not output_path.exists():
                logger.error(
                    f"Audio enhancement failed for {audio_path.name}: "
                    f"{result.stderr[-500:] if result.stderr else 'unknown error'}"
                )
                if output_path.exists():
                    output_path.unlink()
                return None

            if in_place:
                audio_path.unlink()
                output_path.rename(audio_path)
                output_path = audio_path

            logger.info(f"Audio enhanced: {output_path.name}")
            return output_path
        except (subprocess.SubprocessError, OSError) as e:
            logger.error(f"Audio enhancement failed for {audio_path.name}: {e}")
            if output_path != audio_path and output_path.exists():
                output_path.unlink()
            return None

    def process(self, audio_path: str | Path) -> Dict[str, Any]:
        """Run the full quality pass: analyze, and enhance in place when too quiet.

        Never raises — on any failure the original audio is left untouched so
        transcription can proceed with the unmodified file.

        Args:
            audio_path: Path to the audio file (enhanced in place if needed).

        Returns:
            Report dict: ``{'analyzed': bool, 'enhanced': bool,
            'input_loudness_lufs': float | None, 'target_lufs': float}``
        """
        report: Dict[str, Any] = {
            "analyzed": False,
            "enhanced": False,
            "input_loudness_lufs": None,
            "target_lufs": self.target_lufs,
        }

        measured = self.analyze_loudness(audio_path)
        if measured is None:
            return report

        report["analyzed"] = True
        try:
            report["input_loudness_lufs"] = float(measured["input_i"])
        except (KeyError, TypeError, ValueError):
            pass

        if not self.needs_enhancement(measured):
            logger.info(
                f"Audio loudness OK ({report['input_loudness_lufs']} LUFS >= "
                f"{self.quiet_threshold_lufs} LUFS threshold), no enhancement needed"
            )
            return report

        print(
            f"Audio is quiet ({report['input_loudness_lufs']} LUFS) - "
            f"normalizing to {self.target_lufs} LUFS..."
        )
        enhanced = self.enhance_audio(audio_path, measured)
        report["enhanced"] = enhanced is not None
        return report
