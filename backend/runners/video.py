"""
Video: image-to-video via SVD (GPU). Lazy load; serialized with image.
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

DEVICE = "cpu" if (os.environ.get("cuda_visible_devices_video") or os.environ.get("CUDA_VISIBLE_DEVICES")) == "-1" else "cuda"
VIDEO_MODEL_ID = os.path.expanduser((os.environ.get("model_path_video") or os.environ.get("VIDEO_MODEL_ID") or "stabilityai/stable-video-diffusion-img2vid-xt").strip())
NUM_FRAMES_VIDEO = _int_ev("num_frames_video", "NUM_FRAMES_VIDEO", 25)
FPS_VIDEO = _int_ev("fps_video", "FPS_VIDEO", 6)
DECODE_CHUNK_SIZE_VIDEO = _int_ev("decode_chunk_size_video", "DECODE_CHUNK_SIZE_VIDEO", 8)
MOTION_BUCKET_ID_VIDEO = _int_ev("motion_bucket_id_video", "MOTION_BUCKET_ID_VIDEO", 127)
NOISE_AUG_STRENGTH_VIDEO = _float_ev("noise_aug_strength_video", "NOISE_AUG_STRENGTH_VIDEO", 0.02)


class VideoRunner(BaseRunner):
    def __init__(self, resource_manager: Optional[ResourceManager] = None):
        super().__init__(resource_manager=resource_manager, gpu_slot=GPUSlot.VIDEO)
        self._pipe = None

    async def _load(self) -> None:
        import torch
        from diffusers import StableVideoDiffusionPipeline
        pipe = StableVideoDiffusionPipeline.from_pretrained(
            VIDEO_MODEL_ID,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        )
        pipe = pipe.to(DEVICE)
        if DEVICE == "cuda":
            pipe.enable_attention_slicing()
        self._pipe = pipe

    async def _unload(self) -> None:
        if self._pipe is not None:
            import torch
            del self._pipe
            self._pipe = None
            if DEVICE == "cuda":
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

        def _run():
            out = self._pipe(
                image,
                num_frames=nf,
                decode_chunk_size=DECODE_CHUNK_SIZE_VIDEO,
                motion_bucket_id=MOTION_BUCKET_ID_VIDEO,
                noise_aug_strength=NOISE_AUG_STRENGTH_VIDEO,
            )
            frames = out.frames[0]
            if not output_path:
                fd, output_path = tempfile.mkstemp(suffix=".mp4")
                os.close(fd)
            return self._frames_to_mp4(frames, output_path, fps_val)

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
