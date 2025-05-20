import json
import os
from datetime import datetime

SAVE_DIR = "saves"

def ensure_save_directory():
    """Ensure the saves directory exists."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

def save_single_player_game(snake, level, score):
    """Save single player game state."""
    ensure_save_directory()
    
    # Create save data
    save_data = {
        "mode": "single_player",
        "timestamp": datetime.now().isoformat(),
        "snake_data": {
            "body": [(pos.x, pos.y) for pos in snake.body],
            "direction": (snake.direction.x, snake.direction.y),
            "color": snake.color,
            "score": score,
            "level": level,
            "projectiles_available": snake.projectiles,
            "projectile_cooldown": snake.projectile_cooldown
        }
    }
    
    # Generate filename with timestamp
    filename = f"snake_save_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(SAVE_DIR, filename)
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(save_data, f, indent=2)
    
    return filepath

def save_multiplayer_game(game_state):
    """Save multiplayer game state."""
    ensure_save_directory()
    
    # Create save data
    save_data = {
        "mode": "multiplayer",
        "timestamp": datetime.now().isoformat(),
        "snake1_data": {
            "positions": game_state.snake1_pos,
            "direction": game_state.snake1_direction,
            "score": game_state.snake1_score,
            "stunned": game_state.snake1_stunned,
            "projectiles": game_state.snake1_projectiles
        },
        "snake2_data": {
            "positions": game_state.snake2_pos,
            "direction": game_state.snake2_direction,
            "score": game_state.snake2_score,
            "stunned": game_state.snake2_stunned,
            "projectiles": game_state.snake2_projectiles
        },
        "food_pos": game_state.food_pos,
        "projectiles": game_state.projectiles
    }
    
    # Generate filename with timestamp
    filename = f"snake_mp_save_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(SAVE_DIR, filename)
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(save_data, f, indent=2)
    
    return filepath

def load_game(filepath):
    """Load a saved game state."""
    with open(filepath, 'r') as f:
        save_data = json.load(f)
    
    return save_data

def list_saves():
    """List all available save files."""
    ensure_save_directory()
    saves = []
    
    for filename in os.listdir(SAVE_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(SAVE_DIR, filename)
            with open(filepath, 'r') as f:
                save_data = json.load(f)
            
            saves.append({
                'filename': filename,
                'filepath': filepath,
                'timestamp': save_data['timestamp'],
                'mode': save_data['mode']
            })
    
    return sorted(saves, key=lambda x: x['timestamp'], reverse=True) 