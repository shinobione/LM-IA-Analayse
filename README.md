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

Backend Python prévu pour ajouter :

- LUFS BS.1770 / EBU R128
- True Peak
- genre / sous-genre multi-label
- mood / arousal / valence via modèles audio
- détection d'instruments
- segmentation Intro / Verse / Chorus / Drop / Bridge / Outro
- accords avec timestamps
- séparation stems (vocals / drums / bass / other)
- transcription lyrics + timestamps
- embeddings pour similarité entre morceaux
- analyse technique par stem

## Déploiement

Le front statique peut être hébergé directement sur GitHub Pages. La V1 n'a besoin d'aucun backend.
