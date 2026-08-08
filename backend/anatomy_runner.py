from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import librosa
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

TARGET_SR = 22050
HOP = 512
BEATS_PER_UNIT = 4
MIN_SECTION_SECONDS = 7.0
MAX_SECTIONS = 12

PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88], dtype=float)
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17], dtype=float)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(np.asarray(value).reshape(-1)[0])
    except Exception:
        return default


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom <= 1e-12:
        return 0.0
    return float(np.dot(a, b) / denom)


def robust_scale(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return values
    lo, hi = np.percentile(values, [10, 90])
    if hi - lo < 1e-9:
        return np.full_like(values, 0.5)
    return np.clip((values - lo) / (hi - lo), 0.0, 1.0)


def zscore_columns(matrix: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=float)
    mean = np.nanmean(matrix, axis=0, keepdims=True)
    std = np.nanstd(matrix, axis=0, keepdims=True)
    std[std < 1e-8] = 1.0
    return np.nan_to_num((matrix - mean) / std)


def key_from_chroma(chroma: np.ndarray) -> dict[str, Any]:
    c = np.asarray(chroma, dtype=float)
    if c.ndim > 1:
        c = np.mean(c, axis=1)
    if c.size != 12 or np.sum(c) <= 1e-9:
        return {"key": "Unknown", "tonic": None, "mode": None, "confidence": 0.0}

    c = c / (np.linalg.norm(c) + 1e-12)
    scores: list[tuple[float, int, str]] = []
    for root in range(12):
        maj = np.roll(MAJOR_PROFILE, root)
        minp = np.roll(MINOR_PROFILE, root)
        scores.append((cosine_similarity(c, maj), root, "major"))
        scores.append((cosine_similarity(c, minp), root, "minor"))
    scores.sort(reverse=True, key=lambda item: item[0])
    best, second = scores[0], scores[1]
    confidence = clamp((best[0] - second[0]) * 4.0 + (best[0] - 0.65) * 0.5, 0.0, 1.0)
    tonic = PITCH_NAMES[best[1]]
    return {
        "key": f"{tonic} {best[2]}",
        "tonic": tonic,
        "mode": best[2],
        "confidence": round(confidence, 3),
        "score": round(best[0], 3),
    }


def chord_templates() -> tuple[list[str], np.ndarray]:
    labels: list[str] = []
    templates: list[np.ndarray] = []
    for root in range(12):
        major = np.zeros(12, dtype=float)
        major[root] = 1.0
        major[(root + 4) % 12] = 0.82
        major[(root + 7) % 12] = 0.72
        labels.append(PITCH_NAMES[root])
        templates.append(major)

        minor = np.zeros(12, dtype=float)
        minor[root] = 1.0
        minor[(root + 3) % 12] = 0.82
        minor[(root + 7) % 12] = 0.72
        labels.append(PITCH_NAMES[root] + "m")
        templates.append(minor)
    t = np.vstack(templates)
    t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-12
    return labels, t


CHORD_LABELS, CHORD_TEMPLATES = chord_templates()


def chord_for_chroma(chroma: np.ndarray, energy: float) -> tuple[str, float]:
    c = np.asarray(chroma, dtype=float).reshape(-1)
    if c.size != 12 or np.sum(c) < 1e-6 or energy < 1e-4:
        return "N", 0.0
    c = c / (np.linalg.norm(c) + 1e-12)
    scores = CHORD_TEMPLATES @ c
    order = np.argsort(scores)[::-1]
    best_idx, second_idx = int(order[0]), int(order[1])
    best, second = float(scores[best_idx]), float(scores[second_idx])
    confidence = clamp((best - second) * 2.8 + (best - 0.55) * 1.2, 0.0, 1.0)
    if best < 0.57:
        return "N", round(confidence * 0.5, 3)
    return CHORD_LABELS[best_idx], round(confidence, 3)


def compress_chords(chords: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not chords:
        return []
    merged: list[dict[str, Any]] = []
    for chord in chords:
        if merged and merged[-1]["label"] == chord["label"]:
            old_dur = merged[-1]["end"] - merged[-1]["start"]
            new_dur = chord["end"] - chord["start"]
            total = max(old_dur + new_dur, 1e-6)
            merged[-1]["confidence"] = round(
                (merged[-1]["confidence"] * old_dur + chord["confidence"] * new_dur) / total, 3
            )
            merged[-1]["end"] = chord["end"]
        else:
            merged.append(dict(chord))

    changed = True
    while changed and len(merged) >= 3:
        changed = False
        output: list[dict[str, Any]] = []
        i = 0
        while i < len(merged):
            if 0 < i < len(merged) - 1:
                prev_, cur, nxt = merged[i - 1], merged[i], merged[i + 1]
                if (
                    prev_["label"] == nxt["label"]
                    and cur["label"] != prev_["label"]
                    and cur["end"] - cur["start"] < 1.6
                ):
                    if output:
                        output[-1]["end"] = nxt["end"]
                        output[-1]["confidence"] = round(max(output[-1]["confidence"], nxt["confidence"]), 3)
                    i += 2
                    changed = True
                    continue
            output.append(dict(merged[i]))
            i += 1
        merged = output
    return merged


def build_units(beat_frames: np.ndarray, last_frame: int) -> np.ndarray:
    beats = np.asarray(beat_frames, dtype=int)
    beats = beats[(beats > 0) & (beats < last_frame)]
    anchors = [0]
    if beats.size:
        anchors.extend(int(v) for v in beats[::BEATS_PER_UNIT])
    anchors.append(last_frame)
    anchors = sorted(set(anchors))
    cleaned = [anchors[0]]
    for value in anchors[1:]:
        if value - cleaned[-1] >= 2:
            cleaned.append(value)
    if cleaned[-1] != last_frame:
        cleaned.append(last_frame)
    if len(cleaned) < 3:
        cleaned = list(np.linspace(0, last_frame, num=max(3, int(last_frame / 96) + 2), dtype=int))
        cleaned[-1] = last_frame
    return np.asarray(cleaned, dtype=int)


def aggregate_frames(feature: np.ndarray, start: int, end: int) -> np.ndarray:
    start = max(0, min(start, feature.shape[-1] - 1))
    end = max(start + 1, min(end, feature.shape[-1]))
    return np.mean(feature[..., start:end], axis=-1)


def section_boundaries(unit_features: np.ndarray, unit_times: np.ndarray, duration: float) -> list[int]:
    n_units = len(unit_features)
    if n_units <= 4:
        return [0, n_units]

    target = int(clamp(round(duration / 22.0), 4, min(MAX_SECTIONS, max(4, n_units // 2))))
    features = zscore_columns(unit_features)

    novelty = np.zeros(n_units, dtype=float)
    for i in range(1, n_units):
        novelty[i] = 1.0 - cosine_similarity(features[i - 1], features[i])
    if n_units > 4:
        novelty = gaussian_filter1d(novelty, sigma=0.85)

    candidates: set[int] = set()
    try:
        ag = librosa.segment.agglomerative(features.T, k=target)
        for idx in np.asarray(ag, dtype=int).tolist():
            if 0 < idx < n_units:
                left = max(1, idx - 1)
                right = min(n_units - 1, idx + 1)
                refined = left + int(np.argmax(novelty[left : right + 1]))
                candidates.add(refined)
    except Exception:
        pass

    min_distance_units = max(1, int(round(MIN_SECTION_SECONDS / max(duration / n_units, 0.1))))
    peaks, _ = find_peaks(
        novelty,
        distance=min_distance_units,
        prominence=max(0.03, float(np.std(novelty) * 0.35)),
    )
    ranked = sorted(peaks.tolist(), key=lambda i: float(novelty[i]), reverse=True)
    for idx in ranked:
        candidates.add(int(idx))

    ranked_all = sorted(candidates, key=lambda i: float(novelty[i]), reverse=True)
    selected = [0, n_units]
    for idx in ranked_all:
        sec = unit_times[min(idx, len(unit_times) - 1)]
        if all(abs(sec - unit_times[min(existing, len(unit_times) - 1)]) >= MIN_SECTION_SECONDS for existing in selected):
            selected.append(idx)
        if len(selected) >= target + 1:
            break

    while len(selected) < min(target + 1, n_units + 1):
        gaps = sorted(zip(selected[:-1], selected[1:]), key=lambda ab: ab[1] - ab[0], reverse=True)
        if not gaps:
            break
        a, b = gaps[0]
        if b - a <= 1:
            break
        selected.append((a + b) // 2)
        selected = sorted(set(selected))

    return sorted(set(int(v) for v in selected))


def build_repetition_groups(sections: list[dict[str, Any]]) -> None:
    n = len(sections)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for j in range(i + 1, n):
            di = sections[i]["duration"]
            dj = sections[j]["duration"]
            ratio = min(di, dj) / max(di, dj, 1e-6)
            sim = cosine_similarity(np.asarray(sections[i]["embedding"]), np.asarray(sections[j]["embedding"]))
            if sim >= 0.80 and ratio >= 0.58:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    repeated = [indices for indices in groups.values() if len(indices) >= 2]
    repeated.sort(key=lambda idxs: (-len(idxs), idxs[0]))
    for group_id, indices in enumerate(repeated, start=1):
        sims = []
        for a in indices:
            for b in indices:
                if a < b:
                    sims.append(cosine_similarity(np.asarray(sections[a]["embedding"]), np.asarray(sections[b]["embedding"])))
        strength = float(np.mean(sims)) if sims else 0.0
        for idx in indices:
            sections[idx]["repeat_group"] = group_id
            sections[idx]["repeat_count"] = len(indices)
            sections[idx]["repeat_strength"] = round(strength, 3)


def semantic_labels(sections: list[dict[str, Any]], duration: float) -> None:
    if not sections:
        return
    energies = np.array([s["energy"] for s in sections], dtype=float)
    median_energy = float(np.median(energies))

    for section in sections:
        section["type"] = None
        section["label_confidence"] = 0.35

    first = sections[0]
    if first["duration"] <= 30 and first["energy"] <= median_energy + 12:
        first["type"] = "Intro"
        first["label_confidence"] = 0.78

    last = sections[-1]
    if len(sections) > 1 and last["duration"] <= 32 and last["energy"] <= median_energy + 12:
        last["type"] = "Outro"
        last["label_confidence"] = 0.76

    groups: dict[int, list[int]] = {}
    for idx, section in enumerate(sections):
        if section.get("repeat_group"):
            groups.setdefault(int(section["repeat_group"]), []).append(idx)

    if groups:
        scored = []
        for gid, idxs in groups.items():
            mean_energy = float(np.mean([sections[i]["energy"] for i in idxs]))
            mean_rhythm = float(np.mean([sections[i]["rhythmic"] for i in idxs]))
            mean_duration = float(np.mean([sections[i]["duration"] for i in idxs]))
            repeat_strength = float(np.mean([sections[i].get("repeat_strength", 0) for i in idxs]))
            suitability = 1.0 - min(abs(mean_duration - 20.0) / 25.0, 1.0)
            score = len(idxs) * 0.28 + mean_energy / 100 * 0.28 + mean_rhythm / 100 * 0.12 + repeat_strength * 0.22 + suitability * 0.10
            scored.append((score, gid, idxs))
        scored.sort(reverse=True)
        for idx in scored[0][2]:
            if sections[idx]["type"] is None:
                sections[idx]["type"] = "Chorus"
                sections[idx]["label_confidence"] = round(clamp(0.62 + sections[idx].get("repeat_strength", 0) * 0.28, 0, 0.95), 3)

        for _, _gid, idxs in scored[1:]:
            for idx in idxs:
                if sections[idx]["type"] is None:
                    sections[idx]["type"] = "Verse"
                    sections[idx]["label_confidence"] = round(clamp(0.56 + sections[idx].get("repeat_strength", 0) * 0.25, 0, 0.9), 3)

    for idx in range(len(sections) - 1):
        cur, nxt = sections[idx], sections[idx + 1]
        if cur["type"] is None and nxt["type"] == "Chorus" and 5.0 <= cur["duration"] <= 20.0:
            rise = nxt["energy"] - cur["energy"]
            cur["type"] = "Pre-Chorus"
            cur["label_confidence"] = round(clamp(0.58 + max(rise, 0) / 120, 0.55, 0.82), 3)

    for section in sections:
        if section["type"] is None and 0.10 * duration < section["start"] < 0.92 * duration:
            if section["energy"] >= 78 and section["rhythmic"] >= 70:
                section["type"] = "Drop"
                section["label_confidence"] = 0.68

    chorus_indices = [i for i, section in enumerate(sections) if section["type"] == "Chorus"]
    if chorus_indices:
        for idx, section in enumerate(sections):
            if section["type"] is None and idx > chorus_indices[0] and section["start"] > duration * 0.45 and 7 <= section["duration"] <= 38:
                if not section.get("repeat_group"):
                    section["type"] = "Bridge"
                    section["label_confidence"] = 0.61
                    break

    section_letter = 0
    for section in sections:
        if section["type"] is None:
            if section.get("repeat_group"):
                section["type"] = "Verse"
                section["label_confidence"] = 0.54
            else:
                letter = chr(ord("A") + min(section_letter, 25))
                section["type"] = f"Section {letter}"
                section["label_confidence"] = 0.38
                section_letter += 1

    counts: dict[str, int] = {}
    for section in sections:
        base = section["type"]
        counts[base] = counts.get(base, 0) + 1
        if base in {"Verse", "Chorus", "Pre-Chorus", "Drop"}:
            section["label"] = f"{base} {counts[base]}"
        else:
            section["label"] = base


def analyze(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    y, sr = librosa.load(path, sr=TARGET_SR, mono=True)
    if y.size < sr * 2:
        raise RuntimeError("Audio too short for structural analysis.")
    duration = float(librosa.get_duration(y=y, sr=sr))

    peak = float(np.max(np.abs(y))) or 1.0
    y = np.asarray(y / max(peak, 1e-6), dtype=np.float32)
    harmonic, _percussive = librosa.effects.hpss(y, margin=(1.0, 2.0))

    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP)
    tempo_raw, beat_frames = librosa.beat.beat_track(onset_envelope=onset, sr=sr, hop_length=HOP, units="frames")
    tempo = safe_float(tempo_raw)

    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=HOP)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=HOP)[0]
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=HOP)
    chroma = librosa.feature.chroma_cqt(y=harmonic, sr=sr, hop_length=HOP, bins_per_octave=36)

    n_frames = min(len(rms), len(centroid), len(onset), mfcc.shape[1], chroma.shape[1])
    if n_frames < 16:
        raise RuntimeError("Not enough analysis frames.")
    rms = rms[:n_frames]
    centroid = centroid[:n_frames]
    onset = onset[:n_frames]
    mfcc = mfcc[:, :n_frames]
    chroma = chroma[:, :n_frames]

    unit_bounds = build_units(np.asarray(beat_frames, dtype=int), n_frames - 1)
    if unit_bounds[-1] < n_frames - 1:
        unit_bounds[-1] = n_frames - 1

    unit_rows = []
    unit_meta = []
    for idx in range(len(unit_bounds) - 1):
        a, b = int(unit_bounds[idx]), int(unit_bounds[idx + 1])
        if b <= a:
            continue
        ch = aggregate_frames(chroma, a, b)
        mf = aggregate_frames(mfcc, a, b)
        energy = float(np.mean(rms[a:b]))
        onset_mean = float(np.mean(onset[a:b]))
        centroid_mean = float(np.mean(centroid[a:b]))
        row = np.concatenate([ch, mf, [math.log10(energy + 1e-8), math.log10(onset_mean + 1e-8), centroid_mean / sr]])
        unit_rows.append(row)
        unit_meta.append({"a": a, "b": b, "rms": energy, "onset": onset_mean, "centroid": centroid_mean, "chroma": ch})

    unit_features = np.vstack(unit_rows)
    n_units = len(unit_features)
    unit_start_times = np.array([librosa.frames_to_time(meta["a"], sr=sr, hop_length=HOP) for meta in unit_meta], dtype=float)
    unit_end_times = np.array([librosa.frames_to_time(meta["b"], sr=sr, hop_length=HOP) for meta in unit_meta], dtype=float)
    unit_times_for_boundaries = np.append(unit_start_times, unit_end_times[-1])

    boundaries = section_boundaries(unit_features, unit_times_for_boundaries, duration)
    scaled_rms = robust_scale(np.array([meta["rms"] for meta in unit_meta]))
    scaled_onset = robust_scale(np.array([meta["onset"] for meta in unit_meta]))
    scaled_centroid = robust_scale(np.array([meta["centroid"] for meta in unit_meta]))
    normalized_units = zscore_columns(unit_features)

    sections: list[dict[str, Any]] = []
    for sec_idx in range(len(boundaries) - 1):
        ua, ub = boundaries[sec_idx], boundaries[sec_idx + 1]
        if ub <= ua:
            continue
        frame_a = unit_meta[ua]["a"]
        frame_b = unit_meta[min(ub - 1, len(unit_meta) - 1)]["b"]
        start_sec = float(librosa.frames_to_time(frame_a, sr=sr, hop_length=HOP))
        end_sec = min(duration, float(librosa.frames_to_time(frame_b, sr=sr, hop_length=HOP)))
        sec_chroma = np.mean(chroma[:, frame_a:frame_b], axis=1)
        key_info = key_from_chroma(sec_chroma)
        embedding = np.mean(normalized_units[ua:ub], axis=0)
        energy = float(np.mean(scaled_rms[ua:ub]) * 100)
        rhythmic = float(np.mean(scaled_onset[ua:ub]) * 100)
        brightness = float(np.mean(scaled_centroid[ua:ub]) * 100)
        sections.append(
            {
                "index": len(sections),
                "start": round(start_sec, 3),
                "end": round(end_sec, 3),
                "duration": round(max(0.0, end_sec - start_sec), 3),
                "energy": round(energy, 1),
                "rhythmic": round(rhythmic, 1),
                "brightness": round(brightness, 1),
                "key": key_info,
                "repeat_group": None,
                "repeat_count": 1,
                "repeat_strength": 0.0,
                "embedding": embedding.tolist(),
                "_unit_start": ua,
                "_unit_end": ub,
            }
        )

    build_repetition_groups(sections)
    semantic_labels(sections, duration)

    similarity = []
    for a in sections:
        row = []
        for b in sections:
            row.append(round(clamp((cosine_similarity(np.asarray(a["embedding"]), np.asarray(b["embedding"])) + 1) / 2, 0, 1), 3))
        similarity.append(row)

    global_key = key_from_chroma(np.mean(chroma, axis=1))

    chords: list[dict[str, Any]] = []
    for i, meta in enumerate(unit_meta):
        label, conf = chord_for_chroma(np.asarray(meta["chroma"], dtype=float), meta["rms"])
        chords.append(
            {
                "start": round(float(unit_start_times[i]), 3),
                "end": round(min(duration, float(unit_end_times[i])), 3),
                "label": label,
                "confidence": conf,
            }
        )
    chords = compress_chords(chords)

    harmonic_changes = []
    for idx in range(1, len(sections)):
        prev_, cur = sections[idx - 1], sections[idx]
        prev_key, cur_key = prev_["key"], cur["key"]
        if cur_key["key"] != prev_key["key"]:
            harmonic_changes.append(
                {
                    "time": cur["start"],
                    "from": prev_key["key"],
                    "to": cur_key["key"],
                    "confidence": round(max(prev_key["confidence"], cur_key["confidence"]), 3),
                }
            )

    recurrence = np.zeros(n_units, dtype=float)
    for i in range(n_units):
        best = 0.0
        for j in range(n_units):
            if abs(i - j) < 3:
                continue
            best = max(best, cosine_similarity(normalized_units[i], normalized_units[j]))
        recurrence[i] = clamp((best + 1) / 2, 0, 1)

    harmonic_stability = np.array([float(np.max(meta["chroma"]) / (np.sum(meta["chroma"]) + 1e-8)) for meta in unit_meta])
    harmonic_stability = robust_scale(harmonic_stability)
    hook_score = 0.42 * recurrence + 0.28 * scaled_rms + 0.18 * scaled_onset + 0.12 * harmonic_stability

    hooks = []
    for idx in np.argsort(hook_score)[::-1]:
        idx = int(idx)
        if any(abs(idx - hook["_unit"]) < 2 for hook in hooks):
            continue
        section_index = next((section["index"] for section in sections if section["_unit_start"] <= idx < section["_unit_end"]), None)
        hooks.append(
            {
                "_unit": idx,
                "start": round(float(unit_start_times[idx]), 3),
                "end": round(min(duration, float(unit_end_times[idx])), 3),
                "score": round(float(hook_score[idx] * 100), 1),
                "section_index": section_index,
                "reason": "repetition + energy + rhythmic salience + harmonic focus",
            }
        )
        if len(hooks) >= 3:
            break

    impact = 0.48 * scaled_rms + 0.34 * scaled_onset + 0.18 * scaled_centroid
    if len(impact) >= 3:
        impact = gaussian_filter1d(impact, sigma=0.8)
    climax_unit = int(np.argmax(impact))
    climax_time = float((unit_start_times[climax_unit] + unit_end_times[climax_unit]) / 2)
    climax_section = next((section["index"] for section in sections if section["start"] <= climax_time <= section["end"]), None)

    for section in sections:
        section.pop("_unit_start", None)
        section.pop("_unit_end", None)
        section.pop("embedding", None)

    for hook in hooks:
        hook.pop("_unit", None)

    elapsed = time.perf_counter() - started
    return {
        "engine": {
            "name": "LMNotebook Song Anatomy",
            "version": "2.3",
            "algorithm": "beat-synchronous timbre/chroma segmentation + recurrence + tonal template matching",
            "sample_rate_hz": sr,
            "hop_length": HOP,
            "elapsed_seconds": round(elapsed, 2),
            "label_mode": "heuristic-structural",
            "label_note": "Section names are inferred from repetition, energy and position; boundaries/chords are signal-derived.",
        },
        "duration_seconds": round(duration, 3),
        "tempo_bpm": round(tempo, 2),
        "global_key": global_key,
        "sections": sections,
        "section_similarity": similarity,
        "hooks": hooks,
        "climax": {
            "time": round(climax_time, 3),
            "score": round(float(impact[climax_unit] * 100), 1),
            "section_index": climax_section,
        },
        "chords": chords,
        "harmonic_changes": harmonic_changes,
        "summary": {
            "section_count": len(sections),
            "repeat_group_count": len({section["repeat_group"] for section in sections if section.get("repeat_group")}),
            "hook_candidate_count": len(hooks),
            "chord_change_count": max(0, len(chords) - 1),
            "harmonic_change_count": len(harmonic_changes),
        },
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: anatomy_runner.py <audio.wav>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        result = analyze(path)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except Exception as exc:
        print(f"Song Anatomy failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
