#!/bin/bash

# AEON Weapon Generator Deployment Script
# For use on vast.ai or other GPU instances

set -e

echo "🚀 AEON Weapon Generator Deployment"
echo "=================================="

# Check if CUDA is available
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "⚠️  No NVIDIA GPU detected, running in CPU mode"
fi

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -qq

# Install Python if not available
if ! command -v python3 &> /dev/null; then
    echo "🐍 Installing Python..."
    sudo apt-get install -y python3 python3-pip python3-dev
fi

# Install git if not available
if ! command -v git &> /dev/null; then
    echo "🔧 Installing Git..."
    sudo apt-get install -y git
fi

# Clone repository if not exists
if [ ! -d "aeon-generator" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/Samer-Gassoum/aeon-generator.git
    cd aeon-generator
else
    echo "📁 Repository already exists, updating..."
    cd aeon-generator
    git pull
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🔨 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install basic requirements
echo "📦 Installing basic requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if we should install GPU dependencies
if command -v nvidia-smi &> /dev/null; then
    echo "🎮 Installing GPU dependencies..."
    
    # Install PyTorch with CUDA
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
    
    # Install 3D generation dependencies
    pip install trimesh numpy pillow transformers diffusers accelerate
    
    # Ask if user wants to install Hunyuan3D-2
    read -p "Install Hunyuan3D-2 for 3D generation? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🤖 Installing Hunyuan3D-2..."
        
        # Clone Hunyuan3D-2 if not exists
        if [ ! -d "/tmp/Hunyuan3D-2" ]; then
            git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2.git /tmp/Hunyuan3D-2
        fi
        
        cd /tmp/Hunyuan3D-2
        pip install -r requirements.txt
        pip install -e .
        
        # Install texture generation components
        echo "🎨 Installing texture generation components..."
        cd hy3dgen/texgen/custom_rasterizer
        python3 setup.py install
        cd ../differentiable_renderer
        python3 setup.py install
        
        cd /root/aeon-generator || cd ~/aeon-generator
        echo "✅ Hunyuan3D-2 installation completed"
    else
        echo "⏩ Skipping Hunyuan3D-2 installation (will run in fallback mode)"
    fi
else
    echo "💻 CPU mode - skipping GPU dependencies"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p static generated_weapons

# Test the installation
echo "🧪 Testing installation..."
python -c "import fastapi, uvicorn; print('✅ FastAPI available')"

if command -v nvidia-smi &> /dev/null; then
    python -c "import torch; print(f'✅ PyTorch available, CUDA: {torch.cuda.is_available()}')" || echo "⚠️ PyTorch/CUDA issue"
fi

# Start the service
echo ""
echo "🎉 Installation completed!"
echo ""
echo "To start the service:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Or run the test client:"
echo "  python test_client.py"
echo ""
echo "Service will be available at:"
echo "  http://localhost:8000"
echo "  http://0.0.0.0:8000 (for external access)"
echo ""

# Ask if user wants to start the service now
read -p "Start the service now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting AEON Weapon Generator..."
    python main.py
else
    echo "👋 Setup complete! Start the service manually when ready."
fi