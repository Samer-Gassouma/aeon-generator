#!/usr/bin/env python3
"""
Weapon AI Service - Main API Server
Generates weapons based on player personalities using text-to-3D models
"""

import os
import json
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from loguru import logger
import torch

from models.text_generator import WeaponTextGenerator
from models.model_generator import WeaponModelGenerator

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
CONFIG = {
    'API_PORT': int(os.getenv('API_PORT', 8083)),
    'WEAPON_OUTPUT_DIR': os.getenv('WEAPON_OUTPUT_DIR', './generated_weapons'),
    'GAME_SERVER_URL': os.getenv('GAME_SERVER_URL', 'http://localhost:3030'),
    'MAX_WEAPONS_PER_REQUEST': 4,
    'MODEL_CACHE_SIZE': 2
}

# Global model instances
text_generator = None
model_generator = None

def initialize_models():
    """Initialize AI models on startup"""
    global text_generator, model_generator
    
    logger.info("Initializing AI models...")
    
    try:
        # Initialize text generator for weapon scenarios
        text_generator = WeaponTextGenerator()
        logger.info("✓ Text generator loaded")
        
        # Initialize 3D model generator (Hunyuan3D-2)
        model_generator = WeaponModelGenerator()
        logger.info("✓ 3D model generator loaded")
        
        # Create output directory
        os.makedirs(CONFIG['WEAPON_OUTPUT_DIR'], exist_ok=True)
        
        logger.success("All models initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize models: {e}")
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    gpu_available = torch.cuda.is_available()
    models_loaded = text_generator is not None and model_generator is not None
    
    return jsonify({
        'status': 'healthy' if models_loaded else 'initializing',
        'models_loaded': models_loaded,
        'gpu_available': gpu_available,
        'gpu_count': torch.cuda.device_count() if gpu_available else 0,
        'timestamp': time.time()
    })

@app.route('/api/weapons/generate', methods=['POST'])
def generate_weapons():
    """Generate 4 weapons based on player personalities"""
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['player1_personality', 'player2_personality']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        player1_personality = data['player1_personality']
        player2_personality = data['player2_personality']
        arena_theme = data.get('arena_theme', 'medieval')
        
        logger.info(f"Generating weapons for personalities: {player1_personality} vs {player2_personality}")
        
        # Generate weapon scenarios using text model
        weapon_scenarios = text_generator.generate_weapon_scenarios(
            player1_personality=player1_personality,
            player2_personality=player2_personality,
            arena_theme=arena_theme,
            num_weapons=CONFIG['MAX_WEAPONS_PER_REQUEST']
        )
        
        # Generate file paths for 3D models
        timestamp = int(time.time())
        for i, weapon in enumerate(weapon_scenarios):
            filename = f"weapon_{timestamp}_{i}.obj"
            weapon['fileLocation'] = os.path.join(CONFIG['WEAPON_OUTPUT_DIR'], filename)
        
        logger.success(f"Generated {len(weapon_scenarios)} weapon scenarios")
        
        return jsonify({
            'weapons': weapon_scenarios,
            'generation_time': time.time(),
            'arena_theme': arena_theme
        })
        
    except Exception as e:
        logger.error(f"Error generating weapons: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/weapons/create-model', methods=['POST'])
def create_3d_model():
    """Generate 3D model from weapon description"""
    try:
        data = request.get_json()
        
        # Validate input
        if 'description' not in data:
            return jsonify({'error': 'Missing required field: description'}), 400
        
        description = data['description']
        output_path = data.get('output_path')
        
        # Generate default path if not provided
        if not output_path:
            timestamp = int(time.time())
            filename = f"weapon_{timestamp}.obj"
            output_path = os.path.join(CONFIG['WEAPON_OUTPUT_DIR'], filename)
        
        logger.info(f"Generating 3D model for: {description[:50]}...")
        
        start_time = time.time()
        
        # Generate 3D model using Hunyuan3D-2
        success = model_generator.generate_model(
            description=description,
            output_path=output_path
        )
        
        generation_time = time.time() - start_time
        
        if success:
            logger.success(f"3D model generated in {generation_time:.2f}s: {output_path}")
            return jsonify({
                'status': 'completed',
                'model_path': output_path,
                'generation_time': generation_time
            })
        else:
            logger.error("Failed to generate 3D model")
            return jsonify({'error': 'Model generation failed'}), 500
            
    except Exception as e:
        logger.error(f"Error creating 3D model: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/weapons/batch-create', methods=['POST'])
def batch_create_models():
    """Generate 3D models for multiple weapons"""
    try:
        data = request.get_json()
        
        if 'weapons' not in data:
            return jsonify({'error': 'Missing required field: weapons'}), 400
        
        weapons = data['weapons']
        results = []
        
        logger.info(f"Batch generating {len(weapons)} 3D models...")
        
        for i, weapon in enumerate(weapons):
            logger.info(f"Processing weapon {i+1}/{len(weapons)}: {weapon.get('weaponName', 'Unknown')}")
            
            start_time = time.time()
            
            success = model_generator.generate_model(
                description=weapon['description'],
                output_path=weapon['fileLocation']
            )
            
            generation_time = time.time() - start_time
            
            results.append({
                'weapon_name': weapon.get('weaponName', f'Weapon_{i}'),
                'status': 'completed' if success else 'failed',
                'model_path': weapon['fileLocation'] if success else None,
                'generation_time': generation_time
            })
        
        successful = sum(1 for r in results if r['status'] == 'completed')
        logger.success(f"Batch generation completed: {successful}/{len(weapons)} successful")
        
        return jsonify({
            'results': results,
            'summary': {
                'total': len(weapons),
                'successful': successful,
                'failed': len(weapons) - successful
            }
        })
        
    except Exception as e:
        logger.error(f"Error in batch model creation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/reload', methods=['POST'])
def reload_models():
    """Reload AI models (for debugging)"""
    try:
        logger.info("Reloading AI models...")
        success = initialize_models()
        
        if success:
            return jsonify({'status': 'success', 'message': 'Models reloaded successfully'})
        else:
            return jsonify({'error': 'Failed to reload models'}), 500
            
    except Exception as e:
        logger.error(f"Error reloading models: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Weapon AI Service...")
    logger.info(f"Configuration: {CONFIG}")
    
    # Initialize models before starting server
    if not initialize_models():
        logger.error("Failed to initialize models. Exiting...")
        exit(1)
    
    # Start Flask server
    logger.info(f"Starting server on port {CONFIG['API_PORT']}")
    app.run(
        host='0.0.0.0',
        port=CONFIG['API_PORT'],
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )