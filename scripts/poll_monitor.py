#!/usr/bin/env python3
"""
colab-ml-preflight: In-Notebook Execution Monitor

Colab has no external polling API like Kaggle. This script provides
in-notebook monitoring utilities: heartbeat generation, GPU monitoring,
RAM tracking, and session health checks.

Usage (import in Colab notebook):
    from scripts.poll_monitor import ColabMonitor
    monitor = ColabMonitor()
    monitor.start()

Usage (standalone for local testing):
    python poll_monitor.py --check-health
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import threading
from datetime import datetime


class ColabMonitor:
    """In-notebook monitor for Google Colab sessions."""

    def __init__(self, heartbeat_interval: int = 300, gpu_interval: int = 300,
                 checkpoint_dir: str | None = None):
        self.heartbeat_interval = heartbeat_interval
        self.gpu_interval = gpu_interval
        self.checkpoint_dir = checkpoint_dir or '/content/drive/MyDrive/checkpoints/'
        self.stop_event = threading.Event()
        self._threads = []
        self.start_time = time.time()

    def log(self, msg: str) -> None:
        """Emit timestamped log."""
        elapsed = time.time() - self.start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        print(f"[{mins:02d}:{secs:02d}] {msg}", flush=True)

    def check_gpu(self) -> dict | None:
        """Check GPU status. Returns dict with GPU info or None."""
        try:
            import torch
            if not torch.cuda.is_available():
                return {"available": False, "message": "No GPU detected"}
            
            name = torch.cuda.get_device_name(0)
            cap = torch.cuda.get_device_capability(0)
            allocated = torch.cuda.memory_allocated(0) / 1e9
            reserved = torch.cuda.memory_reserved(0) / 1e9
            total = torch.cuda.get_device_properties(0).total_memory / 1e9
            util = allocated / total * 100 if total > 0 else 0

            # Detect Colab tier
            tier = "unknown"
            if "T4" in name:
                tier = "free/pro"
            elif "L4" in name:
                tier = "pro"
            elif "A100" in name:
                tier = "pro+"

            return {
                "available": True,
                "name": name,
                "capability": f"{cap[0]}.{cap[1]}",
                "allocated_gb": round(allocated, 1),
                "reserved_gb": round(reserved, 1),
                "total_gb": round(total, 1),
                "utilization_pct": round(util, 0),
                "tier": tier,
                "oom_risk": util > 85,
            }
        except ImportError:
            return {"available": False, "message": "torch not available"}

    def check_ram(self) -> dict:
        """Check system RAM status."""
        try:
            import psutil
            ram = psutil.virtual_memory()
            return {
                "total_gb": round(ram.total / 1e9, 1),
                "used_gb": round(ram.used / 1e9, 1),
                "available_gb": round(ram.available / 1e9, 1),
                "percent": ram.percent,
                "crash_risk": ram.percent > 90,
            }
        except ImportError:
            return {"error": "psutil not available — pip install psutil"}

    def check_disk(self) -> dict:
        """Check disk space on /content/."""
        import shutil
        try:
            usage = shutil.disk_usage('/content/')
            return {
                "total_gb": round(usage.total / 1e9, 1),
                "used_gb": round(usage.used / 1e9, 1),
                "free_gb": round(usage.free / 1e9, 1),
                "percent": round(usage.used / usage.total * 100, 1),
            }
        except (FileNotFoundError, OSError):
            return {"error": "Not running on Colab"}

    def check_drive_mount(self) -> bool:
        """Check if Google Drive is mounted."""
        return os.path.exists('/content/drive/MyDrive')

    def health_report(self) -> dict:
        """Full health check report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "gpu": self.check_gpu(),
            "ram": self.check_ram(),
            "disk": self.check_disk(),
            "drive_mounted": self.check_drive_mount(),
            "elapsed_seconds": round(time.time() - self.start_time, 0),
        }

    def _gpu_monitor_loop(self) -> None:
        """Background GPU monitoring loop."""
        while not self.stop_event.is_set():
            gpu = self.check_gpu()
            if gpu and gpu.get("available"):
                self.log(f"[GPU] {gpu['name']} | {gpu['allocated_gb']}/{gpu['total_gb']}GB "
                        f"({gpu['utilization_pct']:.0f}%) | tier={gpu['tier']}"
                        f"{' | OOM RISK!' if gpu['oom_risk'] else ''}")
            self.stop_event.wait(self.gpu_interval)

    def start(self) -> None:
        """Start background monitoring."""
        self.log("Starting Colab monitor...")
        self.log(f"Drive mounted: {self.check_drive_mount()}")

        gpu_thread = threading.Thread(target=self._gpu_monitor_loop, daemon=True)
        gpu_thread.start()
        self._threads.append(gpu_thread)

        self.log("Monitor running. Call monitor.stop() to stop.")

    def stop(self) -> None:
        """Stop background monitoring."""
        self.stop_event.set()
        for t in self._threads:
            t.join(timeout=5)
        self.log("Monitor stopped.")

    def heartbeat(self, step: int, total: int, metrics: dict | None = None) -> None:
        """Emit a heartbeat for training loops."""
        timestamp = time.strftime('%H:%M:%S')
        msg = f"[HEARTBEAT] [{timestamp}] {step}/{total}"
        if metrics:
            msg += f" | {' '.join(f'{k}={v:.4f}' for k, v in metrics.items())}"
        print(msg, flush=True)


def print_health_report(report: dict) -> None:
    """Print human-readable health report."""
    print("\nCOLAB HEALTH REPORT")
    print("=" * 50)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Elapsed: {report['elapsed_seconds']}s")
    print(f"Drive Mounted: {report['drive_mounted']}")

    gpu = report.get("gpu", {})
    if gpu.get("available"):
        print(f"\nGPU: {gpu['name']} (CUDA {gpu['capability']})")
        print(f"  VRAM: {gpu['allocated_gb']}/{gpu['total_gb']}GB ({gpu['utilization_pct']}%)")
        print(f"  Tier: {gpu['tier']}")
        if gpu.get("oom_risk"):
            print("  WARNING: OOM risk (>85% utilization)")
    else:
        print(f"\nGPU: {gpu.get('message', 'Not available')}")

    ram = report.get("ram", {})
    if "error" not in ram:
        print(f"\nRAM: {ram['used_gb']}/{ram['total_gb']}GB ({ram['percent']}%)")
        if ram.get("crash_risk"):
            print("  CRITICAL: RAM crash risk (>90% usage)")
    
    disk = report.get("disk", {})
    if "error" not in disk:
        print(f"\nDisk: {disk['used_gb']}/{disk['total_gb']}GB ({disk['percent']}%)")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="colab-ml-preflight: Colab session health monitor"
    )
    parser.add_argument("--check-health", action="store_true",
                        help="Print a one-time health report")
    parser.add_argument("--json-output", action="store_true",
                        help="Output as JSON")

    args = parser.parse_args()

    monitor = ColabMonitor()

    if args.check_health:
        report = monitor.health_report()
        if args.json_output:
            print(json.dumps(report, indent=2))
        else:
            print_health_report(report)
    else:
        print("Usage: python poll_monitor.py --check-health")
        print("Or import in Colab: from scripts.poll_monitor import ColabMonitor")
        sys.exit(0)


if __name__ == "__main__":
    main()
