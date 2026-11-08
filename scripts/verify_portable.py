"""Run the frozen binary outside the source directory, with synthetic data."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    bundle = root / "dist" / ("core" if args.core else "full") / "Licznik-Spotkaniowy"
    if sys.platform == "darwin":
        executable = bundle.with_suffix(".app") / "Contents/MacOS/Licznik-Spotkaniowy"
        portable_readme = bundle.parent / "README.txt"
    elif sys.platform == "win32":
        executable = bundle / "Licznik-Spotkaniowy.exe"
        portable_readme = bundle / "README.txt"
    else:
        executable = bundle / "Licznik-Spotkaniowy"
        portable_readme = bundle / "README.txt"
    instructions = portable_readme.read_text(encoding="utf-8")
    expected_variant = "core" if args.core else "full"
    assert f"Wariant / Variant: {expected_variant}" in instructions
    assert "PL\n" in instructions and "EN\n" in instructions
    assert "github.com/nocnystroz/MeetingAgendaTimer/releases" in instructions
    assert executable.is_file()
    with tempfile.TemporaryDirectory(prefix="licznik-frozen-check-") as temporary:
        report = Path(temporary) / "result.json"
        env = dict(os.environ, MEETING_TIMER_DATA_DIR=temporary, MEETING_TIMER_SMOKE_OUTPUT=str(report),
                   QT_QPA_PLATFORM="offscreen")
        subprocess.run([str(executable), "--smoke-test" if args.core else "--smoke-test-full"],
                       cwd=temporary, env=env, check=True, timeout=45)
        result = json.loads(report.read_text())
        assert result.get("ok") and result.get("network_requests") == 0
        print(json.dumps(result))


if __name__ == "__main__":
    main()
