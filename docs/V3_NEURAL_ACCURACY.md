# SonicTrace Neural Accuracy V3

Status: **V3.2 CANDIDATE — SEMANTIC DIMENSIONS + STYLE-AWARE ARRANGEMENT**

## Why this exists

V2-B used a closed list of 24 genre labels and a softmax across that list. That design forced a winner even when the correct style was absent. A Vietnamese Bolero recording, for example, could only choose among unrelated candidates such as R&B, Soul or Pop.

V3 changes the classification architecture before any deeper Studio integration.

## V3-A — Hierarchical open-vocabulary taxonomy

`backend/app/neural_taxonomy.py` is the canonical CLAP candidate source.

The taxonomy distinguishes broad families, styles and regional vocabulary. In particular:

- `Vietnamese Bolero` is a first-class candidate;
- `Nhạc Vàng` and `Nhạc Trữ Tình` are explicit Vietnamese candidates;
- `Latin Bolero` remains a separate Latin style and is not treated as equivalent to Vietnamese Bolero;
- Hip-Hop, electronic, pop, R&B/Soul, reggae, Latin, rock, jazz, classical/screen and world families are materially expanded;
- moods and instrumentation vocabulary are expanded as well.

Each candidate can have multiple CLAP text prompts. Candidate scoring averages the strongest prompt matches instead of making classification depend on one exact wording.

## V3-B — Segment consensus

Representative 10-second segments are sampled across the track, but they are no longer averaged into one embedding before genre classification.

Each segment is classified separately. Track-level evidence then exposes:

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

V3.1 added the official Discogs-EffNet music-style model as an **optional, fail-safe ONNX expert**.

The expert:

- predicts 400 Discogs styles with multi-label sigmoid scores;
- produces a separate 1280D music-first embedding;
- uses the documented MusiCNN/EffNet input geometry: 16 kHz audio, 512-sample frames, 256-sample hop, 96 mel bands, 128-frame patches and 62-frame patch hop;
- downloads the official ONNX model + metadata on first use and caches them under the gitignored `backend/models/` directory;
- prefers ONNX Runtime CUDA and falls back to CPU;
- never becomes mandatory for a valid CLAP scan: model/dependency/download/inference failure leaves CLAP V3 active.

The Discogs specialist layer itself remains V3.1 in V3.2; V3.2 changes how the combined evidence is interpreted semantically and how it conditions arrangement reading.

## V3-E — Conservative ensemble

`backend/app/genre_ensemble.py` cross-checks CLAP with Discogs400 instead of blindly replacing one model with the other.

Important rules:

- direct style agreement can raise confidence;
- strong broad-family disagreement reduces confidence;
- a specialist override requires a strong **direct** mapped match and a clear ensemble margin;
- the Discogs expert cannot invent cultural/regional facts that do not exist in its taxonomy;
- specifically, `Latin---Bolero` may support a **bolero-like musical structure** for a CLAP `Vietnamese Bolero` result, but it can never rewrite that result to `Latin Bolero` by itself.

The compatibility `neural.genres` list remains available. The expert 1280D embedding stays nested inside the expert payload, while the canonical top-level Catalog embedding remains the established 512D CLAP vector.

## V3-F — Semantic dimensions (V3.2)

V3.2 fixes a second conceptual problem revealed by the real `Tinh Bolero Cho Trân` scan: unlike musical concepts should not compete for one first-place label.

The real scan produced strong evidence for all of the following at once:

- `Nhạc Vàng` — cultural/tradition context;
- `Vietnamese Pop Ballad` — song-form / stylistic-color evidence;
- `Vietnamese Bolero` — specific musical style;
- lower `Neo Soul` evidence — possible secondary resemblance/influence.

V3.2 therefore adds `backend/app/genre_dimensions.py` and an additive:

```text
neural.genre_analysis.dimensions
```

with separate dimensions:

```text
family
style.primary / style.alternatives
tradition.primary / tradition.alternatives
form.primary / form.alternatives
region
influences
unknown
```

For the real Vietnamese case, the intended interpretation is:

```text
Family      Vietnamese / Asian
Style       Vietnamese Bolero
Tradition   Nhạc Vàng
Form        Sentimental Ballad
Region      Vietnam
Influences  secondary evidence only
```

The original V3.1 ranking remains preserved as evidence. V3.2 does **not** rewrite model scores into fake probabilities and does not discard the fact that `Nhạc Vàng` may have the highest raw relevance.

When V3 confidence is `Unknown / hybrid`, the dimensions may still expose the closest style as **evidence-only**. That does not convert an uncertain scan into a confident classification.

## V3-G — Style-aware arrangement grammar (V3.2)

The second real-user issue was structural: after genre authority was fixed, a Vietnamese Bolero scan could still produce an implausible `Drop` because the old arrangement grammar used nearly the same section vocabulary for every style.

V3.2 adds `js/semantic-v32.js` and makes arrangement priors style-aware.

The semantic section vocabulary now includes `Interlude` as a first-class label alongside Intro, Verse, Pre-Chorus, Chorus, Bridge, Drop, Instrumental and Outro.

Grammar profiles include:

- `sentimental-song` — Vietnamese Bolero, Nhạc Vàng, Nhạc Trữ Tình, ballad, Fado, French chanson and related contexts;
- `electronic-drop` — electronic styles where Drop is structurally plausible;
- `hip-hop`;
- `rnb-song`;
- `pop-song`;
- `rock-song`;
- `general` fallback.

For `sentimental-song`, a Drop is strongly penalized. A low-vocal mid-song section with strong instrumental content is instead encouraged toward `Interlude`, `Bridge` or `Instrumental`. This is a **prior, not a hard ban**: exceptional audio evidence can still overcome it.

Electronic/drop-oriented music keeps a strong path toward Drop, and the regression suite explicitly checks that V3.2 does not solve Bolero by destroying valid EDM/Trap-style structure detection.

## Validation

V3.2 is protected by:

- existing FFmpeg regression tests;
- Studio contract tests;
- Neural V3 taxonomy tests;
- V3.1 ensemble tests for regional safety, expert agreement, family conflict and fail-safe fallback;
- V3.2 semantic-dimension tests;
- SHINOBIWAN benchmark tests that prefer `dimensions.style.primary` when present;
- a JS regression reproducing the real `Nhạc Vàng / Vietnamese Pop Ballad / Vietnamese Bolero / Neo Soul` evidence pattern;
- arrangement regressions asserting `Interlude > Drop` for the sentimental-song fixture while preserving materially stronger Drop evidence for an electronic fixture;
- Python/JavaScript syntax and existing Catalog guards;
- the real Discogs-EffNet ONNX smoke test that downloads the official model, builds 128×96 input patches, runs inference through ONNX Runtime and verifies 400 style outputs plus a 1280D embedding.

The CI smoke validates the real ONNX path on CPU. The actual RTX 3060 CUDA execution provider remains a real-machine acceptance check; if CUDA EP is unavailable, the expert falls back to CPU and CLAP remains available.

## Compatibility contract

The existing fields remain:

- `neural.genres`
- `neural.moods`
- `neural.instruments`
- `neural.traits`
- `neural.embedding` (512D)

V3 keeps:

- `neural.genre_analysis`
- `semanticSummary.genreAnalysis`

V3.2 adds only nested semantic dimensions under `neural.genre_analysis.dimensions`. The Studio-facing SonicTrace envelope remains schema version 1.

**No Studio repository or Studio UI is modified by V3.2.** Studio can adopt the richer dimensions later without breaking existing consumers.

## SHINOBIWAN benchmark

The acceptance gate is a reference set of known tracks with artist-confirmed expected family/style labels and regression scoring across engine versions.

Initial mandatory case:

- `Tinh Bolero Cho Trân` → primary musical style `Vietnamese Bolero`, family `Vietnamese / Asian`, not R&B/Soul as forced primary.

V3.2 explicitly allows the raw model/ensemble primary evidence to be `Nhạc Vàng` while the role-aware style dimension resolves to `Vietnamese Bolero`. This is intentional: the benchmark evaluates the musical-style dimension rather than pretending a tradition label and a specific style are the same kind of object.

Additional catalog references should be added only when the expected labels are artist-confirmed.
