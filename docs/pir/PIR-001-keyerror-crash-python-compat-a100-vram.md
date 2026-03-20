# PIR-001: KeyError Crash, Python 3.10+ Syntax, and A100 VRAM Misreporting

## Metadata

| Field | Value |
|-------|-------|
| **PIR ID** | PIR-001 |
| **Date** | 2026-03-20 |
| **Severity** | P2 |
| **Status** | Final |
| **Incident date** | 2026-03-20 |
| **Detection date** | 2026-03-20 |
| **Resolution date** | 2026-03-20 |

## Zone Check

| Dimension | Status | Notes |
|-----------|--------|-------|
| **Severity** | P2 | KeyError crashes preflight; VRAM misinfo causes OOM |
| **Containment** | Contained | All three issues remediated |
| **Blast Radius** | preflight_check.py, colab.json, all downstream callers | |

## 1. Summary

Three defects discovered in colab-ml-preflight: (1) `run_preflight()` error-path dicts missing the `"passed"` key, causing a KeyError crash in `main()` and `print_report()`; (2) `list[dict]` and `int | None` type hints requiring Python 3.10+ but Colab runs 3.12 (acceptable now, but the codebase was forked from a Python 3.8-compat source); (3) A100 VRAM documented as 80GB when Colab Pro+ typically allocates the 40GB variant, risking OOM failures from overestimated memory budgets. Two additional minor issues: a duplicate `or` in the `has_secrets` check and an empty `known_conflicts` array in `colab.json`. All five issues resolved same day.

## 2. Timeline

| Time | Event | Actor |
|------|-------|-------|
| 2026-03-20 | Code forked from kaggle-ml-preflight with Colab adaptations | Developer |
| 2026-03-20 | KeyError crash, Python compat issues, VRAM discrepancy detected during code review | Code review |
| 2026-03-20 | All five issues remediated | Developer |

## 3. Five Whys

### Issue 1: KeyError crash

1. **Why?** -- `main()` accesses `results["passed"]` but early-return error dicts omitted the key.
2. **Why?** -- Error-path dicts were constructed ad-hoc, not validated against the success-path schema.
3. **Why?** -- No shared return schema or data model enforces field completeness.
4. **Why?** -- The codebase uses raw dicts instead of a typed dataclass for results.
5. **Why?** -> **ROOT CAUSE:** No return-type contract between `run_preflight()` and its callers. Dict keys were hand-maintained across two code paths with no shared schema.

### Issue 2: Python 3.10+ syntax

1. **Why?** -- `list[dict]` and `int | None` syntax used in type hints.
2. **Why?** -- Code was written targeting Python 3.10+ built-in generics.
3. **Why?** -- `from __future__ import annotations` is present (defers evaluation), making this safe at runtime on 3.7+, but linters and some toolchains flag it.
4. **Why?** -- Inherited from kaggle variant without verifying cross-version intent.
5. **Why?** -> **ROOT CAUSE:** Fork-and-adapt workflow inherited syntax assumptions without explicit Python version targeting. The `__future__` import mitigates runtime risk but the intent was not documented.

### Issue 3: A100 VRAM 80GB vs 40GB

1. **Why?** -- Documentation and colab.json listed A100 as 80GB.
2. **Why?** -- A100 exists in both 40GB (A100-SXM4-40GB) and 80GB (A100-SXM4-80GB) variants.
3. **Why?** -- The 80GB spec-sheet value was used as the canonical figure.
4. **Why?** -- No verification against the actual Colab Pro+ allocation was performed.
5. **Why?** -> **ROOT CAUSE:** Spec-sheet values used instead of verified platform-specific allocations. Colab Pro+ typically provisions the 40GB variant; 80GB is occasionally available but not guaranteed.

## 4. Blast Radius

| Radius | Affected | How |
|--------|----------|-----|
| Direct | `preflight_check.py` | KeyError crash on invalid file input; misleading VRAM guidance |
| Adjacent | `colab.json` | Incorrect A100 VRAM; empty known_conflicts |
| Downstream | Any notebook user relying on VRAM figures for batch-size calculation | OOM from assuming 80GB when only 40GB is available |
| Potential (if undetected) | Users with .txt or other unsupported files | Silent crash instead of clean error message |

## 5. Prompt Forensics

### Triggering input
```
python preflight_check.py notes.txt
```

### Expected vs actual
- Expected: Clean error message "Unsupported file type" with `passed: False` and exit code 1.
- Actual: `KeyError: 'passed'` traceback crash because the error-return dict was missing the `"passed"` key.

## 6. What Went Well

- Code review caught all five issues before any user encountered them in production.
- The kaggle-ml-preflight variant had the same KeyError bug, so the pattern was already known -- detection was immediate.
- `from __future__ import annotations` was already present, preventing the Python compat issue from being a runtime crash.

## 7. What Went Wrong

- Error-path return dicts were constructed independently of the success path, with no shared schema enforcing field completeness.
- A100 VRAM was taken from NVIDIA spec sheets without verifying the specific SKU Colab provisions.
- `known_conflicts` was left empty in `colab.json` despite the `BNB_CONFLICT` check already existing in code.
- A duplicate `or` in `has_secrets` logic (cosmetic but indicates insufficient review of forked code).

## 8. Where We Got Lucky

- The `"passed"` key was accessed in `main()` which runs on every invocation -- this would have been caught on first use with an unsupported file type. But if the first user only ever passed `.ipynb` files, the bug could have persisted undetected for weeks.
- No user had yet made batch-size decisions based on the 80GB VRAM figure. A 2x overestimate of GPU memory would cause immediate OOM on large model loads.

## 9. Remediation

### Immediate fix
- Added `"passed": False` to both early-return error dicts in `run_preflight()`.
- Standardized A100 VRAM to 40GB in `colab.json` with `"note": "80GB occasionally available"`.
- Removed duplicate `or` in `has_secrets` check.
- Populated `known_conflicts` in `colab.json` with the bitsandbytes/Python 3.12 conflict.

### Permanent fix
- Consider replacing raw dicts with a `@dataclass` or Pydantic model for `run_preflight()` return values to make missing fields a compile-time error.
- Add a platform verification step that checks actual GPU VRAM at runtime via `torch.cuda.get_device_properties()` rather than relying on static config values.

### Detection improvement
- Add a unit test that calls `run_preflight()` with an unsupported file type and asserts `"passed" in result`.
- Add a schema validation test for `colab.json` that verifies all `gpu_options` entries have `vram_gb` values matching known Colab allocations.

## 10. Action Items

| # | Action | Priority | Owner | Due | Status |
|---|--------|----------|-------|-----|--------|
| 1 | Add `"passed"` key to all error-return dicts | P2 | Developer | 2026-03-20 | Done |
| 2 | Standardize A100 VRAM to 40GB in colab.json | P2 | Developer | 2026-03-20 | Done |
| 3 | Remove duplicate `or` in has_secrets check | P3 | Developer | 2026-03-20 | Done |
| 4 | Populate known_conflicts in colab.json | P3 | Developer | 2026-03-20 | Done |
| 5 | Add unit test for error-path return schema | P2 | Developer | 2026-03-27 | Open |
| 6 | Evaluate dataclass/Pydantic for run_preflight return type | P3 | Developer | 2026-04-03 | Open |
| 7 | Add runtime VRAM verification via torch.cuda.get_device_properties() | P3 | Developer | 2026-04-03 | Open |

## 11. Lessons Learned

1. **Every return path needs the same schema.** When a function returns a dict consumed by multiple callers, every code path (success and error) must include every key those callers access. A dataclass or typed model eliminates this class of bug entirely.
2. **Platform specs are not deployment specs.** Hardware exists in multiple SKUs; the spec-sheet maximum is not what a cloud platform provisions. Always verify against the actual allocation, not the product family's maximum.
3. **Fork-and-adapt requires a full diff review.** When forking code across platform variants (kaggle -> colab), every assumption -- return schemas, hardware specs, syntax compatibility -- must be re-verified against the target platform. Bugs in the source propagate silently.
