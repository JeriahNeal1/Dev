"""Regression of actual OEM ROM instructions; no peripheral or instruction stubs."""
import unittest, sys, json, hashlib
from pathlib import Path
sys.path.insert(0,'C:/Dev/A2WC511R_Sim')
from sh2e import ROM, Memory, CPU, FunctionHarness, STOCK_SHA256
OUT=Path(__file__).parent
STOCK=ROM.load('C:/Dev/SubaruRoms/OEM/A2WC511R.bin',STOCK_SHA256)
EVIDENCE=[]

class ROMRoutineTests(unittest.TestCase):
    def test_rolling_bound_negative_control_detects_hole_read(self):
        changed=STOCK.with_overlay(0x7A820,(0xCE756).to_bytes(4,'big'),'negative control: wrong exclusive ROM scan bound')
        m=Memory(changed)
        m.initialize(0xFFFF6FD8,(0xCE754).to_bytes(4,'big')+(0x2034).to_bytes(4,'big')+b'\0'*6)
        m.watch(0xCE754,0xFFAF8,'hole_read_negative_control')
        h=FunctionHarness(m,[(0x7A77C,0x7A7EC),(0x7A828,0x7A8A6),(0x4760,0x4780)])
        h.cpu.track_control_sources=False
        r=h.run(0x7A77C,allowed_writes=[(0xFFFF6FD8,0xFFFF6FE6)],max_steps=16000)
        hits=[e for e in m.events if e['watchpoints']]
        self.assertEqual([(e['address'],e['pc']) for e in hits],[('000CE754','0007A7C2')])
        EVIDENCE.append({'test':'negative_wrong_exclusive_bound','expected_hole_reads':hits,**r})

    def test_checksum_range_validation_fa84(self):
        cases=[(0x2000,0xFFAF7,0),(0,0,0),(0x2000,0x2000,0),(0x2000,0x2002,1),
               (0x2001,0x2003,1),(0x2004,0x2003,1),(0x2000,0x2003,0)]
        for lo,hi,want in cases:
            with self.subTest(lo=lo,hi=hi):
                m=Memory(STOCK);h=FunctionHarness(m,[(0xFA84,0xFAAA)])
                r=h.run(0xFA84,registers={4:lo,5:hi})
                self.assertEqual(h.cpu.r[0],want)
                EVIDENCE.append({'test':'FA84','start':lo,'end':hi,'result':want,**r})

    def test_rolling_rom_checksum_excludes_entire_holes(self):
        for cal,code in [(0xC0034,0x2034),(0xCE650,0x2034),(0xCE752,0x2034),
                         (0xCE754,0x2034),(0xCE754,0x858B2),(0xCE754,0x859BC)]:
            with self.subTest(cal=cal,code=code):
                m=Memory(STOCK)
                m.initialize(0xFFFF6FD8,cal.to_bytes(4,'big')+code.to_bytes(4,'big')+b'\0'*6)
                m.watch(0xCE754,0xFFAF8,'entire_provisional_hole')
                m.watch(0x859BC,0xC0000,'entire_alternative_hole')
                h=FunctionHarness(m,[(0x7A77C,0x7A7EC),(0x7A828,0x7A8A6),(0x4760,0x4780)])
                h.cpu.track_control_sources=False # exact address/data provenance retained; bounded arithmetic test
                if code>=0x858B4 and cal>=0xCE754:
                    # Run actual entry/guards until before the finishing-helper call.
                    cpu=h.cpu;cpu.r[15]=h.stack[1];cpu.pc=0x7A77C;cpu.pr=0xFFFFFFFC
                    cpu.call_context=['0007A77C'];m.write_allowlist=[(0xFFFF6FD8,0xFFFF6FE6),h.stack]
                    for _ in range(1000):
                        cpu.step()
                        if cpu.pc==0x7A87E and not cpu.pending:break
                    else:self.fail('completed-region guards failed to reach finishing-helper boundary')
                    self.assertFalse([e for e in m.events if e['watchpoints']])
                    self.assertFalse([e for e in m.events if e['pc'] in ('0007A7C2','0007A852')])
                    EVIDENCE.append({'test':'7A77C_completed_guard_fragment','cal_pointer':cal,'code_pointer':code,
                        'stop_before_helper':0x7A87E,'steps':len(cpu.trace),'hole_reads':0,
                        'trace_sha256':hashlib.sha256(json.dumps(cpu.trace,sort_keys=True).encode()).hexdigest()})
                    continue
                r=h.run(0x7A77C,allowed_writes=[(0xFFFF6FD8,0xFFFF6FE6)],max_steps=16000)
                self.assertFalse([e for e in m.events if e['watchpoints']])
                reads=[int(e['address'],16) for e in m.events if e['mode']=='r' and e['pc'] in ('0007A7C2','0007A852')]
                expected=min(128,(0xCE754-cal)//2) if cal<0xCE754 else min(128,(0x858B4-code)//2)
                self.assertEqual(len(reads),expected)
                self.assertEqual(reads,list(range(cal if cal<0xCE754 else code,(cal if cal<0xCE754 else code)+2*expected,2)))
                EVIDENCE.append({'test':'7A77C','cal_pointer':cal,'code_pointer':code,'read_count':len(reads),
                    'read_first':reads[0],'read_last':reads[-1],'hole_reads':0,**r})

    def test_actual_additive_loop_f75e_boundary_and_payload_chunks(self):
        rawpath=Path('C:/Dev/Astra_A2WC511R/work/patches/m0_final_05/A2WC511R.M0.EXPERIMENTAL_UNAPPROVED.raw.bin')
        raw=ROM.load(rawpath,'8092a20fd37f17dd351d18c805fdf195c2207af9adecca25e388146c7a9acc37')
        for rom in [STOCK,raw]:
            for start,end in [(0xCE750,0xCE790),(0xE1000,0xE1040),(0xE1324,0xE1364),(0xFFAB8,0xFFAF8)]:
                m=Memory(rom);m.watch(0xCE754,0xFFAF8,'whole_hole')
                cpu=CPU(m,[(0xF75E,0xF768)],(0xFFFFBE00,0xFFFFBFA0))
                cpu.r[15]=0xFFFFBFA0;cpu.r[14]=start;cpu.r[4]=end;cpu.r[12]=0x12345678
                cpu.pc=0xF75E;cpu.track_control_sources=False
                for _ in range(1000):
                    cpu.step()
                    if cpu.pc==0xF766 and not cpu.pending:break
                else:self.fail('checksum loop failed to terminate')
                expected=(0x12345678+sum(int.from_bytes(rom.data[a:a+4],'big') for a in range(start,end,4)))&0xffffffff
                self.assertEqual(cpu.r[12],expected);self.assertEqual(cpu.r[14],end)
                reads=[int(e['address'],16) for e in m.events if e['mode']=='r']
                self.assertEqual(reads,list(range(start,end,4)))
                EVIDENCE.append({'test':'F75E','rom_sha256':rom.sha256,'start':start,'end':end,'sum':expected,
                   'read_addresses':reads,'steps':len(cpu.trace),'trace_sha256':hashlib.sha256(json.dumps(cpu.trace,sort_keys=True).encode()).hexdigest()})

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ROMRoutineTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    (OUT/'routine_regression.json').write_text(json.dumps({'pass':result.wasSuccessful(),'tests':result.testsRun,
       'scenarios':EVIDENCE,'limit':'7A77C incomplete finishing FPU path excluded; F75E tests bounded actual loops, not full reset/peripheral execution.'},indent=2))
    sys.exit(not result.wasSuccessful())
