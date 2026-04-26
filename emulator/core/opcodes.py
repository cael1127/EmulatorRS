"""Opcode definitions for the educational ISA."""

from __future__ import annotations

from enum import IntEnum


class Op(IntEnum):
    NOP = 0
    MOVI = 1  # a=reg, c=imm8
    ADD = 2  # a=dst, b=src
    ADDI = 3  # a=dst, c=imm8
    LOAD = 4  # a=dst, b=addr_reg
    STORE = 5  # a=src, b=addr_reg
    JMP = 6  # c=target_pc
    JZ = 7  # a=reg, c=target_pc
    OUT = 8  # a=src, c=addr8
    HALT = 9
    SYSCALL = 10  # c=service_id
    SUB = 11  # a=dst, b=src
    CMPZ = 12  # a=reg -> zero flag
