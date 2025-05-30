#!/usr/bin/env python3
"""
Test Client & Integration Example
Demonstrates how to integrate Weapon AI Service with AEON game server
"""

import requests
import json
import time
from typing import Dict, List, Any

class WeaponAIClient:
    """Client for interacting with Weapon AI Service"""
    
    def __init__(self, base_url: str = "http://localhost:8083"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the AI service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def generate_weapons(self, player1_personality: str, player2_personality: str, 
                        arena_theme: str = "medieval") -> Dict[str, Any]:
        """Generate weapons based on player personalities"""
        
        payload = {
            "player1_personality": player1_personality,
            "player2_personality": player2_personality,
            "arena_theme": arena_theme
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/weapons/generate",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def create_3d_models(self, weapons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate 3D models for weapons"""
        
        payload = {"weapons": weapons}
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/weapons/batch-create",
                json=payload,
                timeout=300  # 5 minutes for model generation
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def full_weapon_generation_pipeline(self, player1_personality: str, 
                                      player2_personality: str, 
                                      arena_theme: str = "medieval") -> Dict[str, Any]:
        """Complete pipeline: generate scenarios + 3D models"""
        
        print(f"🎯 Starting weapon generation pipeline...")
        print(f"   Player 1: {player1_personality}")
        print(f"   Player 2: {player2_personality}")
        print(f"   Arena: {arena_theme}")
        
        # Step 1: Generate weapon scenarios
        print("\n🔮 Generating weapon scenarios...")
        weapons_result = self.generate_weapons(player1_personality, player2_personality, arena_theme)
        
        if "error" in weapons_result:
            return {"error": f"Scenario generation failed: {weapons_result['error']}"}
        
        weapons = weapons_result.get("weapons", [])
        print(f"✅ Generated {len(weapons)} weapon scenarios")
        
        # Step 2: Generate 3D models
        print("\n🏗️ Generating 3D models...")
        models_result = self.create_3d_models(weapons)
        
        if "error" in models_result:
            return {"error": f"3D model generation failed: {models_result['error']}"}
        
        print("✅ 3D model generation completed")
        
        return {
            "weapons": weapons,
            "model_results": models_result,
            "summary": {
                "total_weapons": len(weapons),
                "successful_models": models_result.get("summary", {}).get("successful", 0),
                "player1_personality": player1_personality,
                "player2_personality": player2_personality,
                "arena_theme": arena_theme
            }
        }

# Integration example for AEON main node server
class AEONGameServerIntegration:
    """Example integration with AEON main node server"""
    
    def __init__(self, weapon_ai_url: str = "http://localhost:8083", 
                 game_server_url: str = "http://localhost:3030"):
        self.weapon_ai = WeaponAIClient(weapon_ai_url)
        self.game_server_url = game_server_url
    
    async def on_players_enter_arena(self, player1_id: str, player2_id: str, arena_id: str):
        """Called when two players enter arena - generates weapons"""
        
        try:
            # Step 1: Fetch player personalities from game database
            player1_data = await self.fetch_player_data(player1_id)
            player2_data = await self.fetch_player_data(player2_id)
            
            player1_personality = player1_data.get("archetype", "aggressive_warrior")
            player2_personality = player2_data.get("archetype", "strategic_mage")
            
            # Step 2: Get arena theme
            arena_data = await self.fetch_arena_data(arena_id)
            arena_theme = arena_data.get("theme", "medieval")
            
            # Step 3: Generate weapons using AI service
            result = self.weapon_ai.full_weapon_generation_pipeline(
                player1_personality, player2_personality, arena_theme
            )
            
            if "error" in result:
                print(f"❌ Weapon generation failed: {result['error']}")
                return False
            
            # Step 4: Store weapons in game database
            weapons = result["weapons"]
            await self.store_arena_weapons(arena_id, weapons)
            
            # Step 5: Notify Unity clients about new weapons
            await self.notify_unity_clients(arena_id, weapons)
            
            print(f"🎮 Arena {arena_id} equipped with {len(weapons)} AI-generated weapons!")
            return True
            
        except Exception as e:
            print(f"❌ Arena setup failed: {e}")
            return False
    
    async def fetch_player_data(self, player_id: str) -> Dict[str, Any]:
        """Fetch player data from game database"""
        # This would interact with your PostgreSQL database
        # Example implementation:
        return {
            "player_id": player_id,
            "archetype": "aggressive_warrior",  # From UserArchetype table
            "personality_traits": ["aggressive", "competitive"],
            "level": 15
        }
    
    async def fetch_arena_data(self, arena_id: str) -> Dict[str, Any]:
        """Fetch arena configuration"""
        return {
            "arena_id": arena_id,
            "theme": "volcanic",
            "size": "medium",
            "environment": "lava_cave"
        }
    
    async def store_arena_weapons(self, arena_id: str, weapons: List[Dict[str, Any]]):
        """Store generated weapons in game database"""
        # This would save weapons to your database for the arena session
        print(f"💾 Storing {len(weapons)} weapons for arena {arena_id}")
        
        for weapon in weapons:
            print(f"   - {weapon['weaponName']} (Player {weapon['player']})")
    
    async def notify_unity_clients(self, arena_id: str, weapons: List[Dict[str, Any]]):
        """Notify Unity clients about available weapons"""
        # This would send WebSocket message to Unity clients
        message = {
            "type": "weapons_spawned",
            "arena_id": arena_id,
            "weapons": weapons
        }
        print(f"📡 Notifying Unity clients: {len(weapons)} weapons available")

def test_weapon_ai_service():
    """Test the Weapon AI Service"""
    
    print("🧪 Testing Weapon AI Service")
    print("=" * 50)
    
    client = WeaponAIClient()
    
    # Test 1: Health check
    print("\n1. Health Check")
    health = client.health_check()
    print(f"   Status: {health.get('status', 'unknown')}")
    print(f"   Models loaded: {health.get('models_loaded', False)}")
    print(f"   GPU available: {health.get('gpu_available', False)}")
    
    if health.get("status") != "healthy":
        print("❌ Service not healthy, aborting tests")
        return
    
    # Test 2: Generate weapon scenarios
    print("\n2. Weapon Scenario Generation")
    start_time = time.time()
    
    result = client.generate_weapons(
        player1_personality="aggressive_warrior",
        player2_personality="strategic_mage",
        arena_theme="volcanic"
    )
    
    scenario_time = time.time() - start_time
    
    if "error" in result:
        print(f"❌ Failed: {result['error']}")
        return
    
    weapons = result.get("weapons", [])
    print(f"✅ Generated {len(weapons)} weapons in {scenario_time:.2f}s")
    
    for i, weapon in enumerate(weapons):
        print(f"   {i+1}. {weapon['weaponName']} (Player {weapon['player']})")
        print(f"      Damage: {weapon['damage']}, Speed: {weapon['speed']}")
        print(f"      Description: {weapon['description'][:60]}...")
    
    # Test 3: Generate 3D models (this will take longer)
    print(f"\n3. 3D Model Generation")
    print("   ⏳ This may take several minutes...")
    
    start_time = time.time()
    model_result = client.create_3d_models(weapons)
    model_time = time.time() - start_time
    
    if "error" in model_result:
        print(f"❌ Failed: {model_result['error']}")
        return
    
    summary = model_result.get("summary", {})
    print(f"✅ Model generation completed in {model_time:.2f}s")
    print(f"   Total: {summary.get('total', 0)}")
    print(f"   Successful: {summary.get('successful', 0)}")
    print(f"   Failed: {summary.get('failed', 0)}")
    
    # Show results
    results = model_result.get("results", [])
    for result in results:
        status_emoji = "✅" if result["status"] == "completed" else "❌"
        print(f"   {status_emoji} {result['weapon_name']}: {result['status']}")
    
    print(f"\n🎉 All tests completed successfully!")
    print(f"💾 Generated weapon models are available in the generated_weapons/ directory")

def demo_integration():
    """Demo the integration with AEON game server"""
    
    print("\n🎮 AEON Integration Demo")
    print("=" * 50)
    
    integration = AEONGameServerIntegration()
    
    # Simulate players entering arena
    import asyncio
    
    async def simulate_arena_entry():
        success = await integration.on_players_enter_arena(
            player1_id="player_001",
            player2_id="player_002", 
            arena_id="arena_volcanic_01"
        )
        
        if success:
            print("🏆 Arena successfully equipped with AI-generated weapons!")
        else:
            print("💥 Arena setup failed")
    
    # Run the simulation
    asyncio.run(simulate_arena_entry())

if __name__ == "__main__":
    print("🔥 AEON Weapon AI Service - Test Client")
    print("=" * 60)
    
    # Test the AI service
    test_weapon_ai_service()
    
    # Demo integration
    demo_integration()
    
    print("\n✨ Testing completed!")
    print("\n📖 Integration Notes:")
    print("   • Add this client to your AEON main node server")
    print("   • Call on_players_enter_arena() when players join arena")
    print("   • Generated weapons will be stored and sent to Unity clients")
    print("   • Modify file paths and database queries for your setup")