"""Phase 3/4 tests for renderer, input, and HLE services."""

from __future__ import annotations

import unittest

from emulator.core.interfaces import Instruction
from emulator.core.opcodes import Op
from emulator.program_loader import decode_rom, encode_rom
from emulator.system import EmulatorSystem


def i(op: Op, a: int = 0, b: int = 0, c: int = 0) -> Instruction:
    return Instruction(opcode=int(op), a=a, b=b, c=c)


class RenderAndServiceTests(unittest.TestCase):
    def test_renderer_draw_point_via_mmio(self) -> None:
        system = EmulatorSystem()
        # cmd=draw(1), x=3, y=2, color=7
        packed = (1 << 24) | (7 << 16) | (2 << 8) | 3
        system.bus.write_u32(0xF200, packed)
        system.bus.tick(1)
        self.assertEqual(system.renderer.framebuffer[2][3], 7)
        self.assertEqual(system.renderer.presented_frames, 1)

    def test_input_device_queue_and_read(self) -> None:
        system = EmulatorSystem()
        system.input.queue_state(123)
        value = system.bus.read_u32(0xF100)
        self.assertEqual(value, 123)
        self.assertEqual(system.bus.read_u32(0xF100), 0)

    def test_syscall_dispatch_and_logging(self) -> None:
        rom = encode_rom(
            [
                i(Op.MOVI, a=0, c=42),
                i(Op.SYSCALL, c=4),  # log r0
                i(Op.SYSCALL, c=1),  # get ticks
                i(Op.HALT),
            ]
        )
        system = EmulatorSystem()
        system.cpu.load_program(decode_rom(rom))
        snapshot = system.cpu.run()
        self.assertEqual(system.services.logs, [42])
        self.assertEqual(snapshot.regs[0], 2)

    def test_service_contract_versions_present(self) -> None:
        system = EmulatorSystem()
        self.assertEqual(system.services.service_versions[1], 1)
        self.assertEqual(system.services.service_versions[2], 1)
        self.assertEqual(system.services.service_versions[3], 1)
        self.assertEqual(system.services.service_versions[4], 1)
        self.assertEqual(system.services.service_versions[5], 1)

    def test_draw_syscall_renders_pixel(self) -> None:
        rom = encode_rom(
            [
                i(Op.MOVI, a=0, c=9),
                i(Op.MOVI, a=1, c=5),
                i(Op.MOVI, a=2, c=14),
                i(Op.SYSCALL, c=5),
                i(Op.HALT),
            ]
        )
        system = EmulatorSystem()
        system.cpu.load_program(decode_rom(rom))
        system.cpu.run()
        self.assertEqual(system.renderer.framebuffer[5][9], 14)


if __name__ == "__main__":
    unittest.main()
