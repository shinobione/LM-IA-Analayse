# SonicTrace V4 Model Lab — neural challenger benchmark

Status: **experimental parallel benchmark only**. This folder does **not** replace SonicTrace V3, does **not** migrate Catalogue V2-E embeddings and does **not** touch SHINOBIWAN STUDIO.

## Current decision

The first challenger that demonstrated the target level of raw music understanding is still **MuQ-MuLan 700M**.

Real RTX 3060 four-track result:

- Stick to You: **PASS** — `Pop` + `Dancehall Pop` #1
- Tachy Psychia: **PASS** — `Hip-Hop / Rap` + `Drift Phonk` #1 + `Electronic Hybrid` #1
- THICK: **PASS** — `Hip-Hop / Rap` + `Drift Phonk` #1; the canonical Dancehall-Pop collapse disappears
- Tình Bolero Cho Trân: **FAIL on family only** — family stays `Pop`, but `Vietnamese Bolero` #1, `Nhạc Trữ Tình` #1 and `Sentimental Ballad` #1 are coherent

MuQ therefore remains the **raw quality reference to beat**. Its current weights are treated by SonicTrace as **CC-BY-NC-4.0 / lab-only**, so it is not promoted into a future commercial product runtime.

No challenger is promoted merely because it is faster or has a better license. Quality must approach MuQ on the same unchanged tracks first.

## Completed benchmark records

- `BENCHMARK-VERDICT-2026-08-17.md` — CLaMP3 vs MuQ-MuLan
- `BENCHMARK-VERDICT-2026-08-18.md` — Microsoft CLAP Candidate C closeout
- `BENCHMARK-VERDICT-2026-08-18-CANDIDATE-D.md` — Hugging Face Larger CLAP Music conversion closeout
- `BENCHMARK-VERDICT-2026-08-18-CANDIDATE-E.md` — native LAION music checkpoint closeout
- `BENCHMARK-VERDICT-2026-08-18-CANDIDATE-F.md` — M2D-CLAP 2025 closeout
- `CANDIDATE-G-FEASIBILITY-2026-08-18.md` — MOSS-Music 8B feasibility gate

## Why this lab exists

The V3 CLAP + Discogs pipeline reached a point where real tracks could receive obviously wrong raw zero-shot labels before any SonicTrace guard ran. The canonical example was `THICK` collapsing toward Dancehall/Eurodance before downstream rescue logic.

The Model Lab tests whether a materially different music representation can solve the upstream understanding problem instead of adding more track-specific rules.

The same four-track torture set and unchanged taxonomy are reused for every compatible embedding challenger. Artist TXT/reference metadata is loaded **only after inference** for benchmark scoring.

## Completed challengers

### Candidate A — CLaMP3 / MERT95M

Pinned source:

`9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8`

Pipeline:

`audio -> MERT-v1-95M -> CLaMP 3 SAAS -> shared 768D music/text embedding -> cosine similarity`

Verdict: useful and materially different from V3, good on Stick and several Bolero axes, but too diffuse on THICK and Tachy Psychia to become the main V4 ear.

### Candidate B — MuQ-MuLan 700M — current quality reference

Model: `OpenMuQ/MuQ-MuLan-large`

Policy:

- fp32
- 24 kHz
- five deterministic evenly-spaced 10-second clips
- normalized clip embeddings, mean pooling, final renormalization
- isolated runtime: `model_lab/.runtime/muq_venv/`

Verdict: **3 PASS / 1 family-only FAIL**. Best real result so far.

Product boundary: current checkpoint treated as **CC-BY-NC-4.0 / lab-only**.

### Candidate C — Microsoft CLAP 2023 — rejected for quality

- package: `msclap==1.3.3`
- checkpoint: `microsoft/msclap / CLAP_weights_2023.pth`
- real result: **0/4 PASS**
- operationally excellent on RTX 3060 (~0.4–0.5 s warmed, ~2.94 GiB peak VRAM)

Verdict: fast/light reference only. It recreates the canonical Dancehall-Pop problem on THICK/Tachy.

### Candidate D — Hugging Face Larger CLAP Music — benchmark invalidated

Model: `laion/larger_clap_music @ a0b4534`

The real run produced suspiciously collapsed cosine output around `0.003–0.009` across radically different tracks. This converted-path result is retained only for reproducibility and is not treated as clean evidence against the original checkpoint.

### Candidate E — Native LAION CLAP Music — rejected for quality

- package: `laion-clap==1.1.7`
- audio model: HTSAT-base
- checkpoint: `music_audioset_epoch_15_esc_90.14.pt`
- real result: **0 PASS / 1 NEAR / 3 FAIL**
- peak VRAM: ~5.45 GiB
- warmed runtime: ~0.4–1 s / track

Verdict: native path is technically healthy, but quality remains below the SonicTrace gate.

### Candidate F — M2D-CLAP 2025 — rejected for quality

Pinned source:

`nttcslab/m2d @ 3d0c4de9447c404a8d3f9f37e04f53bc902e09b3`

Release/model:

- `v0.5.0`
- `m2d_clap_vit_base-80x1001p16x16p16kpBpTI-2025`
- `checkpoint-30.pth`
- 16 kHz / exact 10-second clips / 768D shared embedding

Real result: **0 PASS / 1 NEAR / 3 FAIL**.

- Stick to You: NEAR
- Tachy Psychia: FAIL
- THICK: FAIL
- Tình Bolero Cho Trân: FAIL

Operationally it is excellent (~3.4 GiB peak VRAM and ~0.3 s / warmed track), but it does not approach MuQ's music understanding. No taxonomy, prompt, threshold or rescue-rule tuning is performed to improve it.

License status remains custom upstream `LICENSE.pdf` / **LAB ONLY**.

## Candidate G — MOSS-Music-8B-Instruct — feasibility gate only

Candidate G is deliberately different from the CLAP-style cosine benchmark family. MOSS-Music is a generative music-understanding model targeting genre/style, mood, instrumentation, structure, chord/key/tempo reasoning, lyrics and long-form musical QA.

Target upstream inspected for G0:

- repository: `OpenMOSS/MOSS-Music`
- source commit: `ad107c7ddaa06de168a0dfbc18d3e1e6a40c0e5e`
- model: `OpenMOSS-Team/MOSS-Music-8B-Instruct`
- total size: ~9.1B parameters
- backbone: Qwen3-8B + MOSS-Audio-Encoder
- published dtype: BF16
- license: Apache-2.0

### RTX 3060 gate

BF16/FP16 is not a valid 12 GB pure-GPU target: the raw ~9.1B BF16 weights alone exceed the card's VRAM before activations/audio/KV cache.

8-bit is also not considered a safe enough target for a 12 GB card.

Only a future **isolated 4-bit proof** is worth attempting, and upstream currently does not publish/document an official 4-bit MOSS-Music recipe. Therefore **no model weights are downloaded yet**.

Run the zero-download local preflight first:

`SONICTRACE_V4_MOSS_MUSIC_G_PREFLIGHT.cmd`

It checks:

- NVIDIA GPU / total + free VRAM / driver;
- free disk space;
- WSL availability;
- uv availability;
- whether the workstation is even eligible for a later quantized G1 experiment.

It installs nothing and downloads nothing. See `CANDIDATE-G-FEASIBILITY-2026-08-18.md`.

## Model Lab cleanup

All V4 challenger runtimes, checkpoints and caches are isolated under `model_lab/.runtime/`; benchmark reports live under `model_lab/results/` and are preserved by the cleanup utility.

Double-click:

`SONICTRACE_V4_MODEL_LAB_CLEANUP.cmd`

Menu:

1. **Nettoyage sûr** — keep MuQ + CLaMP3 + shared cache + results; remove rejected Candidate C/D/E/F local runtimes/assets and their dedicated large HF cache entries.
2. **Nettoyage fort** — keep MuQ + shared cache + results; also remove CLaMP3 venv/checkout.
3. **Tout nettoyer** — remove the complete local V4 runtime/cache tree, but keep benchmark results.
4. **Afficher l'espace disque** — show per-folder and total Model Lab runtime usage.

The cleanup script never targets SonicTrace V3 `backend/.venv`, Catalogue V2-E, JS product code or SHINOBIWAN STUDIO.

## Isolation contract

- shared lab root: `model_lab/.runtime/`
- CLaMP3 env: `model_lab/.runtime/venv/`
- CLaMP3 checkout: `model_lab/.runtime/clamp3/`
- MuQ env: `model_lab/.runtime/muq_venv/`
- Microsoft CLAP env: `model_lab/.runtime/msclap_venv/`
- converted Larger CLAP env: `model_lab/.runtime/larger_clap_venv/`
- native LAION env/assets: `model_lab/.runtime/native_laion_music_venv/`, `model_lab/.runtime/native_laion_music/`
- M2D env/assets/source: `model_lab/.runtime/m2d_clap_2025_venv/`, `model_lab/.runtime/m2d_clap_2025/`, `model_lab/.runtime/m2d_clap_2025_src/`
- shared Hugging Face cache: `model_lab/.runtime/huggingface/`
- generated results: `model_lab/results/`
- none of the local runtimes/results are committed
- no SonicTrace V3 backend dependency is replaced
- no catalogue migration occurs during benchmark/feasibility work
- no SHINOBIWAN STUDIO file is touched

## Inference contract

For embedding challengers, inference is **audio only**. Track TXT metadata is never injected into prompts and never reorders inference output.

The benchmark taxonomy is split into independent axes:

1. `family`
2. `style`
3. `tradition`
4. `form`

`benchmarks.json` contains artist-declared/reference knowledge **only for post-inference evaluation**.

A generative challenger such as MOSS-Music must preserve the same anti-cheating boundary: artist TXT/reference truth remains unavailable to the model during analysis and is loaded only afterward for evaluation.

## Reproducibility launchers

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

- setup: `SONICTRACE_V4_LARGER_CLAP_MUSIC_SETUP.cmd`
- benchmark: `SONICTRACE_V4_LARGER_CLAP_MUSIC_BENCHMARK.cmd`

### Candidate E — native LAION CLAP Music

- setup: `SONICTRACE_V4_NATIVE_LAION_MUSIC_SETUP.cmd`
- benchmark: `SONICTRACE_V4_NATIVE_LAION_MUSIC_BENCHMARK.cmd`

### Candidate F — M2D-CLAP 2025

- setup: `SONICTRACE_V4_M2D_CLAP_2025_SETUP.cmd`
- benchmark: `SONICTRACE_V4_M2D_CLAP_2025_BENCHMARK.cmd`

Candidate F is closed and receives no further tuning; these launchers remain only for reproducibility.

### Candidate G — MOSS-Music

- G0 zero-download preflight: `SONICTRACE_V4_MOSS_MUSIC_G_PREFLIGHT.cmd`
- G1 quantized proof: **not implemented yet; gated by G0**

## Decision gate

No challenger replaces V3 merely because one showcase track looks better.

A future V4 integration candidate should demonstrate simultaneously:

- THICK no longer collapsing into unrelated Dancehall/Eurodance output;
- Tachy Psychia landing inside its hard-hybrid Phonk/Trap/Glitch/Drill neighborhood;
- Stick to You remaining in a plausible Pop/Dancehall/Eurodance/Afropop neighborhood;
- Tình Bolero Cho Trân remaining Vietnamese/Bolero without TXT forcing;
- acceptable RTX 3060 runtime and VRAM;
- stable/reproducible deterministic inference;
- a production-compatible model/license boundary.

Until that gate is passed, **MuQ-MuLan remains the raw quality reference**, SonicTrace V3 remains intact, no catalogue embedding migration occurs, and STUDIO remains untouched.