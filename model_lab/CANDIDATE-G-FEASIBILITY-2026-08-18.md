# SonicTrace V4 Model Lab — Candidate G feasibility gate

Date: 2026-08-18

Proposed challenger: **MOSS-Music-8B-Instruct**

Status: **FEASIBILITY ONLY — DO NOT DOWNLOAD YET**

## Why Candidate G is materially different

This is not another CLAP-family cosine classifier. MOSS-Music is a generative music-understanding model built specifically for musical captioning/tagging, lyrics ASR, structural analysis, chord/key/tempo reasoning, instrumentation and long-form musical QA.

Upstream repository:

- `OpenMOSS/MOSS-Music`
- inspected main commit: `ad107c7ddaa06de168a0dfbc18d3e1e6a40c0e5e`

Released model:

- `OpenMOSS-Team/MOSS-Music-8B-Instruct`
- audio encoder: MOSS-Audio-Encoder
- LLM backbone: Qwen3-8B
- total size: ~9.1B parameters
- published weights: BF16
- model license: Apache-2.0

This license boundary is materially more attractive for a future SonicTrace product than MuQ-MuLan's current non-commercial weights.

## Upstream quality signal

The official model card reports strong music-specific evaluation results, including:

- 93.59 on GTZAN genre classification;
- 92.42 on Medley-Solos-DB;
- strong music captioning scores across genre/style, mood, tempo, instrumentation, structure and production dimensions;
- explicit support for structural analysis, chord/key/tempo reasoning, instrumentation and musical description.

These upstream metrics are not a substitute for the SonicTrace four-track torture set, but they are strong enough to justify a feasibility gate.

## Official runtime path

The inspected upstream runtime currently recommends:

- Python >= 3.10 (README recommends Python 3.12);
- `torch==2.9.1+cu128`;
- `torchaudio==2.9.1+cu128`;
- `torchcodec==0.9.*`;
- `transformers==4.57.1`;
- SGLang serving for best quality/throughput.

The repository also ships a simpler Transformers sanity path using `MossMusicModel.from_pretrained(..., torch_dtype="auto", device_map="cuda:0")`.

The model class derives from Hugging Face `PreTrainedModel`, but upstream does **not** currently document or publish an official 4-bit MOSS-Music checkpoint/configuration.

## RTX 3060 12 GB reality check

### BF16 / FP16

Not viable as a pure-GPU SonicTrace path on a 12 GB RTX 3060.

At ~9.1B parameters, BF16 weights alone are roughly 18 GB before activations, audio encoder working memory and KV cache. The official published checkpoint is therefore larger than the available VRAM before inference begins.

### 8-bit

Still not a comfortable target. Raw quantized weights would be roughly 9+ GB before runtime overhead, audio encoder memory, activations and generation cache. This leaves too little safety margin for full-track audio understanding on a 12 GB card.

### 4-bit

**Potentially feasible, but unproven.**

A 9.1B model at nominal 4-bit weight storage is roughly 4.5 GB before quantization metadata and non-quantized modules. That creates a plausible 12 GB loading envelope, but several risks remain:

1. upstream MOSS-Music does not document a supported 4-bit inference recipe;
2. the custom multimodal audio encoder/adapters may remain partially BF16/FP16 even if Qwen linear layers are quantized;
3. audio token sequences and generation KV cache can consume substantial additional VRAM;
4. the officially recommended SGLang path is heavier operationally than the current Model Lab challengers;
5. Windows-native quantized custom-model support must be proven rather than assumed;
6. quantization may alter the music-understanding quality that makes Candidate G interesting in the first place.

## Decision

Candidate G is **NOT rejected**.

It is also **NOT ready for a 15–20 GB blind download**.

The correct next step is a two-stage gate:

### G0 — local preflight, zero model download

Check the actual workstation for:

- RTX model and total/free VRAM;
- NVIDIA driver and CUDA compatibility;
- WSL2 availability/version;
- free disk space;
- Python/uv availability;
- whether a supported quantized runtime path can be assembled without modifying SonicTrace V3.

### G1 — quantized loading proof

Only if G0 is green:

- create a completely separate `model_lab/.runtime/moss_music_8b_4bit/` runtime;
- pin upstream commit and dependencies;
- use MOSS-Music-8B-Instruct, not Thinking, for the first test;
- attempt 4-bit loading with the smallest deterministic audio probe possible;
- do **not** download the four benchmark WAVs or inject TXT metadata into prompts;
- setup must not print READY until a real audio-conditioned response succeeds on the RTX 3060;
- record real peak VRAM and system RAM/offload use.

### G2 — SonicTrace torture set

Only after G1 proves stable:

Run the same four songs without artist TXT during inference and ask MOSS-Music for a strictly machine-readable analysis covering at minimum:

- family;
- primary style + secondary styles;
- tradition/region when justified;
- form;
- mood;
- instrumentation;
- structural summary.

The benchmark truth remains post-inference only.

## Product gate

Candidate G would still have to beat or materially approach MuQ on the same real tracks. The attractive Apache-2.0 license does not compensate for weak music understanding.

No SonicTrace V3, Catalogue V2-E or SHINOBIWAN STUDIO integration should occur during G0/G1/G2.

## Current recommendation

**Proceed with G0 preflight only. Do not download MOSS-Music weights yet.**

MuQ-MuLan remains the raw quality reference until a product-compatible challenger proves otherwise.