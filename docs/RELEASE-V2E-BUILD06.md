# SonicTrace V2-E · BUILD 06 — C3 Deep Audio resilience

Date: 2026-08-11

## Scope

Build 06 opens PHASE UX / C3 and fixes the Deep Audio failure boundary exposed by real-user Studio scans.

The observed production-development failure was:

`FFmpeg loudnorm did not return a measurement block.`

Before Build 06, that single V2-A mastering exception aborted `POST /api/studio/analyze` before Neural, the 512D embedding, Song Anatomy and optional stem fusion could run. Studio then fell back to Browser DSP and incorrectly described the whole Deep Audio coordinator as offline.

## Backend behavior

`backend/app/ffmpeg_analysis.py` now:

- explicitly maps the first audio stream for mastering measurements;
- parses the loudnorm JSON object without depending on FFmpeg whitespace or key order;
- falls back to a real FFmpeg `ebur128=peak=true` measurement when loudnorm JSON is unavailable;
- returns an explicit `provenance: unavailable` measurement object with diagnostics if neither measurement can be recovered;
- applies the same non-fatal rule to `volumedetect`.

A missing mastering measurement therefore no longer raises an exception that kills later Deep Audio layers.

The Studio schema remains `schemaVersion: 1`. No new R2 analysis path or second source of truth is introduced.

## Partial-layer contract

`build_analysis_envelope()` preserves available deep layers and adds durable warnings when a mastering sub-layer reports `provenance: unavailable`.

Expected result for a loudnorm-only problem after Build 06:

- Browser DSP: available when browser decoding succeeds;
- mastering loudness: measured through loudnorm, measured through ebur128 fallback, or explicitly unavailable;
- Neural: still attempted;
- embedding 512D: still retained when Neural succeeds;
- Song Anatomy / structure: still attempted;
- stems/fusion: still attempted when routing/runtime permits;
- warning: explains exactly which layer degraded.

## Version identity

- SonicTrace visible release: `V2-E · BUILD 06`
- default Deep Audio engine version: `2.0.1-alpha`
- Studio contract schema: unchanged at `1`
- API schema: unchanged at `2.2`

## Safety

Build 06 does not:

- write canonical catalog data;
- migrate R2;
- change Track Manager writes;
- change audio retention (temporary processing only);
- change CLAP/K-means/catalog-family algorithms;
- begin Phase 7.

C3 real-user validation still requires the local coordinator to be updated/restarted and a canonical Studio scan to be run against an audio file that previously triggered the loudnorm failure.
