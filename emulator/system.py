"""System wiring for CPU, bus, devices, and services."""

from __future__ import annotations

from emulator.core.bus import MemoryMap, SystemBus
from emulator.core.cpu import CpuCore
from emulator.core.memory import RamMemory
from emulator.core.scheduler import Scheduler
from emulator.devices.audio_device import AudioDevice
from emulator.devices.input_device import InputDevice
from emulator.devices.renderer import RenderDevice
from emulator.devices.timer import TimerDevice
from emulator.services.dispatcher import HleDispatcher


class EmulatorSystem:
    """Convenience wrapper that assembles a full emulation environment."""

    TIMER_ADDR = 0xF000
    INPUT_ADDR = 0xF100
    RENDER_ADDR = 0xF200
    AUDIO_ADDR = 0xF300

    def __init__(self, cycles_per_frame: int = 1_000) -> None:
        # Backing RAM includes normal RAM plus code mirror region.
        memory = RamMemory(size_bytes=MemoryMap().ram_size + MemoryMap().code_size)
        self.bus = SystemBus(memory=memory)
        self.scheduler = Scheduler(cycles_per_frame=cycles_per_frame)
        self.timer = TimerDevice()
        self.input = InputDevice()
        self.renderer = RenderDevice(width=64, height=36)
        self.audio = AudioDevice()
        self.services = HleDispatcher(input_device=self.input, renderer=self.renderer)

        self.bus.register_device(self.TIMER_ADDR, self.timer)
        self.bus.register_device(self.INPUT_ADDR, self.input)
        self.bus.register_device(self.RENDER_ADDR, self.renderer)
        self.bus.register_device(self.AUDIO_ADDR, self.audio)
        self.cpu = CpuCore(bus=self.bus, scheduler=self.scheduler, services=self.services)

