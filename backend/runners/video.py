"""
Video: image-to-video via SVD (GPU or CPU offload). Lazy load; serialized with image.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from runners.base import BaseRunner
from resource_manager import ResourceManager, GPUSlot

def _int_ev(k: str, leg: str, d: int) -> int:
    v = os.environ.get(k) or os.environ.get(leg)
    return int(v) if v else d

def _float_ev(k: str, leg: str, d: float) -> float:
    v = os.environ.get(k) or os.environ.get(leg)
    return float(v) if v else d

def _resolve_device() -> str:
    if (os.environ.get("cuda_visible_devices_video") or os.environ.get("CUDA_VISIBLE_DEVICES")) == "-1":
        return "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _use_cpu_offload() -> bool:
    """Use model CPU offload for SVD on 8 GB GPUs. Env video_cpu_offload=1 or auto if VRAM <= 8.5 GB."""
    v = (os.environ.get("video_cpu_offload") or os.environ.get("VIDEO_CPU_OFFLOAD") or "").lower()
    if v in ("1", "true", "yes"):
        return True
    try:
        import torch
        if torch.cuda.is_available():
            total_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            if total_gb <= 8.5:
                return True
    except Exception:
        pass
    return False

def _video_engine() -> str:
    v = (os.environ.get("video_engine") or os.environ.get("VIDEO_ENGINE") or "svd").strip().lower()
    return v if v in ("svd", "cogvideox") else "svd"

VIDEO_ENGINE = _video_engine()
VIDEO_MODEL_ID = os.path.expanduser((os.environ.get("model_path_video") or os.environ.get("VIDEO_MODEL_ID") or (
    "THUDM/CogVideoX-5b-I2V" if VIDEO_ENGINE == "cogvideox" else "stabilityai/stable-video-diffusion-img2vid-xt"
)).strip())
NUM_FRAMES_VIDEO = _int_ev("num_frames_video", "NUM_FRAMES_VIDEO", 49 if VIDEO_ENGINE == "cogvideox" else 25)
FPS_VIDEO = _int_ev("fps_video", "FPS_VIDEO", 8 if VIDEO_ENGINE == "cogvideox" else 6)
DECODE_CHUNK_SIZE_VIDEO = _int_ev("decode_chunk_size_video", "DECODE_CHUNK_SIZE_VIDEO", 8)
NUM_INFERENCE_STEPS_VIDEO = _int_ev("num_inference_steps_video", "NUM_INFERENCE_STEPS_VIDEO", 20)
MOTION_BUCKET_ID_VIDEO = _int_ev("motion_bucket_id_video", "MOTION_BUCKET_ID_VIDEO", 127)
NOISE_AUG_STRENGTH_VIDEO = _float_ev("noise_aug_strength_video", "NOISE_AUG_STRENGTH_VIDEO", 0.02)
COGVIDEOX_GUIDANCE_SCALE = _float_ev("cogvideox_guidance_scale_video", "COGVIDEOX_GUIDANCE_SCALE", 6.0)


class VideoRunner(BaseRunner):
    def __init__(self, resource_manager: Optional[ResourceManager] = None):
        super().__init__(resource_manager=resource_manager, gpu_slot=GPUSlot.VIDEO)
        self._pipe = None
        self._device: Optional[str] = None
        self._use_offload: bool = False
        self._decode_chunk_size: int = DECODE_CHUNK_SIZE_VIDEO
        self._engine: str = VIDEO_ENGINE
        self._num_inference_steps: int = NUM_INFERENCE_STEPS_VIDEO

    async def _load(self) -> None:
        import torch
        import logging
        log = logging.getLogger(__name__)
        self._device = _resolve_device()
        self._use_offload = _use_cpu_offload()

        if self._engine == "cogvideox":
            try:
                from diffusers import CogVideoXImageToVideoPipeline
            except ImportError:
                log.warning("CogVideoX not available (needs diffusers>=0.30). Falling back to SVD.")
                self._engine = "svd"
            else:
                dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
                pipe = CogVideoXImageToVideoPipeline.from_pretrained(
                    VIDEO_MODEL_ID,
                    torch_dtype=dtype,
                )
                vram_gb = 0
                if torch.cuda.is_available():
                    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                needs_offload = self._use_offload or vram_gb <= 12
                if (self._device == "cuda" or torch.cuda.is_available()) and needs_offload:
                    # enable_model_cpu_offload needs ~19 GB; sequential + vae slicing/tiling gets to ~5 GB
                    pipe.enable_sequential_cpu_offload()
                    pipe.vae.enable_slicing()
                    pipe.vae.enable_tiling()
                    log.info("Video model: CogVideoX I2V with sequential CPU offload + VAE slicing/tiling (~5 GB VRAM). WARNING: expect ~20-30 min per video on 8 GB.")
                else:
                    pipe = pipe.to(self._device or "cuda")
                self._pipe = pipe
                return

        from diffusers import StableVideoDiffusionPipeline
        svd_model_id = os.path.expanduser(
            (os.environ.get("model_path_video") or os.environ.get("VIDEO_MODEL_ID") or "stabilityai/stable-video-diffusion-img2vid-xt").strip()
        )
        pipe = StableVideoDiffusionPipeline.from_pretrained(
            svd_model_id,
            torch_dtype=torch.float16 if (self._device == "cuda" or self._use_offload) else torch.float32,
        )
        if self._use_offload and (self._device == "cuda" or torch.cuda.is_available()):
            pipe.enable_sequential_cpu_offload()
            if hasattr(pipe, "unet") and hasattr(pipe.unet, "enable_forward_chunking"):
                pipe.unet.enable_forward_chunking()
            self._decode_chunk_size = min(DECODE_CHUNK_SIZE_VIDEO, 2)
            log.info("Video model: SVD with sequential CPU offload (8 GB VRAM). Use num_frames_video=5–14, num_inference_steps_video=14–20 for faster runs.")
        else:
            pipe = pipe.to(self._device)
            if self._device == "cuda":
                pipe.enable_attention_slicing()
        self._pipe = pipe

    async def _unload(self) -> None:
        if self._pipe is not None:
            import torch
            del self._pipe
            self._pipe = None
            if self._device == "cuda" or self._use_offload:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    async def generate(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        output_path: Optional[str] = None,
        num_frames: Optional[int] = None,
        fps: Optional[int] = None,
    ) -> str:
        await self.ensure_loaded()
        import asyncio
        from PIL import Image
        nf = num_frames if num_frames is not None else NUM_FRAMES_VIDEO
        fps_val = fps if fps is not None else FPS_VIDEO
        image = Image.open(image_path).convert("RGB")
        steps = self._num_inference_steps

        def _run():
            if output_path:
                save_path = output_path
            else:
                fd, save_path = tempfile.mkstemp(suffix=".mp4")
                os.close(fd)
            if self._engine == "cogvideox":
                img = image.resize((720, 480))
                # CogVideoX-5b-I2V only supports 49 frames; 1.5 supports 81/161
                cog_frames = 49 if nf <= 49 else 81
                out = self._pipe(
                    img,
                    prompt=prompt or "smooth motion, high quality",
                    num_frames=cog_frames,
                    height=480,
                    width=720,
                    num_inference_steps=steps,
                    guidance_scale=COGVIDEOX_GUIDANCE_SCALE,
                )
                frames = out.frames[0]
            else:
                out = self._pipe(
                    image,
                    num_frames=nf,
                    decode_chunk_size=self._decode_chunk_size,
                    motion_bucket_id=MOTION_BUCKET_ID_VIDEO,
                    noise_aug_strength=NOISE_AUG_STRENGTH_VIDEO,
                    num_inference_steps=steps,
                )
                frames = out.frames[0]
            return self._frames_to_mp4(frames, save_path, fps_val)

        return await asyncio.to_thread(_run)

    def _frames_to_mp4(self, frames: list, output_path: str, fps: int) -> str:
        import numpy as np
        from PIL import Image
        arrs = [np.array(f.convert("RGB") if hasattr(f, "convert") else f) for f in frames]
        try:
            import imageio
            imageio.mimsave(output_path, arrs, fps=fps, codec="libx264")
            return output_path
        except Exception:
            gif_path = output_path.replace(".mp4", ".gif")
            imgs = [Image.fromarray(a) for a in arrs]
            imgs[0].save(gif_path, save_all=True, append_images=imgs[1:], duration=1000 // max(1, fps), loop=0)
            return gif_path
