# SonicTrace V2-E · BUILD 07 — Mastering recovery hardening

Date: 2026-08-12

Status: **CANDIDATE — CI required, real-user SINGULARITY smoke required after local UPDATE & START**.

## Why

A fresh Studio scan of `SINGULARITY .:. OBLITERANT` produced a current SonicTrace profile with Neural, finite 512D embedding and structure, but the saved profile remained `PARTIAL` because the mastering layer was unavailable. Studio therefore truthfully displayed missing mastering, LUFS `—` and True Peak `—`.

Build 06 already prevented a mastering failure from discarding later Deep Audio layers. Build 07 now hardens the mastering measurement itself so a transient failure in one FFmpeg measurement path does not immediately force a partial profile when another deterministic FFmpeg measurement path can recover the same class of information.

## Changes

### Loudness / LUFS / True Peak

Primary path remains FFmpeg `loudnorm`.

If `loudnorm`:

- times out;
- cannot execute; or
- returns no usable JSON measurement block;

SonicTrace now still attempts the existing EBU R128 fallback before declaring loudness unavailable.

Recovered values keep provenance:

`measured-ebur128-fallback`

No Browser DSP value is promoted to server mastering truth.

### Mean / max level

Primary path remains FFmpeg `volumedetect`.

If `volumedetect`:

- times out;
- cannot execute; or
- returns no usable measurement;

SonicTrace now attempts a second deterministic FFmpeg pass using `astats` and parses the final overall RMS / Peak level values.

Recovered values keep provenance:

`measured-astats-fallback`

### Diagnostics

Fallback results retain `fallback_reason`, preserving why the primary measurement degraded while still reporting the recovered measured result truthfully.

Only when both the primary and fallback paths fail does the corresponding mastering sub-layer remain `unavailable` and generate the durable partial-profile warning.

## Version identity

- SonicTrace UI: **V2-E · BUILD 07**
- Deep Audio engine default: **2.0.2-alpha**
- API schema: **2.2 unchanged**
- Studio analysis contract schema: **1 unchanged**

## Safety boundaries

Build 07 does not:

- change Neural / CLAP inference;
- change 512D embedding semantics;
- change Song Anatomy or Demucs fusion;
- change Track Manager or R2 persistence;
- retain source audio;
- use Browser DSP to fabricate LUFS/True Peak;
- mutate catalog/Album state;
- change Studio Focus runtime;
- start Phase 7-C.

## Regression coverage

`backend/tests/test_ffmpeg_analysis.py` now protects:

- resilient loudnorm JSON parsing;
- EBU R128 parsing;
- astats level parsing;
- loudnorm timeout → EBU R128 recovery;
- volumedetect timeout → astats recovery;
- explicit unavailable contract shape.

The existing Studio contract regression continues to ensure that a genuinely unavailable mastering layer never drops Neural, 512D embedding or structure.

## Real-user acceptance gate

After merge, run `SONICTRACE_UPDATE_AND_START.cmd`, then re-scan `SINGULARITY .:. OBLITERANT` from Studio.

Expected success state:

```text
Profile      FULL
Audio match  Current
Embedding    512D
LUFS         numeric
True Peak    numeric
```

If the profile remains PARTIAL, preserve the exact warning and provenance: Build 07 must not hide a genuinely unrecoverable FFmpeg failure.