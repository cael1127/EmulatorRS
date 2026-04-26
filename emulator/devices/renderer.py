"""Command-buffer style renderer model."""

from __future__ import annotations

from dataclasses import dataclass

from emulator.core.interfaces import Device


@dataclass(frozen=True)
class DrawPoint:
    x: int
    y: int
    color: int


class RenderDevice(Device):
    """
    Very small software renderer.

    MMIO write encoding:
      bits 0-7   : x
      bits 8-15  : y
      bits 16-23 : color index
      bits 24-31 : command id (1=draw point, 2=clear)
    """

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.framebuffer = [[0 for _ in range(width)] for _ in range(height)]
        self.command_buffer: list[DrawPoint] = []
        self.presented_frames = 0

    def read(self, addr: int) -> int:
        return self.presented_frames

    def _shade_fragment(self, color: int) -> int:
        # Fragment stage placeholder.
        return color & 0xFF

    def _vertex_stage(self, x: int, y: int) -> tuple[int, int]:
        # Vertex stage placeholder (identity transform).
        return x, y

    def _execute_commands(self) -> None:
        for cmd in self.command_buffer:
            x, y = self._vertex_stage(cmd.x, cmd.y)
            if 0 <= x < self.width and 0 <= y < self.height:
                self.framebuffer[y][x] = self._shade_fragment(cmd.color)
        if self.command_buffer:
            self.presented_frames += 1
        self.command_buffer.clear()

    def write(self, addr: int, value: int) -> None:
        cmd_id = (value >> 24) & 0xFF
        x = value & 0xFF
        y = (value >> 8) & 0xFF
        color = (value >> 16) & 0xFF

        if cmd_id == 1:
            self.command_buffer.append(DrawPoint(x=x, y=y, color=color))
        elif cmd_id == 2:
            for row in self.framebuffer:
                row[:] = [0] * self.width
        else:
            # Unknown commands are ignored to keep pipeline robust in tests.
            return

    def tick(self, cycles: int) -> None:
        # Flush commands once per tick as a simplified frame scheduler.
        self._execute_commands()
