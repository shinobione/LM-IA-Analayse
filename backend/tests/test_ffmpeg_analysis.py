from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from app.ffmpeg_analysis import (
    _measurement_env,
    _parse_astats_levels,
    _parse_ebur128_summary,
    _parse_loudnorm_payload,
    _unavailable_loudness,
    analyze_levels,
    analyze_loudness,
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

    def test_astats_parser_uses_final_overall_rms_and_peak(self) -> None:
        stderr = '''
[Parsed_astats_0 @ 1] RMS level dB: -15.8
[Parsed_astats_0 @ 1] Peak level dB: -1.2
[Parsed_astats_0 @ 1] RMS level dB: -14.6
[Parsed_astats_0 @ 1] Peak level dB: -0.7
'''
        payload = _parse_astats_levels(stderr)
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload['mean_volume_db'], -14.6)
        self.assertEqual(payload['max_volume_db'], -0.7)
        self.assertEqual(payload['provenance'], 'measured-astats-fallback')

    def test_measurement_env_forces_plain_ffmpeg_logs(self) -> None:
        env = _measurement_env()
        self.assertEqual(env['AV_LOG_FORCE_NOCOLOR'], '1')
        self.assertNotIn('AV_LOG_FORCE_COLOR', env)

    def test_loudnorm_measurement_can_be_parsed_from_stdout(self) -> None:
        proc = subprocess.CompletedProcess(
            ['ffmpeg'],
            0,
            stdout='''{
  "input_i" : "-12.8",
  "input_tp" : "-0.4",
  "input_lra" : "4.2",
  "input_thresh" : "-22.1"
}''',
            stderr='',
        )
        with patch('app.ffmpeg_analysis._run_ffmpeg', return_value=proc):
            payload = analyze_loudness(Path('fixture.wav'))
        self.assertEqual(payload['integrated_lufs'], -12.8)
        self.assertEqual(payload['true_peak_dbtp'], -0.4)
        self.assertEqual(payload['provenance'], 'measured-loudnorm-json')

    def test_volumedetect_measurement_can_be_parsed_from_stdout(self) -> None:
        proc = subprocess.CompletedProcess(
            ['ffmpeg'],
            0,
            stdout='[Parsed_volumedetect_0] mean_volume: -15.2 dB\n[Parsed_volumedetect_0] max_volume: -0.7 dB',
            stderr='',
        )
        with patch('app.ffmpeg_analysis._run_ffmpeg', return_value=proc):
            payload = analyze_levels(Path('fixture.wav'))
        self.assertEqual(payload['mean_volume_db'], -15.2)
        self.assertEqual(payload['max_volume_db'], -0.7)
        self.assertEqual(payload['provenance'], 'measured')

    def test_loudnorm_timeout_still_attempts_ebur128(self) -> None:
        fallback = {
            'integrated_lufs': -13.2,
            'loudness_range_lu': 5.1,
            'true_peak_dbtp': -0.6,
            'relative_threshold_lufs': -23.0,
            'target_offset_lu': None,
            'normalization_type': 'measurement-only-fallback',
            'provenance': 'measured-ebur128-fallback',
            'standard': 'EBU R128 via FFmpeg ebur128 fallback',
        }
        with patch('app.ffmpeg_analysis._run_ffmpeg', side_effect=subprocess.TimeoutExpired(cmd='ffmpeg', timeout=180)), patch(
            'app.ffmpeg_analysis._analyze_loudness_ebur128', return_value=fallback.copy()
        ):
            payload = analyze_loudness(Path('fixture.wav'))
        self.assertEqual(payload['integrated_lufs'], -13.2)
        self.assertEqual(payload['provenance'], 'measured-ebur128-fallback')
        self.assertIn('loudnorm execution failed', payload['fallback_reason'])

    def test_volumedetect_timeout_still_attempts_astats(self) -> None:
        fallback = {
            'mean_volume_db': -15.1,
            'max_volume_db': -0.5,
            'provenance': 'measured-astats-fallback',
        }
        with patch('app.ffmpeg_analysis._run_ffmpeg', side_effect=subprocess.TimeoutExpired(cmd='ffmpeg', timeout=180)), patch(
            'app.ffmpeg_analysis._analyze_levels_astats', return_value=fallback.copy()
        ):
            payload = analyze_levels(Path('fixture.wav'))
        self.assertEqual(payload['mean_volume_db'], -15.1)
        self.assertEqual(payload['max_volume_db'], -0.5)
        self.assertEqual(payload['provenance'], 'measured-astats-fallback')
        self.assertIn('volumedetect execution failed', payload['fallback_reason'])

    def test_unavailable_loudness_keeps_contract_shape(self) -> None:
        payload = _unavailable_loudness('fixture failure')
        self.assertEqual(payload['provenance'], 'unavailable')
        self.assertEqual(payload['error'], 'fixture failure')
        self.assertIsNone(payload['integrated_lufs'])
        self.assertIsNone(payload['true_peak_dbtp'])


if __name__ == '__main__':
    unittest.main()
