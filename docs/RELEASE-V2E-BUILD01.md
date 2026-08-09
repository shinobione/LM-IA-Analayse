# SonicTrace V2-E · BUILD 01

## Purpose

The SonicTrace public UI previously exposed its product name and analysis-layer labels but no visible release/build identity in the main header. This made production screenshots and user reports ambiguous.

`V2-E · BUILD 01` is the first explicit visible SonicTrace UI release marker.

## UI contract

- `SonicTrace Audio Intelligence` remains the product name.
- The existing subtitle remains `Analyse musicale locale • GPU • structure • paroles`.
- A compact `V2-E · BUILD 01` pill is inserted directly in the brand block beneath the subtitle.
- The marker is idempotent under the existing readability MutationObserver and carries an accessible label/title.
- `document.documentElement.dataset.sonictraceRelease` is set to `v2-e-build-01` for smoke/debug inspection.

## Scope

This release changes only public frontend identity/traceability. It does not modify the DSP engine, neural analysis, catalog memory, Studio coordinator contract, local CUDA runtime, audio retention policy or persistence model.

Safety ref: `safety/pre-sonictrace-build01-release-label-20260809-2128`.
