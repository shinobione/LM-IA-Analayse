# Neural V3.5.5 — Real User Pass

Status: **REAL USER PASS**

Date: 2026-08-17

Scope: SonicTrace standalone only. **No STUDIO product code was modified.**

## What V3.5.5 closes

V3.5.5 closes the family-authority regression uncovered while calibrating hybrid Pop and Vietnamese Bolero material.

The key rule is now:

- the final style, family and semantic dimensions reason over the same final CLAP + Discogs ensemble evidence;
- an authoritative Vietnamese / Asian cluster may resolve its internal style when the ensemble primary is a same-family cultural tradition such as Nhạc Vàng;
- a form-only primary such as Vietnamese Pop Ballad does not receive the same authority and cannot manufacture Vietnamese Bolero;
- declared TXT metadata remains comparison/benchmark context only and is not used to force inference.

## Real-user validation pair

### Tinh Bolero Cho Trân

Validated on the real local DSP runtime.

Resolved dimensions:

- Style: **Vietnamese Bolero**
- Family: **Vietnamese / Asian**
- Tradition: **Nhạc Vàng**
- Form: **Sentimental Ballad**
- Region: **Vietnam**
- Grammar: **chanson sentimentale**

Captured evidence kept the ambiguity visible rather than hiding it:

- CLAP raw primary: Nhạc Vàng 53.5%
- Neo Soul raw: 52.4%
- final ensemble Neo Soul: 55.6%
- final ensemble Nhạc Vàng: 45.6%
- final ensemble Vietnamese Pop Ballad: 40.8%
- final ensemble Vietnamese Bolero: 31.9%
- family cluster: **Vietnamese / Asian authoritative, 77.6%**
- runner-up: **R&B / Soul / Funk 64.9%**
- cluster margin: **12.8%**

The resolved style remains Vietnamese Bolero because the ensemble primary is the same-family tradition Nhạc Vàng and the role-diverse Vietnamese evidence is authoritative.

The structure remained free of the former false EDM Drop interpretation and retained a terminal Outro.

### Stick to You

Validated on the same V3.5.5 runtime after the Bolero fix.

Resolved dimensions:

- Style: **Eurodance**
- Family: **Pop**
- Grammar: **pop**

Captured evidence:

- CLAP raw Eurodance: 54.3%
- CLAP raw Dancehall Pop: 50.5%
- final ensemble Eurodance: **61.1%**
- final ensemble Dancehall Pop: **48.0%**
- family cluster: **Pop authoritative, 95.0%**
- runner-up: Vietnamese / Asian 54.2%
- cluster margin: **40.7%**

This proves the V3.5.5 contextual-tradition authority does not reopen the old `Stick to You -> Vietnamese Bolero` false positive.

## Diagnostic probe policy after validation

The V3.5.3.1 real-payload diagnostic probe was essential to find the final authority bug, but it is no longer part of the normal UI.

Normal SonicTrace runtime:

- diagnostic probe disabled;
- no large diagnostic panel in the semantic context card.

Explicit debug runtime:

- append `&debug=neural` to the local SonicTrace URL;
- the existing read-only payload probe becomes available again;
- the probe never consumes or mutates the live inference response.

## Canonical conclusion

The paired real-user anti-regression is now closed:

- Vietnamese sentimental Bolero material can resolve to Vietnamese Bolero even when isolated Neo Soul evidence is individually strong;
- hybrid Dancehall / Eurodance Pop material remains Pop and does not inherit Vietnamese cultural authority;
- family coherence is resolved from audio-model evidence, not declared metadata.

V3.5.5 is therefore the current validated Neural family-coherence baseline before any future standalone SonicTrace accuracy work or later STUDIO integration planning.
