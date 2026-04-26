"""CLI to run built-in homebrew demo ROMs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from emulator.demos import list_demo_roms
from emulator.framebuffer_dump import framebuffer_to_ascii, framebuffer_to_ppm
from emulator.runtime import run_rom_session


def _parse_input_states(raw: str) -> list[int]:
    if not raw.strip():
        return []
    return [int(chunk.strip(), 0) for chunk in raw.split(",") if chunk.strip()]


def main() -> None:
    demos = list_demo_roms()
    parser = argparse.ArgumentParser(description="Run educational emulator demo ROMs.")
    parser.add_argument("--demo", choices=sorted(demos.keys()), default="arithmetic")
    parser.add_argument("--max-steps", type=int, default=100_000)
    parser.add_argument("--block-cache", action="store_true")
    parser.add_argument(
        "--input-states",
        default="",
        help="Comma-separated integers queued into input device before run (e.g. 1,2,0x10).",
    )
    parser.add_argument(
        "--dump-ppm",
        type=Path,
        default=None,
        metavar="PATH",
        help="After run, write framebuffer as binary P6 PPM (e.g. frame.ppm).",
    )
    parser.add_argument(
        "--dump-ascii",
        type=Path,
        default=None,
        metavar="PATH",
        help="After run, write framebuffer as ASCII art (one char per pixel).",
    )
    parser.add_argument(
        "--trace-out",
        type=Path,
        default=None,
        metavar="PATH",
        help="Append JSONL trace lines (pc, opcode, regs_hash) after each instruction.",
    )
    args = parser.parse_args()

    trace_events: list[tuple[int, int, int]] | None = [] if args.trace_out is not None else None
    report, system = run_rom_session(
        demos[args.demo],
        use_block_cache=args.block_cache,
        max_steps=args.max_steps,
        input_states=_parse_input_states(args.input_states),
        trace_events=trace_events,
    )
    print(json.dumps(report.to_dict(), indent=2))

    if args.trace_out is not None and trace_events is not None:
        with args.trace_out.open("w", encoding="utf-8", newline="\n") as handle:
            for pc, opcode, rh in trace_events:
                handle.write(
                    json.dumps({"pc": pc, "opcode": opcode, "regs_hash": rh}) + "\n"
                )

    if args.dump_ppm is not None:
        args.dump_ppm.write_bytes(framebuffer_to_ppm(system.renderer.framebuffer))
    if args.dump_ascii is not None:
        args.dump_ascii.write_text(
            framebuffer_to_ascii(system.renderer.framebuffer),
            encoding="utf-8",
            newline="\n",
        )


if __name__ == "__main__":
    main()
