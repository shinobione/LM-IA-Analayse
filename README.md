# LMNotebook Neural Audio Analyzer

> SonicTrace UI release: **V2-E · BUILD 08** — COMPLETE · REAL USER PASS. Fresh-runtime enforcement plus deterministic FFmpeg mastering capture now recover the full Studio analysis path without changing canonical authority.
>
> Neural analysis layer: **V3.2 · SEMANTIC DIMENSIONS + ARRANGEMENT GRAMMAR** — merged after green CI + real Discogs ONNX smoke. The standalone UI release remains V2-E Build 08; V3.2 separates style/tradition/form evidence and makes semantic arrangement style-aware while keeping the Studio contract additive and Studio itself untouched.

Analyseur audio expérimental pour fichiers **MP3 / WAV**, construit comme un moteur hybride **Browser DSP V1 + Deep Audio V2**.

## SonicTrace release identity

The public interface is branded **SonicTrace Audio Intelligence** by the readability layer. Starting with **V2-E · BUILD 01**, the main brand block exposes a compact release marker directly below the product subtitle so screenshots, smoke tests and bug reports can identify the deployed UI without opening source/devtools.

**V2-E · BUILD 02** kept the same engine and reorganized the main action workflow only: audio selection and optional Lyrics/TXT context are grouped together first, the two primary analysis choices are presented as equal, prominent actions immediately below, and layer-specific tools remain in a single advanced toolbox. The layout moves the existing controls/handlers instead of creating a second analysis implementation. Mobile stacks the input/actions cleanly.

**V2-E · BUILD 03** corrected the Catalog Intelligence vocabulary exposed by real-user review. The embedding/K-means result is presented for what it actually represents: **Zones acoustiques** based on CLAP proximity. A separate frontend taxonomy derives style families from the saved Neural genre evidence, with canonical families such as `Hip-Hop / Trap`, `R&B / Soul`, `Bass / Dubstep`, `Pop / Electronic Pop` and `Electronic` when the catalog data supports them. A track can contribute to several style families when its saved genre evidence is genuinely hybrid. Mood labels are not used to manufacture genre families.

Real-user smoke then exposed a Build 03 integration bug: the native `catalog-ui.js` render cycle replaces the existing stats content and could erase the taxonomy DOM after it was patched. **V2-E · BUILD 04** keeps the Build 03 taxonomy but adds a durable renderer that re-applies the separation after every native Catalog stats/legend rerender. The acoustic K-means count remains an acoustic-zone count; a separate family count/panel is regenerated from the saved Neural genres.

**V2-E · BUILD 05** unifies the visible language. The Neural genre-derived taxonomy is presented as **Familles sonores** and receives stable family colors. The same primary family color now follows a track through the family cards, 2D map, Catalog track list and `Lecture du catalogue`. The 2D position still comes from CLAP proximity; the K-means result remains a separate **Zone acoustique A / B / …** layer with neutral labels. In short: **position = proximité, couleur = famille sonore, zone = voisinage acoustique**. No similarity, clustering, GPU, backend or catalog-storage algorithm is changed.

**V2-E · BUILD 06** opened PHASE UX / C3. The coordinator mastering path became resilient to FFmpeg `loudnorm` output variations: loudnorm JSON parsing is order/spacing independent, a real `ebur128` measurement is used as fallback, and a measurement that is still unavailable becomes an explicit partial-layer diagnostic instead of aborting `/api/studio/analyze`. Neural, 512D embedding, Song Anatomy and optional stem fusion therefore remain available when only V2-A mastering degrades. Build 06 was accepted through a real-user FULL Studio scan.

**V2-E · BUILD 07** hardened the measurement layer after a fresh `SINGULARITY .:. OBLITERANT` scan exposed a remaining PARTIAL mastering state. `loudnorm` failure/timeout/no-JSON now still attempts EBU R128, while `volumedetect` failure/timeout/no-measurement attempts FFmpeg `astats`. All recovered values keep explicit measured provenance and Browser DSP is never promoted to server mastering truth.

**V2-E · BUILD 08** closes the remaining real-machine seam. `SONICTRACE_UPDATE_AND_START.cmd` now guarantees a managed stop before restarting updated code, `SONICTRACE_START.cmd` pins Deep Audio engine identity `2.0.3-alpha`, and FFmpeg mastering commands explicitly capture plain `info` logs from combined stdout/stderr with UTF-8 replacement. A real-user `SINGULARITY .:. OBLITERANT` scan reached FULL, was explicitly saved, and Studio then confirmed `Canonical reread verified`; the durable R2 profile remained FULL with `-15.1 LUFS` and `0.2 dBTP`. Build 08 is **COMPLETE — REAL USER PASS**.

Build 08 itself preserves the existing CLAP similarity/K-means ancestry, family visual language, IndexedDB catalog data, import/export and project compatibility logic. It does not change canonical persistence authority, source-audio retention, Track Manager/R2 ownership, Song Anatomy/Demucs semantics, Studio Focus runtime or Phase 7-C.

### Neural Accuracy V3.2 — SEMANTIC DIMENSIONS + ARRANGEMENT GRAMMAR

V3 changes the **music-understanding and semantic-reading layers**, not the V2-E Build 08 release identity.

The old V2-B genre path used a small closed candidate list and a softmax that necessarily produced a winner even when the correct style was absent. V3 replaced that failure mode with:

- a materially broader hierarchical, open-vocabulary candidate taxonomy;
- explicit regional vocabulary including `Vietnamese Bolero`, `Nhạc Vàng`, `Nhạc Trữ Tình`, `V-Pop` and related Vietnamese candidates;
- a separate `Latin Bolero` candidate so Vietnamese Bolero is not collapsed into an unrelated regional tradition;
- multi-prompt CLAP evidence per candidate to reduce wording sensitivity;
- genre classification on each representative segment **before** track-level consensus;
- style consensus, family consensus and winner-margin evidence;
- an honest `Unknown / hybrid` result when evidence is too weak or unstable to force a genre;
- expanded mood and instrumentation vocabularies;
- preservation of the existing 512D CLAP track embedding for Catalog Intelligence;
- an additive `neural.genre_analysis` payload and `semanticSummary.genreAnalysis` mirror for future Studio adoption;
- a SHINOBIWAN benchmark harness seeded with the artist-confirmed `Tinh Bolero Cho Trân → Vietnamese Bolero / Vietnamese / Asian` regression case.

V3.1 added a second, music-first expert rather than trusting CLAP alone:

- the official **Discogs-EffNet / Discogs400** ONNX model predicts 400 style labels;
- it produces a separate **1280D music embedding** kept inside the expert payload;
- the existing **512D CLAP embedding remains the canonical Catalog Intelligence embedding**;
- ONNX Runtime prefers CUDA when available and falls back to CPU;
- the expert model/metadata are cached locally under the gitignored `backend/models/` directory;
- any expert download/dependency/inference failure falls back to CLAP V3 instead of breaking the scan;
- a conservative ensemble cross-checks direct style agreement and broad-family disagreement before changing confidence or allowing an override;
- `Latin---Bolero` may support a bolero-like musical structure but **cannot rewrite `Vietnamese Bolero` into a Latin regional label**;
- a real CI smoke test downloads and runs the official ONNX model, verifies 128×96 patches, 400 style outputs and the 1280D embedding.

V3.2 adds a role-aware semantic layer over that evidence:

- `neural.genre_analysis.dimensions.family` — broad family;
- `dimensions.style.primary` — specific musical style;
- `dimensions.tradition.primary` — tradition/cultural context;
- `dimensions.form.primary` — song form / stylistic color;
- `dimensions.region` — regional model inference;
- `dimensions.influences` — secondary evidence;
- `dimensions.unknown` — preserves uncertainty instead of converting evidence into false certainty.

For the real `Tinh Bolero Cho Trân` pattern, `Nhạc Vàng` may remain the strongest **raw evidence** while V3.2 interprets the dimensions as **Style = Vietnamese Bolero**, **Tradition = Nhạc Vàng**, **Form = Sentimental Ballad**, **Family = Vietnamese / Asian**.

The semantic arrangement reader is now style-aware too. It adds `Interlude` as a real section label and uses grammar profiles. Vietnamese Bolero / Nhạc Vàng / Nhạc Trữ Tình / ballad-like contexts strongly penalize an EDM-style `Drop` and favor Interlude / Bridge / Instrumental when supported by the audio, while electronic/drop-oriented music keeps a valid strong Drop path.

Legacy `neural.genres`, `neural.moods`, `neural.instruments`, `neural.traits` and the 512D `neural.embedding` remain available for current consumers. Genre relevance/confidence remains model evidence rather than an absolute probability.

See [`docs/V3_NEURAL_ACCURACY.md`](docs/V3_NEURAL_ACCURACY.md) and [`docs/STUDIO_PHASE5_CONTRACT.md`](docs/STUDIO_PHASE5_CONTRACT.md).

Release docs: [`BUILD 01`](docs/RELEASE-V2E-BUILD01.md), [`BUILD 02`](docs/RELEASE-V2E-BUILD02.md), [`BUILD 03`](docs/RELEASE-V2E-BUILD03.md), [`BUILD 04`](docs/RELEASE-V2E-BUILD04.md), [`BUILD 05`](docs/RELEASE-V2E-BUILD05.md), [`BUILD 06`](docs/RELEASE-V2E-BUILD06.md), [`BUILD 07`](docs/RELEASE-V2E-BUILD07.md), [`BUILD 08`](docs/RELEASE-V2E-BUILD08.md).

## SHINOBIWAN Studio Phase 5 / C3

The coordinator exposes `POST /api/studio/analyze`, a one-upload, temporary-audio endpoint that returns the versioned Studio analysis envelope while preserving partial-layer warnings. Starting with Build 06, an unavailable mastering sub-layer no longer prevents other Deep Audio layers from being returned. Build 08 adds fresh-runtime enforcement and deterministic FFmpeg capture around that same contract. Neural Accuracy V3.2 keeps the envelope at schema version 1 and adds role-aware dimensions under `neural.genre_analysis.dimensions` without removing the V3.1 evidence or existing compatibility fields. The optional Discogs expert remains nested inside that additive neural payload; the top-level 512D embedding contract is unchanged. Canonical persistence remains in LaunchPAD/R2 through Track Manager; SonicTrace does not retain or own a competing production catalog. **No Studio repository or Studio UI change is part of Neural Accuracy V3.2.** See [`docs/STUDIO_PHASE5_CONTRACT.md`](docs/STUDIO_PHASE5_CONTRACT.md).

## Windows — mode zéro fatigue neuronale

Sur la machine RTX 3060, l’usage normal est désormais :

1. **Première installation si le repo n’est pas encore présent :** lancer `LMNotebook_INSTALL.cmd`.
2. **Mise à jour + démarrage sûr :** lancer `SONICTRACE_UPDATE_AND_START.cmd`.
3. **Démarrage quotidien sans update :** lancer `SONICTRACE_START.cmd` ou `LMNotebook_START.cmd`.
4. **Pour arrêter :** lancer `SONICTRACE_STOP.cmd` ou `LMNotebook_STOP.cmd`.

### Runtime isolé avec uv

Le lanceur ne dépend plus du Python installé dans Windows, ni des alias Microsoft Store, ni d’un `PATH` Python correct.

`LMNotebook_START.cmd` :

- détecte ou installe `uv` via `winget` ;
- laisse `uv` télécharger et gérer un Python 3.12 privé pour LMNotebook si nécessaire ;
- crée `backend/.venv` sans modifier le Python système ;
- installe les dépendances backend dans cet environnement isolé ;
- vérifie / installe FFmpeg ;
- crée `backend/.env` si nécessaire ;
- démarre l’API V2 sur `http://127.0.0.1:8000` ;
- démarre le frontend sur `http://127.0.0.1:8008` ;
- ouvre automatiquement LMNotebook dans le navigateur.

Le but est simple : **le système Python de Windows n’est plus une dépendance du projet**.

## V1 — Browser DSP

La V1 fonctionne directement dans le navigateur et garde le fichier audio local :

- décodage PCM via Web Audio API
- durée, sample rate, canaux et taille du fichier
- BPM estimé + confiance
- tonalité majeure/mineure + Camelot + confiance
- RMS dBFS, peak dBFS, crest factor
- détection de clipping, DC offset, zero-crossing rate
- largeur stéréo Mid/Side, balance L/R et corrélation stéréo
- FFT : spectral centroid, roll-off 85%, flatness, flux
- distribution d'énergie par bandes fréquentielles
- chroma 12 notes
- waveform réelle
- spectrogramme réel
- timeline d'énergie
- Sonic DNA mesuré
- diagnostic technique automatique
- export complet en JSON

Les descripteurs de style de la V1 sont **heuristiques**. Ils ne doivent pas être confondus avec une vraie classification de genres par modèle ML.

## V2 — Deep Audio backend

La V2 est amorcée dans `backend/` avec FastAPI.

Architecture retenue pour le développement :

```text
GitHub Pages / navigateur
        │
        ├── Browser DSP V1
        │
        └── Deep Scan V2
                 │
                 ▼
        RTX 3060 12 GB machine
        FastAPI coordinator :8000
          │
          ├── FFmpeg / ffprobe / BS.1770
          ├── modèles neuraux lourds
          │
          └──── LAN ────> RTX 3070 Ti 8 GB worker :8001
                          stems / inférence parallèle
```

Le frontend n'a besoin de connaître que l'adresse du **coordinator RTX 3060**. Le backend inspecte ensuite les workers configurés sur le réseau local.

### V2-A — Mastering de référence — IMPLEMENTED

`POST /api/analyze` et le chemin Studio mesurent côté serveur :

- métadonnées ffprobe : codec, conteneur, bitrate, sample rate, canaux, durée
- Integrated Loudness (LUFS)
- Loudness Range (LRA)
- True Peak (dBTP)
- seuil loudness relatif
- mean / max volume FFmpeg pour cross-check
- provenance explicite (`measured-loudnorm-json`, `measured-ebur128-fallback`, `measured`, `measured-astats-fallback` ou `unavailable`)
- suppression du fichier temporaire après analyse

Endpoints :

- `GET /api/health`
- `GET /api/cluster`
- `POST /api/analyze`
- `POST /api/studio/analyze`
- `/docs`

Le dashboard contient un panneau **Deep Audio V2 node**, un bouton **Deep Scan V2** et une zone dédiée aux mesures mastering V2.

## Hardware plan

### Primary — RTX 3060 12 GB

Rôle prévu :

- coordinateur FastAPI
- modèles nécessitant le plus de VRAM
- genre / mood / embeddings
- transcription lourde si nécessaire
- fallback pour tous les jobs GPU

### Secondary LAN worker — RTX 3070 Ti 8 GB

Rôle prévu :

- Demucs / séparation stems
- modèles plus petits
- transcription parallèle
- batch / jobs concurrents

Le routage privilégie d'abord **la quantité de VRAM requise**, puis la vitesse et la charge du worker.

## Lancement manuel — seulement pour debug

Le mode manuel reste disponible pour le développement avancé, mais n’est pas nécessaire pour l’usage normal.

Adresses locales :

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
http://127.0.0.1:8008
```

Le site GitHub Pages public reste le frontend publié. Le calcul Deep Audio reste assuré par le coordinator local/GPU.

Voir `backend/README.md` pour la configuration complète du cluster RTX 3060 + RTX 3070 Ti.

## V2-B → V3.2 — Neural Music Understanding — IMPLEMENTED

- classification genre / sous-genre **open-vocabulary et hiérarchique** avec familles, styles et régionalité ;
- classification de chaque segment représentatif avant consensus morceau ;
- confiance fondée sur stabilité temporelle + marge de similarité, avec `Unknown / hybrid` lorsque les preuves sont insuffisantes ;
- second expert **Discogs400 / EffNet ONNX** pour validation music-first ;
- ensemble conservateur CLAP + Discogs avec garde de régionalité ;
- dimensions V3.2 séparant **famille / style / tradition / forme / région / influences** ;
- benchmark fondé sur le style musical explicite plutôt que sur un mélange tradition/style ;
- vocabulaire mood élargi ;
- détection d'instruments élargie ;
- embeddings audio CLAP 512D conservés pour Catalog Intelligence ;
- embedding music-first Discogs 1280D conservé séparément dans l'expert ;
- compatibilité maintenue via `neural.genres`, `neural.moods`, `neural.instruments`, `neural.traits` et `neural.embedding` ;
- sortie V3 additive via `neural.genre_analysis` + `neural.genre_analysis.dimensions` ;
- scores de genre exposés comme **evidence/relevance de modèle**, jamais comme probabilités absolues ;
- exécution CUDA locale quand disponible, fallback expert CPU/CLAP fail-safe ;
- lecture sémantique V3.2 style-aware avec `Interlude` et grammaires d'arrangement préservant les vrais Drops électroniques tout en pénalisant les Drops incohérents sur les chansons sentimentales.

## V2-C — Song Anatomy — IMPLEMENTED

- segmentation Intro / Verse / Chorus / Drop / Bridge / Outro
- répétitions / hooks / climax
- structure signal-derived avec labels heuristiques
- exécution coordinator

## V2-D — Stems & Vocals — IMPLEMENTED

- Demucs : vocals / drums / bass / other
- analyse par stem
- routage coordinator / worker LAN
- activité des sources
- fusion V2-C × V2-D lorsque la route GPU est disponible

## V2-E — Catalog Intelligence — IMPLEMENTED / STUDIO PARITY AVAILABLE

- index d'embeddings par track
- carte de similarité réelle du catalogue
- zones acoustiques issues des embeddings CLAP
- familles sonores dérivées des genres Neural sauvegardés
- couleurs de famille stables sur les différentes surfaces Catalog
- projection 2D, outliers, bridges et analyse de projet dans le standalone
- comparaison de versions / masters
- historique d'analyse

Studio s'appuie sur les sidecars R2 canoniques pour la parité utile et ne fait pas de l'IndexedDB standalone une nouvelle autorité.

## Principe de confiance des données

Chaque métrique doit indiquer sa provenance :

- `measured*` : mesure DSP déterministe
- `estimated` : estimation algorithmique
- `neural` : prédiction ML avec confiance
- `heuristic` : score dérivé / expérimental
- `unavailable` : couche tentée mais mesure non récupérable ; ne doit jamais être affichée comme zéro

Les scores comme « commercial potential », « originality » ou « Spotify compatibility » ne doivent jamais être présentés comme des mesures objectives du fichier audio.

## Déploiement

- **Frontend :** GitHub Pages
- **Deep Audio :** RTX 3060 locale + RTX 3070 Ti LAN
- **Canonical catalog persistence :** Track Manager / Cloudflare R2
- **GPU cloud :** inutile tant que les deux GPU locaux couvrent correctement la charge
