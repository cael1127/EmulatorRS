"""Tests for bundled homebrew demo ROM workloads."""

from __future__ import annotations

import unittest

from emulator.demos import list_demo_roms
from emulator.program_loader import decode_rom
from emulator.system import EmulatorSystem


class DemoRomTests(unittest.TestCase):
    def test_demo_registry_contains_multiple_workloads(self) -> None:
        demos = list_demo_roms()
        self.assertGreaterEqual(len(demos), 7)
        self.assertIn("arithmetic", demos)
        self.assertIn("render_service", demos)
        self.assertIn("perf_loop", demos)
        self.assertIn("visual_demo", demos)
        self.assertIn("input_demo", demos)
        self.assertIn("audio_demo", demos)
        self.assertIn("hle_chain", demos)

    def test_arithmetic_demo_stores_expected_value(self) -> None:
        system = EmulatorSystem()
        program = decode_rom(list_demo_roms()["arithmetic"])
        system.cpu.load_program(program)
        system.cpu.run(use_block_cache=True)
        # address 0x20 -> word index 8
        self.assertEqual(system.bus.memory.dump_words(0, 9)[8], 17)

    def test_render_service_demo_draws_and_logs(self) -> None:
        system = EmulatorSystem()
        program = decode_rom(list_demo_roms()["render_service"])
        system.cpu.load_program(program)
        snapshot = system.cpu.run()
        self.assertTrue(snapshot.halted)
        self.assertEqual(system.renderer.framebuffer[4][6], 11)
        self.assertGreaterEqual(len(system.services.logs), 1)

    def test_perf_loop_demo_runs_deterministically(self) -> None:
        rom = list_demo_roms()["perf_loop"]
        a = EmulatorSystem()
        b = EmulatorSystem()
        pa = decode_rom(rom)
        pb = decode_rom(rom)
        a.cpu.load_program(pa)
        b.cpu.load_program(pb)
        sa = a.cpu.run(use_block_cache=False)
        sb = b.cpu.run(use_block_cache=True)
        self.assertEqual(sa.regs, sb.regs)
        self.assertEqual(sa.cycles, sb.cycles)

    def test_visual_demo_draws_diagonal_strip(self) -> None:
        system = EmulatorSystem()
        program = decode_rom(list_demo_roms()["visual_demo"])
        system.cpu.load_program(program)
        system.cpu.run()
        for k in range(16):
            self.assertEqual(system.renderer.framebuffer[6 + k][8 + k], 40 + k)
        painted = sum(
            1
            for row in system.renderer.framebuffer
            for cell in row
            if cell != 0
        )
        self.assertEqual(painted, 16)

    def test_input_demo_reads_queued_states(self) -> None:
        system = EmulatorSystem()
        system.input.queue_state(0xAA)
        system.input.queue_state(0xBB)
        program = decode_rom(list_demo_roms()["input_demo"])
        system.cpu.load_program(program)
        system.cpu.run()
        words = system.bus.memory.dump_words(0, 6)
        self.assertEqual(words[4], 0xAA)
        self.assertEqual(words[5], 0xBB)

    def test_audio_demo_enqueues_samples(self) -> None:
        system = EmulatorSystem()
        program = decode_rom(list_demo_roms()["audio_demo"])
        system.cpu.load_program(program)
        system.cpu.run()
        self.assertEqual(system.audio.samples, [0x10, 0x20, 0x30])
        self.assertEqual(system.bus.read_u32(system.AUDIO_ADDR), 3)

    def test_hle_chain_demo_stores_and_logs(self) -> None:
        system = EmulatorSystem()
        program = decode_rom(list_demo_roms()["hle_chain"])
        system.cpu.load_program(program)
        system.cpu.run()
        word_idx = 0x20 // 4
        expected = (5 ^ 0x55AA) & 0xFFFF
        self.assertEqual(system.bus.memory.dump_words(0, word_idx + 1)[word_idx], expected)
        self.assertEqual(system.services.logs, [2])


if __name__ == "__main__":
    unittest.main()
