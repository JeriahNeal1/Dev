"""Create explicit synthetic 1MiB test data; never an ECU flash candidate."""
import sys
sys.dont_write_bytecode=True
import json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from host.protocol import sha256,require

def main():
    folder=ROOT/'host/fixtures';folder.mkdir(parents=True,exist_ok=False)
    composite=bytearray(((i*73)^(i>>8)^(i>>16)^0xA5)&255 for i in range(0x100000))
    for address in range(0,0x100000,512):
        composite[address:address+8]=b'ADDR'+address.to_bytes(4,'big')
        composite[address+504:address+512]=b'END!'+address.to_bytes(4,'big')
    for start,end in ((0x86000,0xC0000),(0xCF000,0xFF000)):
        composite[start:end]=b'\xFF'*(end-start)
        for address in range(start,end,512):
            composite[address:address+8]=b'GAP!'+address.to_bytes(4,'big')
            composite[address+504:address+512]=b'GEND'+address.to_bytes(4,'big')
    composite[0x10000:0x11000]=bytes(4096)
    composite[0x11000:0x12000]=b'\xFF'*4096
    composite[0x12000:0x16000]=random.Random(7058).randbytes(0x4000)
    collision_path=Path(r'C:\Dev\Astra_A2WC511R\reports\local\ecuflash_dynamic\coverage_contract\nonblank_crc_equal_ff_4096.bin')
    collision=collision_path.read_bytes();require(sha256(collision)=='16847923994211cacbfad93badfd78df74e5bfa5b3493581f9ed99eafd195877','Sealed collision fixture')
    composite[0x86000:0x87000]=collision
    files={'composite':bytes(composite),'random_705827':random.Random(705827).randbytes(0x100000)}
    report={'schema':1,'artifact_class':'SYNTHETIC_EXECUTION_FIXTURES_NOT_FLASH_IMAGES','physical':False,'fixtures':{}}
    for name,data in files.items():
        path=folder/(name+'.bin');path.write_bytes(data)
        report['fixtures'][name]={'path':str(path),'sha256':sha256(data),'bytes':len(data)}
    report['composite_classes']={'zero_page':'10000..10FFF','FF_page':'11000..11FFF','random_pages':'12000..15FFF','FF_CRC_collision':'86000..86FFF','gap_sentinels':['86000..BFFFF','CF000..FEFFF'],'other':'address-derived with first/last markers each512bytes'}
    (folder/'FIXTURES.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
