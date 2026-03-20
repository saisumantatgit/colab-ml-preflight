---
name: launch
description: "Deploy a notebook to Google Colab via Drive, GitHub, or upload"
skill: launch
---

Invoke the **launch** skill to deploy a notebook to Google Colab.

This command covers:
- Google Drive mounting and data access verification
- Colab Secrets verification for gated models
- Runtime selection guide (T4/L4/A100 by model size)
- Dry-run validation cell injection (S16.3)
- Session persistence strategies for surviving disconnects

Usage: `/launch` when ready to deploy and run a validated notebook on Colab.
