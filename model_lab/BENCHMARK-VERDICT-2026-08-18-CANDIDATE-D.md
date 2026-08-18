# SonicTrace V4 Model Lab — Candidate D verdict (2026-08-18)

Status: **Candidate D invalidated as a reliable quality benchmark because the upstream Hugging Face conversion is known to be unreliable.** This record does not modify SonicTrace V3, the catalogue, or SHINOBIWAN STUDIO.

## Candidate

- model: `laion/larger_clap_music`
- pinned revision: `a0b4534`
- interface used: Hugging Face `transformers` `ClapModel` / `ClapProcessor`
- audio policy: five deterministic evenly-spaced exact 10-second clips at 48 kHz
- embedding: 512D
- inference: audio only
- declared TXT/reference metadata used for inference: **NO**

## Real four-track observation

The RTX 3060 run completed technically, but the semantic output was effectively collapsed:

- all four tracks returned **FAIL**;
- raw cosine similarities were extremely small, mostly around `0.003–0.009`;
- rankings were suspiciously similar across radically different tracks;
- `stick-to-you`, `Tachy Psychia`, `THICK`, and `Tình Bolero Cho Trân` all repeatedly favored combinations such as `Grime`, `Dancehall Pop`, `Drift Phonk`, and Vietnamese family/tradition labels in ways that were not musically coherent.

This is not treated as evidence that the original LAION music checkpoint itself is poor.

## Upstream evidence

Two upstream problems make the Hugging Face conversion unsuitable as a trustworthy SonicTrace quality gate:

1. The model's own Hugging Face discussion shows the official zero-shot pipeline returning almost exactly `0.5 / 0.5` for clearly different candidate classes, including `calm piano music` vs `heavy metal` and the README's `dog` vs `vacuum cleaner` example:
   `https://huggingface.co/laion/larger_clap_music/discussions/2`

2. Hugging Face Transformers issue `#26362` and LAION CLAP issue `#126` document a major accuracy drop after converting the larger `HTSAT-base` music CLAP checkpoints to Hugging Face format. In the reported ESC50 evaluation, a native `music_audioset` checkpoint around `R@1 0.9175` fell to roughly `R@1 0.47` after conversion:
   `https://github.com/huggingface/transformers/issues/26362`
   `https://github.com/LAION-AI/CLAP/issues/126`

## Decision

**Do not tune taxonomy prompts, benchmark thresholds, or SonicTrace rescue rules to improve Candidate D.**

Candidate D is preserved as an upstream-conversion failure reference only. It is not ranked below Microsoft CLAP on model quality because the observed result cannot cleanly separate checkpoint quality from conversion/interface failure.

## Next gate

Test the **native LAION CLAP music checkpoint** through LAION's own `laion_clap` implementation:

- checkpoint: `music_audioset_epoch_15_esc_90.14.pt`
- audio encoder: `HTSAT-base`
- non-fusion native path
- official LAION checkpoint source: `lukewys/laion_clap`
- exact checkpoint SHA-256: `fae3e9c087f2909c28a09dc31c8dfcdacbc42ba44c70e972b58c1bd1caf6dedd`

The LAION repository explicitly recommends that checkpoint for music and reports stronger native zero-shot genre performance than the broken converted path. Candidate E therefore asks one narrow question: **does the original native music checkpoint provide a commercially usable ear that approaches MuQ quality without the Hugging Face conversion defect?**
