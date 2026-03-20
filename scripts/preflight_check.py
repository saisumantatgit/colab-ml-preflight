#!/usr/bin/env python3
"""
colab-ml-preflight: Notebook Preflight Validator

Validates an ML notebook (.ipynb) or Python script (.py) against preflight
rules before running on Google Colab. Platform is always Colab — no --platform flag needed.

Usage:
    python preflight_check.py notebook.ipynb [--strict] [--json-output]

Every check traces to a governance section (S-number) or post-incident review.
"""

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Finding data structure
# ---------------------------------------------------------------------------

class Finding:
    """A single preflight finding."""

    BLOCKER = "BLOCKER"
    WARNING = "WARNING"
    INFO = "INFO"

    def __init__(self, severity: str, code: str, message: str, governance: str,
                 cell: int | None = None, line: int | None = None):
        self.severity = severity
        self.code = code
        self.message = message
        self.governance = governance
        self.cell = cell
        self.line = line

    def to_dict(self) -> dict:
        d = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "governance": self.governance,
        }
        if self.cell is not None:
            d["cell"] = self.cell
        if self.line is not None:
            d["line"] = self.line
        return d

    def __str__(self) -> str:
        loc = ""
        if self.cell is not None:
            loc = f"Cell {self.cell}"
        if self.line is not None:
            loc += f":L{self.line}" if loc else f"L{self.line}"
        prefix = f"[{self.severity[0]}] "
        if loc:
            prefix += f"{loc}: "
        return f"{prefix}{self.message} ({self.governance})"


# ---------------------------------------------------------------------------
# Notebook / script loading
# ---------------------------------------------------------------------------

def load_notebook(path: str) -> list[dict]:
    """Load notebook cells. Returns list of {source, cell_type, index}."""
    with open(path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    cells = []
    for i, cell in enumerate(nb.get("cells", [])):
        source = "".join(cell.get("source", []))
        cells.append({
            "source": source,
            "cell_type": cell.get("cell_type", "code"),
            "index": i,
        })
    return cells


def load_script(path: str) -> list[dict]:
    """Load a Python script as a single 'cell'."""
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    return [{"source": source, "cell_type": "code", "index": 0}]


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_syntax(cells: list[dict], findings: list[Finding]) -> None:
    """Check Python syntax of each code cell (S9.3)."""
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        source = cell["source"]
        lines = source.splitlines()
        python_lines = [
            line for line in lines
            if not line.strip().startswith(("%", "!", "?"))
        ]
        clean = "\n".join(python_lines)
        if not clean.strip():
            continue
        try:
            ast.parse(clean)
        except SyntaxError as e:
            findings.append(Finding(
                Finding.BLOCKER, "SYNTAX",
                f"SyntaxError: {e.msg} (line {e.lineno})",
                "S9.3", cell=cell["index"], line=e.lineno,
            ))


def check_json_artifacts(notebook_dir: str, findings: list[Finding]) -> None:
    """Validate JSON files in the notebook directory (S16.1.4)."""
    if not notebook_dir or not os.path.isdir(notebook_dir):
        return
    json_count = 0
    for fname in os.listdir(notebook_dir):
        if fname.endswith(".json"):
            fpath = os.path.join(notebook_dir, fname)
            json_count += 1
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                findings.append(Finding(
                    Finding.BLOCKER, "JSON_INVALID",
                    f"Invalid JSON: {fname} — {e}",
                    "S16.1.4",
                ))
    if json_count > 0:
        findings.append(Finding(
            Finding.INFO, "JSON_OK",
            f"{json_count} JSON artifact(s) validated successfully",
            "S16.1.4",
        ))


def check_install_import_separation(cells: list[dict], findings: list[Finding]) -> None:
    """Check that pip install and import are in separate cells (S12.1)."""
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        source = cell["source"]
        lines = source.splitlines()
        has_install = any(re.match(r"\s*[!%]pip\s+install", line) for line in lines)
        has_import = any(
            re.match(r"\s*(import|from)\s+\w+", line)
            for line in lines
            if not line.strip().startswith("#")
        )
        if has_install and has_import:
            findings.append(Finding(
                Finding.BLOCKER, "CELL_SEPARATION",
                "pip install and import in same cell — split into separate cells. "
                "Colab requires Runtime Restart between install and import.",
                "S12.1", cell=cell["index"],
            ))


def check_deterministic_settings(cells: list[dict], findings: list[Finding]) -> None:
    """Check for deterministic seeds and inference settings (S1, S4)."""
    all_source = "\n".join(c["source"] for c in cells if c["cell_type"] == "code")

    has_seed = any(s in all_source for s in [
        "manual_seed", "random.seed", "np.random.seed",
        "seed_everything", "set_seed",
    ])
    uses_stochastic = any(s in all_source for s in [
        "import torch", "import numpy", "import random",
    ])
    if uses_stochastic and not has_seed:
        findings.append(Finding(
            Finding.WARNING, "NO_SEED",
            "No random seed set — results will not be reproducible",
            "S4",
        ))

    if "temperature" in all_source:
        temp_matches = re.findall(r"temperature\s*=\s*([0-9.]+)", all_source)
        for val in temp_matches:
            if float(val) != 0.0:
                findings.append(Finding(
                    Finding.WARNING, "NON_ZERO_TEMP",
                    f"temperature={val} — should be 0.0 for deterministic inference",
                    "S1.1",
                ))

    if "do_sample" in all_source:
        if "do_sample=True" in all_source or "do_sample = True" in all_source:
            findings.append(Finding(
                Finding.WARNING, "DO_SAMPLE_TRUE",
                "do_sample=True — should be False for deterministic inference",
                "S1.2",
            ))


def check_interactive_inputs(cells: list[dict], findings: list[Finding]) -> None:
    """Check for input() calls that will hang headless runs (S4)."""
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        source = cell["source"]
        python_lines = "\n".join(
            line for line in source.splitlines()
            if not line.strip().startswith(("%", "!", "?"))
        )
        if not python_lines.strip():
            continue
        try:
            tree = ast.parse(python_lines)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "input"):
                findings.append(Finding(
                    Finding.BLOCKER, "INPUT_CALL",
                    "input() will hang in long-running Colab cells — use Colab Secrets or env vars",
                    "S4", cell=cell["index"],
                ))


def check_flush_on_print(cells: list[dict], findings: list[Finding]) -> None:
    """Check that print() statements include flush=True (S4)."""
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        for line_no, line in enumerate(cell["source"].splitlines(), 1):
            stripped = line.strip()
            if (stripped.startswith("print(")
                    and "flush" not in stripped
                    and not stripped.startswith("#")
                    and "tqdm" not in stripped):
                findings.append(Finding(
                    Finding.WARNING, "NO_FLUSH",
                    f"print() without flush=True — Colab stdout may be buffered",
                    "S4", cell=cell["index"], line=line_no,
                ))
                break


def check_gpu_capability(cells: list[dict], findings: list[Finding]) -> None:
    """Check for GPU capability validation presence (S11.1)."""
    all_source = "\n".join(c["source"] for c in cells if c["cell_type"] == "code")
    if "get_device_capability" not in all_source:
        findings.append(Finding(
            Finding.WARNING, "NO_GPU_CHECK",
            "No GPU capability check — add torch.cuda.get_device_capability() to detect T4/L4/A100",
            "S11.1",
        ))


def check_provenance_metadata(cells: list[dict], findings: list[Finding]) -> None:
    """Check for provenance metadata emission (S4.4)."""
    all_source = "\n".join(c["source"] for c in cells if c["cell_type"] == "code")
    required_fields = ["git_commit", "gpu_type", "package_versions"]
    found = sum(1 for f in required_fields if f in all_source)
    if found == 0:
        findings.append(Finding(
            Finding.WARNING, "NO_PROVENANCE",
            "No provenance metadata emission detected (git_commit, gpu_type, package_versions)",
            "S4.4",
        ))


def check_hardcoded_paths(cells: list[dict], findings: list[Finding]) -> None:
    """Check for hardcoded local paths (platform portability)."""
    local_patterns = [
        (r'["\'][A-Z]:\\', "Windows path"),
        (r'["\']/Users/', "macOS path"),
        (r'["\']/home/[a-z]', "Linux home directory"),
        (r'["\']~/[^"\']+["\']', "Home shorthand"),
        (r'["\']/kaggle/', "Kaggle path (wrong platform)"),
        (r'["\']/home/ec2-user/', "SageMaker path (wrong platform)"),
    ]
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        for line_no, line in enumerate(cell["source"].splitlines(), 1):
            if line.strip().startswith("#"):
                continue
            for pattern, label in local_patterns:
                if re.search(pattern, line):
                    findings.append(Finding(
                        Finding.BLOCKER, "HARDCODED_PATH",
                        f"Hardcoded {label} will fail on Colab — use /content/ or /content/drive/MyDrive/",
                        "S17.1", cell=cell["index"], line=line_no,
                    ))
                    break


def check_colab_specific(cells: list[dict], findings: list[Finding]) -> None:
    """Colab-specific checks (S16.1)."""
    all_source = "\n".join(c["source"] for c in cells if c["cell_type"] == "code")

    # BNB + Python 3.12 conflict
    if "bitsandbytes" in all_source:
        findings.append(Finding(
            Finding.WARNING, "BNB_CONFLICT",
            "bitsandbytes may cause triton.ops conflict on Colab (Python 3.12)",
            "S16.1.1",
        ))

    # total_mem vs total_memory
    if ".total_mem" in all_source and ".total_memory" not in all_source:
        findings.append(Finding(
            Finding.BLOCKER, "TOTAL_MEM",
            "Use .total_memory not .total_mem (changed in recent PyTorch)",
            "S16.1.2",
        ))

    # Pip quoting
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        for line in cell["source"].splitlines():
            if re.match(r"\s*!pip\s+install.*>=", line) and '"' not in line and "'" not in line:
                findings.append(Finding(
                    Finding.WARNING, "PIP_QUOTING",
                    f"Unquoted pip version spec — shell may interpret > as redirect",
                    "S16.1.6", cell=cell["index"],
                ))
                break

    # Drive mount check — if outputs are saved to /content/ without Drive
    saves_to_content = bool(re.search(r'save.*["\']/?content/[^d]', all_source))
    has_drive_mount = "drive.mount" in all_source
    if saves_to_content and not has_drive_mount:
        findings.append(Finding(
            Finding.WARNING, "NO_DRIVE_MOUNT",
            "Saving outputs to /content/ without Drive mount — files will be lost on disconnect",
            "COLAB",
        ))

    # Check for gated models without Colab Secrets
    gated_patterns = ["meta-llama/", "google/gemma", "mistralai/"]
    has_gated = any(p in all_source for p in gated_patterns)
    has_secrets = "userdata.get" in all_source or "userdata.get" in all_source
    has_hf_login = "huggingface_hub.login" in all_source or "HF_TOKEN" in all_source
    if has_gated and not has_secrets and not has_hf_login:
        findings.append(Finding(
            Finding.WARNING, "NO_COLAB_SECRETS",
            "Gated model reference found but no Colab Secrets or HF token setup detected",
            "S16.1.3",
        ))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_preflight(path: str, strict: bool = False) -> dict:
    """Run all preflight checks for Colab and return results."""
    findings: list[Finding] = []

    if path.endswith(".ipynb"):
        try:
            cells = load_notebook(path)
        except json.JSONDecodeError:
            return {
                "file": path,
                "valid": False,
                "error": "Not a valid .ipynb file (invalid JSON)",
                "findings": [],
            }
    elif path.endswith(".py"):
        cells = load_script(path)
    else:
        return {
            "file": path,
            "valid": False,
            "error": "Unsupported file type (expected .ipynb or .py)",
            "findings": [],
        }

    # Run all checks
    check_syntax(cells, findings)
    check_json_artifacts(os.path.dirname(os.path.abspath(path)), findings)
    check_install_import_separation(cells, findings)
    check_deterministic_settings(cells, findings)
    check_interactive_inputs(cells, findings)
    check_flush_on_print(cells, findings)
    check_gpu_capability(cells, findings)
    check_provenance_metadata(cells, findings)
    check_hardcoded_paths(cells, findings)
    check_colab_specific(cells, findings)

    blockers = [f for f in findings if f.severity == Finding.BLOCKER]
    warnings = [f for f in findings if f.severity == Finding.WARNING]
    infos = [f for f in findings if f.severity == Finding.INFO]

    if strict:
        passed = len(blockers) == 0 and len(warnings) == 0
    else:
        passed = len(blockers) == 0

    return {
        "file": path,
        "platform": "colab",
        "strict": strict,
        "passed": passed,
        "blockers": len(blockers),
        "warnings": len(warnings),
        "infos": len(infos),
        "findings": [f.to_dict() for f in findings],
    }


def print_report(results: dict) -> None:
    """Print human-readable preflight report."""
    print(f"\nPREFLIGHT REPORT: {results['file']}")
    print(f"Platform: colab (Python 3.12, PyTorch 2.8, CUDA 12.6)")
    if results.get("strict"):
        print("Mode: STRICT (warnings are blockers)")
    print("=" * 50)

    findings = results["findings"]
    blockers = [f for f in findings if f["severity"] == "BLOCKER"]
    warnings = [f for f in findings if f["severity"] == "WARNING"]
    infos = [f for f in findings if f["severity"] == "INFO"]

    if blockers:
        print(f"\nBLOCKERS ({len(blockers)}):")
        for i, f in enumerate(blockers, 1):
            loc = ""
            if "cell" in f:
                loc = f"Cell {f['cell']}"
            if "line" in f:
                loc += f":L{f['line']}" if loc else f"L{f['line']}"
            print(f"  [B{i}] {loc + ': ' if loc else ''}{f['message']} ({f['governance']})")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for i, f in enumerate(warnings, 1):
            loc = ""
            if "cell" in f:
                loc = f"Cell {f['cell']}"
            print(f"  [W{i}] {loc + ': ' if loc else ''}{f['message']} ({f['governance']})")

    if infos:
        print(f"\nINFO ({len(infos)}):")
        for i, f in enumerate(infos, 1):
            print(f"  [I{i}] {f['message']}")

    verdict = "PASS" if results["passed"] else f"FAIL ({results['blockers']} blockers)"
    print(f"\nVERDICT: {verdict}\n")


def main():
    parser = argparse.ArgumentParser(
        description="colab-ml-preflight: Validate ML notebooks before running on Google Colab"
    )
    parser.add_argument("notebook", help="Path to .ipynb or .py file")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as blockers",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    if not os.path.exists(args.notebook):
        print(f"Error: File not found: {args.notebook}", file=sys.stderr)
        sys.exit(2)

    results = run_preflight(args.notebook, args.strict)

    if args.json_output:
        print(json.dumps(results, indent=2))
    else:
        print_report(results)

    sys.exit(0 if results["passed"] else 1)


if __name__ == "__main__":
    main()
