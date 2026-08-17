from __future__ import annotations

import unittest

from app.genre_dimensions import attach_genre_dimensions


class GenreDimensionsV354RuntimeTests(unittest.TestCase):
    def test_real_tinh_bolero_uses_final_ensemble_cluster_not_weaker_raw_clap(self) -> None:
        analysis = {
            'primary': {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'score': 0.62},
            # Deliberately weaker raw CLAP family evidence: this stage alone must
            # NOT be mistaken for the user-visible final evidence.
            'styles': [
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'score': 0.62},
                {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.35},
                {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.31},
                {'label': 'Country', 'family': 'Country / Acoustic', 'score': 0.30},
                {'label': 'Vietnamese Bolero', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.24},
            ],
            # Exact real-user displayed ensemble pattern from Tinh Bolero Cho Trân.
            'ensemble': {
                'status': 'ready',
                'primary': {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'ensemble_score': 0.56},
                'styles': [
                    {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'ensemble_score': 0.56},
                    {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.46},
                    {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.41},
                    {'label': 'Country', 'family': 'Country / Acoustic', 'ensemble_score': 0.35},
                    {
                        'label': 'Vietnamese Bolero',
                        'family': 'Vietnamese / Asian',
                        'region': 'Vietnam',
                        'ensemble_score': 0.32,
                        'structural_support_labels': ['Pop---Ballad'],
                        'regional_coherence': {'status': 'plausible'},
                    },
                ],
            },
            'consensus': {'primary_family': 'R&B / Soul / Funk'},
        }

        dims = attach_genre_dimensions(analysis)['dimensions']
        cluster = dims['coherence']['family_cluster']
        self.assertEqual(dims['coherence']['version'], '3.5.4')
        self.assertEqual(cluster['source'], 'ensemble-style-evidence')
        self.assertEqual(cluster['status'], 'authoritative')
        self.assertEqual(cluster['family'], 'Vietnamese / Asian')
        self.assertAlmostEqual(cluster['score'], 0.7815, places=4)
        self.assertAlmostEqual(cluster['margin'], 0.2215, places=4)
        self.assertEqual(dims['family']['label'], 'Vietnamese / Asian')
        self.assertEqual(dims['style']['primary']['label'], 'Vietnamese Bolero')
        self.assertEqual(dims['tradition']['primary']['label'], 'Nhạc Vàng')
        self.assertEqual(dims['form']['primary']['label'], 'Sentimental Ballad')
        self.assertEqual(dims['region']['label'], 'Vietnam')
        self.assertEqual(dims['coherence']['family_lock']['status'], 'evidence-cluster-authority')

    def test_real_stick_to_you_pop_cluster_remains_authoritative_on_same_stage(self) -> None:
        analysis = {
            'primary': {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'score': 0.52},
            'styles': [
                {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.52},
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'score': 0.45},
                {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.39},
                {'label': 'Eurodance', 'family': 'Pop', 'score': 0.37},
                {'label': 'Dancehall Pop', 'family': 'Pop', 'score': 0.35},
                {'label': 'Vietnamese Bolero', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.28},
            ],
            # Real-user V3.5 result: final ensemble clearly converges on Pop.
            'ensemble': {
                'status': 'ready',
                'primary': {'label': 'Eurodance', 'family': 'Pop', 'ensemble_score': 0.61},
                'styles': [
                    {'label': 'Eurodance', 'family': 'Pop', 'ensemble_score': 0.61},
                    {'label': 'Dancehall Pop', 'family': 'Pop', 'ensemble_score': 0.48},
                    {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.38},
                    {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.30},
                    {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'ensemble_score': 0.29},
                    {
                        'label': 'Vietnamese Bolero',
                        'family': 'Vietnamese / Asian',
                        'region': 'Vietnam',
                        'ensemble_score': 0.24,
                        'structural_support_labels': ['Pop---Ballad'],
                        'regional_coherence': {'status': 'plausible'},
                    },
                ],
            },
            'consensus': {'primary_family': 'Pop'},
        }

        dims = attach_genre_dimensions(analysis)['dimensions']
        cluster = dims['coherence']['family_cluster']
        self.assertEqual(cluster['source'], 'ensemble-style-evidence')
        self.assertEqual(cluster['status'], 'authoritative')
        self.assertEqual(cluster['family'], 'Pop')
        self.assertEqual(dims['family']['label'], 'Pop')
        self.assertEqual(dims['style']['primary']['label'], 'Eurodance')
        self.assertIsNone(dims['tradition']['primary'])
        self.assertIsNone(dims['form']['primary'])
        self.assertIsNone(dims['region']['label'])

    def test_raw_clap_is_still_used_when_ensemble_is_unavailable(self) -> None:
        analysis = {
            'primary': {'label': 'Vietnamese Bolero', 'family': 'Vietnamese / Asian', 'score': 0.61},
            'styles': [
                {'label': 'Vietnamese Bolero', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.61},
                {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.55},
                {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.49},
            ],
            'ensemble': {'status': 'unavailable'},
        }
        dims = attach_genre_dimensions(analysis)['dimensions']
        self.assertEqual(dims['coherence']['family_cluster']['source'], 'raw-audio-style-evidence')
        self.assertEqual(dims['family']['label'], 'Vietnamese / Asian')


if __name__ == '__main__':
    unittest.main()
