"""Locate the durable journal without replacing later repairs."""
from pathlib import Path
if __name__=="__main__":
    print(Path(__file__).resolve().parents[2]/"reports/local/ecuflash_dynamic/SETUP_REPAIR_LOG.md")
