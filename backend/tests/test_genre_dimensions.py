from __future__ import annotations

import unittest

from app.genre_dimensions import attach_genre_dimensions


class GenreDimensionsTests(unittest.TestCase):
    def test_vietnamese_bolero_separates_style_tradition_and_form(self) -> None:
        analysis = {
            'version': '3.1',
            'primary': {
                'label': 'Nhạc Vàng',
                'family': 'Vietnamese / Asian',
                'region': 'Vietnam',
                'score': 0.69,
            },
            'families': [
                {'label': 'Vietnamese / Asian', 'score': 0.69, 'percent': 69.0},
                {'label': 'R&B / Soul / Funk', 'score': 0.48, 'percent': 48.0},
            ],
            'styles': [
                {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.69},
                {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.63},
                {'label': 'Vietnamese Bolero', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.51},
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'region': None, 'score': 0.48},
            ],
            'ensemble': {
                'status': 'ready',
                'primary': {
                    'label': 'Nhạc Vàng',
                    'family': 'Vietnamese / Asian',
                    'region': 'Vietnam',
                    'ensemble_score': 0.69,
                },
                'styles': [
                    {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.69},
                    {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'ensemble_score': 0.63},
                    {
                        'label': 'Vietnamese Bolero',
                        'family': 'Vietnamese / Asian',
                        'region': 'Vietnam',
                        'ensemble_score': 0.51,
                        'structural_support_labels': ['Latin---Bolero', 'Pop---Ballad'],
                        'regional_coherence': {'status': 'supported'},
                    },
                    {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'region': None, 'ensemble_score': 0.48},
                ],
            },
            'consensus': {'primary_family': 'Vietnamese / Asian'},
            'studio_contract': {'mode': 'additive'},
            'provenance': {},
        }

        result = attach_genre_dimensions(analysis)
        dims = result['dimensions']

        self.assertEqual(result['version'], '3.2')
        self.assertEqual(dims['family']['label'], 'Vietnamese / Asian')
        self.assertEqual(dims['style']['primary']['label'], 'Vietnamese Bolero')
        self.assertEqual(dims['tradition']['primary']['label'], 'Nhạc Vàng')
        self.assertEqual(dims['form']['primary']['label'], 'Sentimental Ballad')
        self.assertEqual(dims['form']['primary']['source_label'], 'Vietnamese Pop Ballad')
        self.assertEqual(dims['region']['label'], 'Vietnam')
        self.assertEqual(dims['coherence']['version'], '3.5.5')
        self.assertEqual(dims['coherence']['family_cluster']['source'], 'ensemble-style-evidence')
        self.assertTrue(dims['coherence']['family_cluster']['status'] in {'authoritative', 'insufficient'})
        self.assertTrue(result['studio_contract']['semantic_dimensions_additive'])

        influence_labels = [item['label'] for item in dims['influences']]
        self.assertIn('Neo Soul', influence_labels)
        self.assertNotEqual(dims['style']['primary']['label'], 'Nhạc Vàng')

    def test_generic_trap_remains_a_primary_style(self) -> None:
        analysis = {
            'primary': {'label': 'Trap', 'family': 'Hip-Hop / Rap', 'score': 0.81},
            'styles': [
                {'label': 'Trap', 'family': 'Hip-Hop / Rap', 'score': 0.81},
                {'label': 'Hip-Hop', 'family': 'Hip-Hop / Rap', 'score': 0.67},
                {'label': 'Pop Rap', 'family': 'Hip-Hop / Rap', 'score': 0.54},
            ],
            'consensus': {'primary_family': 'Hip-Hop / Rap'},
        }
        result = attach_genre_dimensions(analysis)
        dims = result['dimensions']
        self.assertEqual(dims['style']['primary']['label'], 'Trap')
        self.assertEqual(dims['family']['label'], 'Hip-Hop / Rap')
        self.assertIsNone(dims['tradition']['primary'])
        self.assertIsNone(dims['form']['primary'])
        self.assertIsNone(dims['region']['label'])

    def test_cross_family_vietnamese_context_is_rejected_for_grime(self) -> None:
        analysis = {
            'primary': {'label': 'Grime', 'family': 'Hip-Hop / Rap', 'score': 0.62},
            'styles': [
                {'label': 'Grime', 'family': 'Hip-Hop / Rap', 'score': 0.62},
                {'label': 'Neo Soul', 'family': 'R&B / Soul / Funk', 'score': 0.51},
                {'label': 'Vietnamese Pop Ballad', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.50},
                {'label': 'Hip-Hop', 'family': 'Hip-Hop / Rap', 'score': 0.49},
                {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.43},
            ],
            'consensus': {'primary_family': 'Hip-Hop / Rap'},
        }
        result = attach_genre_dimensions(analysis)
        dims = result['dimensions']
        self.assertEqual(dims['family']['label'], 'Hip-Hop / Rap')
        self.assertEqual(dims['style']['primary']['label'], 'Grime')
        self.assertIsNone(dims['tradition']['primary'])
        self.assertIsNone(dims['form']['primary'])
        self.assertIsNone(dims['region']['label'])
        rejected = {item['label'] for item in dims['coherence']['rejected_context']}
        self.assertIn('Nhạc Vàng', rejected)
        self.assertIn('Vietnamese Pop Ballad', rejected)

    def test_stick_to_you_regional_form_does_not_manufacture_vietnamese_bolero(self) -> None:
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
        self.assertEqual(dims['style']['primary']['label'], 'Neo Soul')
        self.assertEqual(dims['family']['label'], 'R&B / Soul / Funk')
        self.assertNotEqual(dims['style']['primary']['label'], 'Vietnamese Bolero')
        self.assertIsNone(dims['tradition']['primary'])
        self.assertIsNone(dims['form']['primary'])
        self.assertIsNone(dims['region']['label'])
        self.assertEqual(dims['coherence']['family_lock']['status'], 'released')
        self.assertTrue(dims['coherence']['family_cluster']['style_specific_anchor'] is False)

    def test_v351_fragmented_vietnamese_cluster_restores_real_bolero(self) -> None:
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
                        'structural_support_labels': ['Latin---Bolero', 'Pop---Ballad'],
                        'regional_coherence': {'status': 'supported'},
                    },
                ],
            },
            'consensus': {'primary_family': 'R&B / Soul / Funk'},
        }

        dims = attach_genre_dimensions(analysis)['dimensions']
        self.assertEqual(dims['coherence']['family_cluster']['status'], 'authoritative')
        self.assertEqual(dims['coherence']['family_cluster']['family'], 'Vietnamese / Asian')
        self.assertEqual(dims['family']['label'], 'Vietnamese / Asian')
        self.assertEqual(dims['style']['primary']['label'], 'Vietnamese Bolero')
        self.assertEqual(dims['tradition']['primary']['label'], 'Nhạc Vàng')
        self.assertEqual(dims['form']['primary']['label'], 'Sentimental Ballad')
        self.assertEqual(dims['region']['label'], 'Vietnam')
        self.assertEqual(dims['coherence']['family_lock']['status'], 'evidence-cluster-authority')

    def test_v351_pop_cluster_keeps_real_stick_to_you_out_of_vietnamese_family(self) -> None:
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

    def test_generic_pop_ballad_form_can_cross_into_rnb_without_regional_context(self) -> None:
        analysis = {
            'primary': {'label': 'Alternative R&B', 'family': 'R&B / Soul / Funk', 'score': 0.72},
            'styles': [
                {'label': 'Alternative R&B', 'family': 'R&B / Soul / Funk', 'score': 0.72},
                {'label': 'Pop Ballad', 'family': 'Pop', 'score': 0.55},
            ],
            'consensus': {'primary_family': 'R&B / Soul / Funk'},
        }
        dims = attach_genre_dimensions(analysis)['dimensions']
        self.assertEqual(dims['family']['label'], 'R&B / Soul / Funk')
        self.assertEqual(dims['form']['primary']['label'], 'Ballad')
        self.assertIsNone(dims['region']['label'])

    def test_unknown_keeps_style_as_evidence_only(self) -> None:
        analysis = {
            'primary': {
                'label': 'Unknown / hybrid',
                'candidate': {'label': 'Vietnamese Bolero', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.31},
            },
            'styles': [
                {'label': 'Vietnamese Bolero', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.31},
                {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian', 'region': 'Vietnam', 'score': 0.29},
            ],
            'consensus': {'primary_family': 'Vietnamese / Asian'},
        }
        result = attach_genre_dimensions(analysis)
        dims = result['dimensions']
        self.assertTrue(dims['unknown'])
        self.assertEqual(dims['style']['primary']['label'], 'Vietnamese Bolero')
        self.assertEqual(dims['style']['primary']['authority'], 'evidence-only')


if __name__ == '__main__':
    unittest.main()
