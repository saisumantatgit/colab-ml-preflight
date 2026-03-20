# CS-07: The Import-After-Install Trap

## Colab Relevance: HIGH
This is one of the most common Colab failures. Colab's "Restart Runtime" prompt after pip install adds a wrinkle not found on other platforms.

## The Failure
`ImportError: No module named 'transformers'` despite successful pip install in the same cell.

## Root Cause
Jupyter's `sys.modules` cache is populated at cell start. Packages installed mid-cell via pip are invisible until the next cell executes.

## Colab-Specific Behavior
1. After `!pip install transformers`, Colab may show: "Restart runtime to use newly installed packages"
2. If you restart: Python state is cleared, files in /content/ persist, Drive must be re-mounted
3. If you don't restart: some packages work, others fail silently

## The Fix
```python
# Cell 1: Install ONLY
!pip install -q transformers peft accelerate

# [Accept "Restart Runtime" if prompted]

# Cell 2: Re-mount Drive (if using)
from google.colab import drive
drive.mount('/content/drive')

# Cell 3: Import and verify
import transformers
print(f"transformers={transformers.__version__}", flush=True)
```

## Prevention
The check skill detects `pip install` and `import` in the same cell (BLOCKER).

## Triage Signature
**Category:** ENV.CELL_CACHE
**Detection regex:** `ImportError.*install|ModuleNotFoundError`
