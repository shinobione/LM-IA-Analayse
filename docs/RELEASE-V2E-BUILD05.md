# SonicTrace V2-E — Build 05

**Status:** implementation candidate pending CI + real-user smoke  
**Scope:** Catalog Intelligence frontend only  
**Base:** V2-E Build 04 (`fcadc2ca808e4f78b901f233af7f5fc3e99bf975`)  
**Safety checkpoint:** `safety/pre-v2e-build05-family-visual-language-20260810-0220`

## Why this build exists

Build 04 correctly separated two analytical concepts but still left a visual contradiction:

- **acoustic zones** came from the CLAP 2D projection / K-means clustering;
- **style families** came from saved Neural genre evidence;
- the map, track list and some insight surfaces still used acoustic-cluster colors while the family cards used another color system.

That made the same color mean different things depending on where the user looked.

Build 05 establishes one visible rule:

> **Position = acoustic proximity. Color = primary sonic family. Zone = secondary CLAP neighborhood.**

## User-facing vocabulary

The UI now uses **Familles sonores** as the visible category name for the Neural genre-derived taxonomy.

Examples include, when supported by saved evidence:

- Hip-Hop / Trap
- Bass / Dubstep
- Synthwave
- R&B / Soul
- Pop / Electronic Pop
- Electronic
- Reggae / Dancehall
- Lo-fi / Chillhop
- Rock / Alternative

The internal style-family analysis remains genre-derived and can still keep multiple assignments for hybrid tracks. The **primary** assignment is used only for the canonical display color.

## Stable family colors

Build 05 introduces a deterministic palette rather than assigning colors by card order or cluster number.

The same primary family color is applied to:

- family cards;
- map points;
- Catalog track-list dots;
- the `Lecture du catalogue` family section.

Unknown/dynamic genre families receive a deterministic fallback color derived from their stable family id, so they do not randomly change color after rerendering.

## Acoustic zones become secondary

Acoustic zones are deliberately kept because they answer a different question: which tracks are close in CLAP embedding space?

They no longer compete with genre-family colors:

- the map legend uses neutral **Zone acoustique A / B / …** labels;
- raw dominant genre/mood labels are removed from the visible zone names;
- map microcopy explicitly explains that zones are neighborhoods, not genres;
- bridge language now says that a track connects acoustic zones rather than “families”.

The K-means algorithm, cluster count, projection coordinates and similarity engine are unchanged.

## Technical implementation

New runtime layer:

- `js/catalog-family-language-build05.js`

New styling layer:

- `css/catalog-family-language-build05.css`

The layer runs after the Build 04 durable taxonomy renderer and re-applies its semantics after native Catalog rerenders. It does not fork or replace `catalog-ui.js` or `catalog-similarity.js`.

## Regression guards

CI now checks:

- the Build 03 genre-derived taxonomy ancestry is preserved;
- Build 04 durable rerender behavior is preserved;
- Build 05 has stable family palette entries;
- map and track-list colors use family ids;
- Build 05 does **not** derive family colors from acoustic cluster assignments;
- moods are not used to manufacture family categories;
- acoustic K-means ancestry remains untouched;
- Build 05 CSS/JS assets are loaded and syntax-checked.

## Explicit non-scope

Build 05 does **not** modify:

- FastAPI;
- FFmpeg / loudnorm;
- Neural models / CUDA;
- RTX 3060 / RTX 3070 Ti routing;
- embeddings;
- similarity weights;
- K-means / projection math;
- IndexedDB catalog contents;
- import/export format;
- R2;
- Track Manager;
- SHINOBIWAN Studio;
- C2.5-B or later Album architecture;
- C3 engine work;
- Phase 7.

## Real-user smoke checklist

After GitHub Pages deployment:

1. Confirm the header shows **`V2-E · BUILD 05`**.
2. Open **Catalogue** and confirm both **Zones acoustiques** and **Familles sonores** are present.
3. Confirm `Hip-Hop / Trap`, `Bass / Dubstep`, etc. keep the same color in the family cards and on their map points.
4. Confirm the track-list dot for a track matches its map-point family color.
5. Confirm the acoustic legend says **Zone acoustique A / B / …** and no longer presents `Soul · Uplifting` or `Dubstep · Uplifting` as if those were the only catalog families.
6. Confirm `Lecture du catalogue → Familles sonores` lists the Neural families, not the acoustic clusters.
7. Select several map points and zones; neighbor links and selection behavior must remain functional.
8. Confirm Album/EP selection controls are unchanged.

Build 05 must remain a **candidate** until this real-user smoke passes.
