"""Deterministic input device model."""

from __future__ import annotations

from collections import deque

from emulator.core.interfaces import Device


class InputDevice(Device):
    """
    MMIO input queue.

    - read() returns next queued input state, or 0 when empty.
    - write() appends a synthetic state (useful for tests).
    """

    def __init__(self) -> None:
        self._queue: deque[int] = deque()

    def queue_state(self, state: int) -> None:
        self._queue.append(state & 0xFFFFFFFF)

    def read(self, addr: int) -> int:
        if not self._queue:
            return 0
        return self._queue.popleft()

    def write(self, addr: int, value: int) -> None:
        self.queue_state(value)

    def tick(self, cycles: int) -> None:
        # Input device has no temporal behavior in this demo.
        return
