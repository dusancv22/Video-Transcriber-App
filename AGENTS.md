# Repository Guidelines

## Project Structure & Module Organization
- `src/` hosts runtime modules: `transcription/` orchestrates Whisper pipelines, `translation/` adds subtitle translation, `audio_processing/` wraps FFmpeg and VAD helpers, `ui/` contains PyQt6 widgets, and `post_processing/` cleans transcript text.
- `tests/` mirrors the runtime layout with pytest suites; fixtures and sample outputs sit in `tests/test_transcription/test_files/`.
- UI assets and docs live in `assets/` and `docs/`; packaging artifacts land in `output/` and `dist/` when built.
- Use `run.py` as the local entry point; keep configuration defaults in `src/config/settings.py`.

## Build, Test, and Development Commands
- `python -m venv venv` then `venv\Scripts\activate` prepares a clean environment; install dependencies via `pip install -r requirements.txt`.
- `python run.py` launches the desktop app with live logging to `app_output.log`.
- `pytest` runs the full suite; target areas with `pytest tests/test_transcription/test_pipeline.py -k queue`.
- `pyinstaller VideoTranscriber.spec --clean` produces the Windows executable described in `VideoTranscriber.spec`.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation and type hints, as seen in `src/transcription/whisper_manager.py`.
- Modules, classes, and files use descriptive snake_case or PascalCase (`queue_manager.py`, `WhisperManager`); align tests with the same nouns.
- Prefer `logging.getLogger(__name__)` for diagnostics; avoid bare `print`.
- Keep docstrings concise and action-oriented, documenting parameters and return types.

## Testing Guidelines
- Place new unit tests beside the related package under `tests/`; integration flows belong in `tests/test_transcription/`.
- Name tests using `test_<behavior>` to match existing patterns like `test_audio_processing/test_splitter.py`.
- Run `pytest --maxfail=1 --disable-warnings -q` before pushing; ensure GPU-dependent paths are guarded with `pytest.skip` checks.
- Capture sample inputs under `tests/test_transcription/test_files/` and reuse existing fixtures where possible.

## Commit & Pull Request Guidelines
- Follow the Conventional Commit style used in history (`feat:`, `fix:`, `docs:`, `debug:`) with a succinct imperative summary.
- Reference related issues in the body and describe user-facing changes plus QA steps.
- Include screenshots or log excerpts for UI or pipeline changes and note any model downloads required for reviewers.
- Confirm `pytest` and, if altered, the PyInstaller build completes before requesting review.
