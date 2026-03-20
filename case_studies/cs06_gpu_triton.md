# CS-06: The GPUTooOldForTriton Cascade

## Colab Relevance: HIGH
While Colab's T4 (CUDA 7.5) is above Triton's minimum (7.0), the bitsandbytes + triton.ops conflict on Python 3.12 is a real issue on Colab.

## The Failure
A fine-tuning notebook crashed at the first forward pass with `GPUTooOldForTriton` on a P100 GPU (CUDA 6.0).

## Colab Context
- Colab T4: CUDA 7.5 — meets Triton minimum (7.0), safe for torch.compile
- Colab L4: CUDA 8.9 — fully compatible with all frameworks
- Colab A100: CUDA 8.0 — fully compatible with all frameworks
- **The real risk on Colab**: bitsandbytes importing triton.ops on Python 3.12

## The Fix
1. Add GPU capability check in Cell 1 (see gpu_matrix.md for code)
2. On Colab T4: use float16, avoid bitsandbytes for <=7B inference
3. On Colab L4/A100: bfloat16 is safe

## Prevention
The check skill validates GPU capability and flags bitsandbytes conflicts.

## Triage Signature
**Category:** RESOURCE.GPU_OLD, ENV.TRITON
**Detection regex:** `GPUTooOldForTriton|ModuleNotFoundError.*triton\.ops`
