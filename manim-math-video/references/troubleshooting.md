# Troubleshooting and installation

Run this first:

```bash
python scripts/check_env.py
```

It reports Python, Manim, LaTeX, PyAV, edge-tts, fonts, and optional tools. Use `--json` for a machine-readable report. In a terminal the statuses are colored; use `--color always` or `--no-color` to override.

If you have the repository, the one-step setup is:

```bash
python scripts/setup.py
```

It creates `.venv`, installs `requirements.txt`, and runs the check.

## Minimal installation

### Python

Python 3.10 or newer. A virtual environment is strongly recommended:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Windows cmd
.venv\Scripts\activate.bat
# macOS / Linux
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `manim` is not on PATH, `check_env.py` and `render.py` also look next to the current Python, in a local `.venv`, and at `MANIM_BIN`. Set `MANIM_BIN` to the full executable path when your environment is non-standard:

```powershell
$env:MANIM_BIN = "C:\path\to\.venv\Scripts\manim.exe"
```

```bash
export MANIM_BIN="/path/to/.venv/Scripts/manim.exe"
```

### Manim Community

```bash
python -m pip install manim
manim checkhealth
```

This installs Manim, Cairo, Pango, NumPy, and PyAV on most platforms. If the install fails, see the official Manim installation guide for your OS.

### Narration

```bash
python -m pip install edge-tts
python -m pip install av pillow
```

- `edge-tts` is the default provider (network required).
- `av` (PyAV) converts MP3 to WAV and powers QA. Manim often installs it already.
- `pillow` is used for contact sheets.

### LaTeX (for equations)

Manim's `MathTex` needs a LaTeX distribution and `dvisvgm`.

**Windows**

```powershell
winget install MiKTeX.MiKTeX
# or
choco install miktex
```

After installation, open MiKTeX Console and allow automatic package installation, or install `amsmath` and the packages Manim requests. Restart the terminal and run:

```bash
latex --version
dvisvgm --version
```

**macOS**

```bash
brew install --cask mactex-no-gui
# or a smaller TeX Live install
```

**Linux (Debian/Ubuntu)**

```bash
sudo apt update
sudo apt install texlive texlive-latex-extra texlive-fonts-recommended dvisvgm
```

**Minimal / CI**

TinyTeX is a good option:

```bash
# Follow the TinyTeX installer for your OS, then:
tlmgr install amsmath
```

If LaTeX is missing, equation beats fail loudly. For a silent draft only, set:

```json
"output": { "latex_fallback": true }
```

This renders a Unicode approximation. Never publish it as final mathematics.

### ffmpeg (optional)

Manim 0.22 uses PyAV for most media work, but ffmpeg is still useful for post-production, subtitle burn-in, and audio normalization.

- Windows: `winget install Gyan.FFmpeg`
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

## Common errors

### `latex: command not found` / `FileNotFoundError: latex`

LaTeX is not installed or not on PATH. Install a TeX distribution, restart the terminal, and run `manim checkhealth`. If you only need a draft, use `latex_fallback`.

### `dvisvgm: command not found`

Install `dvisvgm` (often part of TeX Live). On Debian/Ubuntu: `sudo apt install dvisvgm`. On MiKTeX, install the `dvisvgm` package.

### `No module named edge_tts`

```bash
python -m pip install edge-tts
```

If you are using a different Python than the one running the skill, install into the same environment.

### `No module named av` / audio conversion fails

```bash
python -m pip install av
```

Or install ffmpeg and rerun. The TTS script tries PyAV first, then ffmpeg.

### `FileNotFoundError: ffmpeg`

Manim can render video without a system ffmpeg in many cases, but `pydub`-based audio operations may need it. Install ffmpeg or ensure the TTS output is WAV (the script converts it).

### `Voice manifest not found`

Run:

```bash
python scripts/tts.py --episode <episode>
```

For a silent timing draft:

```bash
python scripts/tts.py --episode <episode> --provider none
```

The runtime will still use the manifest's durations, but there will be no audio.

### `No narration segment with id ...`

The storyboard and the voice manifest are out of sync. Rerun `tts.py`. If you renamed a beat, update the storyboard and regenerate.

### Audio ends before the video, or video ends before the audio

The runtime schedules animations inside a narration budget and waits for the remainder. If a custom beat runs longer than `vo.duration`, the audio ends early. Shorten the custom animation or split the beat.

If the video ends before the audio, the scene's total visual time is shorter than the audio. The runtime adds a tail wait for standard beats, but a custom beat may bypass it. Add `self.wait(...)` or use `vo.remaining`.

### Narration is missing after a re-render, or audio is silent in the middle

A second render reuses Manim's cached partial movies, and cached segments can come back without their
per-beat sound. The result looks right but has long silent stretches — usually visible as a sudden
drop in the QA audio level (`RMS` far below the previous render).

Render with caching disabled whenever the scene changed:

```bash
python scripts/render.py --episode <episode-dir> --quality standard --no-cache
```

`render.py` passes `--disable_caching` to Manim. Editing narration text alone is safe (the TTS cache
is keyed by a hash of the text), but editing on-screen text, graph specs, or the theme is not.

### Subtitles are missing

- Check `output.captions` is `true`.
- Check `theme.captions.enabled` is `true`.
- Check that the beat has narration or a caption.
- Manim writes the SRT next to the MP4. `render.py` copies it to `output/`.

### Fonts render as boxes or fall back unexpectedly

The template uses font stacks with fallbacks. If a script (CJK, Arabic, Devanagari) renders as boxes, install a font with that coverage, for example Noto Sans CJK or Noto Sans Devanagari, and set the font explicitly in `theme.json`.

Check available fonts:

```python
import manimpango
print(sorted(manimpango.list_fonts()))
```

### Text overflows the frame

- Shorten the on-screen text.
- Lower `sizes.body` or `sizes.heading`.
- Increase `layout.text_max_width` only if the text still fits.
- Split a bullet list into two beats.
- Use `Font size` in the storyboard? The runtime uses the template sizes; edit `theme.json` for the episode if needed.

### Graph labels overlap

- Reduce the number of ticks (`show_ticks` stays true, but the runtime already thins them).
- Move annotation labels with `label_offset`.
- Remove the legend for a single curve and label the curve directly.
- Split two curves into two beats.
- Change the ranges to give the labels room.

### Graph is empty or has gaps

- Check the expression syntax: `**` for powers, `*` for multiplication.
- Check the domain: logarithms need positive inputs, square roots need nonnegative inputs, division needs a nonzero denominator.
- Check `x_range`/`y_range`: if the function values are outside the y-range, nothing appears.
- Check for `NaN` from a discontinuity; restrict the domain.

### `TransformMatchingTex` fails

Use `ReplacementTransform` instead. Matching depends on the LaTeX substrings being present in both expressions. Keep transformations simple.

### Render is very slow

- Render `draft` first.
- Reduce graph samples and the number of simultaneous animations.
- Avoid `always_redraw` with expensive computations.
- Cache partial movies while iterating.
- Use `standard` 1080p30 instead of 60 fps unless the motion needs it.
- 4K is 4x the pixels of 1080p; expect a large increase.

### Colors look wrong or low contrast

- Check the template's `roles` and `background`.
- Avoid using `danger` and `success` as the only distinction.
- Check the contact sheet and a 1080p still, not only the 480p draft.
- For projectors, prefer `clean-light`.

### Native provider key missing

```bash
export CARTESIA_API_KEY=...       # https://play.cartesia.ai/keys
export ELEVENLABS_API_KEY=...     # https://elevenlabs.io/app/settings/api-keys
```

Run `python scripts/check_env.py` to confirm the key is visible to the skill
interpreter. The installer prints the missing variable when you select a native
provider. Keys are intentionally not stored in `brief.json` or `tts.json`.

### Cartesia returns 401/403 or 422

- Confirm `CARTESIA_API_KEY` is set and starts with `sk_car_`.
- The request uses `Authorization: Bearer` and `Cartesia-Version: 2026-08-14`.
  If the provider changed its API version, override `output.voice.api_version`
  or the `api_version` field in `~/.manim-math-video/tts.json`.
- A 422 usually means an unsupported `voice` id, `model_id`, output format, or
  generation config. List voices with
  `python scripts/tts.py --list-voices --provider cartesia --language en-US`.

### ElevenLabs returns 401/422

- Confirm `ELEVENLABS_API_KEY` is set.
- Use a voice id from `python scripts/voice_samples.py --provider elevenlabs
  --language en-US --list` (a display name is not an id).
- If a model rejects `speed`, remove the override from `voice_settings` or use
  a supported `model_id`.
- Available account voices and models depend on the subscription tier.

### `Edge TTS` returns 403/401 or times out

- Check network access and proxy settings.
- Try `--proxy http://...`.
- Retry; the script retries three times.
- Use a different provider (`piper`, `custom`, or `none` for a draft).
- Do not put API keys in `brief.json`.

### `Piper` executable not found

Install Piper and point to a model:

```bash
python scripts/tts.py --episode <episode> \
  --provider piper \
  --piper-model /path/to/voice.onnx
```

### `Custom` provider produces no audio

The command must write the audio to `{out_file}`. Check the wrapper script manually with the same placeholders. The pipeline converts MP3/other formats to WAV.

### File name too long on Windows

Shorten the series slug, episode slug, or voice id. The TTS cache uses `<beat-id>-<hash>`, which is usually short. Windows path limits can still bite with deep series directories.

### Permission denied when writing output

Check that the episode directory is writable and that no player has the MP4 open. Close the video player and rerun.

### Manim output not found after a successful render

`render.py` searches `media/` for `<episode-id>-<slug>.mp4`. Check the Manim log for the actual path. If you changed the scene file name or class name, pass `--scene` to match.

### `manim render` vs `manim`

Manim 0.22 introduced the `render` subcommand. `render.py` detects the version. If you call Manim manually with an older version, omit `render`.

## Platform notes

### Windows

- Use PowerShell or Git Bash consistently.
- If `manim` is not on PATH, activate the virtual environment first, or set `MANIM_BIN` to the venv's `manim.exe`.
- The pip user-scripts directory is often `%APPDATA%\Python\Python314\Scripts`; add it to PATH if you want the global `manim` command outside the venv.
- Long paths can be enabled in Windows settings, but shorter paths are safer.
- `winget install Gyan.FFmpeg` and `winget install MiKTeX.MiKTeX` are convenient.
- If `latex` is installed but not found, add the MiKTeX `bin` directory to PATH and restart the terminal.

### macOS

- Apple Silicon and Intel both work with Manim Community.
- `brew install --cask mactex-no-gui` is large; TinyTeX is smaller.
- Use `python3` explicitly if `python` is not the virtual environment.

### Linux

- Install Cairo/Pango development packages if the Manim wheel cannot find them.
- For headless servers, use the Cairo renderer (the default) and ensure `ffmpeg`/PyAV are available.
- If fonts are missing, install `fonts-dejavu` and `fonts-noto`.

### Containers / CI

- Pin Python, Manim, edge-tts, and LaTeX versions.
- Cache `media/` and the TTS cache between runs.
- Render `draft` in CI; render final locally or on a larger runner.
- Do not store API keys in the repository.

## Getting help

Include:

- the exact command;
- the full traceback or Manim log tail;
- `python scripts/check_env.py --json`;
- `python scripts/check_env.py --color always` or `--no-color` when piping output;
- the Manim version (`manim --version`);
- the operating system;
- whether the failure is in TTS, Manim, or QA.
