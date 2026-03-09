# ParleyAI — Models and config (all in `backend/.env`)

Copy `backend/.env.example` to `backend/.env` and set paths to your **downloaded** models. **Single command to run the backend:** from repo root `python backend/run.py`, or from `backend/` run `python run.py` (creates venv, installs deps, starts server). The backend loads `.env` on startup; every model and param is configurable there. **Works on Linux, Windows, and macOS** — use forward slashes or OS-native paths (e.g. `C:\Models\...` on Windows; Python accepts both). For **which models to use** (text, TTS, image, video) and **% comparison vs global models**, see **`MODEL_RECOMMENDATIONS.md`**.

---

## 1. Text / LLM (story, chat)

| Variable | Example | Meaning |
|----------|---------|--------|
| `model_path_text` | `/path/to/local-llms` or `/path/to/model.gguf` | Path to GGUF file or directory. If directory, resolution uses `model_family_text` + `quant_text`. |
| `model_family_text` | `Qwen2.5-32B-Instruct` | Family when `model_path_text` is a directory (same as `MODEL_FAMILY`). |
| `quant_text` | `Q5_K_M` | Quant when `model_path_text` is a directory. |
| `ctx_text` | `4096` | Context window (tokens). Must be ≥ prompt + max_tokens; story API uses max_tokens=4096, so use 4096 for 30–90 sec stories (many scenes). 2048 can truncate. |
| `gpu_layers_text` | `-1` | GPU layers (-1 = auto). |
| `batch_size_text` | `512` | Batch size. |

**Path resolution when `model_path_text` is a directory:**  
`{model_path_text}/{model_family_text}/{quant_text}/` → then `{model_path_text}/{model_family_text}/` → then `{model_path_text}/` (first matching `.gguf`).

**Legacy (still supported):** `MODEL_PATH`, `MODEL_FAMILY`, `QUANT`, `CTX`, `GPU_LAYERS`, `BATCH_SIZE`.

---

## 2. TTS

| Variable | Example | Meaning |
|----------|---------|--------|
| `tts_engine` | `edge` or `piper` | `edge` = no local file. `piper` = use local Piper voice. |
| `model_path_tts` | `/path/to/voice.onnx` | Path to Piper `.onnx` voice file (required if `tts_engine=piper`). |
| `voice_id_tts` | `en_US-lessac-medium` | Voice name (Piper / edge). |

**Legacy:** `TTS_ENGINE`, `PIPER_VOICE_PATH`, `PIPER_VOICE`.

---

## 3. Image (text-to-image)

| Variable | Example | Meaning |
|----------|---------|--------|
| `model_path_image` | `/path/to/stable-diffusion-v1-5` or `runwayml/stable-diffusion-v1-5` | Local path to diffusers model dir, or Hugging Face model id. |
| `width_image` | `512` | Default image width. |
| `height_image` | `512` | Default image height. |
| `steps_image` | `25` | Inference steps. |
| `cuda_visible_devices_image` | (empty) or `-1` | Set to `-1` to force CPU for image. |

For **CPU vs GPU speed comparison** and how to install PyTorch with CUDA so image gen uses the GPU, see **IMAGE_CPU_VS_GPU.md**.

**Legacy:** `IMAGE_MODEL_ID`, `CUDA_VISIBLE_DEVICES`.

---

## 4. Video (image-to-video)

| Variable | Example | Meaning |
|----------|---------|--------|
| `model_path_video` | `/path/to/stable-video-diffusion-img2vid-xt` or HF id | Local path to SVD model dir, or Hugging Face model id. |
| `num_frames_video` | `25` | Frames per clip. |
| `fps_video` | `6` | FPS for output. |
| `decode_chunk_size_video` | `8` | Decode chunk size. |
| `motion_bucket_id_video` | `127` | Motion bucket id. |
| `noise_aug_strength_video` | `0.02` | Noise augmentation. |
| `cuda_visible_devices_video` | (empty) or `-1` | Set to `-1` to force CPU for video. |

On **8 GB VRAM**, the video runner auto-enables CPU offload and uses `decode_chunk_size` ≤ 2 so SVD runs without OOM. Optional: `video_cpu_offload=1` to force offload.

For **direct download links** and where to put the SVD files, see **SVD_VIDEO_MODEL_DOWNLOAD.md**.

**Legacy:** `VIDEO_MODEL_ID`, `CUDA_VISIBLE_DEVICES`.

---

## 4b. Where image/video models are downloaded (setup script & first use)

When you run the setup script’s “Pre-download” step (or when `/api/image` or `/api/video` download models on first use), files go to the **Hugging Face cache**.

| Platform | Default cache directory |
|----------|-------------------------|
| **Windows** | `C:\Users\<YourUser>\.cache\huggingface\hub` |
| **Linux/macOS** | `~/.cache/huggingface/hub` |

Inside that folder you’ll see entries like `models--runwayml--stable-diffusion-v1-5` and `models--stabilityai--stable-video-diffusion-img2vid-xt`. The setup script prints the actual path before asking “Pre-download now?”.

**To use a different folder:** set **`HF_HOME`** (or **`HF_HUB_CACHE`**) *before* running the setup script or the backend:

- **Windows (CMD):** `set HF_HOME=D:\HFcache`
- **Windows (PowerShell):** `$env:HF_HOME='D:\HFcache'`
- **Linux/macOS:** `export HF_HOME=~/HFcache`

Then run `setup_windows.bat` or `./setup_fullstack.sh`. All Hugging Face downloads (image + video models) will use that directory. The backend uses the same cache when loading by model ID (e.g. `runwayml/stable-diffusion-v1-5`).

**Pre-download options:** set **`PRELOAD_MODELS`** before running setup to skip the menu: **`n`** = skip both; **`image`** = image only (~5 GB); **`video`** = video only (~20 GB); **`y`** or **`1`** = both (~25 GB). If unset, the script shows: 1 = Image only, 2 = Video only, 3 = Both, 4 = Skip.

---

## 5. Shared / server

| Variable | Example | Meaning |
|----------|---------|--------|
| `enable_text` | `1` | Enable text/LLM (chat, story, /v1). `0` = disable. |
| `enable_tts` | `1` | Enable TTS. `0` = disable. |
| `enable_image` | `1` | Enable image model. `0` = disable. |
| `enable_video` | `1` | Enable video model. `0` = disable. |
| `gpu_unload_after_idle_sec` | `30` | Unload image or video from GPU after N seconds idle (0 = keep loaded). |
| `LFM_IDLE_TIMEOUT` | `300` | When using **llama-server** (LFM2, Qwen, Mistral, custom): stop the subprocess after N seconds with no text/chat requests to free RAM/VRAM. `0` = never auto-stop. Only applies when text backend is llama-server. |
| `gpu_allow_image_and_video_concurrent` | `0` | `1` = allow image and video loaded at same time (needs enough VRAM). `0` = only one at a time. |
| `text_lazy_load` | `1` | `1` = load text/LLM on first chat request (saves RAM/VRAM until needed). `0` = load at startup. |
| `port` | `8000` | Backend server port. |

**Legacy:** `GPU_UNLOAD_AFTER_IDLE_SEC`, `PORT`.

You can run **any combination** of models: set only the ones you want (e.g. `enable_text=1`, `enable_tts=1`, `enable_image=0`, `enable_video=0` for text + TTS only). Disabled routes return 503.

---

## Recommended for i7 + 32GB RAM + 8GB VRAM (e.g. RTX 4070)

Run **all four** models; resources are used **only when that model is asked**, otherwise stay idle:

- **`text_lazy_load=1`** — Text/LLM loads on first chat/story request, not at startup. Saves RAM/VRAM until you use chat.
- **`gpu_allow_image_and_video_concurrent=0`** — Only one of image or video on GPU at a time. Use this for 8GB VRAM.
- **`gpu_unload_after_idle_sec=30`** — After 30s without image (or video) requests, that model unloads from GPU so the other can load when you call it.
- **`LFM_IDLE_TIMEOUT=300`** (or e.g. `60`) — When you use llama-server for text (LFM2, Qwen, Mistral, custom), it stops the subprocess after this many seconds with no chat/story requests, freeing RAM/VRAM. Set in `.env`; default 300. Use `0` to keep it running indefinitely.

Server starts with minimal use. First chat → text loads. First image → image loads on GPU; after 30s idle it unloads. First video → video loads (image unloads if loaded); after 30s idle it unloads. TTS loads on first TTS request.

---

## Quick reference (all in `backend/.env`)

| Slot | Path variable | Main params |
|------|----------------|-------------|
| **Text** | `model_path_text` | `model_family_text`, `quant_text`, `ctx_text`, `gpu_layers_text`, `batch_size_text` |
| **TTS** | `model_path_tts` | `tts_engine`, `voice_id_tts` |
| **Image** | `model_path_image` | `width_image`, `height_image`, `steps_image`, `cuda_visible_devices_image` |
| **Video** | `model_path_video` | `num_frames_video`, `fps_video`, `decode_chunk_size_video`, `motion_bucket_id_video`, `noise_aug_strength_video`, `cuda_visible_devices_video` |

**Enable/disable:** `enable_text`, `enable_tts`, `enable_image`, `enable_video` (1 or 0). **Concurrent image+video:** `gpu_allow_image_and_video_concurrent=1` when you have enough VRAM.

Use **local paths** for downloaded models (e.g. `model_path_image=/home/user/models/stable-diffusion-v1-5`). Diffusers loads from that path; for HF ids it uses the cache.

---

## Tunnel (full-stack only)

When you run the **full-stack** app with `./start.sh` or `.\start_windows.bat`, you can put tunnel options in `backend/.env` and they will be picked up:

| Variable     | Example   | Meaning |
|-------------|-----------|---------|
| `TUNNEL`    | `on` / `off` | Expose the app via a public URL (default: off). |
| `TUNNEL_TOOL` | `auto`, `cloudflared`, `localtunnel` | Which tunnel tool to use (default: auto). |
| `SUBDOMAIN` | `parley-ai` | Custom subdomain for localtunnel (e.g. parley-ai.loca.lt). |

These are **not** used when you run the backend only (`python backend/run.py`); the tunnel is started by the start scripts and forwards the frontend (Vite) port.

---

## Verify GPU use (text model)

To confirm that `gpu_layers_text` is applied and the text model uses the GPU, run:

```bash
# From repo root (with venv active or use backend/venv/bin/python)
python backend/check_gpu_setup.py
```

From the `backend/` folder: `python check_gpu_setup.py`. The script loads your `.env`, prints config, checks whether llama-server is a CUDA build (when applicable), runs one short inference, and if `nvidia-smi` is available reports whether GPU memory increased. It also prints next steps if the backend is CPU-only.
