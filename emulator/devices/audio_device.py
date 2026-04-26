"""Simple MMIO PCM sample sink (educational audio path)."""

from __future__ import annotations

from emulator.core.interfaces import Device


class AudioDevice(Device):
    """
    One register: write enqueues a 32-bit sample; read returns queued count.

    Optional cap drops oldest samples when full (streaming sink model).
    """

    def __init__(self, max_samples: int = 4096) -> None:
        if max_samples < 1:
            raise ValueError("max_samples must be >= 1")
        self.max_samples = max_samples
        self.samples: list[int] = []
        self.total_writes = 0

    def read(self, addr: int) -> int:
        return len(self.samples) & 0xFFFFFFFF

    def write(self, addr: int, value: int) -> None:
        self.total_writes += 1
        v = value & 0xFFFFFFFF
        self.samples.append(v)
        while len(self.samples) > self.max_samples:
            self.samples.pop(0)

    def tick(self, cycles: int) -> None:
        return
