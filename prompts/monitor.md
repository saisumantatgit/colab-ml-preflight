# colab-ml-preflight: Monitor Prompt

You are monitoring a notebook running on Google Colab. There is no external polling API.

## Rules
1. Use IN-NOTEBOOK heartbeats: `print(f"[HEARTBEAT] {step}/{total}", flush=True)`
2. Check GPU with `!nvidia-smi` or torch.cuda memory functions
3. Monitor RAM with psutil — crash risk above 90%
4. Checkpoint to Drive every 500 steps for crash recovery

## Interpreting Silence
- 0-5 min: Normal (JIT compilation). Wait.
- 5-10 min: Possible model download. Check Drive/network.
- 10+ min: Suspicious. Run `!nvidia-smi` in a new cell.
- 30+ min: Likely hang. Interrupt and investigate.

## On Completion
- Verify output files on Drive (NOT just in /content/)
- Download key artifacts locally as backup

## On Crash/Disconnect
- Reconnect, re-mount Drive, check checkpoints, resume
