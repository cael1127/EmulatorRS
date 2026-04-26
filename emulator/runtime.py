"""Runtime helpers for running ROM workloads and collecting reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from emulator.program_loader import decode_rom
from emulator.system import EmulatorSystem
from emulator.traceutil import regs_hash


@dataclass(frozen=True)
class RunReport:
    halted: bool
    pc: int
    cycles: int
    frame_count: int
    regs: tuple[int, ...]
    timer_expirations: int
    rendered_frames: int
    audio_sample_count: int
    audio_last_sample: int
    profiler: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["regs"] = list(self.regs)
        return data


def run_rom_session(
    rom_bytes: bytes,
    *,
    use_block_cache: bool = False,
    max_steps: int = 100_000,
    input_states: list[int] | None = None,
    trace_events: list[tuple[int, int, int]] | None = None,
) -> tuple[RunReport, EmulatorSystem]:
    system = EmulatorSystem(cycles_per_frame=100)
    if input_states:
        for state in input_states:
            system.input.queue_state(state)
    program = decode_rom(rom_bytes)
    system.cpu.load_program(program)

    trace_callback = None
    if trace_events is not None:
        def trace_callback(pc: int, opcode: int, regs: tuple[int, ...]) -> None:
            trace_events.append((pc, int(opcode), regs_hash(regs)))

    snapshot = system.cpu.run(
        max_steps=max_steps,
        use_block_cache=use_block_cache,
        trace=trace_callback,
    )
    profiler = {
        "executed_instructions": system.cpu.profiler.executed_instructions,
        "frame_boundaries": system.cpu.profiler.frame_boundaries,
        "block_cache_hits": system.cpu.profiler.block_cache_hits,
        "block_compiles": system.cpu.profiler.block_compiles,
        "invalidations": system.cpu.profiler.invalidations,
    }
    audio_samples = system.audio.samples
    audio_last = audio_samples[-1] if audio_samples else 0
    report = RunReport(
        halted=snapshot.halted,
        pc=snapshot.pc,
        cycles=snapshot.cycles,
        frame_count=system.scheduler.frame_count,
        regs=snapshot.regs,
        timer_expirations=system.timer.expirations,
        rendered_frames=system.renderer.presented_frames,
        audio_sample_count=len(audio_samples),
        audio_last_sample=audio_last,
        profiler=profiler,
    )
    return report, system


def run_rom_bytes(
    rom_bytes: bytes,
    *,
    use_block_cache: bool = False,
    max_steps: int = 100_000,
    input_states: list[int] | None = None,
) -> RunReport:
    report, _ = run_rom_session(
        rom_bytes,
        use_block_cache=use_block_cache,
        max_steps=max_steps,
        input_states=input_states,
    )
    return report
