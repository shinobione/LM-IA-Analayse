# Neural Accuracy V3.3 — Structure Intelligence

Status: **CANDIDATE — CI GREEN, REAL-USER ACCEPTANCE PENDING**

Date: 2026-08-16

Runtime merge: `07db95787e84cc80045ec67a1dac1a69ec4c8440`

## Scope

V3.3 builds on the real-user-passed V3.2.1 semantic dimensions and style-aware grammar. It does not change genre taxonomy, CLAP/Discogs inference, Catalog storage or the Studio contract.

The goal is section-role precision: distinguish a true terminal Outro/coda from a mid-song Interlude and tighten Verse / Pre-Chorus / Bridge roles with context rather than isolated local evidence.

## Structure Intelligence

V3.3 adds soft structural priors for:

- **Outro / coda** — terminal position, last-section status, vocal/lyrics retreat, low recurrence and energy decay;
- **Interlude** — low-vocal/instrumental contrast inside a song that still continues afterwards;
- **Verse** — vocal + lyric density with lower hook/repetition evidence;
- **Pre-Chorus** — short-ish vocal connector that plausibly leads into stronger hook/repetition/energy;
- **Bridge** — predominantly middle/late unique contrast, penalized when very early or strongly repeating.

These are priors, not hard rules.

## Safety counterexamples

The V3.3 regression suite explicitly protects cases that should *not* be rewritten into Outro:

- a genuine final Chorus with strong vocals, hook and recurrence remains Chorus;
- a genuine terminal electronic Drop remains viable under `electronic-drop` grammar;
- a mid-song Bolero instrumental section remains Interlude-like;
- early Bridge and dangling terminal Pre-Chorus paths are structurally penalized.

## Real-user target

The V3.2.1 acceptance scan of `Tinh Bolero Cho Trân` correctly produced:

- Style: `Vietnamese Bolero`
- Tradition: `Nhạc Vàng`
- Form: `Sentimental Ballad`
- Family: `Vietnamese / Asian`
- Region: `Vietnam`
- the former false `Drop` around 1:31 became `Interlude 2`

One remaining structural question was the long final block starting around 2:57, which still appeared as `Interlude 3`.

V3.3 acceptance target:

- the mid-song 1:31 section remains Interlude-like;
- the terminal ~2:57 block should prefer **Outro** when the real stems/energy/lyrics support closure;
- no regression of the Vietnamese Bolero semantic dimensions;
- no new false Drop.

## CI before merge

All guards passed before merge, including:

- FFmpeg regressions;
- Studio contract;
- Neural V3 taxonomy;
- V3.1 ensemble;
- V3.2 semantic dimensions;
- SHINOBIWAN benchmark;
- V3.2 genre/arrangement regression;
- V3.3 bootstrap/version regression;
- V3.3 structure-intelligence counterexamples;
- Catalog JavaScript guards;
- real Discogs-EffNet ONNX smoke.

## Studio boundary

- no Studio repository change;
- no Studio UI change;
- Studio schema remains v1/additive;
- no Catalog persistence change;
- CLAP 512D and Discogs 1280D roles remain unchanged.

V3.3 becomes **REAL USER PASS** only after the acceptance track is rescanned on the real SonicTrace runtime.
