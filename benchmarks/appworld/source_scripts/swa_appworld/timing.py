"""Measure compiler subprocesses in the parent, outside AppWorld/freezegun."""
from __future__ import annotations
import subprocess
import time


def measure_process(command, **kwargs):
    started = time.perf_counter_ns()
    result = subprocess.run(command, **kwargs)
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    return result, elapsed_ms
