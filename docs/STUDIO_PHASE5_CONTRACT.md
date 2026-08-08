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

## Identity

The standalone V2-E IndexedDB now distinguishes:

- canonical Studio context: `trackId` is reused as `id`;
- standalone analysis: `trackId: null`, `localOnly: true`, local storage key only.

A derived fingerprint remains useful for local duplicate hints but is never a competing canonical `trackId`.
