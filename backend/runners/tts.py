"""
TTS: edge-tts (default, no model) or Piper (CPU). Lazy load on first use.
"""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from typing import Optional

from runners.base import BaseRunner
from resource_manager import ResourceManager, GPUSlot

TTS_ENGINE = os.environ.get("tts_engine") or os.environ.get("TTS_ENGINE", "edge")
PIPER_VOICE = os.environ.get("voice_id_tts") or os.environ.get("PIPER_VOICE", "en_US-lessac-medium")
MODEL_PATH_TTS = (os.environ.get("model_path_tts") or os.environ.get("PIPER_VOICE_PATH") or "").strip()


class TTSRunner(BaseRunner):
    def __init__(self, resource_manager: Optional[ResourceManager] = None):
        super().__init__(resource_manager=resource_manager, gpu_slot=GPUSlot.NONE)
        self._piper_model = None

    async def _load(self) -> None:
        if TTS_ENGINE != "piper":
            return
        from piper import PiperVoice
        voice_path = os.path.expanduser(MODEL_PATH_TTS) if MODEL_PATH_TTS else None
        if not voice_path:
            raise RuntimeError("model_path_tts (or PIPER_VOICE_PATH) required when tts_engine=piper")
        self._piper_model = PiperVoice.load(voice_path)

    async def _unload(self) -> None:
        self._piper_model = None

    async def generate(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> tuple[str, float]:
        if TTS_ENGINE == "edge":
            return await self._generate_edge(text, language, output_path)
        await self.ensure_loaded()
        return await self._generate_piper(text, voice_id or PIPER_VOICE, output_path)

    async def _generate_edge(
        self, text: str, language: Optional[str], output_path: Optional[str]
    ) -> tuple[str, float]:
        import edge_tts
        voice = "en-IN-NeerjaNeural" if (language or "").startswith("hi") else "en-US-JennyNeural"
        communicate = edge_tts.Communicate(text, voice)
        buf = io.BytesIO()
        await communicate.save(buf)
        buf.seek(0)
        if not output_path:
            fd, output_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
        with open(output_path, "wb") as f:
            f.write(buf.read())
        words = len(text.split())
        duration_sec = (words / 150.0) * 60.0 if words else 1.0
        return output_path, duration_sec

    async def _generate_piper(
        self, text: str, voice_id: str, output_path: Optional[str]
    ) -> tuple[str, float]:
        import asyncio
        import wave
        if not output_path:
            fd, output_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
        out_path = Path(output_path)

        def _run():
            with open(out_path, "wb") as f:
                self._piper_model.synthesize(text, f)

        await asyncio.to_thread(_run)
        with wave.open(str(out_path), "rb") as w:
            duration_sec = w.getnframes() / float(w.getframerate() or 1)
        return output_path, duration_sec
