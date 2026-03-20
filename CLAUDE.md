# colab-ml-preflight — Internal Architecture

## What This Is

colab-ml-preflight is a Google Colab-native derivative of ml-preflight. It converts 10 real-world failure case studies and 20 Colab-specific governance rules into 6 executable skills that fire at the right moment in the ML notebook lifecycle.

This is NOT a generic multi-platform tool with Colab bolted on. Every default, every example, every script is pre-configured for Google Colab. There is no --platform flag — it is always Colab.

## Key Differences from Universal ml-preflight

1. **Platform is always Colab** — no --platform flag on any script
2. **Colab-specific error taxonomy** — adds COLAB category (disconnect, RAM crash, preemption, idle, Drive)
3. **No external polling API** — monitor skill uses in-notebook heartbeats, not poll-then-fetch
4. **Drive persistence is mandatory** — build skill enforces Drive mount and Drive output paths
5. **Colab Secrets for auth** — not Kaggle Secrets or AWS IAM
6. **Tier-aware checks** — GPU detection identifies Free (T4), Pro (L4), Pro+ (A100)
7. **Runtime restart awareness** — cell separation accounts for Colab's "Restart Runtime" prompt

## Lifecycle

```
build --> check --> launch --> monitor --> (crash?) --> blackbox
  1         2         3          4                        5

                   + handbook (reference, on-demand)
                         6
```

## 6 Skills

| Skill | Trigger | Colab-Specific Focus |
|-------|---------|---------------------|
| **build** | Constructing a notebook | Drive mount, Colab Secrets, tier-aware dtype |
| **check** | Before running | T4/L4/A100 detection, Drive persistence, env parity |
| **launch** | Deploying to Colab | Drive upload, GitHub integration, runtime selection |
| **monitor** | During execution | In-notebook heartbeats, !nvidia-smi, RAM tracking |
| **blackbox** | After failure | Disconnect/crash/preemption triage + recovery |
| **handbook** | On-demand | Tier comparison, Colab glossary, GPU matrix |

## 4 Scripts

| Script | Purpose | CLI |
|--------|---------|-----|
| `preflight_check.py` | Validate for Colab | `python scripts/preflight_check.py nb.ipynb` |
| `env_parity.py` | Compare vs Colab env | `python scripts/env_parity.py nb.ipynb` |
| `poll_monitor.py` | In-notebook health check | `python scripts/poll_monitor.py --check-health` |
| `triage.py` | Classify Colab errors | `python scripts/triage.py --error-log output.log` |

## Colab Environment (March 2026)

- Python 3.12
- PyTorch 2.8.0+cu126
- CUDA 12.6
- GPUs: T4 (free), L4 (pro), A100 (pro+)
- Working directory: /content/
- Persistent storage: /content/drive/MyDrive/ (Drive mount required)

## Key Design Decisions

1. Skills are self-contained — load ONE at the trigger point
2. Scripts have no --platform flag — always Colab
3. Only colab.json in platforms/ — no multi-platform complexity
4. Error taxonomy includes COLAB-specific category (7 categories total)
5. Monitor skill uses in-notebook patterns, not external API polling
6. Every case study rated for Colab relevance (HIGH/MEDIUM/LOW)
7. All examples use Colab paths (/content/, /content/drive/MyDrive/)
