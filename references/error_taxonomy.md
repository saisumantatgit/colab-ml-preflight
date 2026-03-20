# Colab Error Taxonomy

7 categories (6 standard + 1 Colab-specific) covering all known Colab notebook failure modes.

## Category Overview

| Category | Description | Frequency | Severity |
|----------|-------------|-----------|----------|
| **COLAB** | Colab-specific failures (disconnect, RAM crash, preemption) | ~15% | CRITICAL |
| **ENV** | Environment mismatch | ~45% | BLOCKER |
| **API** | API surface error | ~5% | BLOCKER |
| **AUTH** | Authentication failure | ~10% | BLOCKER |
| **DATA** | Data artifact error | ~5% | BLOCKER |
| **RESOURCE** | Hardware/quota exhaustion | ~15% | BLOCKER |
| **LOGIC** | Script logic bug | ~5% | BLOCKER |

## COLAB — Colab-Specific Errors

| Subcategory | Symptom | Fix |
|-------------|---------|-----|
| COLAB.RAM_CRASH | "Your session crashed due to high RAM usage" | Reduce batch_size, use quantization, del unused models |
| COLAB.DISCONNECT | "Your session is no longer connected" | Save checkpoints to Drive, use resume pattern |
| COLAB.PREEMPTION | GPU disappears mid-run (free tier) | Checkpoint frequently, upgrade to Pro+ |
| COLAB.IDLE | Disconnect after ~90 min idle | Keep browser active, add periodic output |
| COLAB.DRIVE | Drive mount failure or path not found | Re-mount after reconnect, check path case sensitivity |
| COLAB.TIMEOUT | Session killed at 12hr (free/pro) or 24hr (pro+) | Use checkpointing and resume strategy |

## ENV — Environment Errors

| Subcategory | Pattern | Governance | Fix |
|-------------|---------|------------|-----|
| ENV.TRITON | `ModuleNotFoundError: triton.ops` | S13, S16.1.1 | Remove bitsandbytes |
| ENV.BNB | `bitsandbytes` version conflict | S5, S16.1.1 | Cleanse pattern + restart runtime |
| ENV.XFORMERS | `xformers` build failure | S5 | Use matching wheel or disable flash attention |
| ENV.TOKENIZER | `use_fast=False` TypeError | S5, S16.1.5 | Remove use_fast=False |
| ENV.CELL_CACHE | ImportError after pip install | S14, S12 | Separate cells, restart runtime |
| ENV.METADATA | `importlib-metadata` corruption | S2.A | Cleanse pattern + restart runtime |

## API — API Surface Errors

| Subcategory | Pattern | Governance | Fix |
|-------------|---------|------------|-----|
| API.ATTR | `AttributeError` (e.g., .total_mem) | S16.1.2 | Use .total_memory |
| API.DEPRECATED | Deprecated API usage | S16.1.2 | Check library changelog |

## AUTH — Authentication Errors

| Subcategory | Pattern | Governance | Fix |
|-------------|---------|------------|-----|
| AUTH.GATED | 401 Unauthorized on HuggingFace | S16.1.3 | Colab Secrets or ungated mirrors |
| AUTH.TOKEN | Token expired | S3.1 | Regenerate, update Colab Secrets |

## DATA — Data Errors

| Subcategory | Pattern | Governance | Fix |
|-------------|---------|------------|-----|
| DATA.JSON | JSONDecodeError | S16.1.4 | Validate before use |
| DATA.MISSING | FileNotFoundError on /content/ | COLAB | Re-upload or download from Drive |

## RESOURCE — Resource Errors

| Subcategory | Pattern | Governance | Fix |
|-------------|---------|------------|-----|
| RESOURCE.OOM | CUDA out of memory | S11 | Reduce batch, quantize, upgrade tier |
| RESOURCE.GPU_OLD | GPUTooOldForTriton (rare on Colab) | S13 | Disable torch.compile |
| RESOURCE.TIMEOUT | Exceeded session limit | S15 | Checkpoint + resume |
| RESOURCE.DISK | No space left on device | — | Clean /content/, save to Drive |

## LOGIC — Script Logic Errors

| Subcategory | Pattern | Governance | Fix |
|-------------|---------|------------|-----|
| LOGIC.ESCAPING | SyntaxError from notebook generation | S9 | Use %%writefile |
| LOGIC.HANG | No output for extended period | S15 | Check imports, use heartbeats |

## Detection Difficulty

| Level | Method |
|-------|--------|
| **EASY** | Direct regex match — automated by `triage.py` |
| **MEDIUM** | Requires cell context or version info — semi-automated |
| **HARD** | Log gap analysis or timing inference — manual review |
