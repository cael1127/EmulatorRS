"""Simple benchmark runner for interpreter vs block-cache mode."""

from __future__ import annotations

import argparse
import pathlib
import statistics
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from emulator.demos import list_demo_roms
from emulator.runtime import run_rom_bytes


def _run_many(rom: bytes, runs: int, use_block_cache: bool, max_steps: int) -> dict[str, float]:
    durations_ms: list[float] = []
    instructions: list[int] = []
    for _ in range(runs):
        start = time.perf_counter()
        report = run_rom_bytes(
            rom,
            use_block_cache=use_block_cache,
            max_steps=max_steps,
        )
        elapsed = (time.perf_counter() - start) * 1000.0
        durations_ms.append(elapsed)
        instructions.append(report.profiler["executed_instructions"])
    return {
        "avg_ms": statistics.mean(durations_ms),
        "p95_ms": sorted(durations_ms)[max(0, int(0.95 * len(durations_ms)) - 1)],
        "avg_instructions": statistics.mean(instructions),
    }


def main() -> None:
    demos = list_demo_roms()
    parser = argparse.ArgumentParser(description="Benchmark emulator run modes.")
    parser.add_argument("--demo", choices=sorted(demos.keys()), default="perf_loop")
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--max-steps", type=int, default=200_000)
    args = parser.parse_args()

    rom = demos[args.demo]
    interp = _run_many(rom, runs=args.runs, use_block_cache=False, max_steps=args.max_steps)
    cached = _run_many(rom, runs=args.runs, use_block_cache=True, max_steps=args.max_steps)

    print(f"Demo: {args.demo} (runs={args.runs})")
    print(
        "Interpreter: "
        f"avg={interp['avg_ms']:.3f}ms p95={interp['p95_ms']:.3f}ms "
        f"instr={interp['avg_instructions']:.1f}"
    )
    print(
        "Block-cache: "
        f"avg={cached['avg_ms']:.3f}ms p95={cached['p95_ms']:.3f}ms "
        f"instr={cached['avg_instructions']:.1f}"
    )
    speedup = interp["avg_ms"] / cached["avg_ms"] if cached["avg_ms"] > 0 else 0.0
    print(f"Relative speedup: {speedup:.2f}x")


if __name__ == "__main__":
    main()
