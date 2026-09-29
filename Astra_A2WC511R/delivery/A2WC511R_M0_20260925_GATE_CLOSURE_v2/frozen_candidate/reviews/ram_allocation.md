# ram_allocation

OPEN. State is32 bytes at provisional[FFFF7400,FFFF7420). Actual reset DMA crosses this range. Runtime indirect/DMA lifetime ownership is not established. Task/runtime stacks differ from reset SP; no live RAM write or probing was performed. See validation/local/ABI_ALLOCATION_REVIEW.md.
