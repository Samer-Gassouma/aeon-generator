#!/bin/bash

echo "🎮 Setting up AEON Throwable Weapon Generator..."

# Update system
apt-get update
apt-get install -y python3-pip git wget curl

# Create project directory
mkdir -p /workspace/aeon-weapon-generator
cd /workspace/aeon-weapon-generator

# Clone your repository
git clone https://github.com/Samer-Gassouma/aeon-generator.git .

# Create virtual environment
python3 -m venv venvs
source venv/bin/activate

# Install requirements
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p generated_weapons
mkdir -p logs

# Make scripts executable
chmod +x *.sh

# Pre-cache model (optional)
echo "🤖 Pre-loading model cache..."
python3 -c "
from transformers import AutoTokenizer
try:
    print('Downloading LLaMA-Mesh tokenizer...')
    tokenizer = AutoTokenizer.from_pretrained('Zhengyi/LLaMA-Mesh')
    print('✅ Model cache ready!')
except Exception as e:
    print(f'⚠️ Model download will happen on first run: {e}')
"

# Create startup script
cat > start_server.sh << 'EOF'
#!/bin/bash
cd /workspace/aeon-weapon-generator
source venv/bin/activate
echo "🚀 Starting AEON Weapon Generator API..."
echo "📍 Server will be available at: http://0.0.0.0:8000"
echo "📖 API docs at: http://0.0.0.0:8000/docs"
python3 app.py
EOF

chmod +x start_server.sh

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the server:"
echo "   ./start_server.sh"
echo ""
echo "🧪 To test the API:"
echo "   python3 test_api.py"