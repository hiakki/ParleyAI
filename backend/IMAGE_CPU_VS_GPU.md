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

- **`setup_windows.bat`**  
  - Installs base dependencies and `requirements-extra.txt` (which includes CPU-only PyTorch by default).  
  - If **NVIDIA is detected** (`nvidia-smi` works), it then installs **PyTorch with CUDA** from the official index (`cu124` or `cu121`), so image generation uses the GPU.

- **Manual fix if you already ran setup**  
  If you already have the backend installed and see “Torch not compiled with CUDA” or image gen is very slow:

  ```bat
  cd backend
  venv\Scripts\activate
  pip install torch --index-url https://download.pytorch.org/whl/cu124
  ```

  Replace `cu124` with `cu121` if you have CUDA 12.1. Restart the backend after installing.

- **Forcing CPU**  
  Set `CUDA_VISIBLE_DEVICES=-1` (or `cuda_visible_devices_image=-1`) so the image runner uses CPU even when a GPU is available.

## References

- [PyTorch CUDA install](https://pytorch.org/get-started/locally/) — choose OS, pip, and CUDA version.
- [Stable Diffusion inference benchmarks (GPU)](https://www.tomshardware.com/pc-components/gpus/stable-diffusion-benchmarks) — GPU comparison.
- CPU vs GPU inference: GPUs are typically **~8–10× faster** for SD; the gap grows with batch size and resolution.
