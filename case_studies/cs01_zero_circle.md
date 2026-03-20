# CS-01: The Zero Circle Silent Failure

## Colab Relevance: HIGH
On Colab, silent failures are especially dangerous because there is no external monitoring API. If your notebook produces zero output, you may not notice until checking the browser tab minutes later.

## The Failure
An ML notebook ran for 60+ minutes showing no output. The runtime appeared active but produced nothing.

## Root Cause
1. **Missing dependency**: A critical library was imported without `pip install` in the setup cell
2. **Silent failure**: Python's import system silently failed — Colab showed no error, just silence
3. **No observability**: No `print(..., flush=True)` between stages meant zero visibility

## Colab-Specific Impact
- No external polling API means you cannot detect this from outside the notebook
- Free tier idle timeout (~90 min) may disconnect before you notice the hang
- Compute units are consumed silently while the notebook produces nothing

## The Fix
1. Add explicit `!pip install` for ALL imported modules in a dedicated install cell
2. Add `flush=True` to all print statements
3. Add heartbeats: `print(f"[HEARTBEAT] Starting stage {n}...", flush=True)` between every major phase
4. Run `python scripts/preflight_check.py notebook.ipynb` to catch missing dependencies

## Prevention
The check skill validates import-install alignment. The build skill mandates heartbeats between stages.

## Triage Signature
**Category:** LOGIC.HANG, ENV.CELL_CACHE
**Detection:** Zero output is the signature — no regex can catch it
