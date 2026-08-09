# LMNotebook Neural Audio Analyzer

> SonicTrace UI release: **V2-E · BUILD 04** — durable Neural style families separated from acoustic CLAP zones.

Analyseur audio expérimental pour fichiers **MP3 / WAV**, construit comme un moteur hybride **Browser DSP V1 + Deep Audio V2**.

## SonicTrace release identity

The public interface is branded **SonicTrace Audio Intelligence** by the readability layer. Starting with **V2-E · BUILD 01**, the main brand block exposes a compact release marker directly below the product subtitle so screenshots, smoke tests and bug reports can identify the deployed UI without opening source/devtools.

**V2-E · BUILD 02** kept the same engine and reorganized the main action workflow only: audio selection and optional Lyrics/TXT context are grouped together first, the two primary analysis choices are presented as equal, prominent actions immediately below, and layer-specific tools remain in a single advanced toolbox. The layout moves the existing controls/handlers instead of creating a second analysis implementation. Mobile stacks the input/actions cleanly.

**V2-E · BUILD 03** corrected the Catalog Intelligence vocabulary exposed by real-user review. The embedding/K-means result is presented for what it actually represents: **Zones acoustiques** based on CLAP proximity. A separate frontend taxonomy derives **Familles stylistiques** from the saved Neural genre evidence, with canonical families such as `Hip-Hop / Trap`, `R&B / Soul`, `Bass / Dubstep`, `Pop / Electronic Pop` and `Electronic` when the catalog data supports them. A track can contribute to several style families when its saved genre evidence is genuinely hybrid. Mood labels are not used to manufacture genre families.

Real-user smoke then exposed a Build 03 integration bug: the native `catalog-ui.js` render cycle replaces the existing stats content and could erase the taxonomy DOM after it was patched. **V2-E · BUILD 04** keeps the Build 03 taxonomy but adds a durable renderer that re-applies the separation after every native Catalog stats/legend rerender. The acoustic K-means count remains an acoustic-zone count; a separate `Familles stylistiques` count/panel is regenerated from the saved Neural genres. The renderer also labels cluster legend entries as `Zone acoustique N · …`, preventing acoustic proximity from being mistaken for the artist's only genres.

Build 04 deliberately preserves the existing CLAP similarity/K-means ancestry, IndexedDB catalog data, import/export and project compatibility logic. It is frontend-only and does not change DSP, CUDA, FFmpeg/loudnorm, GPU workers, Studio integration or audio-retention behavior. See [`docs/RELEASE-V2E-BUILD01.md`](docs/RELEASE-V2E-BUILD01.md), [`docs/RELEASE-V2E-BUILD02.md`](docs/RELEASE-V2E-BUILD02.md), [`docs/RELEASE-V2E-BUILD03.md`](docs/RELEASE-V2E-BUILD03.md) and [`docs/RELEASE-V2E-BUILD04.md`](docs/RELEASE-V2E-BUILD04.md).

## SHINOBIWAN Studio Phase 5

The coordinator now exposes `POST /api/studio/analyze`, a one-upload, temporary-audio endpoint that returns the versioned Studio analysis envelope while preserving partial-layer warnings. Canonical persistence remains in LaunchPAD/R2 through Track Manager; SonicTrace does not retain or own a competing production catalog. See [`docs/STUDIO_PHASE5_CONTRACT.md`](docs/STUDIO_PHASE5_CONTRACT.md).

## Windows — mode zéro fatigue neuronale

Sur la machine RTX 3060, l’usage normal est désormais :

1. **Première installation si le repo n’est pas encore présent :** lancer `LMNotebook_INSTALL.cmd`.
2. **Tous les jours :** double-cliquer `LMNotebook_START.cmd`.
3. **Pour arrêter :** double-cliquer `LMNotebook_STOP.cmd`.

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
          ├── futurs modèles neuraux lourds
          │
          └──── LAN ────> RTX 3070 Ti 8 GB worker :8001
                          futurs stems / inférence parallèle
```

Le frontend n'a besoin de connaître que l'adresse du **coordinator RTX 3060**. Le backend inspecte ensuite les workers configurés sur le réseau local.

### V2-A — Mastering de référence — IMPLEMENTED FOUNDATION

`POST /api/analyze` mesure côté serveur :

- métadonnées ffprobe : codec, conteneur, bitrate, sample rate, canaux, durée
- Integrated Loudness (LUFS)
- Loudness Range (LRA)
- True Peak (dBTP)
- seuil loudness relatif
- mean / max volume FFmpeg pour cross-check
- provenance explicite `measured`
- suppression du fichier temporaire après analyse

Endpoints :

- `GET /api/health`
- `GET /api/cluster`
- `POST /api/analyze`
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

Le routage futur privilégiera d'abord **la quantité de VRAM requise**, puis la vitesse et la charge du worker.

## Lancement manuel — seulement pour debug

Le mode manuel reste disponible pour le développement avancé, mais n’est pas nécessaire pour l’usage normal.

Adresses locales :

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
http://127.0.0.1:8008
```

Le site GitHub Pages public restera le frontend de production. Quand l'API locale sera validée, elle pourra être exposée proprement via un endpoint **HTTPS sécurisé / tunnel** sans louer immédiatement un GPU cloud.

Voir `backend/README.md` pour la configuration complète du cluster RTX 3060 + RTX 3070 Ti.

## V2-B — Neural Music Understanding — NEXT

- genre / sous-genre multi-label avec probabilités
- mood, valence, arousal, danceability et energy estimés
- détection d'instruments
- embeddings audio
- scores de confiance par modèle
- exécution CUDA locale

## V2-C — Song Anatomy

- segmentation Intro / Verse / Chorus / Drop / Bridge / Outro
- self-similarity matrix
- répétitions / hooks / climax
- accords avec timestamps
- changements de tonalité et tempo local

## V2-D — Stems & Vocals

- Demucs : vocals / drums / bass / other
- analyse DSP par stem
- transcription lyrics + timestamps
- langue détectée
- activité vocale / densité / pitch approximatif
- répartition des jobs entre les deux GPU

## V2-E — Catalog Intelligence

- index d'embeddings par track
- carte de similarité réelle du catalogue
- zones acoustiques issues des embeddings CLAP
- familles stylistiques dérivées des genres Neural sauvegardés
- comparaison de versions / masters
- historique d'analyse

## Principe de confiance des données

Chaque métrique doit indiquer sa provenance :

- `measured` : mesure DSP déterministe
- `estimated` : estimation algorithmique
- `neural` : prédiction ML avec confiance
- `heuristic` : score dérivé / expérimental

Les scores comme « commercial potential », « originality » ou « Spotify compatibility » ne doivent jamais être présentés comme des mesures objectives du fichier audio.

## Déploiement

- **Frontend :** GitHub Pages
- **V2 développement :** RTX 3060 locale + RTX 3070 Ti LAN
- **V2 public :** endpoint HTTPS vers le coordinator local ou hébergement cloud ultérieur
- **GPU cloud :** inutile tant que les deux GPU locaux couvrent correctement la charge