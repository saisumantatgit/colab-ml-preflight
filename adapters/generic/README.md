# colab-ml-preflight: Generic LLM Integration

This guide explains how to use colab-ml-preflight with any LLM coding tool.

## Architecture

1. **Prompts** (`prompts/`): Pure markdown, Colab-specific, works with any LLM
2. **Scripts** (`scripts/`): Plain Python, no --platform flag needed (always Colab)
3. **References** (`references/`, `case_studies/`): Colab-focused knowledge base

## Integration Steps

1. **Copy the prompt** for your lifecycle stage from `prompts/`
2. **Paste as system context** in your LLM tool
3. **Run scripts** for automated validation:
   ```bash
   python scripts/preflight_check.py notebook.ipynb --strict
   python scripts/env_parity.py notebook.ipynb
   ```
4. **Reference docs** are in `references/`

## For CI/CD
```bash
python scripts/preflight_check.py $NOTEBOOK --strict
if [ $? -ne 0 ]; then
    echo "Colab preflight failed. Fix blockers."
    exit 1
fi
```
