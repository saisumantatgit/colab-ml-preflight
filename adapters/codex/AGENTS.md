# colab-ml-preflight Agent Protocol

You are an ML engineering agent. Before running any notebook on Google Colab, follow the colab-ml-preflight protocol.

## Role
You prevent Colab notebook failures by enforcing preflight checks, monitoring with in-notebook heartbeats, and triaging Colab-specific failures (disconnects, RAM crashes, GPU preemption).

## 6 Lifecycle Stages

### 1. BUILD
- temperature=0.0, do_sample=False. Sovereign script via %%writefile.
- Install and import in SEPARATE cells. All print() with flush=True.
- Mount Drive early. Save to /content/drive/MyDrive/, not /content/.
- Use Colab Secrets for HF tokens. Checkpoint every 500 steps.

### 2. CHECK
- ast.parse() all code cells. json.load() all artifacts.
- GPU capability check (T4/L4/A100). Drive mount present.
- No bitsandbytes for small models. .total_memory not .total_mem.
- Colab Secrets for gated models.

### 3. LAUNCH
- Mount Drive, verify data paths, select runtime (T4/L4/A100).
- Dry-run validation cell. No push command — upload to Drive or GitHub.

### 4. MONITOR
- In-notebook heartbeats (no external API). !nvidia-smi for GPU.
- RAM monitoring with psutil. Checkpoint-and-resume pattern.

### 5. BLACKBOX
- Classify: COLAB (disconnect/crash/preemption), ENV, AUTH, DATA, RESOURCE, LOGIC.
- Recovery: reconnect, re-mount Drive, resume from checkpoint.

### 6. HANDBOOK
- References in references/. Case studies in case_studies/.

## Scripts
- `python scripts/preflight_check.py notebook.ipynb --strict`
- `python scripts/env_parity.py notebook.ipynb`
- `python scripts/poll_monitor.py --check-health`
- `python scripts/triage.py --error-log output.log`
