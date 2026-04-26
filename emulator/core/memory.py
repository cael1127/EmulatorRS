"""Memory model for RAM and code region."""

from __future__ import annotations


class RamMemory:
    """Simple 32-bit word-addressable RAM backed by bytearray."""

    def __init__(self, size_bytes: int) -> None:
        if size_bytes <= 0 or size_bytes % 4 != 0:
            raise ValueError("size_bytes must be positive and 4-byte aligned")
        self.size_bytes = size_bytes
        self._data = bytearray(size_bytes)

    def _check_addr(self, addr: int) -> None:
        if addr < 0 or addr + 4 > self.size_bytes:
            raise ValueError(f"address out of range: {addr:#x}")
        if addr % 4 != 0:
            raise ValueError(f"unaligned address: {addr:#x}")

    def read_u32(self, addr: int) -> int:
        self._check_addr(addr)
        return int.from_bytes(self._data[addr : addr + 4], "little")

    def write_u32(self, addr: int, value: int) -> None:
        self._check_addr(addr)
        self._data[addr : addr + 4] = (value & 0xFFFFFFFF).to_bytes(4, "little")

    def dump_words(self, start_addr: int, words: int) -> tuple[int, ...]:
        """Dump an immutable window for deterministic snapshot tests."""
        if words < 0:
            raise ValueError("words must be >= 0")
        return tuple(self.read_u32(start_addr + (i * 4)) for i in range(words))
