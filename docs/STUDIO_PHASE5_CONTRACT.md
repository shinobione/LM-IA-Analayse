# SonicTrace — SHINOBIWAN Studio Phase 5 contract

## Endpoint

```text
POST /api/studio/analyze
```

Multipart fields:

```text
track_id       canonical lower-case kebab-case R2 manifest slug
source_version JSON object supplied by the protected Track Manager read
file           temporary canonical audio bytes
```

The coordinator validates identity/version context, saves the upload to a temporary file, runs the available layers, returns one `SonicTraceAnalysis` schema-v1 envelope and deletes the temporary file in `finally`.

## Partial layers

Mastering is required when FFmpeg is healthy. Neural, Song Anatomy and Demucs/fusion failures are returned as warnings so an available lower layer is not discarded. Browser DSP is calculated by Studio and attached to the review envelope.

## Returned contract

```text
schemaVersion
analysisId
trackId
sourceVersion
analyzedAt
engineVersion
dsp
mastering
neural
embedding (exactly 512D when present)
structure
semanticSummary
stemsSummary
provenance
warnings
privacy.audioStored = false
```

SonicTrace does not save this envelope to its local IndexedDB on behalf of Studio. Studio reviews it and the Track Manager Worker validates/persists it to canonical private R2 sidecars.

## Neural Accuracy V3.1 compatibility

Neural Accuracy V3.1 is deliberately **additive** to the existing schema-v1 envelope so Studio does not need a breaking migration.

Existing consumers may continue reading:

```text
neural.genres
neural.moods
neural.instruments
neural.traits
neural.embedding
```

V3 additionally exposes:

```text
neural.genre_analysis
semanticSummary.genreAnalysis
```

`neural.genre_analysis` contains the richer hierarchical genre result: primary style, broad families, regional candidates, confidence/UNKNOWN state, temporal consensus, per-segment evidence and the optional specialist ensemble evidence. `semanticSummary.genreAnalysis` mirrors that payload for consumers that primarily use the durable summary.

V3.1 may additionally expose the Discogs400 specialist under:

```text
neural.genre_analysis.experts.discogs400
neural.genre_analysis.experts.discogs400.embedding.dimension = 1280
neural.genre_analysis.ensemble
```

### Dual-embedding boundary

The two embeddings have different roles and **must not be silently substituted**:

- top-level `embedding` / `neural.embedding` remains the established **CLAP 512D** vector used by the current Catalog Intelligence and Studio schema-v1 compatibility path;
- the optional **Discogs-EffNet 1280D** music-first embedding stays nested inside `neural.genre_analysis.experts.discogs400.embedding`;
- a future Studio feature may explicitly consume the 1280D expert embedding, but doing so must be a deliberate versioned feature rather than changing the meaning or dimension of the existing top-level embedding field.

If the Discogs expert is unavailable, the V3.1 scan remains valid through CLAP and `genre_analysis.ensemble.status` can degrade to the CLAP-only path. The absence of the expert must not invalidate an otherwise successful Studio analysis.

The legacy 512D CLAP track embedding therefore remains unchanged for Catalog Intelligence compatibility. `schemaVersion` remains `1`.

**This contract preparation does not modify the Studio repository or Studio UI.** Studio can explicitly adopt the richer field later while older clients continue to operate against the compatibility fields.

## Identity

The standalone V2-E IndexedDB now distinguishes:

- canonical Studio context: `trackId` is reused as `id`;
- standalone analysis: `trackId: null`, `localOnly: true`, local storage key only.

A derived fingerprint remains useful for local duplicate hints but is never a competing canonical `trackId`.
