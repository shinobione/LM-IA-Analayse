from __future__ import annotations

from typing import Any


def evaluate_genre_reference(reference: dict[str, Any], genre_analysis: dict[str, Any]) -> dict[str, Any]:
    expected_styles = _expected_primary_styles(reference)
    expected_style = expected_styles[0] if expected_styles else ''
    expected_family = str(reference.get('expectedFamily') or '').strip()
    forbidden = {str(item).strip() for item in reference.get('forbiddenPrimaryStyles') or [] if str(item).strip()}

    primary = genre_analysis.get('primary') if isinstance(genre_analysis.get('primary'), dict) else {}
    raw_primary_style = str(primary.get('label') or '').strip()
    if raw_primary_style == 'Unknown / hybrid':
        candidate = primary.get('candidate') if isinstance(primary.get('candidate'), dict) else {}
        candidate_style = str(candidate.get('label') or '').strip()
    else:
        candidate_style = raw_primary_style

    dimensions = genre_analysis.get('dimensions') if isinstance(genre_analysis.get('dimensions'), dict) else {}
    style_dimension = dimensions.get('style') if isinstance(dimensions.get('style'), dict) else {}
    dimension_primary = style_dimension.get('primary') if isinstance(style_dimension.get('primary'), dict) else {}
    dimension_style = str(dimension_primary.get('label') or '').strip()
    dimension_family = dimensions.get('family') if isinstance(dimensions.get('family'), dict) else {}

    # V3.2 separates cultural/tradition labels from the actual primary musical
    # style. The benchmark therefore prefers the explicit style dimension while
    # preserving the old V3 path for older payloads.
    actual_style = dimension_style or raw_primary_style

    consensus = genre_analysis.get('consensus') if isinstance(genre_analysis.get('consensus'), dict) else {}
    actual_family = str(dimension_family.get('label') or consensus.get('primary_family') or '').strip()
    confidence = genre_analysis.get('confidence') if isinstance(genre_analysis.get('confidence'), dict) else {}
    is_unknown = bool(dimensions.get('unknown')) if dimensions else raw_primary_style == 'Unknown / hybrid'

    relevant_labels = {actual_style, raw_primary_style, candidate_style}
    relevant_labels.discard('')
    relevant_labels.discard('Unknown / hybrid')

    checks = {
        'primary_style': bool(expected_styles) and actual_style in expected_styles,
        'family': bool(expected_family) and actual_family == expected_family,
        'not_forbidden': not bool(relevant_labels & forbidden),
        'not_unknown': not is_unknown,
    }
    passed = all(checks.values())
    return {
        'trackId': reference.get('trackId'),
        'passed': passed,
        'checks': checks,
        'expected': {
            # `primaryStyle` is retained for older consumers; V3.5.1 additionally
            # supports an artist-confirmed cluster when a track is intentionally
            # hybrid and more than one neighbouring primary label is defensible.
            'primaryStyle': expected_style,
            'primaryStyles': expected_styles,
            'family': expected_family,
            'forbiddenPrimaryStyles': sorted(forbidden),
        },
        'actual': {
            'primaryStyle': actual_style,
            'rawPrimaryLabel': raw_primary_style,
            'candidateStyle': candidate_style,
            'family': actual_family,
            'dimensionVersion': dimensions.get('version') if dimensions else None,
            'confidenceLevel': confidence.get('level'),
            'confidencePercent': confidence.get('percent'),
        },
    }


def _expected_primary_styles(reference: dict[str, Any]) -> list[str]:
    multi = reference.get('expectedPrimaryStyles')
    if isinstance(multi, (list, tuple)):
        styles = [str(item).strip() for item in multi if str(item).strip()]
        if styles:
            return list(dict.fromkeys(styles))
    single = str(reference.get('expectedPrimaryStyle') or '').strip()
    return [single] if single else []


def summarize_benchmark(reference_set: dict[str, Any], analyses: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for reference in reference_set.get('tracks') or []:
        if not isinstance(reference, dict):
            continue
        track_id = str(reference.get('trackId') or '').strip()
        payload = analyses.get(track_id) if isinstance(analyses, dict) else None
        if not isinstance(payload, dict):
            rows.append({
                'trackId': track_id,
                'passed': False,
                'checks': {'analysis_present': False},
                'error': 'No genre_analysis payload supplied for this reference track.',
            })
            continue
        rows.append(evaluate_genre_reference(reference, payload))

    passed = sum(1 for row in rows if row.get('passed'))
    total = len(rows)
    return {
        'schemaVersion': 1,
        'benchmark': reference_set.get('name') or 'genre benchmark',
        'passed': passed,
        'total': total,
        'passPercent': round((passed / total * 100.0) if total else 0.0, 1),
        'rows': rows,
    }
