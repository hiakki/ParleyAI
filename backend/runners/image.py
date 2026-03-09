"""
Image: text-to-image via diffusers (GPU or CPU). Lazy load; serialized with video.
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional

from runners.base import BaseRunner
from resource_manager import ResourceManager, GPUSlot

def _resolve_device() -> str:
    """Use CUDA only if env doesn't force CPU and torch has CUDA built in and available."""
    if (os.environ.get("cuda_visible_devices_image") or os.environ.get("CUDA_VISIBLE_DEVICES")) == "-1":
        return "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"

IMAGE_MODEL_ID = os.path.expanduser((os.environ.get("model_path_image") or os.environ.get("IMAGE_MODEL_ID") or "runwayml/stable-diffusion-v1-5").strip())
WIDTH_IMAGE = int(os.environ.get("width_image") or os.environ.get("WIDTH_IMAGE") or "512")
HEIGHT_IMAGE = int(os.environ.get("height_image") or os.environ.get("HEIGHT_IMAGE") or "512")
STEPS_IMAGE = int(os.environ.get("steps_image") or os.environ.get("STEPS_IMAGE") or "25")


class ImageRunner(BaseRunner):
    def __init__(self, resource_manager: Optional[ResourceManager] = None):
        super().__init__(resource_manager=resource_manager, gpu_slot=GPUSlot.IMAGE)
        self._pipe = None
        self._device: Optional[str] = None

    async def _load(self) -> None:
        import torch
        import logging
        log = logging.getLogger(__name__)
        self._device = _resolve_device()
        if self._device == "cpu":
            log.info(
                "Image model: using CPU (PyTorch CUDA not available or disabled). "
                "Re-run setup_windows.bat or setup_fullstack.sh to install PyTorch with CUDA, or: pip install torch --index-url https://download.pytorch.org/whl/cu124"
            )
        from diffusers import StableDiffusionPipeline
        pipe = StableDiffusionPipeline.from_pretrained(
            IMAGE_MODEL_ID,
            torch_dtype=torch.float16 if self._device == "cuda" else torch.float32,
            safety_checker=None,
        )
        pipe = pipe.to(self._device)
        if self._device == "cuda":
            pipe.enable_attention_slicing()
        self._pipe = pipe

    async def _unload(self) -> None:
        if self._pipe is not None:
            import torch
            del self._pipe
            self._pipe = None
            if self._device == "cuda":
                torch.cuda.empty_cache()

    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        output_path: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> str:
        await self.ensure_loaded()
        import asyncio
        w = width if width is not None else WIDTH_IMAGE
        h = height if height is not None else HEIGHT_IMAGE

        def _run():
            out = self._pipe(
                prompt,
                negative_prompt=negative_prompt or "blurry, low quality",
                num_inference_steps=STEPS_IMAGE,
                width=w,
                height=h,
            )
            img = out.images[0]
            if output_path:
                save_path = output_path
            else:
                fd, save_path = tempfile.mkstemp(suffix=".png")
                os.close(fd)
            img.save(save_path)
            return save_path

        return await asyncio.to_thread(_run)
