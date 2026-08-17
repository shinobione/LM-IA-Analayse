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

    def test_v35_adds_first_class_hybrid_dance_pop_styles(self) -> None:
        by_label = {candidate.label: candidate for candidate in GENRE_CANDIDATES}
        self.assertTrue(TAXONOMY_VERSION.startswith('3.6-'))
        self.assertIn('Dancehall Pop', by_label)
        self.assertIn('Eurodance', by_label)
        self.assertIn('Euro-House', by_label)
        self.assertIn('Afropop', by_label)
        self.assertEqual(by_label['Dancehall Pop'].family, 'Pop')
        self.assertEqual(by_label['Euro-House'].family, 'Electronic')
        self.assertEqual(by_label['Afropop'].region, 'Africa')
        dancehall_pop_prompts = ' '.join(by_label['Dancehall Pop'].prompts).lower()
        self.assertIn('dancehall', dancehall_pop_prompts)
        self.assertIn('pop', dancehall_pop_prompts)
        self.assertIn('caribbean', dancehall_pop_prompts)
        neo_soul_prompts = ' '.join(by_label['Neo Soul'].prompts).lower()
        self.assertIn('harmony', neo_soul_prompts)
        self.assertIn('groove', neo_soul_prompts)

    def test_v36_adds_hard_hybrid_styles_and_narrows_grime(self) -> None:
        by_label = {candidate.label: candidate for candidate in GENRE_CANDIDATES}
        for label in ('Cyber Trap', 'Industrial Hip-Hop', 'Glitch Hop', 'Drift Phonk', 'Electronic Drill'):
            self.assertIn(label, by_label)
            self.assertEqual(by_label[label].family, 'Hip-Hop / Rap')
            self.assertGreaterEqual(len(by_label[label].prompts), 3)

        grime = ' '.join(by_label['Grime'].prompts).lower()
        self.assertIn('uk grime', grime)
        self.assertIn('east london', grime)
        self.assertIn('british', grime)
        self.assertNotIn('grime rap with electronic beats', grime)

        cyber = ' '.join(by_label['Cyber Trap'].prompts).lower()
        self.assertIn('industrial', cyber)
        self.assertIn('glitch', cyber)
        self.assertIn('808', cyber)

    def test_taxonomy_is_materially_broader_than_v2_closed_list(self) -> None:
        self.assertTrue(TAXONOMY_VERSION.startswith('3.6-'))
        self.assertGreaterEqual(len(GENRE_CANDIDATES), 99)
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
