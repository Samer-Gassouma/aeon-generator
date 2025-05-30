#!/usr/bin/env python3
"""
AEON Weapon AI System - Main Flask Server
Serves both API endpoints and web interface for weapon generation
"""

import os
import json
import time
import glob
import zipfile
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
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
    'STATIC_DIR': './static',
    'TEMPLATES_DIR': './templates',
    'MAX_WEAPONS_PER_REQUEST': 4,
    'MODEL_CACHE_SIZE': 2,
    'WEB_INTERFACE_ENABLED': True
}

# Global model instances
text_generator = None
model_generator = None
generation_stats = {
    'total_generated': 0,
    'successful_generations': 0,
    'average_time': 0,
    'last_generation': None,
    'personality_counts': {},
    'arena_theme_counts': {}
}

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

def update_stats(weapons, generation_time, success=True):
    """Update generation statistics"""
    global generation_stats
    
    generation_stats['total_generated'] += len(weapons) if weapons else 0
    if success:
        generation_stats['successful_generations'] += 1
    
    # Update average time
    if generation_stats['successful_generations'] > 0:
        old_avg = generation_stats['average_time']
        count = generation_stats['successful_generations']
        generation_stats['average_time'] = (old_avg * (count - 1) + generation_time) / count
    
    generation_stats['last_generation'] = datetime.now().isoformat()
    
    # Update personality counts
    if weapons:
        for weapon in weapons:
            personality = weapon.get('personality', 'unknown')
            generation_stats['personality_counts'][personality] = generation_stats['personality_counts'].get(personality, 0) + 1

# ===============================
# WEB INTERFACE ROUTES
# ===============================

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('index.html', config=CONFIG, stats=generation_stats)

@app.route('/gallery')
def gallery():
    """Model gallery page"""
    # Get all generated weapons
    weapons_data = get_all_weapons_data()
    return render_template('gallery.html', weapons=weapons_data, stats=generation_stats)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

# ===============================
# API ROUTES - WEAPON GENERATION
# ===============================

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
        'web_interface': CONFIG['WEB_INTERFACE_ENABLED'],
        'timestamp': time.time(),
        'stats': generation_stats
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
        
        start_time = time.time()
        
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
            weapon['webPath'] = f"/download/weapon/{filename}"
            weapon['generatedAt'] = datetime.now().isoformat()
        
        generation_time = time.time() - start_time
        
        # Update statistics
        generation_stats['arena_theme_counts'][arena_theme] = generation_stats['arena_theme_counts'].get(arena_theme, 0) + 1
        update_stats(weapon_scenarios, generation_time, True)
        
        logger.success(f"Generated {len(weapon_scenarios)} weapon scenarios in {generation_time:.2f}s")
        
        return jsonify({
            'weapons': weapon_scenarios,
            'generation_time': generation_time,
            'arena_theme': arena_theme,
            'timestamp': timestamp
        })
        
    except Exception as e:
        logger.error(f"Error generating weapons: {e}")
        update_stats(None, 0, False)
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
                'web_path': f"/download/weapon/{os.path.basename(output_path)}",
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
        
        start_time = time.time()
        
        for i, weapon in enumerate(weapons):
            logger.info(f"Processing weapon {i+1}/{len(weapons)}: {weapon.get('weaponName', 'Unknown')}")
            
            model_start_time = time.time()
            
            success = model_generator.generate_model(
                description=weapon['description'],
                output_path=weapon['fileLocation']
            )
            
            model_generation_time = time.time() - model_start_time
            
            results.append({
                'weapon_name': weapon.get('weaponName', f'Weapon_{i}'),
                'status': 'completed' if success else 'failed',
                'model_path': weapon['fileLocation'] if success else None,
                'web_path': weapon.get('webPath') if success else None,
                'generation_time': model_generation_time
            })
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r['status'] == 'completed')
        
        logger.success(f"Batch generation completed in {total_time:.2f}s: {successful}/{len(weapons)} successful")
        
        return jsonify({
            'results': results,
            'summary': {
                'total': len(weapons),
                'successful': successful,
                'failed': len(weapons) - successful,
                'total_time': total_time
            }
        })
        
    except Exception as e:
        logger.error(f"Error in batch model creation: {e}")
        return jsonify({'error': str(e)}), 500

# ===============================
# API ROUTES - WEAPON MANAGEMENT
# ===============================

@app.route('/api/weapons/list', methods=['GET'])
def list_weapons():
    """List all generated weapons"""
    try:
        weapons_data = get_all_weapons_data()
        return jsonify({
            'weapons': weapons_data,
            'count': len(weapons_data),
            'stats': generation_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weapons/stats', methods=['GET'])
def get_stats():
    """Get generation statistics"""
    try:
        # Add file system stats
        weapon_files = glob.glob(os.path.join(CONFIG['WEAPON_OUTPUT_DIR'], '*.obj'))
        file_stats = {
            'total_files': len(weapon_files),
            'total_size': sum(os.path.getsize(f) for f in weapon_files),
            'oldest_file': min(weapon_files, key=os.path.getctime) if weapon_files else None,
            'newest_file': max(weapon_files, key=os.path.getctime) if weapon_files else None
        }
        
        return jsonify({
            'generation_stats': generation_stats,
            'file_stats': file_stats,
            'system_stats': {
                'gpu_available': torch.cuda.is_available(),
                'models_loaded': text_generator is not None and model_generator is not None
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weapons/<weapon_id>', methods=['DELETE'])
def delete_weapon(weapon_id):
    """Delete a specific weapon"""
    try:
        # Find weapon file
        weapon_file = os.path.join(CONFIG['WEAPON_OUTPUT_DIR'], f"{weapon_id}.obj")
        
        if os.path.exists(weapon_file):
            os.remove(weapon_file)
            logger.info(f"Deleted weapon: {weapon_id}")
            return jsonify({'success': True, 'message': f'Weapon {weapon_id} deleted'})
        else:
            return jsonify({'error': 'Weapon not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting weapon {weapon_id}: {e}")
        return jsonify({'error': str(e)}), 500

# ===============================
# DOWNLOAD ROUTES
# ===============================

@app.route('/download/weapon/<filename>')
def download_weapon(filename):
    """Download individual weapon file"""
    try:
        return send_from_directory(CONFIG['WEAPON_OUTPUT_DIR'], filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/download/batch')
def download_batch():
    """Download all weapons as ZIP file"""
    try:
        zip_filename = f"aeon_weapons_{int(time.time())}.zip"
        zip_path = os.path.join(CONFIG['WEAPON_OUTPUT_DIR'], zip_filename)
        
        # Create ZIP file with all weapons
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            weapon_files = glob.glob(os.path.join(CONFIG['WEAPON_OUTPUT_DIR'], '*.obj'))
            for file_path in weapon_files:
                filename = os.path.basename(file_path)
                zipf.write(file_path, filename)
        
        return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        
    except Exception as e:
        logger.error(f"Error creating batch download: {e}")
        return jsonify({'error': str(e)}), 500

# ===============================
# UTILITY FUNCTIONS
# ===============================

def get_all_weapons_data():
    """Get data for all generated weapons"""
    weapons_data = []
    weapon_files = glob.glob(os.path.join(CONFIG['WEAPON_OUTPUT_DIR'], '*.obj'))
    
    for file_path in weapon_files:
        filename = os.path.basename(file_path)
        file_stats = os.stat(file_path)
        
        weapons_data.append({
            'filename': filename,
            'file_path': file_path,
            'web_path': f"/download/weapon/{filename}",
            'size': file_stats.st_size,
            'created_at': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
        })
    
    # Sort by creation time (newest first)
    weapons_data.sort(key=lambda x: x['created_at'], reverse=True)
    return weapons_data

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

# ===============================
# ERROR HANDLERS
# ===============================

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    else:
        return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    else:
        return render_template('index.html', error="Internal server error"), 500

# ===============================
# MAIN ENTRY POINT
# ===============================

if __name__ == '__main__':
    logger.info("Starting AEON Weapon AI System...")
    logger.info(f"Configuration: {CONFIG}")
    
    # Initialize models before starting server
    if not initialize_models():
        logger.error("Failed to initialize models. Exiting...")
        exit(1)
    
    # Start Flask server
    logger.info(f"Starting server on port {CONFIG['API_PORT']}")
    logger.info(f"Web Interface: http://localhost:{CONFIG['API_PORT']}")
    logger.info(f"API Base URL: http://localhost:{CONFIG['API_PORT']}/api")
    
    app.run(
        host='0.0.0.0',
        port=CONFIG['API_PORT'],
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )