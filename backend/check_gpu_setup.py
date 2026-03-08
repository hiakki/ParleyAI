#!/usr/bin/env python3
"""
ParleyAI — GPU setup verification script

Run from repo root:   python backend/check_gpu_setup.py
Run from backend:     python check_gpu_setup.py

Or with venv:         backend/venv/Scripts/python backend/check_gpu_setup.py  (Windows)
                      backend/venv/bin/python backend/check_gpu_setup.py       (Linux/macOS)

This script:
  1. Loads backend/.env and prints text-model config (family, gpu_layers, path).
  2. Detects whether you use llama-server (subprocess) or in-process llama-cpp-python.
  3. If llama-server: checks whether the binary is likely CUDA (Windows).
  4. Runs a minimal inference and, if nvidia-smi is available, reports whether GPU memory increased.
  5. Prints clear next steps if GPU is not used.

For accurate GPU check, run with the backend stopped (so this script loads the model and we can measure).
If the backend is already running, the script will send one request to it and then check nvidia-smi.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

def _backend_dir() -> Path:
    return Path(__file__).resolve().parent

def _load_env():
    backend_dir = _backend_dir()
    os.chdir(backend_dir)
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    env_file = backend_dir / ".env"
    if env_file.exists():
        try:
            import dotenv
            dotenv.load_dotenv(env_file)
        except ImportError:
            pass
    return backend_dir

def _get_nvidia_smi_memory_mb() -> int | None:
    """Return current GPU memory used in MiB, or None if nvidia-smi not available."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode != 0 or not out.stdout.strip():
            return None
        # First GPU only; value may be "1234 MiB" or "1234"
        line = out.stdout.strip().split("\n")[0].strip()
        m = re.search(r"(\d+)", line)
        return int(m.group(1)) if m else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

def _check_llama_server_cuda(bin_path: str) -> tuple[bool, str]:
    """Run llama-server -h and look for CUDA in output. Return (found_cuda, message)."""
    try:
        proc = subprocess.run(
            [bin_path, "-h"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        out_lower = out.lower()
        if "cuda" in out_lower:
            return True, "llama-server help mentions CUDA — likely GPU build."
        # Path-based heuristic (Windows: often in folder named cuda)
        if "cuda" in bin_path.lower():
            return True, "llama-server path contains 'cuda' — likely GPU build."
        return False, "llama-server help/path does not mention CUDA. You may have the CPU/Vulkan build; use the CUDA build for NVIDIA GPU."
    except Exception as e:
        return False, f"Could not run llama-server: {e}"

def main() -> int:
    backend_dir = _load_env()
    print("=" * 60)
    print("ParleyAI — GPU setup check")
    print("=" * 60)

    # Import after env is loaded so server sees .env
    try:
        from server import (
            MODEL_PATH,
            MODEL_FAMILY,
            GPU_LAYERS,
            GPU_LAYERS_SOURCE,
            get_transformer,
            ENABLE_TEXT,
        )
        from llama_transformer import MODEL_FAMILIES, LlamaServerTransformer
    except ImportError as e:
        print(f"Import error: {e}")
        print("Run from repo root: python backend/check_gpu_setup.py")
        print("Or from backend with venv: python check_gpu_setup.py")
        return 1

    if not ENABLE_TEXT:
        print("enable_text=0 — text model is disabled. Enable it in .env to test GPU.")
        return 0

    if not MODEL_PATH or not Path(MODEL_PATH).exists():
        print(f"Model path not set or missing: {MODEL_PATH}")
        print("Set model_path_text (and model_family_text if needed) in backend/.env")
        return 1

    family_info = MODEL_FAMILIES.get(MODEL_FAMILY, {})
    use_server = family_info.get("use_server", False)
    backend_name = "llama-server (subprocess)" if use_server else "llama-cpp-python (in-process)"

    print(f"\nConfig (from .env):")
    print(f"  model_family_text  = {MODEL_FAMILY}")
    print(f"  gpu_layers_text    = {GPU_LAYERS} (source: {GPU_LAYERS_SOURCE})")
    print(f"  model_path_text    = {MODEL_PATH}")
    print(f"  Text backend       = {backend_name}")

    if use_server:
        # Resolve llama-server binary (same logic as LlamaServerTransformer)
        env_path = os.getenv("LLAMA_SERVER_PATH", "").strip()
        if env_path:
            bin_path = Path(os.path.expanduser(env_path))
        else:
            import shutil
            found = shutil.which("llama-server") or shutil.which("llama-server.exe")
            if found:
                bin_path = Path(found)
            else:
                candidates = [
                    backend_dir.parent / "llama-cpp" / "llama-server.exe",
                    backend_dir.parent / "llama-cpp" / "llama-server",
                    backend_dir.parent / "llama-server.exe",
                    backend_dir / "bin" / "llama-server.exe",
                ]
                bin_path = None
                for c in candidates:
                    if c.exists() and c.is_file():
                        bin_path = c
                        break
                if bin_path is None:
                    bin_path = Path("(not found)")

        if isinstance(bin_path, Path) and bin_path.exists():
            cuda_ok, cuda_msg = _check_llama_server_cuda(str(bin_path))
            print(f"  llama-server       = {bin_path}")
            print(f"  CUDA build         = {cuda_msg}")
            if not cuda_ok and GPU_LAYERS > 0:
                print("\n  >>> For GPU use on Windows, install the CUDA build from:")
                print("      https://github.com/ggml-org/llama.cpp/releases")
                print("      e.g. llama-b*-bin-win-cuda-13.1-x64.zip")
        else:
            print(f"  llama-server       = not found (set LLAMA_SERVER_PATH or use setup script)")
    else:
        print("  (In-process: GPU requires llama-cpp-python built with CUDA/Metal)")

    # nvidia-smi available?
    nvidia_ok = _get_nvidia_smi_memory_mb() is not None
    if nvidia_ok:
        print("\nnvidia-smi: found — will measure GPU memory before/after inference.")
    else:
        print("\nnvidia-smi: not in PATH — cannot measure GPU automatically. Watch Task Manager or run 'nvidia-smi -l 1' in another terminal.")

    print("\n" + "-" * 60)
    print("Running one short inference (max 5 tokens)...")
    print("(If the backend server is already running, we'll use it; otherwise we load the model here.)")
    print("-" * 60)

    mem_before = _get_nvidia_smi_memory_mb()

    try:
        # Prefer hitting running server so we don't load model twice
        import urllib.request
        import urllib.error
        import json
        used_server = False
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:8000/v1/chat/completions",
                data=json.dumps({
                    "model": family_info.get("name", MODEL_FAMILY),
                    "messages": [{"role": "user", "content": "Say OK in one word."}],
                    "max_tokens": 5,
                    "stream": False,
                }).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"  Response (from running server): {reply!r}")
            used_server = True
        except (urllib.error.URLError, OSError, Exception):
            pass

        if not used_server:
            print("  (Backend not running — loading model in-process for this script...)")
            trans = get_transformer(
                model_path=MODEL_PATH,
                model_family=MODEL_FAMILY,
                quantization=os.getenv("quant_text") or os.getenv("QUANT", "Q4_K_M"),
                n_ctx=int(os.getenv("ctx_text") or os.getenv("CTX", "2048")),
                n_gpu_layers=GPU_LAYERS,
                n_batch=int(os.getenv("batch_size_text") or os.getenv("BATCH_SIZE", "512")),
            )
            reply = trans.chat(
                [{"role": "user", "content": "Say OK in one word."}],
                max_tokens=5,
                stream=False,
            )
            print(f"  Response: {reply!r}")
            if isinstance(trans, LlamaServerTransformer):
                trans.shutdown()
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    time.sleep(0.5)
    mem_after = _get_nvidia_smi_memory_mb()

    print()
    if nvidia_ok and mem_before is not None and mem_after is not None:
        delta = mem_after - mem_before
        if delta > 50:
            print("Result: GPU memory increased by ~{} MiB — GPU is in use.".format(delta))
        elif mem_after > 100:
            print("Result: GPU memory is {} MiB (change from before: {} MiB). If you see no spike, the text backend may be CPU-only.".format(mem_after, delta))
        else:
            print("Result: No significant GPU memory use detected. Likely CPU-only backend (llama-server non-CUDA build or llama-cpp-python without CUDA).")
    else:
        print("Result: Check Task Manager (Performance → GPU) or run 'nvidia-smi -l 1' during inference to confirm GPU use.")

    print()
    print("Summary:")
    print("  - gpu_layers_text is read from .env and passed to the backend.")
    print("  - GPU is only used if the binary is GPU-capable (CUDA build of llama-server, or llama-cpp-python built with CUDA).")
    print("  - If you still see no GPU: replace llama-server with the CUDA build, or reinstall llama-cpp-python with CUDA.")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
