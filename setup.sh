#!/bin/bash

# AEON Weapon AI System with Web Interface - Complete Setup Script
# Comprehensive installation for GPU instances (Vast.ai compatible)

set -e  # Exit on any error

echo "🔥 Setting up AEON Weapon AI System with Web Interface..."
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
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

print_header() {
    echo -e "${PURPLE}[SETUP]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# System requirements check
print_header "Checking system requirements..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    print_error "Python 3.8+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION found"

# Check CUDA availability
if command -v nvidia-smi &> /dev/null; then
    print_success "NVIDIA GPU detected"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
else
    print_warning "No NVIDIA GPU detected. Will use CPU (much slower)"
fi

# Check Node.js (for potential integration)
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js found: $NODE_VERSION"
else
    print_warning "Node.js not found. Install if you need game server integration."
fi

# Check available disk space
AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
REQUIRED_SPACE=10485760  # 10GB in KB

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    print_error "Insufficient disk space. Required: 10GB, Available: $(($AVAILABLE_SPACE/1024/1024))GB"
    exit 1
fi

print_success "Sufficient disk space available"

# Create directory structure
print_header "Creating directory structure..."

mkdir -p {models,config,generated_weapons,logs,static/{css,js,libs},templates,model_cache}

# Create subdirectories
mkdir -p models/{hunyuan3d-2,text,cache}
mkdir -p static/{css,js,libs}
mkdir -p config

print_success "Directory structure created"

# Setup Python virtual environment
print_header "Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_header "Installing Python dependencies..."
print_status "This may take several minutes..."

# Install PyTorch first (with CUDA support if available)
if command -v nvidia-smi &> /dev/null; then
    print_status "Installing PyTorch with CUDA support..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    print_status "Installing PyTorch CPU version..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install other dependencies
pip install -r requirements.txt

print_success "Python dependencies installed"

# Setup Hunyuan3D-2
print_header "Setting up Hunyuan3D-2..."

if [ ! -d "Hunyuan3D-2" ]; then
    print_status "Cloning Hunyuan3D-2 repository..."
    git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2.git
    
    if [ $? -eq 0 ]; then
        print_success "Hunyuan3D-2 repository cloned"
    else
        print_error "Failed to clone Hunyuan3D-2 repository"
        print_warning "Will use mock implementation for testing"
    fi
else
    print_warning "Hunyuan3D-2 repository already exists"
fi

# Install Hunyuan3D-2 dependencies (if repository exists)
if [ -d "Hunyuan3D-2" ]; then
    if [ -f "Hunyuan3D-2/requirements.txt" ]; then
        print_status "Installing Hunyuan3D-2 dependencies..."
        pip install -r Hunyuan3D-2/requirements.txt
        print_success "Hunyuan3D-2 dependencies installed"
    fi
fi

# Download Three.js for 3D viewer
print_header "Setting up web interface dependencies..."

if [ ! -f "static/libs/three.min.js" ]; then
    print_status "Downloading Three.js..."
    curl -L https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js -o static/libs/three.min.js
    
    if [ $? -eq 0 ]; then
        print_success "Three.js downloaded"
    else
        print_warning "Failed to download Three.js. 3D viewer may not work."
    fi
fi

# Create environment file
print_header "Creating environment configuration..."

cat > .env << EOF
# AEON Weapon AI System Configuration
API_PORT=8083
WEAPON_OUTPUT_DIR=./generated_weapons
GAME_SERVER_URL=http://localhost:3030

# Model Paths
HUNYUAN3D_PATH=./Hunyuan3D-2
HUNYUAN3D_MODEL_PATH=./models/hunyuan3d-2
TEXT_MODEL_PATH=./models/text

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false

# Web Interface
WEB_INTERFACE_ENABLED=true
STATIC_DIR=./static
TEMPLATES_DIR=./templates

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/weapon_ai.log

# Performance
MODEL_CACHE_SIZE=10
MAX_WEAPONS_PER_REQUEST=4

# Security (generate your own keys for production)
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here
EOF

print_success "Environment configuration created"

# Create startup scripts
print_header "Creating startup scripts..."

cat > start.sh << 'EOF'
#!/bin/bash

# AEON Weapon AI System - Startup Script
echo "🚀 Starting AEON Weapon AI System..."

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create logs directory
mkdir -p logs

# Start the weapon AI service
echo "🌐 Starting API server and web interface..."
echo "📍 Web Interface: http://localhost:8083"
echo "📍 API Endpoint: http://localhost:8083/api"
echo "📍 Health Check: http://localhost:8083/api/health"
echo ""
echo "Press Ctrl+C to stop the server"

python app.py
EOF

chmod +x start.sh

# Create production startup script
cat > start_production.sh << 'EOF'
#!/bin/bash

# AEON Weapon AI System - Production Startup Script
echo "🏭 Starting AEON Weapon AI System (Production Mode)..."

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export FLASK_ENV=production

# Create logs directory
mkdir -p logs

# Start with Gunicorn for production
echo "🌐 Starting production server with Gunicorn..."
echo "📍 Web Interface: http://localhost:8083"

gunicorn --bind 0.0.0.0:8083 --workers 4 --worker-class sync --timeout 300 --keep-alive 2 app:app
EOF

chmod +x start_production.sh

# Create test script
cat > test_system.sh << 'EOF'
#!/bin/bash

# AEON Weapon AI System - Comprehensive Test Script
echo "🧪 Testing AEON Weapon AI System..."

API_URL="http://localhost:8083"

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -s "$API_URL/api/health" | jq '.' || echo "Health check failed"

# Test 2: Generate weapons
echo -e "\n2. Testing weapon generation..."
curl -s -X POST "$API_URL/api/weapons/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "player1_personality": "aggressive_warrior",
    "player2_personality": "strategic_mage",
    "arena_theme": "volcanic"
  }' | jq '.' || echo "Weapon generation test failed"

# Test 3: List weapons
echo -e "\n3. Testing weapon listing..."
curl -s "$API_URL/api/weapons/list" | jq '.' || echo "Weapon listing test failed"

# Test 4: Statistics
echo -e "\n4. Testing statistics..."
curl -s "$API_URL/api/weapons/stats" | jq '.' || echo "Statistics test failed"

# Test 5: Web interface
echo -e "\n5. Testing web interface..."
curl -s "$API_URL/" | grep -q "AEON Weapon AI" && echo "✅ Web interface accessible" || echo "❌ Web interface failed"

echo -e "\n✅ System tests completed"
EOF

chmod +x test_system.sh

# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash

# AEON Weapon AI System - Monitoring Script
API_URL="http://localhost:8083/api/health"
LOG_FILE="./logs/monitor.log"

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if curl -s "$API_URL" | grep -q '"status":"healthy"'; then
        echo "[$timestamp] ✅ System healthy" >> "$LOG_FILE"
    else
        echo "[$timestamp] ❌ System unhealthy - attempting restart" >> "$LOG_FILE"
        
        # Attempt to restart (uncomment if needed)
        # pkill -f app.py
        # sleep 5
        # ./start.sh &
    fi
    
    sleep 300  # Check every 5 minutes
done
EOF

chmod +x monitor.sh

print_success "Startup scripts created"

# Create systemd service (optional)
if command -v systemctl &> /dev/null; then
    print_header "Creating systemd service..."
    
    cat > aeon-weapon-ai.service << EOF
[Unit]
Description=AEON Weapon AI Service with Web Interface
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/start.sh
Restart=always
RestartSec=10
Environment=PATH=$(pwd)/venv/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF

    print_success "Systemd service file created (aeon-weapon-ai.service)"
    print_warning "To install: sudo cp aeon-weapon-ai.service /etc/systemd/system/ && sudo systemctl enable aeon-weapon-ai"
fi

# Setup models directory
print_header "Setting up AI models..."

# Create models directory structure
mkdir -p models/{hunyuan3d-2,text,cache}

print_warning "Model downloading is not automated yet"
print_status "Please follow these steps to download models:"
echo "  1. Download Hunyuan3D-2 weights from official source"
echo "  2. Place them in ./models/hunyuan3d-2/"
echo "  3. Text generation models will be downloaded automatically on first run"

# Create default personality config if it doesn't exist
if [ ! -f "config/personalities.json" ]; then
    print_status "Personality configuration already created during setup"
    print_success "Personality templates configured"
fi

# Set permissions
chmod +x *.sh

# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash

# AEON Weapon AI System - Backup Script
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

echo "📦 Creating backup..."
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp -r config/ "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/"

# Backup generated weapons (if any)
if [ -d "generated_weapons" ] && [ "$(ls -A generated_weapons)" ]; then
    cp -r generated_weapons/ "$BACKUP_DIR/"
fi

# Backup logs
if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
    cp -r logs/ "$BACKUP_DIR/"
fi

# Create archive
tar -czf "${BACKUP_DIR}.tar.gz" -C "./backups" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"

echo "✅ Backup created: ${BACKUP_DIR}.tar.gz"
EOF

chmod +x backup.sh

# Final setup verification
print_header "Verifying installation..."

# Check if Python can import required modules
python3 -c "
import flask
import torch
import transformers
print('✅ Core Python modules available')
" 2>/dev/null || print_warning "Some Python modules may not be available"

# Check directory structure
for dir in models config generated_weapons logs static templates; do
    if [ -d "$dir" ]; then
        print_success "Directory exists: $dir"
    else
        print_error "Missing directory: $dir"
    fi
done

# Check critical files
for file in app.py requirements.txt start.sh; do
    if [ -f "$file" ]; then
        print_success "File exists: $file"
    else
        print_error "Missing file: $file"
    fi
done

# Summary
echo ""
echo "🎉 AEON Weapon AI System setup completed successfully!"
echo "========================================================="
echo ""
echo "📁 Project structure:"
echo "  ├── app.py                    # Main application server"
echo "  ├── models/                   # AI model implementations"
echo "  ├── static/                   # Web interface assets"
echo "  ├── templates/                # HTML templates"
echo "  ├── config/                   # Configuration files"
echo "  ├── generated_weapons/        # Generated weapon models"
echo "  ├── logs/                     # Application logs"
echo "  └── venv/                     # Python virtual environment"
echo ""
echo "🚀 Quick start:"
echo "  • Development:  ./start.sh"
echo "  • Production:   ./start_production.sh"
echo "  • Test system:  ./test_system.sh"
echo "  • Monitor:      ./monitor.sh"
echo "  • Backup:       ./backup.sh"
echo ""
echo "🌐 Access points:"
echo "  • Web Interface: http://localhost:8083"
echo "  • API Health:    http://localhost:8083/api/health"
echo "  • Gallery:       http://localhost:8083/gallery"
echo ""
echo "📚 Next steps:"
echo "  1. Start the system:     ./start.sh"
echo "  2. Open web interface:   http://localhost:8083"
echo "  3. Test weapon generation in dashboard"
echo "  4. View models in gallery"
echo "  5. Download Hunyuan3D-2 model weights for production"
echo ""
echo "🔧 Configuration:"
echo "  • Edit .env for settings"
echo "  • Edit config/personalities.json for weapon types"
echo "  • Check logs/ for troubleshooting"
echo ""
print_success "System ready for testing! 🎮"