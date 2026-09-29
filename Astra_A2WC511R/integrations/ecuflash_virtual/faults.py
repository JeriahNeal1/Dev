"""One-shot deterministic faults at reviewed virtual protocol boundaries.

Each fault changes only a fake transport result or fake ECU reply. No physical
device, clock, process or persistent configuration API is used here.
"""
class FaultPlan:
    NAMES=('identity_timeout','session_timeout','upload_begin_timeout',
           'upload_middle_timeout','upload_end_timeout','kernel_start_timeout',
           'read_first_timeout','read_middle_timeout','read_final_timeout',
           'read_malformed','read_checksum','read_disconnect')

    def __init__(self,name=None):
        if name is not None and name not in self.NAMES:raise ValueError('Unknown fault plan')
        self.name=name;self.fired=False

    def match(self,wire):
        if not self.name or self.fired:return None
        if type(wire) is not bytes or len(wire)<6 or wire[-1]!=(sum(wire[:-1])&255):return None
        if wire.startswith(b'\x80\x10\xf0'):
            if len(wire)!=wire[3]+5:return None
        elif wire.startswith(b'\xbe\xef'):
            if len(wire)!=int.from_bytes(wire[2:4],'big')+5:return None
        else:return None
        payload=wire[4:-1]
        if not payload:return None
        wanted={'identity_timeout':b'\xbf','session_timeout':bytes.fromhex('108502'),
                'upload_begin_timeout':bytes.fromhex('36ff3000'),
                'upload_middle_timeout':bytes.fromhex('36ff3900'),
                'upload_end_timeout':bytes.fromhex('36ff4200'),
                'kernel_start_timeout':bytes.fromhex('310101')}
        if self.name in wanted:hit=wire.startswith(b'\x80') and payload.startswith(wanted[self.name])
        else:
            address={'read_middle_timeout':0x80000,'read_final_timeout':0xFFE00}.get(self.name,0)
            hit=wire.startswith(b'\xbe\xef') and len(payload)==7 and payload[0]==3 and int.from_bytes(payload[1:5],'big')==address
        if not hit:return None
        self.fired=True
        action='timeout' if self.name.endswith('_timeout') else self.name.removeprefix('read_')
        return {'name':self.name,'action':action,'one_shot':True,
                'basis':'DELIBERATE_FAKE_TRANSPORT_FAULT_NOT_OBSERVED_HARDWARE',
                'trigger_wire_hex':wire.hex()}
