"""Deterministic trace helpers shared by harness and runtime."""

from __future__ import annotations


def regs_hash(regs: tuple[int, ...]) -> int:
    h = 2166136261
    for value in regs:
        h ^= value & 0xFFFFFFFF
        h = (h * 16777619) & 0xFFFFFFFF
    return h
