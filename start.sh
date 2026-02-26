#!/bin/bash
# start.sh - Start ParleyAI (full-stack local chat application)

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat <<'HELP'
ParleyAI — Local Chat

Usage:
  ./start.sh                         Start with defaults
  MODEL_FAMILY=lfm2_24b ./start.sh   Use LFM2 model
  TUNNEL=on ./start.sh               Expose over the internet

Environment variables:

  Model
    MODEL_FAMILY    llama_70b or lfm2_24b           (default: llama_70b)
    QUANT           Quantization level               (default: Q4_K_M)
    CTX             Context window in tokens          (default: 2048)
    MODEL_PATH      Path to GGUF file or directory    (default: auto-download)

  Hardware
    GPU_LAYERS      Layers offloaded to GPU           (default: 99)
    BATCH_SIZE      Batch size for inference           (default: 512)

  Network
    PORT            Backend port                      (default: 8000)
    TUNNEL          on/off — expose via tunnel         (default: off)
    TUNNEL_TOOL     auto, cloudflared, or localtunnel  (default: auto)
    SUBDOMAIN       Custom subdomain for localtunnel   (e.g. parley-ai → parley-ai.loca.lt)

  LFM2 specific
    LFM_IDLE_TIMEOUT  Seconds before llama-server auto-stops  (default: 300)

Examples:
  # Llama 3.3 70B with 5-bit quantization
  QUANT=Q5_K_M ./start.sh

  # LFM2-24B on 32GB machine
  MODEL_FAMILY=lfm2_24b QUANT=Q4_K_M ./start.sh

  # Expose to the internet via Cloudflare
  TUNNEL=on ./start.sh

  # Use localtunnel instead
  TUNNEL=on TUNNEL_TOOL=localtunnel ./start.sh

  # localtunnel with custom subdomain
  TUNNEL=on TUNNEL_TOOL=localtunnel SUBDOMAIN=parley-ai ./start.sh

  # Custom model path, lower context
  MODEL_PATH=~/models QUANT=IQ3_M CTX=1024 ./start.sh

  # NVIDIA GPU with limited VRAM
  GPU_LAYERS=20 QUANT=IQ2_XXS CTX=512 ./start.sh
HELP
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PATH="$HOME/bin:$PATH"

echo "🦙 ParleyAI — Local Chat"
echo "=================================="
echo ""

# Configuration
export MODEL_FAMILY="${MODEL_FAMILY:-llama_70b}"   # llama_70b or lfm2_24b (30–35GB RAM)
export QUANT="${QUANT:-Q4_K_M}"
export CTX="${CTX:-2048}"
export GPU_LAYERS="${GPU_LAYERS:-99}"
export BATCH_SIZE="${BATCH_SIZE:-512}"
export MODEL_PATH="${MODEL_PATH:-}"
export LFM_IDLE_TIMEOUT="${LFM_IDLE_TIMEOUT:-300}"  # seconds before llama-server auto-stops (0=never)
TUNNEL="${TUNNEL:-off}"                              # on = expose via tunnel
TUNNEL_TOOL="${TUNNEL_TOOL:-auto}"                   # auto, cloudflared, or localtunnel
SUBDOMAIN="${SUBDOMAIN:-}"                           # custom subdomain for localtunnel
BACKEND_PORT="${PORT:-8000}"
FRONTEND_PORT=5173
BACKEND_URL="http://localhost:$BACKEND_PORT"
MAX_WAIT=300  # Max wait time in seconds (5 minutes for large model loading)
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || echo "?.?.?.?")

# Check backend venv
if [ ! -d "backend/venv" ]; then
    echo "❌ Backend not set up!"
    echo "   Run: ./setup_fullstack.sh first"
    exit 1
fi

# Check frontend node_modules
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend not set up!"
    echo "   Run: ./setup_fullstack.sh first"
    exit 1
fi

# Start backend in background
echo "📡 Starting backend server..."
echo "   Model family: $MODEL_FAMILY"
echo "   Quantization: $QUANT"
echo "   Context: $CTX tokens"
echo "   Batch Size: $BATCH_SIZE"
echo "   GPU Layers: $GPU_LAYERS"
[ -n "$MODEL_PATH" ] && echo "   Model Path: $MODEL_PATH"
echo ""

cd backend
source venv/bin/activate
python server.py &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready with health check
echo "⏳ Waiting for backend to load model (this may take 1-3 minutes)..."
WAIT_TIME=0
READY=false

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo ""
        echo "❌ Backend process crashed!"
        exit 1
    fi
    
    if curl -s "$BACKEND_URL/" > /dev/null 2>&1; then
        READY=true
        break
    fi
    
    if [ $((WAIT_TIME % 10)) -eq 0 ] && [ $WAIT_TIME -gt 0 ]; then
        echo "   Still loading... (${WAIT_TIME}s elapsed)"
    fi
    
    sleep 2
    WAIT_TIME=$((WAIT_TIME + 2))
done

if [ "$READY" = false ]; then
    echo ""
    echo "❌ Backend failed to start within ${MAX_WAIT}s!"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "   ✓ Backend ready on $BACKEND_URL (took ${WAIT_TIME}s)"
echo ""

# Write env file for Claude Code CLI
CLAUDE_ENV="$SCRIPT_DIR/.claude_env"
cat > "$CLAUDE_ENV" <<ENVEOF
export ANTHROPIC_BASE_URL=http://localhost:$BACKEND_PORT
export ANTHROPIC_AUTH_TOKEN=not-needed
export ANTHROPIC_MODEL=parleyai
ENVEOF

# Start frontend
echo "🌐 Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to accept connections before starting tunnel
FWAIT=0
while [ $FWAIT -lt 30 ]; do
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
        break
    fi
    sleep 1
    FWAIT=$((FWAIT + 1))
done
echo "   ✓ Frontend ready (${FWAIT}s)"

# Start tunnel if requested
TUNNEL_PID=""
TUNNEL_URL=""
if [ "$TUNNEL" = "on" ]; then
    echo ""
    echo "🌍 Starting internet tunnel (TUNNEL_TOOL=$TUNNEL_TOOL)..."

    # Resolve which tool to use
    USE_CF=false
    USE_LT=false
    if [ "$TUNNEL_TOOL" = "cloudflared" ]; then
        USE_CF=true
    elif [ "$TUNNEL_TOOL" = "localtunnel" ]; then
        USE_LT=true
    else
        # auto: prefer cloudflared, fall back to localtunnel
        if command -v cloudflared &>/dev/null; then
            USE_CF=true
        elif command -v lt &>/dev/null; then
            USE_LT=true
        else
            USE_CF=true  # will trigger auto-install below
        fi
    fi

    # Auto-install if the chosen tool is missing
    if [ "$USE_CF" = true ] && ! command -v cloudflared &>/dev/null; then
        echo "   cloudflared not found — installing..."
        if command -v brew &>/dev/null && brew install cloudflared 2>/dev/null; then
            echo "   ✓ Installed via Homebrew"
        else
            ARCH=$(uname -m)
            if [ "$ARCH" = "arm64" ]; then
                CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"
            else
                CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
            fi
            if curl -fsSL "$CF_URL" -o /tmp/cloudflared.tgz 2>/dev/null; then
                tar -xzf /tmp/cloudflared.tgz -C /tmp 2>/dev/null
                mkdir -p "$HOME/bin"
                mv /tmp/cloudflared "$HOME/bin/cloudflared"
                chmod +x "$HOME/bin/cloudflared"
                export PATH="$HOME/bin:$PATH"
                rm -f /tmp/cloudflared.tgz
                echo "   ✓ Installed to ~/bin/cloudflared"
            else
                echo "   ⚠️  Could not install cloudflared"
                USE_CF=false
            fi
        fi
    fi

    if [ "$USE_LT" = true ] && ! command -v lt &>/dev/null; then
        echo "   localtunnel not found — installing..."
        if npm install -g localtunnel 2>/dev/null; then
            echo "   ✓ Installed localtunnel"
        else
            echo "   ⚠️  Could not install localtunnel"
            USE_LT=false
        fi
    fi

    # Start the tunnel and wait for URL
    TUNNEL_MAX_WAIT=30
    if [ "$USE_CF" = true ] && command -v cloudflared &>/dev/null; then
        cloudflared tunnel --url "http://localhost:$FRONTEND_PORT" --protocol http2 --no-autoupdate 2>"$SCRIPT_DIR/.tunnel.log" &
        TUNNEL_PID=$!
        TWAIT=0
        while [ $TWAIT -lt $TUNNEL_MAX_WAIT ]; do
            TUNNEL_URL=$(grep -o 'https://[a-z0-9\-]*\.trycloudflare\.com' "$SCRIPT_DIR/.tunnel.log" 2>/dev/null | head -1)
            [ -n "$TUNNEL_URL" ] && break
            if ! kill -0 $TUNNEL_PID 2>/dev/null; then
                echo "   ⚠️  Cloudflare tunnel process exited"
                break
            fi
            sleep 2
            TWAIT=$((TWAIT + 2))
            [ $((TWAIT % 6)) -eq 0 ] && echo "   Waiting for tunnel URL... (${TWAIT}s)"
        done
        if [ -n "$TUNNEL_URL" ]; then
            echo "   ✓ Cloudflare Tunnel: $TUNNEL_URL"
        else
            echo "   ⚠️  Timed out waiting for tunnel URL (${TUNNEL_MAX_WAIT}s)"
            echo "   Check .tunnel.log for details"
        fi
    elif [ "$USE_LT" = true ] && command -v lt &>/dev/null; then
        _lt_try_subdomain() {
            local sub="$1"
            local lt_args="--port $FRONTEND_PORT"
            [ -n "$sub" ] && lt_args="$lt_args --subdomain $sub"
            > "$SCRIPT_DIR/.tunnel.log"
            lt $lt_args > "$SCRIPT_DIR/.tunnel.log" 2>&1 &
            TUNNEL_PID=$!
            TWAIT=0
            while [ $TWAIT -lt $TUNNEL_MAX_WAIT ]; do
                TUNNEL_URL=$(grep -o 'https://[^ ]*\.loca\.lt' "$SCRIPT_DIR/.tunnel.log" 2>/dev/null | head -1)
                [ -n "$TUNNEL_URL" ] && break
                if ! kill -0 $TUNNEL_PID 2>/dev/null; then
                    TUNNEL_URL=$(grep -o 'https://[^ ]*\.loca\.lt' "$SCRIPT_DIR/.tunnel.log" 2>/dev/null | head -1)
                    break
                fi
                sleep 2
                TWAIT=$((TWAIT + 2))
            done
        }

        if [ -n "$SUBDOMAIN" ]; then
            echo "   Requesting subdomain: $SUBDOMAIN"
            LT_GOT=""
            LT_ATTEMPT="$SUBDOMAIN"
            for SUFFIX in "" "-1" "-2" "-3" "-4" "-5"; do
                LT_ATTEMPT="${SUBDOMAIN}${SUFFIX}"
                _lt_try_subdomain "$LT_ATTEMPT"
                if [ -n "$TUNNEL_URL" ] && kill -0 $TUNNEL_PID 2>/dev/null; then
                    EXPECTED="https://${LT_ATTEMPT}.loca.lt"
                    if [ "$TUNNEL_URL" = "$EXPECTED" ]; then
                        LT_GOT="$TUNNEL_URL"
                        break
                    else
                        echo "   '$LT_ATTEMPT' taken, got $TUNNEL_URL instead — retrying..."
                        kill $TUNNEL_PID 2>/dev/null
                        wait $TUNNEL_PID 2>/dev/null
                        TUNNEL_URL=""
                        TUNNEL_PID=""
                    fi
                else
                    break
                fi
            done
            if [ -z "$LT_GOT" ] && [ -n "$TUNNEL_URL" ] && kill -0 $TUNNEL_PID 2>/dev/null; then
                LT_GOT="$TUNNEL_URL"
                echo "   Could not claim '$SUBDOMAIN' — using assigned URL"
            fi
            TUNNEL_URL="$LT_GOT"
        else
            _lt_try_subdomain ""
        fi

        if [ -n "$TUNNEL_URL" ] && kill -0 $TUNNEL_PID 2>/dev/null; then
            echo "   ✓ localtunnel: $TUNNEL_URL"
        elif [ -n "$TUNNEL_URL" ]; then
            echo "   ⚠️  localtunnel crashed (their relay servers may be down)"
            echo "   Try: TUNNEL_TOOL=cloudflared instead"
            TUNNEL_URL=""
            TUNNEL_PID=""
        else
            echo "   ⚠️  localtunnel failed — check .tunnel.log"
            echo "   Try: TUNNEL_TOOL=cloudflared instead"
            TUNNEL_PID=""
        fi
    else
        echo "   ⚠️  No tunnel tool available"
        TUNNEL="off"
    fi
    echo ""
fi

echo ""
echo "=================================="
echo "✅ Application started!"
echo ""
echo "   Frontend: http://localhost:$FRONTEND_PORT"
echo "   Backend:  http://localhost:$BACKEND_PORT  (localhost only)"
echo ""
echo "   Network (LAN):"
echo "     Frontend: http://$LOCAL_IP:$FRONTEND_PORT"
if [ -n "$TUNNEL_URL" ]; then
echo ""
echo "   Internet:"
echo "     $TUNNEL_URL"
fi
echo ""
echo "   Claude Code CLI (in another terminal):"
echo "     source $CLAUDE_ENV && claude"
echo ""
echo "   Press Ctrl+C to stop all services"
echo "=================================="

# Handle shutdown
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $FRONTEND_PID 2>/dev/null
    [ -n "$TUNNEL_PID" ] && kill $TUNNEL_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    rm -f "$CLAUDE_ENV" "$SCRIPT_DIR/.tunnel.log"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait
