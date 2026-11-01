# TODO — manim-math-video-studio fixes

Source: read-only code analysis, 2026-11-01 (Manim 0.22.0, edge-tts 7.3.1). Read-only probe results are marked ✅ (reproduced).

## P0 — data loss / broken output (fix first)

- [ ] **render.py dry-run deletes existing deliverables** ✅
  `manim-math-video/scripts/render.py:200-205` — `final_video.unlink()` / `final_srt.unlink()` run before the `--dry-run` return at line 209, and before the render success check. A dry run (or failed render) destroys the previous good MP4/SRT.
  Fix: move the unlink after validation + dry-run gate; only replace on success (rename or copy-then-swap). Also give `final_srt` the quality suffix so `draft` doesn't overwrite the `standard` SRT.
- [ ] **Bars render off-frame with default y_range** ✅
  `manim-math-video/assets/project/manim_lib/graphs.py` bars branch (~line 374) — generic default `[-3,3,1]`; values like `[12,27,19]` produce a 25-unit group centered at y≈+10. Fix: derive `y_range` from values when absent, or reject with a clear error. Update the bars example in `references/graphs.md` (it omits `y_range`).
- [ ] **`text` annotation renders nothing** ✅
  `graphs.py:544-549` — `make_label()` returns `None` unless `label`/`latex` is set; the schema-required `text` field is never read. Fix: fall back to `raw["text"]`.
- [ ] **`animation: "area"` is accepted and documented but does nothing** ✅
  `_common.py` validates it, `references/graphs.md:310` advertises it, `runtime.render_graph` has no branch. Fix: implement (animate the `area` annotation) or drop from validator + docs.
- [ ] **Late-binding lambdas in annotation plots (B023)** — real bug class
  `graphs.py:593, 614, 632, 650, 722` — `lambda t: fn(...)`, `lambda t: y1 + slope*(t-x1)`, etc. close over loop variables reassigned on the next annotation; multiple annotations can end up plotting the *last* one's line. Fix: bind defaults (`lambda t, fn=fn: ...`) or build via a factory. Verify with two secant/tangent annotations with different coordinates.

## P1 — installer safety

- [ ] **`install.py --uninstall` downloads the whole repo when state is missing**
  `uninstall()` calls `resolve_source(None)` just to read `platforms/manifest.json`; with no state file and no network it dies. Fix: derive roots from a built-in fallback map (or read the manifest from the script's own directory when present) — never download on uninstall.
- [ ] **`platforms/build.py --install` destroys targets without preserving `.venv`/state**
  `build.py install()` rmtrees the target; `install.py copy_skill()` preserves `.venv`. Fix: share one copy routine.
- [ ] **`copy_skill` stash race** ✅
  `install.py` — fixed stash path `.manim-math-video-venv-stash` + rmtree; concurrent or crashed installs can destroy the environment. Fix: unique temp name + atomic rename.
- [ ] **`install.ps1` cannot pin tags** ✅
  `install.ps1:92` hardcodes `/zip/refs/heads/$Ref`; `-Ref v0.2.0` fails. Fix: switch `heads`→`tags` for `v*`, mirroring `install.py download_source()`.
- [ ] **`--no-deps` runs `check_env.py` with the system interpreter and reports "blocking issues"**
  Either skip verification when `--no-deps` (with a clear message) or make the message explain the intent.

## P2 — correctness / robustness

- [ ] **`duration_hint` ignored for reused silent segments** ✅
  `tts.py:452-463` — reuse branch keeps the stored duration unconditionally. Changing pacing for silent beats requires `--force`; docs don't say so. Fix: honor `duration_hint` on reuse when the text/hash matches, or document + warn.
- [ ] **Caption cues start before the beat's animations** ✅ (by construction)
  `runtime.voiceover()` adds subcaptions at t=0 while animations begin afterwards; drift accumulates per beat. Fix: emit first cue after intro animations, and/or use `manifest.json` word timings (already stored, never consumed).
- [ ] **Validators crash on malformed JSON** ✅
  `_common.validate_brief` (`series: []` → AttributeError), `validate_storyboard` (`beats: ["oops"]`), `validate_manifest` (`duration: "abc"` → ValueError). Fix: type-guard each section, catch conversion errors, report as validation errors. Add a `--json`-only crash regression test.
- [ ] **Schemas are decorative**
  `assets/brief.schema.json`, `assets/storyboard.schema.json` are never enforced (no `jsonschema` dependency). Either wire schema validation into `validate.py` (add dependency) or delete the claim from docs. At minimum validate `hold` exists (changelog advertises it, nothing checks it).
- [ ] **`validate_manifest` no-op branch**
  `_common.py:733-736` — relative audio path check is `pass`. Implement (needs episode dir) or remove.
- [ ] **`new_episode.py --force` overwrites a filled storyboard** ✅ (by code)
  Guard destroys `storyboard.json`, `script.md`, `episode.py` work without backup. Fix: refuse when `storyboard.json` differs from the skeleton, or back it up.
- [ ] **Series registry written even when episode scaffolding fails**
  `new_episode.py:391-414` — move the registry update after all file writes succeed.
- [ ] **`atomic_write_json` is not atomic across writers** ✅ (by code)
  `_common.py:186-192` — fixed `*.tmp` name; concurrent runs corrupt. Fix: `tempfile.NamedTemporaryFile(dir=parent, delete=False)` + `os.replace`.
- [ ] **Custom TTS sample suffix**: `voice_samples.py` writes `--custom-suffix .mp3` samples unconverted while tts.py converts to WAV. Align behavior.

## P3 — hygiene / docs

- [ ] **Unused imports / variables (ruff F401/F841, verified)**
  `graphs.py` (`sample_values`, `maximum`), `runtime.py` (`math`, `GraphSpecError`, `color`), `check_env.py` (`Path`), `new_episode.py` (`ASSETS`, `QUALITY_PRESETS`), `qa.py` (`json`), `render.py` (`json`), `storyboard_to_script.py` (`Path`), `tts.py` (`load_template`), `validate.py` (`load_voices`). Also `zip(..., strict=True)` for the 4 B905 sites.
- [ ] **Docs claim `--strict-qa` and smoke tests that don't exist yet**
  `tests/`, `.github/workflows/`, `.dockerignore` are untracked/uncommitted while `INSTALL.md` references `tests/install_matrix.py`. Commit them or drop the references.
- [ ] **`my-series/brief.json` says `skill_version: 1.2.0`** while SKILL.md metadata is `1.3.0`. Either regenerate the artifact or make `validate.py` warn on `skill_version` drift.
- [ ] **USAGE.md quick start**: "copy the demo storyboard" produces an episode_id/title mismatch that validation flags. Fix the doc step (edit fields) or provide a `--example` scaffold.
- [ ] **Version drift in docs/index.html**: mixed `blob/main` links and hardcoded `v0.2.0` release links; make refs consistent at next release.
- [ ] **`qa.py` brightness**: clean-light background (~luma 240) sits 7 points below the "nearly white" threshold; confirm no false positives at 1080p or raise the threshold.

## Verification before closing

```bash
python -m ruff check --select F,E9,B --ignore F405,F403 manim-math-video/scripts manim-math-video/assets/project/manim_lib tests/install_matrix.py
python platforms/build.py --check
python tests/install_matrix.py --scope fast
python manim-math-video/scripts/selftest.py
```

Plus targeted probes: two-annotation tangent/secant plot (P0 B023), bars with default ranges, `text` annotation visible in a draft render, dry-run preserves existing `output/`.
