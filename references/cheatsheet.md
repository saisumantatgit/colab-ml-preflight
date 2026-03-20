# colab-ml-preflight Cheatsheet v1.0

## BEFORE BUILDING
```
temperature=0.0, do_sample=False always                    (S1)
Sovereign script via %%writefile, never JSON logic          (S9)
Install cell and import cell MUST be separate               (S12)
All print() must have flush=True                            (S4)
No input() calls — use Colab Secrets instead                (S4)
Set seeds: torch, numpy, random in Cell 1                   (S4)
Mount Google Drive EARLY for output persistence             (COLAB)
Save outputs to /content/drive/MyDrive/, NEVER /content/    (COLAB)
Use Colab Secrets for HF tokens (userdata.get)              (COLAB)
Checkpoint to Drive every 500 steps                         (COLAB)
```

## BEFORE RUNNING
```
ast.parse() on all .py files                                (S9.3)
json.load() on all .json artifacts                          (S16.2)
GPU capability check — detect T4/L4/A100 tier               (S11.1)
No bitsandbytes for <=7B inference on Python 3.12           (S16.1.1)
.total_memory not .total_mem                                (S16.1.2)
Use ungated mirrors when HF token unavailable               (S16.1.3)
No use_fast=False with certain tokenizers                   (S16.1.5)
Quote pip versions: "pkg==1.0.0"                            (S16.1.6)
Verify Drive mount before saving outputs                    (COLAB)
Check Colab Secrets for gated model tokens                  (COLAB)
```

## WHILE RUNNING
```
In-notebook heartbeats every 10 items (no external API)     (S4.5)
!nvidia-smi for GPU status checks                           (COLAB)
Monitor RAM with psutil — crash at >90% usage               (COLAB)
Expect 5-10min silence on first run (JIT)                   (S15)
T4 uses ~1.76 CU/hr, A100 uses ~15 CU/hr                   (COLAB)
Free tier: 12hr max, ~90min idle timeout                    (COLAB)
Pro+: 24hr max, no idle timeout while running               (COLAB)
```

## AFTER FAILURE
```
"Session crashed due to high RAM" = COLAB.RAM_CRASH         (COLAB)
"Runtime disconnected" = COLAB.DISCONNECT or IDLE           (COLAB)
ENV errors are 60% of failures — check env first            (S5)
Re-mount Drive after reconnecting                           (COLAB)
Check Drive checkpoints for recoverable progress            (COLAB)
```

## PROVENANCE (every run)
```
git_commit, model_repo, model_revision, evaluator_file,
input_file, gpu_type, gpu_vram_gb,
package_versions, generation_config                         (S4.4)
```

## SCRIPTS
```
python scripts/preflight_check.py nb.ipynb --strict
python scripts/env_parity.py nb.ipynb
python scripts/poll_monitor.py --check-health
python scripts/triage.py --error-log output.log
```
