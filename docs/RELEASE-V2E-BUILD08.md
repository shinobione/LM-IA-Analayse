# SonicTrace V2-E · BUILD 08 — Runtime freshness + deterministic FFmpeg capture

Date: 2026-08-12

Status: **CANDIDATE — CI required, real-user SINGULARITY smoke required after local UPDATE & START**.

## Why

Build 07 correctly added deterministic FFmpeg fallbacks, but the real-user rescan of `SINGULARITY .:. OBLITERANT` still returned `PARTIAL` with:

- loudnorm exit `0` but no parsed JSON measurement;
- EBU R128 fallback with no parsed summary;
- volumedetect exit `0` but no parsed levels;
- astats fallback with no parsed levels.

The same screenshot also exposed an engine identity mismatch: the returned profile still displayed `2.0.1-alpha` while Build 07 source default was `2.0.2-alpha`.

Build 08 hardens both seams instead of hiding the partial state.

## Runtime freshness

`SONICTRACE_UPDATE_AND_START.cmd` now performs a managed stop after pulling the new code and before starting SonicTrace again. This prevents a schema-compatible API process from surviving an update merely because API schema `2.2` is unchanged.

`SONICTRACE_START.cmd` pins the expected runtime identity:

`LMN_VERSION=2.0.3-alpha`

This prevents a stale machine-level environment value from masking the deployed engine identity.

## FFmpeg measurement capture

All mastering measurement commands now:

- force `-loglevel info` explicitly;
- disable ANSI color through `AV_LOG_FORCE_NOCOLOR=1`;
- decode subprocess output as UTF-8 with replacement for undecodable bytes;
- parse the combined stdout + stderr stream;
- preserve Build 07 loudnorm → EBU R128 and volumedetect → astats fallbacks.

No Browser DSP value is promoted to LUFS / True Peak authority.

## Versions

- SonicTrace UI: **V2-E · BUILD 08**
- Deep Audio engine: **2.0.3-alpha**
- API schema: **2.2 unchanged**
- Studio analysis contract schema: **1 unchanged**

## Safety

Build 08 does not change:

- Track Manager or R2 authority;
- Neural / CLAP inference;
- 512D embedding semantics;
- Song Anatomy / Demucs behavior;
- source-audio retention policy;
- Album/catalog mutation behavior;
- Studio Focus runtime;
- Phase 7-C.

Rollback checkpoint:

`safety/pre-build08-runtime-ffmpeg-capture-20260812`

## Real-user acceptance gate

After merge:

1. run `SONICTRACE_UPDATE_AND_START.cmd`;
2. re-scan `SINGULARITY .:. OBLITERANT` from Studio;
3. confirm the new analysis reports engine `2.0.3-alpha`;
4. expected healthy state:

```text
Profile      FULL
Audio match  Current
Embedding    512D
LUFS         numeric
True Peak    numeric
```

If mastering remains unavailable, preserve the exact warning including the new FFmpeg tail. Build 08 must remain truthful rather than manufacture values.
