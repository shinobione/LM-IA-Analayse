# SonicTrace Neural Accuracy V3

Status: **V3.1 implementation candidate**

## Why this exists

V2-B used a closed list of 24 genre labels and a softmax across that list. That design forced a winner even when the correct style was absent. A Vietnamese Bolero recording, for example, could only choose among unrelated candidates such as R&B, Soul or Pop.

V3 changes the classification architecture before any deeper Studio integration.

## V3-A — Hierarchical open-vocabulary taxonomy

`backend/app/neural_taxonomy.py` is the canonical CLAP taxonomy source.

The taxonomy now distinguishes broad families, styles and regional vocabulary. In particular:

- `Vietnamese Bolero` is a first-class style.
- `Nhạc Vàng` and `Nhạc Trữ Tình` are first-class Vietnamese candidates.
- `Latin Bolero` remains a separate Latin style and is not treated as equivalent to Vietnamese Bolero.
- Hip-Hop, electronic, pop, R&B/Soul, reggae, Latin, rock, jazz, classical/screen and world families are materially expanded.
- moods and instrumentation vocabulary are expanded as well.

Each style can have multiple CLAP text prompts. Candidate scoring averages the strongest prompt matches instead of making classification depend on one exact wording.

## V3-B — Segment consensus

Representative 10-second segments are still sampled across the track, but they are no longer averaged into one embedding before genre classification.

Each segment is classified separately. Track-level style and family evidence is then aggregated, exposing:

- per-segment winner and alternatives;
- style consensus;
- family consensus;
- winner margin;
- confidence level and reasons.

The 512D CLAP track embedding remains unchanged for Catalog Intelligence compatibility.

## V3-C — UNKNOWN / hybrid policy

Genre scores are no longer presented as closed-set softmax probabilities.

The CLAP V3 genre payload uses cosine relevance plus temporal consensus. If evidence is weak or unstable, `primary.label` becomes `Unknown / hybrid` while the closest candidate is still exposed.

This is intentional: an honest unknown is preferable to a confident wrong genre.

## V3-D — Discogs400 music-specialist expert

V3.1 adds the official Discogs-EffNet music-style model as an **optional, fail-safe ONNX expert**.

The expert:

- predicts 400 Discogs styles with multi-label sigmoid scores;
- produces a separate 1280D music-first embedding;
- uses the documented MusiCNN/EffNet input geometry: 16 kHz audio, 512-sample frames, 256-sample hop, 96 mel bands, 128-frame patches and 62-frame patch hop;
- downloads the official ONNX model + metadata from the Essentia model host on first use and caches them under the gitignored `backend/models/` directory;
- prefers ONNX Runtime CUDA and falls back to CPU;
- never becomes mandatory for a valid CLAP scan: model/dependency/download/inference failure leaves CLAP V3 active.

`onnxruntime-gpu` is constrained below 1.27 because the SonicTrace neural runtime is CUDA 12.8, while current ORT 1.27+ PyPI GPU packages default to CUDA 13.

## V3-E — Conservative ensemble

`backend/app/genre_ensemble.py` cross-checks CLAP with Discogs400 instead of blindly replacing one model with the other.

Important rules:

- direct style agreement can raise confidence;
- strong broad-family disagreement reduces confidence;
- a specialist override requires a strong **direct** mapped match and a clear ensemble margin;
- the Discogs expert cannot invent cultural/regional facts that do not exist in its taxonomy;
- specifically, `Latin---Bolero` may support a **bolero-like musical structure** for a CLAP `Vietnamese Bolero` result, but it can never rewrite that result to `Latin Bolero` by itself.

The compatibility `neural.genres` list is re-ranked by ensemble evidence only when Discogs is ready. Otherwise it remains the CLAP V3 list.

The richer result remains under:

- `neural.genre_analysis.primary`
- `neural.genre_analysis.experts`
- `neural.genre_analysis.ensemble`

The expert 1280D embedding remains nested inside the expert payload. The canonical top-level Catalog embedding remains the established 512D CLAP vector.

## Compatibility contract

The existing fields remain:

- `neural.genres`
- `neural.moods`
- `neural.instruments`
- `neural.traits`
- `neural.embedding` (512D)

V3 adds:

- `neural.genre_analysis`

The Studio-facing SonicTrace envelope remains schema version 1. `semanticSummary.genreAnalysis` is additive and mirrors the V3 payload.

**No Studio repository or Studio UI is modified by this phase.** Studio can adopt the richer field later without breaking existing consumers.

## SHINOBIWAN benchmark

The acceptance gate is a reference set of known tracks with artist-confirmed expected family/style labels and regression scoring across engine versions.

Initial mandatory case:

- `Tinh Bolero Cho Trân` → Vietnamese Bolero / Vietnamese-Asian family, not R&B/Soul as forced primary.

The ensemble regression tests additionally assert that Discogs `Latin---Bolero` evidence cannot rewrite an artist-confirmed Vietnamese Bolero result into a Latin regional label.

Additional catalog references should be added only when the expected labels are artist-confirmed.
