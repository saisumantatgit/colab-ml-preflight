# colab-ml-preflight: Blackbox (Postmortem) Prompt

A Colab notebook has failed. Follow structured triage — do NOT ad-hoc debug.

## Protocol
1. **Identify the failure type**: RAM crash, disconnect, GPU preemption, CUDA OOM, import error, or Python error
2. **Classify** using the Colab taxonomy:
   - COLAB: RAM crash, disconnect, preemption, idle timeout, Drive failure
   - ENV: Wrong version, missing package, CUDA conflict
   - AUTH: Gated model, expired token
   - DATA: Corrupt JSON, missing files
   - RESOURCE: OOM, timeout, disk full
   - LOGIC: Escaping bug, hang
3. **Check known fixes**: `templates/known_fixes.yaml`
4. **Recovery**: Reconnect, re-mount Drive, check checkpoints, resume

## Common Colab Fixes (Top 5)
| Error | Fix |
|-------|-----|
| "Session crashed" (RAM) | Reduce batch/quantize |
| "Disconnected" (preemption) | Checkpoint to Drive |
| `CUDA out of memory` | Reduce batch/upgrade tier |
| `ImportError` after install | Restart runtime, separate cells |
| `401 Unauthorized` | Set HF_TOKEN in Colab Secrets |
