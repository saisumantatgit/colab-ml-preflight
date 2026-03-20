# CS-08: The Silent Training Hang Pattern

## Colab Relevance: HIGH
On Colab, a silent hang is indistinguishable from normal JIT compilation without external monitoring. You must rely on in-notebook heartbeats.

## The Failure
A training notebook showed no output for 500+ seconds. Was it hanging or compiling?

## Root Cause
1. **JIT compilation**: torch.compile compiles GPU kernels on first use — 2-10 minutes of silence
2. **Log buffering**: Colab buffers stdout; `logging_steps=10` output may not appear immediately
3. **No heartbeat**: No progress indicator during compilation phase

## Colab-Specific Impact
- No external polling API means you cannot check status from outside
- Free tier may disconnect for "idle" during legitimate JIT compilation silence
- Compute units consumed during silent compilation

## The Fix
1. Before `trainer.train()`:
   ```python
   print("Starting training (first step may take 2-10min for JIT)...", flush=True)
   ```
2. Set `logging_steps=5` for initial debugging
3. Use the background GPU monitor from poll_monitor.py to verify GPU is active:
   ```python
   !nvidia-smi  # Quick check — if GPU shows memory usage, it's working
   ```

## Prevention
The build skill mandates heartbeat logging before training starts (S15.1). The monitor skill provides in-notebook GPU monitoring.

## Triage Signature
**Category:** LOGIC.HANG
