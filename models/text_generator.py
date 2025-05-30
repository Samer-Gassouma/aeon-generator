#!/usr/bin/env python3
"""
Weapon Text Generator
Generates weapon scenarios based on player personalities
"""

import os
import json
import random
from typing import List, Dict, Any
from loguru import logger
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class WeaponTextGenerator:
    """Generates weapon descriptions based on player personalities"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.personality_templates = {}
        self.weapon_stats_ranges = {
            'damage': (30, 100),
            'speed': (20, 90)
        }
        
        # Load personality templates
        self._load_personality_templates()
        
        # Initialize text generation model
        self._initialize_model()
    
    def _load_personality_templates(self):
        """Load personality-based weapon templates"""
        # Default templates if config file doesn't exist
        self.personality_templates = {
            'aggressive_warrior': {
                'weapon_types': ['axe', 'sword', 'mace', 'warhammer', 'claymore', 'battle axe'],
                'materials': ['steel', 'iron', 'darksteel', 'bloodsteel', 'volcanic rock', 'cursed metal'],
                'effects': ['flame', 'lightning', 'poison', 'ice', 'shadow', 'rage'],
                'descriptors': ['brutal', 'massive', 'serrated', 'jagged', 'intimidating', 'fearsome', 'vicious'],
                'damage_modifier': 1.2,
                'speed_modifier': 0.8
            },
            'strategic_mage': {
                'weapon_types': ['staff', 'wand', 'orb', 'tome', 'crystal', 'scepter'],
                'materials': ['crystal', 'enchanted wood', 'mithril', 'arcane stone', 'starlight essence', 'void crystal'],
                'effects': ['arcane', 'frost', 'shadow', 'holy', 'time', 'void', 'mind'],
                'descriptors': ['elegant', 'mystical', 'glowing', 'ancient', 'ethereal', 'wise', 'powerful'],
                'damage_modifier': 0.9,
                'speed_modifier': 1.3
            },
            'defensive_guardian': {
                'weapon_types': ['shield', 'lance', 'hammer', 'defensive blade', 'tower shield', 'holy mace'],
                'materials': ['blessed steel', 'adamantite', 'holy metal', 'reinforced iron', 'divine crystal', 'light stone'],
                'effects': ['protection', 'barrier', 'healing', 'reflection', 'blessing', 'fortification'],
                'descriptors': ['sturdy', 'protective', 'radiant', 'fortified', 'noble', 'steadfast', 'unwavering'],
                'damage_modifier': 0.8,
                'speed_modifier': 0.9
            },
            'agile_assassin': {
                'weapon_types': ['dagger', 'blade', 'throwing knife', 'poison dart', 'curved sword', 'shadow blade'],
                'materials': ['shadow steel', 'quicksilver', 'venom-coated metal', 'silent steel', 'void metal', 'phantom iron'],
                'effects': ['poison', 'shadow', 'stealth', 'bleeding', 'paralysis', 'invisibility'],
                'descriptors': ['swift', 'silent', 'deadly', 'precise', 'curved', 'razor-sharp', 'lethal'],
                'damage_modifier': 0.9,
                'speed_modifier': 1.4
            },
            'elemental_mage': {
                'weapon_types': ['elemental staff', 'focus crystal', 'elemental orb', 'nature wand', 'storm rod'],
                'materials': ['elemental crystal', 'living wood', 'storm glass', 'earth stone', 'fire gem', 'water pearl'],
                'effects': ['fire', 'water', 'earth', 'air', 'lightning', 'nature', 'storm'],
                'descriptors': ['elemental', 'flowing', 'crackling', 'growing', 'shifting', 'natural', 'primal'],
                'damage_modifier': 1.0,
                'speed_modifier': 1.1
            }
        }
        
        # Try to load from config file
        config_path = 'config/personalities.json'
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_templates = json.load(f)
                self.personality_templates.update(loaded_templates)
                logger.info("Loaded personality templates from config file")
            except Exception as e:
                logger.warning(f"Failed to load personality config: {e}")
    
    def _initialize_model(self):
        """Initialize the text generation model"""
        try:
            # Use DistilGPT-2 for fast generation (can be upgraded later)
            model_name = "distilgpt2"
            
            logger.info(f"Loading text generation model: {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Add padding token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.success("Text generation model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load text generation model: {e}")
            self.model = None
            self.tokenizer = None
    
    def generate_weapon_scenarios(self, player1_personality: str, player2_personality: str, 
                                arena_theme: str = "medieval", num_weapons: int = 4) -> List[Dict[str, Any]]:
        """Generate weapon scenarios based on player personalities"""
        
        weapons = []
        
        # Generate 2 weapons for each player
        for player_num in [1, 2]:
            personality = player1_personality if player_num == 1 else player2_personality
            
            for i in range(2):
                weapon = self._generate_single_weapon(personality, arena_theme, player_num)
                weapons.append(weapon)
        
        return weapons
    
    def _generate_single_weapon(self, personality: str, arena_theme: str, player: int) -> Dict[str, Any]:
        """Generate a single weapon based on personality"""
        
        # Get personality template or use default
        template = self.personality_templates.get(personality, self.personality_templates['aggressive_warrior'])
        
        # Select random components
        weapon_type = random.choice(template['weapon_types'])
        material = random.choice(template['materials'])
        effect = random.choice(template['effects'])
        descriptor = random.choice(template['descriptors'])
        
        # Generate weapon name
        weapon_name = self._generate_weapon_name(weapon_type, material, effect, descriptor)
        
        # Generate description using template-based approach or AI model
        description = self._generate_description(weapon_name, weapon_type, material, effect, descriptor, arena_theme)
        
        # Calculate stats based on personality modifiers
        base_damage = random.randint(*self.weapon_stats_ranges['damage'])
        base_speed = random.randint(*self.weapon_stats_ranges['speed'])
        
        damage = int(base_damage * template['damage_modifier'])
        speed = int(base_speed * template['speed_modifier'])
        
        # Ensure stats are within reasonable bounds
        damage = max(20, min(100, damage))
        speed = max(10, min(100, speed))
        
        return {
            'weaponName': weapon_name,
            'description': description,
            'fileLocation': '',  # Will be set by main API
            'damage': damage,
            'speed': speed,
            'player': player,
            'personality': personality,
            'arena_theme': arena_theme,
            'weapon_type': weapon_type,
            'material': material,
            'effect': effect,
            'descriptor': descriptor
        }
    
    def _generate_weapon_name(self, weapon_type: str, material: str, effect: str, descriptor: str) -> str:
        """Generate a weapon name from components"""
        
        # Different naming patterns
        patterns = [
            f"{descriptor.title()} {weapon_type.title()} of {effect.title()}",
            f"{material.title()} {weapon_type.title()}",
            f"{effect.title()} {descriptor} {weapon_type}",
            f"The {descriptor.title()} {weapon_type.title()}",
            f"{material.title()} {effect.title()} {weapon_type.title()}",
            f"{effect.title()}-{descriptor} {weapon_type}",
            f"{descriptor.title()} {material} {weapon_type}"
        ]
        
        return random.choice(patterns)
    
    def _generate_description(self, weapon_name: str, weapon_type: str, material: str, 
                            effect: str, descriptor: str, arena_theme: str) -> str:
        """Generate weapon description using AI model or templates"""
        
        if self.model and self.tokenizer:
            return self._generate_ai_description(weapon_name, weapon_type, material, effect, descriptor, arena_theme)
        else:
            return self._generate_template_description(weapon_name, weapon_type, material, effect, descriptor, arena_theme)
    
    def _generate_ai_description(self, weapon_name: str, weapon_type: str, material: str, 
                               effect: str, descriptor: str, arena_theme: str) -> str:
        """Generate description using AI model"""
        try:
            # Create prompt for weapon description
            prompt = f"A {descriptor} {weapon_type} made of {material} with {effect} effects in a {arena_theme} arena. This legendary weapon"
            
            # Tokenize and generate
            inputs = self.tokenizer.encode(prompt, return_tensors='pt')
            if torch.cuda.is_available():
                inputs = inputs.cuda()
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 60,
                    num_return_sequences=1,
                    temperature=0.8,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.2
                )
            
            # Decode and clean up
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            description = generated_text[len(prompt):].strip()
            
            # Clean up the description
            if description:
                # Take first sentence or reasonable length
                sentences = description.split('.')
                if sentences[0] and len(sentences[0]) > 10:
                    description = sentences[0] + '.'
                else:
                    description = description[:120] + '...'
                
                # Ensure it starts properly
                if not description[0].isupper():
                    description = description[0].upper() + description[1:]
            
            return description if description and len(description) > 20 else self._generate_template_description(weapon_name, weapon_type, material, effect, descriptor, arena_theme)
            
        except Exception as e:
            logger.warning(f"AI description generation failed: {e}")
            return self._generate_template_description(weapon_name, weapon_type, material, effect, descriptor, arena_theme)
    
    def _generate_template_description(self, weapon_name: str, weapon_type: str, material: str, 
                                     effect: str, descriptor: str, arena_theme: str) -> str:
        """Generate description using templates as fallback"""
        
        # Arena-specific elements
        arena_elements = {
            'volcanic': ['molten lava', 'volcanic ash', 'burning rocks', 'fire', 'heat'],
            'ice': ['frozen crystals', 'icy winds', 'frost', 'glacial power', 'frozen essence'],
            'forest': ['ancient trees', 'natural magic', 'forest spirits', 'living wood', 'nature\'s power'],
            'medieval': ['ancient runes', 'battle-tested steel', 'warrior\'s honor', 'knightly valor', 'old magic'],
            'shadow': ['dark energy', 'shadow essence', 'void power', 'darkness', 'nightmare fuel'],
            'desert': ['sand storms', 'scorching heat', 'mirage magic', 'desert winds', 'ancient sands']
        }
        
        arena_element = random.choice(arena_elements.get(arena_theme, arena_elements['medieval']))
        
        templates = [
            f"A {descriptor} {weapon_type} forged from {material}, crackling with {effect} energy and infused with {arena_element}.",
            f"This {material} {weapon_type} radiates {effect} power, its {descriptor} form designed for devastating attacks in {arena_theme} combat.",
            f"Crafted from finest {material}, this {descriptor} {weapon_type} channels {effect} forces and draws strength from {arena_element}.",
            f"A legendary {weapon_type} of {material} construction, imbued with {effect} magic and empowered by {arena_element}.",
            f"The {descriptor} surface of this {material} {weapon_type} glows with {effect} energy, enhanced by the power of {arena_element}.",
            f"Forged in the heart of {arena_theme} lands, this {descriptor} {weapon_type} combines {material} with {effect} magic.",
            f"A {descriptor} {weapon_type} that pulses with {effect} energy, its {material} core resonating with {arena_element}.",
            f"This ancient {weapon_type} of {material} bears the mark of {effect} magic and the essence of {arena_element}."
        ]
        
        return random.choice(templates)
    
    def add_personality_template(self, name: str, template: Dict[str, Any]):
        """Add new personality template"""
        self.personality_templates[name] = template
        logger.info(f"Added personality template: {name}")
    
    def get_supported_personalities(self) -> List[str]:
        """Get list of supported personality types"""
        return list(self.personality_templates.keys())
    
    def get_personality_info(self, personality: str) -> Dict[str, Any]:
        """Get information about a specific personality"""
        if personality in self.personality_templates:
            return self.personality_templates[personality]
        return None
    
    def get_weapon_components(self, personality: str) -> Dict[str, List[str]]:
        """Get available weapon components for a personality"""
        template = self.personality_templates.get(personality, {})
        return {
            'weapon_types': template.get('weapon_types', []),
            'materials': template.get('materials', []),
            'effects': template.get('effects', []),
            'descriptors': template.get('descriptors', [])
        }