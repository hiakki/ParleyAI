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
export MODEL_PATH="${MODEL_PATH:-}"

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
cd backend
source venv/bin/activate
python server.py &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "   Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start!"
    exit 1
fi

echo "   ✓ Backend running on http://localhost:8000"
echo ""

# Start frontend
echo "🌐 Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

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
