# Colab Triage Decision Tree

Structured error diagnosis for failed Colab notebooks. Start from the top and follow branches.

## The Tree

```
START: Your Colab notebook failed.
|
1. What did you see?
|
+-- "Your session crashed due to high RAM usage"
|   --> COLAB.RAM_CRASH
|   FIX: Reduce batch_size, use 8-bit/4-bit quantization
|   FIX: del model; torch.cuda.empty_cache() between stages
|   FIX: Upgrade to Pro+ for more RAM
|
+-- "Your session is no longer connected" / "Runtime disconnected"
|   |
|   +-- Were you actively running code?
|   |   |
|   |   +-- YES (code was executing):
|   |   |   |
|   |   |   +-- Free tier? --> COLAB.PREEMPTION
|   |   |   |   FIX: Checkpoint to Drive every 500 steps
|   |   |   |   FIX: Upgrade to Pro+ for guaranteed GPU
|   |   |   |
|   |   |   +-- Running 12+ hours? --> COLAB.TIMEOUT
|   |   |       FIX: Use checkpoint-and-resume pattern
|   |   |       FIX: Pro+ gives 24 hours max
|   |   |
|   |   +-- NO (notebook was idle):
|   |       --> COLAB.IDLE (~90 min idle timeout)
|   |       FIX: Keep browser tab active / focused
|   |       FIX: Add periodic print() to prevent idle detection
|
+-- "CUDA out of memory"
|   --> RESOURCE.OOM (S11)
|   FIX: Reduce batch_size, gradient_checkpointing=True
|   FIX: T4 has 15GB — try L4 (24GB) or A100 (40GB)
|   See: references/gpu_matrix.md for model sizing
|
+-- "ModuleNotFoundError" or "ImportError"
|   |
|   +-- "triton.ops" --> ENV.TRITON (S13, S16.1.1)
|   |   FIX: Remove bitsandbytes, use float16 directly
|   |
|   +-- Just installed the package? --> ENV.CELL_CACHE (S14, S12)
|   |   FIX: Separate install and import cells
|   |   FIX: Restart runtime after install, then run from import cell
|   |
|   +-- Package not installed --> ENV.CELL_CACHE
|       FIX: Add !pip install in an earlier cell
|
+-- "Drive already mounted" or Drive path errors
|   --> COLAB.DRIVE
|   FIX: Guard: if not os.path.exists('/content/drive/MyDrive'): drive.mount(...)
|   FIX: After reconnect: re-run drive.mount()
|
+-- "FileNotFoundError" on /content/ paths
|   --> DATA.MISSING
|   FIX: Files in /content/ are lost on disconnect
|   FIX: Re-upload or download from Drive/gdown
|
+-- "401 Unauthorized" + HuggingFace
|   --> AUTH.GATED (S16.1.3)
|   FIX: Set HF_TOKEN in Colab Secrets (sidebar > key icon)
|   FIX: from google.colab import userdata; token = userdata.get('HF_TOKEN')
|
+-- "AttributeError: total_mem"
|   --> API.ATTR (S16.1.2)
|   FIX: Use .total_memory not .total_mem
|
+-- "JSONDecodeError"
|   --> DATA.JSON (S16.1.4)
|   FIX: Validate JSON files before use
|
+-- "SyntaxError"
|   --> LOGIC.ESCAPING (S9)
|   FIX: Use %%writefile script.py pattern
|
+-- "No space left on device"
|   --> RESOURCE.DISK
|   FIX: !rm -rf /content/outputs/  (clean temp files)
|   FIX: Save only final model to Drive, not all checkpoints
|
+-- No error but no output for 10+ minutes
|   --> LOGIC.HANG
|   FIX: Check with !nvidia-smi (is GPU active?)
|   FIX: Add heartbeat prints to training loop
|   FIX: First 5-10 min silence is normal (JIT)
|
+-- Other / Unrecognized
    --> UNKNOWN
    ACTION: Copy full traceback, note GPU type and tier
    ACTION: Run: python scripts/triage.py --error-log error.log
```

## Quick Pattern Lookup

| If you see... | It is probably... | Fix |
|---------------|-------------------|-----|
| "session crashed" | COLAB.RAM_CRASH | Reduce batch/quantize |
| "disconnected" (active) | COLAB.PREEMPTION | Checkpoint to Drive |
| "disconnected" (idle) | COLAB.IDLE | Keep tab active |
| `CUDA out of memory` | RESOURCE.OOM | Reduce batch/upgrade tier |
| `triton.ops` | ENV.TRITON | Remove bitsandbytes |
| `ImportError` after install | ENV.CELL_CACHE | Restart runtime |
| `total_mem` | API.ATTR | Use `.total_memory` |
| `401 Unauthorized` + HF | AUTH.GATED | Colab Secrets |
| `JSONDecodeError` | DATA.JSON | Validate before use |
| No output for 30 min | LOGIC.HANG | Check imports, add heartbeats |
