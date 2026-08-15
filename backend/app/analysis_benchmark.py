from __future__ import annotations

from typing import Any


def evaluate_genre_reference(reference: dict[str, Any], genre_analysis: dict[str, Any]) -> dict[str, Any]:
    expected_style = str(reference.get('expectedPrimaryStyle') or '').strip()
    expected_family = str(reference.get('expectedFamily') or '').strip()
    forbidden = {str(item).strip() for item in reference.get('forbiddenPrimaryStyles') or [] if str(item).strip()}

    primary = genre_analysis.get('primary') if isinstance(genre_analysis.get('primary'), dict) else {}
    actual_style = str(primary.get('label') or '').strip()
    if actual_style == 'Unknown / hybrid':
        candidate = primary.get('candidate') if isinstance(primary.get('candidate'), dict) else {}
        candidate_style = str(candidate.get('label') or '').strip()
    else:
        candidate_style = actual_style

    consensus = genre_analysis.get('consensus') if isinstance(genre_analysis.get('consensus'), dict) else {}
    actual_family = str(consensus.get('primary_family') or '').strip()
    confidence = genre_analysis.get('confidence') if isinstance(genre_analysis.get('confidence'), dict) else {}

    checks = {
        'primary_style': bool(expected_style) and actual_style == expected_style,
        'family': bool(expected_family) and actual_family == expected_family,
        'not_forbidden': actual_style not in forbidden and candidate_style not in forbidden,
        'not_unknown': actual_style != 'Unknown / hybrid',
    }
    passed = all(checks.values())
    return {
        'trackId': reference.get('trackId'),
        'passed': passed,
        'checks': checks,
        'expected': {
            'primaryStyle': expected_style,
            'family': expected_family,
            'forbiddenPrimaryStyles': sorted(forbidden),
        },
        'actual': {
            'primaryStyle': actual_style,
            'candidateStyle': candidate_style,
            'family': actual_family,
            'confidenceLevel': confidence.get('level'),
            'confidencePercent': confidence.get('percent'),
        },
    }


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
