# Image-to-Video on 8 GB VRAM (i7, 32 GB RAM, RTX 4070 Laptop)

## Honest verdict

| Engine | Will it run? | Time per video | Practical? |
|--------|-------------|----------------|------------|
| **SVD** (default) | Yes | ~2-5 min (14 frames, 18 steps) | **Yes — recommended** |
| **CogVideoX-5b-I2V** | Yes (fits ~5 GB) | ~20-30 min (49 frames) | Slow, not ideal for iteration |

**Recommendation:** Use **SVD** with reduced frames and steps for affordable generation time. CogVideoX produces higher quality but is 5-10x slower on 8 GB due to sequential CPU offload.

---

## 1. SVD (default) — recommended for 8 GB

- **Model:** `stabilityai/stable-video-diffusion-img2vid-xt` (~5 GB download)
- **Strategy:** Sequential CPU offload + `decode_chunk_size=2`. Auto-detected on 8 GB VRAM.
- **Tuning for speed:**

| Setting | Fast | Balanced | Quality |
|---------|------|----------|---------|
| `num_frames_video` | 5 | 14 | 25 |
| `num_inference_steps_video` | 14 | 18 | 25 |
| Approx time (8 GB, seq offload) | ~1-2 min | ~2-5 min | ~8-12 min |

**Recommended `.env` for 8 GB (SVD, balanced speed/quality):**

```env
video_engine=svd
model_path_video=stabilityai/stable-video-diffusion-img2vid-xt
num_frames_video=14
num_inference_steps_video=18
decode_chunk_size_video=2
fps_video=6
```

---

## 2. CogVideoX-5b-I2V — higher quality, much slower

- **Model:** `THUDM/CogVideoX-5b-I2V` (~20 GB download)
- **Strategy:** `enable_sequential_cpu_offload()` + `vae.enable_slicing()` + `vae.enable_tiling()` = ~5 GB VRAM.
- **Constraints:**
  - Frame count is fixed: **49 frames** (6 sec at 8 fps). Cannot use arbitrary values.
  - Input image is resized to **720x480** automatically.
  - Needs `diffusers>=0.30`. If unavailable, falls back to SVD.
  - `enable_model_cpu_offload()` needs ~19 GB and will OOM on 8 GB; the code uses sequential offload.
- **Real-world timing:**
  - RTX 4070 Super (12 GB): ~15 min per video (reported by users).
  - RTX 4070 Laptop (8 GB, sequential offload): **~20-30 min** per video (estimated).

**`.env` for CogVideoX (if you're okay with the wait):**

```env
video_engine=cogvideox
model_path_video=THUDM/CogVideoX-5b-I2V
num_frames_video=49
num_inference_steps_video=25
fps_video=8
```

**Install requirement:**

```bash
pip install "diffusers>=0.30.0"
```

---

## 3. Why not other models?

| Model | Why not |
|-------|---------|
| CogVideoX-2b | Text-to-video only, no I2V variant |
| Wan2.1 / LightX2V | Separate inference framework (not `diffusers`), not integrated in this backend |
| MobileI2V | Research code, not in `diffusers` |
| AnimateDiff | Text-to-video, not image-to-video |

---

## 4. Environment variable reference

| Variable | Default (SVD) | Default (CogVideoX) | Notes |
|----------|---------------|----------------------|-------|
| `video_engine` | `svd` | – | `svd` or `cogvideox` |
| `model_path_video` | `stabilityai/stable-video-diffusion-img2vid-xt` | `THUDM/CogVideoX-5b-I2V` | HF id or local path |
| `num_frames_video` | 25 | 49 | SVD: any; CogVideoX: 49 or 81 only |
| `num_inference_steps_video` | 20 | 20 | Fewer = faster, lower quality |
| `decode_chunk_size_video` | 8 | – | Use `2` on 8 GB (SVD only) |
| `fps_video` | 6 | 8 | Export FPS |
| `video_cpu_offload` | auto | auto | `1` = force offload |
| `cogvideox_guidance_scale_video` | – | 6.0 | CogVideoX prompt adherence |

---

## Bottom line

For your laptop (i7, 32 GB RAM, 8 GB RTX 4070): **use SVD with `num_frames_video=14`, `num_inference_steps_video=18`**. This gives ~2-5 min per video which is the best "affordable time" option available with current open-source models on 8 GB VRAM.
