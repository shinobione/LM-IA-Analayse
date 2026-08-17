# SonicTrace V4 Model Lab — CLaMP3 / MERT + MuQ-MuLan

Status: **experimental parallel benchmark only**. This folder does **not** replace SonicTrace V3 and does **not** touch SHINOBIWAN STUDIO.

Latest real benchmark decision record:

`model_lab/BENCHMARK-VERDICT-2026-08-17.md`

## Why this lab exists

The V3 CLAP + Discogs pipeline reached a point where real tracks could receive obviously wrong raw zero-shot labels before any SonicTrace guard ran. V4 Model Lab tests whether a music-specialized representation can reduce that upstream error instead of adding more track-specific rules.

## Candidate A — CLaMP 3 SAAS

Official project: `https://github.com/sanderwood/clamp3`

Pinned source commit for this lab:

`9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8`

Official audio pipeline used by this lab:

`audio -> MERT-v1-95M -> CLaMP 3 SAAS -> shared 768D music/text embedding -> cosine similarity`

CLaMP3's official repository describes music-to-text retrieval as a zero-shot classification path and uses MERT features for audio. The lab deliberately uses the official model rather than reimplementing its neural network.

Real four-track verdict: useful, but still too diffuse on THICK and Tachy Psychia to become the main V4 ear. It remains a preserved challenger / reference implementation.

## Candidate B — MuQ-MuLan 700M

Model: `OpenMuQ/MuQ-MuLan-large`

Lab policy:

- fp32
- 24 kHz audio
- five deterministic evenly-spaced 10-second clips per track
- normalized clip embeddings, mean pooling, final renormalization
- separate runtime: `model_lab/.runtime/muq_venv/`
- weights treated as **non-commercial / lab-only** by this project

Real four-track verdict on RTX 3060 12 GB:

- Stick to You: **PASS** — `Pop` + `Dancehall Pop` #1
- Tachy Psychia: **PASS** — `Hip-Hop / Rap` + `Drift Phonk` #1 + `Electronic Hybrid` #1
- THICK: **PASS** — `Hip-Hop / Rap` + `Drift Phonk` #1; canonical Dancehall-Pop collapse removed
- Tình Bolero Cho Trân: **FAIL on family only** — raw family remains `Pop`, while `Vietnamese Bolero` #1, `Nhạc Trữ Tình` #1 and `Sentimental Ballad` #1 are all correct/coherent

MuQ-MuLan is therefore the **strongest raw neural challenger measured so far**, but it is **not promoted into product runtime**. The Bolero family failure remains real and the current weight-license boundary prevents a SonicTrace/STUDIO product decision.

See `BENCHMARK-VERDICT-2026-08-17.md` for the exact captured scores, runtime/VRAM observations and next gate.

## Isolation contract

- runtime: `model_lab/.runtime/`
- separate CLaMP3 Python 3.10 environment: `model_lab/.runtime/venv/`
- separate MuQ environment: `model_lab/.runtime/muq_venv/`
- separate CLaMP3 checkout: `model_lab/.runtime/clamp3/`
- separate Hugging Face cache: `model_lab/.runtime/huggingface/`
- results: `model_lab/results/`
- none of these local folders are committed
- no SonicTrace V3 backend dependency is replaced
- no STUDIO repository/file is touched

## Inference contract

**Audio only.** Track TXT metadata is never injected into challenger prompts and is never used to reorder inference results.

The taxonomy is split into independent axes:

1. `family`
2. `style`
3. `tradition`
4. `form`

This avoids forcing concepts such as `Nhạc Vàng` and `Vietnamese Bolero` to compete for one single label.

`benchmarks.json` contains artist-declared/reference knowledge **only for post-inference evaluation**.

## Double-click workflow (Windows)

### CLaMP3 — first time only

Double-click:

`SONICTRACE_V4_MODEL_LAB_SETUP.cmd`

It creates the isolated Python 3.10/CUDA runtime and checks out the pinned official CLaMP3 source. The first real benchmark may still download the CLaMP3 SAAS checkpoint (~2.57 GB) and MERT-v1-95M model files into the local cache.

### CLaMP3 benchmark

Double-click:

`SONICTRACE_V4_MODEL_LAB_BENCHMARK.cmd`

### MuQ-MuLan — first time / runtime repair

Double-click:

`SONICTRACE_V4_MUQ_MULAN_SETUP.cmd`

The setup pins the isolated MuQ stack to Torch 2.4.1 cu118 + Transformers 4.46.3 and refuses to print READY unless CUDA, the Transformers PyTorch backend and the `MuQMuLan` class are all usable.

### MuQ-MuLan benchmark

Double-click:

`SONICTRACE_V4_MUQ_MULAN_BENCHMARK.cmd`

Select one or several WAV/MP3 files in the Windows picker.

Recommended torture set:

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
- exact model/runtime identity where applicable
- explicit `declared_metadata_used_for_inference: false`

Results are written as JSON and/or human-readable TXT under `model_lab/results/` depending on the challenger runner.

## Decision gate

No challenger is allowed to replace V3 merely because one showcase track looks better.

A future V4 integration candidate should demonstrate, on the same runtime and taxonomy:

- THICK no longer collapsing into unrelated dance-pop/regional styles;
- Tachy Psychia landing inside its hard hybrid neighborhood;
- Stick to You remaining in a plausible Pop/Dancehall/Eurodance neighborhood;
- Tinh Bolero Cho Trân remaining Vietnamese/Bolero without TXT forcing;
- acceptable RTX 3060 runtime and VRAM;
- no regression toward overconfident single-label behavior;
- a production-compatible license for any checkpoint intended to ship with SonicTrace/STUDIO.

MuQ-MuLan currently leads the quality benchmark but does **not** clear the complete product gate. The next lab phase is to benchmark a production-eligible challenger/architecture against the same four tracks, with MuQ retained as the current quality reference.
