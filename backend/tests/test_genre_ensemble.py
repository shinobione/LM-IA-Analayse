from __future__ import annotations

import unittest

from app.genre_ensemble import fuse_genre_analysis


def clap_fixture(primary: str, family: str, confidence: float = 0.60) -> dict:
    return {
        'primary': {
            'label': primary,
            'family': family,
            'similarity': 0.31,
            'score': 0.31,
            'percent': 31.0,
        },
        'styles': [
            {'label': primary, 'family': family, 'similarity': 0.31, 'score': 0.31, 'percent': 31.0},
            {'label': 'Pop Ballad', 'family': 'Pop', 'similarity': 0.26, 'score': 0.26, 'percent': 26.0},
            {'label': 'Contemporary R&B', 'family': 'R&B / Soul / Funk', 'similarity': 0.22, 'score': 0.22, 'percent': 22.0},
            {'label': 'Rock', 'family': 'Rock / Metal', 'similarity': 0.17, 'score': 0.17, 'percent': 17.0},
        ],
        'families': [],
        'confidence': {'score': confidence, 'percent': confidence * 100, 'level': 'medium', 'is_unknown': False},
        'consensus': {'primary_family': family},
    }


def expert_fixture(styles: list[tuple[str, str, float]], families: list[tuple[str, float]]) -> dict:
    return {
        'status': 'ready',
        'top_styles': [
            {'label': label, 'family': family, 'score': score, 'percent': score * 100}
            for label, family, score in styles
        ],
        'families': [{'label': family, 'score': score, 'percent': score * 100} for family, score in families],
        'embedding': {'dimension': 1280, 'vector': [0.0] * 1280},
    }


class GenreEnsembleTests(unittest.TestCase):
    def test_vietnamese_bolero_is_not_rewritten_as_latin_bolero(self) -> None:
        clap = clap_fixture('Vietnamese Bolero', 'Vietnamese / Asian', 0.61)
        expert = expert_fixture(
            [
                ('Latin---Bolero', 'Latin', 0.62),
                ('Pop---Ballad', 'Pop', 0.44),
                ('Funk / Soul---Soul', 'R&B / Soul / Funk', 0.12),
            ],
            [('Latin', 0.28), ('Pop', 0.22), ('R&B / Soul / Funk', 0.08)],
        )
        result = fuse_genre_analysis(clap, expert)
        self.assertEqual(result['primary']['label'], 'Vietnamese Bolero')
        self.assertIn('cannot establish Vietnamese geography', result['ensemble']['regional_guard'])
        bolero = next(item for item in result['ensemble']['styles'] if item['label'] == 'Vietnamese Bolero')
        self.assertGreater(bolero['discogs_structural_support'], 0.5)
        self.assertEqual(bolero['discogs_direct_match'], 0.0)
        self.assertEqual(bolero['regional_coherence']['status'], 'supported')
        self.assertFalse(result['confidence']['regional_coherence_conflict'])

    def test_false_vietnamese_primary_is_demoted_when_discogs_hears_incompatible_family(self) -> None:
        clap = {
            'primary': {
                'label': 'Vietnamese Pop Ballad',
                'family': 'Vietnamese / Asian',
                'region': 'Vietnam',
                'similarity': 0.69,
                'score': 0.69,
                'percent': 69.0,
            },
            'styles': [
                {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'similarity': 0.69, 'score': 0.69},
                {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'similarity': 0.58, 'score': 0.58},
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'similarity': 0.42, 'score': 0.42},
                {'label': 'Country', 'family': 'Country / Acoustic', 'similarity': 0.38, 'score': 0.38},
                {'label': 'Pop', 'family': 'Pop', 'similarity': 0.36, 'score': 0.36},
                {'label': 'Dancehall', 'family': 'Reggae / Caribbean', 'similarity': 0.35, 'score': 0.35},
                {'label': 'House', 'family': 'Electronic', 'similarity': 0.34, 'score': 0.34},
            ],
            'families': [
                {'label': 'Vietnamese / Asian', 'score': 0.69},
                {'label': 'R&B / Soul / Funk', 'score': 0.42},
                {'label': 'Pop', 'score': 0.36},
            ],
            'confidence': {'score': 0.70, 'percent': 70.0, 'level': 'medium', 'is_unknown': False},
            'consensus': {'primary_family': 'Vietnamese / Asian'},
        }
        expert = expert_fixture(
            [
                ('Reggae---Dancehall', 'Reggae / Caribbean', 0.82),
                ('Electronic---House', 'Electronic', 0.63),
                ('Pop---Ballad', 'Pop', 0.04),
            ],
            [('Reggae / Caribbean', 0.41), ('Electronic', 0.31), ('Pop', 0.08), ('R&B / Soul / Funk', 0.07)],
        )
        result = fuse_genre_analysis(clap, expert)
        self.assertTrue(result['confidence']['regional_coherence_conflict'])
        self.assertNotEqual(result['primary']['label'], 'Vietnamese Pop Ballad')
        self.assertNotEqual(result['dimensions']['family']['label'], 'Vietnamese / Asian')
        self.assertIsNone(result['dimensions']['tradition']['primary'])
        self.assertIsNone(result['dimensions']['region']['label'])
        vietnamese_row = next(item for item in result['ensemble']['styles'] if item['label'] == 'Vietnamese Pop Ballad')
        self.assertEqual(vietnamese_row['regional_coherence']['status'], 'conflict')
        self.assertLess(vietnamese_row['regional_coherence']['gate'], 1.0)

    def test_v35_multi_cue_neighborhood_can_resolve_dancehall_pop_over_neo_soul(self) -> None:
        clap = {
            'primary': {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'similarity': 0.44, 'score': 0.44},
            'styles': [
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'similarity': 0.44, 'score': 0.44},
                {'label': 'Dancehall Pop', 'family': 'Pop', 'similarity': 0.43, 'score': 0.43},
                {'label': 'Europop', 'family': 'Pop', 'similarity': 0.40, 'score': 0.40},
                {'label': 'Euro-House', 'family': 'Electronic', 'similarity': 0.39, 'score': 0.39},
                {'label': 'Afropop', 'family': 'Folk / World', 'similarity': 0.38, 'score': 0.38},
                {'label': 'Pop', 'family': 'Pop', 'similarity': 0.35, 'score': 0.35},
            ],
            'families': [
                {'label': 'R&B / Soul / Funk', 'score': 0.44},
                {'label': 'Pop', 'score': 0.43},
                {'label': 'Electronic', 'score': 0.39},
            ],
            'confidence': {'score': 0.61, 'percent': 61.0, 'level': 'medium', 'is_unknown': False},
            'consensus': {'primary_family': 'R&B / Soul / Funk'},
        }
        expert = expert_fixture(
            [
                ('Reggae---Dancehall', 'Reggae / Caribbean', 0.90),
                ('Pop---Europop', 'Pop', 0.75),
                ('Electronic---House', 'Electronic', 0.70),
                ('Funk / Soul---Afrobeat', 'Folk / World', 0.45),
                ('Funk / Soul---Neo Soul', 'R&B / Soul / Funk', 0.06),
            ],
            [('Reggae / Caribbean', 0.40), ('Pop', 0.33), ('Electronic', 0.31), ('R&B / Soul / Funk', 0.05)],
        )
        result = fuse_genre_analysis(clap, expert)
        self.assertEqual(result['primary']['label'], 'Dancehall Pop')
        self.assertEqual(result['dimensions']['style']['primary']['label'], 'Dancehall Pop')
        self.assertEqual(result['dimensions']['family']['label'], 'Pop')
        self.assertEqual(result['ensemble']['style_calibration']['version'], '3.6')
        self.assertFalse(result['ensemble']['style_calibration']['declared_metadata_used_for_inference'])
        dancehall_pop = next(item for item in result['ensemble']['styles'] if item['label'] == 'Dancehall Pop')
        self.assertGreaterEqual(dancehall_pop['discogs_neighborhood_support'], 0.38)
        self.assertGreaterEqual(len(dancehall_pop['neighborhood_support_labels']), 2)
        self.assertEqual(result['primary']['decision'], 'style-calibration-overrode-clap-with-multi-cue-neighborhood')

    def test_v35_single_neighbor_cannot_force_a_hybrid_style(self) -> None:
        clap = {
            'primary': {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'similarity': 0.44, 'score': 0.44},
            'styles': [
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'similarity': 0.44, 'score': 0.44},
                {'label': 'Dancehall Pop', 'family': 'Pop', 'similarity': 0.43, 'score': 0.43},
                {'label': 'Pop', 'family': 'Pop', 'similarity': 0.35, 'score': 0.35},
            ],
            'families': [{'label': 'R&B / Soul / Funk', 'score': 0.44}, {'label': 'Pop', 'score': 0.43}],
            'confidence': {'score': 0.61, 'percent': 61.0, 'level': 'medium', 'is_unknown': False},
            'consensus': {'primary_family': 'R&B / Soul / Funk'},
        }
        expert = expert_fixture(
            [('Reggae---Dancehall', 'Reggae / Caribbean', 0.90)],
            [('Reggae / Caribbean', 0.40), ('R&B / Soul / Funk', 0.05), ('Pop', 0.04)],
        )
        result = fuse_genre_analysis(clap, expert)
        self.assertEqual(result['primary']['label'], 'Neo Soul')
        dancehall_pop = next(item for item in result['ensemble']['styles'] if item['label'] == 'Dancehall Pop')
        self.assertEqual(len(dancehall_pop['neighborhood_support_labels']), 1)

    def test_v36_multi_cue_hard_hybrid_resolves_cyber_trap_over_generic_grime_proxy(self) -> None:
        # THICK/Tachy-style failure shape: Grime wins a broad CLAP wording race,
        # while the audio specialist independently hears Trap + Industrial + Glitch.
        # No TXT or track name is present in the inference fixture.
        clap = {
            'primary': {'label': 'Grime', 'family': 'Hip-Hop / Rap', 'similarity': 0.62, 'score': 0.62},
            'styles': [
                {'label': 'Grime', 'family': 'Hip-Hop / Rap', 'similarity': 0.62, 'score': 0.62},
                {'label': 'Cyber Trap', 'family': 'Hip-Hop / Rap', 'similarity': 0.59, 'score': 0.59},
                {'label': 'Industrial Hip-Hop', 'family': 'Hip-Hop / Rap', 'similarity': 0.57, 'score': 0.57},
                {'label': 'Glitch Hop', 'family': 'Hip-Hop / Rap', 'similarity': 0.55, 'score': 0.55},
                {'label': 'Trap', 'family': 'Hip-Hop / Rap', 'similarity': 0.52, 'score': 0.52},
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'similarity': 0.40, 'score': 0.40},
            ],
            'families': [{'label': 'Hip-Hop / Rap', 'score': 0.62}, {'label': 'R&B / Soul / Funk', 'score': 0.40}],
            'confidence': {'score': 0.64, 'percent': 64.0, 'level': 'medium', 'is_unknown': False},
            'consensus': {'primary_family': 'Hip-Hop / Rap'},
        }
        expert = expert_fixture(
            [
                ('Hip Hop---Trap', 'Hip-Hop / Rap', 0.72),
                ('Electronic---Industrial', 'Electronic', 0.64),
                ('Electronic---Glitch', 'Electronic', 0.58),
                ('Electronic---Dubstep', 'Electronic', 0.20),
                ('Hip Hop---Grime', 'Hip-Hop / Rap', 0.08),
            ],
            [('Hip-Hop / Rap', 0.35), ('Electronic', 0.33), ('R&B / Soul / Funk', 0.04)],
        )
        result = fuse_genre_analysis(clap, expert)
        self.assertEqual(result['primary']['label'], 'Cyber Trap')
        self.assertEqual(result['dimensions']['style']['primary']['label'], 'Cyber Trap')
        self.assertEqual(result['dimensions']['family']['label'], 'Hip-Hop / Rap')
        self.assertEqual(result['primary']['decision'], 'hard-hybrid-specificity-overrode-generic-rap-proxy')
        cyber = next(item for item in result['ensemble']['styles'] if item['label'] == 'Cyber Trap')
        self.assertGreaterEqual(cyber['discogs_neighborhood_support'], 0.40)
        self.assertGreaterEqual(len(cyber['neighborhood_support_labels']), 2)

    def test_v36_real_grime_direct_agreement_blocks_hard_hybrid_override(self) -> None:
        clap = {
            'primary': {'label': 'Grime', 'family': 'Hip-Hop / Rap', 'similarity': 0.62, 'score': 0.62},
            'styles': [
                {'label': 'Grime', 'family': 'Hip-Hop / Rap', 'similarity': 0.62, 'score': 0.62},
                {'label': 'Cyber Trap', 'family': 'Hip-Hop / Rap', 'similarity': 0.60, 'score': 0.60},
                {'label': 'Industrial Hip-Hop', 'family': 'Hip-Hop / Rap', 'similarity': 0.58, 'score': 0.58},
                {'label': 'Trap', 'family': 'Hip-Hop / Rap', 'similarity': 0.55, 'score': 0.55},
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'similarity': 0.40, 'score': 0.40},
            ],
            'families': [{'label': 'Hip-Hop / Rap', 'score': 0.62}],
            'confidence': {'score': 0.64, 'percent': 64.0, 'level': 'medium', 'is_unknown': False},
            'consensus': {'primary_family': 'Hip-Hop / Rap'},
        }
        expert = expert_fixture(
            [
                ('Hip Hop---Grime', 'Hip-Hop / Rap', 0.68),
                ('Hip Hop---Trap', 'Hip-Hop / Rap', 0.60),
                ('Electronic---Industrial', 'Electronic', 0.55),
                ('Electronic---Glitch', 'Electronic', 0.45),
            ],
            [('Hip-Hop / Rap', 0.41), ('Electronic', 0.24)],
        )
        result = fuse_genre_analysis(clap, expert)
        self.assertEqual(result['primary']['label'], 'Grime')
        grime = next(item for item in result['ensemble']['styles'] if item['label'] == 'Grime')
        self.assertGreaterEqual(grime['discogs_direct_match'], 0.30)
        self.assertNotEqual(result['primary']['decision'], 'hard-hybrid-specificity-overrode-generic-rap-proxy')

    def test_direct_trap_agreement_boosts_confidence(self) -> None:
        clap = clap_fixture('Trap', 'Hip-Hop / Rap', 0.58)
        expert = expert_fixture(
            [('Hip Hop---Trap', 'Hip-Hop / Rap', 0.67), ('Hip Hop---Boom Bap', 'Hip-Hop / Rap', 0.21)],
            [('Hip-Hop / Rap', 0.39), ('Electronic', 0.09)],
        )
        result = fuse_genre_analysis(clap, expert)
        self.assertEqual(result['primary']['label'], 'Trap')
        self.assertGreater(result['confidence']['score'], 0.58)
        self.assertEqual(result['ensemble']['status'], 'ready')

    def test_strong_unrelated_expert_family_reduces_confidence(self) -> None:
        clap = clap_fixture('Contemporary R&B', 'R&B / Soul / Funk', 0.53)
        expert = expert_fixture(
            [('Rock---Heavy Metal', 'Rock / Metal', 0.71), ('Rock---Hard Rock', 'Rock / Metal', 0.61)],
            [('Rock / Metal', 0.42), ('R&B / Soul / Funk', 0.04)],
        )
        result = fuse_genre_analysis(clap, expert)
        self.assertLess(result['confidence']['score'], 0.53)
        self.assertTrue(result['confidence']['expert_family_conflict'])

    def test_unavailable_expert_is_fail_safe(self) -> None:
        clap = clap_fixture('Trap', 'Hip-Hop / Rap', 0.58)
        result = fuse_genre_analysis(clap, {'status': 'unavailable', 'error': 'fixture'})
        self.assertEqual(result['primary']['label'], 'Trap')
        self.assertEqual(result['ensemble']['status'], 'clap-only')


if __name__ == '__main__':
    unittest.main()
