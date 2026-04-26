"""Deterministic run harness with trace/snapshot outputs."""

from __future__ import annotations

from dataclasses import dataclass

from emulator.program_loader import decode_rom
from emulator.system import EmulatorSystem
from emulator.traceutil import regs_hash


@dataclass(frozen=True)
class RunResult:
    trace: tuple[tuple[int, int, int], ...]
    final_pc: int
    final_regs: tuple[int, ...]
    cycles: int
    timer_expirations: int
    frame_count: int
    ram_words: tuple[int, ...]


def run_rom(
    rom_bytes: bytes,
    max_steps: int = 100_000,
    use_block_cache: bool = False,
) -> RunResult:
    system = EmulatorSystem(cycles_per_frame=10)
    trace_events: list[tuple[int, int, int]] = []

    def trace(pc: int, opcode: int, regs: tuple[int, ...]) -> None:
        trace_events.append((pc, int(opcode), regs_hash(regs)))

    program = decode_rom(rom_bytes)
    system.cpu.load_program(program)
    snapshot = system.cpu.run(
        max_steps=max_steps,
        trace=trace,
        use_block_cache=use_block_cache,
    )
    ram_words = system.bus.memory.dump_words(0, 8)
    return RunResult(
        trace=tuple(trace_events),
        final_pc=snapshot.pc,
        final_regs=snapshot.regs,
        cycles=snapshot.cycles,
        timer_expirations=system.timer.expirations,
        frame_count=system.scheduler.frame_count,
        ram_words=ram_words,
    )
