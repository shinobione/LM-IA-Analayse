# SonicTrace V2-E · BUILD 03 — Catalog Style Families

Date: 2026-08-10

Status: **IMPLEMENTED CANDIDATE — CI / REAL-USER VISUAL SMOKE REQUIRED**

Safety ref: `safety/pre-v2e-build03-style-families-20260810-0024`

## Why Build 03 exists

Real-user Catalog review with 12 analyzed titles showed only two values under **Familles sonores**: `Soul · Uplifting` and `Dubstep · Uplifting`, despite individual saved analyses visibly containing several Hip-Hop, Trap, Pop/Electronic Pop and related genre results.

This was not caused by missing scans. The existing catalog similarity engine chooses its K-means cluster count with:

```text
k = round(sqrt(n / 2))
```

For `n = 12`:

```text
round(sqrt(6)) = 2
```

The UI then presented those two embedding clusters as if they were the catalog's only style families. Cluster labels also combined one dominant Neural genre with one dominant mood, which further compressed the musical vocabulary.

## Build 03 semantic split

Build 03 does **not** silently redefine the existing CLAP/K-means algorithm.

It separates two different questions:

### Zones acoustiques

The existing embedding projection/K-means result remains the source for map zones and proximity.

It answers:

> Which tracks occupy similar acoustic/embedding neighborhoods?

The previous `Familles sonores` stat is relabeled **Zones acoustiques** with explicit CLAP wording.

### Familles stylistiques

A new independent frontend taxonomy reads the saved Neural genre evidence from each catalog entry and consolidates common labels into understandable families.

Initial canonical mappings include:

- `Hip-Hop / Trap` — Hip-Hop, Rap, Trap, Drill, Boom Bap;
- `R&B / Soul` — R&B, RnB, Rhythm & Blues, Soul, Neo-Soul;
- `Bass / Dubstep` — Dubstep, Bass Music, Brostep, Grime, DnB;
- `Pop / Electronic Pop` — Pop, Electropop, Electronic Pop, Synthpop, Dance Pop;
- `Electronic` — Electronic, Electronica, EDM, House, Techno, Trance, Garage;
- additional mappings for Reggae/Dancehall, Lo-fi/Chillhop and Rock/Alternative.

The taxonomy does not use mood labels to manufacture styles. A family appears only when the saved genre evidence supports it. A track may belong to more than one stylistic family when its Neural genre evidence is genuinely hybrid.

## UI changes

Catalog gains:

- a dedicated **Familles stylistiques** stat;
- the former family count becomes **Zones acoustiques**;
- a separate style-family panel showing family name, track count, top supporting Neural labels and example tracks;
- map cluster legends are explicitly prefixed `Zone acoustique N` so they are no longer mistaken for canonical genre families.

Desktop stats expand to six columns where space permits, then fall back to three/two columns responsively.

## Preserved behavior

Build 03 preserves:

- saved IndexedDB catalog entries;
- CLAP 512D embeddings;
- similarity scores and neighbor ranking;
- existing K-means/projection ancestry;
- project compatibility analysis;
- import/export format;
- Neural scan results themselves;
- the Build 02 unified analysis workflow.

## Explicit non-scope

Build 03 is frontend-only and does **not**:

- change the Neural model;
- rescan audio automatically;
- change GPU workers;
- modify FFmpeg/loudnorm behavior;
- begin C3;
- alter Studio/Track Manager contracts;
- write LaunchPAD/R2 data;
- perform a catalog migration.

## Required visual smoke

After Pages deployment:

1. confirm header shows `V2-E · BUILD 03`;
2. open Catalog with the existing 12-track memory;
3. verify the old `Familles sonores: 2` wording is gone;
4. verify a separate `Zones acoustiques` count remains;
5. verify `Familles stylistiques` shows genre-derived families supported by saved scans;
6. specifically inspect whether Hip-Hop/Trap, R&B/Soul, Bass/Dubstep and Pop/Electronic Pop appear when the existing Neural genre evidence supports them;
7. verify the map still behaves as an embedding/proximity map;
8. verify import/export and track selection still work.

Build 03 remains a candidate until that real catalog is visually checked.