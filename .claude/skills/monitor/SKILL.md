---
name: monitor
trigger: "After starting a Colab notebook — while it is executing"
lifecycle_stage: monitor
description: "In-notebook monitoring with heartbeat patterns, nvidia-smi checks, and session persistence strategies"
platform: colab
---

# Monitor Skill — Colab Execution Monitoring

Colab has LIMITED monitoring API — there is no `colab kernels status` equivalent. Monitoring must happen IN the notebook or via browser observation.

## 1. In-Notebook Heartbeat Pattern (S4.5)

Since Colab has no external polling API, embed heartbeats directly:

```python
import time

def heartbeat_callback(step, total, metrics=None):
    """Emit heartbeat for visibility during long-running Colab sessions."""
    timestamp = time.strftime('%H:%M:%S')
    msg = f"[HEARTBEAT] [{timestamp}] {step}/{total}"
    if metrics:
        msg += f" | {' '.join(f'{k}={v:.4f}' for k, v in metrics.items())}"
    print(msg, flush=True)

# Usage in training loop:
for step in range(total_steps):
    # ... training code ...
    if step % 10 == 0:
        heartbeat_callback(step, total_steps, {'loss': loss.item()})
```

## 2. GPU Monitoring via nvidia-smi

Colab supports `!nvidia-smi` for real-time GPU status:

```python
# Quick check
!nvidia-smi

# Detailed memory monitoring cell (run in a separate cell periodically)
import torch
if torch.cuda.is_available():
    allocated = torch.cuda.memory_allocated(0) / 1e9
    reserved = torch.cuda.memory_reserved(0) / 1e9
    total = torch.cuda.get_device_properties(0).total_memory / 1e9
    util = allocated / total * 100
    print(f"[GPU] allocated={allocated:.1f}GB reserved={reserved:.1f}GB "
          f"total={total:.1f}GB utilization={util:.0f}%", flush=True)
    if util > 85:
        print("WARNING: GPU utilization > 85% — OOM risk", flush=True)
```

### Continuous GPU Monitoring (Background Thread)

```python
import threading
import time
import torch

def gpu_monitor(interval=300, stop_event=None):
    """Background GPU monitor — logs every `interval` seconds."""
    while not (stop_event and stop_event.is_set()):
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1e9
            total = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"[GPU-MONITOR] {allocated:.1f}/{total:.1f}GB "
                  f"({allocated/total*100:.0f}%)", flush=True)
        time.sleep(interval)

# Start monitor
stop_monitor = threading.Event()
monitor_thread = threading.Thread(target=gpu_monitor, args=(300, stop_monitor), daemon=True)
monitor_thread.start()

# Stop when done
# stop_monitor.set()
```

## 3. Silent Hang Detection (S15)

### Expected Silence Windows on Colab

| Phase | Expected Silence | Action |
|-------|-----------------|--------|
| JIT compilation (first step) | 2-10 minutes | Wait — this is normal |
| Model download (first run) | 1-15 minutes | Wait — downloading weights |
| Drive mount | 5-30 seconds | Wait |
| No output after 10+ minutes | N/A | Flag as potential hang |
| No output after 30+ minutes | N/A | Likely genuine hang |

### Hang vs JIT Compilation
```
No output for 0-5 min after RUNNING   -> Likely JIT compilation. Wait.
No output for 5-10 min               -> Possible model download. Check Drive/network.
No output for 10+ min                -> Suspicious. Check with !nvidia-smi
No output for 30+ min                -> Likely hang. Interrupt and check:
                                        - Missing dependency (CS-01)
                                        - Silent import failure
                                        - Infinite loop
                                        - Session disconnect (check browser tab)
```

## 4. Colab Session Persistence Strategies

### Check Session Health
```python
import psutil
import time

def check_session_health():
    """Quick session health check for Colab."""
    ram = psutil.virtual_memory()
    print(f"RAM: {ram.used/1e9:.1f}/{ram.total/1e9:.1f}GB ({ram.percent}%)", flush=True)
    if ram.percent > 90:
        print("CRITICAL: RAM > 90% — session may crash!", flush=True)
    return ram.percent < 90
```

### Checkpoint-and-Resume Pattern
```python
import os
import json

CHECKPOINT_DIR = '/content/drive/MyDrive/checkpoints/my-run/'
PROGRESS_FILE = os.path.join(CHECKPOINT_DIR, 'progress.json')

def save_progress(step, metrics):
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'step': step, 'metrics': metrics}, f)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {'step': 0, 'metrics': {}}

# Resume from last checkpoint after disconnect
progress = load_progress()
start_step = progress['step']
print(f"Resuming from step {start_step}", flush=True)
```

## 5. Colab-Specific Crash Detection

### RAM Crash Warning
Colab displays "Your session crashed due to high RAM usage" when memory is exhausted. Pre-empt this:

```python
import psutil

def check_ram_before_operation(operation_name, min_free_gb=2.0):
    """Check RAM before memory-intensive operations."""
    ram = psutil.virtual_memory()
    free_gb = ram.available / 1e9
    if free_gb < min_free_gb:
        print(f"WARNING: Only {free_gb:.1f}GB RAM free before {operation_name}. "
              f"Risk of session crash!", flush=True)
        return False
    return True

# Usage:
if check_ram_before_operation("model loading"):
    model = AutoModelForCausalLM.from_pretrained(...)
```

## 6. Timeout Calibration for Colab

| Tier | Max Session | Idle Timeout | CU Consumption |
|------|------------|--------------|----------------|
| Free | 12 hours | ~90 min idle | Dynamic |
| Pro | 12 hours | ~90 min idle | T4: ~1.76 CU/hr |
| Pro+ | 24 hours | None (while running) | A100: ~15 CU/hr |

## 7. On Completion

When training/evaluation completes:
1. Verify output files exist on Drive (NOT just in /content/)
2. Check that files are non-empty
3. Download key artifacts locally as backup
4. Log final metrics with provenance metadata

When session crashes or disconnects:
1. Reconnect (if possible)
2. Check Drive for checkpoints
3. If no checkpoint: hand off to blackbox skill for triage
4. Resume from last checkpoint using load_progress()

## References

- Case studies: CS-01 (Zero Circle), CS-02 (Race Conditions), CS-08 (Training Hang)
