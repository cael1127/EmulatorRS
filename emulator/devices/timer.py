"""Simple timer/IRQ-like MMIO device."""

from __future__ import annotations

from emulator.core.interfaces import Device


class TimerDevice(Device):
    """
    Timer mapped at a single MMIO address.

    - write(value): sets period in cycles
    - read(): returns number of expirations
    """

    def __init__(self) -> None:
        self.period_cycles = 0
        self.accumulated = 0
        self.expirations = 0

    def read(self, addr: int) -> int:
        return self.expirations

    def write(self, addr: int, value: int) -> None:
        self.period_cycles = max(0, value)
        self.accumulated = 0
        self.expirations = 0

    def tick(self, cycles: int) -> None:
        if self.period_cycles <= 0:
            return
        self.accumulated += cycles
        while self.accumulated >= self.period_cycles:
            self.accumulated -= self.period_cycles
            self.expirations += 1
