#!/usr/bin/env python3
"""
colab-ml-preflight: Error Classification and Known-Fix Lookup

Classifies Colab notebook failures into a 7-category taxonomy (standard 6 + Colab-specific)
and looks up known fixes from case studies and post-incident reviews.

Usage:
    python triage.py --error-log <file> [--known-fixes known_fixes.yaml] [--json-output]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Error taxonomy (includes Colab-specific patterns)
# ---------------------------------------------------------------------------

ERROR_PATTERNS = [
    # COLAB — Colab-specific errors (checked first)
    {
        "pattern": r"session crashed.*high RAM|Your session crashed",
        "category": "COLAB.RAM_CRASH",
        "case_study": None,
        "governance": "COLAB",
        "cause": "Colab session crashed due to high RAM usage — model or data too large for available memory",
        "fix": "Reduce batch_size, use 8-bit/4-bit quantization, or upgrade to Pro+ for more RAM. Use del model; torch.cuda.empty_cache() between stages.",
        "confidence": "HIGH",
    },
    {
        "pattern": r"session.*disconnected|Runtime disconnected|no longer connected",
        "category": "COLAB.DISCONNECT",
        "case_study": None,
        "governance": "COLAB",
        "cause": "Colab runtime disconnected — idle timeout (~90 min), session timeout (12/24hr), or GPU preemption",
        "fix": "Save checkpoints to Drive every 500 steps. Use checkpoint-and-resume pattern. Upgrade to Pro+ for guaranteed GPU.",
        "confidence": "HIGH",
    },
    {
        "pattern": r"Drive already mounted|drive.*mount.*fail|FileNotFoundError.*/content/drive",
        "category": "COLAB.DRIVE",
        "case_study": None,
        "governance": "COLAB",
        "cause": "Google Drive mount issue — either already mounted, mount failed, or mount lost after disconnect",
        "fix": "Guard mount with: if not os.path.exists('/content/drive/MyDrive'): drive.mount('/content/drive'). Re-mount after reconnecting.",
        "confidence": "HIGH",
    },

    # ENV — Environment errors
    {
        "pattern": r"ModuleNotFoundError.*triton\.ops",
        "category": "ENV.TRITON",
        "case_study": "cs06_gpu_triton",
        "governance": "S13, S16.1.1",
        "cause": "bitsandbytes imports triton.ops which does not exist on Colab's Python 3.12",
        "fix": "Remove bitsandbytes for <=7B inference-only models. Use float16 directly.",
        "confidence": "HIGH",
    },
    {
        "pattern": r"ModuleNotFoundError.*bitsandbytes|bitsandbytes.*error",
        "category": "ENV.BNB",
        "case_study": "cs09_five_failure_gauntlet",
        "governance": "S5, S16.1.1",
        "cause": "bitsandbytes version conflict or missing CUDA runtime on Colab",
        "fix": "Upgrade importlib-metadata first, then install bitsandbytes>=0.45.0. Restart runtime after install.",
        "confidence": "HIGH",
    },
    {
        "pattern": r"xformers.*error|xformers.*fail|cannot.*xformers",
        "category": "ENV.XFORMERS",
        "case_study": None,
        "governance": "S5",
        "cause": "xformers build failure due to PyTorch version mismatch on Colab",
        "fix": "Use pre-built xformers wheel matching Colab's PyTorch version, or disable flash attention",
        "confidence": "MEDIUM",
    },
    {
        "pattern": r"use_fast.*TypeError|TypeError.*bool.*callable.*tokenizer",
        "category": "ENV.TOKENIZER",
        "case_study": "cs09_five_failure_gauntlet",
        "governance": "S5, S16.1.5",
        "cause": "use_fast=False causes TypeError with certain tokenizer+version combos on Colab",
        "fix": "Remove use_fast=False or test tokenizer loading locally first",
        "confidence": "HIGH",
    },
    {
        "pattern": r"ImportError.*install|ModuleNotFoundError",
        "category": "ENV.CELL_CACHE",
        "case_study": "cs07_import_trap",
        "governance": "S14, S12",
        "cause": "Package imported in same cell as pip install, or missing install. On Colab, Runtime Restart may be needed.",
        "fix": "Separate pip install and import into different cells. Restart runtime after installing, then run from import cell.",
        "confidence": "MEDIUM",
    },
    {
        "pattern": r"importlib.*metadata|PackageNotFoundError",
        "category": "ENV.METADATA",
        "case_study": None,
        "governance": "S2.A",
        "cause": "Corrupted package metadata in Colab's Python 3.12 environment",
        "fix": "Run cleanse pattern: pip install -U importlib-metadata first, then restart runtime",
        "confidence": "MEDIUM",
    },

    # API — API surface errors
    {
        "pattern": r"AttributeError.*total_mem[^o]",
        "category": "API.ATTR",
        "case_study": "cs09_five_failure_gauntlet",
        "governance": "S16.1.2",
        "cause": "Correct attribute is .total_memory, not .total_mem",
        "fix": "Change .total_mem to .total_memory",
        "confidence": "HIGH",
    },
    {
        "pattern": r"AttributeError.*has no attribute|DeprecationWarning",
        "category": "API.DEPRECATED",
        "case_study": None,
        "governance": "S16.1.2",
        "cause": "API attribute renamed or removed in Colab's current library versions",
        "fix": "Check library changelog for the correct attribute name",
        "confidence": "MEDIUM",
    },

    # AUTH — Authentication errors
    {
        "pattern": r"401.*Unauthorized.*[Hh]ugging[Ff]ace|gated.*repo|Access.*restricted",
        "category": "AUTH.GATED",
        "case_study": "cs09_five_failure_gauntlet",
        "governance": "S16.1.3",
        "cause": "Model requires HuggingFace authentication — configure via Colab Secrets",
        "fix": "Set HF_TOKEN in Colab Secrets (sidebar > key icon), then: from google.colab import userdata; token = userdata.get('HF_TOKEN')",
        "confidence": "HIGH",
    },
    {
        "pattern": r"token.*expired|Invalid.*token|401.*Unauthorized",
        "category": "AUTH.TOKEN",
        "case_study": None,
        "governance": "S3.1",
        "cause": "API token expired or invalid — Colab sessions require fresh token each time",
        "fix": "Regenerate token on HuggingFace, update Colab Secrets, restart runtime",
        "confidence": "MEDIUM",
    },

    # DATA — Data errors
    {
        "pattern": r"JSONDecodeError|Expecting value|Invalid.*JSON|Extra data",
        "category": "DATA.JSON",
        "case_study": "cs09_five_failure_gauntlet",
        "governance": "S16.1.4",
        "cause": "JSON artifact is corrupted, malformed, or contains non-JSON content",
        "fix": "Validate JSON files: python -c \"import json; json.load(open('file.json'))\"",
        "confidence": "HIGH",
    },
    {
        "pattern": r"FileNotFoundError.*content|No such file.*content",
        "category": "DATA.MISSING",
        "case_study": None,
        "governance": "COLAB",
        "cause": "File missing from /content/ — either never uploaded or lost after disconnect",
        "fix": "Re-upload file, or download from Drive: files are in /content/drive/MyDrive/ if Drive was mounted",
        "confidence": "HIGH",
    },

    # RESOURCE — Resource errors
    {
        "pattern": r"OutOfMemoryError|CUDA out of memory|torch\.cuda\.OutOfMemoryError",
        "category": "RESOURCE.OOM",
        "case_study": None,
        "governance": "S11",
        "cause": "Model + batch size exceeds Colab GPU VRAM (T4=15GB, L4=24GB, A100=80GB)",
        "fix": "Reduce batch_size, enable gradient_checkpointing, use mixed precision or quantization. Consider upgrading Colab tier for more VRAM.",
        "confidence": "HIGH",
    },
    {
        "pattern": r"GPUTooOldForTriton|CUDA capability.*too low|compute capability",
        "category": "RESOURCE.GPU_OLD",
        "case_study": "cs06_gpu_triton",
        "governance": "S13",
        "cause": "GPU CUDA capability below framework minimum (Triton needs >= 7.0). Colab T4 is 7.5, so this is rare on Colab.",
        "fix": "Disable torch.compile, set TORCH_COMPILE_DISABLE=1. This should not happen with Colab's T4/L4/A100.",
        "confidence": "HIGH",
    },
    {
        "pattern": r"exceeded.*time.*limit|timeout|Notebook.*Timeout",
        "category": "RESOURCE.TIMEOUT",
        "case_study": "cs08_training_hang",
        "governance": "S15",
        "cause": "Execution exceeded Colab session limit (Free/Pro: 12hr, Pro+: 24hr)",
        "fix": "Use checkpointing to resume. Save to Drive every N steps. Reduce epochs or optimize data loading.",
        "confidence": "MEDIUM",
    },
    {
        "pattern": r"No space left|Errno 28|disk.*full",
        "category": "RESOURCE.DISK",
        "case_study": None,
        "governance": "",
        "cause": "Disk space exhausted on Colab (~100GB shared with OS)",
        "fix": "Clean /content/ outputs, reduce checkpoint frequency, save only best model to Drive",
        "confidence": "HIGH",
    },

    # LOGIC — Logic errors
    {
        "pattern": r"SyntaxError.*f-string|SyntaxError.*unterminated|SyntaxError.*invalid",
        "category": "LOGIC.ESCAPING",
        "case_study": "cs04_string_escaping",
        "governance": "S9",
        "cause": "String escaping collision when constructing logic inside JSON notebook cells",
        "fix": "Use sovereign script pattern: %%writefile script.py + !python script.py",
        "confidence": "MEDIUM",
    },
]


def classify_error(log_text: str) -> list[dict]:
    """Classify error from log text against known patterns."""
    matches = []
    for entry in ERROR_PATTERNS:
        if re.search(entry["pattern"], log_text, re.IGNORECASE | re.MULTILINE):
            matches.append({
                "category": entry["category"],
                "confidence": entry["confidence"],
                "cause": entry["cause"],
                "fix": entry["fix"],
                "governance": entry["governance"],
                "case_study": entry["case_study"],
                "matched_pattern": entry["pattern"],
            })

    if not matches:
        matches.append({
            "category": "UNKNOWN",
            "confidence": "LOW",
            "cause": "Error does not match any known Colab pattern",
            "fix": "Check full traceback and search for the error message. Consider adding to known_fixes.yaml.",
            "governance": "",
            "case_study": None,
            "matched_pattern": None,
        })

    confidence_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    matches.sort(key=lambda x: confidence_order.get(x["confidence"], 3))
    return matches


def load_custom_fixes(path: str) -> list[dict]:
    """Load additional known fixes from a YAML file."""
    try:
        import yaml
    except ImportError:
        return []

    if not os.path.exists(path):
        return []

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    return data.get("fixes", [])


def print_triage_report(log_text: str, matches: list[dict]) -> None:
    """Print human-readable triage report."""
    error_lines = [
        line for line in log_text.splitlines()
        if any(kw in line.lower() for kw in ["error", "traceback", "exception", "failed", "crashed", "disconnected"])
    ]
    error_summary = error_lines[0][:120] if error_lines else "No recognizable error line"

    print("\nCOLAB TRIAGE REPORT")
    print("=" * 50)
    print(f"Error: {error_summary}")

    primary = matches[0]
    print(f"\nClassification: {primary['category']} ({primary['confidence']} confidence)")

    if primary["case_study"]:
        print(f"Case Study: {primary['case_study']}")
    if primary["governance"]:
        print(f"Governance: {primary['governance']}")

    print(f"\nRoot Cause: {primary['cause']}")
    print(f"\nFix:\n  {primary['fix']}")

    if len(matches) > 1:
        print(f"\nAlternative classifications ({len(matches) - 1}):")
        for m in matches[1:]:
            print(f"  - {m['category']} ({m['confidence']}): {m['cause'][:80]}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="colab-ml-preflight: Error classification and known-fix lookup for Colab"
    )
    parser.add_argument("--error-log", required=True,
                        help="Path to error log file, or '-' for stdin")
    parser.add_argument("--known-fixes",
                        help="Path to additional known-fixes YAML file")
    parser.add_argument("--json-output", action="store_true",
                        help="Output as JSON")
    parser.add_argument("--verbose", action="store_true",
                        help="Show full match details")

    args = parser.parse_args()

    if args.error_log == "-":
        log_text = sys.stdin.read()
    elif os.path.exists(args.error_log):
        with open(args.error_log, "r", encoding="utf-8", errors="replace") as f:
            log_text = f.read()
    else:
        print(f"Error: File not found: {args.error_log}", file=sys.stderr)
        sys.exit(2)

    if not log_text.strip():
        print("Error: No log content to triage", file=sys.stderr)
        sys.exit(2)

    matches = classify_error(log_text)

    if args.json_output:
        print(json.dumps({
            "platform": "colab",
            "classifications": matches,
            "primary": matches[0],
            "total_matches": len(matches),
        }, indent=2))
    else:
        print_triage_report(log_text, matches)

    sys.exit(0)


if __name__ == "__main__":
    main()
