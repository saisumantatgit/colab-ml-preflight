---
name: handbook
trigger: "On-demand reference — when you need Colab-specific rules, term definitions, or quick-reference lookup"
lifecycle_stage: any
description: "Quick-reference cheatsheet, glossary, and deep links to Colab governance rules and case studies"
platform: colab
---

# Handbook Skill — Colab Reference Manual

Use this skill when you need the reasoning behind a rule, a term definition, or a quick-reference lookup.

## Quick-Reference Cheatsheet (Top 20 Colab Rules)

### Before Building
1. `temperature=0.0`, `do_sample=False` always (S1)
2. Sovereign script via `%%writefile`, never logic in JSON (S9)
3. Install cell and import cell MUST be separate (S12)
4. All `print()` must have `flush=True` (S4)
5. No `input()` calls — use Colab Secrets instead (S4)
6. Set seeds: torch, numpy, random in Cell 1 (S4)

### Colab-Specific Setup
7. Mount Google Drive EARLY for output persistence
8. Save all outputs to `/content/drive/MyDrive/`, NEVER `/content/` alone
9. Use Colab Secrets for HF tokens: `from google.colab import userdata`
10. Checkpoint to Drive every 500 steps for crash recovery

### Before Running
11. `ast.parse()` on all .py files (S9.3)
12. `json.load()` on all .json artifacts (S16.2)
13. GPU capability check — detect T4/L4/A100 tier (S11.1)
14. No bitsandbytes for <=7B inference on Python 3.12 (S16.1.1)
15. `.total_memory` not `.total_mem` (S16.1.2)
16. Use ungated mirrors when Colab Secrets lacks HF token (S16.1.3)

### While Running
17. In-notebook heartbeats every 10 items (no external polling API) (S4.5)
18. `!nvidia-smi` for GPU status checks
19. Monitor RAM with `psutil` — crash at >90% usage
20. Expect 5-10min silence on first run with JIT (S15)

## Colab Glossary

| Term | Definition |
|------|-----------|
| **Runtime Type** | The compute backend for a Colab notebook: None (CPU), T4 GPU, L4 GPU, A100 GPU, or TPU. Selected via Runtime > Change runtime type. |
| **Hardware Accelerator** | The GPU/TPU selection in Colab's runtime configuration. Determines available VRAM and compute capability. |
| **Colab Secrets** | Built-in secret storage (sidebar > key icon). Use `from google.colab import userdata; userdata.get('KEY')` to access. Secrets persist across sessions. |
| **Drive Mount** | `from google.colab import drive; drive.mount('/content/drive')`. Connects Google Drive to the Colab filesystem at `/content/drive/MyDrive/`. |
| **Compute Units (CU)** | Colab's billing unit. T4 uses ~1.76 CU/hr, A100 uses ~15 CU/hr. Pro/Pro+ include 100 CU/month; additional at $0.10/CU. |
| **Idle Timeout** | Free/Pro: ~90 minutes of no interaction disconnects the runtime. Pro+: no idle timeout while code is running. |
| **Session Timeout** | Maximum runtime duration. Free/Pro: 12 hours. Pro+: 24 hours. Non-negotiable. |
| **GPU Preemption** | On free tier, Google may reclaim your GPU mid-session for higher-priority users. Results in sudden disconnect with no warning. |
| **Runtime Restart** | After installing packages, Colab may prompt "Restart Runtime." This clears Python state but preserves files in /content/. Drive must be re-mounted. |
| **Sovereign Script** | Standalone `.py` file; notebook only writes and executes it via `%%writefile`. Prevents escaping hell. (S9) |
| **Deterministic Mandate** | All inference uses `temperature=0.0` and `do_sample=False`. (S1) |
| **Cleanse Pattern** | Pip uninstall-then-reinstall resolving corrupted metadata in Python 3.12+. (S2.A) |
| **Provenance Metadata** | 10-field record (git hash, GPU type, etc.) captured at execution time. (S4.4) |
| **Poll-Then-Fetch** | Not applicable on Colab (no external API) — use in-notebook heartbeats instead. |
| **Evaluation Heartbeat** | Explicit `print(..., flush=True)` every N items for visibility. (S4.5) |
| **Zero Circle** | Notebook runs showing no output. On Colab, check for missing imports or Drive mount failures. (S6) |
| **Cell Separation Mandate** | `pip install` and `import` in different cells. On Colab, accept "Restart Runtime" prompt between them. (S12) |
| **gdown** | CLI tool to download files from Google Drive share links. `!pip install gdown && !gdown URL`. |

## Case Study Index

| ID | Title | Colab Relevance | Key Lesson |
|----|-------|----------------|------------|
| CS-01 | Zero Circle Silent Failure | HIGH | Missing dependency = silent hang |
| CS-02 | Asynchronous Race Conditions | LOW | Colab has no external polling |
| CS-03 | Phantom Dataset References | MEDIUM | Drive path references can be phantoms |
| CS-04 | String Escaping Hell | HIGH | Use %%writefile in Colab |
| CS-05 | Incomplete Safety Logic | MEDIUM | Copy ALL logic, not partial |
| CS-06 | GPUTooOldForTriton | HIGH | T4 is safe (7.5), but check capability |
| CS-07 | Import-After-Install Trap | HIGH | Restart Runtime between install and import |
| CS-08 | Silent Training Hang | HIGH | JIT compilation causes silence |
| CS-09 | Five-Failure Gauntlet | HIGH | 5 failures, all preventable with preflight |
| CS-10 | Red Team Baseline | LOW | Colab uses /content/, not /kaggle/working/ |

## Colab Tier Comparison

| Feature | Free | Pro ($9.99/mo) | Pro+ ($49.99/mo) |
|---------|------|----------------|-------------------|
| GPU | T4 (15GB) | T4, L4 (24GB) | T4, L4, A100 (80GB) |
| Session Timeout | 12 hours | 12 hours | 24 hours |
| Idle Timeout | ~90 min | ~90 min | None (while running) |
| Compute Units | Dynamic | 100 CU/mo | 100 CU/mo |
| RAM | Standard | High-RAM option | High-RAM option |
| Priority | Low | Medium | Highest |

## Deep References

- GPU matrix: `references/gpu_matrix.md`
- Error taxonomy: `references/error_taxonomy.md`
- Triage tree: `references/triage_tree.md`
- Full cheatsheet: `references/cheatsheet.md`
- Full glossary: `references/glossary.md`
