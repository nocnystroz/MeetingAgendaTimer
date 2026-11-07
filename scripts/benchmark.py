"""Linux /proc benchmark of the packaged GUI, with isolated temporary data."""

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path


def sample(pid):
    stats = (Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()
    ticks = int(stats[11]) + int(stats[12])
    rss = int(stats[21]) * os.sysconf("SC_PAGE_SIZE")
    return ticks, rss


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    executable = args.executable.resolve()
    with tempfile.TemporaryDirectory(prefix="licznik-benchmark-") as temporary:
        from meeting_timer.documents import terms_version
        # Synthetic benchmark fixture only; never writes acceptance to the user's data folder.
        (Path(temporary) / "consent.json").write_text(json.dumps({
            "accepted": True, "terms_version": terms_version(), "language": "pl",
            "accepted_at": 0, "diagnostic_fixture": True}), encoding="utf-8")
        ready = Path(temporary) / "ready.json"
        env = dict(os.environ, MEETING_TIMER_DATA_DIR=temporary, MEETING_TIMER_READY_FILE=str(ready))
        start = time.perf_counter()
        process = subprocess.Popen([str(executable)], env=env, cwd=temporary,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            while not ready.exists():
                if process.poll() is not None or time.perf_counter() - start > 20:
                    raise RuntimeError("Aplikacja nie potwierdziła gotowości.")
                time.sleep(0.02)
            startup = time.perf_counter() - start
            time.sleep(1)
            ticks_before, rss = sample(process.pid)
            measured_start = time.perf_counter()
            peak = rss
            while time.perf_counter() - measured_start < args.seconds:
                time.sleep(0.2)
                _, rss = sample(process.pid)
                peak = max(peak, rss)
            ticks_after, _ = sample(process.pid)
            elapsed = time.perf_counter() - measured_start
            result = {"startup_s": round(startup, 2), "rss_mib": round(rss / 1024**2, 1),
                      "peak_rss_mib": round(peak / 1024**2, 1),
                      "idle_cpu_one_core_percent": round((ticks_after - ticks_before) /
                      os.sysconf("SC_CLK_TCK") / elapsed * 100, 2), "sample_s": round(elapsed, 1)}
            print(json.dumps(result, indent=2))
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
