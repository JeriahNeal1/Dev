from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3]
src=ROOT/'sim/self_echo.py'
text=src.read_text()
added='''        elif self.reg[SSR]&ORER:
            # SH7058 15.2.6/table15.11: ORER disables subsequent reception
            # until cleared. Preserve the existing unread RDR byte.
            self._event('ECU_self_echo_receiver_error_disabled',value=value)
'''
initial=text.replace(added,'').encode()
report=json.loads((ROOT/'evidence/sim/echo_audit_01/CURRENT_KERNEL_ECHO_FAILURE.json').read_text())
assert hashlib.sha256(initial).hexdigest()==report['model_source']['sha256']
saved=ROOT/'evidence/sim/echo_audit_01/model_before/self_echo_initial.py'
assert not saved.exists();saved.write_bytes(initial)
test=(ROOT/'evidence/sim/echo_audit_01/test_current.py').read_text()
test=test.replace("assert s.peripheral.sci.event_counts['ECU_self_echo_overrun']==len(r.tx_bytes)-1",
 "assert s.peripheral.sci.event_counts['ECU_self_echo_overrun']==1\nassert s.peripheral.sci.event_counts['ECU_self_echo_receiver_error_disabled']==len(r.tx_bytes)-2")
test=test.replace("'Stock programming helper RE-disable evidence is supplied independently by the contracts agent'",
 "'Stock programming helper RE-disable evidence is supplied independently by the contracts agent', 'ORER disables subsequent receives per SH7058 15.2.6 PDF519/table15.11 PDF541. Initial audit01 overcounted overruns; kernel failure classification is unchanged.'")
target=Path(__file__).with_name('test_current.py');assert not target.exists();target.write_text(test)
