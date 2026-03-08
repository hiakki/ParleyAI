from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from resource_manager import ResourceManager, GPUSlot

logger = logging.getLogger(__name__)


class BaseRunner(ABC):
    def __init__(
        self,
        resource_manager: Optional[ResourceManager] = None,
        gpu_slot: GPUSlot = GPUSlot.NONE,
    ):
        self._resource_manager = resource_manager
        self._gpu_slot = gpu_slot
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @abstractmethod
    async def _load(self) -> None: ...

    @abstractmethod
    async def _unload(self) -> None: ...

    async def ensure_loaded(self) -> None:
        if self._loaded:
            return
        if self._gpu_slot != GPUSlot.NONE and self._resource_manager:
            await self._resource_manager.acquire_gpu_for(self._gpu_slot)
        try:
            await self._load()
            self._loaded = True
            logger.info("%s loaded", self.__class__.__name__)
        except Exception:
            if self._gpu_slot != GPUSlot.NONE and self._resource_manager:
                self._resource_manager.release_gpu_immediate(self._gpu_slot)
            raise

    async def unload(self) -> None:
        if not self._loaded:
            return
        await self._unload()
        self._loaded = False
        if self._gpu_slot != GPUSlot.NONE and self._resource_manager:
            self._resource_manager.release_gpu_from(self._gpu_slot)
