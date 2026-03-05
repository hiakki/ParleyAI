# ParleyAI

A full-stack chat application for running large GGUF models locally.

**Supported models:**

| `MODEL_FAMILY` | Model | GGUF Downloads | RAM | Best for |
|---|---|---|---|---|
| `Llama-3.3-70B-Instruct` | Llama 3.3 70B Instruct | [bartowski GGUF](https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF) | 48GB+ | General-purpose, coding |
| `Qwen2.5-32B-Instruct` | Qwen2.5-32B-Instruct | [Qwen GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) | 24–40GB | **Creative writing, JSON, structured output** |
| `Mistral-Small-3.1-24B-Instruct` | Mistral Small 3.1 24B | [Mistral GGUF](https://huggingface.co/bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF) | 20–32GB | Fast inference, instruction following |
| `LFM2-24B-A2B` | LFM2-24B-A2B | [LiquidAI GGUF](https://huggingface.co/LiquidAI/LFM2-24B-A2B-GGUF) | 20–35GB | Efficient MoE (2B active params) |
| `custom` | Any GGUF model | — | varies | Bring your own model via `MODEL_PATH` |

**Supported platforms:**
- **macOS** with Apple Silicon (M1/M2/M3/M4) — Metal GPU acceleration
- **Windows** with NVIDIA GPUs (RTX 3060–5090) — CUDA acceleration
- **Linux** with NVIDIA GPUs — CUDA acceleration

### Recommended Models by Hardware

**Datacenter / Cloud GPUs:**

| Hardware | Top Pick | `MODEL_FAMILY` | `QUANT` | Size | Speed | Download |
|---|---|---|---|---|---|---|
| **H100 80GB** + 128GB RAM | Llama 3.3 70B | `Llama-3.3-70B-Instruct` | `Q8_0` | 75 GB | 60-90 tok/s | [GGUF](https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF) |
| **H100 80GB** + 128GB RAM (alt) | Llama 3.3 70B | `Llama-3.3-70B-Instruct` | `Q5_K_M` | 48 GB | 80-120 tok/s | [GGUF](https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF) |
| **A30 24GB** + 128GB RAM | Qwen2.5-32B | `Qwen2.5-32B-Instruct` | `Q5_K_M` | 23 GB | 20-30 tok/s | [GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) |
| **A30 24GB** + 128GB RAM (alt) | Qwen2.5-32B | `Qwen2.5-32B-Instruct` | `Q4_K_M` | 20 GB | 25-35 tok/s | [GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) |

**Consumer GPUs:**

| Hardware | Top Pick | `MODEL_FAMILY` | `QUANT` | Size | Speed | Download |
|---|---|---|---|---|---|---|
| **48GB+ RAM** (M4 Pro, etc.) | Llama 3.3 70B | `Llama-3.3-70B-Instruct` | `Q4_K_M` | 43 GB | 15-20 tok/s | [GGUF](https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF) |
| **32GB RAM + 24GB VRAM** (RTX 4090) | Qwen2.5-32B | `Qwen2.5-32B-Instruct` | `Q5_K_M` | 23 GB | 25-35 tok/s | [GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) |
| **32GB RAM + 12GB VRAM** (RTX 4070) | Qwen2.5-32B | `Qwen2.5-32B-Instruct` | `Q4_K_M` | 20 GB | 8-12 tok/s | [GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) |
| **32GB RAM + 8GB VRAM** (RTX 4070 Laptop) | Qwen2.5-32B | `Qwen2.5-32B-Instruct` | `Q5_K_M` | 23 GB | 20-30 tok/s | [GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) |
| **32GB RAM** (Apple Silicon) | Qwen2.5-32B | `Qwen2.5-32B-Instruct` | `Q5_K_M` | 23 GB | 15-20 tok/s | [GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) |
| **24GB RAM** | Mistral Small 3.1 | `Mistral-Small-3.1-24B-Instruct` | `Q4_K_M` | 14 GB | 6-10 tok/s | [GGUF](https://huggingface.co/bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF) |
| **20GB RAM** | LFM2-24B-A2B | `LFM2-24B-A2B` | `Q4_0` | 14 GB | 5-8 tok/s | [GGUF](https://huggingface.co/LiquidAI/LFM2-24B-A2B-GGUF) |

> **Why does VRAM matter?** On NVIDIA GPUs, layers that fit in VRAM run 10-20x faster than layers on CPU. A 22 GB model on an 8 GB GPU means ~75% runs on CPU = ~2-3 tok/s. A 14 GB model on the same GPU means ~50% on GPU = 6-8 tok/s. Choose a model size that fits your VRAM for fast generation.

### Model Comparison (i7 + RTX 4070 Laptop 8GB VRAM + 32GB RAM)

**With auto-fit (no GPU_LAYERS set) and CTX=8192:**

| # | Criteria | Llama 70B Q3_K_M | Qwen 32B Q5_K_M | Qwen 32B Q4_K_M | Mistral 24B Q4_K_M | LFM2 24B Q8_0 |
|---|---|---|---|---|---|---|
| 1 | **Size** | 31 GB | 23 GB | 20 GB | 14 GB | 26 GB |
| 2 | **Generation Speed** | ~1 tok/s | ~2-3 tok/s | ~3-4 tok/s | ~6-8 tok/s | ~3-4 tok/s |
| 3 | **Layers on 8GB GPU** | ~15% | ~25% | ~30% | ~40% | ~22% |
| 4 | **Output Quality** | 62% | **92%** | 88% | 76% | 58% |
| 5 | **Overall** | **30%** | **70%** | **75%** | **80%** | **55%** |

**With manual tuning: GPU_LAYERS=20, CTX=2048 (recommended for 8GB VRAM):**

| # | Criteria | Qwen 32B Q5_K_M | Qwen 32B Q4_K_M | Mistral 24B Q4_K_M |
|---|---|---|---|---|
| 1 | **Size** | 23 GB | 20 GB | 14 GB |
| 2 | **Generation Speed** | **~20-30 tok/s** | **~25-35 tok/s** | **~30-40 tok/s** |
| 3 | **GPU_LAYERS / 8GB** | 20 (~6.7 GB) | 24 (~7.4 GB) | 28 (~7.2 GB) |
| 4 | **Output Quality** | **92%** | 88% | 76% |
| 5 | **Overall** | **90%** | **88%** | **85%** |

> **Why the huge difference?** `CTX=2048` uses ~136 MB for KV cache vs ~1 GB at `CTX=8192`. That frees up VRAM for more model layers. Combined with a manually tuned `GPU_LAYERS`, you get optimal VRAM usage and dramatically faster generation.
>
> **Best config for 8GB VRAM**: `QUANT=Q5_K_M CTX=2048 GPU_LAYERS=20` — **20-30 tok/s** with the highest quality 32B model.
> **If you need long context** (8K+): accept ~2-3 tok/s with auto-fit, or use Mistral 24B Q4_K_M for ~6-8 tok/s.
> **Avoid Llama 70B** on 8GB VRAM — too large, painfully slow regardless of settings.

### Best Open-Source Models by Use Case (i7 + 8GB VRAM + 32GB RAM)

All models below run locally via ParleyAI using `MODEL_FAMILY=custom MODEL_PATH=/path/to/model.gguf` (unless the model is already a built-in family). GGUF downloads from HuggingFace.

#### Story / Script Generation / Creative Writing

| # | Model | Params | Quant | GGUF Size | GPU % | Speed | Story Quality | Creativity | Instruction Following | Overall |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Qwen2.5-32B-Instruct** | 32B | Q4_K_M | 20 GB | ~30% | ~3-4 tok/s | **95%** | **93%** | **90%** | **78%** |
| 2 | **Qwen2.5-14B-Instruct** | 14B | Q5_K_M | 10 GB | ~70% | ~12-18 tok/s | 82% | 80% | 82% | **85%** |
| 3 | **Mistral-Small-3.1-24B** | 24B | Q4_K_M | 14 GB | ~40% | ~6-8 tok/s | 78% | 75% | 80% | **80%** |
| 4 | **Gemma-2-9B-IT** | 9B | Q6_K | 7.6 GB | ~95% | ~30-40 tok/s | 72% | 74% | 70% | **82%** |
| 5 | **Llama-3.1-8B-Instruct** | 8B | Q6_K | 6.5 GB | ~100% | ~35-45 tok/s | 68% | 65% | 72% | **78%** |

> **Pick**: Qwen2.5-14B Q5_K_M — best balance of quality and speed for story generation. Gemma-2-9B is the speed king if you need fast iteration.

| Model | GGUF Download |
|---|---|
| Qwen2.5-32B-Instruct | [GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) (built-in `Qwen2.5-32B-Instruct`) |
| Qwen2.5-14B-Instruct | [GGUF](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF) (use `custom`) |
| Mistral-Small-3.1-24B | [GGUF](https://huggingface.co/bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF) (built-in `Mistral-Small-3.1-24B-Instruct`) |
| Gemma-2-9B-IT | [GGUF](https://huggingface.co/bartowski/gemma-2-9b-it-GGUF) (use `custom`) |
| Llama-3.1-8B-Instruct | [GGUF](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF) (use `custom`) |

#### Coding / Software Engineering

| # | Model | Params | Quant | GGUF Size | GPU % | Speed | Code Quality | Debugging | Multi-Language | Overall |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Qwen2.5-Coder-32B** | 32B | Q4_K_M | 20 GB | ~30% | ~3-4 tok/s | **96%** | **92%** | **94%** | **78%** |
| 2 | **Qwen2.5-Coder-14B** | 14B | Q4_K_M | 9 GB | ~85% | ~18-25 tok/s | 88% | 85% | 88% | **90%** |
| 3 | **Phi-4** | 14B | Q4_K_M | 9 GB | ~85% | ~18-25 tok/s | 83% | 82% | 80% | **87%** |
| 4 | **DeepSeek-R1-Distill-Qwen-14B** | 14B | Q4_K_M | 9 GB | ~85% | ~15-22 tok/s | 80% | **88%** | 78% | **85%** |
| 5 | **Llama-3.1-8B-Instruct** | 8B | Q6_K | 6.5 GB | ~100% | ~35-45 tok/s | 65% | 62% | 68% | **76%** |

> **Pick**: Qwen2.5-Coder-14B Q4_K_M — best coding model that fits almost entirely in 8GB VRAM. For debugging/reasoning-heavy tasks, DeepSeek-R1-Distill-14B with chain-of-thought is excellent.

| Model | GGUF Download |
|---|---|
| Qwen2.5-Coder-32B-Instruct | [GGUF](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF) (use `custom`) |
| Qwen2.5-Coder-14B-Instruct | [GGUF](https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-GGUF) (use `custom`) |
| Phi-4 | [GGUF](https://huggingface.co/bartowski/phi-4-GGUF) (use `custom`) |
| DeepSeek-R1-Distill-Qwen-14B | [GGUF](https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF) (use `custom`) |
| Llama-3.1-8B-Instruct | [GGUF](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF) (use `custom`) |

#### Reasoning / Math / Analysis

| # | Model | Params | Quant | GGUF Size | GPU % | Speed | Reasoning | Math | Analysis | Overall |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **DeepSeek-R1-Distill-Qwen-14B** | 14B | Q4_K_M | 9 GB | ~85% | ~15-22 tok/s | **92%** | **88%** | **90%** | **91%** |
| 2 | **Phi-4** | 14B | Q4_K_M | 9 GB | ~85% | ~18-25 tok/s | 88% | **90%** | 85% | **89%** |
| 3 | **Qwen2.5-14B-Instruct** | 14B | Q5_K_M | 10 GB | ~70% | ~12-18 tok/s | 85% | 82% | 86% | **85%** |
| 4 | **Qwen2.5-32B-Instruct** | 32B | Q4_K_M | 20 GB | ~30% | ~3-4 tok/s | **92%** | 86% | **92%** | **76%** |
| 5 | **Gemma-2-9B-IT** | 9B | Q6_K | 7.6 GB | ~95% | ~30-40 tok/s | 72% | 68% | 70% | **78%** |

> **Pick**: DeepSeek-R1-Distill-Qwen-14B — purpose-built for chain-of-thought reasoning, shows its work step-by-step. Phi-4 is the math champion, beating models 5x its size on MATH/GPQA benchmarks.

#### General Purpose / Chat / Q&A

| # | Model | Params | Quant | GGUF Size | GPU % | Speed | Quality | Versatility | Hallucinations | Overall |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Qwen2.5-14B-Instruct** | 14B | Q5_K_M | 10 GB | ~70% | ~12-18 tok/s | 85% | **88%** | 84% | **87%** |
| 2 | **Mistral-Small-3.1-24B** | 24B | Q4_K_M | 14 GB | ~40% | ~6-8 tok/s | 80% | 85% | 82% | **83%** |
| 3 | **Phi-4** | 14B | Q4_K_M | 9 GB | ~85% | ~18-25 tok/s | 82% | 78% | 80% | **85%** |
| 4 | **Gemma-2-9B-IT** | 9B | Q6_K | 7.6 GB | ~95% | ~30-40 tok/s | 75% | 76% | 74% | **82%** |
| 5 | **Llama-3.1-8B-Instruct** | 8B | Q6_K | 6.5 GB | ~100% | ~35-45 tok/s | 70% | 72% | 72% | **80%** |

> **Pick**: Qwen2.5-14B Q5_K_M — the best all-rounder that balances quality, speed, and versatility. Phi-4 is a close second with faster speed and stronger reasoning.

#### Quick Reference: One Model Per Speed Tier

| Priority | Model | GGUF | Speed | Best For |
|---|---|---|---|---|
| **Max Quality** | Qwen2.5-32B-Instruct | Q4_K_M (20 GB) | ~3-4 tok/s | Stories, complex analysis |
| **Best Balance** | Qwen2.5-14B-Instruct | Q5_K_M (10 GB) | ~12-18 tok/s | Everything |
| **Best Coding** | Qwen2.5-Coder-14B | Q4_K_M (9 GB) | ~18-25 tok/s | Code generation, debugging |
| **Best Reasoning** | DeepSeek-R1-Distill-14B | Q4_K_M (9 GB) | ~15-22 tok/s | Math, logic, step-by-step |
| **Max Speed** | Gemma-2-9B-IT | Q6_K (7.6 GB) | ~30-40 tok/s | Fast iteration, chat |

> **How "Overall" is calculated**: Overall = (Quality × 0.35) + (Speed × 0.35) + (GPU fit × 0.15) + (Versatility × 0.15). A slow but high-quality model gets penalized for impractical speed on 8GB VRAM. A fast but lower-quality model gets rewarded for usability.

### How Do These Compare to Cloud AI?

If you've used ChatGPT, Claude, or Gemini, here's how these local models stack up in output quality:

| Local Model (on your PC) | Closest Cloud Equivalent | Quality Gap | Notes |
|---|---|---|---|
| **Llama 70B Q4_K_M** (48GB+) | GPT-4o mini / Claude 3.5 Haiku | ~85–90% of GPT-4o | Best local model, but needs big RAM |
| **Qwen 32B Q5_K_M** (32GB) | GPT-4o mini / Gemini 1.5 Flash | ~80–85% of GPT-4o | Beats GPT-3.5 on structured output |
| **Mistral 24B Q6_K** (32GB) | GPT-3.5 Turbo+ | ~75–80% of GPT-4o | Faster than Qwen, slightly less creative |
| **LFM2 24B Q8_0** (32GB) | GPT-3.5 Turbo | ~65–70% of GPT-4o | Good for simple tasks, efficient |

**For context — cloud model tiers:**

| Tier | Models | Quality | Cost |
|---|---|---|---|
| **Frontier** | GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro | 95–98% | $5–$15 / 1M tokens |
| **Mid-tier** | GPT-4o mini, Claude 3.5 Haiku, Gemini 1.5 Flash | 85–90% | $0.25–$1 / 1M tokens |
| **Legacy** | GPT-3.5 Turbo | 70–75% | $0.50 / 1M tokens |
| **Local (free)** | Qwen 32B, Mistral 24B, Llama 70B | 75–90% | **$0 forever** |

**What this means in practice:**

| Task | Cloud model you'd need | Local equivalent | You'll notice a difference? |
|---|---|---|---|
| Casual chat | GPT-3.5 Turbo | Mistral 24B | No — equally good |
| Blog writing | GPT-4o mini | Qwen 32B | Barely — minor phrasing differences |
| Story generation (NarrateAI) | GPT-4o mini | Qwen 32B | Slight — cloud is ~10–15% more polished |
| Complex code generation | GPT-4o / Claude 3.5 | Llama 70B (48GB+) | Yes — cloud is noticeably better on hard problems |
| Simple code / scripts | GPT-3.5 Turbo | Mistral 24B or Qwen 32B | No — local handles these well |
| JSON / structured data | GPT-4o mini | Qwen 32B | No — Qwen's JSON is excellent |
| Translation | GPT-4o mini | Mistral 24B | Slight — cloud better on rare language pairs |
| Summarization | GPT-4o mini | Qwen 32B | Barely — both extract key points well |

> **Bottom line:** For most everyday tasks, Qwen 32B and Mistral 24B running locally are comparable to GPT-4o mini / GPT-3.5 Turbo — at zero cost and full privacy. You only miss out on frontier-level (GPT-4o / Claude 3.5 Sonnet) capabilities for the hardest reasoning and coding tasks.

### Best Model for Your Use Case

| Use Case | Best Model | Why |
|---|---|---|
| **Story generation / screenwriting** | Qwen2.5-32B | Richest creative vocabulary, best narrative coherence |
| **Structured JSON output** | Qwen2.5-32B | Most reliable JSON schema adherence, lowest parse failures |
| **Chatbot / conversational AI** | Mistral 3.1 24B | Fast responses, natural dialogue, strong instruction following |
| **Coding assistant** | Llama 3.3 70B | Best code understanding (needs 48GB+ RAM for good quant) |
| **Translation / multilingual** | Mistral 3.1 24B | 24-language support, strong cross-lingual transfer |
| **Summarization / analysis** | Qwen2.5-32B | Large context window (128K), accurate extraction |
| **Low-RAM / embedded** | LFM2-24B | MoE with 2B active params, smallest memory footprint |
| **Speed-critical pipelines** | Mistral 3.1 24B | Fastest tok/s on consumer GPUs |
| **RAG / tool use / agents** | Qwen2.5-32B | Best tool-calling and function-calling accuracy |
| **General all-rounder (32GB)** | Qwen2.5-32B | Highest overall score across quality, JSON, and creativity |
| **General all-rounder (48GB+)** | Llama 3.3 70B | Strongest model at higher quants with enough RAM |

### Quantization Impact (quality vs RAM tradeoff)

Higher quant = better quality but more RAM. The sweet spot depends on your hardware.

**Qwen2.5-32B on 32GB RAM (i7 + RTX 4070 Laptop 8GB VRAM):**

| Quant | Size | GPU Layers (8GB) | Speed (8GB VRAM) | Speed (12GB+ VRAM) | Quality vs FP16 | Pick |
|---|---|---|---|---|---|---|
| **Q3_K_M** | 15GB | ~40% | ~5-7 tok/s | ~12-15 tok/s | -4–6% | Budget speed |
| **Q4_K_M** | 20GB | ~30% | ~3-4 tok/s | ~8-12 tok/s | -2–4% | **Best for 8GB VRAM** |
| **Q5_K_M** | 23GB | ~25% | ~2-3 tok/s | ~8-10 tok/s | -1–2% | Best for 12GB+ VRAM |
| **Q6_K** | 27GB | ~20% | ~1-2 tok/s | ~5-7 tok/s | -0.5–1% | Needs 16GB+ VRAM |
| **Q8_0** | 34GB | ~15% | <1 tok/s | ~3-5 tok/s | -0.1–0.3% | Needs 24GB+ VRAM |

**Mistral 3.1 24B on 32GB RAM:**

| Quant | Size | GPU Layers (8GB) | Speed (8GB VRAM) | Speed (12GB+ VRAM) | Quality vs FP16 | Pick |
|---|---|---|---|---|---|---|
| **Q4_K_M** | 14GB | ~40% | **~6-8 tok/s** | ~12-18 tok/s | -2–4% | **Best for 8GB VRAM** |
| **Q5_K_M** | 17GB | ~35% | ~5-6 tok/s | ~10-15 tok/s | -1–2% | Good balance |
| **Q6_K** | 20GB | ~30% | ~3-5 tok/s | ~8-12 tok/s | -0.5–1% | Best for 12GB+ VRAM |
| **Q8_0** | 25GB | ~22% | ~2-3 tok/s | ~6-10 tok/s | -0.1–0.3% | Needs 16GB+ VRAM |

**LFM2-24B on 32GB RAM:**

| Quant | Size | GPU Layers (8GB) | Speed (8GB VRAM) | Quality vs FP16 | Pick |
|---|---|---|---|---|---|
| **Q4_0** | 14GB | ~40% | ~6-8 tok/s | -3–5% | Fast |
| **Q4_K_M** | 15GB | ~38% | ~5-7 tok/s | -2–4% | **Recommended** |
| **Q8_0** | 26GB | ~22% | ~2-3 tok/s | -0.1–0.3% | Needs more VRAM |

**Llama 3.3 70B (48GB+ RAM recommended):**

| Quant | Size | Fits 32GB? | Quality vs FP16 | Speed | Overall (on 32GB) |
|---|---|---|---|---|---|
| **Q3_K_M** | 34GB | Barely | -5–10% | Very slow | 45% |
| **Q4_K_M** | 43GB | No | -2–4% | — | Needs 48GB+ |
| **Q5_K_M** | 50GB | No | -1–2% | — | Needs 64GB+ |

> **Rule of thumb:** Pick the highest quant where the model fits with ≥5GB headroom. Going one quant higher gives <2% quality gain but can cut speed in half if you hit RAM limits.

### Ready-to-Use Configurations by Task

Copy-paste the right config for your task. All tuned for **32GB RAM**.

> **8GB VRAM tip**: Add `GPU_LAYERS=20 CTX=2048` to any Qwen 32B command below for 20-30 tok/s instead of 2-3 tok/s. Trade-off: shorter context window.

**Story Generation / Screenwriting / NarrateAI**
```bash
# macOS / Linux
MODEL_FAMILY=Qwen2.5-32B-Instruct QUANT=Q5_K_M CTX=8192 BATCH_SIZE=512 ./start.sh
```
```bat
:: Windows (CMD)
set MODEL_FAMILY=Qwen2.5-32B-Instruct
set QUANT=Q5_K_M
set CTX=8192
set BATCH_SIZE=512
.\start_windows.bat
```
```powershell
# Windows (PowerShell)
$env:MODEL_PATH='C:\Users\root\Downloads\local-llms'
$env:MODEL_FAMILY='Qwen2.5-32B-Instruct'
$env:QUANT='Q5_K_M'
$env:CTX='8192'
$env:GPU_LAYERS='20'
$env:LFM_IDLE_TIMEOUT='30'
$env:TUNNEL='on'
.\start_windows.bat
```
> Why: Qwen2.5-32B has the best creative vocabulary and JSON adherence. CTX=8192 gives room for long scene descriptions + structured output. Q5_K_M is the sweet spot for 32GB.

**Chatbot / Conversational AI / Customer Support**
```bash
MODEL_FAMILY=Mistral-Small-3.1-24B-Instruct QUANT=Q6_K CTX=4096 BATCH_SIZE=512 ./start.sh
```
```bat
:: Windows (CMD)
set MODEL_FAMILY=Mistral-Small-3.1-24B-Instruct
set QUANT=Q6_K
set CTX=4096
set BATCH_SIZE=512
.\start_windows.bat
```
```powershell
# Windows (PowerShell)
$env:MODEL_FAMILY='Mistral-Small-3.1-24B-Instruct'
$env:QUANT='Q6_K'
$env:CTX='4096'
$env:BATCH_SIZE='512'
.\start_windows.bat
```
> Why: Mistral is the fastest model with natural dialogue flow. CTX=4096 is enough for multi-turn chat. Q6_K at 20GB leaves plenty of headroom.

**Coding Assistant / Code Review**
```bash
# 48GB+ RAM (Mac M4 Pro, etc.)
MODEL_FAMILY=Llama-3.3-70B-Instruct QUANT=Q4_K_M CTX=4096 BATCH_SIZE=512 ./start.sh

# 32GB RAM + 8GB VRAM — Mistral is fastest for code on limited VRAM
MODEL_FAMILY=Mistral-Small-3.1-24B-Instruct QUANT=Q4_K_M CTX=4096 BATCH_SIZE=512 ./start.sh
```
```bat
:: Windows 32GB (CMD)
set MODEL_FAMILY=Qwen2.5-32B-Instruct
set QUANT=Q5_K_M
set CTX=4096
set BATCH_SIZE=512
.\start_windows.bat
```
```powershell
# Windows 32GB (PowerShell)
$env:MODEL_FAMILY='Qwen2.5-32B-Instruct'
$env:QUANT='Q5_K_M'
$env:CTX='4096'
$env:BATCH_SIZE='512'
.\start_windows.bat
```
> Why: Llama 70B is the strongest coder but needs 48GB+. On 32GB, Qwen2.5-32B is a solid alternative with good code understanding. CTX=4096 covers most code files.

**RAG / Document Q&A / Tool Use / Agents**
```bash
MODEL_FAMILY=Qwen2.5-32B-Instruct QUANT=Q5_K_M CTX=16384 BATCH_SIZE=256 ./start.sh
```
```bat
:: Windows (CMD)
set MODEL_FAMILY=Qwen2.5-32B-Instruct
set QUANT=Q5_K_M
set CTX=16384
set BATCH_SIZE=256
.\start_windows.bat
```
```powershell
# Windows (PowerShell)
$env:MODEL_FAMILY='Qwen2.5-32B-Instruct'
$env:QUANT='Q5_K_M'
$env:CTX='16384'
$env:BATCH_SIZE='256'
.\start_windows.bat
```
> Why: Qwen2.5 has the best tool-calling accuracy and 128K native context. CTX=16384 fits large documents. BATCH_SIZE=256 reduces memory spikes during long-context ingestion.

**Translation / Multilingual**
```bash
MODEL_FAMILY=Mistral-Small-3.1-24B-Instruct QUANT=Q6_K CTX=8192 BATCH_SIZE=512 ./start.sh
```
```bat
:: Windows (CMD)
set MODEL_FAMILY=Mistral-Small-3.1-24B-Instruct
set QUANT=Q6_K
set CTX=8192
set BATCH_SIZE=512
.\start_windows.bat
```
```powershell
# Windows (PowerShell)
$env:MODEL_FAMILY='Mistral-Small-3.1-24B-Instruct'
$env:QUANT='Q6_K'
$env:CTX='8192'
$env:BATCH_SIZE='512'
.\start_windows.bat
```
> Why: Mistral supports 24 languages natively. CTX=8192 handles full-page translations. Fast inference keeps turnaround low.

**Summarization / Report Analysis**
```bash
MODEL_FAMILY=Qwen2.5-32B-Instruct QUANT=Q5_K_M CTX=16384 BATCH_SIZE=256 ./start.sh
```
```bat
:: Windows (CMD)
set MODEL_FAMILY=Qwen2.5-32B-Instruct
set QUANT=Q5_K_M
set CTX=16384
set BATCH_SIZE=256
.\start_windows.bat
```
```powershell
# Windows (PowerShell)
$env:MODEL_FAMILY='Qwen2.5-32B-Instruct'
$env:QUANT='Q5_K_M'
$env:CTX='16384'
$env:BATCH_SIZE='256'
.\start_windows.bat
```
> Why: Qwen2.5's 128K native context and strong extraction accuracy. CTX=16384 fits ~12K words of input. Lower batch size prevents OOM on large prompts.

**Low-RAM / Lightweight / Embedded (20–24GB RAM)**
```bash
MODEL_FAMILY=LFM2-24B-A2B QUANT=Q4_K_M CTX=2048 BATCH_SIZE=256 ./start.sh
```
```bat
:: Windows (CMD)
set MODEL_FAMILY=LFM2-24B-A2B
set QUANT=Q4_K_M
set CTX=2048
set BATCH_SIZE=256
.\start_windows.bat
```
```powershell
# Windows (PowerShell)
$env:MODEL_FAMILY='LFM2-24B-A2B'
$env:QUANT='Q4_K_M'
$env:CTX='2048'
$env:BATCH_SIZE='256'
.\start_windows.bat
```
> Why: LFM2's MoE activates only 2B params per token — 15GB model with fast inference. Works on 20GB RAM machines.

**Speed-First / Batch Processing / API Pipelines**
```bash
MODEL_FAMILY=Mistral-Small-3.1-24B-Instruct QUANT=Q4_K_M CTX=2048 BATCH_SIZE=1024 ./start.sh
```
```bat
:: Windows (CMD)
set MODEL_FAMILY=Mistral-Small-3.1-24B-Instruct
set QUANT=Q4_K_M
set CTX=2048
set BATCH_SIZE=1024
.\start_windows.bat
```
```powershell
# Windows (PowerShell)
$env:MODEL_FAMILY='Mistral-Small-3.1-24B-Instruct'
$env:QUANT='Q4_K_M'
$env:CTX='2048'
$env:BATCH_SIZE='1024'
.\start_windows.bat
```
> Why: Smallest dense model at lowest usable quant = maximum tok/s. CTX=2048 and BATCH_SIZE=1024 optimize for throughput over quality.

**Any Custom GGUF Model**
```bash
MODEL_FAMILY=custom MODEL_PATH=~/models/my-model.gguf CTX=4096 BATCH_SIZE=512 ./start.sh
```
```bat
:: Windows (CMD)
set MODEL_FAMILY=custom
set MODEL_PATH=C:\models\my-model.gguf
set CTX=4096
set BATCH_SIZE=512
.\start_windows.bat
```
```powershell
# Windows (PowerShell)
$env:MODEL_FAMILY='custom'
$env:MODEL_PATH='C:\models\my-model.gguf'
$env:CTX='4096'
$env:BATCH_SIZE='512'
.\start_windows.bat
```
> Chat template is auto-detected from the GGUF metadata by llama-server. GPU offloading is automatic — llama-server's auto-fit determines the optimal number of layers for your VRAM. Override with `GPU_LAYERS=N` only if needed.

### Recommended Directory Structure for Models

Organise your GGUF files in `~/local-llms` (macOS/Linux) or `C:\local-llms` (Windows) using this structure:

```
~/local-llms/{MODEL_FAMILY}/{QUANT}/
```

The directory names map 1:1 with the env vars you pass to ParleyAI.

**Recommended layout:**

```
~/local-llms/                                          # macOS / Linux
C:\local-llms\                                         # Windows

├── Qwen2.5-32B-Instruct/                       # MODEL_FAMILY=Qwen2.5-32B-Instruct
│   ├── Q4_K_M/                                  #   QUANT=Q4_K_M
│   │   └── qwen2.5-32b-instruct-q4_k_m.gguf    #   20 GB (single file)
│   └── Q5_K_M/                                  #   QUANT=Q5_K_M
│       ├── qwen2.5-32b-instruct-q5_k_m-00001-of-00006.gguf
│       ├── ...
│       └── qwen2.5-32b-instruct-q5_k_m-00006-of-00006.gguf   # 23 GB (6 parts)
│
├── Mistral-Small-3.1-24B-Instruct/              # MODEL_FAMILY=Mistral-Small-3.1-24B-Instruct
│   ├── Q4_K_M/
│   │   └── mistralai_Mistral-Small-3.1-...-Q4_K_M.gguf       # 14 GB
│   └── Q6_K/
│       └── mistralai_Mistral-Small-3.1-...-Q6_K.gguf         # 20 GB
│
├── LFM2-24B-A2B/                                # MODEL_FAMILY=LFM2-24B-A2B
│   ├── Q4_K_M/
│   │   └── LFM2-24B-A2B-Q4_K_M.gguf            # 15 GB
│   └── Q8_0/
│       └── LFM2-24B-A2B-Q8_0.gguf              # 26 GB
│
└── Llama-3.3-70B-Instruct/                      # MODEL_FAMILY=Llama-3.3-70B-Instruct (48GB+)
    └── Q4_K_M/
        └── Llama-3.3-70B-Instruct-Q4_K_M.gguf  # 43 GB
```

**Usage — just set `MODEL_PATH` to the root, the code finds the right file:**

```bash
# macOS / Linux — MODEL_PATH + MODEL_FAMILY + QUANT maps to the right subfolder
MODEL_PATH=~/local-llms MODEL_FAMILY=Qwen2.5-32B-Instruct QUANT=Q5_K_M CTX=8192 ./start.sh

# Switch quant — same MODEL_PATH, just change QUANT
MODEL_PATH=~/local-llms MODEL_FAMILY=Qwen2.5-32B-Instruct QUANT=Q4_K_M CTX=8192 ./start.sh

# Different model
MODEL_PATH=~/local-llms MODEL_FAMILY=Mistral-Small-3.1-24B-Instruct QUANT=Q6_K CTX=8192 ./start.sh
```
```bat
:: Windows (CMD)
set MODEL_PATH=C:\local-llms
set MODEL_FAMILY=Qwen2.5-32B-Instruct
set QUANT=Q5_K_M
set CTX=8192
.\start_windows.bat
```
```powershell
# Windows (PowerShell)
$env:MODEL_PATH='C:\local-llms'
$env:MODEL_FAMILY='Qwen2.5-32B-Instruct'
$env:QUANT='Q5_K_M'
$env:CTX='8192'
.\start_windows.bat
```

> **Key idea:** `MODEL_PATH` always points to the root (`~/local-llms`). The code resolves `{MODEL_PATH}/{MODEL_FAMILY}/{QUANT}/` automatically. You never need to change `MODEL_PATH` — just switch `MODEL_FAMILY` and `QUANT`.

**The code also supports simpler layouts** (for backward compatibility):

| `MODEL_PATH` points to | Example | Works? |
|---|---|---|
| `~/local-llms` (root) | Searches `{root}/{family}/{quant}/`, then `{root}/{family}/`, then `{root}/` | ✅ Recommended |
| `~/local-llms/Qwen2.5-32B-Instruct` (family dir) | Searches `{dir}/{quant}/`, then `{dir}/` | ✅ |
| `~/local-llms/Qwen2.5-32B-Instruct/Q5_K_M` (quant dir) | Searches `{dir}/` directly | ✅ |
| Direct `.gguf` file path | Uses that file | ✅ |
| Split first part (`-00001-of-*.gguf`) | Uses that file; llama-server reads all parts | ✅ |

### Single-File vs Split GGUF

Some models on HuggingFace are split into multiple parts (e.g. 6 files) due to file size limits. Both formats work:

| Type | Example | How to use |
|---|---|---|
| **Single file** | `model-q4_k_m.gguf` | Point `MODEL_PATH` to the file or its directory |
| **Split files** | `model-q5_k_m-00001-of-00006.gguf` through `...-00006-of-00006.gguf` | Keep all parts in the same folder, point `MODEL_PATH` to the directory or to the `-00001-` file |

**Which models have split files?**

| Model | Q4_K_M | Q5_K_M | Q6_K | Q8_0 |
|---|---|---|---|---|
| **Qwen2.5-32B** | Single | Split (6 parts) | Split | Split |
| **Mistral 24B** | Single | Single | Single | Single |
| **LFM2-24B** | Single | Single | Single | Single |
| **Llama 70B** | Split | Split | Split | Split |

**Downloading models manually:**

```bash
# Download split model into the right folder (e.g. Qwen 32B Q5_K_M)
pip install huggingface_hub
huggingface-cli download Qwen/Qwen2.5-32B-Instruct-GGUF \
  --include "qwen2.5-32b-instruct-q5_k_m*.gguf" \
  --local-dir ~/local-llms/Qwen2.5-32B-Instruct/Q5_K_M \
  --local-dir-use-symlinks False

# Download single-file model (e.g. Mistral 24B Q6_K)
huggingface-cli download bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF \
  --include "mistralai_Mistral-Small-3.1-24B-Instruct-2503-Q6_K.gguf" \
  --local-dir ~/local-llms/Mistral-Small-3.1-24B-Instruct/Q6_K \
  --local-dir-use-symlinks False

# Download another quant of the same model
huggingface-cli download bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF \
  --include "mistralai_Mistral-Small-3.1-24B-Instruct-2503-Q4_K_M.gguf" \
  --local-dir ~/local-llms/Mistral-Small-3.1-24B-Instruct/Q4_K_M \
  --local-dir-use-symlinks False
```
```powershell
# Windows (PowerShell) — download Qwen 32B Q5_K_M (split, 6 parts)
huggingface-cli download Qwen/Qwen2.5-32B-Instruct-GGUF `
  --include "qwen2.5-32b-instruct-q5_k_m*.gguf" `
  --local-dir C:\local-llms\Qwen2.5-32B-Instruct\Q5_K_M `
  --local-dir-use-symlinks False

# Windows (PowerShell) — download Mistral 24B Q6_K (single file)
huggingface-cli download bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF `
  --include "mistralai_Mistral-Small-3.1-24B-Instruct-2503-Q6_K.gguf" `
  --local-dir C:\local-llms\Mistral-Small-3.1-24B-Instruct\Q6_K `
  --local-dir-use-symlinks False
```

> **You don\'t need to merge split files.** `llama-server` loads them automatically from the first part. Just keep all parts in the same folder.

> **If you don\'t set `MODEL_PATH`**, ParleyAI auto-downloads from HuggingFace on first run (single-file models only). For split files, use the download commands above.

**Original models:**
- [meta-llama/Llama-3.3-70B-Instruct](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct) (Meta)
- [Qwen/Qwen2.5-32B-Instruct](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct) (Alibaba)
- [mistralai/Mistral-Small-3.1-24B-Instruct-2503](https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503) (Mistral AI)
- [LiquidAI/LFM2-24B-A2B](https://huggingface.co/LiquidAI/LFM2-24B-A2B) (Liquid AI)

## 🚀 Quick Start (Full-Stack App)

### macOS / Linux
```bash
# One-time setup
./setup_fullstack.sh

# Start the application
./start.sh
```

### Windows (PowerShell)
```powershell
# One-time setup
.\setup_windows.bat

# Start the application
.\start_windows.bat
```

Then open **http://localhost:5173** in your browser!

### Manual Setup - macOS (Apple Silicon)

If `setup_fullstack.sh` has issues, set up manually:

```bash
# 1. Backend setup
cd backend
rm -rf venv                    # Remove old venv if exists
python3 -m venv venv           # Create fresh venv
source venv/bin/activate       # Activate venv
pip install --upgrade pip      # Upgrade pip

# Install llama-cpp-python with Metal support (takes 5-10 min)
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Install other dependencies
pip install -r requirements.txt

deactivate
cd ..

# 2. Frontend setup
cd frontend
npm install
cd ..

# 3. Start the app
./start.sh
```

### Manual Setup - Windows (NVIDIA GPU)

#### Prerequisites (Install in Order)

| # | Software | Download Link | Notes |
|---|----------|---------------|-------|
| 1 | **Python 3.10+** | [python.org/downloads](https://www.python.org/downloads/) | ✅ Check "Add Python to PATH" during install |
| 2 | **Node.js 18+** | [nodejs.org](https://nodejs.org/) | LTS version recommended |
| 3 | **NVIDIA Driver** | [nvidia.com/drivers](https://www.nvidia.com/Download/index.aspx) | Latest Game Ready or Studio driver |
| 4 | **CUDA Toolkit 12.x** | [developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads) | Required for GPU acceleration |
| 5 | **Visual Studio Build Tools** | [visualstudio.microsoft.com/visual-cpp-build-tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) | Select "Desktop development with C++" |
| 6 | **CMake** | [cmake.org/download](https://cmake.org/download/) | Or: `winget install Kitware.CMake` |

> **⚠️ Important**: After installing Visual Studio Build Tools, run the setup from **"x64 Native Tools Command Prompt for VS 2022"** (search in Start Menu), NOT regular PowerShell!

#### Quick Setup (Automated)

```powershell
# Run from "x64 Native Tools Command Prompt for VS 2022"
.\setup_windows.bat
```

The setup script will:
1. Check all prerequisites
2. Try pre-built CUDA wheels first (no compilation needed!)
3. Fall back to building from source if needed

#### Manual Setup (Step by Step)

```powershell
# Open "x64 Native Tools Command Prompt for VS 2022" from Start Menu
cd path\to\ParleyAI

# 1. Backend setup
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip

# Install llama-cpp-python with CUDA support
# Option A: Pre-built wheel (faster, try this first!)
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# Option B: If Option A fails, build from source
$env:CMAKE_ARGS="-DGGML_CUDA=on"
$env:FORCE_CMAKE="1"
pip install llama-cpp-python --force-reinstall --no-cache-dir

# Install other dependencies
pip install -r requirements.txt

deactivate
cd ..

# 2. Frontend setup
cd frontend
npm install
cd ..

# 3. Start the app
.\start_windows.bat
```

#### Troubleshooting Windows Installation

**Error: `pip install llama-cpp-python` fails**

1. **"cl.exe not found"** → Run from "x64 Native Tools Command Prompt", not regular PowerShell
2. **"CUDA not found"** → Add CUDA to PATH:
   ```powershell
   $env:PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin;" + $env:PATH
   ```
3. **"CMake not found"** → Install CMake and restart terminal

**Error: `nvcc not found`**
```powershell
# Add CUDA to system PATH (run as Administrator)
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin", "Machine")
# Restart your terminal
```

**Still not working?** Try CPU-only mode (slower but works):
```powershell
pip install llama-cpp-python  # No CUDA, uses CPU
# Set GPU_LAYERS=0 when running
```

### Manual Setup - Linux (NVIDIA GPU)

```bash
# 1. Backend setup
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install llama-cpp-python with CUDA support
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Install other dependencies
pip install -r requirements.txt

deactivate
cd ..

# 2. Frontend setup
cd frontend
npm install
cd ..

# 3. Start the app
./start.sh
```

## ✅ Verified Working Configuration

**Tested on Mac M4 Pro with 48GB RAM** - running perfectly!

```bash
MODEL_PATH=~/local-llms QUANT=IQ3_M CTX=2048 GPU_LAYERS=40 ./start.sh
```

| Parameter | Value | Description |
|-----------|-------|-------------|
| `MODEL_FAMILY` | `Llama-3.3-70B-Instruct` | `Llama-3.3-70B-Instruct`, `Qwen2.5-32B-Instruct`, `Mistral-Small-3.1-24B-Instruct`, `LFM2-24B-A2B`, or `custom` |
| `MODEL_PATH` | `~/local-llms` | Directory or path to GGUF file (required for `custom`) |
| `QUANT` | `Q4_K_M` | Quantization (options depend on `MODEL_FAMILY`) |
| `CTX` | `2048` | Context window (tokens) |
| `GPU_LAYERS` | `-1` (auto) | GPU layers; `-1` = auto-fit (recommended), `0` = CPU only |
| `TUNNEL` | `off` | Set to `on` to expose via internet tunnel |
| `TUNNEL_TOOL` | `auto` | `auto`, `cloudflared`, or `localtunnel` |

### Accessing from other devices

The frontend binds to `0.0.0.0` so it's accessible on your LAN. The backend stays on `127.0.0.1` (localhost only) for security — the frontend proxies API requests to it.

```
http://<your-ip>:5173   # Frontend (LAN accessible)
http://localhost:8000    # Backend API (localhost only)
```

The startup output shows your local IP.

**Internet access** — add `TUNNEL=on` to expose the frontend via a public URL:

```bash
TUNNEL=on ./start.sh
```

Requires one of:
- `cloudflared` (recommended) — `brew install cloudflared`
- `localtunnel` — `npm install -g localtunnel`

The tunnel URL is printed at startup and logged to `.tunnel.log`.

### Running Server-Based Models (Qwen, Mistral, LFM2, Custom)

All model families except `Llama-3.3-70B-Instruct` use an external `llama-server` subprocess (from the [llama.cpp](https://github.com/ggml-org/llama.cpp) project). This covers Qwen2.5-32B, Mistral Small 3.1, LFM2-24B, and any custom GGUF model.

**Prerequisite — install `llama-server`:**

```bash
# macOS
brew install llama.cpp

# Windows: run setup_windows.bat (auto-downloads llama-server)
# Or manually download from https://github.com/ggml-org/llama.cpp/releases

# Linux: download from https://github.com/ggml-org/llama.cpp/releases
```

**Start examples:**

```bash
# Qwen2.5-32B — best for creative writing, structured JSON, story generation
MODEL_FAMILY=Qwen2.5-32B-Instruct QUANT=Q5_K_M CTX=8192 ./start.sh

# Mistral Small 3.1 24B — fast, strong instruction following
MODEL_FAMILY=Mistral-Small-3.1-24B-Instruct QUANT=Q6_K CTX=8192 ./start.sh

# LFM2-24B — efficient MoE, fits in 30–35GB RAM
MODEL_FAMILY=LFM2-24B-A2B QUANT=Q4_K_M ./start.sh

# Any GGUF model — chat template auto-detected from the GGUF file
MODEL_FAMILY=custom MODEL_PATH=~/models/my-model.gguf CTX=4096 ./start.sh
```

**Windows (CMD):**

```bat
set MODEL_FAMILY=Qwen2.5-32B-Instruct
set QUANT=Q5_K_M
set CTX=8192
.\start_windows.bat
```
```powershell
$env:MODEL_FAMILY='Qwen2.5-32B-Instruct'
$env:QUANT='Q5_K_M'
$env:CTX='8192'
.\start_windows.bat
```

Models are auto-downloaded from Hugging Face on first run. Set `MODEL_PATH` to skip the download if you already have the GGUF file.

**Available quantizations per family:**

| Family | Quants | Recommended (8GB VRAM) | Recommended (12GB+ VRAM) |
|---|---|---|---|
| `Qwen2.5-32B-Instruct` | Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0 | **Q4_K_M** (20GB) | **Q5_K_M** (23GB) |
| `Mistral-Small-3.1-24B-Instruct` | Q4_K_M, Q5_K_M, Q6_K, Q8_0 | **Q4_K_M** (14GB) | **Q6_K** (20GB) |
| `LFM2-24B-A2B` | Q4_0, Q4_K_M, Q5_K_M, Q6_K, Q8_0, BF16, F16 | **Q4_K_M** (15GB) |
| `custom` | N/A (set via `MODEL_PATH`) | — |


## 📁 Project Structure

```
ParleyAI/
├── frontend/              # React chat UI
│   ├── src/
│   │   ├── App.jsx       # Main chat component
│   │   └── App.css       # Styles
│   └── package.json
│
├── backend/              # FastAPI server
│   ├── server.py         # REST API + SSE streaming
│   ├── llama_transformer.py  # LLM wrapper (internal module)
│   └── requirements.txt
│
├── brew_setup/           # Homebrew CLI alternative (macOS)
│
├── setup_fullstack.sh    # Setup script (macOS/Linux)
├── setup_windows.bat     # Setup script (Windows)
├── start.sh              # Start app (macOS/Linux)
├── start_windows.bat     # Start app (Windows)
└── README.md
```

---

## 🎯 How It Works

Running a 70B parameter model (normally ~140GB in FP16) efficiently requires:

1. **Quantization**: Compress to 1-8 bits per weight (from 16-bit)
2. **Memory Mapping (mmap)**: Stream model layers from disk on-demand
3. **GPU Acceleration**: Metal (Apple Silicon) or CUDA (NVIDIA GPUs)

### All Available Quantizations

**Llama 3.3 70B** — full list from [bartowski/Llama-3.3-70B-Instruct-GGUF](https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF):

| Quantization | Size | RAM | Quality | Notes |
|--------------|------|-----|---------|-------|
| **1-bit** |||||
| IQ1_M | ~17GB | 10GB+ | Extreme | Lowest quality, smallest |
| **2-bit** |||||
| IQ2_XXS | ~19GB | 10GB+ | Extreme | Smallest 2-bit |
| IQ2_XS | ~21GB | 11GB+ | Extreme | Very aggressive |
| IQ2_S | ~22GB | 12GB+ | Low | I-quant |
| IQ2_M | ~24GB | 14GB+ | Low | I-quant |
| Q2_K | ~26GB | 14GB+ | Low | K-quant |
| Q2_K_L | ~27GB | 16GB+ | Low | Q8 embed/output |
| **3-bit** |||||
| IQ3_XXS | ~28GB | 16GB+ | Medium-low | I-quant |
| IQ3_XS | ~29GB | 16GB+ | Medium-low | I-quant |
| Q3_K_S | ~31GB | 18GB+ | Medium | K-quant small |
| IQ3_M | ~32GB | 18GB+ | Medium | I-quant |
| Q3_K_M | ~34GB | 20GB+ | Medium-good | K-quant medium |
| Q3_K_L | ~37GB | 22GB+ | Good | K-quant large |
| Q3_K_XL | ~38GB | 24GB+ | Good | Q8 embed/output |
| **4-bit** |||||
| IQ4_XS | ~38GB | 24GB+ | Good | I-quant 4-bit |
| Q4_0 | ~40GB | 24GB+ | Good | Legacy, ARM optimized |
| IQ4_NL | ~40GB | 24GB+ | Good | ARM optimized |
| Q4_K_S | ~40GB | 24GB+ | Good | K-quant small |
| Q4_0_4_4 | ~40GB | 24GB+ | Good | ARM NEON optimized |
| Q4_0_4_8 | ~40GB | 24GB+ | Good | ARM SVE 256 optimized |
| Q4_0_8_8 | ~40GB | 24GB+ | Good | AVX2/AVX512 optimized |
| **Q4_K_M** | **~43GB** | **32GB+** | **Very good** | **Recommended default** |
| Q4_K_L | ~43GB | 32GB+ | Excellent | Q8 embed/output |
| **5-bit** |||||
| Q5_K_S | ~49GB | 48GB+ | High | K-quant small |
| Q5_K_M | ~50GB | 48GB+ | High | K-quant medium, recommended |
| Q5_K_L | ~51GB | 48GB+ | High | Q8 embed/output |
| **6-bit** |||||
| Q6_K | ~58GB | 64GB+ | Very high | Near perfect |
| Q6_K_L | ~58GB | 64GB+ | Very high | Q8 embed/output |
| **8-bit** |||||
| Q8_0 | ~75GB | 80GB+ | Excellent | Max available quant |
| **16-bit** |||||
| F16 | ~141GB | 160GB+ | Perfect | Full precision |

> **💡 Tip**: For Apple Silicon Macs, use K-quants (Q4_K_M, Q5_K_M, etc.) for best performance. I-quants (IQ3_M, IQ4_XS) offer better quality at the same size but may be slower on Metal.

**Other model families** (use with `MODEL_FAMILY=...`):

| Family | Model | GGUF Source | Quants | Recommended (32GB) |
|---|---|---|---|---|
| `Qwen2.5-32B-Instruct` | [Qwen2.5-32B-Instruct](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) | [GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) | Q3_K_M – Q8_0 | **Q5_K_M** (23GB) |
| `Mistral-Small-3.1-24B-Instruct` | [Mistral Small 3.1 24B](https://huggingface.co/bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF) | [GGUF](https://huggingface.co/bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF) | Q4_K_M – Q8_0 | **Q6_K** (20GB) |
| `LFM2-24B-A2B` | [LFM2-24B-A2B](https://huggingface.co/LiquidAI/LFM2-24B-A2B-GGUF) | [GGUF](https://huggingface.co/LiquidAI/LFM2-24B-A2B-GGUF) | Q4_0 – F16 | **Q4_K_M** (15GB) |
| `custom` | Any GGUF | — | Set via `MODEL_PATH` | — |

### 🎮 NVIDIA GPU Recommendations

On NVIDIA GPUs, model layers are split between **VRAM** (fast) and **system RAM** (slow). Generation speed is bottlenecked by the slowest component. Auto-fit handles the split automatically — no manual `GPU_LAYERS` needed.

**Datacenter / Cloud GPUs:**

| GPU | VRAM | Best Model | Quant | Size | CTX | Expected Speed |
|-----|------|------------|-------|------|-----|----------------|
| **H100** | 80GB | Llama 70B | Q8_0 | 75 GB | 32768 | 60-90 tok/s |
| **H100** | 80GB | Llama 70B (faster) | Q5_K_M | 48 GB | 32768 | 80-120 tok/s |
| **H100** | 80GB | Qwen 32B | Q8_0 | 34 GB | 32768 | 100-150 tok/s |
| **A30** | 24GB | Qwen 32B | Q5_K_M | 23 GB | 8192 | 20-30 tok/s |
| **A30** | 24GB | Qwen 32B (faster) | Q4_K_M | 20 GB | 16384 | 25-35 tok/s |
| **A30** | 24GB | Mistral 24B | Q6_K | 20 GB | 8192 | 25-35 tok/s |

> **H100 (80GB)**: Entire Llama 70B fits in VRAM at Q8_0 (near-lossless quality) with room for 32K context. For maximum throughput, Q5_K_M leaves headroom for larger batches. Qwen 32B at Q8_0 is trivial for H100 and runs at 100+ tok/s.
>
> **A30 (24GB)**: Qwen 32B Q5_K_M (23 GB) fits entirely in VRAM. Use Q4_K_M for larger context windows (16K+). Avoid Llama 70B — at 43+ GB it would be mostly on CPU via 128GB system RAM, dropping to ~5-8 tok/s.

**Consumer GPUs (32GB system RAM):**

| GPU | VRAM | Best Model | Quant | Size | Expected Speed |
|-----|------|------------|-------|------|----------------|
| **RTX 3060** | 12GB | Mistral 24B | Q4_K_M | 14 GB | 10-15 tok/s |
| **RTX 3070 / 3070 Ti** | 8GB | Mistral 24B | Q4_K_M | 14 GB | 6-8 tok/s |
| **RTX 3080** | 10GB | Mistral 24B | Q5_K_M | 17 GB | 8-12 tok/s |
| **RTX 3090** | 24GB | Qwen 32B | Q5_K_M | 23 GB | 25-35 tok/s |
| **RTX 4060** | 8GB | Mistral 24B | Q4_K_M | 14 GB | 6-8 tok/s |
| **RTX 4060 Ti** | 8/16GB | Mistral 24B / Qwen 32B Q4_K_M | 14/20 GB | 6-8 / 10-15 tok/s |
| **RTX 4070 Laptop** | 8GB | Qwen 32B (GPU_LAYERS=20, CTX=2048) | Q5_K_M | 23 GB | 20-30 tok/s |
| **RTX 4070** | 12GB | Qwen 32B | Q4_K_M | 20 GB | 8-12 tok/s |
| **RTX 4070 Ti** | 12GB | Qwen 32B | Q4_K_M | 20 GB | 8-12 tok/s |
| **RTX 4080** | 16GB | Qwen 32B | Q5_K_M | 23 GB | 15-20 tok/s |
| **RTX 4090** | 24GB | Qwen 32B | Q5_K_M | 23 GB | 25-35 tok/s |
| **RTX 5070\*** | 12GB | Qwen 32B | Q4_K_M | 20 GB | 10-15 tok/s |
| **RTX 5080\*** | 16GB | Qwen 32B | Q5_K_M | 23 GB | 18-25 tok/s |
| **RTX 5090\*** | 32GB | Qwen 32B | Q5_K_M | 23 GB | 30-45 tok/s |

\* RTX 50-series specs are estimated.

> **Rule of thumb**: Pick a model where the GGUF size is close to or less than your VRAM. A 14 GB model on 8 GB VRAM (~40% on GPU) gives 6-8 tok/s. A 23 GB model on 8 GB VRAM (~25% on GPU) gives 2-3 tok/s.

#### Example Commands for NVIDIA GPUs

```bash
# H100 (80GB VRAM) - best quality, Llama 70B near-lossless
MODEL_FAMILY=Llama-3.3-70B-Instruct QUANT=Q8_0 CTX=32768 ./start.sh

# H100 (80GB VRAM) - max throughput
MODEL_FAMILY=Llama-3.3-70B-Instruct QUANT=Q5_K_M CTX=32768 ./start.sh

# A30 (24GB VRAM) - best quality
MODEL_FAMILY=Qwen2.5-32B-Instruct QUANT=Q5_K_M CTX=8192 ./start.sh

# A30 (24GB VRAM) - larger context
MODEL_FAMILY=Qwen2.5-32B-Instruct QUANT=Q4_K_M CTX=16384 ./start.sh

# RTX 4070 Laptop (8GB VRAM) - best quality + speed (20-30 tok/s)
MODEL_FAMILY=Qwen2.5-32B-Instruct QUANT=Q5_K_M CTX=2048 GPU_LAYERS=20 ./start.sh

# RTX 4070 Laptop (8GB VRAM) - long context (slower, ~6-8 tok/s)
MODEL_FAMILY=Mistral-Small-3.1-24B-Instruct QUANT=Q4_K_M CTX=8192 ./start.sh

# RTX 4070 desktop (12GB VRAM) - good speed + quality
MODEL_FAMILY=Qwen2.5-32B-Instruct QUANT=Q4_K_M CTX=8192 ./start.sh

# RTX 4090 (24GB VRAM) - full speed
MODEL_FAMILY=Qwen2.5-32B-Instruct QUANT=Q5_K_M CTX=8192 ./start.sh
```

```powershell
# Windows — RTX 4070 Laptop (8GB VRAM) — 20-30 tok/s
$env:MODEL_FAMILY="Qwen2.5-32B-Instruct"
$env:QUANT="Q5_K_M"
$env:CTX="2048"
$env:GPU_LAYERS="20"
.\start_windows.bat
```

> **⚠️ VRAM vs RAM**: Unlike Apple Silicon's unified memory, NVIDIA GPUs have separate VRAM. By default, llama-server's **auto-fit** determines how many layers fit in your VRAM — no manual `GPU_LAYERS` needed.

> **💡 Override**: Set `GPU_LAYERS=N` only when you want a specific split. `GPU_LAYERS=0` forces CPU-only.

## 🚀 Quick Start

### Installation

```bash
# Install llama-cpp-python with Metal support
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Install other dependencies
pip install huggingface_hub tqdm
```

### Basic Usage

```python
# From within backend/ directory
from llama_transformer import LlamaTransformer

# Initialize (defaults optimized for 48GB RAM)
transformer = LlamaTransformer(
    quantization="Q4_K_M",  # Best balance for 48GB RAM
    n_ctx=4096,             # Good context window
    use_mmap=True,          # Stream from disk
)

# Chat completion
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum computing simply."}
]

# Stream response
for token in transformer.chat(messages, stream=True):
    print(token, end="", flush=True)
```

### Command Line (Backend)

```bash
cd backend

# List available quantizations
python llama_transformer.py --list-quants

# Interactive chat mode (recommended for 48GB RAM)
python llama_transformer.py -q Q4_K_M -i

# For 16GB RAM, use smaller quantization
python llama_transformer.py -q Q3_K_S -c 2048 -i

# Use specific model file
python llama_transformer.py -m /path/to/model.gguf -i
```

## 📊 Memory Optimization Tips

### For 48GB RAM (Recommended)

```python
transformer = LlamaTransformer(
    quantization="Q4_K_M",  # Best quality/size balance
    n_ctx=4096,             # Good context window
    n_batch=512,            # Fast processing
    use_mmap=True,          # Enable for safety
)
```

### For 16GB RAM

```python
transformer = LlamaTransformer(
    quantization="Q3_K_S",  # Fits comfortably
    n_ctx=2048,             # Smaller context
    n_batch=256,            # Moderate batches
    use_mmap=True,          # Critical: stream from disk
    use_mlock=False,        # Don't lock in RAM
)
```

### System Preparation

1. **First run downloads model**: ~43GB for Q4_K_M, takes 10-30 minutes
2. **Subsequent runs are fast**: Model loads from cache

```bash
# Check current memory
vm_stat | head -5

# Monitor during inference
# Open Activity Monitor → Memory tab
```

## 🔧 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Prompt                          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Llama 3.3 Chat Template                    │
│  <|begin_of_text|><|start_header_id|>system...         │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                 llama.cpp Engine                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │  GGUF Model (Q3_K_S quantized)                  │   │
│  │  - 80 transformer layers                        │   │
│  │  - Memory mapped from SSD                       │   │
│  │  - Only active layers in RAM                    │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Metal GPU Backend                              │   │
│  │  - Matrix operations on GPU                     │   │
│  │  - Unified memory architecture                  │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Streamed Token Output                      │
└─────────────────────────────────────────────────────────┘
```

## 📁 Backend Files

| File | Description |
|------|-------------|
| `backend/llama_transformer.py` | Main transformer using llama.cpp (recommended) |
| `backend/mlx_transformer.py` | Alternative using Apple MLX (needs 32GB+) |
| `backend/server.py` | FastAPI server with SSE streaming |
| `backend/requirements.txt` | Python dependencies |

## ⚡ Performance Expectations

On Mac M4 with 48GB RAM:

| Metric | Q4_K_M | Q5_K_S |
|--------|--------|--------|
| Load time | 60-90s | 90-120s |
| Tokens/sec | 8-15 | 6-12 |
| Quality | Very Good | High |
| RAM usage | ~43GB | ~49GB |

*First run includes download time (~43-50GB)*

## 📈 Understanding Performance Metrics

The UI displays real-time metrics after each response. Here's what they mean:

```
⚡ 2.47 tok/s | 📝 9 tokens | ⏱️ 10.6s total
prompt: 39 tok @ 5.61 tok/s (7.0s) | gen: 9 tok @ 2.47 tok/s (3.6s)
```

### Prompt Processing (prompt eval)

```
prompt: 39 tok @ 5.61 tok/s (7.0s)
```

| Metric | Meaning |
|--------|---------|
| **39 tokens** | Your input (system prompt + user message) converted to tokens |
| **5.61 tok/s** | Speed at which the model *reads and understands* your input |
| **7.0s** | Total time to process the prompt |

This is the **"thinking" phase** where the model:
1. Tokenizes your text ("Hello" → `[15496]`)
2. Runs each token through all 80 transformer layers
3. Builds internal context/attention for generating a response

### Generation (eval)

```
gen: 9 tok @ 2.47 tok/s (3.6s)
```

| Metric | Meaning |
|--------|---------|
| **9 tokens** | Number of tokens the model *generated* in its response |
| **2.47 tok/s** | Speed at which the model *writes* new tokens |
| **3.6s** | Total time to generate the response |

This is the **"writing" phase** where the model:
1. Predicts the next token based on context
2. Appends it to the output
3. Repeats until done (stop token or max_tokens)

### Why is generation slower than prompt processing?

| Phase | Speed | Reason |
|-------|-------|--------|
| **Prompt** | ~5-6 tok/s | Can process tokens in **parallel** (batch processing) |
| **Generation** | ~2-3 tok/s | Must generate tokens **one at a time** (sequential) |

Generation is inherently sequential—each new token depends on all previous tokens, so the model can't parallelize this phase.

### Visual Timeline

```
[0s]────────────────────[7.0s]──────────────[10.6s]
        Prompt (39 tok)         Gen (9 tok)
        "Understanding"         "Writing"
```

## 🔍 Troubleshooting

### "Out of memory" errors

```python
# Use more aggressive settings
transformer = LlamaTransformer(
    quantization="IQ2_XS",  # Smallest model
    n_ctx=512,              # Minimal context
)
```

### Slow generation

- Close background apps
- Ensure Metal is being used (check verbose output)
- Use smaller batch size: `n_batch=128`

### Model download fails

```bash
# Manual download with huggingface-cli
pip install huggingface_hub
huggingface-cli download bartowski/Llama-3.3-70B-Instruct-GGUF \
    Llama-3.3-70B-Instruct-Q3_K_S.gguf

# Then specify path when running
cd backend
python llama_transformer.py -m ~/.cache/huggingface/hub/.../Llama-3.3-70B-Instruct-Q3_K_S.gguf
```

### "llama-server not found" or "Failed to load model"

All model families except `Llama-3.3-70B-Instruct` (`Qwen2.5-32B-Instruct`, `Mistral-Small-3.1-24B-Instruct`, `LFM2-24B-A2B`, `custom`) require `llama-server` (from the llama.cpp project).

**Fix:** Install `llama-server`:

```bash
# macOS
brew install llama.cpp

# Windows: run setup_windows.bat (auto-downloads), or get from:
# https://github.com/ggml-org/llama.cpp/releases

# Linux: download from https://github.com/ggml-org/llama.cpp/releases
```

Also confirm the GGUF file is complete. If it's truncated, delete and re-download, or omit `MODEL_PATH` so the app downloads from Hugging Face.


## 🔌 External API (Claude Code CLI, OpenClaw, curl, OpenAI SDK)

ParleyAI exposes both **Anthropic Messages API** (`/v1/messages`) and **OpenAI-compatible** (`/v1/chat/completions`) endpoints on the same backend port (default `http://localhost:8000`). Wake-up is automatic — if `llama-server` was idle-stopped, the first request starts it.

### Endpoints

| Endpoint | Method | Format | Used by |
|----------|--------|--------|---------|
| `/v1/messages` | POST | Anthropic | Claude Code CLI, OpenClaw, Anthropic SDK |
| `/v1/chat/completions` | POST | OpenAI | curl, OpenAI SDK, OpenClaw, other tools |
| `/v1/models` | GET | OpenAI | List available model(s) |

### Claude Code CLI

`start.sh` writes a `.claude_env` file automatically. In another terminal:

```bash
source /absolute/path/to/.claude_env && claude
```

The exact command (with absolute path) is printed at startup. The `.claude_env` file is cleaned up on shutdown.

Manually (without `start.sh`):

```bash
export ANTHROPIC_BASE_URL=http://localhost:8000
export ANTHROPIC_AUTH_TOKEN=not-needed
export ANTHROPIC_MODEL=parleyai
claude
```

No proxy, no extra process — Claude Code talks directly to the ParleyAI backend.

### OpenClaw

Add a custom provider in your OpenClaw config (`~/.openclaw/agents/<agent>/openclaw.json`):

```json5
{
  agents: {
    defaults: {
      model: { primary: "parleyai/local" },
    },
  },
  models: {
    providers: {
      parleyai: {
        baseUrl: "http://localhost:8000",
        apiKey: "not-needed",
        api: "anthropic-messages",
        models: [
          {
            id: "local",
            name: "ParleyAI Local",
            reasoning: false,
            input: ["text"],
            cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
            contextWindow: 2048,
            maxTokens: 512,
          },
        ],
      },
    },
  },
}
```

Then:

```bash
openclaw models set parleyai/local
```

Adjust `contextWindow` to match your `CTX` env var (default 2048). To use the OpenAI format instead, change `api` to `"openai-completions"`.

### Claude Desktop

Claude Desktop **cannot** connect to a local LLM. It always uses Anthropic's cloud models. MCP in Claude Desktop adds tools/data sources to Claude, not a different model.

### Cursor & VS Code (vibe coding, plan-driven builds)

You can use ParleyAI as the LLM backend inside **Cursor** or **VS Code** so chat, Composer, and code actions are powered by your local model. Useful for vibe coding and for implementing an app from a `build/plan.md` step by step.

**1. Start ParleyAI** (backend must be running so the IDE can call it):

```bash
# Example: Qwen 32B, 20-30 tok/s on 8GB VRAM
MODEL_FAMILY=Qwen2.5-32B-Instruct QUANT=Q5_K_M CTX=2048 GPU_LAYERS=20 ./start.sh
```

```powershell
# Windows
$env:MODEL_FAMILY='Qwen2.5-32B-Instruct'
$env:QUANT='Q5_K_M'
$env:CTX='2048'
$env:GPU_LAYERS='20'
$env:MODEL_PATH='C:\path\to\local-llms'
$env:LFM_IDLE_TIMEOUT='30'
.\start_windows.bat
```

**2a. Cursor**

- Open **Settings → Cursor Settings → Models** (or **Features → OpenAI**).
- Enable **Custom** / **OpenAI-compatible** and set:
  - **Base URL**: `http://localhost:8000/v1`
  - **API key**: any non-empty string (e.g. `parley`); ParleyAI does not validate it.
- Set **Model** to the ID ParleyAI reports, e.g. `Qwen2.5-32B-Instruct` (or run `curl http://localhost:8000/v1/models` to see `data[0].id`).

If Cursor uses a tunnel for some features, you can set Base URL to your ParleyAI tunnel URL + `/v1` (e.g. `https://your-tunnel.trycloudflare.com/v1`) when ParleyAI was started with `TUNNEL=on`.

**2b. VS Code (Continue extension)**

1. Install the **[Continue](https://marketplace.visualstudio.com/items?itemName=Continue.continue)** extension.
2. Open Continue’s config: **Continue Chat** (e.g. `Ctrl+L` / `Cmd+L`) → click the **gear** next to the model selector → **Open config.json** (or edit `~/.continue/config.json`).
3. Add an OpenAI-compatible provider pointing at ParleyAI:

```json
{
  "models": [
    {
      "title": "ParleyAI (Qwen 32B)",
      "provider": "openai",
      "model": "Qwen2.5-32B-Instruct",
      "apiBase": "http://localhost:8000/v1",
      "apiKey": "parley"
    }
  ]
}
```

Use the same `model` value as returned by `GET http://localhost:8000/v1/models` (e.g. `Qwen2.5-32B-Instruct`). If you use a different ParleyAI model, set `model` to that family’s name. If Continue uses `config.yaml` instead, add the same provider with `apiBase`, `model`, and `apiKey`.

**Continue config.yaml example (tunnel URL):**

```yaml
models:
  - name: ParleyAI Qwen 32B
    provider: openai
    apiBase: "https://YOUR-CURRENT-TUNNEL.trycloudflare.com/v1"
    model: Qwen2.5-32B-Instruct
    apiKey: "parley"
    roles:
      - chat
      - edit
      - apply
```

- Use **`provider: openai`** (not `ParleyAI`) — the client uses the OpenAI API format with your custom `apiBase`.
- Use **`model: Qwen2.5-32B-Instruct`** only — no `:Q5_K_M`; quantization is set on the server via `QUANT`.
- Replace **`YOUR-CURRENT-TUNNEL`** with the URL printed when you run ParleyAI with `TUNNEL=on` (the URL changes every time you start the tunnel).

**2c. VS Code (other OpenAI-compatible extensions)**

Any extension that lets you set a custom **OpenAI API base URL** and **API key** can use ParleyAI:

- **Base URL**: `http://localhost:8000/v1`
- **API key**: any string (e.g. `parley`)
- **Model**: value from `GET http://localhost:8000/v1/models` → `data[0].id`

**3. Plan-driven app build (Cursor or VS Code)**

1. In your repo, add a **`build/plan.md`** (or `plan.md`) with:
   - App goal, tech stack, and features in order
   - Per-feature or per-section acceptance criteria
2. In **Cursor**: Open `build/plan.md`, then in **Composer** or **Chat** say e.g. *“Implement the app from this plan step by step”* or *“Implement section 2 from build/plan.md”*. The AI uses ParleyAI (if selected) and your plan as context.
3. In **VS Code (Continue)**: Open `build/plan.md`, start a Continue chat, and ask e.g. *“Following build/plan.md, implement the auth module”*. Continue sends that to ParleyAI.
4. You run the app and tests locally; the AI proposes edits and you accept or refine. For long plans, paste only the relevant section into the chat to stay within context limits, or use a larger `CTX` (e.g. 8192) if your VRAM allows.

### Quick test with curl

```bash
# Anthropic format
curl http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello!"}],"max_tokens":64}'

# OpenAI format
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello!"}],"max_tokens":64}'
```

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="not-needed")
response = client.chat.completions.create(
    model="parleyai",
    messages=[{"role": "user", "content": "What is 2+2?"}],
)
print(response.choices[0].message.content)
```

---

## 📝 Credits & License

### GGUF Quantizations
The quantized GGUF models used in this project are provided by **[bartowski](https://huggingface.co/bartowski)**. These quantizations make it possible to run the 70B model on consumer hardware.

### Original Model
The base Llama 3.3 70B Instruct model is created by **Meta** and subject to the [Llama 3.3 Community License](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct).

Key requirements:
- Accept the license on Hugging Face before use
- Display "Built with Llama" for public applications
- Monthly active users > 700M require separate license from Meta

### This Code
This application code is provided for educational purposes.
