# Multiplayer Snake Game

A modern take on the classic Snake game with multiplayer support, combat mechanics, and a lobby system.

## Features

### Game Modes
- Single Player: Classic snake gameplay with modern features
- Multiplayer: Two-player competitive mode
- Network Play: Play over network with lobby system

### Gameplay Features
- Classic snake movement and growth mechanics
- Combat system with projectiles (5 charges per player)
- Stun mechanics when hit by projectiles
- Auto-recharging projectile system
- In-game chat system
- Color customization for snakes
- Score tracking
- Visual effects and sound system

### Technical Features
- Client-server architecture
- Lobby system with room management
- Network synchronization
- Graceful disconnection handling
- Modern UI with neon effects
- Sound effects and background music

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd snake-game
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

1. Start the game using the launcher:
```bash
python launch_game.py
```

2. Select game mode:
   - Single Player: Play alone
   - Multiplayer: Play with two players locally
   - Quit: Exit the game

3. Choose your snake color in the color selection screen

## Controls

### Player 1 (or Single Player)
- ↑ (Up Arrow): Move up
- ↓ (Down Arrow): Move down
- ← (Left Arrow): Move left
- → (Right Arrow): Move right
- SPACE: Shoot projectile

### Player 2 (Multiplayer only)
- W: Move up
- S: Move down
- A: Move left
- D: Move right
- LEFT SHIFT: Shoot projectile

### General Controls
- ENTER: Open/send chat
- ESC: Cancel chat
- Close window to quit

## Project Structure

- `launch_game.py`: Main game launcher with menu system
- `server.py`: Game server implementation
- `client.py`: Game client and rendering
- `requirements.txt`: Python dependencies
- `assets/`: Sound files and resources

## Dependencies

- Python 3.6+
- pygame >= 2.5.0
- numpy >= 1.24.0
- scipy >= 1.11.0

## Game Rules

1. Basic Rules:
   - Eat food to grow longer
   - Don't hit walls
   - Don't collide with yourself
   - In multiplayer, don't hit other players

2. Combat System:
   - Each player has 5 projectile charges
   - Hitting an opponent with a projectile stuns them
   - Projectiles recharge over time
   - Stunned players can't move temporarily

3. Scoring:
   - Points for collecting food
   - Game ends when a player crashes
   - Winner announced on game over

## Development

The game is built with Python and Pygame, featuring:
- Modern client-server architecture
- Real-time networking
- State synchronization
- Event-driven gameplay
- Sound system with procedural audio
- Particle effects and animations

## License

This project is licensed under the MIT License - see the LICENSE file for details.