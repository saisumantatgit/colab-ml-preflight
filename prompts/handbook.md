# colab-ml-preflight: Handbook (Reference) Prompt

Look up Colab governance rules, tier details, or term definitions.

## Resources
- **Cheatsheet**: Top 20 Colab rules — `references/cheatsheet.md`
- **Glossary**: Colab-specific terms — `references/glossary.md`
- **GPU Matrix**: T4/L4/A100 by tier — `references/gpu_matrix.md`
- **Error Taxonomy**: 7 categories (incl. COLAB-specific) — `references/error_taxonomy.md`
- **Triage Tree**: Colab decision tree — `references/triage_tree.md`
- **Case Studies**: 10 adapted for Colab — `case_studies/`
- **Known Fixes**: Error-to-fix mapping — `templates/known_fixes.yaml`

## Colab Tiers
| Feature | Free | Pro ($9.99) | Pro+ ($49.99) |
|---------|------|-------------|---------------|
| GPU | T4 (15GB) | T4, L4 (24GB) | T4, L4, A100 (80GB) |
| Timeout | 12hr | 12hr | 24hr |
| Idle | ~90min | ~90min | None (running) |
| CU | Dynamic | 100/mo | 100/mo |

## Section Index
S1: Deterministic. S2: Env Hardening. S4: Checklist. S9: Sovereign Script. S11: GPU. S12: Cell Separation. S16: Five-Failure Gauntlet.
