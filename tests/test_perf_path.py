"""Phase 2 tests for block-cache/JIT prototype and invalidation."""

from __future__ import annotations

import unittest

from emulator.core.interfaces import Instruction
from emulator.core.opcodes import Op
from emulator.program_loader import decode_rom, encode_rom
from emulator.system import EmulatorSystem
from tests.harness import run_rom


def i(op: Op, a: int = 0, b: int = 0, c: int = 0) -> Instruction:
    return Instruction(opcode=int(op), a=a, b=b, c=c)


class PerfPathTests(unittest.TestCase):
    def test_block_cache_matches_interpreter_state(self) -> None:
        rom = encode_rom(
            [
                i(Op.MOVI, a=0, c=1),
                i(Op.ADDI, a=0, c=2),
                i(Op.ADDI, a=0, c=3),
                i(Op.ADDI, a=0, c=4),
                i(Op.HALT),
            ]
        )
        interp = run_rom(rom, use_block_cache=False)
        cached = run_rom(rom, use_block_cache=True)
        self.assertEqual(interp.final_regs, cached.final_regs)
        self.assertEqual(interp.cycles, cached.cycles)

    def test_block_cache_records_hits_and_compiles(self) -> None:
        program = decode_rom(
            encode_rom(
                [
                    i(Op.MOVI, a=0, c=1),
                    i(Op.ADDI, a=0, c=1),
                    i(Op.JMP, c=1),
                ]
            )
        )
        system = EmulatorSystem()
        system.cpu.load_program(program)
        with self.assertRaises(RuntimeError):
            # Intentional loop: run budget forces stop.
            system.cpu.run(max_steps=50, use_block_cache=True)
        self.assertGreater(system.cpu.profiler.block_compiles, 0)
        self.assertGreater(system.cpu.profiler.block_cache_hits, 0)

    def test_code_write_invalidation(self) -> None:
        program = decode_rom(
            encode_rom(
                [
                    i(Op.MOVI, a=0, c=7),
                    i(Op.ADDI, a=0, c=1),
                    i(Op.HALT),
                ]
            )
        )
        system = EmulatorSystem()
        system.cpu.load_program(program)
        # Prime cache.
        system.cpu.step()
        system.cpu.use_block_cache = True
        system.cpu.step()
        self.assertTrue(system.cpu.block_cache or system.cpu.block_meta)
        # Write to code mirror region: should invalidate block metadata.
        system.bus.write_u32(0x8004, 0xDEADBEEF)
        self.assertGreaterEqual(system.cpu.profiler.invalidations, 1)


if __name__ == "__main__":
    unittest.main()
