# LMNotebook V2-B — Neural Music Understanding

V2-B is an optional GPU layer on top of the deterministic V2-A mastering analysis. If V2-B fails to install or run, V2-A stays available.

## Runtime

- Python 3.12 is managed privately by `uv` inside `backend/.venv`.
- PyTorch 2.11.0 is installed from the official CUDA 12.8 wheel index.
- The first CUDA verification performs a real matrix multiplication on the NVIDIA GPU.
- Model cache is kept under `backend/models/huggingface/` and is ignored by Git.

## First model

LMNotebook uses `laion/clap-htsat-unfused` through Hugging Face Transformers.

CLAP maps audio and natural-language text into the same embedding space. V2-B uses representative 10-second segments from across the track, averages the normalized audio embeddings, then compares that track embedding against curated candidate prompts.

Current neural outputs:

- genre / style ranking
- mood / emotion ranking
- instrumentation ranking
- relative perceptual axes: electronic, vocal, energy, brightness, danceability, aggression, atmosphere
- 512-dimensional track embedding for future catalog similarity

## Important interpretation rule

The displayed percentages are **relative zero-shot scores inside each candidate set**. They are not calibrated real-world probabilities and are not Spotify Audio Features. Every neural result is explicitly marked with `neural` provenance.

## Privacy

Audio uploads to the local API are temporary and deleted after the request. Model weights are cached locally; audio is not retained by V2-B.

## Next steps

- validate CLAP on a representative set of tracks
- tune candidate taxonomies against the catalog
- persist embeddings locally and build true similarity maps
- add a second specialized music-tagging model if CLAP needs genre refinement
- connect the RTX 3070 Ti LAN worker for parallel jobs
- add stems and transcription only after V2-B is stable
