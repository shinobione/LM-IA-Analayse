from __future__ import annotations

import copy
from typing import Any

from .genre_dimensions import attach_genre_dimensions

ENSEMBLE_VERSION = '3.4.1'

# Direct bridges only where the two taxonomies genuinely mean roughly the same
# musical style. Regional/cultural labels are intentionally NOT inferred from
# Discogs classes that lack that geography.
DISCOGS_TO_V3: dict[str, str] = {
    'Hip Hop---Boom Bap': 'Boom Bap',
    'Hip Hop---Cloud Rap': 'Cloud Rap',
    'Hip Hop---G-Funk': 'G-Funk',
    'Hip Hop---Grime': 'Grime',
    'Hip Hop---Horrorcore': 'Horrorcore',
    'Hip Hop---Jazzy Hip-Hop': 'Jazzy Hip-Hop',
    'Hip Hop---Pop Rap': 'Pop Rap',
    'Hip Hop---Trap': 'Trap',
    'Funk / Soul---Contemporary R&B': 'Contemporary R&B',
    'Funk / Soul---Neo Soul': 'Neo Soul',
    'Funk / Soul---New Jack Swing': 'New Jack Swing',
    'Funk / Soul---Soul': 'Soul',
    'Funk / Soul---Funk': 'Funk',
    'Pop---Ballad': 'Pop Ballad',
    'Pop---Chanson': 'French Chanson',
    'Pop---City Pop': 'City Pop',
    'Pop---Europop': 'Europop',
    'Pop---Indie Pop': 'Indie Pop',
    'Pop---J-pop': 'J-Pop',
    'Pop---K-pop': 'K-Pop',
    'Electronic---Ambient': 'Ambient',
    'Electronic---Dark Ambient': 'Dark Ambient',
    'Electronic---Deep House': 'Deep House',
    'Electronic---Downtempo': 'Downtempo',
    'Electronic---Drum n Bass': 'Drum and Bass',
    'Electronic---Dubstep': 'Dubstep',
    'Electronic---Glitch': 'Glitch',
    'Electronic---House': 'House',
    'Electronic---IDM': 'IDM',
    'Electronic---Industrial': 'Industrial Electronic',
    'Electronic---Jungle': 'Jungle',
    'Electronic---Synth-pop': 'Synth-Pop',
    'Electronic---Synthwave': 'Synthwave',
    'Electronic---Techno': 'Techno',
    'Electronic---Trance': 'Trance',
    'Electronic---Trip Hop': 'Trip Hop',
    'Electronic---Vaporwave': 'Vaporwave',
    'Reggae---Dancehall': 'Dancehall',
    'Reggae---Dub': 'Dub',
    'Reggae---Lovers Rock': 'Lovers Rock',
    'Reggae---Reggae': 'Reggae',
    'Reggae---Ska': 'Ska',
    'Reggae---Soca': 'Soca',
    'Latin---Bolero': 'Latin Bolero',
    'Latin---Cumbia': 'Cumbia',
    'Latin---Reggaeton': 'Reggaeton',
    'Latin---Salsa': 'Salsa',
    'Latin---Samba': 'Samba',
    'Latin---Tango': 'Tango',
    'Jazz---Bossa Nova': 'Bossa Nova',
    'Jazz---Jazz-Funk': 'Jazz-Funk',
    'Jazz---Smooth Jazz': 'Smooth Jazz',
    'Folk, World, & Country---Fado': 'Fado',
    'Folk, World, & Country---Folk': 'Folk',
    'Folk, World, & Country---Highlife': 'Highlife',
    'Folk, World, & Country---Indian Classical': 'Indian Classical',
    'Folk, World, & Country---Zouk': 'Zouk',
    'Funk / Soul---Afrobeat': 'Afrobeat',
    'Rock---Alternative Rock': 'Alternative Rock',
    'Rock---Dream Pop': 'Dream Pop',
    'Rock---Hard Rock': 'Hard Rock',
    'Rock---Heavy Metal': 'Heavy Metal',
    'Rock---Indie Rock': 'Indie Rock',
    'Rock---Post Rock': 'Post-Rock',
    'Rock---Punk': 'Punk',
    'Rock---Shoegaze': 'Shoegaze',
    'Classical---Classical': 'Classical',
    'Classical---Neo-Classical': 'Neo-Classical',
    'Stage & Screen---Score': 'Cinematic Score',
    'Stage & Screen---Soundtrack': 'Soundtrack',
}

VIETNAMESE_STRUCTURAL_SUPPORT: dict[str, tuple[str, ...]] = {
    'Vietnamese Bolero': ('Latin---Bolero', 'Pop---Ballad', 'Folk, World, & Country---Folk'),
    'Nhạc Vàng': ('Pop---Ballad', 'Folk, World, & Country---Folk', 'Latin---Bolero'),
    'Nhạc Trữ Tình': ('Pop---Ballad', 'Folk, World, & Country---Folk'),
    'Vietnamese Pop Ballad': ('Pop---Ballad',),
    'V-Pop': ('Pop---Vocal', 'Pop---Ballad'),
    'Vietnamese Folk': ('Folk, World, & Country---Folk',),
    'Vietnamese Traditional': ('Folk, World, & Country---Folk',),
    'Asian Ballad': ('Pop---Ballad',),
}

# Discogs cannot prove Vietnamese geography, but it can say whether the musical
# structure underneath a regional label is plausible. V3.4.1 uses this matrix
# as a coherence gate rather than granting every Vietnamese label a free 0.50
# family-support score.
VIETNAMESE_COMPATIBLE_EXPERT_FAMILIES: dict[str, tuple[str, ...]] = {
    'Vietnamese Bolero': ('Latin', 'Pop', 'Folk / World', 'Country / Acoustic'),
    'Nhạc Vàng': ('Pop', 'Folk / World', 'Latin', 'Country / Acoustic'),
    'Nhạc Trữ Tình': ('Pop', 'Folk / World', 'R&B / Soul / Funk', 'Country / Acoustic'),
    'Vietnamese Pop Ballad': ('Pop', 'R&B / Soul / Funk', 'Country / Acoustic'),
    'V-Pop': ('Pop', 'Electronic', 'R&B / Soul / Funk'),
    'Vietnamese Folk': ('Folk / World', 'Country / Acoustic'),
    'Vietnamese Traditional': ('Folk / World', 'Country / Acoustic'),
    'Asian Ballad': ('Pop', 'R&B / Soul / Funk', 'Country / Acoustic'),
}


def fuse_genre_analysis(clap_analysis: dict[str, Any], expert: dict[str, Any] | None) -> dict[str, Any]:
    result = copy.deepcopy(clap_analysis)
    expert = expert or {'status': 'unavailable'}
    original_primary = copy.deepcopy(result.get('primary'))
    result['experts'] = {
        'clap': {
            'primary': original_primary,
            'confidence': copy.deepcopy(result.get('confidence')),
            'method': 'open-vocabulary segment consensus',
        },
        'discogs400': expert,
    }

    if expert.get('status') != 'ready':
        result['ensemble'] = {
            'version': ENSEMBLE_VERSION,
            'status': 'clap-only',
            'primary': original_primary,
            'styles': copy.deepcopy(result.get('styles') or []),
            'reason': f"Discogs expert {expert.get('status') or 'unavailable'}; CLAP V3 remains authoritative for this scan.",
        }
        return attach_genre_dimensions(result)

    clap_styles = [item for item in result.get('styles') or [] if isinstance(item, dict) and item.get('label')]
    if not clap_styles:
        result['ensemble'] = {'version': ENSEMBLE_VERSION, 'status': 'clap-only', 'primary': original_primary, 'styles': []}
        return attach_genre_dimensions(result)

    expert_styles = [item for item in expert.get('top_styles') or [] if isinstance(item, dict)]
    expert_by_discogs = {str(item.get('label')): float(item.get('score') or 0.0) for item in expert_styles}
    expert_by_v3: dict[str, float] = {}
    for label, score in expert_by_discogs.items():
        mapped = DISCOGS_TO_V3.get(label)
        if mapped:
            expert_by_v3[mapped] = max(expert_by_v3.get(mapped, 0.0), score)
    expert_family = {
        str(item.get('label')): float(item.get('score') or 0.0)
        for item in expert.get('families') or []
        if isinstance(item, dict) and item.get('label')
    }
    expert_top_family = str((expert.get('families') or [{}])[0].get('label') or '') if expert.get('families') else ''
    expert_top_family_score = float((expert.get('families') or [{}])[0].get('score') or 0.0) if expert.get('families') else 0.0

    similarities = [float(item.get('similarity') or item.get('score') or 0.0) for item in clap_styles]
    low, high = min(similarities), max(similarities)
    spread = max(high - low, 1e-6)

    rows: list[dict[str, Any]] = []
    for rank, item in enumerate(clap_styles):
        label = str(item['label'])
        family = str(item.get('family') or '')
        similarity = float(item.get('similarity') or item.get('score') or 0.0)
        clap_norm = max(0.0, min(1.0, (similarity - low) / spread))
        # Rank prior avoids over-amplifying tiny numerical differences at the tail.
        rank_prior = max(0.0, 1.0 - rank / max(1, len(clap_styles) - 1))
        clap_evidence = 0.78 * clap_norm + 0.22 * rank_prior

        direct = expert_by_v3.get(label, 0.0)
        structural = 0.0
        structural_labels: list[str] = []
        if label in VIETNAMESE_STRUCTURAL_SUPPORT:
            for discogs_label in VIETNAMESE_STRUCTURAL_SUPPORT[label]:
                value = expert_by_discogs.get(discogs_label, 0.0)
                if value > structural:
                    structural = value
                if value >= 0.15:
                    structural_labels.append(discogs_label)
        style_support = max(direct, structural * 0.72)

        regional = _regional_coherence(
            label,
            family,
            structural=structural,
            expert_family=expert_family,
            expert_top_family=expert_top_family,
            expert_top_family_score=expert_top_family_score,
        )
        if family == 'Vietnamese / Asian':
            family_support = float(regional['compatible_family_support'])
        else:
            family_support = expert_family.get(family, 0.0)

        combined = 0.62 * clap_evidence + 0.25 * style_support + 0.13 * family_support
        combined *= float(regional['gate'])
        rows.append({
            **item,
            'ensemble_score': round(max(0.0, min(1.0, combined)), 5),
            'ensemble_percent': round(max(0.0, min(1.0, combined)) * 100.0, 1),
            'clap_evidence': round(clap_evidence, 5),
            'discogs_style_support': round(style_support, 5),
            'discogs_family_support': round(family_support, 5),
            'discogs_direct_match': round(direct, 5),
            'discogs_structural_support': round(structural, 5),
            'structural_support_labels': structural_labels,
            'regional_coherence': regional,
            'provenance': 'neural-ensemble-clap-discogs400-v3.4.1',
        })

    rows.sort(key=lambda item: float(item['ensemble_score']), reverse=True)
    winner = rows[0]
    runner = rows[1] if len(rows) > 1 else winner
    ensemble_margin = float(winner['ensemble_score']) - float(runner['ensemble_score'])

    clap_primary_label, clap_primary_row = _primary_label_and_row(original_primary)
    clap_candidate_label = str((clap_primary_row or {}).get('label') or '')
    clap_ensemble_row = next((item for item in rows if item.get('label') == clap_candidate_label), None)
    winner_label = str(winner.get('label') or '')
    winner_direct = float(winner.get('discogs_direct_match') or 0.0)

    final_label = clap_primary_label
    decision = 'kept-clap-primary'
    forced_unknown_candidate: dict[str, Any] | None = None

    # V3.4.1 regional coherence guard. A regional CLAP primary may no longer stay
    # authoritative solely because it won the text similarity race. If Discogs
    # strongly hears an incompatible family and the regional structural proxies
    # are weak, prefer a coherent non-regional candidate or explicitly UNKNOWN.
    regional_conflict = bool(
        clap_ensemble_row
        and str(clap_ensemble_row.get('family') or '') == 'Vietnamese / Asian'
        and str((clap_ensemble_row.get('regional_coherence') or {}).get('status') or '') == 'conflict'
    )
    if regional_conflict:
        nonregional = next((item for item in rows if str(item.get('family') or '') != 'Vietnamese / Asian'), None)
        regional_score = float(clap_ensemble_row.get('ensemble_score') or 0.0)
        if nonregional is not None:
            nonregional_score = float(nonregional.get('ensemble_score') or 0.0)
            nonregional_family_support = float(nonregional.get('discogs_family_support') or 0.0)
            expert_matches_nonregional = expert_top_family and expert_top_family == str(nonregional.get('family') or '')
            if (
                nonregional_family_support >= 0.14
                and (expert_matches_nonregional or nonregional_score >= regional_score - 0.07)
            ):
                final_label = str(nonregional.get('label') or '')
                decision = 'regional-primary-rejected-by-cross-family-coherence'
            else:
                final_label = 'Unknown / hybrid'
                forced_unknown_candidate = copy.deepcopy(nonregional)
                decision = 'regional-primary-demoted-to-unknown-by-cross-family-coherence'
        else:
            final_label = 'Unknown / hybrid'
            decision = 'regional-primary-demoted-to-unknown-by-cross-family-coherence'
    elif clap_primary_label == 'Unknown / hybrid':
        candidate = original_primary.get('candidate') if isinstance(original_primary, dict) else None
        candidate_label = str(candidate.get('label') or '') if isinstance(candidate, dict) else ''
        # Promote UNKNOWN only when both experts independently support the same
        # non-regional style with a meaningful margin.
        if winner_label == candidate_label and winner_direct >= 0.30 and ensemble_margin >= 0.06 and float(winner['ensemble_score']) >= 0.68:
            final_label = winner_label
            decision = 'promoted-from-unknown-by-direct-expert-agreement'
    elif winner_label != clap_primary_label:
        # A specialist model may overturn CLAP only with a direct taxonomic match,
        # not through family resemblance or a regional proxy.
        if winner_direct >= 0.38 and ensemble_margin >= 0.10 and float(winner['ensemble_score']) >= 0.72:
            final_label = winner_label
            decision = 'specialist-overrode-clap-with-strong-direct-agreement'

    if final_label == clap_primary_label and clap_primary_label != 'Unknown / hybrid':
        primary_row = next((item for item in rows if item.get('label') == final_label), None) or clap_primary_row or winner
        final_primary = {
            **primary_row,
            'label': final_label,
            'decision': decision,
        }
    elif final_label != 'Unknown / hybrid':
        primary_row = next((item for item in rows if item.get('label') == final_label), None) or winner
        final_primary = {**primary_row, 'decision': decision}
    elif forced_unknown_candidate is not None:
        final_primary = {
            'label': 'Unknown / hybrid',
            'candidate': forced_unknown_candidate,
            'reason': 'Regional evidence conflicts with the music-specialist family evidence; SonicTrace refuses to force a geographic style.',
            'decision': decision,
        }
    else:
        final_primary = copy.deepcopy(original_primary)
        if isinstance(final_primary, dict):
            final_primary['decision'] = decision

    confidence = copy.deepcopy(result.get('confidence') or {})
    base_confidence = float(confidence.get('score') or 0.0)
    primary_ensemble_row = next((item for item in rows if item.get('label') == final_label), None)
    if primary_ensemble_row:
        direct = float(primary_ensemble_row.get('discogs_direct_match') or 0.0)
        structural = float(primary_ensemble_row.get('discogs_structural_support') or 0.0)
        family_support = float(primary_ensemble_row.get('discogs_family_support') or 0.0)
        if direct >= 0.25:
            base_confidence += min(0.12, direct * 0.16)
        elif structural >= 0.25 and str(primary_ensemble_row.get('family')) == 'Vietnamese / Asian':
            base_confidence += min(0.07, structural * 0.10)
        elif family_support < 0.08 and str(primary_ensemble_row.get('family')) != 'Vietnamese / Asian':
            base_confidence -= 0.08

    final_family = str(primary_ensemble_row.get('family') or '') if primary_ensemble_row else ''
    strong_family_conflict = bool(regional_conflict) or (
        expert_top_family
        and final_family
        and expert_top_family != final_family
        and expert_top_family_score >= 0.22
    )
    if strong_family_conflict:
        base_confidence -= 0.10
    if regional_conflict:
        base_confidence -= 0.12

    base_confidence = max(0.0, min(1.0, base_confidence))
    confidence['score'] = round(base_confidence, 4)
    confidence['percent'] = round(base_confidence * 100.0, 1)
    confidence['level'] = 'high' if base_confidence >= 0.72 else 'medium' if base_confidence >= 0.50 else 'low'
    confidence['ensemble_version'] = ENSEMBLE_VERSION
    confidence['expert_family_conflict'] = strong_family_conflict
    confidence['regional_coherence_conflict'] = regional_conflict
    confidence['note'] = 'Evidence confidence after CLAP temporal consensus + Discogs400 specialist cross-check + V3.4.1 cross-family coherence; not an absolute genre probability.'

    result['primary'] = final_primary
    result['confidence'] = confidence
    result['ensemble'] = {
        'version': ENSEMBLE_VERSION,
        'status': 'ready',
        'decision': decision,
        'primary': copy.deepcopy(final_primary),
        'styles': rows,
        'margin': round(ensemble_margin, 5),
        'expert_top_family': expert_top_family,
        'expert_top_family_score': round(expert_top_family_score, 5),
        'regional_coherence_conflict': regional_conflict,
        'regional_guard': (
            'Discogs400 cannot establish Vietnamese geography. V3.4.1 therefore requires compatible musical-structure evidence '
            'before a regional label may stay authoritative; Latin---Bolero can support bolero structure but never establish geography.'
        ),
    }
    return attach_genre_dimensions(result)


def _regional_coherence(
    label: str,
    family: str,
    *,
    structural: float,
    expert_family: dict[str, float],
    expert_top_family: str,
    expert_top_family_score: float,
) -> dict[str, Any]:
    if family != 'Vietnamese / Asian':
        return {
            'status': 'not-regional',
            'gate': 1.0,
            'compatible_family_support': expert_family.get(family, 0.0),
            'expert_top_family': expert_top_family,
        }

    compatible_families = VIETNAMESE_COMPATIBLE_EXPERT_FAMILIES.get(label, ('Pop', 'Folk / World'))
    compatible_family_support = max((expert_family.get(name, 0.0) for name in compatible_families), default=0.0)
    support = max(float(structural), compatible_family_support)
    top_incompatible = bool(
        expert_top_family
        and expert_top_family not in compatible_families
        and expert_top_family_score >= 0.20
    )

    if top_incompatible and support < 0.18:
        status = 'conflict'
        gate = 0.62
    elif support < 0.12:
        status = 'weak'
        gate = 0.76
    elif support >= 0.22:
        status = 'supported'
        gate = 1.0
    else:
        status = 'plausible'
        gate = 0.92

    return {
        'status': status,
        'gate': round(gate, 4),
        'compatible_family_support': round(compatible_family_support, 5),
        'structural_support': round(float(structural), 5),
        'expert_top_family': expert_top_family,
        'expert_top_family_score': round(float(expert_top_family_score), 5),
        'compatible_expert_families': list(compatible_families),
    }


def _primary_label_and_row(primary: Any) -> tuple[str, dict[str, Any] | None]:
    if not isinstance(primary, dict):
        return '', None
    label = str(primary.get('label') or '')
    if label == 'Unknown / hybrid':
        candidate = primary.get('candidate')
        return label, candidate if isinstance(candidate, dict) else None
    return label, primary
