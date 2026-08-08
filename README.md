# LMNotebook Neural Audio Analyzer

Analyseur audio expérimental pour fichiers **MP3 / WAV**, désormais construit comme un moteur hybride **Browser DSP V1 + Deep Audio V2**.

## Windows — mode zéro fatigue neuronale

Sur la machine RTX 3060, l’usage normal est désormais :

1. **Première installation si le repo n’est pas encore présent :** lancer `LMNotebook_INSTALL.cmd`.
2. **Tous les jours :** double-cliquer `LMNotebook_START.cmd` ou le raccourci **LMNotebook Audio Analyzer** créé automatiquement sur le Bureau.
3. **Pour arrêter :** double-cliquer `LMNotebook_STOP.cmd`.

Le lanceur START s’occupe automatiquement de :

- mettre le repo à jour avec Git quand c’est sûr ;
- détecter Python, FFmpeg, ffprobe et NVIDIA ;
- tenter d’installer automatiquement Git / Python / FFmpeg via `winget` quand ils manquent ;
- détecter la RTX et afficher sa VRAM ;
- créer l’environnement Python `.venv` au premier lancement ;
- installer / mettre à jour les dépendances backend ;
- créer `backend/.env` si nécessaire ;
- démarrer l’API V2 sur le port `8000` ;
- démarrer le frontend local sur le port `8008` ;
- attendre que le moteur réponde ;
- ouvrir automatiquement LMNotebook dans le navigateur ;
- créer un raccourci Bureau ;
- enregistrer un log dans `logs/` en cas de souci.

En cas d’erreur, **aucun diagnostic manuel n’est demandé** : envoyer simplement une capture de la fenêtre du lanceur ou le dernier fichier de `logs/`.

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

La V2 est maintenant amorcée dans `backend/` avec FastAPI.

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

Le dashboard contient maintenant un panneau **Deep Audio V2 node**, un bouton **Deep Scan V2** et une zone dédiée aux mesures mastering V2.

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

Le mode manuel reste disponible pour le développement avancé, mais il n’est plus nécessaire pour l’usage normal.

Backend :

```powershell
cd backend
Copy-Item .env.example .env
.\run_windows.ps1
```

Frontend :

```powershell
.\run_frontend_windows.ps1
```

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
- clusters sonores
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
