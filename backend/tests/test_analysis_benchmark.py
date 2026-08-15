from __future__ import annotations

import unittest

from app.analysis_benchmark import evaluate_genre_reference, summarize_benchmark


REFERENCE = {
    'trackId': 'tinh-bolero-cho-tran',
    'expectedPrimaryStyle': 'Vietnamese Bolero',
    'expectedFamily': 'Vietnamese / Asian',
    'forbiddenPrimaryStyles': ['Contemporary R&B', 'Soul'],
}


class AnalysisBenchmarkTests(unittest.TestCase):
    def test_artist_confirmed_bolero_case_passes(self) -> None:
        analysis = {
            'primary': {'label': 'Vietnamese Bolero'},
            'consensus': {'primary_family': 'Vietnamese / Asian'},
            'confidence': {'level': 'high', 'percent': 84.0},
        }
        result = evaluate_genre_reference(REFERENCE, analysis)
        self.assertTrue(result['passed'])
        self.assertTrue(all(result['checks'].values()))

    def test_v32_can_keep_nhac_vang_as_raw_context_but_bolero_as_style(self) -> None:
        analysis = {
            'primary': {'label': 'Nhạc Vàng', 'family': 'Vietnamese / Asian'},
            'consensus': {'primary_family': 'Vietnamese / Asian'},
            'dimensions': {
                'version': '3.2',
                'unknown': False,
                'family': {'label': 'Vietnamese / Asian'},
                'style': {'primary': {'label': 'Vietnamese Bolero'}},
                'tradition': {'primary': {'label': 'Nhạc Vàng'}},
            },
            'confidence': {'level': 'high', 'percent': 78.0},
        }
        result = evaluate_genre_reference(REFERENCE, analysis)
        self.assertTrue(result['passed'])
        self.assertTrue(all(result['checks'].values()))
        self.assertEqual(result['actual']['primaryStyle'], 'Vietnamese Bolero')
        self.assertEqual(result['actual']['rawPrimaryLabel'], 'Nhạc Vàng')
        self.assertEqual(result['actual']['dimensionVersion'], '3.2')

    def test_old_rnb_failure_mode_is_rejected(self) -> None:
        analysis = {
            'primary': {'label': 'Contemporary R&B'},
            'consensus': {'primary_family': 'R&B / Soul / Funk'},
            'confidence': {'level': 'medium', 'percent': 61.0},
        }
        result = evaluate_genre_reference(REFERENCE, analysis)
        self.assertFalse(result['passed'])
        self.assertFalse(result['checks']['primary_style'])
        self.assertFalse(result['checks']['not_forbidden'])

    def test_unknown_is_honest_but_does_not_pass_strict_reference(self) -> None:
        analysis = {
            'primary': {'label': 'Unknown / hybrid', 'candidate': {'label': 'Vietnamese Bolero'}},
            'consensus': {'primary_family': 'Vietnamese / Asian'},
            'confidence': {'level': 'low', 'percent': 31.0},
        }
        result = evaluate_genre_reference(REFERENCE, analysis)
        self.assertFalse(result['passed'])
        self.assertFalse(result['checks']['not_unknown'])
        self.assertTrue(result['checks']['not_forbidden'])

    def test_unknown_dimension_still_fails_strict_reference(self) -> None:
        analysis = {
            'primary': {'label': 'Unknown / hybrid', 'candidate': {'label': 'Vietnamese Bolero'}},
            'consensus': {'primary_family': 'Vietnamese / Asian'},
            'dimensions': {
                'version': '3.2',
                'unknown': True,
                'family': {'label': 'Vietnamese / Asian'},
                'style': {'primary': {'label': 'Vietnamese Bolero', 'authority': 'evidence-only'}},
            },
            'confidence': {'level': 'low', 'percent': 31.0},
        }
        result = evaluate_genre_reference(REFERENCE, analysis)
        self.assertFalse(result['passed'])
        self.assertTrue(result['checks']['primary_style'])
        self.assertFalse(result['checks']['not_unknown'])

    def test_summary_marks_missing_analysis_as_failure(self) -> None:
        result = summarize_benchmark({'name': 'fixture', 'tracks': [REFERENCE]}, {})
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['passed'], 0)
        self.assertEqual(result['passPercent'], 0.0)


if __name__ == '__main__':
    unittest.main()
