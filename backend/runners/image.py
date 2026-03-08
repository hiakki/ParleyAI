"""
Image: text-to-image via diffusers (GPU). Lazy load; serialized with video.
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional

from runners.base import BaseRunner
from resource_manager import ResourceManager, GPUSlot

DEVICE = "cpu" if (os.environ.get("cuda_visible_devices_image") or os.environ.get("CUDA_VISIBLE_DEVICES")) == "-1" else "cuda"
IMAGE_MODEL_ID = os.path.expanduser((os.environ.get("model_path_image") or os.environ.get("IMAGE_MODEL_ID") or "runwayml/stable-diffusion-v1-5").strip())
WIDTH_IMAGE = int(os.environ.get("width_image") or os.environ.get("WIDTH_IMAGE") or "512")
HEIGHT_IMAGE = int(os.environ.get("height_image") or os.environ.get("HEIGHT_IMAGE") or "512")
STEPS_IMAGE = int(os.environ.get("steps_image") or os.environ.get("STEPS_IMAGE") or "25")


class ImageRunner(BaseRunner):
    def __init__(self, resource_manager: Optional[ResourceManager] = None):
        super().__init__(resource_manager=resource_manager, gpu_slot=GPUSlot.IMAGE)
        self._pipe = None

    async def _load(self) -> None:
        import torch
        from diffusers import StableDiffusionPipeline
        pipe = StableDiffusionPipeline.from_pretrained(
            IMAGE_MODEL_ID,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
            safety_checker=None,
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
            if not output_path:
                fd, output_path = tempfile.mkstemp(suffix=".png")
                os.close(fd)
            img.save(output_path)
            return output_path

        return await asyncio.to_thread(_run)
