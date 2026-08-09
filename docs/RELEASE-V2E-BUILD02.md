# SonicTrace V2-E · BUILD 02

Status: frontend UI release candidate / real-user smoke pending.

Safety ref: `safety/pre-build02-action-layout-20260809-2238`

## Scope

Build 02 reorganizes the primary SonicTrace analysis workflow without changing any analysis engine contract.

The main drop-zone workflow is now ordered as:

1. selected audio/file context;
2. **Audio** input action and **Paroles / contexte** input side-by-side on desktop;
3. **Analyse express** and **Analyse complète** as equal primary choices;
4. layer status strip;
5. one consolidated **Outils avancés** disclosure for individual expert layers.

On narrow screens the input row and analysis actions stack to one column.

## Implementation rules

- Existing `#choose-audio-btn` is moved into the new audio slot; it is not cloned or replaced.
- Existing `#semantic-lyrics-wrap` is moved into the Lyrics/context slot; its input/clear behavior is unchanged.
- Existing low-level analysis buttons remain the advanced-tool implementation.
- Unified quick/full buttons keep their existing orchestration logic and handlers.
- The readability layer yields toolbox ownership to `#unified-analysis-shell` so two competing advanced-tool containers cannot appear.
- Loader query versions advance for unified/readability assets so GitHub Pages clients do not keep Build 01 UI files.

## Release identity

Visible release marker:

`V2-E · BUILD 02`

DOM release identity:

`data-sonictrace-release="v2-e-build-02"`

## Frozen engine boundary

Build 02 changes no:

- FastAPI endpoint;
- FFmpeg/loudnorm logic;
- Browser DSP algorithm;
- Neural inference;
- CUDA/GPU routing;
- Demucs/stems;
- embeddings;
- Song Anatomy;
- Catalog Intelligence data;
- Studio analysis contract;
- R2/Track Manager integration;
- production audio retention policy.

The known Studio `PARTIAL` / FFmpeg loudnorm measurement-block problem remains deliberately deferred to C3 and is not hidden or treated by this UI release.

## Validation

`scripts/test-release-label.mjs` guards both the Build 02 visible release identity and the workflow DOM/CSS contract, including cache-busted loader assets and unified advanced-tool ownership.
