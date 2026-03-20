---
name: monitor
description: "Monitor a running Colab notebook with in-notebook heartbeats and GPU checks"
skill: monitor
---

Invoke the **monitor** skill to track a notebook running on Google Colab.

This command provides:
- In-notebook heartbeat patterns (no external polling API on Colab)
- `!nvidia-smi` GPU monitoring
- Background GPU memory monitoring via threading
- RAM crash detection and prevention
- Session persistence with checkpoint-and-resume pattern
- Idle timeout awareness and keep-alive strategies

Usage: `/monitor` while a notebook is running on Colab.
