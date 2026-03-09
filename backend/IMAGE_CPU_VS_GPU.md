# Image generation: CPU vs GPU comparison

ParleyAI’s `/api/image` (Stable Diffusion via diffusers) can run on **CPU** or **GPU** (CUDA). The backend chooses automatically: if PyTorch was installed with CUDA and a GPU is available, it uses the GPU; otherwise it falls back to CPU.

## Why use GPU?

| Metric | CPU | GPU (e.g. RTX 3060) | GPU (e.g. RTX 4090) |
|--------|-----|----------------------|----------------------|
| **Time per image** (512×512, ~25 steps) | **~30 s – 2+ min** | **~3–5 s** | **~1–2 s** |
| **8 scenes** (NarrateAI typical) | **~4–16 min** | **~25–40 s** | **~10–20 s** |
| **Practical for batch** | Slow, often impractical | Yes | Yes |

- CPU: one 512×512 image often takes **30 seconds to several minutes** depending on CPU and steps.
- GPU: same image on a mid-range GPU (e.g. RTX 3060) is **~3–5 seconds**; high-end (e.g. RTX 4090) **~1–2 seconds**.
- For **8 scenes**, that’s roughly **4–16 minutes on CPU** vs **under a minute on GPU**.

So GPU reduces latency by roughly **one order of magnitude** (often 8–10× or more) and makes multi-scene image generation practical.

## What the setup does

- **Windows:** Run **`setup_windows.bat`**. It installs base deps and `requirements-extra.txt`, then if **NVIDIA is detected** (`nvidia-smi`) it installs **PyTorch with CUDA** automatically (tries **cu128**, then **cu124**, then cu121). No manual pip step needed.
- **Linux/macOS:** Run **`./setup_fullstack.sh`**. It installs `requirements-extra.txt`, then if **NVIDIA is detected** it installs PyTorch with CUDA (cu128 → cu124 → cu121). On Mac (no NVIDIA) image gen uses CPU unless you use Metal builds separately.

**Why not CUDA 13.1?** PyTorch does not publish an official **cu131** wheel yet. The newest pip wheels are typically **cu128** (CUDA 12.8). Those builds work with your **CUDA 13.1 driver** (driver is backward compatible). When PyTorch adds cu131, the script can be updated to try it first.

- **Manual fix** (re-run setup or install manually)  
  If you already have the backend installed and see “Torch not compiled with CUDA” or image gen is very slow:

  Re-run the setup script, or in the backend venv: `pip install torch --index-url https://download.pytorch.org/whl/cu128` (or cu124 / cu121). Restart the backend after installing.

- **Forcing CPU**  
  Set `CUDA_VISIBLE_DEVICES=-1` (or `cuda_visible_devices_image=-1`) so the image runner uses CPU even when a GPU is available.

## References

- [PyTorch CUDA install](https://pytorch.org/get-started/locally/) — choose OS, pip, and CUDA version.
- [Stable Diffusion inference benchmarks (GPU)](https://www.tomshardware.com/pc-components/gpus/stable-diffusion-benchmarks) — GPU comparison.
- CPU vs GPU inference: GPUs are typically **~8–10× faster** for SD; the gap grows with batch size and resolution.
