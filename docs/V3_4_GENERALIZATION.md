# SonicTrace Neural Accuracy V3.4 — Cross-Genre Generalization

Status: **CANDIDATE — CI + real-user validation required**

## Why V3.4 exists

V3.2/V3.3 fixed the concrete `Tinh Bolero Cho Trân` failure mode: role-aware Vietnamese style interpretation, sentimental-song arrangement grammar, Interlude instead of a false Drop, and terminal Outro intelligence.

That success exposed the next risk: overfitting SonicTrace to one real-user case while leaving other major families with much weaker structural priors.

V3.4 therefore generalizes structure intelligence across:

- Hip-Hop / Rap;
- Trap / Drill / Phonk / Grime impact sections;
- R&B / Soul song forms;
- Pop / Synth-pop song forms;
- Rock song forms;
- electronic / EDM drop-oriented forms.

## New evidence roles

V3.4 combines the existing section emission score with family-aware evidence:

- vocal activity;
- lyric density;
- lyric-hook evidence;
- audio hook/repetition evidence;
- drums + bass + energy impact;
- local energy rise from the previous section;
- section position and V3.3 terminality.

### Verse vs Chorus/Hook

Dense vocal sections with low repetition/hook evidence are favored toward Verse. Repeated vocal sections with strong hook evidence gain Chorus/Refrain support.

This is deliberately family-aware rather than a global hard rule.

### Real Drop vs generic instrumental

Electronic music keeps a strong Drop path when drums, bass, energy and transition impact support it. Low-impact or lyric-heavy electronic sections have Drop confidence reduced.

Trap/Phonk/Drill/Grime keep a more conservative Drop path for genuine low-vocal high-impact beat sections without turning normal rap verses into Drops.

### Song topology

Small transition priors now support common close-call paths:

- Pre-Chorus → Chorus for Pop/R&B/Rock;
- Verse ↔ Chorus for Pop/R&B/Rock and Hip-Hop;
- Bridge → Chorus for song-form families;
- Instrumental/Interlude → Drop for electronic grammar.

These priors are intentionally weaker than section audio evidence.

## Preserved V3.3 invariants

V3.4 must continue to pass:

- Vietnamese Bolero mid-song Interlude > Drop;
- terminal sentimental coda → Outro;
- genuine final Chorus remains Chorus;
- genuine terminal EDM Drop remains viable;
- terminal Pre-Chorus is rejected;
- early Bridge is penalized relative to mid/late Bridge.

## Validation

`scripts/test-semantic-generalization-v34.mjs` adds synthetic adversarial fixtures for:

- Boom Bap lyrical Verse;
- Trap impact section;
- Synth-pop repeated Chorus;
- Alternative R&B lyrical Verse;
- low-impact vocal Dubstep section;
- real high-impact Dubstep Drop;
- Pop Pre-Chorus → Chorus topology;
- Hip-Hop Verse → Hook topology;
- EDM vs Pop Drop-transition contrast.

Real-user acceptance should then sample at least one non-Bolero track from several families before V3.4 is considered fully generalized.

## Boundary

SonicTrace only. No Studio repository, Studio UI or Studio schema change is part of V3.4.
