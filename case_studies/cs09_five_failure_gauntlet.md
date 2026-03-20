# CS-09: The Five-Failure Gauntlet

## Colab Relevance: HIGH
All five failures in this gauntlet occur on Colab, magnified by the lack of local validation before running.

## The Failure
Five consecutive notebook runs failed, each revealing a distinct environment mismatch. Total time wasted: ~1 hour. All preventable.

## The Five Sub-Failures on Colab

### v1: ModuleNotFoundError: triton.ops
- **Category:** ENV.TRITON
- **Colab cause:** bitsandbytes imports triton.ops on Colab's Python 3.12
- **Fix:** Remove bitsandbytes for <=7B inference

### v2: AttributeError: total_mem
- **Category:** API.ATTR
- **Colab cause:** Colab's PyTorch 2.8 uses `.total_memory`, not `.total_mem`
- **Fix:** Change to `.total_memory`

### v3: 401 Unauthorized on HuggingFace
- **Category:** AUTH.GATED
- **Colab cause:** No HF token in Colab Secrets
- **Fix:** Set HF_TOKEN in Colab Secrets (sidebar > key icon)

### v4: JSONDecodeError
- **Category:** DATA.JSON
- **Colab cause:** Corrupted JSON file downloaded from Hub
- **Fix:** Validate JSON before use

### v5: TypeError from use_fast=False
- **Category:** ENV.TOKENIZER
- **Colab cause:** Specific tokenizer+version combo on Colab
- **Fix:** Remove use_fast=False

## Prevention
Running `python scripts/preflight_check.py notebook.ipynb --strict` catches all five issues before execution.

## Cost (if not caught)
| Metric | Value |
|--------|-------|
| Failed runs | 5 |
| Time wasted | ~1 hour |
| CU consumed | ~2-8 CU (T4) |
| All preventable | Yes (100%) |
