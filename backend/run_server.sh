#!/bin/bash
# run_server.sh - Start the Llama backend server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
export QUANT="${QUANT:-Q4_K_M}"
export CTX="${CTX:-2048}"
export GPU_LAYERS="${GPU_LAYERS:-99}"
export PORT="${PORT:-8000}"
export MODEL_PATH="${MODEL_PATH:-}"

# Check for venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv
source venv/bin/activate

echo "🦙 Starting Llama 3.3 70B Backend Server"
echo "========================================="
echo "   Quantization: $QUANT"
echo "   Context: $CTX tokens"
echo "   GPU Layers: $GPU_LAYERS"
echo "   Port: $PORT"
echo "========================================="
echo ""

# Run server
python server.py
