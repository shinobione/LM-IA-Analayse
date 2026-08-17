# SonicTrace V4 Model Lab — CLaMP3 / MERT + MuQ-MuLan + Microsoft CLAP

Status: **experimental parallel benchmark only**. This folder does **not** replace SonicTrace V3 and does **not** touch SHINOBIWAN STUDIO.

Latest completed real benchmark decision record:

`model_lab/BENCHMARK-VERDICT-2026-08-17.md`

## Why this lab exists

The V3 CLAP + Discogs pipeline reached a point where real tracks could receive obviously wrong raw zero-shot labels before any SonicTrace guard ran. V4 Model Lab tests whether a different musical/audio-language representation can reduce that upstream error instead of adding more track-specific rules.

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

MuQ-MuLan is therefore the **strongest raw neural challenger measured so far**, but it is **not promoted into product runtime**. The Bolero family failure remains real and the current non-commercial weight-license boundary prevents a SonicTrace/STUDIO product decision.

See `BENCHMARK-VERDICT-2026-08-17.md` for the exact captured scores, runtime/VRAM observations and next gate.

## Candidate C — Microsoft CLAP 2023

Official code: `microsoft/CLAP`, pinned for this lab to:

`e8a6467b87cd85716e20c6a008126150d9740be0`

Official Python package / checkpoint path:

- package: `msclap==1.3.3`
- version: `2023`
- checkpoint: `microsoft/msclap / CLAP_weights_2023.pth`
- checkpoint SHA-256 recorded by the lab: `2cef4016d47d00eb28d153d522f397222057f95000e9bad6b9583c631284a1e6`
- code license: MIT
- checkpoint license: MS-PL

The Microsoft checkpoint is **not** marked non-commercial. It is therefore a candidate for the product-license gate, subject to full compliance with MS-PL terms and a product legal review before any shipping decision. The Model Lab does not interpret that as unconditional legal clearance.

Microsoft CLAP 2023 uses 44.1 kHz audio and a 7-second model duration. The upstream wrapper normally random-trims audio longer than its duration. SonicTrace does **not** allow that randomness in the benchmark: Candidate C first decodes the source and creates five deterministic evenly-spaced **exact 7-second clips**. Only those clips are sent to the official `msclap` embedding API. Exact-duration clips take the wrapper's deterministic duration branch, so no truth-aware or random passage selection can occur.

The same unchanged `family / style / tradition / form` taxonomy and the same four-track post-inference benchmark are used. No V3 rule, taxonomy weight or expected answer is modified to favor Candidate C.

Candidate C is intentionally a separate checkpoint/implementation from SonicTrace V3, whose current default neural model is LAION CLAP. Its purpose is to measure whether a commercially plausible audio-language checkpoint can approach MuQ quality before we look at any product integration.

## Isolation contract

- runtime: `model_lab/.runtime/`
- separate CLaMP3 Python 3.10 environment: `model_lab/.runtime/venv/`
- separate MuQ environment: `model_lab/.runtime/muq_venv/`
- separate Microsoft CLAP environment: `model_lab/.runtime/msclap_venv/`
- separate CLaMP3 checkout: `model_lab/.runtime/clamp3/`
- shared isolated Hugging Face cache: `model_lab/.runtime/huggingface/`
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

### CLaMP3 benchmark

Double-click:

`SONICTRACE_V4_MODEL_LAB_BENCHMARK.cmd`

### MuQ-MuLan — first time / runtime repair

Double-click:

`SONICTRACE_V4_MUQ_MULAN_SETUP.cmd`

### MuQ-MuLan benchmark

Double-click:

`SONICTRACE_V4_MUQ_MULAN_BENCHMARK.cmd`

### Microsoft CLAP 2023 — first time only

Double-click:

`SONICTRACE_V4_MS_CLAP_SETUP.cmd`

It creates `model_lab/.runtime/msclap_venv/`, pins the CUDA runtime used by this lab, installs `msclap==1.3.3`, and verifies CUDA plus the official `CLAP` class import. It does not instantiate or download the checkpoint until the benchmark.

### Microsoft CLAP 2023 benchmark

Double-click:

`SONICTRACE_V4_MS_CLAP_BENCHMARK.cmd`

Select the same WAV/MP3 torture set:

- `THICK`
- `Tachy Psychia`
- `Stick to You`
- `Tinh Bolero Cho Trân`

For every track the lab records:

- Top-10 per semantic axis
- raw cosine similarities
- benchmark `PASS / NEAR / FAIL`
- total runtime
- GPU name/driver
- peak observed NVIDIA VRAM usage
- exact model/runtime identity where applicable
- explicit `declared_metadata_used_for_inference: false`

Results are written as JSON and human-readable TXT under `model_lab/results/`.

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

MuQ-MuLan currently leads the quality benchmark but does **not** clear the complete product gate. Candidate C now asks a narrower question: can Microsoft CLAP 2023, under a materially more product-compatible license boundary than MuQ's non-commercial weights, approach that quality on the exact same torture set?

No catalogue embedding migration and no SonicTrace/STUDIO integration occurs during this benchmark phase.
