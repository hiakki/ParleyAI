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

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
else
    echo "   ✓ Virtual environment exists"
fi

source venv/bin/activate

if python -c "import llama_cpp" 2>/dev/null; then
    echo "   ✓ llama-cpp-python already installed"
else
    echo "   Installing llama-cpp-python with Metal..."
    CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-cache-dir
fi

echo "   Checking Python dependencies..."
pip install -q --upgrade -r requirements.txt

echo "   Installing optional dependencies (TTS, image, video)..."
pip install -q --upgrade -r requirements-extra.txt 2>/dev/null || true

# If NVIDIA GPU present, install PyTorch with CUDA so /api/image uses GPU
if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
    echo "   Installing PyTorch with CUDA for GPU image generation..."
    if pip install torch --index-url https://download.pytorch.org/whl/cu124 --force-reinstall 2>/dev/null; then
        echo "   ✓ PyTorch with CUDA 12.4 installed"
    elif pip install torch --index-url https://download.pytorch.org/whl/cu121 --force-reinstall 2>/dev/null; then
        echo "   ✓ PyTorch with CUDA 12.1 installed"
    else
        echo "   ⚠️  PyTorch CUDA install failed (image gen will use CPU if used)"
    fi
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
