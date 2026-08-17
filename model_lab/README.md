# SonicTrace V4 Model Lab — CLaMP3 / MERT

Status: **experimental parallel benchmark only**. This folder does **not** replace SonicTrace V3 and does **not** touch SHINOBIWAN STUDIO.

## Why this lab exists

The V3 CLAP + Discogs pipeline reached a point where real tracks could receive obviously wrong raw zero-shot labels before any SonicTrace guard ran. V4 Model Lab tests whether a music-specialized representation can reduce that upstream error instead of adding more track-specific rules.

## Candidate A — CLaMP 3 SAAS

Official project: `https://github.com/sanderwood/clamp3`

Pinned source commit for this lab:

`9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8`

Official audio pipeline used by this lab:

`audio -> MERT-v1-95M -> CLaMP 3 SAAS -> shared 768D music/text embedding -> cosine similarity`

CLaMP3's official repository describes music-to-text retrieval as a zero-shot classification path and uses MERT features for audio. The lab deliberately uses the official model rather than reimplementing its neural network.

## Isolation contract

- runtime: `model_lab/.runtime/`
- separate Python 3.10 environment: `model_lab/.runtime/venv/`
- separate CLaMP3 checkout: `model_lab/.runtime/clamp3/`
- separate Hugging Face cache: `model_lab/.runtime/huggingface/`
- results: `model_lab/results/`
- none of these local folders are committed
- no SonicTrace V3 backend dependency is replaced
- no STUDIO repository/file is touched

## Inference contract

**Audio only.** Track TXT metadata is never injected into CLaMP3 prompts and is never used to reorder inference results.

The taxonomy is split into independent axes:

1. `family`
2. `style`
3. `tradition`
4. `form`

This avoids forcing concepts such as `Nhạc Vàng` and `Vietnamese Bolero` to compete for one single label.

`benchmarks.json` contains artist-declared/reference knowledge **only for post-inference evaluation**.

## Double-click workflow (Windows)

### First time only

Double-click:

`SONICTRACE_V4_MODEL_LAB_SETUP.cmd`

It creates the isolated Python 3.10/CUDA runtime and checks out the pinned official CLaMP3 source. The first real benchmark may still download the CLaMP3 SAAS checkpoint (~2.57 GB) and MERT-v1-95M model files into the local cache.

### Benchmark

Double-click:

`SONICTRACE_V4_MODEL_LAB_BENCHMARK.cmd`

Select one or several WAV/MP3 files in the Windows picker.

Recommended first torture set:

- `THICK`
- `Tachy Psychia`
- `Stick to You`
- `Tinh Bolero Cho Trân`

For every track the lab records:

- Top-10 per semantic axis
- raw cosine similarities
- benchmark `PASS / NEAR / FAIL`
- total and per-axis runtime
- GPU name/driver
- peak observed NVIDIA VRAM usage
- exact CLaMP3 commit
- explicit `declared_metadata_used_for_inference: false`

Results are written as both JSON and human-readable TXT under `model_lab/results/`.

## Decision gate

CLaMP3 is **not** allowed to replace V3 merely because one showcase track looks better.

A future V4 integration candidate should first demonstrate, on the same runtime and taxonomy:

- THICK no longer collapsing into unrelated dance-pop/regional styles;
- Tachy Psychia landing inside its hard hybrid neighborhood;
- Stick to You remaining in a plausible Pop/Dancehall/Eurodance neighborhood;
- Tinh Bolero Cho Trân remaining Vietnamese/Bolero without TXT forcing;
- acceptable RTX 3060 runtime and VRAM;
- no regression toward overconfident single-label behavior.

If CLaMP3 fails this gate, the lab remains disposable and SonicTrace V3 is untouched.

## Candidate B (later)

MuQ-MuLan remains a Phase-2 challenger, not a dependency of this first lab. Its official weights use a non-commercial license, so benchmark results and licensing must be evaluated separately before any product decision.
