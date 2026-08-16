from __future__ import annotations

import copy
from typing import Any

DIMENSIONS_VERSION = '3.2'
COHERENCE_VERSION = '3.4.1'

# V3.2 stops forcing unlike concepts to compete for one first place.
# These role mappings are intentionally conservative: only labels whose musical
# role is clear are moved out of the primary-style race.
TRADITION_LABELS = {
    'Nhạc Vàng': 'Nhạc Vàng',
    'Nhạc Trữ Tình': 'Nhạc Trữ Tình',
}

FORM_LABELS = {
    'Vietnamese Pop Ballad': 'Sentimental Ballad',
    'Asian Ballad': 'Sentimental Ballad',
    'Pop Ballad': 'Ballad',
}

# A form can describe more than one family, but a regional form must never leak
# into an unrelated winning family merely because its raw CLAP score is high.
FORM_ALLOWED_FAMILIES: dict[str, set[str]] = {
    'Vietnamese Pop Ballad': {'Vietnamese / Asian'},
    'Asian Ballad': {'Vietnamese / Asian'},
    'Pop Ballad': {'Pop', 'R&B / Soul / Funk', 'Country / Acoustic', 'Vietnamese / Asian'},
}

# Labels left in the style role compete for `dimensions.style.primary`.
# A tiny specificity prior only resolves near-ties; it never manufactures
# evidence that is not already present in the model output.
STYLE_SPECIFICITY_BONUS = {
    'Vietnamese Bolero': 0.035,
    'V-Pop': 0.020,
    'Vietnamese Folk': 0.020,
    'Vietnamese Traditional': 0.020,
    'Latin Bolero': 0.020,
    'G-Funk': 0.015,
    'Boom Bap': 0.015,
    'Drill': 0.015,
    'Phonk': 0.015,
}


def attach_genre_dimensions(genre_analysis: dict[str, Any]) -> dict[str, Any]:
    """Attach additive semantic dimensions to an existing V3 analysis.

    V3.4.1 keeps the V3.2 payload shape but adds a coherence guard: tradition,
    regional form and region are only promoted when they are compatible with
    the resolved family. Incompatible evidence may still remain visible as a
    secondary influence, but it cannot drive the main interpretation/grammar.
    """
    result = copy.deepcopy(genre_analysis or {})
    rows = _evidence_rows(result)
    primary = _effective_primary(result)
    primary_unknown = str(primary.get('label') or '').strip() == 'Unknown / hybrid'

    style_rows = [row for row in rows if _role_for(row) == 'style']
    tradition_rows = [row for row in rows if _role_for(row) == 'tradition']
    form_rows = [row for row in rows if _role_for(row) == 'form']

    primary_style = _pick_primary_style(style_rows, primary)
    broad_family = _family_for(primary_style, primary, result)

    traditions, rejected_traditions = _coherent_context_rows(tradition_rows, broad_family, role='tradition')
    forms, rejected_forms = _coherent_context_rows(form_rows, broad_family, role='form')
    region = _region_for(primary_style, traditions, broad_family)

    tradition_primary = traditions[0] if traditions else None
    form_primary = _normalize_form(forms[0]) if forms else None

    primary_style_label = str((primary_style or {}).get('label') or '').strip()
    excluded = {
        primary_style_label,
        str((tradition_primary or {}).get('label') or '').strip(),
        str((forms[0] if forms else {}).get('label') or '').strip(),
    }
    influences = _pick_influences(rows, excluded, broad_family, primary_style)

    rejected_context = [
        {
            'label': str(row.get('label') or ''),
            'family': row.get('family'),
            'role': role,
            'evidence_percent': round(_score(row) * 100.0, 1),
            'reason': f'incompatible with resolved family {broad_family or "General"}',
        }
        for role, rejected in (('tradition', rejected_traditions), ('form', rejected_forms))
        for row in rejected
    ]

    dimensions = {
        'version': DIMENSIONS_VERSION,
        'coherence': {
            'version': COHERENCE_VERSION,
            'status': 'guarded',
            'resolved_family': broad_family or 'General',
            'rejected_context': rejected_context,
        },
        'family': {
            'label': broad_family or 'General',
            'evidence': _family_evidence(broad_family, result, primary_style),
        },
        'style': {
            'primary': _dimension_row(primary_style, role='style', authority='evidence-only' if primary_unknown else 'resolved'),
            'alternatives': [
                _dimension_row(row, role='style', authority='evidence')
                for row in _alternative_rows(style_rows, primary_style)[:4]
            ],
        },
        'tradition': {
            'primary': _dimension_row(tradition_primary, role='tradition', authority='evidence') if tradition_primary else None,
            'alternatives': [
                _dimension_row(row, role='tradition', authority='evidence')
                for row in traditions[1:4]
            ],
        },
        'form': {
            'primary': form_primary,
            'alternatives': [_normalize_form(row) for row in forms[1:4]],
        },
        'region': {
            'label': region,
            'authority': 'model-inference' if region else 'unresolved',
        },
        'influences': influences,
        'unknown': primary_unknown,
        'note': (
            'V3.2 semantic dimensions separate style, tradition/cultural context, form and secondary influences. '
            'V3.4.1 prevents incompatible cross-family context from becoming authoritative. '
            'Evidence scores remain model relevance, not absolute genre probabilities.'
        ),
    }

    result['dimensions'] = dimensions
    result['version'] = DIMENSIONS_VERSION
    result.setdefault('studio_contract', {})['semantic_dimensions_additive'] = True
    result.setdefault('provenance', {})['dimensions'] = (
        'role-aware semantic decomposition over CLAP + Discogs ensemble evidence with V3.4.1 family-coherence guard; '
        'no metadata fact is inferred solely from a structural proxy'
    )
    return result


def _evidence_rows(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    ensemble = analysis.get('ensemble') if isinstance(analysis.get('ensemble'), dict) else {}
    source = ensemble.get('styles') if ensemble.get('status') == 'ready' else analysis.get('styles')
    rows: list[dict[str, Any]] = []
    for item in source or []:
        if not isinstance(item, dict) or not item.get('label'):
            continue
        row = copy.deepcopy(item)
        score = _score(row)
        row['evidence_score'] = round(score, 5)
        row['evidence_percent'] = round(score * 100.0, 1)
        rows.append(row)
    rows.sort(key=_score, reverse=True)
    return rows


def _effective_primary(analysis: dict[str, Any]) -> dict[str, Any]:
    ensemble = analysis.get('ensemble') if isinstance(analysis.get('ensemble'), dict) else {}
    primary = ensemble.get('primary') if isinstance(ensemble.get('primary'), dict) else analysis.get('primary')
    return copy.deepcopy(primary) if isinstance(primary, dict) else {}


def _role_for(row: dict[str, Any]) -> str:
    label = str(row.get('label') or '')
    if label in TRADITION_LABELS:
        return 'tradition'
    if label in FORM_LABELS:
        return 'form'
    return 'style'


def _pick_primary_style(rows: list[dict[str, Any]], primary: dict[str, Any]) -> dict[str, Any] | None:
    if not rows:
        candidate = primary.get('candidate') if isinstance(primary.get('candidate'), dict) else primary
        return copy.deepcopy(candidate) if isinstance(candidate, dict) and candidate.get('label') else None

    # Restrict the style result to the same family as the authoritative primary
    # when possible. This prevents a secondary regional style from hijacking an
    # otherwise coherent Hip-Hop/Pop/R&B decision.
    primary_candidate = primary.get('candidate') if isinstance(primary.get('candidate'), dict) else primary
    primary_family = str(primary_candidate.get('family') or '') if isinstance(primary_candidate, dict) else ''
    family_rows = [row for row in rows if primary_family and str(row.get('family') or '') == primary_family]
    candidates = family_rows or rows

    def ranking(row: dict[str, Any]) -> tuple[float, float]:
        evidence = _score(row)
        bonus = STYLE_SPECIFICITY_BONUS.get(str(row.get('label') or ''), 0.0)
        return evidence + bonus, evidence

    return copy.deepcopy(max(candidates, key=ranking))


def _family_for(
    primary_style: dict[str, Any] | None,
    primary: dict[str, Any],
    analysis: dict[str, Any],
) -> str:
    if primary_style and primary_style.get('family'):
        return str(primary_style['family'])
    candidate = primary.get('candidate') if isinstance(primary.get('candidate'), dict) else primary
    if isinstance(candidate, dict) and candidate.get('family'):
        return str(candidate['family'])
    consensus = analysis.get('consensus') if isinstance(analysis.get('consensus'), dict) else {}
    return str(consensus.get('primary_family') or '')


def _region_for(
    primary_style: dict[str, Any] | None,
    coherent_traditions: list[dict[str, Any]],
    family: str,
) -> str | None:
    if primary_style and str(primary_style.get('family') or '') == family and primary_style.get('region'):
        return str(primary_style['region'])
    for row in coherent_traditions:
        if row.get('region'):
            return str(row['region'])
    if family == 'Vietnamese / Asian':
        return 'Vietnam'
    return None


def _coherent_context_rows(
    rows: list[dict[str, Any]],
    family: str,
    *,
    role: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for row in rows:
        row_family = str(row.get('family') or '')
        label = str(row.get('label') or '')
        compatible = False
        if role == 'tradition':
            # Traditions are cultural context: unlike broad forms, they require
            # exact family coherence before they may become authoritative.
            compatible = bool(family and row_family == family)
        elif role == 'form':
            allowed = FORM_ALLOWED_FAMILIES.get(label)
            compatible = family in allowed if allowed is not None else bool(family and row_family == family)
        if compatible:
            accepted.append(copy.deepcopy(row))
        else:
            rejected.append(copy.deepcopy(row))

    accepted.sort(key=_score, reverse=True)
    rejected.sort(key=_score, reverse=True)
    return accepted, rejected


def _alternative_rows(rows: list[dict[str, Any]], primary: dict[str, Any] | None) -> list[dict[str, Any]]:
    primary_label = str((primary or {}).get('label') or '')
    return [copy.deepcopy(row) for row in rows if str(row.get('label') or '') != primary_label]


def _pick_influences(
    rows: list[dict[str, Any]],
    excluded: set[str],
    family: str,
    primary_style: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    primary_score = _score(primary_style or {})
    minimum = max(0.16, primary_score * 0.48)
    candidates = []
    for row in rows:
        label = str(row.get('label') or '')
        if not label or label in excluded or _role_for(row) == 'tradition' or _score(row) < minimum:
            continue
        candidates.append(row)

    def influence_rank(row: dict[str, Any]) -> tuple[int, float]:
        same_family = str(row.get('family') or '') == family
        role_priority = 2 if _role_for(row) == 'form' else 1
        return (3 if same_family else 0) + role_priority, _score(row)

    out = []
    for row in sorted(candidates, key=influence_rank, reverse=True)[:4]:
        item = _dimension_row(row, role='influence', authority='evidence')
        if item:
            item['source_role'] = _role_for(row)
            out.append(item)
    return out


def _normalize_form(row: dict[str, Any]) -> dict[str, Any]:
    label = str(row.get('label') or '')
    normalized = FORM_LABELS.get(label, label)
    item = _dimension_row(row, role='form', authority='evidence') or {}
    item['label'] = normalized
    item['source_label'] = label
    return item


def _dimension_row(
    row: dict[str, Any] | None,
    *,
    role: str,
    authority: str,
) -> dict[str, Any] | None:
    if not isinstance(row, dict) or not row.get('label'):
        return None
    score = _score(row)
    return {
        'label': str(row.get('label')),
        'family': row.get('family'),
        'region': row.get('region'),
        'evidence_score': round(score, 5),
        'evidence_percent': round(score * 100.0, 1),
        'role': role,
        'authority': authority,
        'provenance': row.get('provenance') or row.get('score_kind') or 'neural-evidence',
    }


def _family_evidence(family: str, analysis: dict[str, Any], primary_style: dict[str, Any] | None) -> dict[str, Any]:
    for row in analysis.get('families') or []:
        if isinstance(row, dict) and str(row.get('label') or '') == family:
            return {
                'score': round(_score(row), 5),
                'percent': round(_score(row) * 100.0, 1),
                'source': 'family-consensus',
            }
    score = _score(primary_style or {})
    return {
        'score': round(score, 5),
        'percent': round(score * 100.0, 1),
        'source': 'primary-style-evidence',
    }


def _score(row: dict[str, Any]) -> float:
    for key in ('ensemble_score', 'evidence_score', 'score', 'similarity'):
        value = row.get(key)
        if value is None:
            continue
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            continue
    return 0.0
