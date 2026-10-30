# Demo episode

![Contact sheet](demo-preview.jpg)

`demo-series/` contains the source for a verified 3-minute episode:

- **Series:** Path of Knowledge
- **Episode:** `s01e001` — Why the derivative of x² is 2x
- **Template:** `clean-light`
- **Quality:** draft 480p15 was rendered and QA'd; the brief targets `standard` 1080p30
- **Voice:** `en-US-AvaMultilingualNeural` (`warm-teacher`, `-3%`)
- **Language:** `en-US`
- **Duration:** ~167 s

The generated MP4, WAV files, and media cache are intentionally not committed. The preview above is the contact sheet from the verified draft render. Regenerate the artifacts with:

```bash
cd manim-math-video
export PATH="/path/to/TinyTeX/bin/windows:$PATH"   # if LaTeX is not already on PATH

python scripts/validate.py --episode examples/demo-series/episodes/001-why-derivative-x-squared
python scripts/tts.py --episode examples/demo-series/episodes/001-why-derivative-x-squared
python scripts/render.py --episode examples/demo-series/episodes/001-why-derivative-x-squared --quality draft
```

The source includes the full storyboard, the readable script, the theme snapshot, and the standalone `manim_lib/` runtime. The rendered QA report showed:

- 854x480 at 15 fps
- AAC narration present; peak -5.0 dB, RMS -23.7 dB
- 37 subtitle cues, 96% coverage
- No QA warnings after the target duration was set to 180 s

To regenerate the preview contact sheet:

```bash
python scripts/qa.py \
  --video examples/demo-series/episodes/001-why-derivative-x-squared/output/*.mp4 \
  --srt examples/demo-series/episodes/001-why-derivative-x-squared/output/*.srt \
  --out-dir examples/demo-series/episodes/001-why-derivative-x-squared/qa
```
