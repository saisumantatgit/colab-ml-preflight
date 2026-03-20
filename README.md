# colab-ml-preflight

**Stop losing training runs to Colab disconnects and silent failures.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Platform: Google Colab](https://img.shields.io/badge/platform-Google%20Colab-orange.svg)](https://colab.research.google.com/)

---

## The Problem

Runtime disconnected. 3 hours of training, gone. Your outputs? Gone. Your Drive mount? "File not found."

You restart the notebook. You wait for the GPU. "Your session crashed due to high RAM usage." Try again. Different error — `ModuleNotFoundError` because Colab restarted the runtime and your imports need to run again. Third attempt: 40 minutes in, "Your session is no longer connected." The free tier preempted your GPU.

This is not a skill issue. **This is Colab's reality.**

- Free tier GPUs get preempted without warning
- `/content/` is wiped on every disconnect — if you didn't save to Drive, it's gone
- "Restart Runtime" after pip install breaks your Python state silently
- ~90 minutes of idle disconnects your session even if you're just reading logs
- AI-generated code has **1.7x more bugs** than human-written code ([CodeRabbit 2025](https://www.coderabbit.ai/))

colab-ml-preflight closes this gap. It converts 10 real-world failure case studies and 20 Colab-specific governance rules into automated checks that fire before you run, not after you crash.

---

## Without vs With colab-ml-preflight

| Without | With |
|---------|------|
| Run and pray on Colab free tier | Preflight checks catch errors in seconds |
| Lose 3 hours of training on disconnect | Checkpoint-to-Drive pattern saves progress |
| Debug "session crashed" with no context | Structured triage identifies RAM crash vs preemption vs OOM |
| Outputs saved to /content/ = lost on disconnect | Drive persistence enforced by default |
| Same mistakes repeated across sessions | 10 case studies converted to automated checks |
| Hope the notebook doesn't hang silently | In-notebook heartbeats with GPU/RAM monitoring |

---

## The 6 Lifecycle Stages

```
  build ──> check ──> launch ──> monitor ──> (success)
    |          |         |          |
    |          |         |          +──> (crash?) ──> blackbox
    |          |         |
    +──────────+─────────+──────────────> handbook (on-demand)
```

| Stage | What it does | When it fires |
|-------|-------------|---------------|
| **build** | Enforces Colab-safe notebook construction | Creating a notebook |
| **check** | Pre-run validation gate | Before executing on Colab |
| **launch** | Safe deployment via Drive, GitHub, or upload | Setting up the Colab session |
| **monitor** | In-notebook heartbeats + GPU/RAM monitoring | During execution |
| **blackbox** | Colab-specific triage (disconnect, crash, preemption) | After a failure |
| **handbook** | Colab quick-reference + tier comparison | On-demand |

---

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/build` | Construct notebook with Drive persistence + Colab Secrets | `/build` for a fine-tuning notebook |
| `/check` | Preflight validation (T4/L4/A100 detection, Drive mount, env parity) | `/check` before running |
| `/launch` | Deploy via Drive mount, runtime selection, data verification | `/launch` to set up Colab session |
| `/monitor` | In-notebook heartbeats, `!nvidia-smi`, RAM tracking | `/monitor` during training |
| `/blackbox` | Triage disconnects, RAM crashes, GPU preemption | `/blackbox` when Colab crashes |
| `/handbook` | Colab tier comparison, GPU matrix, glossary | `/handbook` for reference |

## Scripts (No --platform Flag Needed)

| Script | Purpose | CLI |
|--------|---------|-----|
| `preflight_check.py` | Validate notebook for Colab | `python scripts/preflight_check.py nb.ipynb [--strict]` |
| `env_parity.py` | Check notebook vs Colab environment | `python scripts/env_parity.py nb.ipynb` |
| `poll_monitor.py` | In-notebook health monitor | `python scripts/poll_monitor.py --check-health` |
| `triage.py` | Classify Colab errors + known fixes | `python scripts/triage.py --error-log output.log` |

---

## Quick Start

### Install

```bash
# Clone
git clone https://github.com/saisumantatgit/colab-ml-preflight.git

# Install into your ML project
cd your-ml-project
bash /path/to/colab-ml-preflight/install.sh
```

### Validate a Notebook

```bash
# Preflight check (always targets Colab — no --platform flag)
python scripts/preflight_check.py my_training_notebook.ipynb

# Environment parity check against Colab
python scripts/env_parity.py my_training_notebook.ipynb

# Strict mode (warnings = blockers)
python scripts/preflight_check.py my_training_notebook.ipynb --strict
```

### Colab Notebook Template

```python
# Cell 1: Seeds
import random
import numpy as np
random.seed(42)
np.random.seed(42)

# Cell 2: Install (ONLY installs, no imports)
!pip install -q "transformers>=4.46.0" peft accelerate

# [Accept "Restart Runtime" if prompted]

# Cell 3: Mount Drive + Imports
from google.colab import drive
drive.mount('/content/drive')

import torch
torch.manual_seed(42)
import transformers
print(f"torch={torch.__version__}, transformers={transformers.__version__}", flush=True)

# Cell 4: GPU Check
if torch.cuda.is_available():
    name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"GPU: {name}, VRAM: {vram:.1f}GB", flush=True)
else:
    print("NO GPU — change runtime type!", flush=True)

# Cell 5+: Your code (save outputs to Drive)
import os
OUTPUT_DIR = '/content/drive/MyDrive/ml-outputs/my-experiment/'
os.makedirs(OUTPUT_DIR, exist_ok=True)
```

---

## Colab Tier Comparison

| Feature | Free | Pro ($9.99/mo) | Pro+ ($49.99/mo) |
|---------|------|----------------|-------------------|
| **GPU** | T4 (15GB) | T4, L4 (24GB) | T4, L4, A100 (80GB) |
| **Max Session** | 12 hours | 12 hours | 24 hours |
| **Idle Timeout** | ~90 min | ~90 min | None (while running) |
| **Compute Units** | Dynamic | 100 CU/mo | 100 CU/mo |
| **RAM** | Standard | High-RAM option | High-RAM option |
| **GPU Priority** | Low (preemption risk) | Medium | Highest (guaranteed) |

### How Preflight Adapts by Tier

| Check | Free Tier | Pro | Pro+ |
|-------|-----------|-----|------|
| GPU capability | T4 (7.5) — no BF16 | L4 (8.9) — full support | A100 (8.0) — full support |
| Dtype recommendation | float16 only | float16 or bfloat16 | bfloat16 recommended |
| Checkpoint frequency | Every 250 steps (preemption risk) | Every 500 steps | Every 1000 steps |
| Timeout warning | 11.5 hours | 11.5 hours | 23.5 hours |
| Idle prevention | Critical | Important | Not needed |

---

## Colab-Specific Error Patterns

| Error | What Happened | Fix |
|-------|--------------|-----|
| "Session crashed due to high RAM" | Model too large for available RAM | Reduce batch, quantize, upgrade tier |
| "Your session is no longer connected" | Idle timeout, preemption, or session limit | Checkpoint to Drive, keep tab active |
| `CUDA out of memory` | Model exceeds T4's 15GB / L4's 24GB | Reduce batch, gradient checkpointing |
| `ModuleNotFoundError` after restart | Runtime restart cleared Python state | Re-run import cells (not install cells) |
| Files missing from /content/ | Disconnect wiped ephemeral storage | Always save to Drive, never just /content/ |

---

## Cross-LLM Compatibility

| Tool | Adapter | Installation |
|------|---------|-------------|
| **Claude Code** | Skills + commands + hooks | `install.sh` (auto-detected) |
| **Codex** | Single `AGENTS.md` | Copy `adapters/codex/AGENTS.md` |
| **Cursor** | Rules file | Copy `adapters/cursor/.cursor/rules/ml-preflight.md` |
| **Aider** | Config file | Copy `adapters/aider/.aider.conf.yml` |
| **Any other** | Prompts directory | Paste from `prompts/` into your tool |

---

## Project Structure

```
colab-ml-preflight/
├── .claude-plugin/          # Plugin manifest + hooks (Colab-specific)
├── .claude/skills/          # 6 Colab-native skill definitions
├── .claude/commands/        # 6 command triggers
├── scripts/                 # 4 Python scripts (no --platform flag needed)
├── references/              # GPU matrix (T4/L4/A100), Colab cheatsheet, taxonomy
├── case_studies/            # 10 case studies adapted for Colab context
├── platforms/               # colab.json only (single platform)
├── templates/               # Config template + known fixes (Colab-prominent)
├── prompts/                 # 6 LLM-agnostic Colab prompts
├── adapters/                # Claude Code, Codex, Cursor, Aider, Generic
├── install.sh               # Auto-detect installer
├── CLAUDE.md                # Internal architecture
├── CONTRIBUTING.md          # How to contribute
└── README.md                # This file
```

---

## Part of the ml-preflight Family

colab-ml-preflight is a **Colab-native derivative** of [ml-preflight](https://github.com/saisumantatgit/ml-preflight), the universal ML notebook preflight plugin.

| Version | Platform | Repository |
|---------|----------|------------|
| **ml-preflight** | Universal (Kaggle, Colab, SageMaker, HF Jobs) | [github.com/saisumantatgit/ml-preflight](https://github.com/saisumantatgit/ml-preflight) |
| **colab-ml-preflight** | Google Colab (this repo) | [github.com/saisumantatgit/colab-ml-preflight](https://github.com/saisumantatgit/colab-ml-preflight) |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add Colab-specific fixes, case studies, and error patterns.

---

## License

MIT License. Copyright (c) 2026 Sai Sumanth Battepati.

See [LICENSE](LICENSE) for full text.
