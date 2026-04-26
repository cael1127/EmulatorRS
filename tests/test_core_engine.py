"""Phase 1 tests for interpreter, memory map, and timer scaffolding."""

from __future__ import annotations

import unittest

from emulator.core.interfaces import Instruction
from emulator.core.opcodes import Op
from emulator.program_loader import encode_rom
from tests.harness import run_rom


def i(op: Op, a: int = 0, b: int = 0, c: int = 0) -> Instruction:
    return Instruction(opcode=int(op), a=a, b=b, c=c)


class CoreEngineTests(unittest.TestCase):
    def test_arithmetic_branch_store(self) -> None:
        rom = encode_rom(
            [
                i(Op.MOVI, a=0, c=5),
                i(Op.MOVI, a=1, c=7),
                i(Op.ADD, a=0, b=1),
                i(Op.MOVI, a=2, c=0),
                i(Op.JZ, a=2, c=7),
                i(Op.MOVI, a=0, c=99),
                i(Op.NOP),
                i(Op.MOVI, a=3, c=0x10),
                i(Op.STORE, a=0, b=3),
                i(Op.HALT),
            ]
        )
        result = run_rom(rom)
        self.assertEqual(result.final_regs[0], 12)
        self.assertEqual(result.ram_words[4], 12)  # addr 0x10 == 4th word index

    def test_timer_mmio_device(self) -> None:
        rom = encode_rom(
            [
                i(Op.MOVI, a=0, c=3),
                i(Op.OUT, a=0, c=0),  # timer device at MMIO offset 0
                i(Op.NOP),
                i(Op.NOP),
                i(Op.NOP),
                i(Op.NOP),
                i(Op.HALT),
            ]
        )
        result = run_rom(rom)
        self.assertEqual(result.timer_expirations, 2)

    def test_trace_is_deterministic(self) -> None:
        rom = encode_rom(
            [
                i(Op.MOVI, a=0, c=10),
                i(Op.ADDI, a=0, c=2),
                i(Op.CMPZ, a=0),
                i(Op.HALT),
            ]
        )
        first = run_rom(rom)
        second = run_rom(rom)
        self.assertEqual(first.trace, second.trace)
        self.assertEqual(first.final_regs, second.final_regs)


if __name__ == "__main__":
    unittest.main()
