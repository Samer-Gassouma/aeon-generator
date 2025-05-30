#!/bin/bash

# Weapon AI Service Setup Script
# For AEON MMORPG - Text-to-3D Weapon Generation

set -e  # Exit on any error

echo "🔥 Setting up Weapon AI Service for AEON..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check system requirements
print_status "Checking system requirements..."

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

# Check available disk space
AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
REQUIRED_SPACE=10485760  # 10GB in KB

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    print_error "Insufficient disk space. Required: 10GB, Available: $(($AVAILABLE_SPACE/1024/1024))GB"
    exit 1
fi

print_success "Sufficient disk space available"

# Create directory structure
print_status "Creating directory structure..."
mkdir -p models config generated_weapons logs

# Create configuration directories
mkdir -p config
mkdir -p logs

print_success "Directory structure created"

# Setup Python virtual environment
print_status "Setting up Python virtual environment..."

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
print_status "Installing Python dependencies..."
pip install -r requirements.txt

print_success "Python dependencies installed"

# Setup Hunyuan3D-2
print_status "Setting up Hunyuan3D-2..."

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

# Create environment file
print_status "Creating environment configuration..."

cat > .env << EOF
# Weapon AI Service Configuration
API_PORT=8083
WEAPON_OUTPUT_DIR=./generated_weapons
GAME_SERVER_URL=http://localhost:3030

# Model Paths
HUNYUAN3D_PATH=./Hunyuan3D-2
HUNYUAN3D_MODEL_PATH=./models/hunyuan3d-2
TEXT_MODEL_PATH=./models/text

# Flask Configuration
FLASK_DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/weapon_ai.log
EOF

print_success "Environment configuration created"

# Create personality configuration
print_status "Creating personality configuration..."

cat > config/personalities.json << 'EOF'
{
  "aggressive_warrior": {
    "weapon_types": ["axe", "sword", "mace", "warhammer", "claymore"],
    "materials": ["steel", "iron", "darksteel", "bloodsteel", "volcanic rock"],
    "effects": ["flame", "lightning", "poison", "ice", "shadow"],
    "descriptors": ["brutal", "massive", "serrated", "jagged", "intimidating", "fearsome"],
    "damage_modifier": 1.2,
    "speed_modifier": 0.8
  },
  "strategic_mage": {
    "weapon_types": ["staff", "wand", "orb", "tome", "crystal"],
    "materials": ["crystal", "enchanted wood", "mithril", "arcane stone", "starlight essence"],
    "effects": ["arcane", "frost", "shadow", "holy", "time", "void"],
    "descriptors": ["elegant", "mystical", "glowing", "ancient", "ethereal", "wise"],
    "damage_modifier": 0.9,
    "speed_modifier": 1.3
  },
  "defensive_guardian": {
    "weapon_types": ["shield", "lance", "hammer", "defensive blade", "tower shield"],
    "materials": ["blessed steel", "adamantite", "holy metal", "reinforced iron", "divine crystal"],
    "effects": ["protection", "barrier", "healing", "reflection", "blessing"],
    "descriptors": ["sturdy", "protective", "radiant", "fortified", "noble", "steadfast"],
    "damage_modifier": 0.8,
    "speed_modifier": 0.9
  },
  "agile_assassin": {
    "weapon_types": ["dagger", "blade", "throwing knife", "poison dart", "curved sword"],
    "materials": ["shadow steel", "quicksilver", "venom-coated metal", "silent steel", "void metal"],
    "effects": ["poison", "shadow", "stealth", "bleeding", "paralysis"],
    "descriptors": ["swift", "silent", "deadly", "precise", "curved", "razor-sharp"],
    "damage_modifier": 0.9,
    "speed_modifier": 1.4
  },
  "elemental_mage": {
    "weapon_types": ["elemental staff", "focus crystal", "elemental orb", "nature wand"],
    "materials": ["elemental crystal", "living wood", "storm glass", "earth stone"],
    "effects": ["fire", "water", "earth", "air", "lightning", "nature"],
    "descriptors": ["elemental", "flowing", "crackling", "growing", "shifting"],
    "damage_modifier": 1.0,
    "speed_modifier": 1.1
  }
}
EOF

print_success "Personality configuration created"

# Create startup script
print_status "Creating startup scripts..."

cat > start_server.sh << 'EOF'
#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the weapon AI service
echo "Starting Weapon AI Service..."
python app.py
EOF

chmod +x start_server.sh

# Create test script
cat > test_api.sh << 'EOF'
#!/bin/bash

# Test script for Weapon AI Service API
API_URL="http://localhost:8083"

echo "🧪 Testing Weapon AI Service API..."

# Test health endpoint
echo "Testing health endpoint..."
curl -s "$API_URL/api/health" | jq '.' || echo "Health check failed"

# Test weapon generation
echo -e "\nTesting weapon generation..."
curl -s -X POST "$API_URL/api/weapons/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "player1_personality": "aggressive_warrior",
    "player2_personality": "strategic_mage",
    "arena_theme": "volcanic"
  }' | jq '.' || echo "Weapon generation test failed"

echo -e "\n✅ API tests completed"
EOF

chmod +x test_api.sh

print_success "Startup scripts created"

# Create systemd service (optional)
if command -v systemctl &> /dev/null; then
    print_status "Creating systemd service..."
    
    cat > weapon-ai.service << EOF
[Unit]
Description=AEON Weapon AI Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/start_server.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    print_success "Systemd service file created (weapon-ai.service)"
    print_warning "To install: sudo cp weapon-ai.service /etc/systemd/system/ && sudo systemctl enable weapon-ai"
fi

# Download models (placeholder)
print_status "Setting up AI models..."

# Create models directory structure
mkdir -p models/{hunyuan3d-2,text,cache}

print_warning "Model downloading is not automated yet"
print_status "Please follow these steps to download models:"
echo "  1. Download Hunyuan3D-2 weights from official source"
echo "  2. Place them in ./models/hunyuan3d-2/"
echo "  3. Text generation models will be downloaded automatically on first run"

# Set permissions
chmod +x *.sh

# Final setup verification
print_status "Verifying installation..."

# Check if Python can import required modules
python3 -c "
import flask
import torch
import transformers
print('✅ Core Python modules available')
" 2>/dev/null || print_warning "Some Python modules may not be available"

# Summary
echo ""
echo "🎉 Setup completed successfully!"
echo "================================================"
echo ""
echo "📁 Project structure:"
echo "  ├── app.py              # Main API server"
echo "  ├── models/             # AI model implementations"
echo "  ├── config/             # Configuration files"
echo "  ├── generated_weapons/  # Output directory"
echo "  ├── logs/               # Log files"
echo "  └── venv/               # Python virtual environment"
echo ""
echo "🚀 Quick start:"
echo "  1. Start the service:    ./start_server.sh"
echo "  2. Test the API:         ./test_api.sh"
echo "  3. Check logs:           tail -f logs/weapon_ai.log"
echo ""
echo "🔗 API will be available at: http://localhost:8083"
echo ""
echo "📚 Next steps:"
echo "  • Download Hunyuan3D-2 model weights"
echo "  • Configure GPU instance on Vast.ai"
echo "  • Test integration with main game server"
echo ""
print_success "Ready for testing! 🎮"