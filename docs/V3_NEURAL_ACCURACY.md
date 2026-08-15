# SonicTrace Neural Accuracy V3

Status: **foundation candidate**

## Why this exists

V2-B used a closed list of 24 genre labels and a softmax across that list. That design forced a winner even when the correct style was absent. A Vietnamese Bolero recording, for example, could only choose among unrelated candidates such as R&B, Soul or Pop.

V3 changes the classification architecture before any deeper Studio integration.

## V3-A — Hierarchical open-vocabulary taxonomy

`backend/app/neural_taxonomy.py` is the canonical taxonomy source.

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

Genre scores are no longer presented as softmax probabilities.

The V3 genre payload uses CLAP cosine relevance plus temporal consensus. If evidence is weak or unstable, `primary.label` becomes `Unknown / hybrid` while the closest candidate is still exposed.

This is intentional: an honest unknown is preferable to a confident wrong genre.

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

## Music-specialist expert model — next layer

The preferred specialist complement remains Discogs400 / Discogs-EffNet because the official model predicts 400 Discogs styles and exposes a 1280D music embedding.

Native Essentia Python bindings are not currently a good fit for the Windows SonicTrace runtime. The expert layer should therefore be integrated through a Windows-safe ONNX preprocessing/inference path or a separate worker, without making the current CLAP runtime fragile.

The V3 output contract is intentionally shaped so a future `genre_experts` section can be fused without replacing `genre_analysis`.

## SHINOBIWAN benchmark

The next acceptance gate is not visual polish. It is a reference set of known tracks with declared expected family/style labels and regression scoring across engine versions.

Initial mandatory case:

- `Tinh Bolero Cho Trân` → Vietnamese Bolero / Vietnamese-Asian family, not R&B/Soul as forced primary.

Additional catalog references should be added only when the expected labels are artist-confirmed.
