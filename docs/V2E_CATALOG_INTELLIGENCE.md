# SonicTrace V2-E — Catalog Intelligence

V2-E turns completed SonicTrace analyses into a local catalog. Audio files remain disposable: WAV/MP3 bytes are never persisted by this layer.

## V2-E.1 — Catalog Memory

Storage: browser IndexedDB (`sonictrace-catalog`).

A saved track contains only structured analysis data:

- compact browser DSP (BPM, key, dynamics, stereo, spectral descriptors, DNA)
- backend mastering measurements
- Neural genres, moods, instruments and traits
- CLAP embedding (model, dimension, vector)
- compact V2-C×V2-D fusion structure, hooks, climax and stem activity
- semantic summary
- declared TXT metadata (`TITLE`, `YEAR`, `BPM`, `GENRE`, `MOOD`, `THEMES`, `ERA`, `ENERGY`, `LANGUAGE`, `STYLE_PROMPT`, etc.)
- artistic concordance between declared intent and detected properties
- compute/provenance metadata

The current analysis responses are captured non-destructively with `response.clone()` and local DSP is captured by wrapping the existing analyzer prototype. Existing analysis code remains the source of truth.

A deterministic fingerprint deduplicates repeated saves of the same analyzed track. Catalog JSON export/import is provided for backup and transfer.

## V2-E.2 — Similarity Engine

The human-facing similarity score combines available evidence and re-normalizes when a component is missing:

- CLAP embedding: 62%
- Neural traits: 12%
- genre/mood overlap: 8%
- BPM compatibility: 7%
- key compatibility: 4%
- structure: 5%
- mastering: 2%

The UI explains the main reasons (shared mood/genre, energy, vocal presence, atmosphere, tempo, tonal compatibility, structure, mastering) instead of exposing raw cosine values alone.

## V2-E.3 — Catalog Map

The catalog page adds dedicated `Analyse / Catalogue` navigation without adding another analysis button.

The map uses a deterministic PCA-like 2D projection of CLAP embeddings, then lightweight k-means grouping. It identifies:

- natural sound families
- pairs at or above 92% similarity as potentially redundant
- low-neighborhood outliers
- bridge tracks with strong neighbors across clusters

Selecting a track highlights and explains its nearest neighbors.

## V2-E.4 — Project / Album Intelligence

Users can select catalog tracks and request a project analysis. SonicTrace computes:

- average pairwise sonic coherence
- selection outliers
- a bridge candidate
- a proposed sequencing order

Sequencing uses similarity, energy arc, BPM compatibility, key compatibility, structure and vocal/atmospheric traits. Each position receives a human role such as Opening, Rise, First peak, Breather, Relaunch, Final peak or Closing.

Projects can be saved to the same local IndexedDB without storing audio.

## Privacy boundary

V2-E does **not** store source audio. Existing backend upload privacy still applies to the analysis runtime; V2-E only persists the structured outputs returned after analysis.
