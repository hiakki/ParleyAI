#!/usr/bin/env python3
"""
ParleyAI Backend Server

FastAPI backend providing REST API and Server-Sent Events (SSE) for streaming
chat responses from local GGUF models (Llama 3.3 70B, LFM2-24B, etc.).
"""

# Load .env first so all config is from backend/.env
import os
from pathlib import Path as _Path
_env_file = _Path(__file__).resolve().parent / ".env"
if _env_file.exists():
    try:
        import dotenv
        dotenv.load_dotenv(_env_file)
    except ImportError:
        with open(_env_file, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))

import json
import asyncio
import logging
import sys
import threading
import time
import uuid
import glob
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import field_validator, ConfigDict
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from llama_transformer import LlamaTransformer, LlamaServerTransformer, get_transformer, PerfMetrics, MODEL_FAMILIES

# Optional: TTS, image, video (lazy-loaded). Only register routes if deps available.
_tts_available = False
try:
    import edge_tts  # noqa: F401
    from runners.tts import TTSRunner
    _tts_available = True
except ImportError:
    pass

_image_video_available = False
_resource_manager = None
_image_runner = None
_video_runner = None
_tts_runner = None
try:
    from resource_manager import ResourceManager, GPUSlot
    from runners.image import ImageRunner
    from runners.video import VideoRunner
    _image_video_available = True
except ImportError as e:
    logger.debug("Optional runners (image/video) not available: %s", e)

# Setup logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Create log file with timestamp
log_filename = LOG_DIR / f"server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Only one request can use the text model at a time (llama-server is single-request).
# Streaming holds this for the whole stream; other requests get 503 if they can't acquire quickly.
_transformer_lock = threading.Lock()
TRANSFORMER_LOCK_TIMEOUT = 2  # seconds to wait before returning 503 "model busy"

# Configuration from environment (.env or os.environ); prefer *_text / *_image / *_video / *_tts names
MODEL_FAMILY = os.getenv("model_family_text") or os.getenv("MODEL_FAMILY", "Llama-3.3-70B-Instruct")
QUANT = os.getenv("quant_text") or os.getenv("QUANT", "Q4_K_M")
MODEL_PATH_ENV = os.getenv("model_path_text") or os.getenv("MODEL_PATH", None)
CTX = int(os.getenv("ctx_text") or os.getenv("CTX", "2048"))
_gpu_layers_raw = os.getenv("gpu_layers_text") or os.getenv("GPU_LAYERS", "-1")
GPU_LAYERS = int(_gpu_layers_raw)
GPU_LAYERS_SOURCE = "gpu_layers_text" if os.getenv("gpu_layers_text") else ("GPU_LAYERS" if os.getenv("GPU_LAYERS") else "default")
BATCH_SIZE = int(os.getenv("batch_size_text") or os.getenv("BATCH_SIZE", "512"))


def _env_bool(name: str, default: bool = True) -> bool:
    v = (os.getenv(name) or os.getenv(name.upper()) or ("1" if default else "0")).lower()
    return v in ("1", "true", "yes", "on")


ENABLE_TEXT = _env_bool("enable_text", True)
ENABLE_TTS = _env_bool("enable_tts", True)
ENABLE_IMAGE = _env_bool("enable_image", True)
ENABLE_VIDEO = _env_bool("enable_video", True)
GPU_ALLOW_IMAGE_VIDEO_CONCURRENT = _env_bool("gpu_allow_image_and_video_concurrent", False)
# When 1, text/LLM loads on first chat request (saves RAM/VRAM until needed; recommended for 8GB VRAM).
TEXT_LAZY_LOAD = _env_bool("text_lazy_load", True)

# Resolve MODEL_PATH - handle directory vs file (filename depends on model_family)
def _find_split_first_part(directory: str, stem: str) -> str | None:
    """Find the first part of a split GGUF (e.g. model-00001-of-00006.gguf)."""
    pattern = os.path.join(directory, f"{stem}-00001-of-*.gguf")
    matches = sorted(glob.glob(pattern))
    return matches[0] if matches else None

def _find_gguf_in_dir(directory: str, filename: str | None) -> str | None:
    """Search a directory for a GGUF file by exact name, split pattern, variant, or sole file."""
    if filename:
        full_path = os.path.join(directory, filename)
        if os.path.exists(full_path):
            return full_path

        stem = os.path.splitext(filename)[0]
        split_path = _find_split_first_part(directory, stem)
        if split_path:
            return split_path

        variant_matches = sorted(glob.glob(os.path.join(directory, f"{stem}*.gguf")))
        if variant_matches:
            return variant_matches[0]

    gguf_matches = sorted(glob.glob(os.path.join(directory, "*.gguf")))
    non_split = [f for f in gguf_matches if not _is_split_continuation(f)]
    if len(non_split) == 1:
        return non_split[0]
    return None

def _is_split_continuation(path: str) -> bool:
    """True for split parts 2+ (not the first part, not single files)."""
    name = os.path.basename(path)
    for i in range(2, 100):
        if f"-{i:05d}-of-" in name:
            return True
    return False

def resolve_model_path(path_env: str | None, quant: str, model_family: str) -> str | None:
    """Resolve model path from environment variable.
    
    Search order for directories:
      1. {path}/{model_family}/{quant}/  (e.g. ~/local-llms/Qwen2.5-32B-Instruct/Q5_K_M/)
      2. {path}/{model_family}/          (e.g. ~/local-llms/Qwen2.5-32B-Instruct/)
      3. {path}/                         (e.g. ~/local-llms/)
    At each level: exact filename > split first part > variant > sole GGUF.
    """
    if path_env is None:
        return None
    
    path = os.path.expanduser(path_env)
    
    if os.path.isdir(path):
        quants = MODEL_FAMILIES.get(model_family, {}).get("quants", {})
        filename = quants.get(quant, {}).get("filename") if quant in quants else None

        # Check {path}/{model_family}/{quant}/ first
        nested = os.path.join(path, model_family, quant)
        if os.path.isdir(nested):
            result = _find_gguf_in_dir(nested, filename)
            if result:
                return result

        # Check {path}/{model_family}/
        family_dir = os.path.join(path, model_family)
        if os.path.isdir(family_dir):
            result = _find_gguf_in_dir(family_dir, filename)
            if result:
                return result

        # Check {path}/ directly
        return _find_gguf_in_dir(path, filename)
    
    if os.path.isfile(path):
        return path
    
    return None

MODEL_PATH = resolve_model_path(MODEL_PATH_ENV, QUANT, MODEL_FAMILY)

# Global transformer instance (loaded at startup or on first request when text_lazy_load=1)
transformer: Optional[LlamaTransformer] = None
_transformer_load_lock = asyncio.Lock()  # serializes loading only; inference uses _transformer_lock (threading)


async def ensure_text_loaded() -> None:
    """Load the text/LLM model on first use when text_lazy_load=1. Idempotent."""
    global transformer
    if not ENABLE_TEXT or transformer is not None:
        return
    async with _transformer_load_lock:
        if transformer is not None:
            return
        logger.info("Loading text model on first request...")
        try:
            trans = await asyncio.to_thread(
                get_transformer,
                quantization=QUANT,
                model_path=MODEL_PATH,
                model_family=MODEL_FAMILY,
                n_ctx=CTX,
                n_gpu_layers=GPU_LAYERS,
                n_batch=BATCH_SIZE,
            )
            transformer = trans
            logger.info("Text model loaded successfully")
        except Exception as e:
            logger.error("Failed to load text model: %s", e)
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the transformer on startup when enable_text=1 and text_lazy_load=0; else load on first request."""
    global transformer
    logger.info("=" * 60)
    logger.info("Initializing Backend Server")
    logger.info("=" * 60)
    logger.info("Enabled: text=%s tts=%s image=%s video=%s", ENABLE_TEXT, ENABLE_TTS, ENABLE_IMAGE, ENABLE_VIDEO)
    if ENABLE_TEXT:
        logger.info(f"Model family: {MODEL_FAMILY} ({MODEL_FAMILIES.get(MODEL_FAMILY, {}).get('name', '')})")
        logger.info(f"Quantization: {QUANT}")
        logger.info(f"Context: {CTX} tokens")
        logger.info(f"Batch Size: {BATCH_SIZE}")
        logger.info(f"GPU Layers: {GPU_LAYERS} (from {GPU_LAYERS_SOURCE})")
        if GPU_LAYERS > 0:
            logger.info("If you see no GPU use: ensure llama-server is the CUDA build (Windows) or llama-cpp-python was built with CUDA; CPU-only builds ignore GPU layers.")
        logger.info("Optimizations: Flash Attention enabled, KV Offload enabled")
        if MODEL_PATH:
            logger.info(f"Model Path: {MODEL_PATH}")
        if TEXT_LAZY_LOAD:
            logger.info("Text model will load on first chat/story request (text_lazy_load=1)")
        else:
            try:
                transformer = get_transformer(
                    quantization=QUANT,
                    model_path=MODEL_PATH,
                    model_family=MODEL_FAMILY,
                    n_ctx=CTX,
                    n_gpu_layers=GPU_LAYERS,
                    n_batch=BATCH_SIZE,
                )
                logger.info("Text model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise
    else:
        logger.info("Text model disabled (enable_text=0)")
    logger.info(f"Log file: {log_filename}")
    logger.info("Server ready")
    yield
    logger.info("Shutting down...")
    if transformer and isinstance(transformer, LlamaServerTransformer):
        transformer.shutdown()


app = FastAPI(
    title="ParleyAI API",
    description="ParleyAI — chat with local GGUF models (Llama 3.3 70B, LFM2-24B, etc.)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: localhost + tunnel origins so IDE clients (Cursor, Continue) can call /v1 via tunnel
_cors_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
# Allow any trycloudflare.com / localtunnel / ngrok origin when using TUNNEL=on
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://([a-z0-9-]+\.(trycloudflare\.com|loca\.lt|ngrok-free\.app|ngrok\.io)|localhost)(:\d+)?$",
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str  # "user", "assistant", or "system"
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    max_tokens: int = 512
    temperature: float = 0.7
    stream: bool = True


class ChatResponse(BaseModel):
    response: str
    tokens_generated: int = 0


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "enabled": {"text": ENABLE_TEXT, "tts": ENABLE_TTS, "image": ENABLE_IMAGE, "video": ENABLE_VIDEO},
        "model_family": MODEL_FAMILY if ENABLE_TEXT else None,
        "model": MODEL_FAMILIES.get(MODEL_FAMILY, {}).get("name", MODEL_FAMILY) if ENABLE_TEXT else None,
        "quantization": QUANT if ENABLE_TEXT else None,
        "context_window": CTX if ENABLE_TEXT else None,
    }


@app.get("/api/models")
async def list_models():
    """List available quantization options for the current model family."""
    if not ENABLE_TEXT:
        raise HTTPException(status_code=503, detail="Text model disabled (enable_text=0)")
    await ensure_text_loaded()
    if transformer is None:
        raise HTTPException(status_code=503, detail="Text model not loaded")
    quants = MODEL_FAMILIES.get(MODEL_FAMILY, {}).get("quants", {})
    return {
        "model_family": MODEL_FAMILY,
        "models": [
            {
                "id": name,
                "size_gb": info["size_gb"],
                "quality": info["quality"],
                "recommended_ram": info["recommended_ram"],
            }
            for name, info in quants.items()
        ],
        "current": QUANT,
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat completion endpoint.
    
    If stream=True, returns Server-Sent Events (SSE).
    If stream=False, returns complete response as JSON.
    """
    if not ENABLE_TEXT or transformer is None:
        raise HTTPException(
            status_code=503,
            detail="Text model disabled (enable_text=0) or not loaded",
        )
    await ensure_text_loaded()
    if transformer is None:
        raise HTTPException(status_code=503, detail="Text model not loaded")
    
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    # Log the request
    user_msg = next((m["content"][:100] for m in messages if m["role"] == "user"), "")
    logger.info(f"Chat request: stream={request.stream}, max_tokens={request.max_tokens}")
    logger.info(f"User message: {user_msg}{'...' if len(user_msg) >= 100 else ''}")
    
    if request.stream:
        logger.info("[api/chat] Stream started (waiting for first token...)")
        return StreamingResponse(
            stream_chat(messages, request.max_tokens, request.temperature),
            media_type="text/event-stream",
        )
    else:
        if not _transformer_lock.acquire(blocking=True, timeout=TRANSFORMER_LOCK_TIMEOUT):
            raise HTTPException(
                status_code=503,
                detail="Model is busy with another request (streaming or generation in progress). Please try again later.",
            )
        try:
            response = transformer.chat(
                messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=False,
            )
            logger.info(f"Response generated: {len(response)} chars")
            return ChatResponse(response=response)
        finally:
            _transformer_lock.release()


async def stream_chat(
    messages: list[dict],
    max_tokens: int,
    temperature: float,
):
    """Generator for SSE streaming with performance metrics."""
    _transformer_lock.acquire()
    try:
        logger.info("Starting streaming generation...")
        logger.info("[api/chat] Calling model (if cold start: loading + prompt eval can take 1–2 min before first token)...")
        token_count = 0
        first_token_logged = False
        stream_start = time.time()
        last_status_log = stream_start
        STATUS_INTERVAL = 10  # log "still streaming" every N seconds
        try:
            for token, metrics in transformer.chat_with_metrics(
                messages,
                max_tokens=max_tokens,
                temperature=temperature,
            ):
            if token is not None:
                if not first_token_logged:
                    logger.info("[api/chat] Streaming output...")
                    first_token_logged = True
                token_count += 1
                now = time.time()
                if now - last_status_log >= STATUS_INTERVAL:
                    elapsed = int(now - stream_start)
                    logger.info("[api/chat] Still streaming... %ds elapsed, %d tokens so far", elapsed, token_count)
                    last_status_log = now
                # Streaming token
                data = json.dumps({"token": token, "done": False})
                yield f"data: {data}\n\n"
                await asyncio.sleep(0)  # Allow other tasks to run
            elif metrics is not None:
                # Final message with metrics
                logger.info(f"Generation complete: {token_count} tokens")
                logger.info(f"Performance: {metrics.tokens_per_second:.2f} tok/s, "
                           f"prompt: {metrics.prompt_tokens} tok @ {metrics.prompt_per_second:.2f} tok/s, "
                           f"total: {metrics.total_time_ms:.0f}ms")
                data = json.dumps({
                    "token": "",
                    "done": True,
                    "metrics": metrics.to_dict(),
                })
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(f"Error during streaming: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
    finally:
        _transformer_lock.release()


@app.post("/api/generate")
async def generate(prompt: str, max_tokens: int = 512, temperature: float = 0.7):
    """Raw text generation endpoint (non-chat format)."""
    if not ENABLE_TEXT or transformer is None:
        raise HTTPException(status_code=503, detail="Text model disabled (enable_text=0) or not loaded")
    await ensure_text_loaded()
    if transformer is None:
        raise HTTPException(status_code=503, detail="Text model not loaded")
    if not _transformer_lock.acquire(blocking=True, timeout=TRANSFORMER_LOCK_TIMEOUT):
        raise HTTPException(
            status_code=503,
            detail="Model is busy with another request (streaming or generation in progress). Please try again later.",
        )
    try:
        response = transformer.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False,
        )
        return {"response": response}
    finally:
        _transformer_lock.release()


# --- Optional: story (script JSON), TTS, image, video (lazy-loaded when deps installed) ---

def _get_resource_manager():
    global _resource_manager
    if not _image_video_available:
        return None
    if _resource_manager is None:
        idle = float(os.getenv("gpu_unload_after_idle_sec") or os.getenv("GPU_UNLOAD_AFTER_IDLE_SEC", "30") or "30")
        from resource_manager import ResourceManager
        _resource_manager = ResourceManager(
            unload_gpu_after_idle_sec=idle if idle > 0 else None,
            allow_image_video_concurrent=GPU_ALLOW_IMAGE_VIDEO_CONCURRENT,
        )
    return _resource_manager


def _get_tts_runner():
    global _tts_runner
    if _tts_runner is None and _tts_available:
        from runners.tts import TTSRunner
        rm = _get_resource_manager() if _image_video_available else None
        _tts_runner = TTSRunner(resource_manager=rm)
    return _tts_runner


def _get_image_runner():
    global _image_runner
    if _image_runner is None and _image_video_available:
        from runners.image import ImageRunner
        _image_runner = ImageRunner(resource_manager=_get_resource_manager())
    return _image_runner


def _get_video_runner():
    global _video_runner
    if _video_runner is None and _image_video_available:
        from runners.video import VideoRunner
        _video_runner = VideoRunner(resource_manager=_get_resource_manager())
    return _video_runner


class StoryRequest(BaseModel):
    prompt: str
    system: Optional[str] = None
    max_tokens: int = 4096
    stream: bool = False


class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    language: Optional[str] = None


class ImageRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 512
    height: int = 512


class VideoRequest(BaseModel):
    image_path: str
    prompt: Optional[str] = None
    num_frames: int = 25
    fps: int = 6


async def _stream_story_sse(messages: list[dict], max_tokens: int, temperature: float):
    """SSE: stream raw text deltas so the client can avoid proxy timeouts."""
    _transformer_lock.acquire()
    try:
        for token, _ in transformer.chat_with_metrics(
            messages, max_tokens=max_tokens, temperature=temperature,
        ):
            if token is not None:
                yield f"data: {json.dumps({'delta': token})}\n\n"
                await asyncio.sleep(0)
        yield "data: {\"done\": true}\n\n"
    finally:
        _transformer_lock.release()


@app.post("/api/story")
async def api_story(req: StoryRequest):
    """Generate story/script as JSON. Uses the same LLM. Set stream=true to stream tokens (avoids proxy timeouts)."""
    if not ENABLE_TEXT or transformer is None:
        raise HTTPException(status_code=503, detail="Text model disabled (enable_text=0) or not loaded")
    await ensure_text_loaded()
    if transformer is None:
        raise HTTPException(status_code=503, detail="Text model not loaded")
    system = req.system or "You are a scriptwriter. Respond with valid JSON only: { title, description, hashtags, scenes: [{ text, visualDescription }] }."
    messages = [{"role": "system", "content": system}, {"role": "user", "content": req.prompt}]

    if req.stream:
        return StreamingResponse(
            _stream_story_sse(messages, req.max_tokens, 0.95),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    if not _transformer_lock.acquire(blocking=True, timeout=TRANSFORMER_LOCK_TIMEOUT):
        raise HTTPException(
            status_code=503,
            detail="Model is busy with another request (streaming or generation in progress). Please try again later.",
        )
    try:
        raw = transformer.chat(messages, max_tokens=req.max_tokens, temperature=0.95, stream=False)
        raw = raw.strip()
        if "```json" in raw:
            raw = raw.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in raw:
            raw = raw.split("```", 1)[1].split("```", 1)[0].strip()
        try:
            out = json.loads(raw)
        except json.JSONDecodeError:
            out = {"title": "Untitled", "description": "", "hashtags": [], "scenes": [{"text": raw[:500], "visualDescription": "Scene"}]}
        scenes = out.get("scenes") or []
        if not isinstance(scenes, list):
            scenes = []
        return {"data": {"title": out.get("title") or "Untitled", "description": out.get("description") or "", "hashtags": out.get("hashtags") or [], "scenes": [{"text": s.get("text", ""), "visualDescription": s.get("visualDescription", "")} for s in scenes]}}
    finally:
        _transformer_lock.release()


if _tts_available or _image_video_available:
    @app.post("/api/tts")
    async def api_tts(req: TTSRequest):
        if not ENABLE_TTS:
            raise HTTPException(status_code=503, detail="TTS disabled (enable_tts=0)")
        if not _tts_available:
            raise HTTPException(status_code=503, detail="TTS not available; pip install edge-tts")
        runner = _get_tts_runner()
        path, duration_sec = await runner.generate(req.text, voice_id=req.voice_id, language=req.language)
        return {"audio_path": path, "duration_sec": duration_sec}

if _image_video_available:
    @app.post("/api/image")
    async def api_image(req: ImageRequest):
        if not ENABLE_IMAGE:
            raise HTTPException(status_code=503, detail="Image model disabled (enable_image=0)")
        if not GPU_ALLOW_IMAGE_VIDEO_CONCURRENT:
            vr = _get_video_runner()
            if vr.is_loaded:
                await vr.unload()
        ir = _get_image_runner()
        path = await ir.generate(req.prompt, negative_prompt=req.negative_prompt, width=req.width, height=req.height)
        return {"image_path": path}

    @app.post("/api/video")
    async def api_video(req: VideoRequest):
        if not ENABLE_VIDEO:
            raise HTTPException(status_code=503, detail="Video model disabled (enable_video=0)")
        if not Path(req.image_path).exists():
            raise HTTPException(status_code=400, detail="image_path not found")
        if not GPU_ALLOW_IMAGE_VIDEO_CONCURRENT:
            ir = _get_image_runner()
            if ir.is_loaded:
                await ir.unload()
        vr = _get_video_runner()
        path = await vr.generate(req.image_path, prompt=req.prompt, num_frames=req.num_frames, fps=req.fps)
        return {"video_path": path}


# ---------------------------------------------------------------------------
# OpenAI-compatible /v1 endpoints
# Allows external tools (Claude Code CLI, curl, etc.) to use this backend
# with any OpenAI-compatible client. Wake-up is handled automatically for
# llama-server-backed models (LFM2, etc.).
# ---------------------------------------------------------------------------

class OpenAIMessage(BaseModel):
    """OpenAI-style message; content can be string or array of parts (e.g. VS Code AI Chat)."""
    role: str
    content: Union[str, list[dict[str, Any]]] = ""

    @field_validator("content", mode="before")
    @classmethod
    def content_to_str(cls, v: object) -> str:
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            return " ".join(
                part.get("text", "") for part in v
                if isinstance(part, dict) and part.get("type") == "text"
            )
        return ""


class OpenAIChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: str = ""
    messages: list[OpenAIMessage]
    max_tokens: int = 512
    temperature: float = 0.7
    stream: bool = False


@app.get("/v1/models")
async def openai_list_models():
    """OpenAI-compatible model list."""
    if not ENABLE_TEXT or transformer is None:
        raise HTTPException(status_code=503, detail="Text model disabled (enable_text=0) or not loaded")
    await ensure_text_loaded()
    if transformer is None:
        raise HTTPException(status_code=503, detail="Text model not loaded")
    family = MODEL_FAMILIES.get(MODEL_FAMILY, {})
    return {
        "object": "list",
        "data": [{
            "id": MODEL_FAMILY,
            "object": "model",
            "owned_by": "local",
            "meta": {
                "name": family.get("name", MODEL_FAMILY),
                "quantization": QUANT,
            },
        }],
    }


@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    """
    OpenAI-compatible chat completions endpoint.

    Works with any client that supports a custom base URL (Claude Code CLI,
    OpenAI Python SDK, curl, etc.).  Wakes up llama-server automatically if
    it was idle-stopped.
    """
    if not ENABLE_TEXT or transformer is None:
        raise HTTPException(status_code=503, detail="Text model disabled (enable_text=0) or not loaded")

    await ensure_text_loaded()
    if transformer is None:
        raise HTTPException(status_code=503, detail="Text model not loaded")

    messages = [{"role": m.role, "content": (m.content or "")} for m in request.messages]
    messages = [m for m in messages if m["content"] and isinstance(m["content"], str)]
    if not messages:
        raise HTTPException(status_code=400, detail="At least one message with non-empty content is required")
    user_msg = next((m["content"][:100] for m in messages if m["role"] == "user"), "")
    logger.info(f"[v1] Chat request: stream={request.stream}, max_tokens={request.max_tokens}")
    logger.info(f"[v1] User message: {user_msg}{'...' if len(user_msg) >= 100 else ''}")

    model_name = MODEL_FAMILIES.get(MODEL_FAMILY, {}).get("name", MODEL_FAMILY)
    ts = int(__import__("time").time())

    if request.stream:
        logger.info("[v1] Stream started (waiting for first token). If llama-server was idle, it will load the model now — first token can take 1–2 min for large models.")
        return StreamingResponse(
            openai_stream_chat(messages, request.max_tokens, request.temperature, model_name, ts),
            media_type="text/event-stream",
        )

    # Non-streaming
    if not _transformer_lock.acquire(blocking=True, timeout=TRANSFORMER_LOCK_TIMEOUT):
        raise HTTPException(
            status_code=503,
            detail="Model is busy with another request (streaming or generation in progress). Please try again later.",
        )
    try:
        response_text = transformer.chat(
            messages, max_tokens=request.max_tokens, temperature=request.temperature, stream=False,
        )
        logger.info(f"[v1] Response: {len(response_text)} chars")
        return {
            "id": f"chatcmpl-{ts}",
            "object": "chat.completion",
            "created": ts,
            "model": model_name,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
    finally:
        _transformer_lock.release()


async def openai_stream_chat(
    messages: list[dict], max_tokens: int, temperature: float,
    model_name: str, ts: int,
):
    """SSE generator in OpenAI streaming format."""
    _transformer_lock.acquire()  # hold for entire stream so /api/story etc. get 503 instead of blocking
    try:
        first_token_logged = False
        stream_start = time.time()
        last_status_log = stream_start
        STATUS_INTERVAL = 10  # log "still streaming" every N seconds
        token_count = 0
        logger.info("[v1] Calling model (if cold start: loading + prompt eval can take 1–2 min before first token)...")
        try:
            for token, metrics in transformer.chat_with_metrics(
                messages, max_tokens=max_tokens, temperature=temperature,
            ):
                if token is not None:
                    token_count += 1
                    if not first_token_logged:
                        logger.info("[v1] Streaming output...")
                        first_token_logged = True
                    now = time.time()
                    if now - last_status_log >= STATUS_INTERVAL:
                        elapsed = int(now - stream_start)
                        logger.info("[v1] Still streaming... %ds elapsed, %d tokens so far", elapsed, token_count)
                        last_status_log = now
                    chunk = {
                        "id": f"chatcmpl-{ts}",
                        "object": "chat.completion.chunk",
                        "created": ts,
                        "model": model_name,
                        "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0)
                elif metrics is not None:
                    logger.info(f"[v1] Done: {metrics.completion_tokens} tok, {metrics.tokens_per_second:.1f} tok/s")
                    final = {
                        "id": f"chatcmpl-{ts}",
                        "object": "chat.completion.chunk",
                        "created": ts,
                        "model": model_name,
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    }
                    yield f"data: {json.dumps(final)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"[v1] Stream error: {e}", exc_info=True)
            err = {"error": {"message": str(e), "type": "server_error"}}
            yield f"data: {json.dumps(err)}\n\n"
            yield "data: [DONE]\n\n"
    finally:
        _transformer_lock.release()


# ---------------------------------------------------------------------------
# Anthropic Messages-compatible /v1/messages endpoint
# Lets Claude Code CLI talk to ParleyAI directly — no proxy needed.
# Set ANTHROPIC_BASE_URL=http://localhost:8000 to use.
# ---------------------------------------------------------------------------

class AnthropicMessage(BaseModel):
    role: str
    content: str | list

class AnthropicMessagesRequest(BaseModel):
    model: str = ""
    messages: list[AnthropicMessage]
    max_tokens: int = 512
    temperature: float = 0.7
    stream: bool = False
    system: str | list | None = None
    # Accept and ignore fields Claude Code may send
    model_config = {"extra": "allow"}


def _extract_anthropic_messages(request: AnthropicMessagesRequest) -> list[dict]:
    """Convert Anthropic-format messages to simple role/content dicts."""
    msgs = []
    if request.system:
        system_text = request.system
        if isinstance(system_text, list):
            system_text = "\n".join(
                b["text"] for b in system_text if isinstance(b, dict) and b.get("type") == "text"
            )
        msgs.append({"role": "system", "content": system_text})
    for m in request.messages:
        content = m.content
        if isinstance(content, list):
            content = "\n".join(
                b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text"
            )
        msgs.append({"role": m.role, "content": content})
    return msgs


@app.post("/v1/messages")
async def anthropic_messages(request: AnthropicMessagesRequest):
    """
    Anthropic Messages API compatible endpoint.

    Claude Code CLI sets ANTHROPIC_BASE_URL and sends requests here.
    Wakes up llama-server automatically if it was idle-stopped.
    """
    if not ENABLE_TEXT or transformer is None:
        raise HTTPException(status_code=503, detail="Text model disabled (enable_text=0) or not loaded")

    await ensure_text_loaded()
    if transformer is None:
        raise HTTPException(status_code=503, detail="Text model not loaded")

    messages = _extract_anthropic_messages(request)
    user_msg = next((m["content"][:100] for m in messages if m["role"] == "user"), "")
    logger.info(f"[messages] Chat request: stream={request.stream}, max_tokens={request.max_tokens}")
    logger.info(f"[messages] User message: {user_msg}{'...' if len(user_msg) >= 100 else ''}")

    model_name = MODEL_FAMILIES.get(MODEL_FAMILY, {}).get("name", MODEL_FAMILY)
    msg_id = f"msg_{uuid.uuid4().hex[:24]}"

    if request.stream:
        logger.info("[messages] Stream started (waiting for first token). If llama-server was idle, model load can take 1–2 min.")
        return StreamingResponse(
            anthropic_stream_chat(messages, request.max_tokens, request.temperature, model_name, msg_id),
            media_type="text/event-stream",
        )

    if not _transformer_lock.acquire(blocking=True, timeout=TRANSFORMER_LOCK_TIMEOUT):
        raise HTTPException(
            status_code=503,
            detail="Model is busy with another request (streaming or generation in progress). Please try again later.",
        )
    try:
        response_text = transformer.chat(
            messages, max_tokens=request.max_tokens, temperature=request.temperature, stream=False,
        )
        logger.info(f"[messages] Response: {len(response_text)} chars")
        return {
            "id": msg_id,
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": response_text}],
            "model": model_name,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }
    finally:
        _transformer_lock.release()


async def anthropic_stream_chat(
    messages: list[dict], max_tokens: int, temperature: float,
    model_name: str, msg_id: str,
):
    """SSE generator in Anthropic streaming format."""
    _transformer_lock.acquire()
    try:
        def sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        yield sse("message_start", {
            "type": "message_start",
            "message": {
                "id": msg_id, "type": "message", "role": "assistant",
                "content": [], "model": model_name,
                "stop_reason": None, "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        })
        yield sse("content_block_start", {
            "type": "content_block_start", "index": 0,
            "content_block": {"type": "text", "text": ""},
        })
        yield sse("ping", {"type": "ping"})

        output_tokens = 0
        first_token_logged = False
        stream_start = time.time()
        last_status_log = stream_start
        STATUS_INTERVAL = 10  # log "still streaming" every N seconds
        logger.info("[messages] Calling model (if cold start: loading + prompt eval can take 1–2 min before first token)...")
        try:
            for token, metrics in transformer.chat_with_metrics(
                messages, max_tokens=max_tokens, temperature=temperature,
            ):
                if token is not None:
                    if not first_token_logged:
                        logger.info("[messages] Streaming output...")
                        first_token_logged = True
                    output_tokens += 1
                    now = time.time()
                    if now - last_status_log >= STATUS_INTERVAL:
                        elapsed = int(now - stream_start)
                        logger.info("[messages] Still streaming... %ds elapsed, %d tokens so far", elapsed, output_tokens)
                        last_status_log = now
                    yield sse("content_block_delta", {
                        "type": "content_block_delta", "index": 0,
                        "delta": {"type": "text_delta", "text": token},
                    })
                    await asyncio.sleep(0)
                elif metrics is not None:
                    output_tokens = getattr(metrics, "completion_tokens", output_tokens)
                    logger.info(f"[messages] Done: {output_tokens} tok, {metrics.tokens_per_second:.1f} tok/s")

            yield sse("content_block_stop", {"type": "content_block_stop", "index": 0})
            yield sse("message_delta", {
                "type": "message_delta",
                "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                "usage": {"output_tokens": output_tokens},
            })
            yield sse("message_stop", {"type": "message_stop"})
        except Exception as e:
            logger.error(f"[messages] Stream error: {e}", exc_info=True)
            yield sse("error", {
                "type": "error",
                "error": {"type": "server_error", "message": str(e)},
            })
    finally:
        _transformer_lock.release()


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("port") or os.getenv("PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port)
