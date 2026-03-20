# colab-ml-preflight Rules for Cursor (Google Colab)

## Notebook Construction Rules
1. temperature=0.0, do_sample=False for all inference
2. %%writefile pattern for scripts — never logic in JSON
3. pip install and import MUST be in separate cells
4. All print() must have flush=True
5. No input() — use Colab Secrets instead
6. Seeds in Cell 1: torch, numpy, random
7. Mount Drive EARLY: drive.mount('/content/drive')
8. Save to /content/drive/MyDrive/, NEVER just /content/
9. Use Colab Secrets for tokens: userdata.get('HF_TOKEN')
10. Checkpoint to Drive every 500 steps

## Pre-Run Rules
11. ast.parse() all Python code
12. json.load() all JSON artifacts
13. GPU capability check (detect T4/L4/A100 tier)
14. No bitsandbytes for <=7B inference on Python 3.12
15. .total_memory not .total_mem
16. Colab Secrets for gated models
17. Quote pip versions: "pkg==1.0.0"

## While Running
18. In-notebook heartbeats (no external polling API)
19. !nvidia-smi for GPU checks
20. Monitor RAM — crash at >90%

## Scripts
- preflight_check.py: Validate before run (no --platform needed)
- env_parity.py: Check Colab env compatibility
- poll_monitor.py: In-notebook health monitor
- triage.py: Classify Colab errors
