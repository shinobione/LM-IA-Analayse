# SonicTrace V2-E · BUILD 04

Date: 2026-08-10

Status: **IMPLEMENTED CANDIDATE — CI / PAGES / REAL-USER CATALOG SMOKE REQUIRED**

Safety ref: `safety/pre-v2e-build04-native-style-taxonomy-20260810-0110`

## Problem confirmed by real-user smoke

Build 03 introduced a correct distinction between:

- **Zones acoustiques** — the existing CLAP embedding / K-means proximity clusters;
- **Familles stylistiques** — a separate taxonomy derived from the saved Neural genre evidence.

However the public Catalog still displayed the old `Familles sonores` statistic and the user still could not see `Hip-Hop / Trap`.

The root cause was UI ownership, not missing taxonomy code. `catalog-ui.js` owns the normal Catalog render cycle and replaces the contents of `#st-catalog-stats` on every render. Build 03 patched the DOM after render, but its observer only reacted when the stats/legend elements themselves were added. Replacing the existing element's children therefore erased the Build 03 labels and panel without scheduling another taxonomy render.

## Build 04 correction

Build 04 keeps the Build 03 taxonomy and adds a **durable Catalog renderer** which survives native Catalog rerenders.

The renderer:

1. reads the saved catalog through `SonicTraceCatalog.memory.getTracks()`;
2. reuses `SonicTraceCatalog.styleFamilies.analyze(tracks)` — no second taxonomy implementation;
3. converts the legacy acoustic cluster statistic from `Familles sonores` to `Zones acoustiques`;
4. preserves the acoustic K-means count as acoustic information only;
5. creates/updates a separate `Familles stylistiques` statistic;
6. creates/updates the style-family panel with supporting Neural genre labels and representative track titles;
7. relabels the acoustic legend as `Zone acoustique N · …`;
8. observes child mutations of the existing stats/legend roots, so `catalog-ui.js` can rerender without permanently wiping the taxonomy layer.

## Style-family evidence

The underlying Build 03 family definitions remain unchanged. They include canonical families such as:

- `Hip-Hop / Trap`
- `R&B / Soul`
- `Bass / Dubstep`
- `Pop / Electronic Pop`
- `Electronic`
- `Reggae / Dancehall`
- `Lo-fi / Chillhop`
- `Rock / Alternative`

The taxonomy uses saved **Neural genres** first. Declared genre metadata is used only as fallback when no usable Neural genre evidence exists. Mood labels are not used to manufacture styles.

A track can contribute to multiple accepted style families when the saved Neural evidence is hybrid.

## Acoustic clusters remain intact

Build 04 deliberately preserves the existing CLAP similarity/K-means algorithm, including its historical cluster-count heuristic. With 12 catalog tracks that heuristic can legitimately produce 2 acoustic zones. Build 04 does **not** reinterpret those two zones as the artist's only two genres.

## Non-scope

Build 04 is frontend/catalog-presentation only. It changes no:

- Neural model;
- embedding model;
- GPU/CUDA worker;
- FFmpeg/loudnorm processing;
- coordinator API;
- Studio bridge;
- LaunchPAD runtime;
- Track Manager Worker;
- R2 data;
- C3 backend parity work.

## Required smoke

After CI and GitHub Pages publication:

1. hard-refresh SonicTrace and confirm `V2-E · BUILD 04`;
2. open Catalog;
3. confirm the stat previously named `Familles sonores` reads `Zones acoustiques`;
4. confirm a separate `Familles stylistiques` count is visible;
5. confirm the style-family panel remains present after selecting several tracks and after Catalog rerenders;
6. inspect whether `Hip-Hop / Trap`, `R&B / Soul`, `Bass / Dubstep`, `Pop / Electronic Pop` or `Electronic` appear according to the **actual saved Neural genre evidence**;
7. verify acoustic neighbor/map behavior remains unchanged.

Build 04 must not be considered visually complete until this real-user Catalog smoke passes.
