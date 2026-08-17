from __future__ import annotations

import unittest

import runtime_manager


class RuntimeManagerTests(unittest.TestCase):
    def test_windows_netstat_listener_parser_targets_only_requested_port(self) -> None:
        sample = """
  TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING       4242
  TCP    127.0.0.1:8001         0.0.0.0:0              LISTENING       5151
  TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       4343
  TCP    [::1]:8008             [::]:0                 LISTENING       6262
  TCP    127.0.0.1:8000         127.0.0.1:53000        ESTABLISHED     4242
"""
        self.assertEqual(runtime_manager._parse_windows_netstat_listeners(sample, 8000), {4242, 4343})
        self.assertEqual(runtime_manager._parse_windows_netstat_listeners(sample, 8008), {6262})
        self.assertEqual(runtime_manager._parse_windows_netstat_listeners(sample, 8001), {5151})
        self.assertEqual(runtime_manager._parse_windows_netstat_listeners(sample, 9000), set())


if __name__ == "__main__":
    unittest.main()
