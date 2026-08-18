# SonicTrace V4 Model Lab — Candidate F closeout

Date: 2026-08-18

Candidate: **M2D-CLAP 2025**

Upstream:

- repository: `nttcslab/m2d`
- pinned source commit: `3d0c4de9447c404a8d3f9f37e04f53bc902e09b3`
- release: `v0.5.0`
- model: `m2d_clap_vit_base-80x1001p16x16p16kpBpTI-2025`
- checkpoint: `checkpoint-30.pth`
- checkpoint SHA-256: `238521603c04862ab151cdd80980b591cb36ebe844d43203992fac9ef085c8a1`
- license status: custom upstream `LICENSE.pdf`; **LAB ONLY / unresolved for product use**

## Protocol

The real RTX 3060 run used the same unchanged SonicTrace V4 torture set and taxonomy as the previous challengers:

- five deterministic evenly-spaced exact 10-second clips per track;
- 16 kHz audio;
- normalized clip embeddings, mean pooling, final normalization;
- official M2D-CLAP audio/text embedding path;
- benchmark/reference metadata loaded only after inference;
- `declared_metadata_used_for_inference = false`.

No taxonomy, prompt, threshold or rescue-rule tuning was performed for Candidate F.

## Real four-track result

### Stick to You — NEAR

- family: `Pop` #1 (`0.3680`)
- style: `V-Pop` #1 (`0.3610`)
- useful intended neighborhood still appears: `Afropop` #2 (`0.3595`), `Dancehall Pop` #4 (`0.3308`)
- Vietnamese-tradition leakage remains visible (`Nhạc Trữ Tình`, `Nhạc Vàng`)

Conclusion: partially coherent but not clean enough to pass.

### Tachy Psychia — FAIL

- family: `Pop` #1 (`0.3420`), `Hip-Hop / Rap` #2 (`0.3126`)
- style: `V-Pop` #1 (`0.3355`), `Eurodance` #2 (`0.3193`), `Drill` #3 (`0.3181`)
- expected Phonk/Trap/Glitch hard-hybrid identity is not recovered in the Top-5

Conclusion: fails the central V4 quality gate.

### THICK — FAIL

- family: `Pop` #1 (`0.3317`), `Hip-Hop / Rap` #3 (`0.3007`)
- style: `V-Pop` #1 (`0.3274`), `Drill` #2 (`0.3268`), `Eurodance` #3 (`0.3203`)
- hard-hybrid cues are present but do not control the interpretation

Conclusion: fails the canonical anti-collapse requirement.

### Tình Bolero Cho Trân — FAIL

- family: `Country / Acoustic` #1 (`0.3345`), `Vietnamese / Asian` #2 (`0.2969`)
- style: `Soul` #1 (`0.3271`), `Country` #2 (`0.3266`), `Vietnamese Bolero` #3 (`0.3135`)
- tradition is strong: `Nhạc Trữ Tình` #1 (`0.3380`), `Nhạc Vàng` #2 (`0.2950`)
- form is strong: `Sentimental Ballad` #1 (`0.3345`)

Conclusion: detects important cultural/form evidence but still misidentifies the main family/style.

## Operational performance

- first track: ~21.6 s including warm-up
- warmed tracks: ~0.3 s each
- peak GPU memory: ~3.4 GiB

Candidate F is operationally excellent on the RTX 3060, but fast incorrect classification does not satisfy the SonicTrace V4 quality gate.

## Final decision

**REJECTED FOR QUALITY.**

Real score: **0 PASS / 1 NEAR / 3 FAIL**.

M2D-CLAP 2025 does not approach the current MuQ-MuLan quality reference on the same unchanged four-track benchmark. In particular it does not recover the required hard-hybrid identity of both `THICK` and `Tachy Psychia` while preserving clean interpretation of `Stick to You` and `Tình Bolero Cho Trân`.

Candidate F remains reproducible in the Model Lab but receives no prompt/threshold tuning and is not promoted into SonicTrace V3, Catalogue or SHINOBIWAN STUDIO.

## Current V4 reference

MuQ-MuLan remains the raw quality reference:

- Stick to You: PASS
- Tachy Psychia: PASS (`Hip-Hop / Rap`, `Drift Phonk` #1)
- THICK: PASS (`Hip-Hop / Rap`, `Drift Phonk` #1)
- Tình Bolero Cho Trân: FAIL on family only, while style/tradition/form are coherent

The next useful question is no longer whether another generic CLAP-like model can be tuned to the torture set. Any further challenger must be materially different and must have a credible path to production licensing and RTX 3060 operation.