# Colab GPU Matrix

Reference for Google Colab GPU tiers, capabilities, and model fitting guidelines.

## Colab GPU Tiers

| Tier | GPU | CUDA Cap | VRAM | Price | Best For |
|------|-----|----------|------|-------|----------|
| **Free** | Tesla T4 | 7.5 | 15 GB | $0 | <=7B inference, <=3B fine-tuning |
| **Pro** | L4 | 8.9 | 24 GB | $9.99/mo | <=7B fine-tuning, <=13B inference (INT4) |
| **Pro+** | A100 | 8.0 | 40/80 GB | $49.99/mo | <=13B fine-tuning, <=70B inference (INT4) |

## Compute Unit Costs

| GPU | CU/hour | Hours per 100 CU | Cost per hour (extra CUs) |
|-----|---------|-------------------|---------------------------|
| T4 | ~1.76 | ~57 hours | $0.176 |
| L4 | ~4.0 | ~25 hours | $0.40 |
| A100 | ~15 | ~6.7 hours | $1.50 |

## Framework Minimum Requirements

| Framework | Min CUDA Cap | Colab T4 | Colab L4 | Colab A100 | Failure Mode |
|-----------|-------------|----------|----------|------------|--------------|
| Triton | 7.0 | OK (7.5) | OK (8.9) | OK (8.0) | `GPUTooOldForTriton` crash |
| torch.compile | 7.0 | OK (7.5) | OK (8.9) | OK (8.0) | Silent fallback or crash |
| xformers (flash) | 7.5+ | OK (7.5) | OK (8.9) | OK (8.0) | Build failure / ImportError |
| BFloat16 native | 8.0+ | NO (7.5) | OK (8.9) | OK (8.0) | Silent precision loss |

**Key insight:** Colab's T4 does NOT support native BFloat16. Always use `torch.float16` on free tier.

## What Fits Where (Model Sizing)

| Model Size | FP16 VRAM | INT4 VRAM | T4 (15GB) | L4 (24GB) | A100 (80GB) |
|------------|-----------|-----------|-----------|-----------|-------------|
| 1B | 2 GB | 0.5 GB | Inference + Training | Inference + Training | Inference + Training |
| 3B | 6 GB | 1.5 GB | Inference + Training (tight) | Inference + Training | Inference + Training |
| 7B | 14 GB | 3.5 GB | Inference only (tight) | Inference + Training | Inference + Training |
| 13B | 26 GB | 6.5 GB | INT4 inference only | INT4 inference | Inference + Training |
| 70B | 140 GB | 35 GB | No | No | INT4 inference only |

**Training note:** Training requires 2-4x inference VRAM due to optimizer states, gradients, and activations.

## Preflight GPU Validation Code (S11.1)

```python
import torch

if torch.cuda.is_available():
    cap = torch.cuda.get_device_capability(0)
    props = torch.cuda.get_device_properties(0)
    name = props.name
    vram = props.total_memory / 1e9
    
    # Detect Colab tier
    if 'T4' in name:
        tier, dtype = 'Free/Pro', 'torch.float16'
    elif 'L4' in name:
        tier, dtype = 'Pro', 'torch.float16 or torch.bfloat16'
    elif 'A100' in name:
        tier, dtype = 'Pro+', 'torch.bfloat16'
    else:
        tier, dtype = 'Unknown', 'torch.float16'
    
    print(f"GPU: {name}", flush=True)
    print(f"CUDA Capability: {cap[0]}.{cap[1]}", flush=True)
    print(f"VRAM: {vram:.1f} GB", flush=True)
    print(f"Colab Tier: {tier}", flush=True)
    print(f"Recommended dtype: {dtype}", flush=True)
else:
    print("No GPU detected. Go to Runtime > Change runtime type > GPU", flush=True)
```

## Graceful Degradation Code (S11.2)

```python
import os
import torch

cap = torch.cuda.get_device_capability(0) if torch.cuda.is_available() else (0, 0)
vram = torch.cuda.get_device_properties(0).total_memory / 1e9 if torch.cuda.is_available() else 0

# Dtype selection based on Colab GPU
if cap[0] >= 8:
    compute_dtype = torch.bfloat16  # A100, L4
elif cap[0] >= 7:
    compute_dtype = torch.float16   # T4
else:
    compute_dtype = torch.float32   # CPU fallback

# Batch size selection based on VRAM
if vram >= 40:       # A100
    batch_size = 8
elif vram >= 20:     # L4
    batch_size = 4
elif vram >= 12:     # T4
    batch_size = 2
else:                # CPU
    batch_size = 1

print(f"Auto-config: dtype={compute_dtype}, batch_size={batch_size}", flush=True)
```
