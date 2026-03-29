#!/bin/bash
# setup_fullstack.sh - Set up ParleyAI (full-stack local chat application)
# Safe to re-run — only installs what's new or upgraded.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🦙 Setting up ParleyAI"
echo "============================================="
echo ""

# Setup Backend
echo "📦 Setting up Backend..."
cd backend

# Debian/Ubuntu minimal images ship python3 without venv; `python3 -m venv` then fails with ensurepip errors.
if ! python3 -c "import ensurepip" 2>/dev/null; then
    PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "3")"
    echo ""
    echo "❌ Python venv support (ensurepip) is not available."
    echo "   On Debian/Ubuntu, install the matching venv package, then re-run this script:"
    echo ""
    echo "      sudo apt update"
    echo "      sudo apt install -y python${PY_VER}-venv"
    echo ""
    echo "   Or: sudo apt install -y python3-venv"
    echo ""
    exit 1
fi

# Require bin/activate — a stale or empty "venv" dir breaks source
if [ ! -f "venv/bin/activate" ]; then
    if [ -d "venv" ]; then
        echo "   ⚠️  venv/ exists but is incomplete (no bin/activate). Removing and recreating..."
        rm -rf venv
    fi
    echo "   Creating virtual environment..."
    python3 -m venv venv
else
    echo "   ✓ Virtual environment exists"
fi

source venv/bin/activate

# llama-cpp-python: platform-specific build (Metal is macOS-only; Linux needs gcc to compile)
if python -c "import llama_cpp" 2>/dev/null; then
    echo "   ✓ llama-cpp-python already installed"
else
    _UNAME_S="$(uname -s)"
    if [ "$_UNAME_S" = "Linux" ]; then
        if ! command -v gcc &>/dev/null; then
            echo ""
            echo "❌ C compiler (gcc) not found. llama-cpp-python builds from source on Linux."
            echo "   Install build tools, then re-run this script:"
            echo ""
            echo "      sudo apt update && sudo apt install -y build-essential cmake"
            echo ""
            exit 1
        fi
        # CUDA build only if the toolkit is present (driver alone is not enough)
        if command -v nvcc &>/dev/null; then
            echo "   Installing llama-cpp-python (CUDA)..."
            CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --no-cache-dir
        else
            echo "   Installing llama-cpp-python (CPU; for GPU-accelerated llama-cpp install nvidia-cuda-toolkit or set up CUDA + nvcc, then re-run)..."
            pip install llama-cpp-python --no-cache-dir
        fi
    elif [ "$_UNAME_S" = "Darwin" ]; then
        echo "   Installing llama-cpp-python (Metal)..."
        CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-cache-dir
    else
        echo "   Installing llama-cpp-python..."
        pip install llama-cpp-python --no-cache-dir
    fi
fi

echo "   Checking Python dependencies..."
pip install -q --upgrade -r requirements.txt

echo "   Installing optional dependencies (TTS, image, video)..."
pip install -q --upgrade -r requirements-extra.txt 2>/dev/null || true

# If NVIDIA GPU present, install PyTorch with CUDA so /api/image uses GPU
if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
    echo "   Installing PyTorch with CUDA for GPU image generation..."
    if pip install torch --index-url https://download.pytorch.org/whl/cu130 --force-reinstall 2>/dev/null; then
        echo "   ✓ PyTorch with CUDA 13.0 installed"
    elif pip install torch --index-url https://download.pytorch.org/whl/cu128 --force-reinstall 2>/dev/null; then
        echo "   ✓ PyTorch with CUDA 12.8 installed"
    elif pip install torch --index-url https://download.pytorch.org/whl/cu124 --force-reinstall 2>/dev/null; then
        echo "   ✓ PyTorch with CUDA 12.4 installed"
    elif pip install torch --index-url https://download.pytorch.org/whl/cu121 --force-reinstall 2>/dev/null; then
        echo "   ✓ PyTorch with CUDA 12.1 installed"
    else
        echo "   ⚠️  PyTorch CUDA install failed (image gen will use CPU if used)"
    fi
fi

# Pre-download image + video models so first use doesn't wait on huge downloads
echo ""
echo "========================================"
echo "  Pre-download image + video models (optional)"
echo "========================================"
echo "Image model (text-to-image):  ~5 GB   - runwayml/stable-diffusion-v1-5"
echo "Video model (image-to-video): ~20 GB  - stabilityai/stable-video-diffusion-img2vid-xt"
python -c "import os; h=os.environ.get('HF_HOME', os.path.join(os.path.expanduser('~'), '.cache', 'huggingface')); c=os.environ.get('HF_HUB_CACHE', os.path.join(h, 'hub')); print('Cache directory:', c)"
echo "To use a different folder, set HF_HOME (e.g. export HF_HOME=~/HFcache). PRELOAD_MODELS: n=skip, image=~5GB, video=~20GB, y=both."
echo ""
if [[ -n "${PRELOAD_MODELS:-}" && "$PRELOAD_MODELS" =~ ^[nN]$ ]]; then
    echo "   [SKIP] PRELOAD_MODELS=$PRELOAD_MODELS - models will download on first use."
elif [[ "${PRELOAD_MODELS:-}" == "image" ]]; then
    echo "Pre-downloading image only (~5 GB)..."
    echo ""
    echo "Downloading image model: runwayml/stable-diffusion-v1-5 (~5 GB)..."
    python -c "from huggingface_hub import snapshot_download; snapshot_download('runwayml/stable-diffusion-v1-5'); print('[OK] Image model cached.')" || echo "[SKIP] Image model download failed."
elif [[ "${PRELOAD_MODELS:-}" == "video" ]]; then
    echo "Pre-downloading video only (~20 GB)..."
    echo ""
    echo "Downloading video model: stabilityai/stable-video-diffusion-img2vid-xt (~20 GB)..."
    python -c "from huggingface_hub import snapshot_download; snapshot_download('stabilityai/stable-video-diffusion-img2vid-xt'); print('[OK] Video model cached.')" || echo "[SKIP] Video model download failed."
elif [[ -n "${PRELOAD_MODELS:-}" ]]; then
    echo "Pre-downloading both (~25 GB)..."
    echo ""
    echo "Downloading image model: runwayml/stable-diffusion-v1-5 (~5 GB)..."
    python -c "from huggingface_hub import snapshot_download; snapshot_download('runwayml/stable-diffusion-v1-5'); print('[OK] Image model cached.')" || echo "[SKIP] Image model download failed."
    echo ""
    echo "Downloading video model: stabilityai/stable-video-diffusion-img2vid-xt (~20 GB)..."
    python -c "from huggingface_hub import snapshot_download; snapshot_download('stabilityai/stable-video-diffusion-img2vid-xt'); print('[OK] Video model cached.')" || echo "[SKIP] Video model download failed."
else
    read -p "Pre-download: 1=Image only (~5 GB), 2=Video only (~20 GB), 3=Both (~25 GB), 4=Skip [1-4]: " PRELOAD_CHOICE
    case "${PRELOAD_CHOICE:-4}" in
        1) echo ""; echo "Downloading image model: runwayml/stable-diffusion-v1-5 (~5 GB)..."
           python -c "from huggingface_hub import snapshot_download; snapshot_download('runwayml/stable-diffusion-v1-5'); print('[OK] Image model cached.')" || echo "[SKIP] Image model download failed." ;;
        2) echo ""; echo "Downloading video model: stabilityai/stable-video-diffusion-img2vid-xt (~20 GB)..."
           python -c "from huggingface_hub import snapshot_download; snapshot_download('stabilityai/stable-video-diffusion-img2vid-xt'); print('[OK] Video model cached.')" || echo "[SKIP] Video model download failed." ;;
        3) echo ""; echo "Downloading image model: runwayml/stable-diffusion-v1-5 (~5 GB)..."
           python -c "from huggingface_hub import snapshot_download; snapshot_download('runwayml/stable-diffusion-v1-5'); print('[OK] Image model cached.')" || echo "[SKIP] Image model download failed."
           echo ""; echo "Downloading video model: stabilityai/stable-video-diffusion-img2vid-xt (~20 GB)..."
           python -c "from huggingface_hub import snapshot_download; snapshot_download('stabilityai/stable-video-diffusion-img2vid-xt'); print('[OK] Video model cached.')" || echo "[SKIP] Video model download failed." ;;
        *) echo "   [SKIP] Models will download on first use." ;;
    esac
fi

deactivate
cd ..
echo "   ✓ Backend ready"
echo ""

# Setup Frontend
echo "📦 Setting up Frontend..."
cd frontend

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found!"
    echo "   Install with: brew install node"
    exit 1
fi

if [ -d "node_modules" ]; then
    echo "   Checking for updates..."
    npm install --prefer-offline
else
    echo "   Installing dependencies..."
    npm install
fi

cd ..
echo "   ✓ Frontend ready"
echo ""

# Tunnel tools (optional, for TUNNEL=on)
echo "📦 Checking tunnel tools..."

# cloudflared
if command -v cloudflared &>/dev/null; then
    echo "   ✓ cloudflared already installed"
else
    CF_INSTALLED=false

    if command -v brew &>/dev/null; then
        echo "   Installing cloudflared via Homebrew..."
        if brew install cloudflared 2>/dev/null; then
            CF_INSTALLED=true
        else
            echo "   ⚠️  Homebrew install failed, trying direct download..."
        fi
    fi

    if [ "$CF_INSTALLED" = false ]; then
        ARCH=$(uname -m)
        if [ "$ARCH" = "arm64" ]; then
            CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"
        else
            CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
        fi
        echo "   Downloading cloudflared binary..."
        if curl -fsSL "$CF_URL" -o /tmp/cloudflared.tgz 2>/dev/null; then
            tar -xzf /tmp/cloudflared.tgz -C /tmp 2>/dev/null
            if [ -f /tmp/cloudflared ]; then
                mkdir -p "$HOME/bin"
                mv /tmp/cloudflared "$HOME/bin/cloudflared"
                chmod +x "$HOME/bin/cloudflared"
                export PATH="$HOME/bin:$PATH"
                CF_INSTALLED=true
            fi
            rm -f /tmp/cloudflared.tgz
        fi
    fi

    if [ "$CF_INSTALLED" = true ]; then
        echo "   ✓ cloudflared installed"
    else
        echo "   ⚠️  Could not install cloudflared (not critical)"
    fi
fi

# localtunnel
if command -v lt &>/dev/null; then
    echo "   ✓ localtunnel already installed"
else
    echo "   Installing localtunnel..."
    if npm install -g localtunnel 2>/dev/null; then
        echo "   ✓ localtunnel installed"
    else
        echo "   ⚠️  Could not install localtunnel (not critical)"
    fi
fi
echo ""

echo "============================================="
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "   ./start.sh"
echo ""
echo "Backend only (single command — creates venv, installs deps, starts server):"
echo "   python backend/run.py"
echo "   # or from backend folder:  python run.py"
echo ""
echo "To expose over the internet:"
echo "   TUNNEL=on ./start.sh"
echo ""
echo "Or start individually:"
echo "   Backend:  cd backend && python run.py"
echo "   Backend:  cd backend && ./run_server.sh"
echo "   Frontend: cd frontend && npm run dev"
echo "============================================="
