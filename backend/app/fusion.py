from __future__ import annotations

import math
from typing import Any

STEM_NAMES = ('vocals', 'drums', 'bass', 'other')
FUSION_VERSION = '2.4'


def fuse_anatomy_stems(anatomy: dict[str, Any], separation: dict[str, Any]) -> dict[str, Any]:
    source_sections = list(anatomy.get('sections') or [])
    if not source_sections:
        raise RuntimeError('Song Anatomy returned no sections.')
    stems = {str(item.get('name')): item for item in separation.get('stems', []) if item.get('name')}
    if not stems:
        raise RuntimeError('Demucs returned no stems to fuse.')

    sections: list[dict[str, Any]] = []
    raw_db_by_stem: dict[str, list[float]] = {name: [] for name in STEM_NAMES}

    for source in source_sections:
        start = float(source.get('start') or 0.0)
        end = float(source.get('end') or start)
        powers: dict[str, float] = {}
        db_values: dict[str, float] = {}
        for name in STEM_NAMES:
            db = _section_db(stems.get(name), start, end)
            power = _db_to_power(db)
            db_values[name] = db
            powers[name] = power
            raw_db_by_stem[name].append(db)

        total_power = sum(powers.values()) or 1.0
        sections.append(
            {
                **source,
                'original_label': source.get('label') or source.get('type'),
                'stem_activity': {
                    name: {
                        'dbfs': round(db_values[name], 2),
                        'share_percent': round(powers[name] / total_power * 100.0, 1),
                        'score': 0.0,
                    }
                    for name in STEM_NAMES
                },
            }
        )

    for name in STEM_NAMES:
        db_values = raw_db_by_stem[name]
        lo = _percentile(db_values, 0.15)
        hi = _percentile(db_values, 0.90)
        if hi - lo < 2.0:
            lo = min(db_values or [-60.0])
            hi = max(db_values or [-20.0])
        for idx, db in enumerate(db_values):
            sections[idx]['stem_activity'][name]['score'] = round(_scale(db, lo, hi), 1)

    fused_similarity = _fused_similarity(anatomy.get('section_similarity') or [], sections)
    _apply_repeat_groups(sections, fused_similarity)

    anatomy_hooks = list(anatomy.get('hooks') or [])
    anatomy_climax = anatomy.get('climax') or {}
    duration = float(anatomy.get('duration_seconds') or max(float(s.get('end') or 0.0) for s in sections) or 1.0)

    for idx, section in enumerate(sections):
        repeat_strength = float(section.get('fusion_repeat_strength') or section.get('repeat_strength') or 0.0)
        hook_prior = max(
            [float(h.get('score') or 0.0) / 100.0 for h in anatomy_hooks if h.get('section_index') == idx] or [0.0]
        )
        v = _stem_score(section, 'vocals') / 100.0
        d = _stem_score(section, 'drums') / 100.0
        b = _stem_score(section, 'bass') / 100.0
        energy = float(section.get('energy') or 0.0) / 100.0
        rhythmic = float(section.get('rhythmic') or 0.0) / 100.0
        recurrence = max(repeat_strength, _best_off_diagonal(fused_similarity, idx))
        section['fusion_hook_score'] = round(
            _clamp(0.30 * recurrence + 0.19 * energy + 0.17 * v + 0.14 * d + 0.08 * b + 0.12 * hook_prior, 0.0, 1.0)
            * 100.0,
            1,
        )
        section['fusion_climax_score'] = round(
            _clamp(0.30 * energy + 0.24 * d + 0.17 * b + 0.14 * v + 0.15 * rhythmic, 0.0, 1.0)
            * 100.0,
            1,
        )

    _assign_group_priors(sections)
    label_scores = [_base_label_scores(section, idx, sections, fused_similarity, duration) for idx, section in enumerate(sections)]

    for idx in range(len(sections) - 1):
        current = sections[idx]
        nxt = sections[idx + 1]
        next_chorus = label_scores[idx + 1].get('Chorus', 0.0)
        rise = _clamp((float(nxt.get('energy') or 0.0) - float(current.get('energy') or 0.0)) / 45.0, -1.0, 1.0)
        duration_fit = 1.0 - min(abs(float(current.get('duration') or 0.0) - 12.0) / 18.0, 1.0)
        vocal = _stem_score(current, 'vocals') / 100.0
        pre = 0.48 * next_chorus + 0.16 * max(rise, 0.0) + 0.14 * duration_fit + 0.14 * vocal + 0.08 * (float(current.get('rhythmic') or 0.0) / 100.0)
        if next_chorus >= 0.78:
            pre += 0.08
        if float(current.get('duration') or 0.0) > 22.0:
            pre *= 0.58
        if current.get('fusion_chorus_group_prior', 0.0) >= 0.70:
            pre *= 0.55
        label_scores[idx]['Pre-Chorus'] = _clamp(pre, 0.0, 1.0)

    label_counts: dict[str, int] = {}
    for idx, section in enumerate(sections):
        scores = label_scores[idx]
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        best_type, best_score = ordered[0]
        second_score = ordered[1][1] if len(ordered) > 1 else 0.0
        margin = best_score - second_score
        confidence = _clamp(0.34 + best_score * 0.42 + margin * 0.55, 0.38, 0.96)

        if best_score < 0.43:
            best_type = f"Section {chr(ord('A') + min(idx, 25))}"
            confidence = min(confidence, 0.48)

        label_counts[best_type] = label_counts.get(best_type, 0) + 1
        numbered = best_type in {'Verse', 'Chorus', 'Pre-Chorus', 'Drop'}
        label = f'{best_type} {label_counts[best_type]}' if numbered else best_type

        section['fusion_type'] = best_type
        section['fusion_label'] = label
        section['fusion_confidence'] = round(confidence, 3)
        section['fusion_score'] = round(best_score, 3)
        section['fusion_alternatives'] = [
            {'type': name, 'score': round(score, 3)}
            for name, score in ordered[1:3]
        ]
        section['evidence'] = _evidence(section, idx, sections, fused_similarity)

    climax_idx = max(range(len(sections)), key=lambda i: float(sections[i].get('fusion_climax_score') or 0.0))
    original_climax_idx = anatomy_climax.get('section_index')
    if original_climax_idx is not None:
        original_climax_idx = int(original_climax_idx)
        if 0 <= original_climax_idx < len(sections):
            original_score = float(sections[original_climax_idx].get('fusion_climax_score') or 0.0)
            best_score = float(sections[climax_idx].get('fusion_climax_score') or 0.0)
            if original_score >= best_score - 7.0:
                climax_idx = original_climax_idx

    climax_section = sections[climax_idx]
    climax_time = (
        float(anatomy_climax.get('time'))
        if anatomy_climax.get('section_index') == climax_idx and anatomy_climax.get('time') is not None
        else (float(climax_section.get('start') or 0.0) + float(climax_section.get('end') or 0.0)) / 2.0
    )

    hook_indices = sorted(
        range(len(sections)),
        key=lambda i: float(sections[i].get('fusion_hook_score') or 0.0),
        reverse=True,
    )
    fused_hooks: list[dict[str, Any]] = []
    for idx in hook_indices:
        if any(abs(float(sections[idx].get('start') or 0.0) - float(item['start'])) < 8.0 for item in fused_hooks):
            continue
        fused_hooks.append(
            {
                'section_index': idx,
                'label': sections[idx].get('fusion_label'),
                'start': sections[idx].get('start'),
                'end': sections[idx].get('end'),
                'score': sections[idx].get('fusion_hook_score'),
                'evidence': sections[idx].get('evidence', [])[:4],
            }
        )
        if len(fused_hooks) >= 3:
            break

    repeat_groups = sorted({
        int(section['fusion_repeat_group'])
        for section in sections
        if section.get('fusion_repeat_group')
    })

    return {
        'engine': {
            'name': 'LMNotebook Song Understanding Fusion',
            'version': FUSION_VERSION,
            'mode': 'V2-C x V2-D',
            'algorithm': 'structural recurrence + temporal Demucs stem activity + harmony + energy/rhythm evidence scoring',
            'label_note': 'Section labels remain inferred; confidence and evidence are exposed. Boundaries come from V2-C signal analysis.',
        },
        'sections': sections,
        'section_similarity': fused_similarity,
        'hooks': fused_hooks,
        'climax': {
            'section_index': climax_idx,
            'time': round(climax_time, 3),
            'score': climax_section.get('fusion_climax_score'),
            'label': climax_section.get('fusion_label'),
        },
        'summary': {
            'section_count': len(sections),
            'fusion_repeat_group_count': len(repeat_groups),
            'hook_candidate_count': len(fused_hooks),
            'labels': label_counts,
        },
        'provenance': {
            'boundaries': 'V2-C signal-derived structural segmentation',
            'harmony': 'V2-C chroma/key/chord analysis',
            'stem_activity': 'V2-D Demucs temporal RMS measurements',
            'labels': 'V2-CD evidence fusion inference',
        },
    }


def _section_db(stem: dict[str, Any] | None, start: float, end: float) -> float:
    if not stem:
        return -120.0
    activity = stem.get('activity') or {}
    values = list(activity.get('rms_dbfs') or [])
    window = float(activity.get('window_seconds') or 1.0)
    if not values or window <= 0:
        mean_db = stem.get('levels', {}).get('mean_volume_db')
        try:
            return float(mean_db)
        except (TypeError, ValueError):
            return -120.0

    first = max(0, int(math.floor(start / window)))
    last = min(len(values), max(first + 1, int(math.ceil(end / window))))
    selected = values[first:last]
    if not selected:
        return -120.0
    powers = [_db_to_power(value) for value in selected]
    mean_power = sum(powers) / max(1, len(powers))
    return 10.0 * math.log10(max(mean_power, 1e-12))


def _fused_similarity(base_matrix: list[list[Any]], sections: list[dict[str, Any]]) -> list[list[float]]:
    n = len(sections)
    matrix: list[list[float]] = []
    for i in range(n):
        row: list[float] = []
        for j in range(n):
            base = 1.0 if i == j else _matrix_value(base_matrix, i, j, 0.0)
            stem_similarity = _cosine(_section_vector(sections[i]), _section_vector(sections[j]))
            row.append(round(_clamp(0.70 * base + 0.30 * stem_similarity, 0.0, 1.0), 3))
        matrix.append(row)
    return matrix


def _section_vector(section: dict[str, Any]) -> list[float]:
    return [
        _stem_score(section, 'vocals') / 100.0,
        _stem_score(section, 'drums') / 100.0,
        _stem_score(section, 'bass') / 100.0,
        _stem_score(section, 'other') / 100.0,
        float(section.get('energy') or 0.0) / 100.0,
        float(section.get('rhythmic') or 0.0) / 100.0,
        float(section.get('brightness') or 0.0) / 100.0,
    ]


def _apply_repeat_groups(sections: list[dict[str, Any]], matrix: list[list[float]]) -> None:
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
            di = float(sections[i].get('duration') or 0.0)
            dj = float(sections[j].get('duration') or 0.0)
            ratio = min(di, dj) / max(di, dj, 1e-6)
            if matrix[i][j] >= 0.77 and ratio >= 0.55:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for idx in range(n):
        groups.setdefault(find(idx), []).append(idx)
    repeated = [items for items in groups.values() if len(items) >= 2]
    repeated.sort(key=lambda items: (-len(items), items[0]))

    for gid, indices in enumerate(repeated, start=1):
        sims = [matrix[a][b] for a in indices for b in indices if a < b]
        strength = sum(sims) / max(1, len(sims))
        for idx in indices:
            sections[idx]['fusion_repeat_group'] = gid
            sections[idx]['fusion_repeat_count'] = len(indices)
            sections[idx]['fusion_repeat_strength'] = round(strength, 3)


def _assign_group_priors(sections: list[dict[str, Any]]) -> None:
    groups: dict[int, list[dict[str, Any]]] = {}
    for section in sections:
        gid = section.get('fusion_repeat_group')
        if gid:
            groups.setdefault(int(gid), []).append(section)
    if not groups:
        return

    scored: list[tuple[float, int]] = []
    for gid, items in groups.items():
        count = max(1, len(items))
        energy = sum(float(item.get('energy') or 0.0) for item in items) / count / 100.0
        vocals = sum(_stem_score(item, 'vocals') for item in items) / count / 100.0
        drums = sum(_stem_score(item, 'drums') for item in items) / count / 100.0
        hooks = sum(float(item.get('fusion_hook_score') or 0.0) for item in items) / count / 100.0
        strength = sum(float(item.get('fusion_repeat_strength') or 0.0) for item in items) / count
        scored.append((0.26 * energy + 0.22 * vocals + 0.20 * drums + 0.22 * hooks + 0.10 * strength, gid))

    scored.sort(reverse=True)
    best_score = scored[0][0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0
    for score, gid in scored:
        if gid == scored[0][1]:
            prior = _clamp(0.72 + max(best_score - second_score, 0.0) * 0.8, 0.72, 0.96)
        else:
            prior = _clamp(0.12 + max(score - second_score, 0.0) * 0.2, 0.10, 0.28)
        for section in groups[gid]:
            section['fusion_chorus_group_prior'] = round(prior, 3)


def _base_label_scores(section: dict[str, Any], idx: int, sections: list[dict[str, Any]], matrix: list[list[float]], duration: float) -> dict[str, float]:
    start = float(section.get('start') or 0.0)
    sec_duration = float(section.get('duration') or 0.0)
    position = start / max(duration, 1e-6)
    energy = float(section.get('energy') or 0.0) / 100.0
    rhythmic = float(section.get('rhythmic') or 0.0) / 100.0
    v = _stem_score(section, 'vocals') / 100.0
    d = _stem_score(section, 'drums') / 100.0
    b = _stem_score(section, 'bass') / 100.0
    other = _stem_score(section, 'other') / 100.0
    repeat_strength = float(section.get('fusion_repeat_strength') or 0.0)
    repeat_count = int(section.get('fusion_repeat_count') or 1)
    repeat = max(repeat_strength, 0.72 if repeat_count >= 2 else 0.0)
    hook = float(section.get('fusion_hook_score') or 0.0) / 100.0
    novelty = 1.0 - _best_off_diagonal(matrix, idx)
    original_type = str(section.get('type') or '')

    intro = 0.05
    if idx == 0:
        intro = 0.42 + 0.20 * (1.0 - v) + 0.14 * (1.0 - d) + 0.12 * (1.0 - energy) + 0.12 * _duration_fit(sec_duration, 18.0, 25.0)

    outro = 0.05
    if idx == len(sections) - 1:
        outro = 0.40 + 0.18 * (1.0 - v) + 0.15 * (1.0 - d) + 0.14 * (1.0 - energy) + 0.13 * _duration_fit(sec_duration, 18.0, 28.0)

    chorus_prior = float(section.get('fusion_chorus_group_prior') or 0.0)
    chorus = (
        0.25 * chorus_prior + 0.18 * v + 0.14 * d + 0.09 * b + 0.15 * hook + 0.10 * energy + 0.05 * rhythmic + 0.04 * repeat
    )
    if original_type == 'Chorus':
        chorus += 0.05

    verse = (
        0.24 * v + 0.10 * d + 0.07 * b + 0.18 * repeat + 0.14 * (1.0 - hook) + 0.12 * (1.0 - abs(energy - 0.58)) + 0.10 * _duration_fit(sec_duration, 22.0, 28.0) + 0.05 * (1.0 - chorus_prior)
    )
    if original_type == 'Verse':
        verse += 0.05

    drop = 0.27 * d + 0.22 * b + 0.17 * energy + 0.15 * rhythmic + 0.10 * (1.0 - v) + 0.09 * hook
    if original_type == 'Drop':
        drop += 0.05

    late = _clamp((position - 0.42) / 0.45, 0.0, 1.0)
    bridge = 0.28 * novelty + 0.18 * late + 0.15 * (1.0 - repeat) + 0.14 * v + 0.10 * other + 0.08 * energy + 0.07 * _duration_fit(sec_duration, 18.0, 26.0)
    if original_type == 'Bridge':
        bridge += 0.06

    return {
        'Intro': _clamp(intro, 0.0, 1.0),
        'Verse': _clamp(verse, 0.0, 1.0),
        'Chorus': _clamp(chorus, 0.0, 1.0),
        'Pre-Chorus': 0.0,
        'Bridge': _clamp(bridge, 0.0, 1.0),
        'Drop': _clamp(drop, 0.0, 1.0),
        'Outro': _clamp(outro, 0.0, 1.0),
    }


def _evidence(section: dict[str, Any], idx: int, sections: list[dict[str, Any]], matrix: list[list[float]]) -> list[str]:
    evidence: list[str] = []
    v = _stem_score(section, 'vocals')
    d = _stem_score(section, 'drums')
    b = _stem_score(section, 'bass')
    other = _stem_score(section, 'other')
    energy = float(section.get('energy') or 0.0)
    rhythm = float(section.get('rhythmic') or 0.0)
    hook = float(section.get('fusion_hook_score') or 0.0)

    if v >= 68:
        evidence.append(f'vocals élevés {v:.0f}%')
    elif v <= 28:
        evidence.append(f'vocals faibles {v:.0f}%')
    if d >= 68:
        evidence.append(f'drums élevés {d:.0f}%')
    elif d <= 25:
        evidence.append(f'drums faibles {d:.0f}%')
    if b >= 68:
        evidence.append(f'bass élevée {b:.0f}%')
    if other >= 70:
        evidence.append(f'instrumental/other dominant {other:.0f}%')
    if energy >= 72:
        evidence.append(f'énergie mix élevée {energy:.0f}%')
    if rhythm >= 70:
        evidence.append(f'saillance rythmique {rhythm:.0f}%')
    if section.get('fusion_repeat_group'):
        evidence.append(
            f"répétition R{section['fusion_repeat_group']} ×{section.get('fusion_repeat_count', 2)} ({float(section.get('fusion_repeat_strength') or 0.0) * 100:.0f}%)"
        )
    if hook >= 65:
        evidence.append(f'hook fusion {hook:.0f}%')
    if idx < len(sections) - 1:
        rise = float(sections[idx + 1].get('energy') or 0.0) - energy
        if rise >= 15:
            evidence.append(f'montée vers section suivante +{rise:.0f} énergie')
    novelty = 1.0 - _best_off_diagonal(matrix, idx)
    if novelty >= 0.30:
        evidence.append(f'section distincte / nouveauté {novelty * 100:.0f}%')
    return evidence or ['indices structurels mixtes, aucune signature dominante']


def _stem_score(section: dict[str, Any], name: str) -> float:
    try:
        return float(section.get('stem_activity', {}).get(name, {}).get('score') or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _best_off_diagonal(matrix: list[list[float]], idx: int) -> float:
    if idx < 0 or idx >= len(matrix):
        return 0.0
    return max([float(value) for j, value in enumerate(matrix[idx]) if j != idx] or [0.0])


def _matrix_value(matrix: list[list[Any]], i: int, j: int, default: float) -> float:
    try:
        return float(matrix[i][j])
    except (IndexError, TypeError, ValueError):
        return default


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na <= 1e-12 or nb <= 1e-12:
        return 0.0
    return _clamp(dot / (na * nb), 0.0, 1.0)


def _percentile(values: list[float], q: float) -> float:
    clean = sorted(float(v) for v in values if math.isfinite(float(v)))
    if not clean:
        return -60.0
    if len(clean) == 1:
        return clean[0]
    pos = _clamp(q, 0.0, 1.0) * (len(clean) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return clean[lo]
    frac = pos - lo
    return clean[lo] * (1.0 - frac) + clean[hi] * frac


def _scale(value: float, lo: float, hi: float) -> float:
    if hi - lo <= 1e-9:
        return 50.0
    return _clamp((value - lo) / (hi - lo), 0.0, 1.0) * 100.0


def _duration_fit(value: float, center: float, radius: float) -> float:
    return _clamp(1.0 - abs(value - center) / max(radius, 1e-6), 0.0, 1.0)


def _db_to_power(value: Any) -> float:
    try:
        db = float(value)
    except (TypeError, ValueError):
        return 1e-12
    if not math.isfinite(db):
        return 1e-12
    return 10.0 ** (db / 10.0)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
