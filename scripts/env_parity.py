#!/usr/bin/env python3
"""
colab-ml-preflight: Environment Parity Checker

Compares notebook environment assumptions against Google Colab's known constraints.
Detects version mismatches, package conflicts, and Colab-specific pitfalls.

Usage:
    python env_parity.py notebook.ipynb [--snapshot-file platforms/colab.json] [--json-output]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Colab snapshot (built-in default)
# ---------------------------------------------------------------------------

COLAB_SNAPSHOT = {
    "python_version": "3.12",
    "torch_version": "2.8",
    "cuda_version": "12.6",
    "working_directory": "/content/",
    "drive_mount_point": "/content/drive/MyDrive/",
    "pre_installed": [
        "torch", "torchvision", "torchaudio", "numpy", "pandas",
        "scikit-learn", "scipy", "matplotlib", "seaborn", "pillow",
    ],
    "not_pre_installed": [
        "transformers", "peft", "accelerate", "bitsandbytes",
        "datasets", "evaluate", "huggingface_hub",
    ],
    "known_conflicts": [
        {
            "pattern": "bitsandbytes",
            "condition": "python>=3.12",
            "description": "bitsandbytes may import triton.ops which fails on Colab (Python 3.12)",
            "fix": "Remove bitsandbytes for <=7B inference-only models",
            "governance": "S16.1.1",
        },
    ],
    "gpu_options": [
        {"name": "Tesla T4", "vram_gb": 15, "cuda_capability": "7.5", "tier": "free"},
        {"name": "L4", "vram_gb": 24, "cuda_capability": "8.9", "tier": "pro"},
        {"name": "A100", "vram_gb": 40, "cuda_capability": "8.0", "tier": "pro+"},
    ],
}


def load_snapshot(snapshot_file: str | None = None) -> dict:
    """Load Colab platform snapshot from file or use built-in default."""
    if snapshot_file and os.path.exists(snapshot_file):
        with open(snapshot_file, "r") as f:
            return json.load(f)

    # Try bundled snapshot
    script_dir = Path(__file__).parent.parent
    bundled = script_dir / "platforms" / "colab.json"
    if bundled.exists():
        with open(bundled, "r") as f:
            return json.load(f)

    return COLAB_SNAPSHOT


def extract_notebook_assumptions(path: str) -> dict:
    """Extract environment assumptions from a notebook or script."""
    if path.endswith(".ipynb"):
        with open(path, "r", encoding="utf-8") as f:
            nb = json.load(f)
        sources = [
            "".join(cell.get("source", []))
            for cell in nb.get("cells", [])
            if cell.get("cell_type") == "code"
        ]
    else:
        with open(path, "r", encoding="utf-8") as f:
            sources = [f.read()]

    all_source = "\n".join(sources)

    # Extract pip install packages
    pip_packages = []
    for match in re.finditer(r"[!%]pip\s+install\s+([^\n]+)", all_source):
        line = match.group(1)
        for pkg in line.split():
            pkg = pkg.strip('"').strip("'")
            if not pkg.startswith("-"):
                pip_packages.append(pkg)

    # Extract imports
    imports = set()
    for match in re.finditer(r"^\s*(?:import|from)\s+(\w+)", all_source, re.MULTILINE):
        imports.add(match.group(1))

    # Extract hardcoded paths
    paths_found = []
    path_patterns = [
        (r'["\'](/content/[^"\']+)["\']', "colab"),
        (r'["\'](/kaggle/[^"\']+)["\']', "kaggle"),
        (r'["\'](/home/ec2-user/[^"\']+)["\']', "sagemaker"),
        (r'["\'](/Users/[^"\']+)["\']', "local_mac"),
        (r'["\']([A-Z]:\\[^"\']+)["\']', "local_win"),
        (r'["\'](/home/[a-z][^"\']+)["\']', "local_linux"),
    ]
    for pattern, ptype in path_patterns:
        for match in re.finditer(pattern, all_source):
            paths_found.append({"path": match.group(1), "type": ptype})

    # Check for gated model references
    gated_patterns = [r"meta-llama/", r"google/gemma", r"mistralai/"]
    gated_models = []
    for pattern in gated_patterns:
        for match in re.finditer(pattern, all_source):
            gated_models.append(match.group())

    return {
        "pip_packages": pip_packages,
        "imports": list(imports),
        "paths": paths_found,
        "gated_models": gated_models,
        "uses_bitsandbytes": "bitsandbytes" in all_source,
        "uses_total_mem": ".total_mem" in all_source and ".total_memory" not in all_source,
        "uses_use_fast_false": "use_fast=False" in all_source or "use_fast = False" in all_source,
        "has_drive_mount": "drive.mount" in all_source,
        "saves_to_content": bool(re.search(r'save.*["\']/?content/[^d]', all_source)),
        "has_colab_secrets": "userdata.get" in all_source,
    }


def check_parity(assumptions: dict, snapshot: dict) -> list[dict]:
    """Compare assumptions against Colab snapshot."""
    findings = []

    # Check hardcoded paths for wrong platform
    for p in assumptions["paths"]:
        if p["type"].startswith("local_"):
            findings.append({
                "severity": "MISMATCH",
                "message": f"Hardcoded local path will fail on Colab: {p['path'][:60]}",
                "fix": "Use /content/ for working directory or /content/drive/MyDrive/ for persistent storage",
                "governance": "S17.1",
            })
        elif p["type"] not in ("colab",):
            findings.append({
                "severity": "MISMATCH",
                "message": f"Path is for {p['type']}, not Colab: {p['path'][:60]}",
                "fix": "Use /content/ or /content/drive/MyDrive/",
                "governance": "S17.1",
            })

    # Check known conflicts
    for conflict in snapshot.get("known_conflicts", []):
        pattern = conflict.get("pattern", "")
        if pattern and pattern in "\n".join(assumptions.get("pip_packages", [])):
            findings.append({
                "severity": "MISMATCH",
                "message": conflict["description"],
                "fix": conflict["fix"],
                "governance": conflict.get("governance", ""),
            })

    # Check gated models without auth
    if assumptions["gated_models"] and not assumptions["has_colab_secrets"]:
        findings.append({
            "severity": "MISMATCH",
            "message": f"Gated model references found but no Colab Secrets setup detected: {', '.join(assumptions['gated_models'])}",
            "fix": "Use Colab Secrets (from google.colab import userdata) or ungated community mirrors",
            "governance": "S16.1.3",
        })

    # Check .total_mem
    if assumptions["uses_total_mem"]:
        findings.append({
            "severity": "MISMATCH",
            "message": ".total_mem is not a valid attribute — use .total_memory",
            "fix": "Change .total_mem to .total_memory",
            "governance": "S16.1.2",
        })

    # Check Drive mount for persistence
    if assumptions["saves_to_content"] and not assumptions["has_drive_mount"]:
        findings.append({
            "severity": "MISMATCH",
            "message": "Saving to /content/ without Drive mount — outputs lost on disconnect",
            "fix": "Add drive.mount('/content/drive') and save to /content/drive/MyDrive/",
            "governance": "COLAB",
        })

    # Check pre-installed packages (unnecessary installs)
    pre_installed = set(snapshot.get("pre_installed", snapshot.get("pre_installed_packages", [])))
    for pkg in assumptions["pip_packages"]:
        pkg_name = re.split(r"[><=!]", pkg)[0].lower().replace("-", "_")
        if pkg_name in {p.lower().replace("-", "_") for p in pre_installed}:
            findings.append({
                "severity": "INFO",
                "message": f"{pkg} is already pre-installed on Colab — install may cause version conflict",
                "fix": "Remove from pip install unless you need a specific version",
                "governance": "S16.2",
            })

    return findings


def print_parity_report(path: str, findings: list[dict]) -> None:
    """Print human-readable parity report."""
    print(f"\nENVIRONMENT PARITY: {path} vs Google Colab")
    print("=" * 50)

    mismatches = [f for f in findings if f["severity"] == "MISMATCH"]
    infos = [f for f in findings if f["severity"] == "INFO"]

    if mismatches:
        print(f"\nMISMATCHES ({len(mismatches)}):")
        for i, f in enumerate(mismatches, 1):
            print(f"  [M{i}] {f['message']} ({f['governance']})")
            print(f"       FIX: {f['fix']}")
    else:
        print("\nNo mismatches found.")

    if infos:
        print(f"\nINFO ({len(infos)}):")
        for i, f in enumerate(infos, 1):
            print(f"  [I{i}] {f['message']}")

    count = len(mismatches)
    print(f"\nVERDICT: {count} mismatch(es) found\n")


def main():
    parser = argparse.ArgumentParser(
        description="colab-ml-preflight: Check environment parity between notebook and Google Colab"
    )
    parser.add_argument("notebook", help="Path to .ipynb or .py file")
    parser.add_argument(
        "--snapshot-file",
        help="Path to Colab snapshot JSON (default: bundled)",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    if not os.path.exists(args.notebook):
        print(f"Error: File not found: {args.notebook}", file=sys.stderr)
        sys.exit(2)

    snapshot = load_snapshot(args.snapshot_file)
    assumptions = extract_notebook_assumptions(args.notebook)
    findings = check_parity(assumptions, snapshot)

    if args.json_output:
        print(json.dumps({
            "file": args.notebook,
            "platform": "colab",
            "findings": findings,
        }, indent=2))
    else:
        print_parity_report(args.notebook, findings)

    mismatches = [f for f in findings if f["severity"] == "MISMATCH"]
    sys.exit(1 if mismatches else 0)


if __name__ == "__main__":
    main()
