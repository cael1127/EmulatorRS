"""Deterministic cycle scheduler."""

from __future__ import annotations


class Scheduler:
    """Tracks cycle budget and frame boundaries."""

    def __init__(self, cycles_per_frame: int = 1_000) -> None:
        if cycles_per_frame <= 0:
            raise ValueError("cycles_per_frame must be > 0")
        self.cycles_per_frame = cycles_per_frame
        self.total_cycles = 0
        self._frame_cycles = 0
        self.frame_count = 0

    def advance(self, cycles: int) -> bool:
        """Advance by cycles and return True whenever a frame boundary is crossed."""
        if cycles < 0:
            raise ValueError("cycles must be >= 0")
        self.total_cycles += cycles
        self._frame_cycles += cycles
        crossed = False
        while self._frame_cycles >= self.cycles_per_frame:
            self._frame_cycles -= self.cycles_per_frame
            self.frame_count += 1
            crossed = True
        return crossed
