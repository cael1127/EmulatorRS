# Emulator Architecture (Homebrew-Only)

This project intentionally models modern-console concepts using a legal-safe workflow:

- Only homebrew/test ROMs.
- Only self-generated encrypted assets.
- No firmware extraction, key extraction, or DRM bypass mechanisms.

## Core Design

- `CPU`: fetch/decode/execute loop for a compact educational ISA.
- `Bus`: routes addresses to RAM or MMIO devices.
- `Scheduler`: deterministic cycle stepping and frame boundaries.
- `Devices`: timer, input, renderer, and a simple audio sample sink behind MMIO registers.
- `Services`: HLE-style syscall dispatcher for file/input/time/log.

## Determinism Strategy

- Every step emits a compact trace event `(pc, opcode, regs_hash)`.
- Final state snapshots include PC/registers/cycle count and RAM windows.
- Tests compare snapshots/golden traces for exact repeatability.

## Performance Strategy

- Start with interpreter for correctness.
- Add a block cache ("Python JIT prototype") that compiles basic blocks
  into host callables.
- Invalidate cached blocks on writes to emulated code memory or when MMIO
  side effects would make reuse unsafe.

## Graphics + Input Model

- Renderer accepts command-buffer style writes via MMIO.
- Pipeline stages are represented conceptually:
  1. command decode
  2. vertex transform (identity in demo)
  3. fragment shade (palette lookup)
- Input device exposes deterministic queued button states.

## Crypto Learning Track

- Separate `crypto_lab` module demonstrates:
  - key derivation,
  - authenticated encryption (AES-GCM),
  - integrity/tamper detection,
  - nonce misuse risk handling.

The loader only accepts self-authored encrypted asset containers.
