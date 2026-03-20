---
name: check
description: "Run preflight validation before running a notebook on Google Colab"
skill: check
---

Invoke the **check** skill to validate a notebook before Colab execution.

This command runs:
- Syntax validation on all code cells (S9.3)
- JSON artifact validation (S16.1.4)
- Import-install alignment check (S4)
- GPU capability gate for T4/L4/A100 (S11)
- The 6-item Colab checklist from PIR-003 (S16.1)
- Drive mount and persistence verification
- Colab Secrets configuration check
- Environment parity check against Colab (Python 3.12, PyTorch 2.8, CUDA 12.6)

Usage: `/check` before running any notebook on Google Colab.

Scripts: `scripts/preflight_check.py`, `scripts/env_parity.py`
