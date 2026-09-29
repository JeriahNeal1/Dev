"""Read-only, hash-pinned import of the existing narrow SH-2E interpreter."""
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys

CORE_PATH=Path(r'C:\Dev\A2WC511R_Sim\sh2e.py')
CORE_SHA256='b47ac261634c116c3ffcdf19da9ec73e7014c034cd349ea8867f5f54895cdfff'
if sha256(CORE_PATH.read_bytes()).hexdigest()!=CORE_SHA256:
    raise RuntimeError('Frozen SH-2E core identity mismatch')
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('_readkernel_frozen_sh2e',CORE_PATH)
sh2e=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=sh2e
spec.loader.exec_module(sh2e)
SimulationStop=sh2e.SimulationStop
