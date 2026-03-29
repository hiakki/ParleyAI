#!/usr/bin/env python3
"""
ParleyAI backend — single script to run everything.

From backend folder:
  python run.py

From repo root:
  python backend/run.py

This script:
  1. Ensures a virtual environment exists (creates venv if missing)
  2. Installs dependencies from requirements.txt (and optionally requirements-extra.txt)
  3. Starts the server (loads .env, runs uvicorn)

Works on Windows, Linux, and macOS.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

def main() -> int:
    backend_dir = Path(__file__).resolve().parent
    os.chdir(backend_dir)

    venv_dir = backend_dir / "venv"
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
        venv_pip = venv_dir / "Scripts" / "pip.exe"
    else:
        venv_python = venv_dir / "bin" / "python"
        venv_pip = venv_dir / "bin" / "pip"

    # 1. Create venv if missing or incomplete (empty dir, wrong OS copy, etc.)
    if not venv_dir.is_dir():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        print("Done.")
    elif not venv_python.exists():
        print(f"venv/ exists but is incomplete (no {venv_python.name}). Recreating...")
        shutil.rmtree(venv_dir)
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        print("Done.")

    if not venv_python.exists():
        print(f"Error: venv Python not found at {venv_python}")
        return 1

    # 2. Install dependencies
    req_txt = backend_dir / "requirements.txt"
    if req_txt.exists():
        print("Installing dependencies from requirements.txt...")
        subprocess.run(
            [str(venv_pip), "install", "-q", "-r", str(req_txt)],
            check=True,
            cwd=backend_dir,
        )
        print("Done.")

    req_extra = backend_dir / "requirements-extra.txt"
    if req_extra.exists():
        print("Installing optional dependencies from requirements-extra.txt...")
        subprocess.run(
            [str(venv_pip), "install", "-q", "-r", str(req_extra)],
            check=True,
            cwd=backend_dir,
        )
        print("Done.")

    # 3. Run server (loads .env via server.py and runs uvicorn)
    print("Starting ParleyAI backend server...")
    return subprocess.run(
        [str(venv_python), "server.py"],
        cwd=backend_dir,
    ).returncode


if __name__ == "__main__":
    sys.exit(main())
