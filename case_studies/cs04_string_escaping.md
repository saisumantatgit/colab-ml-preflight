# CS-04: String Escaping Hell / The Sovereign Script Solution

## Colab Relevance: HIGH
Colab notebooks are JSON files (.ipynb). Constructing complex Python code inside notebook cells programmatically leads to escaping collisions.

## The Failure
Programmatically generated Colab notebook cells contained Python syntax errors from f-string/JSON escaping collisions.

## Root Cause
1. **Escaping collision**: Python f-strings collided with JSON string escaping and notebook cell parsing
2. **Invisible until runtime**: Generated notebook appeared fine but contained invalid Python

## The Fix
Use the `%%writefile` pattern in Colab:
```python
# Cell 1: Write the script
%%writefile /content/script.py
import torch
# ... all your logic here ...

# Cell 2: Run it
!python /content/script.py
```

## Prevention
The build skill enforces the sovereign script pattern. The check skill validates syntax with `ast.parse()`.

## Triage Signature
**Category:** LOGIC.ESCAPING
**Detection regex:** `SyntaxError.*f-string|SyntaxError.*unterminated`
