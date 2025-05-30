#!/bin/bash

# Fixed Local Setup for AEON Weapon Generator
echo "🎮 Setting up AEON Throwable Weapon Generator (Local Version)..."

# Check if we have Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+ first"
    exit 1
fi

# Create project directory in user's home
PROJECT_DIR="$HOME/aeon-weapon-generator"
echo "📁 Creating project directory at: $PROJECT_DIR"

# Remove existing directory if it exists
if [ -d "$PROJECT_DIR" ]; then
    echo "⚠️ Directory exists. Removing old installation..."
    rm -rf "$PROJECT_DIR"
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Download the repository files directly
echo "📥 Downloading project files..."

# Download main files
curl -o app.py https://raw.githubusercontent.com/Samer-Gassouma/aeon-generator/main/app.py
curl -o requirements.txt https://raw.githubusercontent.com/Samer-Gassouma/aeon-generator/main/requirements.txt
curl -o test_api.py https://raw.githubusercontent.com/Samer-Gassouma/aeon-generator/main/test_api.py

# Create requirements.txt if download failed
if [ ! -f "requirements.txt" ]; then
    echo "📝 Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
transformers==4.36.0
torch==2.1.0
requests==2.31.0
pydantic==2.5.0
python-multipart==0.0.6
trimesh==4.0.5
numpy==1.24.3
EOF
fi

# Create app.py if download failed
if [ ! -f "app.py" ]; then
    echo "📝 Creating basic app.py..."
    cat > app.py << 'EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import random
import uuid

app = FastAPI(title="AEON Throwable Weapon Generator")

class PlayerPersonality(BaseModel):
    archetype: str
    aggression: float
    creativity: float
    precision: float

class ArenaRequest(BaseModel):
    player1: PlayerPersonality
    player2: PlayerPersonality
    arena_type: str = "standard"

class ThrowableWeapon(BaseModel):
    weaponName: str
    description: str
    fileLocation: str
    damage: int
    speed: int
    weight: float
    throwingRange: int

class ArenaResponse(BaseModel):
    weapons: List[ThrowableWeapon]
    generation_id: str

THROWABLE_TEMPLATES = {
    "warrior": ["throwing axe", "war hammer", "heavy spear", "battle stone"],
    "mage": ["crystal orb", "magic staff", "enchanted stone", "spell scroll"],
    "rogue": ["throwing knife", "poison dart", "smoke bomb", "caltrops"],
    "archer": ["weighted arrow", "hunting javelin", "throwing star", "sling stone"]
}

def generate_throwable_description(archetype: str, personality: PlayerPersonality) -> str:
    templates = THROWABLE_TEMPLATES.get(archetype, THROWABLE_TEMPLATES["warrior"])
    base_weapon = random.choice(templates)
    
    modifiers = []
    if personality.aggression > 0.7:
        modifiers.extend(["serrated", "brutal", "heavy", "menacing"])
    if personality.creativity > 0.7:
        modifiers.extend(["ornate", "unusual", "mystical", "crafted"])
    if personality.precision > 0.7:
        modifiers.extend(["balanced", "sharp", "aerodynamic", "precise"])
    
    modifier = random.choice(modifiers) if modifiers else "simple"
    return f"A {modifier} {base_weapon}"

def generate_weapon_stats(personality: PlayerPersonality) -> dict:
    base_damage = random.randint(60, 100)
    base_speed = random.randint(70, 95)
    base_weight = random.uniform(0.5, 3.0)
    base_range = random.randint(8, 15)
    
    if personality.aggression > 0.7:
        base_damage += 15
        base_weight += 0.5
    if personality.precision > 0.7:
        base_speed += 10
        base_range += 3
    if personality.creativity > 0.7:
        base_damage += random.randint(-10, 20)
    
    return {
        "damage": min(120, base_damage),
        "speed": min(100, base_speed),
        "weight": round(base_weight, 1),
        "throwingRange": min(20, base_range)
    }

@app.post("/generate-arena-weapons", response_model=ArenaResponse)
async def generate_arena_weapons(request: ArenaRequest):
    try:
        weapons = []
        generation_id = str(uuid.uuid4())
        
        for i in range(4):
            player = request.player1 if i % 2 == 0 else request.player2
            description = generate_throwable_description(player.archetype, player)
            stats = generate_weapon_stats(player)
            
            weapon_name = description.replace("A ", "").replace("a ", "").title()
            filename = f"throwable_{uuid.uuid4().hex[:8]}.obj"
            
            weapon = ThrowableWeapon(
                weaponName=weapon_name,
                description=description,
                fileLocation=f"/arena/weapons/{filename}",
                damage=stats["damage"],
                speed=stats["speed"],
                weight=stats["weight"],
                throwingRange=stats["throwingRange"]
            )
            weapons.append(weapon)
        
        return ArenaResponse(weapons=weapons, generation_id=generation_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "AEON Weapon Generator is running"}

@app.get("/")
async def root():
    return {
        "message": "AEON Throwable Weapon Generator API",
        "endpoints": [
            "POST /generate-arena-weapons - Generate weapons for arena",
            "GET /health - Health check",
            "GET /docs - API documentation"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
fi

# Create test_api.py if download failed
if [ ! -f "test_api.py" ]; then
    echo "📝 Creating test_api.py..."
    cat > test_api.py << 'EOF'
import requests
import json

def test_weapon_generation():
    url = "http://localhost:8000/generate-arena-weapons"
    
    payload = {
        "player1": {
            "archetype": "warrior",
            "aggression": 0.8,
            "creativity": 0.3,
            "precision": 0.6
        },
        "player2": {
            "archetype": "mage",
            "aggression": 0.2,
            "creativity": 0.9,
            "precision": 0.7
        }
    }
    
    print("🧪 Testing weapon generation...")
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Generated {len(result['weapons'])} weapons:")
            
            for i, weapon in enumerate(result['weapons'], 1):
                print(f"\n🗡️ Weapon {i}:")
                print(f"  Name: {weapon['weaponName']}")
                print(f"  Description: {weapon['description']}")
                print(f"  Damage: {weapon['damage']}")
                print(f"  Speed: {weapon['speed']}")
                print(f"  Weight: {weapon['weight']} kg")
                print(f"  Range: {weapon['throwingRange']} meters")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the server is running!")

if __name__ == "__main__":
    test_weapon_generation()
EOF
fi

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Create directories
mkdir -p generated_weapons
mkdir -p logs

# Create startup script
cat > start_server.sh << 'EOF'
#!/bin/bash
cd "$HOME/aeon-weapon-generator"
source venv/bin/activate
echo "🚀 Starting AEON Weapon Generator API..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📖 API docs at: http://localhost:8000/docs"
echo "🛑 Press Ctrl+C to stop the server"
python3 app.py
EOF

chmod +x start_server.sh

# Create stop script
cat > stop_server.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping AEON Weapon Generator..."
pkill -f "python3 app.py"
echo "✅ Server stopped"
EOF

chmod +x stop_server.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Project location: $PROJECT_DIR"
echo ""
echo "🚀 To start the server:"
echo "   cd $PROJECT_DIR"
echo "   ./start_server.sh"
echo ""
echo "🧪 To test the API (in another terminal):"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   python3 test_api.py"
echo ""
echo "🌐 Once running, visit: http://localhost:8000/docs"
echo ""