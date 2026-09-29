"""RK02 release entrypoint; no provider or executable is launched."""
import sys
sys.dont_write_bytecode=True
from release_rk02 import main
if __name__=='__main__':main()
