# SonicTrace V4 Model Lab — Candidate E closeout

Date: 2026-08-18

Candidate: **Native LAION CLAP music checkpoint**

- package: `laion-clap 1.1.7`
- audio model: `HTSAT-base`
- fusion: disabled
- checkpoint: `music_audioset_epoch_15_esc_90.14.pt`
- checkpoint SHA-256: `fae3e9c087f2909c28a09dc31c8dfcdacbc42ba44c70e972b58c1bd1caf6dedd`
- audio: 48 kHz
- policy: five deterministic evenly-spaced exact 10-second clips; per-clip L2 normalization -> mean -> final L2 normalization
- inference: audio only; declared TXT/reference truth loaded only after all rankings
- GPU: NVIDIA GeForce RTX 3060 12 GB

## Real four-track result

### `stick-to-you.wav` — NEAR

- elapsed: 5.4 s
- peak GPU memory: 5492 MiB
- family #1: `Pop 0.4251`
- style Top-5: `Synth-Pop 0.4861`, `Afropop 0.4795`, `Dancehall Pop 0.4616`, `Eurodance 0.4572`, `V-Pop 0.4200`
- form #1: `Pop Ballad 0.4562`

Interpretation: the global Pop reading is correct and the intended Dancehall/Afropop/Eurodance neighborhood is visible, but the primary style remains too generic/misaligned for a clean PASS.

### `Tachy Psychia.wav` — FAIL

- elapsed: 0.4 s
- peak GPU memory: 5446 MiB
- family #1: `Pop 0.4752`
- style #1: `Eurodance 0.5087`
- hard-hybrid targets such as Drift Phonk / Cyber Trap / Glitch Hop / Electronic Drill do not reach Top-5
- form #1: `General Song Form 0.3968`

Interpretation: the native checkpoint still collapses a hard Phonk/Trap/Glitch hybrid toward Pop/Eurodance. This is a core quality failure, not a threshold issue.

### `THICK.wav` — FAIL

- elapsed: 0.4 s
- peak GPU memory: 5461 MiB
- family #1: `Pop 0.4110`
- style Top-5: `Eurodance 0.4648`, `Euro-House 0.4081`, `Cyber Trap 0.4003`, `Synth-Pop 0.3907`, `House 0.3539`
- form #1: `General Song Form 0.4268`

Interpretation: Candidate E sees `Cyber Trap` in the Top-3 and is materially more informative than the broken Hugging Face conversion, but Pop/Eurodance still dominates the final zero-shot reading. The canonical THICK failure is therefore not solved.

### `Tình Bolero Cho Trân.wav` — FAIL

- elapsed: 1.0 s
- peak GPU memory: 5488 MiB
- family #1: `Country / Acoustic 0.2753`; `Vietnamese / Asian` only #5 at `0.0994`
- style #1: `Contemporary R&B 0.3984`; `Vietnamese Bolero` #2 at `0.3495`
- tradition: `Nhạc Trữ Tình 0.3709` #1 and `Nhạc Vàng 0.3440` #2
- form: `Sentimental Ballad 0.3765` #1

Interpretation: tradition and form are excellent, and Vietnamese Bolero is close on style, but the main family/style decision is still wrong. This is not sufficient for product promotion.

## Decision

Candidate E is **rejected as the main SonicTrace V4 ear**.

It is not considered a broken benchmark: unlike Candidate D, cosine similarities are healthy and the four tracks receive meaningfully different rankings. The native LAION path therefore validates that the Hugging Face conversion was indeed a separate problem, but it also shows that the original native music checkpoint itself is still below the quality bar required by SonicTrace for this taxonomy and torture set.

No taxonomy prompt, threshold, expected benchmark value, rescue rule, V3 backend, catalogue or STUDIO change is made to improve Candidate E.

## Current raw-quality ranking

1. **MuQ-MuLan 700M** — 3/4 PASS; current quality reference; blocked from product promotion by CC-BY-NC-4.0 weights.
2. **CLaMP3 / MERT95M** — useful and musically informative, but too diffuse on THICK and Tachy.
3. **Native LAION CLAP Music (Candidate E)** — 0 PASS / 1 NEAR; fast once warm, but hard-hybrid and Bolero authority remain insufficient.
4. **Microsoft CLAP 2023 (Candidate C)** — 0/4 PASS; fast/light but recreates Dancehall-Pop failures.
5. **HF Larger CLAP Music (Candidate D)** — invalidated converted path; not comparable as clean model-quality evidence.

## Next-step policy

Stop testing additional LAION CLAP variants unless there is materially new training or architecture evidence. Do not return to per-track rescue rules.

The next challenger should be architecturally distinct and should preserve the same unchanged four-track, audio-only gate. M2D-CLAP 2025 is a plausible research candidate because it is a newer audio-language representation with official zero-shot support, but its repository points to a custom `LICENSE.pdf`; treat its product/commercial status as unresolved until that license is reviewed explicitly.
