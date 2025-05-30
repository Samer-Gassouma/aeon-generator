from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import uuid
import os
import json
import random
from typing import List, Dict, Optional
from datetime import datetime
import uvicorn

app = FastAPI(title="AEON Weapon Generator", version="1.0.0")

# Create directories
os.makedirs("generated_weapons", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage for jobs (replace with Redis in production)
generation_jobs = {}

class PlayerPersonality(BaseModel):
    archetype: str  # e.g., "warrior", "mage", "rogue", "paladin"
    traits: List[str]  # e.g., ["aggressive", "tactical", "mystical"]
    power_level: int  # 1-100

class WeaponRequest(BaseModel):
    arena_id: str
    player1: PlayerPersonality
    player2: PlayerPersonality

class WeaponData(BaseModel):
    weapon_name: str
    description: str
    file_location: str
    damage: int
    speed: int
    rarity: str

class JobStatus(BaseModel):
    job_id: str
    status: str  # "processing", "completed", "failed"
    progress: int  # 0-100
    weapons: Optional[List[WeaponData]] = None
    error: Optional[str] = None

# Weapon generation templates based on personality combinations
WEAPON_TEMPLATES = {
    "warrior": {
        "names": ["Berserker's Blade", "Iron Cleaver", "Battle Axe", "Warhammer"],
        "descriptions": ["massive two-handed sword with battle scars", "heavy iron axe with tribal markings", "ancient warhammer with glowing runes", "serrated blade dripping with power"],
        "damage_range": (80, 100),
        "speed_range": (20, 40)
    },
    "mage": {
        "names": ["Arcane Staff", "Crystal Wand", "Flame Rod", "Ice Scepter"],
        "descriptions": ["mystical staff crowned with floating crystals", "elegant wand pulsing with magical energy", "staff channeling elemental fire", "frozen scepter radiating cold power"],
        "damage_range": (60, 80),
        "speed_range": (70, 90)
    },
    "rogue": {
        "names": ["Shadow Dagger", "Poison Blade", "Silent Edge", "Assassin's Fang"],
        "descriptions": ["curved dagger wreathed in shadows", "twin blades coated with venom", "nearly invisible blade that bends light", "serrated knife designed for stealth kills"],
        "damage_range": (50, 70),
        "speed_range": (80, 100)
    },
    "paladin": {
        "names": ["Holy Sword", "Divine Mace", "Light Bringer", "Sacred Hammer"],
        "descriptions": ["radiant sword blessed by divine light", "golden mace emanating holy energy", "weapon forged from pure light", "hammer that purifies evil"],
        "damage_range": (70, 85),
        "speed_range": (50, 70)
    }
}

def generate_weapon_scenario(p1: PlayerPersonality, p2: PlayerPersonality, index: int) -> WeaponData:
    """Generate a weapon based on player personalities"""
    
    # Choose dominant archetype
    archetypes = [p1.archetype, p2.archetype]
    chosen_archetype = random.choice(archetypes)
    
    if chosen_archetype not in WEAPON_TEMPLATES:
        chosen_archetype = "warrior"  # fallback
    
    template = WEAPON_TEMPLATES[chosen_archetype]
    
    # Generate weapon properties
    weapon_name = random.choice(template["names"])
    base_description = random.choice(template["descriptions"])
    
    # Add personality influence to description
    traits = p1.traits + p2.traits
    if "aggressive" in traits:
        base_description += " with razor-sharp edges"
    if "mystical" in traits:
        base_description += " glowing with ancient magic"
    if "tactical" in traits:
        base_description += " designed for precise strikes"
    
    # Calculate stats based on personalities
    avg_power = (p1.power_level + p2.power_level) / 2
    power_modifier = avg_power / 100
    
    damage = random.randint(*template["damage_range"])
    damage = int(damage * (0.8 + 0.4 * power_modifier))
    
    speed = random.randint(*template["speed_range"])
    speed = int(speed * (0.8 + 0.4 * power_modifier))
    
    # Determine rarity
    rarity_roll = random.random()
    if rarity_roll < 0.05:
        rarity = "legendary"
        damage = int(damage * 1.5)
    elif rarity_roll < 0.2:
        rarity = "epic"
        damage = int(damage * 1.3)
    elif rarity_roll < 0.5:
        rarity = "rare"
        damage = int(damage * 1.1)
    else:
        rarity = "common"
    
    file_name = f"weapon_{index}_{uuid.uuid4().hex[:8]}.glb"
    
    return WeaponData(
        weapon_name=weapon_name,
        description=base_description,
        file_location=f"/static/{file_name}",
        damage=damage,
        speed=speed,
        rarity=rarity
    )

async def generate_3d_weapon(description: str, file_path: str) -> bool:
    """Generate 3D weapon using Hunyuan3D-2"""
    try:
        # Import here to avoid issues if not installed
        from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
        from hy3dgen.texgen import Hunyuan3DPaintPipeline
        
        print(f"Generating 3D model for: {description}")
        
        # Generate shape
        shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained('tencent/Hunyuan3D-2')
        mesh = shape_pipeline(prompt=description)[0]
        
        # Generate texture
        texture_pipeline = Hunyuan3DPaintPipeline.from_pretrained('tencent/Hunyuan3D-2')
        textured_mesh = texture_pipeline(mesh, prompt=description)
        
        # Export as GLB
        textured_mesh.export(file_path)
        
        print(f"Successfully generated: {file_path}")
        return True
        
    except ImportError:
        print("Hunyuan3D-2 not installed, creating placeholder file")
        # Create placeholder GLB file for testing
        placeholder_content = b"GLB_PLACEHOLDER_FOR_TESTING"
        with open(file_path, "wb") as f:
            f.write(placeholder_content)
        return True
        
    except Exception as e:
        print(f"Error generating 3D model: {e}")
        return False

async def process_weapon_generation(job_id: str, request: WeaponRequest):
    """Background task to generate weapons"""
    try:
        generation_jobs[job_id]["status"] = "processing"
        generation_jobs[job_id]["progress"] = 10
        
        weapons = []
        
        # Generate 4 weapons
        for i in range(4):
            weapon_data = generate_weapon_scenario(request.player1, request.player2, i)
            weapons.append(weapon_data)
            
            # Update progress
            generation_jobs[job_id]["progress"] = 10 + (i * 20)
            
            # Generate 3D model
            file_name = os.path.basename(weapon_data.file_location)
            full_path = os.path.join("static", file_name)
            
            success = await generate_3d_weapon(weapon_data.description, full_path)
            
            if not success:
                raise Exception(f"Failed to generate 3D model for weapon {i}")
            
            # Update progress after each weapon
            generation_jobs[job_id]["progress"] = 30 + (i * 17)
        
        # Complete
        generation_jobs[job_id]["status"] = "completed"
        generation_jobs[job_id]["progress"] = 100
        generation_jobs[job_id]["weapons"] = weapons
        
        print(f"Job {job_id} completed successfully")
        
    except Exception as e:
        generation_jobs[job_id]["status"] = "failed"
        generation_jobs[job_id]["error"] = str(e)
        print(f"Job {job_id} failed: {e}")

@app.get("/")
async def root():
    return {
        "service": "AEON Weapon Generator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/weapons/generate",
            "/api/weapons/status/{job_id}",
            "/api/weapons/list",
            "/docs"
        ]
    }

@app.post("/api/weapons/generate")
async def generate_weapons(request: WeaponRequest, background_tasks: BackgroundTasks):
    """Start weapon generation for arena battle"""
    job_id = str(uuid.uuid4())
    
    # Initialize job
    generation_jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "request": request.dict()
    }
    
    # Start background generation
    background_tasks.add_task(process_weapon_generation, job_id, request)
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/weapons/status/{job_id}")
async def get_weapon_status(job_id: str):
    """Check status of weapon generation job"""
    if job_id not in generation_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = generation_jobs[job_id]
    return JobStatus(**job_data)

@app.get("/api/weapons/list")
async def list_generated_weapons():
    """List all generated weapons for debugging"""
    weapons = []
    static_dir = "static"
    
    if os.path.exists(static_dir):
        for file in os.listdir(static_dir):
            if file.endswith('.glb'):
                weapons.append({
                    "filename": file,
                    "path": f"/static/{file}",
                    "size": os.path.getsize(os.path.join(static_dir, file))
                })
    
    return {"weapons": weapons, "count": len(weapons)}

@app.delete("/api/weapons/cleanup/{job_id}")
async def cleanup_weapons(job_id: str):
    """Clean up generated weapons for a job"""
    if job_id not in generation_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = generation_jobs[job_id]
    deleted_files = []
    
    if job_data.get("weapons"):
        for weapon in job_data["weapons"]:
            file_name = os.path.basename(weapon["file_location"])
            file_path = os.path.join("static", file_name)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(file_name)
    
    # Remove job from memory
    del generation_jobs[job_id]
    
    return {"deleted_files": deleted_files, "job_removed": True}

@app.get("/api/test/sample-request")
async def get_sample_request():
    """Get sample request for testing"""
    return {
        "arena_id": "test_arena_001",
        "player1": {
            "archetype": "warrior",
            "traits": ["aggressive", "tactical"],
            "power_level": 75
        },
        "player2": {
            "archetype": "mage",
            "traits": ["mystical", "intelligent"],
            "power_level": 68
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)