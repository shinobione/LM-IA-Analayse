# SonicTrace V4 Model Lab — real benchmark verdict (2026-08-17)

Status: **Model Lab evidence only**. This decision record does not promote a challenger into SonicTrace V3 and does not touch SHINOBIWAN STUDIO.

## Benchmark contract

All results below come from the same four-track torture set and the same Model Lab taxonomy axes (`family`, `style`, `tradition`, `form`).

Inference remains **audio only**. Artist TXT metadata is evaluation-only and was not used to choose, reorder, or rescue inference results:

`declared_metadata_used_for_inference = false`

MuQ-MuLan policy used for the real run:

- model: `OpenMuQ/MuQ-MuLan-large`
- fp32
- 24 kHz audio
- five deterministic evenly-spaced 10-second clips per track
- normalized clip embeddings, mean pooling, final renormalization
- RTX 3060 12 GB

## Candidate A — CLaMP3 / MERT95M

Previously observed real behavior on the same torture set:

- **Stick to You:** good / PASS neighborhood (`Pop`, `Dancehall Pop`, `Euro-House`, `Eurodance`).
- **Tachy Psychia:** FAIL; still too diffuse, with `Drum and Bass`, `Eurodance`, `Electronic Drill`, `Euro-House` competing closely.
- **THICK:** FAIL; no longer collapses to Dancehall Pop, but remains too generic / Euro-House-Eurodance biased.
- **Tình Bolero Cho Trân:** automatic family FAIL, while `Vietnamese Bolero`, `Nhạc Trữ Tình` and `Sentimental Ballad` are all musically strong.
- observed peak VRAM: about 4.1 GiB.
- warmed per-track runtime: about 26–33 seconds in the captured four-track run.

Conclusion: useful and substantially different from V3, but not strong enough on THICK + Tachy to become the main V4 ear.

## Candidate B — MuQ-MuLan 700M

### Stick to You — PASS

- family: `Pop 0.4849`
- style: `Dancehall Pop 0.5043`, `Contemporary R&B 0.5037`, `V-Pop 0.4508`, `Afropop 0.4478`, `Synth-Pop 0.4071`
- form: `Pop Ballad 0.5184`
- elapsed: `24.6s`
- peak VRAM: `5078 MiB`

This preserves the intended Pop / Dancehall / Afro-pop neighborhood without TXT forcing.

### Tachy Psychia — PASS

- family: `Hip-Hop / Rap 0.3277`
- style: `Drift Phonk 0.4144`, `Dubstep 0.3867`, `Synth-Pop 0.2442`, `Alternative Hip-Hop 0.2394`, `Contemporary R&B 0.2315`
- form: `Electronic Hybrid 0.5184`, `Rap Song 0.4774`
- elapsed: `0.6s`
- peak VRAM: `5077 MiB`

This is the first challenger result that places Tachy directly in a credible hard-hybrid neighborhood instead of leading with Eurodance/Euro-House.

### THICK — PASS

- family: `Hip-Hop / Rap 0.3755`
- style: `Drift Phonk 0.3590`, `Dubstep 0.3139`, `Synth-Pop 0.2757`, `Alternative Hip-Hop 0.2735`, `Eurodance 0.2729`
- form: `Electronic Hybrid 0.5127`, `Rap Song 0.4849`
- elapsed: `0.6s`
- peak VRAM: `5075 MiB`

The canonical V3 failure (`Dancehall Pop` as the main understanding) is gone in the raw challenger output. THICK now lands in a much more credible Hip-Hop / hard-electronic neighborhood.

### Tình Bolero Cho Trân — FAIL (family only)

- family: `Pop 0.3261`, `R&B / Soul / Funk 0.2172`, `Vietnamese / Asian 0.2164`, `Country / Acoustic 0.1607`
- style: `Vietnamese Bolero 0.4639` (#1)
- tradition: `Nhạc Trữ Tình 0.4042` (#1), `Vietnamese Traditional 0.3279`, `Nhạc Vàng 0.2144`
- form: `Sentimental Ballad 0.4862` (#1)
- elapsed: `1.3s`
- peak VRAM: `5068 MiB`

The FAIL remains valid because the raw `family` axis does not rank `Vietnamese / Asian` first. We do **not** weaken the benchmark to turn this into a synthetic 4/4 PASS.

At the same time, three independent semantic axes are exceptionally coherent: style, tradition and form all identify the intended musical/cultural neighborhood without TXT inference.

## Decision

**MuQ-MuLan is the strongest raw neural challenger measured so far in SonicTrace V4 Model Lab.**

It beats CLaMP3 decisively on the two difficult hard-hybrid tracks while preserving Stick to You and retaining excellent Bolero style/tradition/form recognition.

This is **not** a production promotion.

Current blockers:

1. **Bolero family axis is still wrong in raw zero-shot output.** The benchmark stays FAIL.
2. **MuQ-MuLan weights are currently treated by this project as non-commercial / lab-only.** Do not wire this checkpoint into SonicTrace product runtime or STUDIO.
3. A 700M fp32 model uses roughly 5.1 GiB peak VRAM in this captured run, acceptable on the RTX 3060 but heavier than CLaMP3.

## Architectural implication

The result supports the original V4 hypothesis: replacing the upstream musical representation produces a much larger gain than adding more V3 rescue rules.

A future V4 architecture may therefore separate responsibilities rather than ask one label list to do everything:

- DSP remains factual (`tempo`, `key`, loudness, mastering measurements).
- a music-specialized V4 ear provides style / mood / instrumentation / semantic embeddings.
- Discogs-EffNet remains an optional expert / second opinion, not a growing rescue-rule engine.
- family can eventually be resolved through a model-agnostic semantic ontology using consistent evidence from child axes, but **no Bolero-specific rescue is introduced by this benchmark closeout**.
- V2-E catalogue embeddings are not migrated during Model Lab benchmarking.

## Next gate

Do **not** tune MuQ prompts or benchmark thresholds to manufacture a fourth PASS.

The next Model Lab action should be to identify and benchmark a **production-eligible / commercially usable challenger or architecture** against the exact same four tracks and taxonomy, using MuQ-MuLan as the current quality reference.

Until that gate is passed:

- SonicTrace V3 stays intact;
- CLaMP3 stays intact;
- MuQ-MuLan stays isolated in Model Lab;
- STUDIO stays untouched.
