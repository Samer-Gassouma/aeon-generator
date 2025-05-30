from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import os
import uuid
import random

app = FastAPI(title="AEON Throwable Weapon Generator")

# Models will be loaded globally
text_model = None
text_tokenizer = None
mesh_model = None
mesh_tokenizer = None

class PlayerPersonality(BaseModel):
    archetype: str  # e.g., "warrior", "mage", "rogue"
    aggression: float  # 0.0 - 1.0
    creativity: float  # 0.0 - 1.0
    precision: float   # 0.0 - 1.0

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

# Throwable weapon templates based on personalities
THROWABLE_TEMPLATES = {
    "warrior": ["throwing axe", "war hammer", "heavy spear", "battle stone"],
    "mage": ["crystal orb", "magic staff", "enchanted stone", "spell scroll"],
    "rogue": ["throwing knife", "poison dart", "smoke bomb", "caltrops"],
    "archer": ["weighted arrow", "hunting javelin", "throwing star", "sling stone"]
}

def load_models():
    """Load the AI models"""
    global text_model, text_tokenizer, mesh_model, mesh_tokenizer
    
    print("Loading models...")
    
    # Load LLaMA-Mesh model for text-to-3D generation
    try:
        model_name = "Zhengyi/LLaMA-Mesh"
        print(f"Loading {model_name}...")
        
        mesh_tokenizer = AutoTokenizer.from_pretrained(model_name)
        mesh_model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        print("LLaMA-Mesh loaded successfully!")
        
    except Exception as e:
        print(f"Error loading LLaMA-Mesh: {e}")
        print("Falling back to text-only generation...")
        
        # Fallback to smaller model
        fallback_model = "microsoft/DialoGPT-medium"
        text_tokenizer = AutoTokenizer.from_pretrained(fallback_model)
        text_model = AutoModelForCausalLM.from_pretrained(fallback_model)

def personality_to_prompt(p1: PlayerPersonality, p2: PlayerPersonality) -> str:
    """Convert personalities to weapon generation prompt"""
    
    # Determine dominant traits
    p1_dominant = max([("aggressive", p1.aggression), ("creative", p1.creativity), ("precise", p1.precision)], key=lambda x: x[1])
    p2_dominant = max([("aggressive", p2.aggression), ("creative", p2.creativity), ("precise", p2.precision)], key=lambda x: x[1])
    
    prompt = f"""Generate a throwable weapon for arena combat.

Player 1: {p1.archetype} (dominant trait: {p1_dominant[0]})
Player 2: {p2.archetype} (dominant trait: {p2_dominant[0]})

Create a simple throwable object that reflects these personalities. The weapon should be something a player can pick up and throw at their opponent.

Weapon description:"""

    return prompt

def generate_weapon_stats(description: str, personality: PlayerPersonality) -> Dict[str, Any]:
    """Generate weapon stats based on description and personality"""
    
    base_damage = random.randint(60, 100)
    base_speed = random.randint(70, 95)
    base_weight = random.uniform(0.5, 3.0)
    base_range = random.randint(8, 15)
    
    # Personality modifiers
    if personality.aggression > 0.7:
        base_damage += 15
        base_weight += 0.5
    
    if personality.precision > 0.7:
        base_speed += 10
        base_range += 3
        
    if personality.creativity > 0.7:
        base_damage += random.randint(-10, 20)  # More unpredictable
    
    return {
        "damage": min(120, base_damage),
        "speed": min(100, base_speed),
        "weight": round(base_weight, 1),
        "throwingRange": min(20, base_range)
    }

def generate_3d_mesh(description: str) -> str:
    """Generate 3D mesh using LLaMA-Mesh or return placeholder"""
    
    if mesh_model is None:
        # Return placeholder path for fallback
        filename = f"throwable_{uuid.uuid4().hex[:8]}.obj"
        return f"/arena/weapons/{filename}"
    
    try:
        # LLaMA-Mesh prompt format
        prompt = f"Generate a 3D model of: {description}"
        
        inputs = mesh_tokenizer(prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = mesh_model.generate(
                **inputs,
                max_length=512,
                temperature=0.8,
                do_sample=True,
                pad_token_id=mesh_tokenizer.eos_token_id
            )
        
        generated_text = mesh_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract OBJ content if generated
        if "v " in generated_text and "f " in generated_text:
            # Save the OBJ file
            filename = f"throwable_{uuid.uuid4().hex[:8]}.obj"
            filepath = f"./generated_weapons/{filename}"
            
            # Create directory if it doesn't exist
            os.makedirs("./generated_weapons", exist_ok=True)
            
            # Extract and save OBJ content
            obj_start = generated_text.find("v ")
            obj_content = generated_text[obj_start:]
            
            with open(filepath, 'w') as f:
                f.write(obj_content)
            
            return f"/arena/weapons/{filename}"
        else:
            # Fallback
            filename = f"throwable_{uuid.uuid4().hex[:8]}.obj"
            return f"/arena/weapons/{filename}"
            
    except Exception as e:
        print(f"3D generation error: {e}")
        filename = f"throwable_{uuid.uuid4().hex[:8]}.obj"
        return f"/arena/weapons/{filename}"

def generate_throwable_description(archetype: str, personality: PlayerPersonality) -> str:
    """Generate a simple throwable weapon description"""
    
    templates = THROWABLE_TEMPLATES.get(archetype, THROWABLE_TEMPLATES["warrior"])
    base_weapon = random.choice(templates)
    
    # Add personality-based modifiers
    modifiers = []
    
    if personality.aggression > 0.7:
        modifiers.extend(["serrated", "brutal", "heavy", "menacing"])
    if personality.creativity > 0.7:
        modifiers.extend(["ornate", "unusual", "mystical", "crafted"])
    if personality.precision > 0.7:
        modifiers.extend(["balanced", "sharp", "aerodynamic", "precise"])
    
    modifier = random.choice(modifiers) if modifiers else "simple"
    
    descriptions = {
        "throwing axe": f"A {modifier} throwing axe with a curved blade",
        "crystal orb": f"A {modifier} crystal orb that glows with inner energy",
        "throwing knife": f"A {modifier} throwing knife with perfect balance",
        "war hammer": f"A {modifier} war hammer designed for throwing",
        "magic staff": f"A {modifier} magic staff that can be hurled with force",
        "poison dart": f"A {modifier} dart tipped with potent toxins",
        "heavy spear": f"A {modifier} spear weighted for maximum throwing power",
        "enchanted stone": f"A {modifier} stone imbued with magical properties",
        "smoke bomb": f"A {modifier} smoke bomb that creates concealing clouds",
        "battle stone": f"A {modifier} stone carved for warfare",
        "spell scroll": f"A {modifier} scroll that explodes with magical energy",
        "caltrops": f"A {modifier} set of caltrops that scatter on impact",
        "weighted arrow": f"A {modifier} arrow designed for hand throwing",
        "hunting javelin": f"A {modifier} javelin crafted for precise throws",
        "throwing star": f"A {modifier} throwing star with razor edges",
        "sling stone": f"A {modifier} stone perfectly shaped for slinging"
    }
    
    return descriptions.get(base_weapon, f"A {modifier} {base_weapon}")

@app.on_event("startup")
async def startup_event():
    """Load models when server starts"""
    load_models()

@app.post("/generate-arena-weapons", response_model=ArenaResponse)
async def generate_arena_weapons(request: ArenaRequest):
    """Generate 4 throwable weapons for arena combat"""
    
    try:
        weapons = []
        generation_id = str(uuid.uuid4())
        
        # Generate 2 weapons per player
        for i in range(4):
            # Alternate between players
            player = request.player1 if i % 2 == 0 else request.player2
            
            # Generate weapon description
            description = generate_throwable_description(player.archetype, player)
            
            # Generate stats
            stats = generate_weapon_stats(description, player)
            
            # Generate 3D model
            file_location = generate_3d_mesh(description)
            
            # Create weapon name
            weapon_name = description.replace("A ", "").replace("a ", "").title()
            
            weapon = ThrowableWeapon(
                weaponName=weapon_name,
                description=description,
                fileLocation=file_location,
                damage=stats["damage"],
                speed=stats["speed"],
                weight=stats["weight"],
                throwingRange=stats["throwingRange"]
            )
            
            weapons.append(weapon)
        
        return ArenaResponse(
            weapons=weapons,
            generation_id=generation_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": mesh_model is not None or text_model is not None
    }

@app.get("/")
async def root():
    """Root endpoint with API info"""
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