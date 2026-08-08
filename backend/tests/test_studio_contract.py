from __future__ import annotations

import unittest
import ast
from pathlib import Path

from app.studio_contract import build_analysis_envelope, parse_source_version, parse_track_id


class StudioContractTests(unittest.TestCase):
    def test_entrypoint_declares_studio_route(self) -> None:
        entrypoint = Path(__file__).resolve().parents[1] / 'app' / 'entrypoint.py'
        tree = ast.parse(entrypoint.read_text(encoding='utf-8'))
        routes = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and decorator.args and isinstance(decorator.args[0], ast.Constant):
                    routes.append(decorator.args[0].value)
        self.assertIn('/api/studio/analyze', routes)

    def test_canonical_track_id(self) -> None:
        self.assertEqual(parse_track_id('ghost-signal'), 'ghost-signal')
        with self.assertRaises(ValueError):
            parse_track_id('Ghost Signal')

    def test_source_version_is_explicit(self) -> None:
        source = parse_source_version('{"kind":"r2-etag","value":"abc","sizeBytes":42,"filename":"audio.wav"}')
        self.assertEqual(source['value'], 'abc')
        self.assertEqual(source['sizeBytes'], 42)

    def test_envelope_keeps_512d_embedding_and_no_audio(self) -> None:
        neural = {'embedding': {'model': 'clap', 'dimension': 512, 'vector': [0.0] * 512}}
        result = build_analysis_envelope(
            track_id='ghost-signal',
            source_version={'kind': 'r2-etag', 'value': 'abc', 'sizeBytes': 42},
            engine_version={'apiSchema': '2.2'},
            mastering={},
            neural=neural,
            structure={},
            stems_summary=None,
            provenance={},
            warnings=[],
        )
        self.assertEqual(result['trackId'], 'ghost-signal')
        self.assertEqual(result['embedding']['dimension'], 512)
        self.assertFalse(result['privacy']['audioStored'])
        self.assertTrue(result['analysisId'].startswith('sta-'))


if __name__ == '__main__':
    unittest.main()
