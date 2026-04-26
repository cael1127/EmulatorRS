"""Interpreter-first CPU core with block-cache JIT prototype."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from emulator.core.interfaces import CpuSnapshot, Instruction, ServiceDispatcher
from emulator.core.opcodes import Op
from emulator.core.scheduler import Scheduler


TraceFn = Callable[[int, int, tuple[int, ...]], None]


@dataclass
class CpuProfiler:
    """Counters used by optimization phases."""

    opcode_counts: dict[int, int] = field(default_factory=dict)
    executed_instructions: int = 0
    frame_boundaries: int = 0
    block_cache_hits: int = 0
    block_compiles: int = 0
    invalidations: int = 0

    def record_opcode(self, opcode: int) -> None:
        self.executed_instructions += 1
        self.opcode_counts[opcode] = self.opcode_counts.get(opcode, 0) + 1


@dataclass(frozen=True)
class BlockMeta:
    start_pc: int
    end_pc_exclusive: int


class CpuCore:
    """Minimal guest CPU with 8 general-purpose registers."""

    REG_COUNT = 8
    MMIO_BASE = 0xF000

    def __init__(
        self,
        bus,
        scheduler: Scheduler,
        services: ServiceDispatcher | None = None,
    ) -> None:
        self.bus = bus
        self.scheduler = scheduler
        self.services = services
        self.regs = [0] * self.REG_COUNT
        self.pc = 0
        self.halted = False
        self.zero_flag = False
        self.cycles = 0
        self.program: list[Instruction] = []
        self.profiler = CpuProfiler()
        self.block_cache: dict[int, Callable[[TraceFn | None], int]] = {}
        self.block_meta: dict[int, BlockMeta] = {}
        self.code_base = 0x8000
        self.use_block_cache = False
        self.bus.set_code_invalidator(self.invalidate_blocks_for_addr)

    def load_program(self, program: list[Instruction]) -> None:
        self.program = program
        self.pc = 0
        self.halted = False
        self.zero_flag = False
        self.cycles = 0
        self.regs = [0] * self.REG_COUNT
        self.profiler = CpuProfiler()
        self.block_cache.clear()
        self.block_meta.clear()

    def snapshot(self) -> CpuSnapshot:
        return CpuSnapshot(
            pc=self.pc,
            regs=tuple(self.regs),
            halted=self.halted,
            cycles=self.cycles,
        )

    def _require_reg(self, idx: int) -> int:
        if idx < 0 or idx >= self.REG_COUNT:
            raise ValueError(f"register out of range: {idx}")
        return idx

    def _tick_once(self) -> None:
        self.cycles += 1
        self.bus.tick(1)
        if self.scheduler.advance(1):
            self.profiler.frame_boundaries += 1

    def _execute_single(self, instr: Instruction, trace: TraceFn | None = None) -> None:
        opcode = Op(instr.opcode)
        self.profiler.record_opcode(opcode)
        if trace is not None:
            trace(self.pc, opcode, tuple(self.regs))

        advance_pc = True
        a = self._require_reg(instr.a) if opcode in (Op.MOVI, Op.ADD, Op.ADDI, Op.LOAD, Op.STORE, Op.JZ, Op.OUT, Op.SUB, Op.CMPZ) else 0
        b = self._require_reg(instr.b) if opcode in (Op.ADD, Op.LOAD, Op.STORE, Op.SUB) else 0
        imm = instr.c & 0xFF

        if opcode == Op.NOP:
            pass
        elif opcode == Op.MOVI:
            self.regs[a] = imm
            self.zero_flag = self.regs[a] == 0
        elif opcode == Op.ADD:
            self.regs[a] = (self.regs[a] + self.regs[b]) & 0xFFFFFFFF
            self.zero_flag = self.regs[a] == 0
        elif opcode == Op.ADDI:
            self.regs[a] = (self.regs[a] + imm) & 0xFFFFFFFF
            self.zero_flag = self.regs[a] == 0
        elif opcode == Op.SUB:
            self.regs[a] = (self.regs[a] - self.regs[b]) & 0xFFFFFFFF
            self.zero_flag = self.regs[a] == 0
        elif opcode == Op.CMPZ:
            self.zero_flag = self.regs[a] == 0
        elif opcode == Op.LOAD:
            addr = self.regs[b]
            self.regs[a] = self.bus.read_u32(addr)
            self.zero_flag = self.regs[a] == 0
        elif opcode == Op.STORE:
            addr = self.regs[b]
            self.bus.write_u32(addr, self.regs[a])
        elif opcode == Op.JMP:
            self.pc = imm
            advance_pc = False
        elif opcode == Op.JZ:
            if self.regs[a] == 0:
                self.pc = imm
                advance_pc = False
        elif opcode == Op.OUT:
            addr = self.MMIO_BASE + (imm * 4)
            self.bus.write_u32(addr, self.regs[a])
        elif opcode == Op.SYSCALL:
            if self.services is None:
                raise RuntimeError("syscall attempted without service dispatcher")
            args = tuple(self.regs[:4])
            self.regs[0] = self.services.call(imm, args)
            self.zero_flag = self.regs[0] == 0
        elif opcode == Op.HALT:
            self.halted = True
        else:
            raise RuntimeError(f"unsupported opcode: {opcode}")

        if advance_pc:
            self.pc += 1
        self._tick_once()

    def _compile_block(self, start_pc: int) -> Callable[[TraceFn | None], int]:
        """
        Build a straight-line block callable.

        We stop at control flow, MMIO, syscalls, and memory operations to keep
        side effects explicit and make invalidation boundaries obvious.
        """
        end = start_pc
        simple_ops = {Op.NOP, Op.MOVI, Op.ADD, Op.ADDI, Op.SUB, Op.CMPZ}
        while end < len(self.program):
            op = Op(self.program[end].opcode)
            if op not in simple_ops:
                break
            end += 1
        if end == start_pc:
            end += 1

        block_instrs = self.program[start_pc:end]
        self.block_meta[start_pc] = BlockMeta(start_pc=start_pc, end_pc_exclusive=end)
        self.profiler.block_compiles += 1

        def run_block(trace: TraceFn | None = None) -> int:
            executed = 0
            for instr in block_instrs:
                if self.halted:
                    break
                self._execute_single(instr, trace=trace)
                executed += 1
                # If control flow changed unexpectedly, stop block execution.
                if self.pc != start_pc + executed:
                    break
            return executed

        return run_block

    def invalidate_blocks_for_addr(self, addr: int) -> None:
        """Invalidate blocks affected by writes in code mirror region."""
        if addr < self.code_base:
            return
        pc = (addr - self.code_base) // 4
        to_remove: list[int] = []
        for block_start, meta in self.block_meta.items():
            if meta.start_pc <= pc < meta.end_pc_exclusive:
                to_remove.append(block_start)
        if not to_remove and pc in self.block_cache:
            to_remove.append(pc)
        for block_start in to_remove:
            self.block_cache.pop(block_start, None)
            self.block_meta.pop(block_start, None)
            self.profiler.invalidations += 1

    def step(self, trace: TraceFn | None = None) -> None:
        if self.halted:
            return
        if self.pc < 0 or self.pc >= len(self.program):
            raise RuntimeError(f"pc out of program range: {self.pc}")
        if self.use_block_cache:
            block = self.block_cache.get(self.pc)
            if block is None:
                block = self._compile_block(self.pc)
                self.block_cache[self.pc] = block
            else:
                self.profiler.block_cache_hits += 1
            executed = block(trace=trace)
            if executed == 0:
                # Fallback to single-step if a compiled block immediately exits.
                self._execute_single(self.program[self.pc], trace=trace)
            return
        self._execute_single(self.program[self.pc], trace=trace)

    def run(
        self,
        max_steps: int = 100_000,
        trace: TraceFn | None = None,
        use_block_cache: bool = False,
    ) -> CpuSnapshot:
        self.use_block_cache = use_block_cache
        steps = 0
        while not self.halted and steps < max_steps:
            before = self.cycles
            self.step(trace=trace)
            steps += self.cycles - before
        if not self.halted:
            raise RuntimeError(f"program did not halt within {max_steps} steps")
        return self.snapshot()
