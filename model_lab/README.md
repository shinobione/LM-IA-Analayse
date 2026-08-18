# SonicTrace V4 Model Lab — neural challenger benchmark

Status: **experimental parallel benchmark only**. This folder does **not** replace SonicTrace V3 and does **not** touch SHINOBIWAN STUDIO.

Latest completed real benchmark decision records:

- `model_lab/BENCHMARK-VERDICT-2026-08-17.md` — CLaMP3 vs MuQ-MuLan
- `model_lab/BENCHMARK-VERDICT-2026-08-18.md` — Microsoft CLAP Candidate C closeout
- `model_lab/BENCHMARK-VERDICT-2026-08-18-CANDIDATE-D.md` — Hugging Face Larger CLAP Music conversion closeout
- `model_lab/BENCHMARK-VERDICT-2026-08-18-CANDIDATE-E.md` — native LAION music checkpoint closeout

## Why this lab exists

The V3 CLAP + Discogs pipeline reached a point where real tracks could receive obviously wrong raw zero-shot labels before any SonicTrace guard ran. V4 Model Lab tests whether a different musical/audio-language representation can reduce that upstream error instead of adding more track-specific rules.

The same four-track torture set and unchanged taxonomy are reused for every challenger. Artist TXT/reference metadata is loaded **only after inference** for benchmark scoring.

## Current ranking

### 1. Candidate B — MuQ-MuLan 700M

Model: `OpenMuQ/MuQ-MuLan-large`

Real four-track verdict on RTX 3060 12 GB:

- Stick to You: **PASS** — `Pop` + `Dancehall Pop` #1
- Tachy Psychia: **PASS** — `Hip-Hop / Rap` + `Drift Phonk` #1 + `Electronic Hybrid` #1
- THICK: **PASS** — `Hip-Hop / Rap` + `Drift Phonk` #1; canonical Dancehall-Pop collapse removed
- Tình Bolero Cho Trân: **FAIL on family only** — raw family remains `Pop`, while `Vietnamese Bolero` #1, `Nhạc Trữ Tình` #1 and `Sentimental Ballad` #1 are coherent

MuQ-MuLan remains the **quality reference to beat**, but its current checkpoint weights are treated by this project as **CC-BY-NC-4.0 / lab-only**, so it is not promoted into SonicTrace/STUDIO product runtime.

Lab policy:

- fp32
- 24 kHz
- five deterministic evenly-spaced 10-second clips
- normalized clip embeddings, mean pooling, final renormalization
- isolated runtime: `model_lab/.runtime/muq_venv/`

### 2. Candidate A — CLaMP3 / MERT95M

Official source pinned to:

`9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8`

Pipeline:

`audio -> MERT-v1-95M -> CLaMP 3 SAAS -> shared 768D music/text embedding -> cosine similarity`

Real verdict: useful and materially different from V3, but still too diffuse on THICK and Tachy Psychia to become the main V4 ear. Preserved as a reference challenger.

### 3. Candidate E — Native LAION CLAP Music — rejected for quality

Native identity:

- package: `laion-clap==1.1.7`
- audio model: `HTSAT-base`
- fusion: disabled
- checkpoint: `music_audioset_epoch_15_esc_90.14.pt`
- checkpoint SHA-256: `fae3e9c087f2909c28a09dc31c8dfcdacbc42ba44c70e972b58c1bd1caf6dedd`
- code license: Apache-2.0
- checkpoint repository metadata: CC0-1.0

Real four-track result: **0 PASS / 1 NEAR**.

- Stick to You: **NEAR** — family `Pop`; intended Afropop / Dancehall Pop / Eurodance neighborhood is present, but `Synth-Pop` is primary
- Tachy Psychia: **FAIL** — family `Pop`, style `Eurodance`; hard-hybrid Phonk/Trap/Glitch/Drill neighborhood is not recovered
- THICK: **FAIL** — `Cyber Trap` appears #3, but `Pop` / `Eurodance` / `Euro-House` remain dominant
- Tình Bolero Cho Trân: **FAIL** — `Nhạc Trữ Tình` and `Nhạc Vàng` plus `Sentimental Ballad` are strong, but family is `Country / Acoustic` and style is `Contemporary R&B`; `Vietnamese Bolero` is only #2

Candidate E is a valid native-path benchmark — unlike Candidate D, its cosine scores are healthy and track rankings differ materially — but its quality is still below the SonicTrace gate. No prompt, threshold or rescue-rule tuning is performed to improve it.

See `BENCHMARK-VERDICT-2026-08-18-CANDIDATE-E.md`.

### 4. Candidate C — Microsoft CLAP 2023 — rejected for quality

Official code commit:

`e8a6467b87cd85716e20c6a008126150d9740be0`

Checkpoint:

`microsoft/msclap / CLAP_weights_2023.pth`

Real four-track result: **0/4 PASS**.

- Stick to You: `Dancehall Pop` style #1, but family incorrectly `R&B / Soul / Funk` and Vietnamese-tradition leakage
- Tachy Psychia: **`Dancehall Pop` #1** despite `Drift Phonk` in Top-5
- THICK: **`Dancehall Pop` #1**, recreating the canonical V3 failure
- Tình Bolero Cho Trân: style/tradition/form strong, but family still wrong

Operationally it is excellent on RTX 3060 (~0.4–0.5 s warmed, ~2.94 GiB peak VRAM, 1024D), but quality is not sufficient. It remains a fast/light reference only; no prompt or threshold tuning is performed to rescue it.

License boundary: MIT code / MS-PL checkpoint, with compliance/legal review required before any hypothetical product use.

## Candidate D — Hugging Face Larger CLAP Music — benchmark invalidated

Model:

`laion/larger_clap_music @ a0b4534`

The real RTX 3060 run completed technically but produced suspiciously collapsed semantic output: all four tracks failed, cosine similarities were mostly around `0.003–0.009`, and radically different songs received very similar rankings.

This is **not treated as clean evidence against the original LAION music checkpoint**. Upstream reports document a severe accuracy regression for the larger HTSAT-base checkpoints after conversion to Hugging Face Transformers, and the model's own Hugging Face discussion contains near-50/50 zero-shot outputs for obviously different candidate classes.

Candidate D is therefore preserved only as an **unreliable converted-path reference**. Do not tune SonicTrace prompts, thresholds, benchmark expectations, or rescue rules to improve it.

See `BENCHMARK-VERDICT-2026-08-18-CANDIDATE-D.md`.

## Next research candidate

Do **not** spend more rounds on additional LAION CLAP variants. Candidate E showed that the native music checkpoint is healthier than the converted Hugging Face path, but it still does not solve the hard-hybrid or Bolero authority problems.

The next architecture worth researching is **M2D-CLAP 2025** (`nttcslab/m2d`), because it is a newer audio-language representation and its official repository provides zero-shot classification support. It is not yet an active SonicTrace candidate: the repository points to a custom `LICENSE.pdf`, so its product/commercial boundary must be reviewed explicitly before any promotion. If benchmarked, it must use the exact same unchanged audio-only torture set and no TXT forcing.

## Isolation contract

- shared lab root: `model_lab/.runtime/`
- CLaMP3 env: `model_lab/.runtime/venv/`
- MuQ env: `model_lab/.runtime/muq_venv/`
- Microsoft CLAP env: `model_lab/.runtime/msclap_venv/`
- converted Larger CLAP env: `model_lab/.runtime/larger_clap_venv/`
- native LAION music env: `model_lab/.runtime/native_laion_music_venv/`
- native LAION checkpoint: `model_lab/.runtime/native_laion_music/`
- CLaMP3 checkout: `model_lab/.runtime/clamp3/`
- shared Hugging Face cache: `model_lab/.runtime/huggingface/`
- generated results: `model_lab/results/`
- none of the local runtimes/results are committed
- no SonicTrace V3 backend dependency is replaced
- no catalogue migration occurs during the benchmark phase
- no SHINOBIWAN STUDIO file is touched

## Inference contract

**Audio only.** Track TXT metadata is never injected into challenger prompts and never reorders inference output.

The taxonomy is split into independent axes:

1. `family`
2. `style`
3. `tradition`
4. `form`

`benchmarks.json` contains artist-declared/reference knowledge **only for post-inference evaluation**.

## Double-click workflow (Windows)

### CLaMP3

- setup: `SONICTRACE_V4_MODEL_LAB_SETUP.cmd`
- benchmark: `SONICTRACE_V4_MODEL_LAB_BENCHMARK.cmd`

### MuQ-MuLan

- setup/repair: `SONICTRACE_V4_MUQ_MULAN_SETUP.cmd`
- benchmark: `SONICTRACE_V4_MUQ_MULAN_BENCHMARK.cmd`

### Microsoft CLAP 2023

- setup/repair: `SONICTRACE_V4_MS_CLAP_SETUP.cmd`
- benchmark: `SONICTRACE_V4_MS_CLAP_BENCHMARK.cmd`

### Candidate D — converted LAION Larger CLAP Music

Preserved only for reproducibility; no further tuning is planned:

- setup: `SONICTRACE_V4_LARGER_CLAP_MUSIC_SETUP.cmd`
- benchmark: `SONICTRACE_V4_LARGER_CLAP_MUSIC_BENCHMARK.cmd`

### Candidate E — native LAION CLAP Music

Preserved as a completed native-path reference; no further tuning is planned:

- setup: `SONICTRACE_V4_NATIVE_LAION_MUSIC_SETUP.cmd`
- benchmark: `SONICTRACE_V4_NATIVE_LAION_MUSIC_BENCHMARK.cmd`

Candidate E reports:

- `model_lab/results/native-laion-music-benchmark-YYYYMMDD-HHMMSS.json`
- `model_lab/results/native-laion-music-benchmark-YYYYMMDD-HHMMSS.txt`
- `model_lab/results/native-laion-music-last-run.log`
- `model_lab/results/native-laion-music-last-error.txt` on failure

Every report records Top rankings, raw cosine similarities, benchmark status, runtime, GPU/VRAM, checkpoint identity/hash and explicit `declared_metadata_used_for_inference: false`.

## Decision gate

No challenger replaces V3 merely because one showcase track looks better.

A future V4 integration candidate should demonstrate simultaneously:

- THICK no longer collapsing into unrelated Dancehall/Eurodance output;
- Tachy Psychia landing inside its hard hybrid Phonk/Trap/Glitch/Drill neighborhood;
- Stick to You remaining in a plausible Pop/Dancehall/Eurodance/Afropop neighborhood;
- Tình Bolero Cho Trân remaining Vietnamese/Bolero without TXT forcing;
- acceptable RTX 3060 runtime and VRAM;
- stable/reproducible deterministic inference;
- a production-compatible model/license boundary.

Until that gate is passed, MuQ-MuLan remains the raw quality reference, SonicTrace V3 remains intact, no catalogue embedding migration occurs, and STUDIO remains untouched.
