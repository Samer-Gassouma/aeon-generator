import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:8000"  # Change this to your deployed URL

def test_weapon_generation():
    """Test the complete weapon generation flow"""
    
    print("🧪 Testing AEON Weapon Generator")
    print("=" * 50)
    
    # 1. Test service health
    print("1. Testing service health...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Service is running: {response.json()['service']}")
    except Exception as e:
        print(f"❌ Service health check failed: {e}")
        return
    
    # 2. Get sample request data
    print("\n2. Getting sample request data...")
    try:
        response = requests.get(f"{BASE_URL}/api/test/sample-request")
        sample_data = response.json()
        print(f"✅ Sample data received")
        print(f"   Player 1: {sample_data['player1']['archetype']} (Level {sample_data['player1']['power_level']})")
        print(f"   Player 2: {sample_data['player2']['archetype']} (Level {sample_data['player2']['power_level']})")
    except Exception as e:
        print(f"❌ Failed to get sample data: {e}")
        return
    
    # 3. Start weapon generation
    print("\n3. Starting weapon generation...")
    try:
        response = requests.post(f"{BASE_URL}/api/weapons/generate", json=sample_data)
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data["job_id"]
            print(f"✅ Generation started with job ID: {job_id}")
        else:
            print(f"❌ Generation failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Failed to start generation: {e}")
        return
    
    # 4. Monitor generation progress
    print("\n4. Monitoring generation progress...")
    max_attempts = 30  # 30 seconds timeout
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{BASE_URL}/api/weapons/status/{job_id}")
            status_data = response.json()
            
            status = status_data["status"]
            progress = status_data.get("progress", 0)
            
            print(f"   Status: {status} - Progress: {progress}%")
            
            if status == "completed":
                print("✅ Generation completed!")
                weapons = status_data["weapons"]
                print(f"   Generated {len(weapons)} weapons:")
                
                for i, weapon in enumerate(weapons, 1):
                    print(f"     {i}. {weapon['weapon_name']} ({weapon['rarity']})")
                    print(f"        Damage: {weapon['damage']}, Speed: {weapon['speed']}")
                    print(f"        Description: {weapon['description']}")
                    print(f"        File: {weapon['file_location']}")
                
                break
                
            elif status == "failed":
                error = status_data.get("error", "Unknown error")
                print(f"❌ Generation failed: {error}")
                return
                
            elif status in ["queued", "processing"]:
                time.sleep(1)
                attempt += 1
                
        except Exception as e:
            print(f"❌ Error checking status: {e}")
            return
    
    if attempt >= max_attempts:
        print("❌ Generation timed out")
        return
    
    # 5. List all generated weapons
    print("\n5. Listing all generated weapons...")
    try:
        response = requests.get(f"{BASE_URL}/api/weapons/list")
        weapons_list = response.json()
        print(f"✅ Found {weapons_list['count']} weapon files:")
        
        for weapon_file in weapons_list["weapons"]:
            print(f"   - {weapon_file['filename']} ({weapon_file['size']} bytes)")
            
    except Exception as e:
        print(f"❌ Failed to list weapons: {e}")
    
    # 6. Test cleanup (optional)
    print(f"\n6. Testing cleanup...")
    try:
        response = requests.delete(f"{BASE_URL}/api/weapons/cleanup/{job_id}")
        cleanup_data = response.json()
        print(f"✅ Cleanup completed:")
        print(f"   - Deleted {len(cleanup_data['deleted_files'])} files")
        print(f"   - Job removed: {cleanup_data['job_removed']}")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
    
    print("\n🎉 Test completed!")

def test_custom_personalities():
    """Test with custom personality combinations"""
    
    print("\n🧪 Testing Custom Personalities")
    print("=" * 50)
    
    # Test different personality combinations
    test_cases = [
        {
            "name": "Aggressive Warriors",
            "arena_id": "test_aggressive",
            "player1": {
                "archetype": "warrior",
                "traits": ["aggressive", "brutal"],
                "power_level": 90
            },
            "player2": {
                "archetype": "warrior", 
                "traits": ["aggressive", "tactical"],
                "power_level": 85
            }
        },
        {
            "name": "Mystical vs Stealth",
            "arena_id": "test_mystical_stealth",
            "player1": {
                "archetype": "mage",
                "traits": ["mystical", "intelligent"],
                "power_level": 70
            },
            "player2": {
                "archetype": "rogue",
                "traits": ["stealthy", "quick"],
                "power_level": 75
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        try:
            # Start generation
            response = requests.post(f"{BASE_URL}/api/weapons/generate", json=test_case)
            job_data = response.json()
            job_id = job_data["job_id"]
            
            # Wait for completion
            while True:
                response = requests.get(f"{BASE_URL}/api/weapons/status/{job_id}")
                status_data = response.json()
                
                if status_data["status"] == "completed":
                    weapons = status_data["weapons"]
                    print(f"  ✅ Generated {len(weapons)} weapons")
                    
                    for weapon in weapons[:2]:  # Show first 2 weapons
                        print(f"     - {weapon['weapon_name']}: {weapon['description']}")
                    
                    break
                elif status_data["status"] == "failed":
                    print(f"  ❌ Failed: {status_data.get('error')}")
                    break
                
                time.sleep(1)
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    # Run basic test
    test_weapon_generation()
    
    # Uncomment to run additional tests
    # test_custom_personalities()