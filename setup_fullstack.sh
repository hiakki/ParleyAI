#!/bin/bash
# setup_fullstack.sh - Set up the full-stack Llama Chat application

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🦙 Setting up Llama 3.3 70B Chat Application"
echo "============================================="
echo ""

# Setup Backend
echo "📦 Setting up Backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "   Installing dependencies..."
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install -r requirements.txt

deactivate
cd ..
echo "   ✓ Backend setup complete"
echo ""

# Setup Frontend
echo "📦 Setting up Frontend..."
cd frontend

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found!"
    echo "   Install with: brew install node"
    exit 1
fi

echo "   Installing dependencies..."
npm install

cd ..
echo "   ✓ Frontend setup complete"
echo ""

echo "============================================="
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "   ./start.sh"
echo ""
echo "Or start individually:"
echo "   Backend:  cd backend && ./run_server.sh"
echo "   Frontend: cd frontend && npm run dev"
echo "============================================="
