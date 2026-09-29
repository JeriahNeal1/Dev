"""Focused ISA/peripheral regressions and actual reset/fault scenarios.

No active feature fixture or old artifact is modified. Mutations stay in the new
timestamped report directory and are explicitly negative ROM test inputs.
"""
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import boot

STOCK = Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin')
CANDIDATE = Path(r'C:\Dev\Astra_A2WC511R\reports\local\m07_residency\build_audit_02\one_page.RESEARCH_NOT_RESIDENCY_PROVEN.checksum_corrected.bin')
OUT = Path(r'C:\Dev\Astra_A2WC511R\reports\local\prehardware\boot')


def tiny(opcodes, regs=None, scenario=None):
    raw=bytearray(0x100000)
    raw[0x100:0x100+2*len(opcodes)]=b''.join(x.to_bytes(2,'big') for x in opcodes)
    scenario=scenario or boot.Scenario(ram_power_on_byte=None)
    m=boot.BootMemory(boot.sh2e.ROM.synthetic(raw,'focused new-boot opcode regression'),scenario)
    c=boot.BootCPU(m,scenario);c.pc=0x100;c.r[15]=0xFFFFBFA0;c.call_context=['test']
    for reg,val in (regs or {}).items():c._reg(reg,val,{'test:input'})
    return c,m


def main():
    out=OUT/('run_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'))
    out.mkdir(parents=True)
    checks=[]
    def check(name,condition,detail=None):
        checks.append(dict(name=name,status='PASS' if condition else 'FAIL',detail=detail))
        if not condition:raise AssertionError(name)
    def rejects(name,callback,expected):
        try:callback()
        except (boot.Frontier,boot.sh2e.SimulationStop,ValueError) as exc:
            check(name,expected in str(exc),str(exc));return
        check(name,False,'Did not fail closed')
    def persist(name,x):
        p=out/(name+'.json');p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8');return str(p)
    # Exact architectural corner cases for each newly reached instruction.
    for value in [0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF]:
        c,m=tiny([0x6217],{1:value});c.step()
        check(f'NOT_{value:08X}',c.r[2]==(value^0xFFFFFFFF) and c.t==0)
        c,m=tiny([0x4129],{1:value});c.step()
        check(f'SHLR16_{value:08X}',c.r[1]==value//65536 and c.t==0)
        for opcode,signed_result in [(0x4111,value<0x80000000),(0x4115,0<value<0x80000000)]:
            c,m=tiny([opcode],{1:value});c.step();check(f'CMP_{opcode:04X}_{value:08X}',bool(c.t)==signed_result)
    c,m=tiny([0x212E,0x031A],{1:0xABCDFFFF,2:0x1234FFFF});c.mach=0x87654321;c.t=1
    c.step();c.step();check('MULU_word_width_MACL_STS',c.r[3]==0xFFFE0001 and c.mach==0x87654321 and c.t==1)
    c,m=tiny([0x812F],{0:0xAABBCCDD,2:0xFFFF2000});c.step()
    check('MOVW_disp_scaled_lowword_big_endian',m.read(0xFFFF201E,2)[0]==0xCCDD)
    c,m=tiny([0x212A],{1:0xAAAAAAAA,2:0x55555555});c.step();check('XOR_all_bits',c.r[1]==0xFFFFFFFF)
    c,m=tiny([0x412E,0x416A],{1:0xFFFFFFFF});c.step();c.step()
    check('VBR_and_SH7058_fixed_FPSCR_bits',c.vbr==0xFFFFFFFF and c.fpscr==0x58C61)
    c,m=tiny([0xA001,0x6217,0x0009,0x0009],{1:1});c.step();c.step()
    check('extended_opcode_branch_delay_target',c.pc==0x106 and c.r[2]==0xFFFFFFFE)
    c,m=tiny([0x412E,0x0009,0x0009],{1:0},boot.Scenario(irq_at_step=1,irq_is_nmi=True));c.step();c.step()
    rejects('IRQ_after_LDC_deferred_exactly_one',c.step,'IRQ_EXCEPTION_CONTEXT_REQUIRED')
    c,m=tiny([0x0000]);rejects('unsupported_opcode_visible',c.step,'Unsupported SH-2E opcode')
    c,m=tiny([0x0009]);rejects('unknown_MMIO_no_default',lambda:m.read(0xFFFFEEFE,2),'Unknown MMIO')
    rejects('uninitialized_RAM_strict',lambda:m.read(0xFFFF1000,4),'Uninitialized RAM')
    rejects('MMIO_alignment',lambda:m.write(0xFFFFEC21,2,0),'Unaligned')
    rejects('SYSCR2_wrong_key',lambda:m.write(0xFFFFF70A,2,0x8800),'3C key')
    m.write(0xFFFFED18,2,0);check('NMI_readonly_high_not_cleared',m.read(0xFFFFED18,2)[0]==0x8000)
    check('HCAN_reset_mask_not_zero',m.read(0xFFFFD050,2)[0]==65535 and m.read(0xFFFFD852,2)[0]==65535)
    check('HCAN_GSR_reset',m.read(0xFFFFD002,2)[0]==12)
    m.write(0xFFFFD000,2,0);check('explicit_idle_CAN_release',m.read(0xFFFFD002,2)[0]==4)
    rejects('HCAN_readonly_GSR',lambda:m.write(0xFFFFD002,2,0),'read-only')
    rejects('HCAN_mailbox_hole',lambda:m.write(0xFFFFD114,2,0),'reserved')
    rejects('HCAN_transmit_request',lambda:m.write(0xFFFFD022,2,1),'HCAN_TRANSMISSION_REQUEST')
    m.write(0xFFFFEC12,2,0x5A1F);m.write(0xFFFFEC10,2,0x5A00);m.write(0xFFFFEC10,2,0xA53C)
    m.advance(131071);check('WDT_before_overflow',m.wdt['tcnt']==255 and m.wdt['overflows']==0)
    m.advance(1);check('WDT_interval_flag_exact_envelope',m.wdt['tcnt']==0 and m.wdt['tcsr']==0xBC and m.wdt['overflows']==1)
    m.write(0xFFFFEC10,2,0xA53C);check('WDT_flag_clear',m.read(0xFFFFEC10,1)[0]==0x3C)
    rejects('WDT_live_divisor_change',lambda:m.write(0xFFFFEC10,2,0xA53D),'WDT_LIVE_CLOCK_MODE_CHANGE')
    rejects('ADC_invalid_sensor_not_invented',lambda:m.read(0xFFFFF800,2),'ADC_INPUT_MODEL_REQUIRED')
    rejects('SCI_unmodeled_read',lambda:m.read(0xFFFFF005,1),'SCI_STARTUP_MODEL_REQUIRED')
    # Real reset, exact image identity, deterministic replay and existing candidate.
    stock=boot.run_image(STOCK,boot.sh2e.STOCK_SHA256,evidence_dir=out/'stock_traces')
    persist('stock',stock)
    check('stock_real_boot_application_entry',any(x['name']=='application_reset_entry' for x in stock['milestones']))
    check('stock_known_clock_frontier',stock['status']=='CONDITIONAL' and stock['stop']['code']=='CLOCK_OR_RESERVED_SYSCR2' and stock['stop']['pc']=='00004B4C')
    check('stock_SSM_not_claimed',not stock['ssm_readiness']['reached'] and not stock['coverage']['SCI_access_reached'])
    check('fixture_RAM_distinct_from_OEM_write_coverage',stock['coverage']['fixture_initialized_RAM_bytes']==49152 and 0<stock['coverage']['actual_OEM_unique_RAM_written_bytes']<49152)
    replay=boot.run_image(STOCK,boot.sh2e.STOCK_SHA256)
    check('deterministic_replay',stock['semantic_sha256']==replay['semantic_sha256'])
    candidate_sha=sha256(CANDIDATE.read_bytes()).hexdigest()
    comparison=boot.compare_images(STOCK,CANDIDATE,boot.sh2e.STOCK_SHA256,candidate_sha,evidence_dir=out/'comparison_traces')
    persist('stock_vs_frozen_m07',comparison)
    check('candidate_prefix_equal_not_residency_PASS',comparison['status']=='CONDITIONAL' and not comparison['differences'] and comparison['equal_frontier'])
    faults=[]
    for name,scenario,expected in [
        ('nmi_low_wait',boot.Scenario(nmi_high=False,max_steps=1000),'INSTRUCTION_BUDGET'),
        ('tight_stack',boot.Scenario(stack_low=0xFFFFBF90),'SimulationStop'),
        ('strict_RAM_unknown',boot.Scenario(ram_power_on_byte=None),'SimulationStop'),
        ('NMI_at_delayed_call',boot.Scenario(irq_at_step=1,irq_is_nmi=True),'IRQ_EXCEPTION_CONTEXT_REQUIRED'),
        ('IRQ_masked_pending',boot.Scenario(irq_at_step=0,max_steps=500),'INSTRUCTION_BUDGET'),
        ('watchdog_envelope_fault',boot.Scenario(stop_on_timer_overflow=True,cycles_per_instruction=100000),'WDT_OVERFLOW_ENVELOPE'),
        ('CAN_external_model_withheld',boot.Scenario(can_idle_configuration=False),'HCAN_RESET_RELEASE'),
    ]:
        x=boot.run_image(STOCK,boot.sh2e.STOCK_SHA256,scenario)
        check(name,x['stop']['code']==expected,x['stop'])
        faults.append(dict(name=name,status=x['status'],stop=x['stop'],irq=x.get('irq'),scope='Fault detected/model boundary observed; no successful full-boot fault recovery claim'))
    raw=STOCK.read_bytes()
    def mutation(name,address,payload):
        path=out/(name+'.NEGATIVE_TEST_ONLY.bin');path.write_bytes(raw[:address]+payload+raw[address+len(payload):]);return path
    for name,address,payload,expected in [
        ('invalid_SP',4,(0x12345678).to_bytes(4,'big'),'Stack pointer'),
        ('unknown_opcode',0xAAC,b'\x00\x00','Unsupported SH-2E opcode'),
        ('unexpected_branch',0,(0xE1000).to_bytes(4,'big'),'Unsupported SH-2E opcode'),
        ('unknown_MMIO_pool',0xBB4,b'\xEE\xFE','Unknown MMIO'),
    ]:
        p=mutation(name,address,payload);x=boot.run_image(p)
        check(name,x['status']=='FAIL' and expected in x['stop']['detail'],x['stop'])
        faults.append(dict(name=name,status=x['status'],stop=x['stop'],image_sha256=x['image']['sha256']))
    p=mutation('changed_bus_write',0xAC2,b'\xE3\x0C')
    mismatch=boot.compare_images(STOCK,p,scenario=boot.Scenario(max_steps=400))
    check('stock_candidate_external_write_negative',mismatch['status']=='FAIL' and any(d['kind']=='observable_trace' for d in mismatch['differences']))
    persist('differential_negative',mismatch)
    p=mutation('hidden_terminal_register',0x51F8,b'\xE7\x11')
    terminal=boot.compare_images(STOCK,p)
    check('terminal_register_only_difference_detected',terminal['status']=='FAIL' and not terminal['terminal_state_equal']
          and {d['kind'] for d in terminal['differences']}=={'terminal_state'})
    persist('terminal_register_negative',terminal)
    x=boot.run_image(STOCK,'0'*64);check('image_hash_negative',x['status']=='FAIL' and 'mismatch' in x['stop']['detail'])
    faults += [dict(name='invalid_sensor_recovery',status='CONDITIONAL',detail='ADC conversion/sensor consumer not reached from reset; direct guard tested, recovery untested'),
               dict(name='communication_startup',status='CONDITIONAL',detail='Boot CAN configuration reached; application SCI/SSM setup not reached'),
               dict(name='admissible_ISR_execution',status='CONDITIONAL',detail='NMI admission/defer point tested; actual exception stack/handler/RTE unmodeled')]
    summary=dict(schema=1,status='PASS',meaning='Regression checks passed; overall boot remains CONDITIONAL',checks=checks,check_count=len(checks),faults=faults,
                 stock_report=str(out/'stock.json'),comparison_report=str(out/'stock_vs_frozen_m07.json'),stock_stop=stock['stop'],
                 source_hashes=boot.dependencies()+[dict(path=str(Path(__file__).resolve()),sha256=sha256(Path(__file__).read_bytes()).hexdigest())],
                 frozen_M07_residency='FAIL_UNCHANGED',full_boot='CONDITIONAL',SSM_readiness='CONDITIONAL',hardware='NOT_PERFORMED')
    persist('regressions',summary)
    print(json.dumps(dict(status='PASS',checks=len(checks),out=str(out),stock_stop=stock['stop'])))


if __name__=='__main__':main()
