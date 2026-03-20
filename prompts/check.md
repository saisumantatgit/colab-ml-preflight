# colab-ml-preflight: Check (Preflight) Prompt

You are validating an ML notebook before running it on Google Colab.

## Validation Checklist

### Blockers (must fix)
1. `ast.parse()` all code cells
2. `json.load()` all JSON artifacts
3. No pip install + import in same cell
4. No `input()` calls
5. No hardcoded local paths (/Users/, /home/, C:\, /kaggle/)
6. `.total_memory` not `.total_mem`, quoted pip versions

### Warnings (should fix)
7. `flush=True` on all prints
8. GPU capability check present (detect T4/L4/A100)
9. Deterministic: temperature=0.0, do_sample=False
10. Drive mount present for output persistence
11. Colab Secrets configured for gated models
12. No bitsandbytes on Python 3.12 for small model inference

### Automated
```bash
python scripts/preflight_check.py notebook.ipynb --strict
python scripts/env_parity.py notebook.ipynb
```

Report: BLOCKER/WARNING/INFO with S-number. Verdict: PASS or FAIL.
