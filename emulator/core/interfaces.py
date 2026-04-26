"""Core interface contracts for the educational emulator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Protocol


@dataclass(frozen=True)
class Instruction:
    """Decoded guest instruction."""

    opcode: int
    a: int = 0
    b: int = 0
    c: int = 0


@dataclass(frozen=True)
class CpuSnapshot:
    """Serializable CPU state for deterministic testing."""

    pc: int
    regs: tuple[int, ...]
    halted: bool
    cycles: int


class Device(ABC):
    """MMIO device contract."""

    @abstractmethod
    def read(self, addr: int) -> int:
        """Read a value from a device-local register."""

    @abstractmethod
    def write(self, addr: int, value: int) -> None:
        """Write a value to a device-local register."""

    @abstractmethod
    def tick(self, cycles: int) -> None:
        """Advance device time."""


class Memory(Protocol):
    """Addressable memory abstraction."""

    def read_u32(self, addr: int) -> int:
        """Read a 32-bit little-endian word."""

    def write_u32(self, addr: int, value: int) -> None:
        """Write a 32-bit little-endian word."""


class Bus(Protocol):
    """System bus abstraction."""

    def read_u32(self, addr: int) -> int:
        """Read from RAM or mapped MMIO."""

    def write_u32(self, addr: int, value: int) -> None:
        """Write to RAM or mapped MMIO."""

    def tick(self, cycles: int) -> None:
        """Propagate time to devices."""

    def invalidate_code_at_addr(self, addr: int) -> None:
        """Signal that code cache may be stale after a write."""


class ServiceDispatcher(Protocol):
    """High-level service wrapper entrypoint."""

    def call(self, service_id: int, args: Iterable[int]) -> int:
        """Run a service and return integer status/result."""

