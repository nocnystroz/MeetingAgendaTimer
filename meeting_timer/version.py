"""Commit identity for both a source checkout and a frozen portable build."""

import json
import subprocess
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def build_info():
    bundled = Path(__file__).parent / "build_info.json"
    if bundled.is_file():
        try:
            value = json.loads(bundled.read_text(encoding="utf-8"))
            if isinstance(value.get("commit"), str) and len(value["commit"]) >= 8:
                return value
        except (OSError, ValueError, AttributeError):
            pass
    root = Path(__file__).resolve().parents[1]
    try:
        commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                         stderr=subprocess.DEVNULL, text=True, timeout=2).strip()
        dirty = bool(subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"],
                                            stderr=subprocess.DEVNULL, text=True, timeout=2).strip())
        number = int(subprocess.check_output(["git", "-C", str(root), "rev-list", "--count", "HEAD"],
                                            stderr=subprocess.DEVNULL, text=True, timeout=2).strip())
        return {"commit": commit, "number": number, "dirty": dirty}
    except (OSError, subprocess.SubprocessError):
        return {"commit": "development", "dirty": False}


def version():
    value = build_info()
    return str(value.get("number", "dev")) + ("*" if value.get("dirty") else "")
