# Neural Accuracy V3.2.1 — REAL USER PASS

Status: **COMPLETE — REAL USER PASS for semantic dimensions + style-aware arrangement bootstrap**

Date: 2026-08-16

## Acceptance track

Real-user validation used the same `Tinh Bolero Cho Trân` WAV + TXT context that originally exposed the R&B/Soul misclassification and later the V3.2 bootstrap fallback.

Observed Neural evidence remained stable:

- `Nhạc Vàng` ~69%
- `Vietnamese Pop Ballad` ~63%
- `Vietnamese Bolero` ~51%
- `Neo Soul` lower secondary evidence

V3.2.1 correctly interprets those signals by role instead of forcing unlike concepts into one ranking:

- **Style:** `Vietnamese Bolero`
- **Tradition:** `Nhạc Vàng`
- **Form:** `Sentimental Ballad`
- **Family:** `Vietnamese / Asian`
- **Region:** `Vietnam`
- **Arrangement grammar:** `sentimental-song` / UI wording `chanson sentimentale`

The visible Semantic summary also reports `Vietnamese Bolero` as the dominant style rather than `Nhạc Vàng` or R&B/Soul.

## Arrangement acceptance

The real scan previously labeled the short section around 1:31 as `Drop` even though the song is Vietnamese Bolero / sentimental-song.

After V3.2.1 bootstrap hardening, the same section is labeled **`Interlude 2`**. This confirms that `semantic-v32.js` is actually loaded at runtime and that the style-aware sentimental-song grammar is active rather than the V3.1 generic fallback.

The accepted real-user arrangement now contains no EDM-style `Drop` on this Bolero case.

## Bootstrap regression that V3.2.1 closes

`semantic-bootstrap.js` previously returned early when `#semantic-arrangement-btn` already existed, before loading the V3.2 helper. Depending on UI boot order, SonicTrace could therefore display a V3.2 status while silently using V3.1 genre authority + generic arrangement grammar.

V3.2.1 fixes that by:

- loading/verifying the V3.2 helper before the existing-button early return;
- cache-busting helper/client assets as V3.2.1;
- surfacing an explicit runtime error rather than silently pretending V3.2 is active without its helper;
- protecting the ordering with a CI regression guard.

## Scope of the pass

This REAL USER PASS validates:

- role-aware semantic taxonomy;
- `Vietnamese Bolero` style authority;
- `Nhạc Vàng` tradition separation;
- sentimental-song arrangement grammar;
- removal of the false Bolero `Drop` on the acceptance track;
- correct runtime bootstrap of the V3.2 helper.

It does **not** claim that every structural label is final or universally correct. In the accepted scan, the long final section beginning around 2:57 is labeled `Interlude 3`; future structure-quality work may compare that reading against `Outro` using end-of-track position, vocal decay, recurrence and terminal-energy evidence.

That remaining tuning is separate from the V3.2.1 bootstrap/semantic correctness validated here.

## Compatibility / Studio boundary

- no Studio repository change;
- no Studio UI change;
- Studio schema remains v1/additive;
- `neural.embedding` remains CLAP 512D;
- Discogs 1280D remains nested in the expert payload;
- V3.2 semantic dimensions remain additive under `neural.genre_analysis.dimensions`.

## CI

Before merge of V3.2.1, all guards passed, including:

- FFmpeg regressions;
- Studio contract;
- Neural V3 taxonomy;
- V3.1 ensemble;
- V3.2 semantic dimensions;
- SHINOBIWAN benchmark;
- Semantic V3.2 genre + arrangement regression;
- bootstrap ordering regression;
- Catalog JS guards;
- real Discogs-EffNet ONNX smoke.
