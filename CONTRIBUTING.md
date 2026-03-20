# Contributing to colab-ml-preflight

## How to Add a Colab-Specific Fix

1. Open `templates/known_fixes.yaml`
2. Add a new entry with: id, pattern (regex), category, cause, fix, confidence
3. For Colab-specific fixes, use the `COLAB.*` category prefix
4. The `scripts/triage.py` script picks up new entries automatically

## How to Add a Case Study

1. Create `case_studies/csNN_descriptive_name.md`
2. Include: Colab Relevance rating (HIGH/MEDIUM/LOW), The Failure, Root Cause, Colab-Specific Impact, The Fix, Prevention
3. Add the triage signature to `templates/known_fixes.yaml`
4. Update `references/error_taxonomy.md` if introducing a new subcategory

## How to Add an Error Pattern

1. Add the regex pattern to `scripts/triage.py` in the `ERROR_PATTERNS` list
2. For Colab-specific errors, put them in the COLAB section (checked first)
3. Add the corresponding entry to `templates/known_fixes.yaml`
4. Update `references/error_taxonomy.md` and `references/triage_tree.md`

## How to Update the Colab Snapshot

1. Run a fresh Colab notebook to check versions:
   ```python
   !python --version
   !pip show torch
   !nvcc --version
   ```
2. Update `platforms/colab.json` with new versions
3. Update `CLAUDE.md` Colab Environment section

## How to Add a CLI Adapter

1. Create a directory under `adapters/`
2. Follow existing patterns (Codex: AGENTS.md, Cursor: rules file, Aider: config)
3. Update `install.sh` with a new case

## Code Style

- Python scripts: Standard library only (no ML framework deps)
- Markdown: ATX headers, pipe tables, fenced code blocks
- YAML: 2-space indentation
- All governance rules must have an S-number reference
- All examples must use Colab paths (/content/, /content/drive/MyDrive/)

## Testing

```bash
# Syntax check all Python scripts
python -m py_compile scripts/preflight_check.py
python -m py_compile scripts/env_parity.py
python -m py_compile scripts/poll_monitor.py
python -m py_compile scripts/triage.py

# Run preflight on a test notebook
python scripts/preflight_check.py test_notebook.ipynb

# Validate platform snapshot
python -c "import json; json.load(open('platforms/colab.json'))"
```
