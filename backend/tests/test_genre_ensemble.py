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
