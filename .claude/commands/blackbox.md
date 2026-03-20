---
name: blackbox
description: "Triage a failed Colab notebook — disconnects, crashes, RAM exhaustion, and errors"
skill: blackbox
---

Invoke the **blackbox** skill to diagnose a Colab notebook failure.

This command provides:
- Colab-specific failure classification (disconnect, RAM crash, GPU preemption, idle timeout)
- Structured triage decision tree for Colab errors
- Standard error classification into 6 categories + Colab-specific category
- Known-fix lookup from 10 case studies
- Recovery checklist (reconnect, re-mount Drive, resume from checkpoint)

Usage: `/blackbox` after a Colab notebook fails, crashes, or disconnects.

Script: `scripts/triage.py`
