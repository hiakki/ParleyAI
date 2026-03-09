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

def _attach_image_encoder_device_hook(pipe) -> None:
    """With CPU offload, the pipeline may feed CUDA tensors to image_encoder which is on CPU. Move input to encoder device."""
    enc = getattr(pipe, "image_encoder", None)
    if enc is None:
        return

    def _pre_hook(module, args):
        if not args:
            return args
        tup = args if isinstance(args, tuple) else (args,)
        if not hasattr(tup[0], "to"):
            return args
        try:
            dev = next(module.parameters()).device
            out = (tup[0].to(dev),) + tup[1:]
            return out if isinstance(args, tuple) else out[0]
        except StopIteration:
            return args

    enc.register_forward_pre_hook(_pre_hook, with_kwargs=False)


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
        self._device: Optional[str] = None
        self._use_offload: bool = False
        self._decode_chunk_size: int = DECODE_CHUNK_SIZE_VIDEO  # can be overridden in _load when offload

    async def _load(self) -> None:
        import torch
        import logging
        log = logging.getLogger(__name__)
        self._device = _resolve_device()
        self._use_offload = _use_cpu_offload()
        from diffusers import StableVideoDiffusionPipeline
        pipe = StableVideoDiffusionPipeline.from_pretrained(
            VIDEO_MODEL_ID,
            torch_dtype=torch.float16 if (self._device == "cuda" or self._use_offload) else torch.float32,
        )
        if self._use_offload and (self._device == "cuda" or torch.cuda.is_available()):
            pipe.enable_model_cpu_offload()
            if hasattr(pipe, "unet") and hasattr(pipe.unet, "enable_forward_chunking"):
                pipe.unet.enable_forward_chunking()
            self._decode_chunk_size = min(DECODE_CHUNK_SIZE_VIDEO, 2)  # 2 is safe for 8 GB
            # Ensure image_encoder receives inputs on its device (CPU when offloaded); avoid cuda/cpu mismatch
            _attach_image_encoder_device_hook(pipe)
            log.info("Video model: using CPU offload + chunking (runs on 8 GB VRAM)")
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

        def _run():
            out = self._pipe(
                image,
                num_frames=nf,
                decode_chunk_size=self._decode_chunk_size,
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
