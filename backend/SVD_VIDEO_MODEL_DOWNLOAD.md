# Stable Video Diffusion (SVD) — direct downloads and where to put files

Model: **stabilityai/stable-video-diffusion-img2vid-xt** (image-to-video).

If the in-app download is slow or failing, use the direct links below and place files so the folder layout matches the Hugging Face repo.

---

## 1. Direct download links (Hugging Face)

Base URL: `https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/resolve/main/`

### Large weight files (~20 GB total)

| File | Size | Direct link |
|------|------|-------------|
| **svd_xt.safetensors** | ~9.56 GB | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/resolve/main/svd_xt.safetensors |
| **svd_xt_image_decoder.safetensors** | ~9.5 GB | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/resolve/main/svd_xt_image_decoder.safetensors |

### Config and small files (root)

| File | Direct link |
|------|-------------|
| **model_index.json** | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/resolve/main/model_index.json |

### Subfolders (required for diffusers)

Download these files into subfolders with the same names (create the folder first, then save the file into it):

| Save as | Size (approx) | Direct link |
|--------|----------------|-------------|
| **unet/diffusion_pytorch_model.safetensors** | ~2.9 GB | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/resolve/main/unet/diffusion_pytorch_model.safetensors |
| **vae/diffusion_pytorch_model.safetensors** | ~335 MB | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/resolve/main/vae/diffusion_pytorch_model.safetensors |
| **image_encoder/config.json** | small | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/resolve/main/image_encoder/config.json |
| **image_encoder/model.fp16.safetensors** | (if present) | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/resolve/main/image_encoder/model.fp16.safetensors |
| **scheduler/scheduler_config.json** | small | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/resolve/main/scheduler/scheduler_config.json |
| **feature_extractor/preprocessor_config.json** | small | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/resolve/main/feature_extractor/preprocessor_config.json |

If a link 404s, open the repo in the browser and copy the resolve link from the file’s “download” button:

- **feature_extractor:** https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/tree/main/feature_extractor  
- **image_encoder:** https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/tree/main/image_encoder  
- **scheduler:** https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/tree/main/scheduler  
- **unet:** https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/tree/main/unet  
- **vae:** https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/tree/main/vae

---

## 2. Where to keep the files

Use **one** of these:

### Option A — Custom folder (recommended for pre-download)

1. Create a folder, e.g.:
   - **Windows:** `D:\work\ParleyAI\models\stable-video-diffusion-img2vid-xt`
   - **Linux/macOS:** `~/models/stable-video-diffusion-img2vid-xt` or `$HOME/ParleyAI/models/stable-video-diffusion-img2vid-xt`

2. Inside it, mirror the repo layout:
   - Put `svd_xt.safetensors`, `svd_xt_image_decoder.safetensors`, and `model_index.json` in the root of that folder.
   - Create subfolders `feature_extractor`, `image_encoder`, `scheduler`, `unet`, `vae` and put the corresponding files from the Hugging Face repo into each.

3. In **backend/.env** set:
   ```env
   model_path_video=D:\work\ParleyAI\models\stable-video-diffusion-img2vid-xt
   ```
   (adjust path to your folder; use forward slashes or your OS path.)

### Option B — Hugging Face cache (let one download finish)

If you let the app/diffusers download finish once, files go to the HF cache, e.g.:

- **Windows:** `C:\Users\<YourUser>\.cache\huggingface\hub\models--stabilityai--stable-video-diffusion-img2vid-xt\snapshots\<revision>\`
- **Linux/macOS:** `~/.cache/huggingface/hub/models--stabilityai--stable-video-diffusion-img2vid-xt/snapshots/<revision>/`

You don’t need to set `model_path_video` then; the default ID `stabilityai/stable-video-diffusion-img2vid-xt` uses this cache.

---

## 3. Easiest: one-time full download via CLI

From a terminal (with `huggingface_hub` installed, e.g. in backend venv):

```bash
# Windows (backend venv)
cd D:\work\ParleyAI\backend
venv\Scripts\activate
huggingface-cli download stabilityai/stable-video-diffusion-img2vid-xt --local-dir D:\work\ParleyAI\models\stable-video-diffusion-img2vid-xt
```

Then in **backend/.env**:

```env
model_path_video=D:/work/ParleyAI/models/stable-video-diffusion-img2vid-xt
```

(Use your actual path; Windows can use `/` in .env.)

---

## 4. Summary

| What | Where |
|------|--------|
| **Direct links (big files)** | Above: `svd_xt.safetensors`, `svd_xt_image_decoder.safetensors`, `model_index.json` |
| **Full layout** | Same as repo: root files + `feature_extractor/`, `image_encoder/`, `scheduler/`, `unet/`, `vae/` |
| **Custom folder** | e.g. `D:\work\ParleyAI\models\stable-video-diffusion-img2vid-xt` |
| **.env** | `model_path_video=<path-to-that-folder>` |
