#!/bin/bash
# Download llama-server from ggml-org/llama.cpp releases into ./llama-cpp/
# Required for server-based text models (Qwen, LFM2, Mistral, custom, arbitrary family names).
# Safe to re-run — skips if llama-server is already on PATH or in llama-cpp/.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
TARGET_DIR="$REPO_ROOT/llama-cpp"
mkdir -p "$TARGET_DIR"

if command -v llama-server &>/dev/null; then
    echo "   ✓ llama-server already on PATH: $(command -v llama-server)"
    exit 0
fi
if [ -x "$TARGET_DIR/llama-server" ]; then
    echo "   ✓ llama-server already at $TARGET_DIR/llama-server"
    exit 0
fi

echo "   Downloading llama-server (ggml-org/llama.cpp latest release)..."

export REPO_ROOT="$REPO_ROOT"

python3 << 'PY'
import json
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request

repo_root = os.environ["REPO_ROOT"]
target_dir = os.path.join(repo_root, "llama-cpp")
os.makedirs(target_dir, exist_ok=True)

api = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
req = urllib.request.Request(api, headers={"User-Agent": "ParleyAI-Setup"})
with urllib.request.urlopen(req, timeout=120) as r:
    release = json.load(r)

assets = release.get("assets") or []
names_urls = {a["name"]: a["browser_download_url"] for a in assets}

import platform

sysname = platform.system()
machine = platform.machine().lower()

candidates = []
if sysname == "Linux":
    if machine in ("x86_64", "amd64"):
        # Prebuilt for Ubuntu/glibc — works on most Debian/Ubuntu server images
        candidates = [n for n in names_urls if n.endswith("bin-ubuntu-x64.tar.gz")]
    elif machine in ("aarch64", "arm64"):
        candidates = [n for n in names_urls if "openEuler-aarch64" in n and n.endswith(".tar.gz")]
elif sysname == "Darwin":
    if machine == "arm64":
        candidates = [n for n in names_urls if "bin-macos-arm64.tar.gz" in n]
    else:
        candidates = [n for n in names_urls if "bin-macos-x64.tar.gz" in n]

if not candidates:
    print("ERROR: No matching llama.cpp binary for this OS/arch in the latest release.", file=sys.stderr)
    print(f"  system={sysname} machine={machine}", file=sys.stderr)
    print("  Build from source: https://github.com/ggml-org/llama.cpp", file=sys.stderr)
    sys.exit(1)

# Prefer highest build id if multiple (sort by name descending)
candidates.sort(reverse=True)
asset_name = candidates[0]
url = names_urls[asset_name]
print(f"   Using asset: {asset_name}")

fd, tmp_path = tempfile.mkstemp(suffix=".tar.gz")
os.close(fd)
try:
    print("   Fetching archive...")
    urllib.request.urlretrieve(url, tmp_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        with tarfile.open(tmp_path, "r:*") as tf:
            try:
                tf.extractall(tmpdir, filter="data")
            except TypeError:
                tf.extractall(tmpdir)

        found = None
        for root, _, files in os.walk(tmpdir):
            if "llama-server" in files:
                p = os.path.join(root, "llama-server")
                if os.path.isfile(p):
                    found = p
                    break
        if not found:
            print("ERROR: llama-server not found inside archive.", file=sys.stderr)
            sys.exit(1)

        dest = os.path.join(target_dir, "llama-server")
        shutil.copy2(found, dest)
        os.chmod(dest, 0o755)
        print(f"   ✓ Installed: {dest}")
finally:
    try:
        os.remove(tmp_path)
    except OSError:
        pass
PY
