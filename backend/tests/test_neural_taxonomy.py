from __future__ import annotations

import unittest

from app.neural_taxonomy import GENRE_CANDIDATES, TAXONOMY_VERSION, confidence_policy, families


class NeuralTaxonomyTests(unittest.TestCase):
    def test_vietnamese_bolero_is_first_class_and_not_latin_bolero(self) -> None:
        by_label = {candidate.label: candidate for candidate in GENRE_CANDIDATES}
        self.assertIn('Vietnamese Bolero', by_label)
        self.assertIn('Latin Bolero', by_label)
        self.assertEqual(by_label['Vietnamese Bolero'].region, 'Vietnam')
        self.assertEqual(by_label['Vietnamese Bolero'].family, 'Vietnamese / Asian')
        self.assertEqual(by_label['Latin Bolero'].family, 'Latin')
        self.assertNotEqual(by_label['Vietnamese Bolero'].prompts, by_label['Latin Bolero'].prompts)
        joined = ' '.join(by_label['Vietnamese Bolero'].prompts).lower()
        self.assertIn('nhạc vàng', joined)
        self.assertIn('nhạc trữ tình', joined)

    def test_taxonomy_is_materially_broader_than_v2_closed_list(self) -> None:
        self.assertTrue(TAXONOMY_VERSION.startswith('3.0-'))
        self.assertGreaterEqual(len(GENRE_CANDIDATES), 90)
        self.assertGreaterEqual(len(families()), 10)

    def test_confidence_can_return_unknown_instead_of_forcing_a_genre(self) -> None:
        result = confidence_policy(
            primary_similarity=0.08,
            second_similarity=0.075,
            style_consensus=0.20,
            family_consensus=0.40,
        )
        self.assertTrue(result['is_unknown'])
        self.assertEqual(result['level'], 'low')
        self.assertTrue(result['reasons'])

    def test_stable_segment_consensus_can_produce_high_confidence(self) -> None:
        result = confidence_policy(
            primary_similarity=0.31,
            second_similarity=0.23,
            style_consensus=1.0,
            family_consensus=1.0,
        )
        self.assertFalse(result['is_unknown'])
        self.assertEqual(result['level'], 'high')
        self.assertGreaterEqual(result['score'], 0.72)


if __name__ == '__main__':
    unittest.main()
