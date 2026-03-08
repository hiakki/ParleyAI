"""
GPU use for optional image/video runners.
By default only one of image or video uses VRAM at a time.
Set gpu_allow_image_and_video_concurrent=1 to allow both loaded at once (needs enough VRAM).
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


class GPUSlot(str, Enum):
    NONE = "none"
    IMAGE = "image"
    VIDEO = "video"


class ResourceManager:
    def __init__(
        self,
        unload_gpu_after_idle_sec: Optional[float] = 30.0,
        allow_image_video_concurrent: bool = False,
    ):
        self._unload_after_idle_sec = unload_gpu_after_idle_sec
        self._allow_concurrent = allow_image_video_concurrent

        # Serial mode: one lock, one slot, one idle task
        self._gpu_lock = asyncio.Lock()
        self._current_gpu_slot: GPUSlot = GPUSlot.NONE
        self._idle_task: Optional[asyncio.Task] = None

        # Concurrent mode: per-slot lock and idle task
        self._image_lock = asyncio.Lock()
        self._video_lock = asyncio.Lock()
        self._image_idle_task: Optional[asyncio.Task] = None
        self._video_idle_task: Optional[asyncio.Task] = None

    @property
    def current_gpu_slot(self) -> GPUSlot:
        if self._allow_concurrent:
            if self._image_lock.locked():
                return GPUSlot.IMAGE
            if self._video_lock.locked():
                return GPUSlot.VIDEO
            return GPUSlot.NONE
        return self._current_gpu_slot

    async def acquire_gpu_for(self, slot: GPUSlot) -> None:
        if slot == GPUSlot.NONE:
            return
        if self._allow_concurrent:
            if slot == GPUSlot.IMAGE:
                await self._image_lock.acquire()
                if self._image_idle_task and not self._image_idle_task.done():
                    self._image_idle_task.cancel()
                    try:
                        await self._image_idle_task
                    except asyncio.CancelledError:
                        pass
                    self._image_idle_task = None
            elif slot == GPUSlot.VIDEO:
                await self._video_lock.acquire()
                if self._video_idle_task and not self._video_idle_task.done():
                    self._video_idle_task.cancel()
                    try:
                        await self._video_idle_task
                    except asyncio.CancelledError:
                        pass
                    self._video_idle_task = None
            return
        # Serial mode
        await self._gpu_lock.acquire()
        self._current_gpu_slot = slot
        if self._idle_task and not self._idle_task.done():
            self._idle_task.cancel()
            try:
                await self._idle_task
            except asyncio.CancelledError:
                pass
            self._idle_task = None

    def release_gpu_from(
        self, slot: GPUSlot, unload_callback: Optional[Callable[[], Awaitable[None]]] = None
    ) -> None:
        if slot == GPUSlot.NONE:
            return
        if self._allow_concurrent:
            if slot == GPUSlot.IMAGE:
                if self._image_lock.locked():
                    self._image_lock.release()
                if self._unload_after_idle_sec and unload_callback:
                    async def _idle():
                        try:
                            await asyncio.sleep(self._unload_after_idle_sec)
                            await unload_callback()
                        except asyncio.CancelledError:
                            pass
                    self._image_idle_task = asyncio.create_task(_idle())
            elif slot == GPUSlot.VIDEO:
                if self._video_lock.locked():
                    self._video_lock.release()
                if self._unload_after_idle_sec and unload_callback:
                    async def _idle():
                        try:
                            await asyncio.sleep(self._unload_after_idle_sec)
                            await unload_callback()
                        except asyncio.CancelledError:
                            pass
                    self._video_idle_task = asyncio.create_task(_idle())
            return
        # Serial mode
        if self._current_gpu_slot == slot:
            self._current_gpu_slot = GPUSlot.NONE
            if self._gpu_lock.locked():
                self._gpu_lock.release()
        if self._unload_after_idle_sec and unload_callback and slot != GPUSlot.NONE:
            async def _idle_unload():
                try:
                    await asyncio.sleep(self._unload_after_idle_sec)
                    if self._current_gpu_slot == GPUSlot.NONE:
                        await unload_callback()
                except asyncio.CancelledError:
                    pass

            self._idle_task = asyncio.create_task(_idle_unload())

    def release_gpu_immediate(self, slot: GPUSlot) -> None:
        if slot == GPUSlot.NONE:
            return
        if self._allow_concurrent:
            if slot == GPUSlot.IMAGE:
                if self._image_lock.locked():
                    self._image_lock.release()
                if self._image_idle_task and not self._image_idle_task.done():
                    self._image_idle_task.cancel()
                    self._image_idle_task = None
            elif slot == GPUSlot.VIDEO:
                if self._video_lock.locked():
                    self._video_lock.release()
                if self._video_idle_task and not self._video_idle_task.done():
                    self._video_idle_task.cancel()
                    self._video_idle_task = None
            return
        if self._current_gpu_slot == slot:
            self._current_gpu_slot = GPUSlot.NONE
            if self._gpu_lock.locked():
                self._gpu_lock.release()
        if self._idle_task and not self._idle_task.done():
            self._idle_task.cancel()
            self._idle_task = None
