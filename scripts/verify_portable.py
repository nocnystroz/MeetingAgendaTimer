"""Run the frozen binary outside the source directory, with synthetic data."""

import argparse
import json
import os
import platform
import plistlib
import subprocess
import sys
import tempfile
import zipfile
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
    if sys.platform in ("win32", "darwin"):
        archive = root / "dist" / (
            f"licznik-{platform.system().lower()}-{platform.machine().lower()}-{expected_variant}.zip")
        with zipfile.ZipFile(archive) as stream:
            names = stream.namelist()
            assert "Licznik-Spotkaniowy/README.txt" in names
            launcher = ("Licznik-Spotkaniowy/Licznik-Spotkaniowy.app/Contents/MacOS/Licznik-Spotkaniowy"
                        if sys.platform == "darwin" else "Licznik-Spotkaniowy/Licznik-Spotkaniowy.exe")
            assert launcher in names
            assert all(name.startswith(("Licznik-Spotkaniowy/", "__MACOSX/")) for name in names)
        if sys.platform == "darwin":
            resources = bundle.with_suffix(".app") / "Contents/Resources"
            with (bundle.with_suffix(".app") / "Contents/Info.plist").open("rb") as stream:
                plist = plistlib.load(stream)
            assert (resources / plist["CFBundleIconFile"]).is_file()
        else:
            import pefile
            pe = pefile.PE(str(executable))
            assert any(entry.id == pefile.RESOURCE_TYPE["RT_GROUP_ICON"]
                       for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries)
            pe.close()
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
