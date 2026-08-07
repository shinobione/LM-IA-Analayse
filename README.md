# LMNotebook Neural Audio Analyzer

Analyseur audio expérimental pour fichiers **MP3 / WAV**.

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

## V2 — Deep Neural Scan

La V2 devient une architecture hybride : le navigateur garde la V1 instantanée, puis un backend Python effectue les calculs trop lourds ou nécessitant des modèles ML.

### Architecture cible

```text
GitHub Pages / Frontend
        │
        ├── Browser DSP V1 (instantané)
        │
        └── POST /api/analyze
                  │
                  ▼
             FastAPI backend
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
   FFmpeg      Essentia    Neural models
   / ffprobe   / librosa   / embeddings
       │          │          │
       └──────────┼──────────┘
                  ▼
          Unified analysis JSON
                  │
                  ▼
         Dashboard + provenance
```

### V2-A — Mastering / mesures de référence

Premier backend à construire, car il améliore immédiatement la précision sans dépendre de gros modèles :

- FFmpeg / ffprobe pour normaliser et inspecter les fichiers
- LUFS intégré, short-term et momentary selon BS.1770 / EBU R128
- Loudness Range (LRA)
- True Peak
- dynamique et headroom
- détection de clipping / inter-sample risk
- mesures spectrales plus robustes
- résultat JSON fusionné avec le DSP navigateur

### V2-B — Neural Music Understanding

Ajouter ensuite les modèles audio :

- genre / sous-genre multi-label avec probabilités
- mood, valence, arousal, danceability et energy estimés
- détection d'instruments
- embeddings audio pour empreinte de morceau et similarité
- scores de confiance affichés pour chaque prédiction

### V2-C — Song Anatomy

- segmentation Intro / Verse / Chorus / Drop / Bridge / Outro
- self-similarity matrix
- détection de répétitions / hooks / climax
- accords avec timestamps
- changements de tonalité et tempo local

### V2-D — Stems & Vocals

- séparation stems avec Demucs : vocals / drums / bass / other
- analyse DSP indépendante de chaque stem
- transcription lyrics avec timestamps
- langue détectée
- activité vocale / densité / plages de pitch approximatives

### V2-E — Catalog Intelligence

Quand plusieurs morceaux ont été analysés :

- index d'embeddings par track
- carte de similarité réelle du catalogue
- détection de clusters sonores
- comparaison de deux versions d'un même morceau
- historique des masters et différences V1/V2

## Principe de confiance des données

Chaque métrique doit indiquer sa provenance :

- `measured` : mesure DSP déterministe
- `estimated` : estimation algorithmique
- `neural` : prédiction d'un modèle ML avec confiance
- `heuristic` : score dérivé / expérimental

Les scores comme « commercial potential », « originality » ou « Spotify compatibility » ne doivent jamais être présentés comme des mesures objectives du fichier audio.

## Déploiement

Le front statique reste sur **GitHub Pages**.

Le backend V2 doit être hébergé séparément sur un service capable d'exécuter Python, FFmpeg et éventuellement des modèles lourds. Le front appelle ensuite l'URL du backend via HTTPS/CORS.

**Prochain jalon recommandé : V2-A.** Créer `backend/` avec FastAPI + endpoint `/api/analyze`, brancher LUFS / True Peak / ffprobe, puis connecter ce résultat au dashboard existant avant d'ajouter les modèles neuraux.
