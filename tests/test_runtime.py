"""Tests for runtime report helpers."""

from __future__ import annotations

import unittest

from emulator.demos import list_demo_roms
from emulator.runtime import run_rom_bytes, run_rom_session


class RuntimeTests(unittest.TestCase):
    def test_run_report_has_profiler_fields(self) -> None:
        report = run_rom_bytes(list_demo_roms()["arithmetic"], use_block_cache=True)
        data = report.to_dict()
        self.assertTrue(data["halted"])
        self.assertIn("profiler", data)
        self.assertIn("executed_instructions", data["profiler"])
        self.assertIn("block_cache_hits", data["profiler"])
        self.assertIn("audio_sample_count", data)
        self.assertEqual(data["audio_sample_count"], 0)

    def test_run_session_collects_trace(self) -> None:
        trace: list[tuple[int, int, int]] = []
        report, _system = run_rom_session(
            list_demo_roms()["arithmetic"],
            trace_events=trace,
        )
        self.assertTrue(report.halted)
        self.assertGreater(len(trace), 0)
        self.assertEqual(len(trace), report.cycles)


if __name__ == "__main__":
    unittest.main()
