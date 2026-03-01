# ParleyAI

A full-stack chat application for running large GGUF models locally.

**Supported models:**

| `MODEL_FAMILY` | Model | GGUF Downloads | RAM | Best for |
|---|---|---|---|---|
| `llama_70b` | Llama 3.3 70B Instruct | [bartowski GGUF](https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF) | 48GB+ | General-purpose, coding |
| `qwen_32b` | Qwen2.5-32B-Instruct | [Qwen GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) | 24–40GB | **Creative writing, JSON, structured output** |
| `mistral_24b` | Mistral Small 3.1 24B | [Mistral GGUF](https://huggingface.co/bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF) | 20–32GB | Fast inference, instruction following |
| `lfm2_24b` | LFM2-24B-A2B | [LiquidAI GGUF](https://huggingface.co/LiquidAI/LFM2-24B-A2B-GGUF) | 20–35GB | Efficient MoE (2B active params) |
| `custom` | Any GGUF model | — | varies | Bring your own model via `MODEL_PATH` |

**Supported platforms:**
- **macOS** with Apple Silicon (M1/M2/M3/M4) — Metal GPU acceleration
- **Windows** with NVIDIA GPUs (RTX 3060–5090) — CUDA acceleration
- **Linux** with NVIDIA GPUs — CUDA acceleration

### Recommended Models by Hardware

| Hardware | Top Pick | `MODEL_FAMILY` | `QUANT` | Download |
|---|---|---|---|---|
| **48GB+ RAM** (M4 Pro, etc.) | Llama 3.3 70B | `llama_70b` | `Q4_K_M` | [43GB GGUF](https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF) |
| **32GB RAM + RTX 4070** | Qwen2.5-32B | `qwen_32b` | `Q5_K_M` | [23GB GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) |
| **32GB RAM** (story/JSON) | Qwen2.5-32B | `qwen_32b` | `Q4_K_M` | [20GB GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) |
| **32GB RAM** (fast) | Mistral Small 3.1 | `mistral_24b` | `Q6_K` | [20GB GGUF](https://huggingface.co/bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF) |
| **24GB RAM** | Mistral Small 3.1 | `mistral_24b` | `Q4_K_M` | [14GB GGUF](https://huggingface.co/bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF) |
| **20GB RAM** | LFM2-24B-A2B | `lfm2_24b` | `Q4_0` | [14GB GGUF](https://huggingface.co/LiquidAI/LFM2-24B-A2B-GGUF) |

### Model Comparison (i7 + RTX 4070 8GB + 32GB RAM)

| # | Criteria | Llama 70B Q3_K_M | Qwen 32B Q5_K_M | Mistral 24B Q6_K | LFM2 24B Q8_0 |
|---|---|---|---|---|---|
| 1 | **Hardware Compatibility** | 40% | 85% | 93% | 78% |
| 2 | **Speed** | 20% | 65% | 85% | 82% |
| 3 | **Output Quality** | 62% | 92% | 76% | 58% |
| 4 | **Hallucinations** (less = better) | 58% | 86% | 78% | 55% |
| 5 | **Overall** | **45%** | **82%** | **83%** | **68%** |

> **For creative/structured output** (stories, JSON): Qwen2.5-32B Q5_K_M is the best pick.
> **For speed-first workflows**: Mistral 3.1 24B Q6_K edges out with faster inference at nearly the same overall score.
> **Avoid Llama 70B** on 32GB RAM — the aggressive Q3 quantization needed to fit it undermines its quality advantage.

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

**Qwen2.5-32B on 32GB RAM (i7 + RTX 4070 8GB):**

| Quant | Size | Fits 32GB? | Quality vs FP16 | Speed | Overall |
|---|---|---|---|---|---|
| **Q4_K_M** | 20GB | Comfortable | -2–4% | Fast | 78% |
| **Q5_K_M** | 23GB | Comfortable | -1–2% | Good | **82% (recommended)** |
| **Q6_K** | 27GB | Tight (CTX≤4096) | -0.5–1% | Slower | 76% |
| **Q8_0** | 34GB | No (swaps) | -0.1–0.3% | Very slow | 58% |

**Mistral 3.1 24B on 32GB RAM:**

| Quant | Size | Fits 32GB? | Quality vs FP16 | Speed | Overall |
|---|---|---|---|---|---|
| **Q4_K_M** | 14GB | Easy | -2–4% | Very fast | 80% |
| **Q5_K_M** | 17GB | Easy | -1–2% | Fast | 84% |
| **Q6_K** | 20GB | Comfortable | -0.5–1% | Good | **86% (recommended)** |
| **Q8_0** | 25GB | Comfortable | -0.1–0.3% | Good | 85% |

**LFM2-24B on 32GB RAM:**

| Quant | Size | Fits 32GB? | Quality vs FP16 | Speed | Overall |
|---|---|---|---|---|---|
| **Q4_0** | 14GB | Easy | -3–5% | Very fast | 65% |
| **Q4_K_M** | 15GB | Easy | -2–4% | Fast | **68% (recommended)** |
| **Q8_0** | 26GB | Comfortable | -0.1–0.3% | Good | 72% |

**Llama 3.3 70B (48GB+ RAM recommended):**

| Quant | Size | Fits 32GB? | Quality vs FP16 | Speed | Overall (on 32GB) |
|---|---|---|---|---|---|
| **Q3_K_M** | 34GB | Barely | -5–10% | Very slow | 45% |
| **Q4_K_M** | 43GB | No | -2–4% | — | Needs 48GB+ |
| **Q5_K_M** | 50GB | No | -1–2% | — | Needs 64GB+ |

> **Rule of thumb:** Pick the highest quant where the model fits with ≥5GB headroom. Going one quant higher gives <2% quality gain but can cut speed in half if you hit RAM limits.

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
MODEL_PATH=~/llama-models QUANT=IQ3_M CTX=2048 GPU_LAYERS=40 ./start.sh
```

| Parameter | Value | Description |
|-----------|-------|-------------|
| `MODEL_FAMILY` | `llama_70b` | `llama_70b`, `qwen_32b`, `mistral_24b`, `lfm2_24b`, or `custom` |
| `MODEL_PATH` | `~/llama-models` | Directory or path to GGUF file (required for `custom`) |
| `QUANT` | `Q4_K_M` | Quantization (options depend on `MODEL_FAMILY`) |
| `CTX` | `2048` | Context window (tokens) |
| `GPU_LAYERS` | `99` or `-1` | Layers offloaded to GPU |
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

All model families except `llama_70b` use an external `llama-server` subprocess (from the [llama.cpp](https://github.com/ggml-org/llama.cpp) project). This covers Qwen2.5-32B, Mistral Small 3.1, LFM2-24B, and any custom GGUF model.

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
MODEL_FAMILY=qwen_32b QUANT=Q5_K_M CTX=8192 ./start.sh

# Mistral Small 3.1 24B — fast, strong instruction following
MODEL_FAMILY=mistral_24b QUANT=Q6_K CTX=8192 ./start.sh

# LFM2-24B — efficient MoE, fits in 30–35GB RAM
MODEL_FAMILY=lfm2_24b QUANT=Q4_K_M ./start.sh

# Any GGUF model — chat template auto-detected from the GGUF file
MODEL_FAMILY=custom MODEL_PATH=~/models/my-model.gguf CTX=4096 ./start.sh
```

**Windows (CMD):**

```bat
set MODEL_FAMILY=qwen_32b
set QUANT=Q5_K_M
set CTX=8192
.\start_windows.bat
```

Models are auto-downloaded from Hugging Face on first run. Set `MODEL_PATH` to skip the download if you already have the GGUF file.

**Available quantizations per family:**

| Family | Quants | Recommended (32GB RAM) |
|---|---|---|
| `qwen_32b` | Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0 | **Q5_K_M** (23GB) |
| `mistral_24b` | Q4_K_M, Q5_K_M, Q6_K, Q8_0 | **Q6_K** (20GB) |
| `lfm2_24b` | Q4_0, Q4_K_M, Q5_K_M, Q6_K, Q8_0, BF16, F16 | **Q4_K_M** (15GB) |
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
| `qwen_32b` | [Qwen2.5-32B-Instruct](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) | [GGUF](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF) | Q3_K_M – Q8_0 | **Q5_K_M** (23GB) |
| `mistral_24b` | [Mistral Small 3.1 24B](https://huggingface.co/bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF) | [GGUF](https://huggingface.co/bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF) | Q4_K_M – Q8_0 | **Q6_K** (20GB) |
| `lfm2_24b` | [LFM2-24B-A2B](https://huggingface.co/LiquidAI/LFM2-24B-A2B-GGUF) | [GGUF](https://huggingface.co/LiquidAI/LFM2-24B-A2B-GGUF) | Q4_0 – F16 | **Q4_K_M** (15GB) |
| `custom` | Any GGUF | — | Set via `MODEL_PATH` | — |

### 🎮 NVIDIA GPU Recommendations

For Windows/Linux with NVIDIA GPUs, the model is split between **VRAM** (fast) and **System RAM** (slower). More layers on GPU = faster inference.

| GPU | VRAM | Recommended Quant | GPU Layers | System RAM Needed |
|-----|------|-------------------|------------|-------------------|
| **RTX 3060** | 12GB | IQ2_XXS, IQ2_XS | 20-25 | 16GB+ |
| **RTX 3070** | 8GB | IQ1_M, IQ2_XXS | 15-20 | 24GB+ |
| **RTX 3070 Ti** | 8GB | IQ1_M, IQ2_XXS | 15-20 | 24GB+ |
| **RTX 3080** | 10GB | IQ2_XXS, IQ2_XS | 18-22 | 20GB+ |
| **RTX 3090** | 24GB | Q3_K_S, IQ3_M | 35-45 | 16GB+ |
| **RTX 4060** | 8GB | IQ1_M, IQ2_XXS | 15-20 | 24GB+ |
| **RTX 4060 Ti** | 8/16GB | IQ2_XXS / Q2_K | 15-25 | 20GB+ |
| **RTX 4070** | 12GB | IQ2_XS, Q2_K | 22-28 | 20GB+ |
| **RTX 4070 Ti** | 12GB | IQ2_XS, Q2_K | 22-28 | 20GB+ |
| **RTX 4080** | 16GB | Q2_K, Q3_K_S | 28-35 | 16GB+ |
| **RTX 4090** | 24GB | Q3_K_M, IQ3_M | 40-50 | 16GB+ |
| **RTX 5060** | 8GB* | IQ1_M, IQ2_XXS | 15-20 | 24GB+ |
| **RTX 5070** | 12GB* | IQ2_XS, Q2_K | 22-28 | 20GB+ |
| **RTX 5080** | 16GB* | Q2_K, Q3_K_S | 28-35 | 16GB+ |
| **RTX 5090** | 32GB* | Q4_K_S, Q4_K_M | 50-60 | 16GB+ |

\* RTX 50-series specs are estimated based on expected configurations.

#### Example Commands for NVIDIA GPUs

```powershell
# RTX 4060 (8GB VRAM) - Windows
$env:MODEL_FAMILY="llama_70b"   # or qwen_32b, mistral_24b, lfm2_24b, custom
$env:MODEL_PATH="C:\llama-models"
$env:QUANT="IQ2_XXS"
$env:CTX="1024"
$env:GPU_LAYERS="18"
.\start_windows.bat

# RTX 4070 (12GB VRAM) + 32GB RAM - Qwen2.5-32B for creative writing
MODEL_FAMILY=qwen_32b QUANT=Q5_K_M CTX=8192 GPU_LAYERS=99 ./start.sh

# RTX 4090 (24GB VRAM) - Llama 70B
MODEL_PATH=~/llama-models QUANT=Q3_K_M CTX=2048 GPU_LAYERS=45 ./start.sh

# RTX 3070 Ti (8GB VRAM) - Mistral 24B (smaller model, faster)
MODEL_FAMILY=mistral_24b QUANT=Q4_K_M CTX=4096 GPU_LAYERS=33 ./start.sh
```

> **⚠️ VRAM vs RAM**: Unlike Apple Silicon's unified memory, NVIDIA GPUs have separate VRAM. If the model doesn't fit in VRAM, layers are offloaded to CPU (slower). Use `GPU_LAYERS` to control how many layers go to GPU.

> **💡 Performance Tip**: Start with fewer GPU layers and increase until you hit VRAM limits. Watch for "CUDA out of memory" errors.

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

All model families except `llama_70b` (`qwen_32b`, `mistral_24b`, `lfm2_24b`, `custom`) require `llama-server` (from the llama.cpp project).

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
