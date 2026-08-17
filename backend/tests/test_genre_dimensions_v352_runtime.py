from __future__ import annotations

import unittest

from app.genre_dimensions import attach_genre_dimensions


class GenreDimensionsV355RuntimeTests(unittest.TestCase):
    def test_real_tinh_bolero_contextual_tradition_primary_resolves_style(self) -> None:
        analysis = {
            # Real CLAP payload captured from the user's scan.
            'primary': {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.535},
            'styles': [
                {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.535},
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'score': 0.524},
                {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.521},
                {'label': 'Vietnamese Bolero', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.488},
                {'label': 'Country', 'family': 'Country / Acoustic', 'score': 0.471},
                {'label': 'Classical', 'family': 'Classical / Screen', 'score': 0.423},
            ],
            # Real CLAP + Discogs payload captured in the diagnostic panel.
            # Neo Soul is the largest individual style score, but the ensemble
            # primary remains Nhạc Vàng (kept-clap-primary), which is a tradition.
            'ensemble': {
                'status': 'ready',
                'primary': {
                    'label': 'Nhạc Vàng',
                    'family': 'Vietnamese / Asian',
                    'region': 'Vietnam',
                    'ensemble_score': 0.456,
                },
                'decision': 'kept-clap-primary',
                'styles': [
                    {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'ensemble_score': 0.556},
                    {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.456},
                    {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.408},
                    {'label': 'Country', 'family': 'Country / Acoustic', 'ensemble_score': 0.354},
                    {
                        'label': 'Vietnamese Bolero',
                        'family': 'Vietnamese / Asian',
                        'region': 'Vietnam',
                        'ensemble_score': 0.319,
                        'structural_support_labels': ['Pop---Ballad'],
                        'regional_coherence': {'status': 'plausible'},
                    },
                    {'label': 'Classical', 'family': 'Classical / Screen', 'ensemble_score': 0.191},
                    # Hidden below the visible top rows in the real UI. This
                    # reproduces the diagnostic runner-up R&B cluster at ~64.9%,
                    # keeping the family margin below the old 18% cross-family
                    # semantic-override threshold.
                    {'label': 'Contemporary R&B', 'family': 'R&B / Soul / Funk', 'ensemble_score': 0.169},
                ],
            },
            'consensus': {'primary_family': 'R&B / Soul / Funk'},
        }

        dims = attach_genre_dimensions(analysis)['dimensions']
        cluster = dims['coherence']['family_cluster']
        self.assertEqual(dims['coherence']['version'], '3.5.5')
        self.assertEqual(cluster['source'], 'ensemble-style-evidence')
        self.assertEqual(cluster['status'], 'authoritative')
        self.assertEqual(cluster['family'], 'Vietnamese / Asian')
        self.assertAlmostEqual(cluster['score'], 0.7761, places=4)
        self.assertAlmostEqual(cluster['runner_up_score'], 0.64895, places=4)
        self.assertAlmostEqual(cluster['margin'], 0.12715, places=4)
        self.assertLess(cluster['margin'], 0.18)
        self.assertEqual(dims['family']['label'], 'Vietnamese / Asian')
        self.assertEqual(dims['style']['primary']['label'], 'Vietnamese Bolero')
        self.assertEqual(dims['tradition']['primary']['label'], 'Nhạc Vàng')
        self.assertEqual(dims['form']['primary']['label'], 'Sentimental Ballad')
        self.assertEqual(dims['region']['label'], 'Vietnam')
        self.assertEqual(dims['coherence']['family_lock']['status'], 'contextual-tradition-cluster-authority')

    def test_regional_form_primary_still_cannot_manufacture_vietnamese_bolero(self) -> None:
        analysis = {
            'primary': {
                'label': 'Vietnamese Pop Ballad',
                'family': 'Vietnamese / Asian',
                'region': 'Vietnam',
                'score': 0.47,
            },
            'styles': [
                {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.47},
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'score': 0.42},
                {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.39},
                {'label': 'Country', 'family': 'Country / Acoustic', 'score': 0.38},
                {'label': 'Pop', 'family': 'Pop', 'score': 0.36},
                {'label': 'Vietnamese Bolero', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.34},
            ],
            'ensemble': {
                'status': 'ready',
                'primary': {
                    'label': 'Vietnamese Pop Ballad',
                    'family': 'Vietnamese / Asian',
                    'region': 'Vietnam',
                    'ensemble_score': 0.47,
                },
                'styles': [
                    {
                        'label': 'Vietnamese Pop Ballad',
                        'family': 'Vietnamese / Asian',
                        'region': 'Vietnam',
                        'ensemble_score': 0.47,
                        'structural_support_labels': ['Pop---Ballad'],
                        'regional_coherence': {'status': 'supported'},
                    },
                    {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'ensemble_score': 0.42},
                    {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.39},
                    {'label': 'Country', 'family': 'Country / Acoustic', 'ensemble_score': 0.38},
                    {'label': 'Pop', 'family': 'Pop', 'ensemble_score': 0.36},
                    {
                        'label': 'Vietnamese Bolero',
                        'family': 'Vietnamese / Asian',
                        'region': 'Vietnam',
                        'ensemble_score': 0.34,
                        'structural_support_labels': ['Pop---Ballad'],
                        'regional_coherence': {'status': 'supported'},
                    },
                ],
            },
            'consensus': {'primary_family': 'Vietnamese / Asian'},
        }

        dims = attach_genre_dimensions(analysis)['dimensions']
        self.assertEqual(dims['coherence']['family_cluster']['status'], 'authoritative')
        self.assertEqual(dims['coherence']['family_cluster']['family'], 'Vietnamese / Asian')
        self.assertEqual(dims['style']['primary']['label'], 'Neo Soul')
        self.assertEqual(dims['family']['label'], 'R&B / Soul / Funk')
        self.assertNotEqual(dims['style']['primary']['label'], 'Vietnamese Bolero')
        self.assertEqual(dims['coherence']['family_lock']['status'], 'released')

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
