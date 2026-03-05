#!/usr/bin/env python3
"""
ParleyAI Backend Server

FastAPI backend providing REST API and Server-Sent Events (SSE) for streaming
chat responses from local GGUF models (Llama 3.3 70B, LFM2-24B, etc.).
"""

import os
import json
import asyncio
import logging
import sys
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


# Configuration from environment
MODEL_FAMILY = os.getenv("MODEL_FAMILY", "Llama-3.3-70B-Instruct")
QUANT = os.getenv("QUANT", "Q4_K_M")
MODEL_PATH_ENV = os.getenv("MODEL_PATH", None)
CTX = int(os.getenv("CTX", "2048"))
GPU_LAYERS = int(os.getenv("GPU_LAYERS", "-1"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "512"))

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

# Global transformer instance
transformer: Optional[LlamaTransformer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the transformer on startup."""
    global transformer
    logger.info("=" * 60)
    logger.info("Initializing Backend Server")
    logger.info("=" * 60)
    logger.info(f"Model family: {MODEL_FAMILY} ({MODEL_FAMILIES.get(MODEL_FAMILY, {}).get('name', '')})")
    logger.info(f"Log file: {log_filename}")
    logger.info(f"Quantization: {QUANT}")
    logger.info(f"Context: {CTX} tokens")
    logger.info(f"Batch Size: {BATCH_SIZE}")
    logger.info(f"GPU Layers: {GPU_LAYERS}")
    logger.info("Optimizations: Flash Attention enabled, KV Offload enabled")
    if MODEL_PATH:
        logger.info(f"Model Path: {MODEL_PATH}")
    
    try:
        transformer = get_transformer(
            quantization=QUANT,
            model_path=MODEL_PATH,
            model_family=MODEL_FAMILY,
            n_ctx=CTX,
            n_gpu_layers=GPU_LAYERS,
            n_batch=BATCH_SIZE,
        )
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
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
        "model_family": MODEL_FAMILY,
        "model": MODEL_FAMILIES.get(MODEL_FAMILY, {}).get("name", MODEL_FAMILY),
        "quantization": QUANT,
        "context_window": CTX,
    }


@app.get("/api/models")
async def list_models():
    """List available quantization options for the current model family."""
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
    if transformer is None:
        logger.error("Chat request received but model not loaded")
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    # Log the request
    user_msg = next((m["content"][:100] for m in messages if m["role"] == "user"), "")
    logger.info(f"Chat request: stream={request.stream}, max_tokens={request.max_tokens}")
    logger.info(f"User message: {user_msg}{'...' if len(user_msg) >= 100 else ''}")
    
    if request.stream:
        return StreamingResponse(
            stream_chat(messages, request.max_tokens, request.temperature),
            media_type="text/event-stream",
        )
    else:
        response = transformer.chat(
            messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=False,
        )
        logger.info(f"Response generated: {len(response)} chars")
        return ChatResponse(response=response)


async def stream_chat(
    messages: list[dict],
    max_tokens: int,
    temperature: float,
):
    """Generator for SSE streaming with performance metrics."""
    logger.info("Starting streaming generation...")
    token_count = 0
    
    try:
        for token, metrics in transformer.chat_with_metrics(
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
        ):
            if token is not None:
                # Streaming token
                token_count += 1
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


@app.post("/api/generate")
async def generate(prompt: str, max_tokens: int = 512, temperature: float = 0.7):
    """Raw text generation endpoint (non-chat format)."""
    if transformer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    response = transformer.generate(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=False,
    )
    return {"response": response}


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
    if transformer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    user_msg = next((m["content"][:100] for m in messages if m["role"] == "user"), "")
    logger.info(f"[v1] Chat request: stream={request.stream}, max_tokens={request.max_tokens}")
    logger.info(f"[v1] User message: {user_msg}{'...' if len(user_msg) >= 100 else ''}")

    model_name = MODEL_FAMILIES.get(MODEL_FAMILY, {}).get("name", MODEL_FAMILY)
    ts = int(__import__("time").time())

    if request.stream:
        return StreamingResponse(
            openai_stream_chat(messages, request.max_tokens, request.temperature, model_name, ts),
            media_type="text/event-stream",
        )

    # Non-streaming
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


async def openai_stream_chat(
    messages: list[dict], max_tokens: int, temperature: float,
    model_name: str, ts: int,
):
    """SSE generator in OpenAI streaming format."""
    try:
        for token, metrics in transformer.chat_with_metrics(
            messages, max_tokens=max_tokens, temperature=temperature,
        ):
            if token is not None:
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
    if transformer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    messages = _extract_anthropic_messages(request)
    user_msg = next((m["content"][:100] for m in messages if m["role"] == "user"), "")
    logger.info(f"[messages] Chat request: stream={request.stream}, max_tokens={request.max_tokens}")
    logger.info(f"[messages] User message: {user_msg}{'...' if len(user_msg) >= 100 else ''}")

    model_name = MODEL_FAMILIES.get(MODEL_FAMILY, {}).get("name", MODEL_FAMILY)
    msg_id = f"msg_{uuid.uuid4().hex[:24]}"

    if request.stream:
        return StreamingResponse(
            anthropic_stream_chat(messages, request.max_tokens, request.temperature, model_name, msg_id),
            media_type="text/event-stream",
        )

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


async def anthropic_stream_chat(
    messages: list[dict], max_tokens: int, temperature: float,
    model_name: str, msg_id: str,
):
    """SSE generator in Anthropic streaming format."""
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
    try:
        for token, metrics in transformer.chat_with_metrics(
            messages, max_tokens=max_tokens, temperature=temperature,
        ):
            if token is not None:
                output_tokens += 1
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


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port)
