from __future__ import annotations

import unittest

from app.ffmpeg_analysis import (
    _parse_ebur128_summary,
    _parse_loudnorm_payload,
    _unavailable_loudness,
)


class FfmpegAnalysisParsingTests(unittest.TestCase):
    def test_loudnorm_parser_ignores_noise_and_unrelated_json(self) -> None:
        stderr = r'''
ffmpeg banner noise
{"status":"not-the-measurement"}
[Parsed_loudnorm_0 @ 000001]
{
    "input_tp" : "-0.71",
    "input_i" : "-12.04",
    "input_thresh" : "-22.30",
    "input_lra" : "6.20",
    "target_offset" : "-0.10",
    "normalization_type" : "dynamic"
}
more noise
'''
        payload = _parse_loudnorm_payload('', stderr)
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload['input_i'], '-12.04')
        self.assertEqual(payload['input_tp'], '-0.71')

    def test_loudnorm_parser_returns_none_without_measurement_object(self) -> None:
        self.assertIsNone(_parse_loudnorm_payload('{"input_i":"-12"}', 'no useful object'))

    def test_ebur128_summary_parser_recovers_integrated_lra_threshold_and_peak(self) -> None:
        stderr = '''
[Parsed_ebur128_0 @ 000001] Summary:

  Integrated loudness:
    I:         -13.4 LUFS
    Threshold: -23.7 LUFS

  Loudness range:
    LRA:         7.1 LU
    Threshold: -33.8 LUFS
    LRA low:   -17.5 LUFS
    LRA high:  -10.4 LUFS

  True peak:
    Peak:       -0.8 dBFS
'''
        payload = _parse_ebur128_summary(stderr)
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload['integrated_lufs'], -13.4)
        self.assertEqual(payload['loudness_range_lu'], 7.1)
        self.assertEqual(payload['relative_threshold_lufs'], -23.7)
        self.assertEqual(payload['true_peak_dbtp'], -0.8)
        self.assertEqual(payload['provenance'], 'measured-ebur128-fallback')

    def test_unavailable_loudness_keeps_contract_shape(self) -> None:
        payload = _unavailable_loudness('fixture failure')
        self.assertEqual(payload['provenance'], 'unavailable')
        self.assertEqual(payload['error'], 'fixture failure')
        self.assertIsNone(payload['integrated_lufs'])
        self.assertIsNone(payload['true_peak_dbtp'])


if __name__ == '__main__':
    unittest.main()
