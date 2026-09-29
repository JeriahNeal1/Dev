"""Assemble hash-bound scoped acquisition contracts; never performs acquisition."""
import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
STOCK=Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin')
def pin(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def main():
    raw=STOCK.read_bytes();assert pin(STOCK)['sha256']=='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
    kernel=pin(ROOT/'build/attempt_03/kernel.bin')
    assert kernel['sha256']=='3d70abfb8617b87e1b9c52724fd27ed4066ba231818994e780c8ba3006de273f'
    refs=['BINARY_REVIEW_attempt_03.json','OEM_LOADER_REGRESSION.json','KWP_PRODUCER_REGRESSIONS.json','KWP_WIRE_CONTRACT.json','BOOT_ENTRY_REGRESSIONS.json','BOOT_SETUP_CONTRACT.json','UPLOAD_WIRE_CONTRACT.json','UPLOAD_NEGATIVE_CONTROLS.json']
    for name in refs:
        item=json.loads((HERE/name).read_text());assert item['status'].startswith('PASS'),(name,item['status'])
    blocks=[('quiescence',0x47AFC,0x47C3C),('mask_save_restore',0x2088,0x209C),('mask_enter_exit',0x3AF4,0x3B28),('gpio_mask_helpers',0x4ACC,0x4B1C)]
    # Record exact reviewed object bytes, including referenced constants where
    # necessary. These are provenance bounds, not newly asserted IDA ownership.
    blocks=blocks[:4]+[('zero_scaler_code',0xAC9A,0xACCA),('zero_scaler_literals',0xACDC,0xACFC),('fixedpoint_product',0x2390,0x2424),('zero_pair_writer',0x8384,0x83AE),('zero_pair_literals',0x848C,0x8498),('marker',0xF6FE,0xF706),('boot_and_loader',0x1008,0x1F44)]
    code=[{'name':n,'start':f'{a:08X}','end_exclusive':f'{b:08X}','sha256':hashlib.sha256(raw[a:b]).hexdigest()} for n,a,b in blocks]
    gpio=[('00047B28','FFFFF746','PDDR','OR','0200'),('00047B46','FFFFF746','PDDR','OR','0800'),('00047B64','FFFFF754','PEDR','OR','0001'),('00047B78','FFFFF754','PEDR','OR','0002'),('00047B92','FFFFF754','PEDR','AND_NOT','0040'),('00047BA8','FFFFF76C','PJDR','AND_NOT','0004'),('00047BB2','FFFFF76C','PJDR','AND_NOT','0005'),('00047BC4','FFFFF75E','PLDR','OR','0040'),('00047BDA','FFFFF75E','PLDR','OR','0080'),('00047BEC','FFFFF76C','PJDR','OR','0040')]
    physical=[
      'Actual ECU must have the pinned stock-compatible acquisition code, vectors, constants and active user-MAT view; BF/CAL identity alone is not byte attestation.',
      'Successful ordinary KWP state and accepted SCI2 RXI response-echo caller, SR.I1..15; unexpected direct mask0 calls are not admitted.',
      'OEM programming-admission inputs/timer or ADC condition must occur physically; no bypass is supplied. The regression uses PFDRbit6 andPLDRbit2 low for at least78 timer ticks.',
      'No corrupting DMA, unexpected nested interrupt/NMI/exception, reset or power loss during upload and before the owned kernel disables DMA and installs its private state. OEM4ACC temporarily uses I14; NMI is never masked.',
      'Clock/baud, real UART and adapter behavior, electrical GPIO/FWE coupling, external watchdog and stable RAM/power must be validated physically.',
      'Owned binary must reach RAM intact. Additive packet checksums and OEMlow16sum5AA5 do not authenticate arbitrary corruption.',
      'Exit requires verified loss of ECU operating power/reset and subsequent OEM identity; no timed key-off or adapter Disconnect claim substitutes for this.'
    ]
    out={'schema':1,'artifact_class':'TEMP_RAM_ACQUISITION_TOOL','status':'PASS','scope':'Conditional offline fixed-protocol and bounded actual-stock entry contract; not current-vehicle or physical qualification',
      'kernel_sha256':kernel['sha256'],'stock_rom':pin(STOCK),'complete_fixed_protocol':True,'security_preserved':True,'flash_controller_stores_on_admitted_path':0,
      'admitted_entry':{'caller':'Actual SCI2 RXI vector209: VBRFFC50 +344 -> ROMFFF94=31FC; 340C captures then restores nonzero accepted interrupt mask before device dispatch',
        'call_chain':['31FC','340C','5F84','470C6','47CAE','47E24','4808C','4717E','47AFC','471AE','40','125C','12A4','1314','1440','1670','194C','1C28','FFFF3004'],
        'conditions':['63F0=0 KWP path','Valid response echo and final-TX state','63E0 bit10 selected by validated108502','Acknowledged fixed34/36/31 and low16sum5AA5'],
        'SR_I_at_uploaded_entry':15,'SP_at_uploaded_entry':'FFFFBFA0','VBR_at_uploaded_entry':'00001F44','owned_kernel_reinitializes':['SR','SP','VBR','DMAOR','WDT','privateBSS','guards','SCI2']},
      'protocol':{'native_identity':'BF producer separately retained; does not attest complete ROM','application_requests':['81','8300','2701','2702+actualseedkey','108502'],
        'positive_payloads':['C1EF8F','C30000FF00FF00','6701+4byteseed','670234','5085'],
        'security':'Actual16round seed transform479A0->47AD2->47A4C; 47970 checks key against63EC; cooldown/length/session/lock validation retained unchanged.',
        'upload_declaration':'34FF300004 +BE24(1776); fixedpositivealigned length <=8192','upload_blocks':14,'upload_block_bytes_max':128,'upload_ACK':'76','declaration_ACK':'7484','start_request':'310101','start_ACK':'710101'},
      'quiescence':{'proof_kind':'Actual raw-code call/value-domain derivation plus separately executed mask helpers; floating callees closed by exact+0 inputs and finite ROM constants, not FPU simulation.',
        'closed_callees':['F6FE','2088','2098','4B04','AC9A','2390','3AF4','3B08','8384','4ACC'],
        'scheduler_exclusion':'3AF4 returns callerSR.I mask1..15; 3B08 nonzero branch reaches3B1C before any OS descriptor access. Fifteen masks executed; artificial mask0 visibly fails atFFFF12C8.',
        'RAM_writes':['FFFF2000 word55AA','FFFF2FD8 long0','FFFF2D74 word0','FFFF2E54 word0','FFFF2E56 word0','bounded call stack'],
        'floating_contract':'FLDI0 at47B32 setsFR15 exact+0. AC9A multiplies by ROMACF4 finite65536, converts0, invokes integer2390 withR4=0 andu16R5. 8384 converts ROMCCCB8u16=24, multiplies by+0 and stores0. No data-dependent pointer or called target.',
        'gpio':[{'call_site':c,'address':a,'register':n,'operation':op,'mask':mask,'width':2} for c,a,n,op,mask in gpio],
        'important':'These GPIO changes are additional OEM programming-session effects. They are not claimed to be already-running ordinary task behavior; the owned payload adds no engine-output algorithm.'},
      'initial_boot':{'entry':'125C fromROM1004, not1150 fromROM1000','clock':'1CBE(R4=0) writesword3C00toSYSCR2FFFFF70A thenfourNOP; CKSEL0 CPU4xEXTAL, peripheral2xEXTAL.',
        'callees':['1CBE','1DD4','1B56','1A66','1A5A','14E6','1CDC','1008','1C94','1DB6','1C28','12FE'],
        'peripherals':['GPIOF720..F776 exactlisted31store1B56 initialization','SCI2F010..F016','WDTEC10/EC12','SYSCR2F70A','ADCF818/F819 andconditionalreadF802','PFDRF74E masked80/200','conditionalPDDR F746OR0200','loopGPIOdirection/functionF750/F752/F756/F758/F75A/F75C'],
        'FWE_limit':'No directflashcontroller store or FKEY/SCO/erase/program operation. Quiescence preservesPD8;1B56 writesPDDR3CFF andPDIOR0320 selectingPD8outputlow. This does not prove board-levelFWE voltage or otherGPIOeffects.',
        'DMA_limit':'OEM path has no provenDMAquiescence beforeclockchange/upload; no asynchronous corruptingDMA is an explicitentry assumption, eliminated prospectively onlybyownedDMAOR0.'},
      'loader_store_domains':{'parser_globals':'FFFFBFA0..FFFFBFE4 andboundedstack','fixed_upload':'[FFFF3000,FFFF36F0),444orderedlongstores at1646','generic_loader_warning':'General OEM accepts weaker request combinations; hostfixed positive/alignedboundeddeclaration andorderedblocks are required. Wrong/malformed requests are not granted a universal safety claim.',
        'checksum_warning':'Actual36 decrypts/stores RAM before trailing framechecksum. Negativechecksum givesnoACK afterpossibleRAMwrites; hostmustabort. This doesnotwriteflash.'},
      'reviewed_code_blocks':code,'regression_refs':[pin(HERE/n) for n in refs],
      'manual':{'url':'https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual','revision':'REJ09B0046-0300H Rev3 September2004','sections':['2.1','4.2 SYSCR2','6.3 exceptionacceptance','7.1 SCI2RXIvector209','15 SCI2','21/22GPIO']},
      'physical_assumptions':physical,'physical_operations':0,'unqualified_alternatives':['Artificialmask0 invocationofscheduler3B08','OtherROMorpatchedbootcode','Genericarbitraryloadercommands','Unexpectedasynchronousexecution','Boardpinsemanticsorphysicalpoweroff']}
    (HERE/'OEM_ACQUISITION_CONTRACT.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'scope':out['scope'],'regressions':len(refs),'flash_controller_stores_on_admitted_path':0}))
if __name__=='__main__':main()
