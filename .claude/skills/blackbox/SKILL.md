---
name: blackbox
trigger: "After a Colab notebook failure — runtime crash, disconnect, RAM exhaustion, or error"
lifecycle_stage: postmortem
description: "Structured triage for Colab-specific failures using error taxonomy, decision tree, and known-fix lookup"
platform: colab
---

# Blackbox Skill — Colab Failure Triage

When a Colab notebook fails, follow this structured triage protocol. Do NOT ad-hoc debug — use the decision tree first.

## Step 1: Identify the Failure Type

Colab has unique failure modes not found on other platforms:

| Failure | Symptom | Category |
|---------|---------|----------|
| **Runtime disconnected** | "Your session is no longer connected" banner | COLAB.DISCONNECT |
| **RAM crash** | "Your session crashed due to high RAM usage" | RESOURCE.OOM_RAM |
| **GPU preemption** | GPU disappears mid-run (free tier) | COLAB.PREEMPTION |
| **Session timeout** | Notebook stops after 12/24 hours | RESOURCE.TIMEOUT |
| **Idle disconnect** | "Runtime disconnected" after ~90 min idle | COLAB.IDLE |
| **CUDA OOM** | `CUDA out of memory` error | RESOURCE.OOM |
| **Import error** | `ModuleNotFoundError` | ENV.CELL_CACHE |
| **Drive mount failure** | "Drive already mounted" or timeout | COLAB.DRIVE |

## Step 2: Colab Triage Decision Tree

```
START: Your Colab notebook failed.

1. What message did you see?
|
+-- "Your session crashed due to high RAM usage"
|   --> RESOURCE.OOM_RAM
|   --> FIX: Reduce batch_size, load model in 8-bit/4-bit quantization
|   --> FIX: Use `del model; torch.cuda.empty_cache()` between stages
|   --> FIX: Upgrade to Pro+ for more RAM
|
+-- "Your session is no longer connected" / "Runtime disconnected"
|   |
|   +-- Were you actively running code?
|   |   YES --> COLAB.PREEMPTION (free tier GPU preemption)
|   |   |   --> FIX: Save checkpoints every 500 steps to Drive
|   |   |   --> FIX: Upgrade to Pro+ for guaranteed GPU
|   |   |
|   |   NO --> COLAB.IDLE (idle timeout ~90 min)
|   |       --> FIX: Keep browser tab active
|   |       --> FIX: Add periodic output to prevent idle detection
|
+-- "CUDA out of memory"
|   --> RESOURCE.OOM (S11)
|   --> FIX: Reduce batch_size, enable gradient_checkpointing
|   --> FIX: Switch to L4 (Pro) or A100 (Pro+) for more VRAM
|   --> See: GPU matrix (T4=15GB, L4=24GB, A100=80GB)
|
+-- "ModuleNotFoundError" or "ImportError"
|   |
|   +-- "triton.ops" --> ENV.TRITON (S13, S16.1.1)
|   |   FIX: Remove bitsandbytes for <=7B inference-only
|   |
|   +-- Other module --> ENV.CELL_CACHE (S14, S12)
|       FIX: Separate pip install and import into different cells
|       FIX: Restart runtime after installing, then run from import cell
|
+-- "Drive already mounted at /content/drive" 
|   --> COLAB.DRIVE (not an error — this is informational)
|   --> FIX: Skip drive.mount() if already mounted:
|       if not os.path.exists('/content/drive/MyDrive'):
|           drive.mount('/content/drive')
|
+-- "FileNotFoundError" on Drive paths
|   --> COLAB.DRIVE (mount lost after disconnect)
|   --> FIX: Re-mount Drive after reconnecting
|   --> FIX: Check if file path is correct (case-sensitive)
|
+-- "401 Unauthorized" + HuggingFace
|   --> AUTH.GATED (S16.1.3)
|   --> FIX: Set HF_TOKEN in Colab Secrets (sidebar > key icon)
|   --> FIX: Use ungated community mirrors
|
+-- Any Python error (Traceback)
    --> Go to standard triage (Step 3)
```

## Step 3: Standard Error Triage

Run automated classification:

```bash
python scripts/triage.py --error-log error_output.log
```

### Error Taxonomy Quick Reference

| Category | Subcategories | Frequency |
|----------|--------------|-----------|
| **ENV** | TRITON, BNB, XFORMERS, TOKENIZER, CELL_CACHE, METADATA | ~60% |
| **API** | ATTR, DEPRECATED | ~10% |
| **AUTH** | GATED, TOKEN | ~10% |
| **DATA** | JSON, PHANTOM, CORRUPT | ~5% |
| **RESOURCE** | OOM, OOM_RAM, TIMEOUT, DISK | ~10% |
| **LOGIC** | ESCAPING, HANG, INCOMPLETE | ~3% |
| **COLAB** | DISCONNECT, PREEMPTION, IDLE, DRIVE | ~2% |

## Step 4: Post-Fix Protocol

After identifying and applying a fix:
1. Re-run the preflight check: `python scripts/preflight_check.py notebook.ipynb --strict`
2. If runtime was restarted: re-run install cells, then import cells, then continue
3. If Drive was unmounted: re-mount before continuing
4. Check Drive checkpoints for recoverable progress
5. Document the new error pattern in `templates/known_fixes.yaml` if novel

## Colab Recovery Checklist

After a crash or disconnect:
- [ ] Reconnect to runtime (or start new runtime)
- [ ] Re-mount Google Drive
- [ ] Check for saved checkpoints on Drive
- [ ] Load progress from checkpoint (if checkpoint-and-resume pattern was used)
- [ ] Re-run from the appropriate cell (not from the beginning)

## References

- Script: `scripts/triage.py`
- Full taxonomy: `references/error_taxonomy.md`
- Full decision tree: `references/triage_tree.md`
- Known fixes: `templates/known_fixes.yaml`
- Case studies: All 10 in `case_studies/`
