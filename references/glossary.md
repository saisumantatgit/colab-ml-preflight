# Colab Glossary

Definitions of key terms used throughout colab-ml-preflight.

## Colab-Specific Terms

| Term | Definition |
|------|-----------|
| **Runtime Type** | The compute backend for a Colab notebook: None (CPU), T4 GPU, L4 GPU, A100 GPU, or TPU. Selected via Runtime > Change runtime type. |
| **Hardware Accelerator** | The GPU/TPU selection in Colab's runtime configuration. Determines available VRAM, CUDA capability, and compute unit consumption rate. |
| **Colab Secrets** | Built-in secret storage accessed via sidebar > key icon. Use `from google.colab import userdata; userdata.get('KEY')`. Secrets persist across sessions but require explicit access grants per notebook. |
| **Drive Mount** | `from google.colab import drive; drive.mount('/content/drive')`. Connects Google Drive to `/content/drive/MyDrive/`. Required for persistent storage. Must be re-executed after reconnection. |
| **Compute Units (CU)** | Colab's billing unit for GPU time. T4: ~1.76 CU/hr. L4: ~4 CU/hr. A100: ~15 CU/hr. Pro/Pro+ include 100 CU/month. Additional CUs: $0.10 each. |
| **Idle Timeout** | Free/Pro tier disconnect after ~90 minutes of no interaction. The browser tab must remain active. Pro+ has no idle timeout while code is actively executing. |
| **Session Timeout** | Maximum runtime duration before forced termination. Free/Pro: 12 hours. Pro+: 24 hours. Non-negotiable — use checkpointing for long jobs. |
| **GPU Preemption** | On free tier, Google may reclaim your GPU mid-session for higher-priority users. Results in sudden "session disconnected" with no prior warning. |
| **Runtime Restart** | After installing or upgrading packages, Colab may prompt "Restart Runtime." This clears Python process state but preserves files in /content/. Google Drive must be re-mounted afterward. |
| **gdown** | CLI tool for downloading files from Google Drive share links. `!pip install gdown && !gdown https://drive.google.com/uc?id=FILE_ID`. Pre-installed on Colab. |
| **/content/** | Colab's working directory. Ephemeral — wiped on disconnect, runtime restart, or session end. Never save important outputs here without Drive backup. |
| **/content/drive/MyDrive/** | Mount point for Google Drive. Persistent storage that survives session changes. All important outputs should be saved here. |

## General ML Preflight Terms

| Term | Definition | Origin |
|------|-----------|--------|
| **Sovereign Script** | A standalone `.py` file that contains all execution logic. The notebook only writes it via `%%writefile` and executes it with `!python`. Prevents string escaping collisions. | S9 |
| **Deterministic Mandate** | All model inference uses `temperature=0.0` and `do_sample=False` for reproducible outputs. | S1 |
| **Cleanse Pattern** | Pip uninstall-then-reinstall sequence resolving corrupted metadata in Python 3.12+. Critical on Colab which runs 3.12. | S2.A |
| **Provenance Metadata** | 10-field record captured at execution time: git_commit, model_repo, model_revision, evaluator_file, input_file, gpu_type, gpu_vram_gb, package_versions, generation_config. | S4.4 |
| **Evaluation Heartbeat** | Explicit `print(..., flush=True)` every N items during long-running loops. Essential on Colab which has no external monitoring API. | S4.5 |
| **Extraction Drift** | Model leaks training-stage fields into responses due to prompt template mismatch. | S1.3 |
| **Zero Circle** | Notebook runs showing no output. On Colab, typically caused by missing imports, Drive mount failures, or silent crashes. | S6 |
| **Five-Failure Gauntlet** | 5 consecutive failures from 5 distinct environment mismatches — all preventable with preflight checks. | S16 |
| **Cell Separation Mandate** | `pip install` and `import` in different cells. On Colab, accept "Restart Runtime" prompt between them. | S12 |
| **Boundary Validation** | Validate artifacts at system boundary crossings, not at the destination. | S16.2 |
| **Graceful Degradation** | Disable advanced GPU features when capability is below minimum. On Colab: T4 lacks BFloat16, use float16 instead. | S11.2 |
| **Full Armor Injection** | Copy ALL logic to cloud notebooks, never partial. Partial copying creates security gaps. | S10.1 |
| **Environment Parity** | Dev and execution environments aligned. Colab runs Python 3.12 + PyTorch 2.8 + CUDA 12.6. | PIR-003 |
