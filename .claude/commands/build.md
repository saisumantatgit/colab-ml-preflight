---
name: build
description: "Construct an ML notebook with Colab-safe, deterministic patterns"
skill: build
---

Invoke the **build** skill to construct a notebook following colab-ml-preflight governance rules.

This command enforces:
- Deterministic inference settings (S1)
- Environment hardening with cleanse pattern for Colab's Python 3.12 (S2)
- Google Drive mounting for output persistence
- Full construction checklist (S4)
- Sovereign script pattern — never logic in JSON (S9)
- Cell separation mandate — install and import in separate cells (S12)
- Colab Secrets for authentication — never hardcode tokens

Usage: `/build` when creating any ML notebook for Google Colab.
