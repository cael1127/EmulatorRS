"""System bus and memory map."""

from __future__ import annotations

from dataclasses import dataclass

from emulator.core.interfaces import Device
from emulator.core.memory import RamMemory


@dataclass(frozen=True)
class MemoryMap:
    ram_base: int = 0x0000
    ram_size: int = 0x8000
    code_base: int = 0x8000  # Writable code mirror for cache invalidation demos.
    code_size: int = 0x1000
    mmio_base: int = 0xF000
    mmio_size: int = 0x0400


class SystemBus:
    """Routes reads/writes across RAM, code mirror, and MMIO devices."""

    def __init__(self, memory: RamMemory, memory_map: MemoryMap | None = None) -> None:
        self.memory = memory
        self.map = memory_map or MemoryMap()
        self._devices: dict[int, Device] = {}
        self._invalidate_cb = None

    def set_code_invalidator(self, callback) -> None:
        self._invalidate_cb = callback

    def register_device(self, addr: int, device: Device) -> None:
        if addr in self._devices:
            raise ValueError(f"device already mapped at {addr:#x}")
        self._devices[addr] = device

    def _is_ram(self, addr: int) -> bool:
        return self.map.ram_base <= addr < self.map.ram_base + self.map.ram_size

    def _is_code(self, addr: int) -> bool:
        return self.map.code_base <= addr < self.map.code_base + self.map.code_size

    def _is_mmio(self, addr: int) -> bool:
        return self.map.mmio_base <= addr < self.map.mmio_base + self.map.mmio_size

    def _to_ram_addr(self, addr: int) -> int:
        if self._is_ram(addr):
            return addr - self.map.ram_base
        if self._is_code(addr):
            # Code mirror lives after RAM region in backing RAM.
            return (addr - self.map.code_base) + self.map.ram_size
        raise ValueError(f"address not RAM-backed: {addr:#x}")

    def read_u32(self, addr: int) -> int:
        if self._is_ram(addr) or self._is_code(addr):
            return self.memory.read_u32(self._to_ram_addr(addr))
        if self._is_mmio(addr):
            device = self._devices.get(addr)
            if device is None:
                raise ValueError(f"unmapped MMIO read at {addr:#x}")
            return device.read(addr)
        raise ValueError(f"address out of map: {addr:#x}")

    def write_u32(self, addr: int, value: int) -> None:
        if self._is_ram(addr) or self._is_code(addr):
            self.memory.write_u32(self._to_ram_addr(addr), value)
            if self._is_code(addr):
                self.invalidate_code_at_addr(addr)
            return
        if self._is_mmio(addr):
            device = self._devices.get(addr)
            if device is None:
                raise ValueError(f"unmapped MMIO write at {addr:#x}")
            device.write(addr, value)
            return
        raise ValueError(f"address out of map: {addr:#x}")

    def tick(self, cycles: int) -> None:
        for device in self._devices.values():
            device.tick(cycles)

    def invalidate_code_at_addr(self, addr: int) -> None:
        if self._invalidate_cb is not None:
            self._invalidate_cb(addr)
