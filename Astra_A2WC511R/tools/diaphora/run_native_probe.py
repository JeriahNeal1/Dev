"""Native -S entry, disposable database only, with guaranteed process exit."""
from pathlib import Path
import traceback
import ida_pro
code=0
try:
    probe=Path('C:/Dev/Astra_A2WC511R/tools/diaphora/ida_environment_probe.py')
    exec(compile(probe.read_text(encoding='utf-8'),str(probe),'exec'),globals())
except BaseException:
    Path('C:/Dev/Astra_A2WC511R/reports/local/diaphora/NATIVE_PROBE_FAILURE.txt').write_text(traceback.format_exc(),encoding='utf-8')
    code=1
finally:
    ida_pro.qexit(code)
