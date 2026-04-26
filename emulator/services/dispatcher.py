"""HLE syscall dispatcher and demo services."""

from __future__ import annotations

from collections.abc import Iterable

from emulator.devices.input_device import InputDevice
from emulator.devices.renderer import RenderDevice


class HleDispatcher:
    """
    Service IDs:
      1: get monotonic ticks
      2: read input state
      3: mock file read (returns deterministic pseudo-content length)
      4: log value (returns 0)
      5: draw point using args (x, y, color)
    """

    def __init__(self, input_device: InputDevice, renderer: RenderDevice) -> None:
        self.input_device = input_device
        self.renderer = renderer
        self.ticks = 0
        self.logs: list[int] = []
        self.service_versions = {
            1: 1,
            2: 1,
            3: 1,
            4: 1,
            5: 1,
        }

    def call(self, service_id: int, args: Iterable[int]) -> int:
        self.ticks += 1
        values = list(args)
        if service_id == 1:
            return self.ticks
        if service_id == 2:
            return self.input_device.read(0)
        if service_id == 3:
            file_id = values[0] if values else 0
            return (file_id ^ 0x55AA) & 0xFFFF
        if service_id == 4:
            self.logs.append(values[0] if values else 0)
            return 0
        if service_id == 5:
            x = values[0] & 0xFF if len(values) > 0 else 0
            y = values[1] & 0xFF if len(values) > 1 else 0
            color = values[2] & 0xFF if len(values) > 2 else 1
            packed = (1 << 24) | (color << 16) | (y << 8) | x
            self.renderer.write(0, packed)
            return 0
        return 0xFFFFFFFF
