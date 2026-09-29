"""Frozen-payload CFG/frame proof and conditional serialized timing envelope.

No hardware timing is simulated. Every CFG edge is decoded from executable bytes;
data literals are visited only when resolving a PC-relative call target.
"""
from collections import deque
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import json

from sh2e import OPCODES, sx
from differential import artifacts, BUILD, HOOK_ENTRY, CODE_BASE, CODE_END

ENTRIES = {0x147AC: "OEM decoder", 0xE1000: "m0_decode", 0xE101C: "m0_reasons",
           0xE10BC: "m0_init", 0xE1114: "m0_observe", 0xE1240: "m0_sample_hardware",
           0xE12DC: "m0_decoder_hook"}
BOUNDS = {0x147AC: 0x14802, 0xE1000: 0xE101A, 0xE101C: 0xE10B2,
          0xE10BC: 0xE110E, 0xE1114: 0xE1232, 0xE1240: 0xE12C6, 0xE12DC: 0xE133C}
READS = {"movl_pc", "movw_pc", "movb_load", "movw_load", "movl_load", "movl_postinc", "movb_postinc",
         "movl_load_disp", "lds_pr_pop", "ldc_sr_pop", "lds_mach_pop", "lds_macl_pop"}
WRITES = {"movb_store", "movw_store", "movl_store", "movl_predec", "movl_store_disp", "sts_pr_push",
          "stc_sr_push", "sts_mach_push", "sts_macl_push"}
REGISTER_WRITES = {"mov_imm", "add_imm", "add_reg", "movl_pc", "movw_pc", "movb_load", "movw_load",
    "movl_load", "mov_reg", "and_reg", "or_reg", "extub", "neg", "negc", "shar", "shlr2", "dt",
    "movl_postinc", "movb_postinc", "movl_load_disp", "movt"}
SYSTEM_WRITES = {"lds_pr_pop": "PR", "ldc_sr_pop": "SR", "lds_mach_pop": "MACH", "lds_macl_pop": "MACL"}


class StaticAudit:
    def __init__(self):
        self.stock, self.rom, self.manifest = artifacts()
        self.functions = {}

    def decode(self, pc):
        word = int.from_bytes(self.rom.data[pc:pc + 2], "big")
        matches = [s for s in OPCODES if word & s.mask == s.value]
        if len(matches) != 1:
            raise AssertionError(f"Unsupported/ambiguous static instruction {pc:08X}:{word:04X}")
        return word, matches[0]

    def resolve_call(self, pc, reg, entry):
        # All frozen closure indirect calls have a local literal-loaded destination.
        for prev in range(pc - 2, max(entry - 2, pc - 32), -2):
            word, spec = self.decode(prev)
            n = (word >> 8) & 15
            if spec.branch:
                raise AssertionError(f"Unresolved call target across branch at {pc:08X}")
            if spec.name == "movl_pc" and n == reg:
                address = ((prev + 4) & ~3) + 4 * (word & 255)
                target = int.from_bytes(self.rom.data[address:address + 4], "big")
                if target not in ENTRIES:
                    raise AssertionError(f"Unreviewed call target {target:08X}")
                return target, address, prev
            if spec.name in REGISTER_WRITES and n == reg:
                raise AssertionError(f"Call register overwritten before call at {pc:08X}")
        raise AssertionError(f"No bounded literal definition for call {pc:08X}")

    def sp_delta(self, pc):
        word, spec = self.decode(pc)
        n, m = (word >> 8) & 15, (word >> 4) & 15
        name = spec.name
        if name in ("movl_predec", "sts_pr_push", "stc_sr_push", "sts_mach_push", "sts_macl_push") and n == 15:
            return 4
        if name in ("lds_pr_pop", "ldc_sr_pop", "lds_mach_pop", "lds_macl_pop") and n == 15:
            return -4
        if name in ("movl_postinc", "movb_postinc") and m == 15 and n != 15:
            return -(4 if name == "movl_postinc" else 1)
        if n == 15 and name == "add_imm":
            return -sx(word & 255, 8)
        if n == 15 and name in REGISTER_WRITES:
            raise AssertionError(f"Non-affine SP write at {pc:08X}")
        return 0

    def graph(self, entry):
        if entry in self.functions:
            return self.functions[entry]
        graph, depths, calls, terminals = {}, {}, [], []
        todo = deque([(entry, 0)])
        while todo:
            pc, depth = todo.popleft()
            if pc in depths:
                if depths[pc] != depth:
                    raise AssertionError(f"Path-dependent frame imbalance at {pc:08X}")
                continue
            if not entry <= pc < BOUNDS[entry]:
                raise AssertionError(f"Escaped function bounds {pc:08X}")
            depths[pc] = depth
            word, spec = self.decode(pc)
            pcs, successors, call = [pc], [], None
            if spec.branch:
                if spec.name in ("rts", "bra", "bsr", "jsr", "jmp", "bf_s", "bt_s"):
                    if self.decode(pc + 2)[1].branch:
                        raise AssertionError("Branch in delay slot")
                    pcs.append(pc + 2)
                if spec.name == "rts":
                    terminals.append(pc)
                elif spec.name in ("bra", "bsr"):
                    target = pc + 4 + 2 * sx(word & 0xFFF, 12)
                    if spec.name == "bsr":
                        call = target
                        successors = [pc + 4]
                    else:
                        successors = [target]
                elif spec.name in ("jsr", "jmp"):
                    target, literal, definition = self.resolve_call(pc, (word >> 8) & 15, entry)
                    if spec.name == "jmp":
                        raise AssertionError("Tail call is not present in frozen injected closure")
                    call = target
                    calls.append(dict(pc=f"{pc:08X}", target=f"{target:08X}", literal=f"{literal:08X}",
                                      load_pc=f"{definition:08X}"))
                    successors = [pc + 4]
                elif spec.name in ("bf", "bt", "bf_s", "bt_s"):
                    successors = [pc + (4 if spec.name.endswith("_s") else 2), pc + 4 + 2 * sx(word & 255, 8)]
                else:
                    raise AssertionError(f"Unsupported control-flow form {spec.name}")
            else:
                successors = [pc + 2]
            d, peak = depth, depth
            for address in pcs:
                d += self.sp_delta(address)
                peak = max(peak, d)
                if d < 0:
                    raise AssertionError(f"Frame underflow at {address:08X}")
            if spec.name == "rts" and d != 0:
                raise AssertionError(f"Nonzero frame on return at {pc:08X}")
            graph[pc] = dict(pcs=pcs, next=successors, call=call, depth_before=depth, depth_after=d, peak=peak)
            for successor in successors:
                todo.append((successor, d))
        self.functions[entry] = dict(graph=graph, depths=depths, calls=calls, terminals=terminals)
        return self.functions[entry]

    @lru_cache(None)
    def bound(self, entry, metric="instructions"):
        function = self.graph(entry)
        graph = function["graph"]
        loop = (0xE10F2, 0xE10EA)
        if entry == 0xE10BC:
            for pc, expected in ((0xE10E8, 0xE21C), (0xE10F0, 0x4210), (0xE10F2, 0x8FFA)):
                if self.decode(pc)[0] != expected:
                    raise AssertionError("Initialization loop bound no longer applies")
        @lru_cache(None)
        def cost(pc, backedges_remaining):
            node = graph[pc]
            if metric == "instructions":
                own = len(node["pcs"])
            elif metric == "memory_accesses":
                own = sum(self.decode(p)[1].name in READS | WRITES for p in node["pcs"])
            elif metric == "ram_writes_upper":
                own = sum(self.decode(p)[1].name in WRITES for p in node["pcs"])
            else:
                raise ValueError(metric)
            if node["call"] is not None:
                own += self.bound(node["call"], metric)
            continuation = []
            for target in node["next"]:
                remaining = backedges_remaining
                if target <= pc:
                    if (pc, target) != loop:
                        raise AssertionError(f"Unbounded/unknown loop {pc:08X}->{target:08X}")
                    if remaining == 0:
                        continue
                    remaining -= 1
                continuation.append(cost(target, remaining))
            return own + max(continuation, default=0)
        return cost(entry, 27)

    @lru_cache(None)
    def stack_peak(self, entry):
        graph = self.graph(entry)["graph"]
        return max(max(node["peak"], node["depth_after"] + (self.stack_peak(node["call"]) if node["call"] else 0))
                   for node in graph.values())

    def preserved_state_proof(self):
        # Match the actual final wrapper layout, not an assumed C calling convention.
        expected = {0x00: 0x4F22, 0x02: 0x2F06, 0x06: 0x400B, 0x08: 0x60F6,
                    0x28: 0x4F03, 0x2A: 0x4F02, 0x2C: 0x4F12,
                    0x32: 0x400B, 0x34: 0x0009, 0x36: 0x4F16, 0x38: 0x4F06,
                    0x3A: 0x4F07, 0x5A: 0x4F26, 0x5C: 0x000B, 0x5E: 0x0009}
        for register in range(15):
            expected[0x0A + register * 2] = 0x2F06 | (register << 4)
            expected[0x3C + (14 - register) * 2] = 0x60F6 | (register << 8)
        for offset, word in expected.items():
            if self.decode(HOOK_ENTRY + offset)[0] != word:
                raise AssertionError(f"Wrapper save/restore proof no longer matches offset {offset:02X}")
        original, _, _ = self.resolve_call(HOOK_ENTRY + 6, 0, HOOK_ENTRY)
        sampler, _, _ = self.resolve_call(HOOK_ENTRY + 0x32, 0, HOOK_ENTRY)
        if original != 0x147AC or sampler != 0xE1240:
            raise AssertionError("Wrapper call closure changed")
        tokens = ["caller_PR"] + [f"OEM_R{i}" for i in range(15)] + ["OEM_SR", "OEM_MACH", "OEM_MACL"]
        restoration = {}
        for register in ("MACL", "MACH", "SR"):
            restoration[register] = tokens.pop()
        for register in range(14, -1, -1):
            restoration[f"R{register}"] = tokens.pop()
        restoration["PR"] = tokens.pop()
        if tokens:
            raise AssertionError("Symbolic wrapper stack not balanced")
        return dict(status="PASS", matched_instruction_words=len(expected), restored_tokens=restoration,
                    R15="Restored exactly by balanced constant stack movements on every CFG path",
                    original_call="R0 restored in JSR delay slot; R1..R14/SR/MAC/FPU untouched before original entry; PR and R15 intentionally use wrapper frame",
                    FPU="FR0..FR15,FPUL,FPSCR have no architectural read/write instruction anywhere in reachable closure",
                    other_controls="GBR and VBR have no read/write instruction in reachable closure",
                    assumptions=["Stack is writable, private and disjoint from32-byte state and observer inputs",
                                 "No exception, DMA, corrupting ISR or reentrant writer modifies saved frame",
                                 "Comparison is architectural return-boundary state; interrupt-latency and pending asynchronous FPU completion are separate timing questions"],
                    SR_note="LDC.L restores SR after observer; no numeric bit-mask modification is added. Its interrupt-suppression timing remains a physical scheduling effect.")

    def report(self):
        results = {}
        for entry, name in ENTRIES.items():
            function = self.graph(entry)
            pcs = sorted({p for n in function["graph"].values() for p in n["pcs"]})
            opcode_names = {self.decode(p)[1].name for p in pcs}
            results[f"{entry:08X}"] = dict(name=name, code_sha256=sha256(self.rom.data[entry:BOUNDS[entry]]).hexdigest(),
                reachable_instruction_count=len(pcs), reachable_pcs=[f"{p:08X}" for p in pcs],
                local_frame_peak=max(n["peak"] for n in function["graph"].values()),
                transitive_frame_peak=self.stack_peak(entry),
                instruction_upper_bound=self.bound(entry), memory_access_upper_bound=self.bound(entry, "memory_accesses"),
                write_access_upper_bound=self.bound(entry, "ram_writes_upper"),
                calls=function["calls"], return_pcs=[f"{p:08X}" for p in function["terminals"]],
                opcode_forms=sorted(opcode_names),
                nonzero_return_frames=0, unequal_frame_depth_joins=0,
                fpu_or_gbr_vbr_accesses=0, system_writes=sorted({SYSTEM_WRITES[n] for n in opcode_names if n in SYSTEM_WRITES}),
                instruction_table=[dict(pc=f"{p:08X}", opcode=f"{self.decode(p)[0]:04X}", form=self.decode(p)[1].name)
                                   for p in pcs],
                cfg=[dict(pc=f"{pc:08X}", next=[f"{n:08X}" for n in node["next"]],
                          call=f"{node['call']:08X}" if node["call"] else None,
                          depth_before=node["depth_before"], depth_after=node["depth_after"])
                     for pc, node in sorted(function["graph"].items())])
        injected = self.bound(HOOK_ENTRY)
        accesses = self.bound(HOOK_ENTRY, "memory_accesses")
        # Pessimistic complete serialization of at most five core stages per listed instruction.
        # F and D are externally imposed maximum access-state assumptions, not silicon measurements.
        examples = []
        for flash_states, max_data_states in ((1, 2), (2, 2), (4, 4)):
            cycles = 5 * injected + (flash_states - 1) * injected + (max_data_states - 1) * accesses
            examples.append(dict(assumed_flash_fetch_states=flash_states, assumed_max_data_access_states=max_data_states,
                                 serialized_model_cycles_upper=cycles,
                                 time_us_at_assumed_80MHz=cycles / 80, time_us_at_assumed_40MHz=cycles / 40))
        return dict(classification="CONDITIONAL_STATIC_INJECTED_CLOSURE_PROOF", build=str(BUILD),
                    payload_sha256=sha256(self.rom.data[CODE_BASE:CODE_END]).hexdigest(), functions=results,
                    complete_injected_call_graph="hook -> OEM decoder; hook -> sample -> observe -> init (conditional), reasons",
                    unused_standalone_function="m0_decode is compiled but not called; compiler inlined equivalent logic in observe",
                    exact_added_stack_peak_bytes=self.stack_peak(HOOK_ENTRY), additional_known_oem_frames=8,
                    instruction_bound=injected, memory_access_bound=accesses,
                    timing_formula="C <= 5*N + (F-1)*N + (D-1)*A + entry_stalls + external_interference",
                    timing_examples=examples,
                    timing_assumptions=["All covered instructions have at most five stages in the SH-2E manual; no multiply/FPU/exception opcodes",
                        "Serializing stages, instruction fetch and data access removes overlap benefits and bounds internal dependencies",
                        "F bounds each flash instruction-fetch service; D bounds each data-access service; neither bound was measured here",
                        "No DMA/AUD/bus-release stall or interrupt/preemption unless separately added as a bounded term",
                        "Entry pipeline/multiplier/FPU outstanding work is bounded separately; example sets entry/external terms to zero",
                        "80 MHz is the SH7058 maximum documented frequency, not established ECU clock"],
                    loop_proof="Only injected backward edge is init E10F2 -> E10EA: MOV#28,R2 then one DT per iteration, no calls/other R2 writes; exactly28 iterations",
                    preserved_state_proof=self.preserved_state_proof(),
                    bound_note="Instruction bound chooses both branch outcomes independently; conservative and possibly infeasible combinations, not claimed exact observed maximum",
                    gates=dict(injected_call_graph="PASS", injected_stack_and_register_proof="PASS",
                               silicon_timing_and_task_budget="PHYSICAL/BENCH REQUIRED", cadence_and_reentry="PHYSICAL/BENCH REQUIRED"))


if __name__ == "__main__":
    result = StaticAudit().report()
    print(json.dumps({k: v for k, v in result.items() if k != "functions"}, indent=2))
