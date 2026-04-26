# PolygotEmulator (Educational, Homebrew-Only)

This project demonstrates how to model modern-console concepts in software
without using protected firmware or commercial game content.

## Implemented

- Interpreter-first CPU with fetch/decode/execute.
- Virtual memory map + MMIO bus routing.
- Timer, input, and command-buffer style renderer devices.
- Block-cache/JIT prototype with invalidation hooks and profiling counters.
- HLE-style syscall/service dispatcher.
- Deterministic trace/snapshot test harness.
- MMIO audio sample sink and extra homebrew demos (input, audio, HLE chain).
- JSONL execution trace export from the CLI.
- AES-GCM encrypted asset pack lab with tamper/replay/wrong-key tests.

## Safety Scope

- Homebrew/test ROMs only.
- Self-generated assets only.
- No key extraction, no DRM bypass, no firmware dumping workflows.

## Run Tests

```bash
python -m unittest discover -s tests -v
```

## Run Demo ROMs

```bash
python run_rom.py --demo arithmetic
python run_rom.py --demo render_service --block-cache
python run_rom.py --demo perf_loop --block-cache
python run_rom.py --demo visual_demo --dump-ppm pattern.ppm --dump-ascii pattern.txt
python run_rom.py --demo input_demo --input-states 170,187
python run_rom.py --demo audio_demo
python run_rom.py --demo hle_chain
python run_rom.py --demo arithmetic --trace-out trace.jsonl
```

## Dump framebuffer (after run)

Writes the software framebuffer from the render device (mostly black unless the demo drew pixels).

```bash
python run_rom.py --demo render_service --dump-ppm out.ppm --dump-ascii out.txt
```

Open `out.ppm` in an image viewer or browser; `out.txt` is a quick terminal-friendly preview.

## Run Benchmark

```bash
python scripts/benchmark.py --demo perf_loop --runs 50
```

## Enable Crypto Tests

```bash
pip install -r requirements.txt
python -m unittest tests.test_crypto_lab -v
```
