# LMNotebook Deep Audio V2 — local GPU cluster

The V2 backend is designed around the hardware currently available to the project:

- **Primary machine:** NVIDIA RTX 3060 12 GB — coordinator + primary neural worker
- **LAN machine:** NVIDIA RTX 3070 Ti 8 GB — secondary GPU worker

The first V2 milestone (V2-A mastering) does not require CUDA, but the API already detects NVIDIA GPUs and exposes cluster capabilities so the next neural layers can use both cards.

## Target architecture

```text
GitHub Pages dashboard
        |
        | HTTPS later / localhost during development
        v
RTX 3060 12 GB machine
FastAPI coordinator :8000
  |-- FFmpeg / ffprobe / BS.1770 mastering
  |-- V2-B genre + mood + embeddings (planned)
  |-- large neural models when VRAM matters
  |
  `---- LAN ----> RTX 3070 Ti 8 GB worker :8001
                  |-- Demucs stems (planned)
                  |-- transcription / smaller neural jobs
                  `-- parallel inference jobs
```

The coordinator is the only endpoint the frontend needs to know. It will eventually route GPU jobs to the best available node.

## V2-A already implemented

`POST /api/analyze`

Current server-side measurements:

- ffprobe container / codec / bitrate / sample rate / channels / duration
- Integrated Loudness (LUFS)
- Loudness Range (LRA)
- True Peak (dBTP)
- relative loudness threshold
- FFmpeg mean / max volume cross-check
- explicit `measured` provenance
- temporary file deletion after analysis

Operational endpoints:

- `GET /api/health` — FFmpeg + NVIDIA GPU capability snapshot
- `GET /api/cluster` — coordinator + configured LAN workers
- `POST /api/analyze` — V2-A mastering scan
- `/docs` — FastAPI interactive API documentation

## 1. Install prerequisites on the RTX 3060 machine

Required now:

1. Python 3.11 or 3.12
2. FFmpeg + ffprobe available in `PATH`
3. Current NVIDIA driver (`nvidia-smi` should work)

CUDA / PyTorch is **not required yet** for V2-A.

## 2. Run the coordinator on Windows

Open PowerShell in `backend/`:

```powershell
Copy-Item .env.example .env
.\run_windows.ps1
```

Then open:

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/docs
```

The dashboard V2 panel uses `http://127.0.0.1:8000` by default for local development.

## 3. Prepare the RTX 3070 Ti LAN worker

Clone the same repository on the second machine. In `backend/.env` use for example:

```env
LMN_NODE_NAME=RTX3070TI-WORKER
LMN_NODE_ROLE=gpu-worker
LMN_WORKERS=
```

Run the worker on port 8001:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Allow TCP port **8001 only on the private/local Windows network firewall profile**.

On the RTX 3060 coordinator, set its `.env` to the LAN IP of the worker:

```env
LMN_NODE_NAME=RTX3060-PRIMARY
LMN_NODE_ROLE=coordinator
LMN_WORKERS=http://192.168.x.x:8001
```

Restart the coordinator, then `GET /api/cluster` will report both machines and their GPU VRAM.

## GPU routing strategy

### RTX 3060 12 GB — primary

The 12 GB VRAM makes this the preferred node for:

- larger audio transformers
- embeddings / genre / mood models
- transcription models when model size matters
- jobs that would be tight on an 8 GB card
- coordinator responsibilities

### RTX 3070 Ti 8 GB — secondary / fast worker

The 3070 Ti has higher raw compute than the 3060 but less VRAM. It is a strong candidate for:

- Demucs stem separation
- smaller transcription models
- parallel inference
- batch jobs
- models known to fit comfortably inside 8 GB

The routing layer will prefer **VRAM fit first**, then speed / current load.

## HTTPS and GitHub Pages

During development the frontend and backend can both be served locally.

For the public GitHub Pages site, the V2 API must eventually be reachable through HTTPS. The preferred local-GPU solution is:

```text
GitHub Pages HTTPS
      |
      v
secure HTTPS tunnel / reverse proxy
      |
      v
RTX3060 FastAPI coordinator on the local machine
```

This lets the project use the local GPUs without immediately renting cloud GPU hardware. We will configure the tunnel only after the local API has been validated.

## Privacy model

V2-A currently uses:

```text
upload -> temporary file -> analysis -> JSON response -> delete temporary file
```

The server does not intentionally retain uploaded masters.

## Next implementation layers

1. **Validate V2-A locally** on a known WAV and compare LUFS / True Peak with a trusted meter.
2. Install CUDA-compatible PyTorch on both GPU machines.
3. V2-B: genre / subgenre, mood, valence, arousal, embeddings, instruments.
4. V2-C: structure, repetitions, chords, hooks, climax.
5. V2-D: Demucs stems + transcription + per-stem analysis.
6. Add the job router so both local GPUs can work concurrently.
7. Add an HTTPS tunnel for the public GitHub Pages dashboard.
