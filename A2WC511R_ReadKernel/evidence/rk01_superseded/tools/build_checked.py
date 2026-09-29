"""Compile then enforce the reviewed closed store/entry contract before use.

A new binary hash requires a new independent review. An unreviewed object can
remain development evidence, but this command fails and cannot qualify it.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,importlib.util,json
from build import build,ROOT

def main():
    p=argparse.ArgumentParser();p.add_argument('name');a=p.parse_args()
    manifest=build(a.name)
    spec=importlib.util.spec_from_file_location('readkernel_store_review',ROOT/'evidence/contracts/review_binary.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.review(ROOT/'build'/a.name)
    assert result['flash_stores']==0 and result['prohibited_accesses']==0
    assert result['computed_executable_calls']==0 and result['external_OEM_calls']==0
    assert result['instruction_count']==len(manifest['instruction_addresses'])
    out=ROOT/'build'/a.name/'COMPILE_STATIC_GUARD.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'PASS_COMPILE_AND_FIXED_BINARY_STORE_GUARD','report':str(out),
      'kernel_sha256':manifest['kernel_sha256'],'vehicle_qualified':False}))

if __name__=='__main__':main()
