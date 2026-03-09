# Recommended local models (i7, 32GB RAM, 8GB RTX 4070)

Use these with ParleyAI for **story text**, **TTS (EN + HI)**, **images**, and **image-to-video**. Percentages are rough comparisons to well-known public/global models so you can correlate. **All paths and config work on Linux, Windows, and macOS** — the backend uses Python’s `os.path` and `pathlib`; use forward slashes or native paths (e.g. `C:\Models\model.gguf` on Windows).

---

## 1. Text — story writing (scary, cosmos, crime, mystery, satisfying, zero-to-hero, funny)

**Goal:** One local LLM that can handle all these genres well.

### Recommended (fits your hardware)

| Model | VRAM/RAM | vs GPT-4 (story quality) | Notes |
|-------|----------|--------------------------|--------|
| **L3-Grand-Story-Darkness-MOE-4X8-24.9B** (Q4_K_M) | ~14 GB → 8GB GPU + CPU or full CPU 32GB | **~95%** | **Best for story.** Llama3-based MoE (4×8B, ~8B active). Exceptional prose, horror, sci‑fi, mystery, vivid imagery; uncensored. Use `model_family_text=custom` and `model_path_text=/path/to/model.gguf`. [GGUF](https://huggingface.co/DavidAU/L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-GGUF) |
| **Qwen 2.5 32B Instruct** (Q4_K_M) | ~20–24 GB RAM (CPU offload) or partial GPU | **~82–88%** | Better creativity and genre variety; fits 32GB RAM with GPU layers for speed. |
| **Qwen 2.5 7B Instruct** (Q4_K_M or Q5_K_M) | ~6–8 GB VRAM or CPU + 32GB RAM | **~70–78%** | Best balance on 8GB if you skip the Grand-Story model. Strong instruction-following, good for structured scripts. |
| **Llama-3.2-4X3B-MOE-Ultra-Instruct** (10B, Q4_K_M) | ~6 GB | **~90%** | Max speed (35–50 tok/s), 128K context; story quality slightly below L3-Grand-Story. [GGUF](https://huggingface.co/DavidAU/Llama-3.2-4X3B-MOE-Ultra-Instruct-10B-GGUF) |
| **Mistral 7B / Mistral Small** (Q4_K_M / Q5_K_M) | ~6–8 GB | **~68–75%** | Good for mystery/crime; slightly behind Qwen 2.5 7B on average. |
| **Gemma 2 9B** (Q4_K_M) | ~7–8 GB | **~72–78%** | “Most natural-sounding prose”; good for emotional/satisfying arcs. |

**Rough scale (100% = GPT-4 level for your story tasks):**

- **GPT-4 / Claude (public):** 100% (reference).
- **L3-Grand-Story-Darkness-MOE-4X8:** **~95%** (ParleyAI’s top story pick).
- **Qwen 3 235B (if you had the VRAM):** ~95–98%.
- **Qwen 2.5 32B:** ~82–88%.
- **Llama-3.2-4X3B-MOE-Ultra:** ~90%.
- **Qwen 2.5 7B / Gemma 2 9B:** ~70–78%.
- **Llama 3.1 8B / Mistral 7B:** ~68–75%.

**Practical pick for you:** **L3-Grand-Story-Darkness-MOE-4X8-24.9B** (Q4_K_M) for best story quality — fits 8GB VRAM + 32GB RAM with partial GPU (~15–25 tok/s) or full CPU. In `.env` set:

```env
model_family_text=custom
model_path_text=/path/to/L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-D_AU-Q4_k_m.gguf
```

(See **Download paths** below for direct links and other quants.)  
If you prefer maximum speed or long context, use **Llama-3.2-4X3B-MOE-Ultra** or **Qwen 2.5 7B** instead.

**Laptop comparison (typical tok/s):** If you’re choosing among **LFM2 24B a2b Q8_0**, **Qwen2.4 32B Instruct Q5_K_M**, and **L3-Grand-Story-Darkness-MOE-4X8-24.9B Q5_K_M**:

| Model | Speed (typical) | Best for |
|-------|-----------------|-----------|
| **LFM2 24B Q8_0** | **13–16 tok/s** | **Best for story on a laptop** — fastest; Q8_0 keeps quality high. Use when you want short wait and many drafts. |
| **Qwen2.4 32B Q5_K_M** | 3–4 tok/s | Strong general instruct; good stories but not story-specialized. Middle option. |
| **L3-Grand-Story Q5_K_M** | 2–3 tok/s | **Best story prose** (horror, sci‑fi, mystery, vivid narrative); slowest. Use when quality matters more than speed. |

**Recommendation:** Default to **LFM2 24B Q8_0** for day-to-day story writing (speed + quality). Use **L3-Grand-Story** when you want maximum narrative quality and can wait longer (e.g. final pass or important scenes).

---

## 2. TTS — English + Hindi

**Goal:** Local or cloud TTS for both English and Hindi for shorts/reels.

### Options (laptop: i7 + 32GB + 8GB)

| Option | English | Hindi | vs “human-like” | Works in ParleyAI | Notes |
|--------|---------|--------|------------------|-------------------|--------|
| **Edge TTS (cloud)** | ✅ | ✅ | **~85–92%** | ✅ Yes (default) | No local model; free. Set `tts_engine=edge`. Use `voice_id_tts` or pass per request. |
| **Piper (local)** | ✅ | ✅ | **~72–82%** | ✅ Yes | One `.onnx` per voice; CPU. EN: e.g. `en_US-lessac-medium`. HI: `hi_IN-priyamvada-medium`, `hi_IN-rohan-medium`, `hi_IN-pratham-medium`. |
| **Coqui XTTS v2 (local)** | ✅ | ✅ | **~80–88%** | ❌ Not yet | Best local EN+HI; would need XTTS runner in backend. |

**Edge TTS voice IDs (set `voice_id_tts` in `.env` or pass in request):**

- **English (US):** `en-US-JennyNeural`, `en-US-GuyNeural`, `en-US-AriaNeural`, `en-US-ChristopherNeural`
- **English (India):** `en-IN-NeerjaNeural`, `en-IN-PrabhatNeural`
- **Hindi:** `hi-IN-MadhurNeural`, `hi-IN-SwaraNeural`, `hi-IN-HilaNeural`

(Backend uses `en-US-JennyNeural` by default and `en-IN-NeerjaNeural` when `language` starts with `hi`; override with `voice_id_tts`.)

**Piper (fully local) — download one voice per language:**

- **English:** [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) → `en/en_US/lessac/medium` → `en_US-lessac-medium.onnx` (+ `.onnx.json`)
- **Hindi:** [rhasspy/piper-voices hi_IN](https://huggingface.co/rhasspy/piper-voices/tree/main/hi/hi_IN) → e.g. `priyamvada/medium` → `hi_IN-priyamvada-medium.onnx` (+ `.onnx.json`)

**Rough scale (100% = premium human-like TTS):**

- **Commercial (ElevenLabs, Azure Neural):** ~92–98%.
- **Edge TTS:** ~85–92%.
- **Coqui XTTS v2:** ~80–88%.
- **Piper (EN + HI):** ~72–82%.

**Practical pick for your laptop:**

- **Easiest (no download):** **Edge TTS** — `tts_engine=edge`, `voice_id_tts=en-US-JennyNeural` (or `hi-IN-MadhurNeural` for Hindi). Already in ParleyAI.
- **Fully local:** **Piper** — `tts_engine=piper`, `model_path_tts=/path/to/en_US-lessac-medium.onnx` (or a Hindi `.onnx`). For two languages use two voice files and switch `model_path_tts` / or call with different config per request if your client supports it.

---

## 3. Images — scary, cosmos, crime, mystery, satisfying, zero-to-hero, funny

**Goal:** One model that can do all these styles well on 8GB VRAM.

### Recommended (8GB VRAM laptop)

| Model | VRAM | vs DALL·E 3 / Midjourney | Works in ParleyAI today | Notes |
|-------|------|---------------------------|--------------------------|--------|
| **SD 1.5** (runwayml/stable-diffusion-v1-5) | ~4–6 GB | **~58–68%** | ✅ Yes (default pipeline) | Fast, light. Good for scary, cosmos, crime, mystery with strong prompts. Default in ParleyAI. |
| **SDXL 1.0** (stabilityai/stable-diffusion-xl-base-1.0) | ~6–8 GB | **~70–78%** vs DALL·E 3, **~65–74%** vs MJ | ⚠️ Needs XL pipeline | Better quality; 8GB with 512–768 res + attention slicing. |
| **FLUX.1 Schnell** (black-forest-labs/FLUX.1-schnell) | ~8 GB (with CPU offload) | **~78–85%** vs DALL·E 3, **~72–80%** vs MJ | ⚠️ Needs Flux pipeline | Best 8GB quality; 4 steps; diffusers uses `FluxPipeline` + `enable_model_cpu_offload()`. |

**Rough scale (100% = DALL·E 3 / Midjourney):**

- **Midjourney v6/v7:** 100% (aesthetic). **DALL·E 3:** 100% (prompt adherence).
- **FLUX.1 Schnell:** ~78–85% (DALL·E 3), ~72–80% (MJ).
- **SDXL:** ~70–78% (DALL·E 3), ~65–74% (MJ).
- **SD 1.5:** ~58–68%.

**Practical pick for your laptop:**

- **Works today, no code change:** **SD 1.5** — set `model_path_image=runwayml/stable-diffusion-v1-5` (or local path). Covers scary, cosmos, crime, mystery, satisfying, funny with good prompts. ~58–68% vs DALL·E 3.
- **Better quality when supported:** **SDXL** or **FLUX.1 Schnell** — ParleyAI’s image runner currently uses `StableDiffusionPipeline` (SD 1.5 only). SDXL needs `StableDiffusionXLPipeline`; Flux needs `FluxPipeline` + CPU offload for 8GB. Until then, SD 1.5 is the default that runs out of the box.

**.env (SD 1.5, works now):**
```env
model_path_image=runwayml/stable-diffusion-v1-5
width_image=512
height_image=512
steps_image=25
```

---

## 4. Image-to-video — put life into images, hook viewers, more views

**Goal:** Local model that adds motion to your generated images for shorts/reels.

### Recommended (8GB VRAM laptop)

| Model | VRAM | vs Runway/Kling-style I2V | Works in ParleyAI | Notes |
|-------|------|----------------------------|-------------------|--------|
| **Stable Video Diffusion (SVD) XT** | ~8 GB (with chunking) | **~70–78%** | ✅ Yes | 25 frames, 576×1024. Use `decode_chunk_size_video=2` on 8GB. |
| **SVD (14-frame)** | ~6–8 GB | **~65–72%** | ✅ Yes (same pipeline, fewer frames) | Lighter; set `num_frames_video=14`. |

**Rough scale (100% = Runway Gen-3 / Kling):**

- **Runway Gen-3 / Kling:** 100%.
- **SVD XT (local, 8GB):** ~70–78%.
- **SVD 14-frame:** ~65–72%.

**Practical pick for your laptop:** **Stable Video Diffusion img2vid-xt** — supported out of the box. For 8GB set `decode_chunk_size_video=2` so frames decode in smaller chunks and stay within VRAM.

**.env (SVD XT on 8GB):**
```env
model_path_video=stabilityai/stable-video-diffusion-img2vid-xt
num_frames_video=25
fps_video=6
decode_chunk_size_video=2
motion_bucket_id_video=127
noise_aug_strength_video=0.02
```

---

## 5. Summary table (your laptop: i7 + 32GB RAM + 8GB RTX 4070)

| Slot | Recommended model | Approx. vs “global best” | Works in ParleyAI today |
|------|-------------------|--------------------------|--------------------------|
| **Text (story)** | **L3-Grand-Story-Darkness-MOE-4X8-24.9B** (custom) | **~95%** of GPT-4 | ✅ `model_family_text=custom`, `model_path_text=/path/to/model.gguf` |
| **TTS** | Edge TTS (EN+HI) or Piper (EN+HI) | **~72–92%** of premium TTS | ✅ Edge default; Piper with `model_path_tts` to `.onnx` |
| **Image** | SD 1.5 (runwayml/stable-diffusion-v1-5) | **~58–68%** of DALL·E 3 / MJ | ✅ Default pipeline. SDXL/Flux need pipeline support. |
| **Video (I2V)** | SVD XT (img2vid-xt), `decode_chunk_size_video=2` | **~70–78%** of Runway/Kling | ✅ `model_path_video=stabilityai/stable-video-diffusion-img2vid-xt` |

All of these can run on your laptop with the current ParleyAI config (lazy load, serial image/video, idle unload). Use `MODELS_AND_CONFIG.md` and `.env.example` for full parameters.

---

## 6. Download paths and quantization

Direct links and recommended quants for each slot. Use **resolve** URLs to download the file; or clone the repo and point `model_path_*` to the local file.

### Text (GGUF) — L3-Grand-Story-Darkness-MOE-4X8-24.9B

Repo: [DavidAU/L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-GGUF](https://huggingface.co/DavidAU/L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-GGUF)

| Quantization | Filename | Size (approx) | Use case |
|--------------|----------|----------------|----------|
| **Q4_K_M** (recommended) | `L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-D_AU-Q4_k_m.gguf` | ~15 GB | Best balance quality/speed for 8GB GPU + RAM |
| Q5_K_M | `L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-D_AU-q5_k_m.gguf` | ~18 GB | Higher quality, more VRAM/RAM |
| Q4_K_S | `L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-D_AU-Q4_k_s.gguf` | ~14.5 GB | Slightly smaller |
| Q3_K_M | `L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-D_AU-Q3_k_m.gguf` | ~12 GB | Fits tighter RAM |
| IQ4_XS | `L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-D_AU-IQ4_XS.gguf` | ~14 GB | Alternative 4-bit |

**Direct download (Q4_K_M):**
```
https://huggingface.co/DavidAU/L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-GGUF/resolve/main/L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-D_AU-Q4_k_m.gguf
```

Or: `huggingface-cli download DavidAU/L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-GGUF L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-D_AU-Q4_k_m.gguf --local-dir ./models`

### TTS (Piper) — English and Hindi

One `.onnx` (+ `.onnx.json`) per voice. Set `model_path_tts` to the **.onnx** path.

**English (en_US-lessac-medium):**
- `https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx`
- `https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json`

**Hindi — Priyamvada (medium):**
- `https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/priyamvada/medium/hi_IN-priyamvada-medium.onnx`
- `https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/priyamvada/medium/hi_IN-priyamvada-medium.onnx.json`

**Hindi — Rohan (medium):** [hi_IN/rohan/medium](https://huggingface.co/rhasspy/piper-voices/tree/main/hi/hi_IN/rohan/medium) — `hi_IN-rohan-medium.onnx` (+ `.onnx.json`)  
**Hindi — Pratham (medium):** [hi_IN/pratham/medium](https://huggingface.co/rhasspy/piper-voices/tree/main/hi/hi_IN/pratham/medium) — `hi_IN-pratham-medium.onnx` (+ `.onnx.json`)

### Image — SD 1.5 (diffusers)

- **Model ID:** `runwayml/stable-diffusion-v1-5`  
- **Repo:** [runwayml/stable-diffusion-v1-5](https://huggingface.co/runwayml/stable-diffusion-v1-5)  
- Pre-download: `huggingface-cli download runwayml/stable-diffusion-v1-5 --local-dir ./models/stable-diffusion-v1-5` then `model_path_image=./models/stable-diffusion-v1-5`

### Video — SVD img2vid-xt (diffusers)

- **Model ID:** `stabilityai/stable-video-diffusion-img2vid-xt`  
- **Repo:** [stabilityai/stable-video-diffusion-img2vid-xt](https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt)  
- Pre-download: `huggingface-cli download stabilityai/stable-video-diffusion-img2vid-xt --local-dir ./models/stable-video-diffusion-img2vid-xt` then `model_path_video=./models/stable-video-diffusion-img2vid-xt`

---

### Laptop quick .env (copy-paste base)

```env
# Text (best story quality) — use path to downloaded Q4_K_M GGUF (see Download paths above)
model_family_text=custom
model_path_text=/path/to/L3-Grand-Story-Darkness-MOE-4X8-24.9B-e32-D_AU-Q4_k_m.gguf

# TTS: Edge (no download) or Piper (local)
tts_engine=edge
voice_id_tts=en-US-JennyNeural
# model_path_tts=/path/to/en_US-lessac-medium.onnx

# Image (works with default runner)
model_path_image=runwayml/stable-diffusion-v1-5
width_image=512
height_image=512
steps_image=25

# Video (8GB: use chunk size 2)
model_path_video=stabilityai/stable-video-diffusion-img2vid-xt
decode_chunk_size_video=2
num_frames_video=25
fps_video=6
```
