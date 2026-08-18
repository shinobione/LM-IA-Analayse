# SonicTrace V4 Model Lab — Candidate C benchmark closeout (2026-08-18)

Status: **Model Lab evidence only**. This record does not promote any challenger into SonicTrace V3 and does not touch SHINOBIWAN STUDIO.

## Benchmark contract

Candidate C was evaluated on the same four-track torture set and unchanged Model Lab taxonomy axes (`family`, `style`, `tradition`, `form`).

Inference remained **audio only**:

`declared_metadata_used_for_inference = false`

Captured runtime:

- model: `microsoft/msclap / CLAP_weights_2023.pth`
- official code commit: `e8a6467b87cd85716e20c6a008126150d9740be0`
- checkpoint SHA-256: `2cef4016d47d00eb28d153d522f397222057f95000e9bad6b9583c631284a1e6`
- code license: MIT
- checkpoint license: MS-PL
- embedding dimension: 1024
- 44.1 kHz audio
- five deterministic evenly-spaced exact 7-second clips per track
- normalized clip embeddings, mean pooling, final renormalization
- RTX 3060 12 GB

## Candidate C — Microsoft CLAP 2023

### Stick to You — FAIL

- family: `R&B / Soul / Funk 0.4118`, `Hip-Hop / Rap 0.3891`, `Pop 0.3842`
- style: `Dancehall Pop 0.4958` (#1), `Afropop 0.4235`, `V-Pop 0.4185`, `Contemporary R&B 0.4121`, `Synth-Pop 0.4084`
- tradition: `Nhạc Trữ Tình 0.3368` (#1)
- form: `Pop Ballad 0.4552` (#1)
- elapsed: `3.6s` first measured track after model/taxonomy initialization
- peak VRAM: `2935 MiB`

The style axis is good, but the family axis misses `Pop` and the tradition axis shows an implausible Vietnamese bias. Candidate C therefore does not clear the unchanged benchmark.

### Tachy Psychia — FAIL

- family: `Electronic / EDM 0.5116`, `Hip-Hop / Rap 0.4895`
- style: `Dancehall Pop 0.5638` (#1), `Synth-Pop 0.5335`, `Grime 0.5327`, `V-Pop 0.5188`, `Drift Phonk 0.5161`
- form: `Electronic Hybrid 0.5852` (#1), `Pop Ballad 0.5412`, `Rap Song 0.4929`
- elapsed: `0.4s`
- peak VRAM: `2937 MiB`

Although `Drift Phonk` enters the Top-5 and the family/form axes are plausible, the primary style collapses to `Dancehall Pop`. This recreates the class of upstream failure that motivated V4 Model Lab.

### THICK — FAIL

- family: `Electronic / EDM 0.4718`, `Hip-Hop / Rap 0.4559`
- style: `Dancehall Pop 0.5159` (#1), `Synth-Pop 0.4916`, `Grime 0.4702`, `Drift Phonk 0.4627`, `Drum and Bass 0.4403`
- form: `Electronic Hybrid 0.4833` (#1), `Pop Ballad 0.4429`, `Rap Song 0.4200`
- elapsed: `0.5s`
- peak VRAM: `2937 MiB`

This is a decisive quality failure: the canonical `THICK -> Dancehall Pop` collapse returns as the raw #1 style, despite credible hard-hybrid alternatives being present lower in the ranking.

### Tình Bolero Cho Trân — FAIL (family only)

- family: `Pop 0.3872`, `Country / Acoustic 0.3801`, `R&B / Soul / Funk 0.3799`, `Vietnamese / Asian 0.2536`
- style: `Vietnamese Bolero 0.4491` (#1)
- tradition: `Nhạc Trữ Tình 0.4741` (#1), `Nhạc Vàng 0.4029`
- form: `Sentimental Ballad 0.4746` (#1)
- elapsed: `0.5s`
- peak VRAM: `2937 MiB`

As with MuQ and CLaMP3, the specialized axes recognize the Bolero well. The raw family axis remains wrong, so the benchmark stays FAIL.

## Decision

**Microsoft CLAP 2023 is rejected as the main V4 quality candidate.**

It does offer excellent operational characteristics on the RTX 3060:

- warmed inference around `0.4–0.5s` per track in the captured run;
- peak VRAM around `2.94 GiB`;
- 1024D embeddings;
- a materially more product-compatible license boundary than MuQ-MuLan's non-commercial weights, subject to MS-PL compliance and legal review.

But those advantages do not compensate for the musical regressions:

1. `Tachy Psychia -> Dancehall Pop #1`;
2. `THICK -> Dancehall Pop #1`;
3. strong Vietnamese-tradition leakage on unrelated tracks;
4. `Stick to You` misses the expected Pop family despite a correct style #1.

The exact four-track score is therefore **0/4 PASS** under the unchanged benchmark.

## Current ranking

1. **MuQ-MuLan 700M** — strongest raw musical understanding measured so far; 3/4 PASS, Bolero family-only FAIL; blocked from product promotion by CC-BY-NC-4.0 weights.
2. **CLaMP3 / MERT95M** — useful reference, but too diffuse on THICK/Tachy and much slower in the captured run.
3. **Microsoft CLAP 2023** — fastest/lightest challenger, but quality is not sufficient and the canonical Dancehall-Pop collapse returns.

## Next gate

Do not tune Microsoft CLAP prompts or benchmark thresholds to rescue this result.

The next challenger should remain:

- audio-only;
- isolated from V3/STUDIO;
- evaluated with the same taxonomy and four tracks;
- production-eligible or at least materially closer to a commercial product gate than MuQ-MuLan.

MuQ-MuLan remains the quality reference to beat.
