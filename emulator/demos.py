"""Homebrew demo ROM workloads for experimentation."""

from __future__ import annotations

from emulator.core.interfaces import Instruction
from emulator.core.opcodes import Op
from emulator.program_loader import encode_rom


def _i(op: Op, a: int = 0, b: int = 0, c: int = 0) -> Instruction:
    return Instruction(opcode=int(op), a=a, b=b, c=c)


def arithmetic_demo_rom() -> bytes:
    """Compute simple arithmetic and store result to RAM."""
    program = [
        _i(Op.MOVI, a=0, c=5),
        _i(Op.MOVI, a=1, c=9),
        _i(Op.ADD, a=0, b=1),
        _i(Op.ADDI, a=0, c=3),  # r0 = 17
        _i(Op.MOVI, a=2, c=0x20),
        _i(Op.STORE, a=0, b=2),  # mem[0x20] = 17
        _i(Op.HALT),
    ]
    return encode_rom(program)


def render_and_service_demo_rom() -> bytes:
    """Draw one point via HLE service and read service ticks."""
    program = [
        _i(Op.MOVI, a=0, c=6),  # x
        _i(Op.MOVI, a=1, c=4),  # y
        _i(Op.MOVI, a=2, c=11),  # color
        _i(Op.SYSCALL, c=5),  # draw point
        _i(Op.SYSCALL, c=1),  # monotonic ticks -> r0
        _i(Op.SYSCALL, c=4),  # log current r0
        _i(Op.HALT),
    ]
    return encode_rom(program)


def loop_perf_demo_rom(iterations: int = 80) -> bytes:
    """Tight arithmetic loop for interpreter vs block-cache comparisons."""
    if iterations <= 0 or iterations > 255:
        raise ValueError("iterations must be in range 1..255")
    program = [
        _i(Op.MOVI, a=0, c=iterations),
        _i(Op.MOVI, a=1, c=1),
        _i(Op.MOVI, a=2, c=0),  # running sum
        _i(Op.ADD, a=2, b=0),
        _i(Op.SUB, a=0, b=1),
        _i(Op.JZ, a=0, c=7),
        _i(Op.JMP, c=3),
        _i(Op.HALT),
    ]
    return encode_rom(program)


def visual_demo_rom() -> bytes:
    """
    Draw a visible diagonal using HLE draw (syscall 5) in a loop.

    For i in 0..15: pixel at (8+i, 6+i) with color (40+i). When i reaches 16, exit.
    Registers: r3=i, r7=16-i for exit test.
    """
    # Instruction indices: 0 setup; 1..7 draw one pixel; 8 bump i; 9..11 exit test; 12 jmp; 13 halt
    program = [
        _i(Op.MOVI, a=3, c=0),  # i = 0
        _i(Op.MOVI, a=0, c=8),
        _i(Op.ADD, a=0, b=3),  # x = 8 + i
        _i(Op.MOVI, a=1, c=6),
        _i(Op.ADD, a=1, b=3),  # y = 6 + i
        _i(Op.MOVI, a=2, c=40),
        _i(Op.ADD, a=2, b=3),  # color = 40 + i
        _i(Op.SYSCALL, c=5),
        _i(Op.ADDI, a=3, c=1),  # i += 1
        _i(Op.MOVI, a=7, c=16),
        _i(Op.SUB, a=7, b=3),  # r7 = 16 - i
        _i(Op.JZ, a=7, c=13),  # done when i == 16
        _i(Op.JMP, c=1),  # loop to draw step
        _i(Op.HALT),
    ]
    return encode_rom(program)


def input_demo_rom() -> bytes:
    """Read two queued input values via syscall 2 and store them to RAM."""
    program = [
        _i(Op.MOVI, a=2, c=0x10),
        _i(Op.SYSCALL, c=2),
        _i(Op.STORE, a=0, b=2),
        _i(Op.MOVI, a=2, c=0x14),
        _i(Op.SYSCALL, c=2),
        _i(Op.STORE, a=0, b=2),
        _i(Op.HALT),
    ]
    return encode_rom(program)


def audio_demo_rom() -> bytes:
    """Enqueue three small PCM-ish samples via MMIO audio sink (OUT @ 0xF300)."""
    # OUT offset from 0xF000: (0xF300 - 0xF000) / 4 = 0xC0
    program = [
        _i(Op.MOVI, a=0, c=0x10),
        _i(Op.OUT, a=0, c=0xC0),
        _i(Op.MOVI, a=0, c=0x20),
        _i(Op.OUT, a=0, c=0xC0),
        _i(Op.MOVI, a=0, c=0x30),
        _i(Op.OUT, a=0, c=0xC0),
        _i(Op.HALT),
    ]
    return encode_rom(program)


def hle_chain_demo_rom() -> bytes:
    """Exercise file mock, tick, and log services in one ROM."""
    program = [
        _i(Op.MOVI, a=0, c=5),
        _i(Op.SYSCALL, c=3),
        _i(Op.MOVI, a=1, c=0x20),
        _i(Op.STORE, a=0, b=1),
        _i(Op.SYSCALL, c=1),
        _i(Op.SYSCALL, c=4),
        _i(Op.HALT),
    ]
    return encode_rom(program)


def list_demo_roms() -> dict[str, bytes]:
    """Named demo ROM mapping for CLI and tests."""
    return {
        "arithmetic": arithmetic_demo_rom(),
        "render_service": render_and_service_demo_rom(),
        "perf_loop": loop_perf_demo_rom(),
        "visual_demo": visual_demo_rom(),
        "input_demo": input_demo_rom(),
        "audio_demo": audio_demo_rom(),
        "hle_chain": hle_chain_demo_rom(),
    }
