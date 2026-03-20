# colab-ml-preflight: Build Prompt

You are constructing an ML notebook for Google Colab. Follow these rules exactly.

## Mandatory Construction Rules

1. **Deterministic inference**: `temperature=0.0` and `do_sample=False` for all inference. Template parity with training.

2. **Environment hardening**: Cleanse pattern for Colab's Python 3.12. Dtype: float16 for T4, bfloat16 for L4/A100.

3. **Cell structure**:
   - Cell 1: Seeds (torch.manual_seed, np.random.seed, random.seed)
   - Cell 2: Package installation ONLY (no imports)
   - [Accept "Restart Runtime" if prompted]
   - Cell 3: Drive mount + imports + version verification
   - Remaining: Logic

4. **Sovereign script**: `%%writefile /content/script.py` + `!python /content/script.py`. Never logic in JSON.

5. **Logging**: All `print()` with `flush=True`. Heartbeats every 10 items.

6. **Forbidden**: No `input()`. No hardcoded local paths. No install+import in same cell.

7. **Drive persistence**: Mount Drive early. Save ALL outputs to `/content/drive/MyDrive/`, NEVER just `/content/`.

8. **Auth**: Use Colab Secrets for HF tokens: `from google.colab import userdata`

## References
- GPU matrix: `references/gpu_matrix.md`
- Cheatsheet: `references/cheatsheet.md`
