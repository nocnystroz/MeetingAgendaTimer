"""Build on the target OS. Bundles interpreter; never installs anything globally."""

import argparse
import importlib.metadata
import importlib.util
import json
import os
import platform
import plistlib
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def package_licenses(destination, full):
    from packaging.requirements import Requirement
    destination.mkdir(parents=True, exist_ok=True)
    packages = ["licznik-spotkaniowy", "PySide6-Essentials", "shiboken6", "certifi"]
    if full:
        packages += ["SoundCard", "numpy", "cffi", "keyring", "PySide6-Addons"]
    seen = set()
    manifest = []
    for name in packages:
        normalized = name.lower().replace("_", "-")
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            dist = importlib.metadata.distribution(name)
        except importlib.metadata.PackageNotFoundError:
            continue
        for requirement in dist.requires or []:
            dependency = Requirement(requirement)
            if not dependency.marker or dependency.marker.evaluate({"extra": ""}):
                packages.append(dependency.name)
        manifest.append({"name": name, "version": dist.version,
                         "license": dist.metadata.get("License-Expression", dist.metadata.get("License", "See upstream")),
                         "url": dist.metadata.get("Home-page", "")})
        target = destination / name
        target.mkdir(exist_ok=True)
        (target / "METADATA.txt").write_text(dist.read_text("METADATA") or name, encoding="utf-8")
        for file in dist.files or []:
            if any(term in str(file).lower() for term in ("license", "copying", "notice")):
                source = Path(dist.locate_file(file))
                if source.is_file():
                    shutil.copy2(source, target / (str(file).replace("/", "_").replace("\\", "_")))
    (destination / "components.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def trim_linux_plugins(bundle):
    """Drop unused virtual keyboard/GTK theme, then only unreferenced native libraries."""
    if not sys.platform.startswith("linux") or not shutil.which("readelf"):
        return
    internal = bundle / "_internal"
    for name in ("libqtvirtualkeyboardplugin.so", "libqgtk3.so"):
        for plugin in internal.rglob(name):
            plugin.unlink()
    for prefixes in [("libQt6Quick", "libQt6Qml", "libQt6VirtualKeyboard"), ("libgtk-3.so",)]:
        candidates = [p for p in internal.rglob("*.so*") if p.name.startswith(prefixes)]
        names = {p.name for p in candidates}
        referenced = False
        for binary in internal.rglob("*.so*"):
            if binary in candidates or binary.is_symlink():
                continue
            result = subprocess.run(["readelf", "-d", str(binary)], capture_output=True, text=True)
            if any(f"[{name}]" in result.stdout for name in names):
                referenced = True
                break
        if not referenced:
            for candidate in candidates:
                candidate.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", action="store_true", help="Bez audio, magazynu kluczy i przechwytywania okna")
    args = parser.parse_args()
    variant = "core" if args.core else "full"
    name = "Licznik-Spotkaniowy"
    output = ROOT / "dist" / variant
    build = ROOT / "build" / variant
    build.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
    number = int(subprocess.check_output(["git", "rev-list", "--count", "HEAD"], cwd=ROOT, text=True).strip())
    version_file = build / "build_info.json"
    version_file.write_text(json.dumps({"commit": commit, "number": number, "dirty": dirty}), encoding="utf-8")
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed",
               "--name", name, "--distpath", str(output), "--workpath", str(build / "work"),
               "--specpath", str(build), "--collect-data", "meeting_timer",
               "--add-data", f"{ROOT / 'meeting_timer/assets'}:meeting_timer/assets"]
    command += ["--add-data", f"{version_file}:meeting_timer"]
    if sys.platform.startswith("linux") and shutil.which("strip"):
        command.append("--strip")
    for filename in ("README.md", "PRIVACY.md", "LICENSE", "TERMS.md", "THIRD_PARTY.md", "AGENTS.md", "ROADMAP.md"):
        command += ["--add-data", f"{ROOT / filename}:."]
    exclusions = ["tkinter", "matplotlib", "pandas", "scipy", "IPython", "PySide6.QtWebEngineCore",
                  "PySide6.QtWebEngineWidgets", "PySide6.QtQml", "PySide6.QtQuick"]
    if args.core:
        exclusions += ["soundcard", "numpy", "keyring", "PySide6.QtMultimedia"]
    else:
        for module in ("soundcard", "keyring", "PySide6.QtMultimedia"):
            if importlib.util.find_spec(module) is None:
                parser.error(f"Brak {module}. Uruchom: uv sync --extra dev --extra audio --extra keyring --extra capture")
        command += ["--collect-data", "soundcard", "--collect-submodules", "keyring.backends"]
        # PulseAudio loaded by CFFI, invisible to static import analysis.
        if sys.platform.startswith("linux"):
            from ctypes.util import find_library
            library = find_library("pulse")
            if not library:
                parser.error("Brak systemowej biblioteki libpulse.")
            listing = subprocess.check_output(["ldconfig", "-p"], text=True)
            candidates = [line.split("=>", 1)[1].strip() for line in listing.splitlines()
                          if library in line and "=>" in line]
            if candidates:
                command += ["--add-binary", f"{candidates[0]}:."]
    for module in exclusions:
        command += ["--exclude-module", module]
    if sys.platform == "darwin":
        command += ["--osx-bundle-identifier", "pl.licznik-spotkaniowy.desktop"]
    subprocess.run(command + [str(ROOT / "run.py")], cwd=ROOT, check=True)
    bundle = output / (name + ".app" if sys.platform == "darwin" else name)
    trim_linux_plugins(bundle)
    if sys.platform == "darwin":
        plist_path = bundle / "Contents/Info.plist"
        with plist_path.open("rb") as stream:
            plist = plistlib.load(stream)
        plist.update({"NSMicrophoneUsageDescription": "Nagrywanie spotkania po naciśnięciu Nagraj.",
                      "NSScreenCaptureUsageDescription": "Zapis zrzutów wybranego ekranu lub okna na żądanie użytkownika.",
                      "NSAudioCaptureUsageDescription": "Nagrywanie wybranego źródła dźwięku spotkania."})
        with plist_path.open("wb") as stream:
            plistlib.dump(plist, stream)
    docs = bundle / "Contents/Resources" if sys.platform == "darwin" else bundle
    # Only our Polish interface and optional Polish Qt standard dialog strings are needed.
    for translations in bundle.rglob("translations"):
        if translations.is_dir() and "PySide6" in str(translations):
            for translation in translations.glob("*.qm"):
                if translation.name not in ("qtbase_pl.qm", "qtbase_de.qm", "qtbase_fr.qm"):
                    translation.unlink()
    for filename in ("README.md", "PRIVACY.md", "LICENSE", "TERMS.md", "THIRD_PARTY.md", "AGENTS.md", "ROADMAP.md"):
        shutil.copy2(ROOT / filename, docs / filename)
    shutil.copytree(ROOT / "docs", docs / "docs", dirs_exist_ok=True)
    package_licenses(docs / "third-party-licenses", full=not args.core)
    shutil.copy2(ROOT / "meeting_timer/assets/Tabler-LICENSE.txt", docs / "third-party-licenses/Tabler-LICENSE.txt")
    shutil.copytree(ROOT / "licenses", docs / "third-party-licenses/upstream", dirs_exist_ok=True)
    if sys.platform == "darwin":
        subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(bundle)], check=True)
    archive_base = ROOT / "dist" / f"licznik-{platform.system().lower()}-{platform.machine().lower()}-{variant}"
    if os.name == "nt":
        archive = shutil.make_archive(str(archive_base), "zip", root_dir=output, base_dir=bundle.name)
    else:
        archive = str(archive_base) + ".tar.gz"
        with tarfile.open(archive, "w:gz", compresslevel=3) as stream:
            stream.add(bundle, arcname=bundle.name)
    size = sum(p.stat().st_size for p in bundle.rglob("*") if p.is_file() and not p.is_symlink())
    print(f"Paczka: {archive}\nRozpakowana: {size / 1024**2:.1f} MiB")


if __name__ == "__main__":
    main()
