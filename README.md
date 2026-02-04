# Llama 3.3 70B Chat

A full-stack chat application for Meta's **Llama 3.3 70B Instruct** model running locally on Mac with Apple Silicon.

**Reference**: [meta-llama/Llama-3.3-70B-Instruct](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct)

## 🚀 Quick Start (Full-Stack App)

```bash
# One-time setup
./setup_fullstack.sh

# Start the application
./start.sh
```

Then open **http://localhost:5173** in your browser!

### Manual Setup (if setup script fails)

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

## ✅ Verified Working Configuration

**Tested on Mac M4 Pro with 48GB RAM** - running perfectly!

```bash
MODEL_PATH=~/llama-models QUANT=IQ3_M CTX=2048 GPU_LAYERS=40 ./start.sh
```

| Parameter | Value | Description |
|-----------|-------|-------------|
| `MODEL_PATH` | `~/llama-models` | Directory containing GGUF models |
| `QUANT` | `IQ3_M` | 32GB model, medium quality I-quant |
| `CTX` | `1080` | Context window (tokens) |
| `GPU_LAYERS` | `40` | Layers offloaded to Metal GPU |

## 📁 Project Structure

```
local_ai_chat_app/
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
├── brew_setup/           # Homebrew CLI alternative
├── setup_fullstack.sh    # Full-stack setup script
├── start.sh              # Start both frontend + backend
└── README.md
```

---

## 🎯 How It Works

Running a 70B parameter model (normally ~140GB in FP16) efficiently requires:

1. **Quantization**: Compress to 4-8 bits per weight
2. **Memory Mapping (mmap)**: Stream model layers from disk on-demand
3. **Metal GPU Acceleration**: Leverage Apple Silicon's unified memory

| Quantization | Model Size | RAM Needed | Quality |
|--------------|------------|------------|---------|
| IQ2_XXS | ~19GB | 10GB+ | Extreme compression |
| Q2_K | ~26GB | 12GB+ | Low quality |
| Q3_K_S | ~31GB | 16GB+ | Medium quality |
| Q4_K_S | ~40GB | 24GB+ | Good quality |
| **Q4_K_M** | **~43GB** | **32GB+** | **Very good (recommended)** |
| Q4_K_L | ~43GB | 32GB+ | Excellent (Q8 embed/output) |
| Q5_K_S | ~49GB | 48GB+ | High quality |
| Q5_K_M | ~50GB | 48GB+ | High quality |

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

## 📝 License

This code is provided for educational purposes. The Llama 3.3 model is subject to Meta's [Llama 3.3 Community License](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct).

Key requirements:
- Accept the license on Hugging Face before use
- Display "Built with Llama" for public applications
- Monthly active users > 700M require separate license from Meta
