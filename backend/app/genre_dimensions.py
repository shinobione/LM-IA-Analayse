from __future__ import annotations

import copy
from typing import Any

DIMENSIONS_VERSION = '3.2'
COHERENCE_VERSION = '3.5.2'

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

# V3.5.1+: open-vocabulary labels can fragment one coherent musical family into
# several medium-scoring candidates. Aggregate only the strongest few labels so
# a family is not rewarded merely for having a larger vocabulary.
FAMILY_CLUSTER_WEIGHTS = (1.00, 0.55, 0.30)
FAMILY_CLUSTER_MIN_ROW = 0.16
FAMILY_CLUSTER_MIN_SCORE = 0.58
FAMILY_CLUSTER_MIN_MARGIN = 0.08
REGIONAL_CLUSTER_MIN_LABELS = 3
GENERAL_CLUSTER_MIN_LABELS = 2

# V3.5.2: a real regional cluster is allowed to recover a fragmented family even
# when Discogs does not emit the Latin-Bolero proxy. This is deliberately strict:
# the regional cluster must dominate by a large margin and contain independent
# style + tradition + form cues, including the exact Vietnamese Bolero style.
REGIONAL_SEMANTIC_OVERRIDE_MIN_SCORE = 0.74
REGIONAL_SEMANTIC_OVERRIDE_MIN_MARGIN = 0.18


def attach_genre_dimensions(genre_analysis: dict[str, Any]) -> dict[str, Any]:
    """Attach additive semantic dimensions to an existing V3 analysis.

    V3.5.2 keeps the V3.5.1 family aggregation but removes an accidental veto:
    `Latin---Bolero` remains strong specialist support, not a mandatory proof of
    Vietnamese Bolero. A dominant multi-role Vietnamese cluster may recover the
    family on its own, while contextual regional primaries remain guarded.
    """
    result = copy.deepcopy(genre_analysis or {})
    rows = _evidence_rows(result)
    raw_rows = _raw_evidence_rows(result)
    primary = _effective_primary(result)
    primary_unknown = str(primary.get('label') or '').strip() == 'Unknown / hybrid'

    style_rows = [row for row in rows if _role_for(row) == 'style']
    tradition_rows = [row for row in rows if _role_for(row) == 'tradition']
    form_rows = [row for row in rows if _role_for(row) == 'form']

    family_cluster = _resolve_family_cluster(raw_rows)
    primary_style = _pick_primary_style(style_rows, primary, family_cluster)
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

    primary_candidate = _primary_candidate(primary)
    primary_role = _role_for(primary_candidate) if primary_candidate else None
    family_lock = _family_lock_status(primary_candidate, primary_style, family_cluster)

    dimensions = {
        'version': DIMENSIONS_VERSION,
        'coherence': {
            'version': COHERENCE_VERSION,
            'status': 'guarded',
            'resolved_family': broad_family or 'General',
            'primary_role': primary_role,
            'family_lock': family_lock,
            'family_cluster': family_cluster,
            'rejected_context': rejected_context,
        },
        'family': {
            'label': broad_family or 'General',
            'evidence': _family_evidence(broad_family, result, primary_style, family_cluster),
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
            'V3.5.2 aggregates fragmented same-family audio evidence and treats Latin-Bolero as supporting evidence, not a geographic veto. '
            'Evidence scores remain model relevance, not absolute genre probabilities.'
        ),
    }

    result['dimensions'] = dimensions
    result['version'] = DIMENSIONS_VERSION
    result.setdefault('studio_contract', {})['semantic_dimensions_additive'] = True
    result.setdefault('provenance', {})['dimensions'] = (
        'role-aware semantic decomposition over CLAP + Discogs ensemble evidence with V3.5.2 regional family authority; '
        'declared metadata is not inference input and specialist proxies remain supporting rather than geographic proof'
    )
    return result


def _evidence_rows(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    ensemble = analysis.get('ensemble') if isinstance(analysis.get('ensemble'), dict) else {}
    source = ensemble.get('styles') if ensemble.get('status') == 'ready' else analysis.get('styles')
    return _normalized_rows(source)


def _raw_evidence_rows(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    """Return raw CLAP/open-vocabulary style rows for family aggregation.

    The ensemble may deliberately penalize a regional label because Discogs
    cannot prove geography. Family aggregation therefore happens on the raw
    audio/text evidence, while the eventual style selection still uses the
    expert-enriched ensemble rows.
    """
    return _normalized_rows(analysis.get('styles'))


def _normalized_rows(source: Any) -> list[dict[str, Any]]:
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


def _primary_candidate(primary: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(primary, dict):
        return {}
    candidate = primary.get('candidate') if isinstance(primary.get('candidate'), dict) else primary
    return copy.deepcopy(candidate) if isinstance(candidate, dict) else {}


def _role_for(row: dict[str, Any]) -> str:
    label = str(row.get('label') or '')
    if label in TRADITION_LABELS:
        return 'tradition'
    if label in FORM_LABELS:
        return 'form'
    return 'style'


def _resolve_family_cluster(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        family = str(row.get('family') or '')
        if not family or _score(row) < FAMILY_CLUSTER_MIN_ROW:
            continue
        grouped.setdefault(family, []).append(row)

    summaries: list[dict[str, Any]] = []
    for family, family_rows in grouped.items():
        ordered = sorted(family_rows, key=_score, reverse=True)
        top = ordered[: len(FAMILY_CLUSTER_WEIGHTS)]
        aggregate = sum(weight * _score(row) for weight, row in zip(FAMILY_CLUSTER_WEIGHTS, top))
        aggregate = max(0.0, min(1.0, aggregate))
        style_rows = [row for row in ordered if _role_for(row) == 'style']
        minimum_labels = REGIONAL_CLUSTER_MIN_LABELS if family == 'Vietnamese / Asian' else GENERAL_CLUSTER_MIN_LABELS
        eligible = bool(
            len(ordered) >= minimum_labels
            and style_rows
            and aggregate >= FAMILY_CLUSTER_MIN_SCORE
        )
        summaries.append({
            'family': family,
            'score': round(aggregate, 5),
            'percent': round(aggregate * 100.0, 1),
            'label_count': len(ordered),
            'supporting_labels': [str(row.get('label') or '') for row in ordered[:4]],
            'roles': sorted({_role_for(row) for row in ordered}),
            'eligible': eligible,
            'style_specific_anchor': any(_can_anchor_family_from_context(row) for row in style_rows),
        })

    summaries.sort(key=lambda item: float(item.get('score') or 0.0), reverse=True)
    if not summaries:
        return {
            'status': 'none',
            'family': None,
            'score': 0.0,
            'percent': 0.0,
            'margin': 0.0,
            'supporting_labels': [],
            'families': [],
            'source': 'raw-audio-style-evidence',
        }

    best = summaries[0]
    runner = summaries[1] if len(summaries) > 1 else None
    runner_score = float((runner or {}).get('score') or 0.0)
    margin = float(best.get('score') or 0.0) - runner_score
    authoritative = bool(best.get('eligible')) and margin >= FAMILY_CLUSTER_MIN_MARGIN
    return {
        **copy.deepcopy(best),
        'status': 'authoritative' if authoritative else 'insufficient',
        'margin': round(margin, 5),
        'runner_up_family': (runner or {}).get('family'),
        'runner_up_score': round(runner_score, 5),
        'families': copy.deepcopy(summaries[:6]),
        'source': 'raw-audio-style-evidence',
    }


def _pick_primary_style(
    rows: list[dict[str, Any]],
    primary: dict[str, Any],
    family_cluster: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not rows:
        candidate = _primary_candidate(primary)
        return copy.deepcopy(candidate) if candidate.get('label') and _role_for(candidate) == 'style' else None

    primary_candidate = _primary_candidate(primary)
    primary_family = str(primary_candidate.get('family') or '')
    primary_role = _role_for(primary_candidate) if primary_candidate.get('label') else None

    cluster = family_cluster or {}
    cluster_family = str(cluster.get('family') or '') if cluster.get('status') == 'authoritative' else ''
    cluster_rows = [row for row in rows if cluster_family and str(row.get('family') or '') == cluster_family]
    cluster_can_override = False
    if cluster_rows:
        if cluster_family == 'Vietnamese / Asian':
            # A specialist Latin-Bolero proxy is strong support, but not a veto:
            # Vietnamese Bolero is not required to look sufficiently Latin to be
            # culturally Vietnamese. V3.5.2 therefore also accepts a dominant,
            # role-diverse regional cluster when the current primary is a true
            # non-regional style. Contextual regional primaries remain guarded.
            specialist_anchor = any(_can_anchor_family_from_context(row) for row in cluster_rows)
            roles = {str(role) for role in cluster.get('roles') or []}
            labels = {str(label) for label in cluster.get('supporting_labels') or []}
            semantic_anchor = bool(
                primary_role == 'style'
                and primary_family != cluster_family
                and {'style', 'tradition', 'form'}.issubset(roles)
                and {'Vietnamese Bolero', 'Nhạc Vàng', 'Vietnamese Pop Ballad'}.issubset(labels)
                and float(cluster.get('score') or 0.0) >= REGIONAL_SEMANTIC_OVERRIDE_MIN_SCORE
                and float(cluster.get('margin') or 0.0) >= REGIONAL_SEMANTIC_OVERRIDE_MIN_MARGIN
            )
            cluster_can_override = specialist_anchor or semantic_anchor
        elif cluster_family == primary_family:
            cluster_can_override = True
        elif primary_role in {'form', 'tradition'} or str(primary_candidate.get('label') or '') == 'Unknown / hybrid':
            cluster_can_override = True
        else:
            # Cross-family replacement of an explicit non-regional style is kept
            # conservative: demand a clearly dominant multi-label family cluster.
            cluster_can_override = bool(
                float(cluster.get('score') or 0.0) >= 0.72
                and float(cluster.get('margin') or 0.0) >= 0.18
            )

    if cluster_rows and cluster_can_override:
        candidates = cluster_rows
    else:
        family_rows = [row for row in rows if primary_family and str(row.get('family') or '') == primary_family]

        # A true style primary is allowed to anchor its family. A form/tradition
        # is contextual evidence, not permission to manufacture the best-looking
        # style from the same regional family. This remains the V3.4.2 guard.
        if primary_role == 'style' and family_rows:
            candidates = family_rows
        elif primary_role in {'form', 'tradition'} and family_rows:
            authoritative_family_rows = [row for row in family_rows if _can_anchor_family_from_context(row)]
            candidates = authoritative_family_rows or rows
        else:
            candidates = rows

    def ranking(row: dict[str, Any]) -> tuple[float, float]:
        evidence = _score(row)
        bonus = STYLE_SPECIFICITY_BONUS.get(str(row.get('label') or ''), 0.0)
        return evidence + bonus, evidence

    return copy.deepcopy(max(candidates, key=ranking))


def _can_anchor_family_from_context(row: dict[str, Any]) -> bool:
    family = str(row.get('family') or '')
    if not family:
        return False
    if family != 'Vietnamese / Asian':
        return True

    # Discogs cannot establish geography. For a contextual Vietnamese primary,
    # only a style with a style-specific proxy may anchor the regional family.
    # V3.5.2 deliberately keeps this strict for contextual primary cases; the
    # semantic-cluster path above is a separate cross-family recovery mechanism.
    label = str(row.get('label') or '')
    structural_labels = {str(item) for item in row.get('structural_support_labels') or []}
    regional = row.get('regional_coherence') if isinstance(row.get('regional_coherence'), dict) else {}
    status = str(regional.get('status') or '')

    if label == 'Vietnamese Bolero':
        return 'Latin---Bolero' in structural_labels and status not in {'conflict', 'weak'}
    return False


def _family_lock_status(
    primary_candidate: dict[str, Any],
    primary_style: dict[str, Any] | None,
    family_cluster: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not primary_candidate:
        return {'status': 'unresolved', 'reason': 'no primary candidate'}

    role = _role_for(primary_candidate)
    family = str(primary_candidate.get('family') or '')
    style_family = str((primary_style or {}).get('family') or '')
    cluster = family_cluster or {}
    cluster_family = str(cluster.get('family') or '')

    if (
        cluster.get('status') == 'authoritative'
        and cluster_family
        and cluster_family == style_family
        and cluster_family != family
    ):
        return {
            'status': 'evidence-cluster-authority',
            'family': style_family,
            'score': cluster.get('score'),
            'margin': cluster.get('margin'),
            'supporting_labels': copy.deepcopy(cluster.get('supporting_labels') or []),
            'reason': 'multiple same-family audio labels outweighed an isolated primary from another family',
        }

    if role == 'style' and family == style_family:
        return {'status': 'authoritative-style', 'family': family}
    if family and family == style_family and _can_anchor_family_from_context(primary_style or {}):
        return {'status': 'context-supported-by-style-specific-proxy', 'family': family}
    return {
        'status': 'released',
        'family': family or None,
        'reason': 'primary is contextual or was not supported strongly enough to lock the resolved style family',
    }


def _family_for(
    primary_style: dict[str, Any] | None,
    primary: dict[str, Any],
    analysis: dict[str, Any],
) -> str:
    if primary_style and primary_style.get('family'):
        return str(primary_style['family'])
    candidate = _primary_candidate(primary)
    if candidate.get('family') and _role_for(candidate) == 'style':
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


def _family_evidence(
    family: str,
    analysis: dict[str, Any],
    primary_style: dict[str, Any] | None,
    family_cluster: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cluster = family_cluster or {}
    if cluster.get('status') == 'authoritative' and str(cluster.get('family') or '') == family:
        return {
            'score': round(float(cluster.get('score') or 0.0), 5),
            'percent': round(float(cluster.get('score') or 0.0) * 100.0, 1),
            'source': 'cross-label-family-cluster',
            'supporting_labels': copy.deepcopy(cluster.get('supporting_labels') or []),
            'margin': round(float(cluster.get('margin') or 0.0), 5),
        }

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
