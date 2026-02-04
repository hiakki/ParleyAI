#!/bin/bash
# start.sh - Start the full-stack Llama Chat application

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🦙 Llama 3.3 70B Chat Application"
echo "=================================="
echo ""

# Configuration
export QUANT="${QUANT:-Q4_K_M}"
export CTX="${CTX:-2048}"
export GPU_LAYERS="${GPU_LAYERS:-99}"
export BATCH_SIZE="${BATCH_SIZE:-512}"
export MODEL_PATH="${MODEL_PATH:-}"
BACKEND_PORT="${PORT:-8000}"
BACKEND_URL="http://localhost:$BACKEND_PORT"
MAX_WAIT=300  # Max wait time in seconds (5 minutes for large model loading)

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
    # Check if process is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo ""
        echo "❌ Backend process crashed!"
        exit 1
    fi
    
    # Try health check
    if curl -s "$BACKEND_URL/" > /dev/null 2>&1; then
        READY=true
        break
    fi
    
    # Show progress every 10 seconds
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

# Start frontend
echo "🌐 Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 2

echo ""
echo "=================================="
echo "✅ Application started!"
echo ""
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo ""
echo "   Press Ctrl+C to stop all services"
echo "=================================="

# Handle shutdown
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $FRONTEND_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait
