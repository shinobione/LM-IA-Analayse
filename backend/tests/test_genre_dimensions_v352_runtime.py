from __future__ import annotations

import unittest

from app.genre_dimensions import attach_genre_dimensions


class GenreDimensionsV352RuntimeTests(unittest.TestCase):
    def test_real_tinh_bolero_cluster_does_not_require_latin_proxy(self) -> None:
        analysis = {
            'primary': {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'score': 0.56},
            'styles': [
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'score': 0.56},
                {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.46},
                {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.41},
                {'label': 'Country', 'family': 'Country / Acoustic', 'score': 0.35},
                {'label': 'Vietnamese Bolero', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.32},
            ],
            'ensemble': {
                'status': 'ready',
                'primary': {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'ensemble_score': 0.58},
                'styles': [
                    {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'ensemble_score': 0.58},
                    {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.43},
                    {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.39},
                    {'label': 'Country', 'family': 'Country / Acoustic', 'ensemble_score': 0.34},
                    {
                        'label': 'Vietnamese Bolero',
                        'family': 'Vietnamese / Asian',
                        'region': 'Vietnam',
                        'ensemble_score': 0.31,
                        'structural_support_labels': ['Pop---Ballad'],
                        'regional_coherence': {'status': 'plausible'},
                    },
                ],
            },
            'consensus': {'primary_family': 'R&B / Soul / Funk'},
        }

        dims = attach_genre_dimensions(analysis)['dimensions']
        self.assertEqual(dims['coherence']['version'], '3.5.2')
        self.assertEqual(dims['coherence']['family_cluster']['status'], 'authoritative')
        self.assertEqual(dims['coherence']['family_cluster']['family'], 'Vietnamese / Asian')
        self.assertEqual(dims['family']['label'], 'Vietnamese / Asian')
        self.assertEqual(dims['style']['primary']['label'], 'Vietnamese Bolero')
        self.assertEqual(dims['tradition']['primary']['label'], 'Nhạc Vàng')
        self.assertEqual(dims['form']['primary']['label'], 'Sentimental Ballad')
        self.assertEqual(dims['region']['label'], 'Vietnam')
        self.assertEqual(dims['coherence']['family_lock']['status'], 'evidence-cluster-authority')

    def test_real_stick_to_you_pop_cluster_remains_authoritative(self) -> None:
        analysis = {
            'primary': {'label': 'Eurodance', 'family': 'Pop', 'score': 0.61},
            'styles': [
                {'label': 'Eurodance', 'family': 'Pop', 'score': 0.61},
                {'label': 'Dancehall Pop', 'family': 'Pop', 'score': 0.48},
                {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.38},
                {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.30},
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'score': 0.29},
                {'label': 'Vietnamese Bolero', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.24},
            ],
            'ensemble': {
                'status': 'ready',
                'primary': {'label': 'Eurodance', 'family': 'Pop', 'ensemble_score': 0.66},
                'styles': [
                    {'label': 'Eurodance', 'family': 'Pop', 'ensemble_score': 0.66},
                    {'label': 'Dancehall Pop', 'family': 'Pop', 'ensemble_score': 0.52},
                    {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.34},
                    {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.27},
                    {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'ensemble_score': 0.25},
                    {
                        'label': 'Vietnamese Bolero',
                        'family': 'Vietnamese / Asian',
                        'region': 'Vietnam',
                        'ensemble_score': 0.21,
                        'structural_support_labels': ['Pop---Ballad'],
                        'regional_coherence': {'status': 'plausible'},
                    },
                ],
            },
            'consensus': {'primary_family': 'Pop'},
        }

        dims = attach_genre_dimensions(analysis)['dimensions']
        self.assertEqual(dims['coherence']['family_cluster']['status'], 'authoritative')
        self.assertEqual(dims['coherence']['family_cluster']['family'], 'Pop')
        self.assertEqual(dims['family']['label'], 'Pop')
        self.assertEqual(dims['style']['primary']['label'], 'Eurodance')
        self.assertIsNone(dims['tradition']['primary'])
        self.assertIsNone(dims['form']['primary'])
        self.assertIsNone(dims['region']['label'])


if __name__ == '__main__':
    unittest.main()
