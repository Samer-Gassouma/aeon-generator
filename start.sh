#!/bin/bash

# AEON Weapon AI System - Main Startup Script
# Starts the complete system with web interface and API

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

# ASCII Art Banner
echo -e "${PURPLE}"
cat << 'EOF'
   ╔═══════════════════════════════════════════════════════════════╗
   ║                                                               ║
   ║     █████╗ ███████╗ ██████╗ ███╗   ██╗                      ║
   ║    ██╔══██╗██╔════╝██╔═══██╗████╗  ██║                      ║
   ║    ███████║█████╗  ██║   ██║██╔██╗ ██║                      ║
   ║    ██╔══██║██╔══╝  ██║   ██║██║╚██╗██║                      ║
   ║    ██║  ██║███████╗╚██████╔╝██║ ╚████║                      ║
   ║    ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝                      ║
   ║                                                               ║
   ║    🔫 WEAPON AI SYSTEM with WEB INTERFACE 🔫                 ║
   ║                                                               ║
   ╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-flight checks
print_status "Running pre-flight checks..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run ./setup.sh first"
    exit 1
fi

# Check if main application exists
if [ ! -f "app.py" ]; then
    print_error "app.py not found. Please ensure all files are in place"
    exit 1
fi

# Check if dependencies are installed
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found"
    exit 1
fi

print_success "Pre-flight checks passed"

# Activate virtual environment
print_status "Activating Python virtual environment..."
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create necessary directories
print_status "Creating runtime directories..."
mkdir -p logs generated_weapons model_cache

# Check Python dependencies
print_status "Checking Python dependencies..."
python3 -c "
import flask
import torch
import transformers
print('✅ Core dependencies available')
" 2>/dev/null || {
    print_warning "Some dependencies may be missing. Installing..."
    pip install -r requirements.txt
}

# Check GPU availability
print_status "Checking GPU availability..."
if python3 -c "import torch; print('GPU Available:', torch.cuda.is_available())" 2>/dev/null; then
    print_success "GPU check completed"
else
    print_warning "Could not check GPU status"
fi

# Check system resources
print_status "Checking system resources..."

# Check memory
TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}')
AVAILABLE_MEM=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}')
print_status "Memory: ${AVAILABLE_MEM}GB available / ${TOTAL_MEM}GB total"

# Check disk space
DISK_SPACE=$(df -h . | awk 'NR==2 {print $4}')
print_status "Disk space available: $DISK_SPACE"

# Port check
PORT=8083
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    print_warning "Port $PORT is already in use. Attempting to stop existing process..."
    pkill -f "app.py" || true
    sleep 2
fi

# Create startup log
LOG_FILE="logs/startup_$(date +%Y%m%d_%H%M%S).log"
print_status "Logging to: $LOG_FILE"

# Display startup information
echo ""
echo -e "${GREEN}🚀 Starting AEON Weapon AI System...${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}📍 System Information:${NC}"
echo "   • API Port: $PORT"
echo "   • Environment: $([ "$FLASK_ENV" = "production" ] && echo "Production" || echo "Development")"
echo "   • Python: $(python3 --version)"
echo "   • Working Directory: $(pwd)"
echo ""
echo -e "${BLUE}🌐 Access Points:${NC}"
echo "   • Web Interface:  http://localhost:$PORT"
echo "   • API Health:     http://localhost:$PORT/api/health"
echo "   • Model Gallery:  http://localhost:$PORT/gallery"
echo "   • API Docs:       http://localhost:$PORT/api"
echo ""
echo -e "${BLUE}⚡ Features Available:${NC}"
echo "   • ✅ AI Weapon Generation"
echo "   • ✅ 3D Model Creation" 
echo "   • ✅ Web Dashboard"
echo "   • ✅ Model Gallery with 3D Viewer"
echo "   • ✅ Real-time Statistics"
echo "   • ✅ Batch Downloads"
echo "   • ✅ API Testing Interface"
echo ""
echo -e "${YELLOW}📝 Usage:${NC}"
echo "   1. Open http://localhost:$PORT in your browser"
echo "   2. Select player personalities in the dashboard"
echo "   3. Click 'Generate Weapons' to create 4 unique weapons"
echo "   4. View generated models in the gallery"
echo "   5. Download individual weapons or batch download all"
echo ""
echo -e "${YELLOW}🔧 Controls:${NC}"
echo "   • Press Ctrl+C to stop the server"
echo "   • Check logs/ directory for troubleshooting"
echo "   • Use ./test_system.sh to run tests"
echo "   • Use ./monitor.sh for health monitoring"
echo ""

# Create a cleanup function
cleanup() {
    echo ""
    print_status "Shutting down AEON Weapon AI System..."
    
    # Kill any background processes
    jobs -p | xargs -r kill
    
    # Save final stats
    if [ -f "logs/session_stats.json" ]; then
        mv logs/session_stats.json "logs/session_stats_$(date +%Y%m%d_%H%M%S).json"
    fi
    
    print_success "System stopped gracefully"
    echo -e "${PURPLE}Thank you for using AEON Weapon AI System! 🎮${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Final check before starting
print_status "Performing final system check..."

# Test import of main modules
python3 -c "
try:
    from models.text_generator import WeaponTextGenerator
    from models.model_generator import WeaponModelGenerator
    print('✅ AI modules can be imported')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
" || {
    print_error "Critical modules cannot be imported"
    exit 1
}

print_success "All systems ready!"

# Start the application
echo ""
echo -e "${GREEN}🎮 LAUNCHING AEON WEAPON AI SYSTEM...${NC}"
echo ""

# Start with logging
exec python3 app.py 2>&1 | tee "$LOG_FILE"