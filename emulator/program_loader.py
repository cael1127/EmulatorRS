"""ROM encode/decode helpers for test and demo programs."""

from __future__ import annotations

from emulator.core.interfaces import Instruction


INSTR_SIZE = 4


def decode_rom(blob: bytes) -> list[Instruction]:
    """Decode a binary ROM where each instruction is 4 bytes."""
    if len(blob) % INSTR_SIZE != 0:
        raise ValueError("rom size must be a multiple of 4 bytes")
    out: list[Instruction] = []
    for i in range(0, len(blob), INSTR_SIZE):
        opcode, a, b, c = blob[i : i + INSTR_SIZE]
        out.append(Instruction(opcode=opcode, a=a, b=b, c=c))
    return out


def encode_rom(program: list[Instruction]) -> bytes:
    """Encode instruction list to ROM bytes."""
    data = bytearray()
    for instr in program:
        data.extend(
            (
                instr.opcode & 0xFF,
                instr.a & 0xFF,
                instr.b & 0xFF,
                instr.c & 0xFF,
            )
        )
    return bytes(data)
