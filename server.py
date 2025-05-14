import socket
import pickle
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import random
from collections import deque

@dataclass
class GameState:
    snake1_pos: List[Tuple[float, float]]
    snake2_pos: List[Tuple[float, float]]
    snake1_direction: Tuple[float, float]
    snake2_direction: Tuple[float, float]
    food_pos: Tuple[float, float]
    snake1_score: int
    snake2_score: int
    projectiles: List[Tuple[float, float, float, float]]
    snake1_stunned: int
    snake2_stunned: int
    snake1_projectiles: int
    snake2_projectiles: int
    game_over: bool
    winner: str
    chat_messages: deque

@dataclass
class Room:
    id: str
    name: str
    host: socket.socket
    guest: Optional[socket.socket]
    game_state: GameState
    host_ready: bool
    guest_ready: bool
    in_game: bool
    single_player: bool

class LobbyServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(10)  # Allow more connections for lobby
        print(f"Server started on {host}:{port}")
        
        self.rooms: Dict[str, Room] = {}
        self.client_to_room: Dict[socket.socket, str] = {}
        self.lock = threading.Lock()

    def create_game_state(self) -> GameState:
        """Create a fresh game state."""
        return GameState(
            [(5, 5), (4, 5), (3, 5)],  # snake1_pos
            [(20, 20), (19, 20), (18, 20)],  # snake2_pos
            (1, 0),  # snake1_direction
            (-1, 0),  # snake2_direction
            (10, 10),  # food_pos
            0,  # snake1_score
            0,  # snake2_score
            [],  # projectiles
            0,  # snake1_stunned
            0,  # snake2_stunned
            5,  # snake1_projectiles
            5,  # snake2_projectiles
            False,  # game_over
            "",  # winner
            deque(maxlen=5)  # chat_messages
        )

    def create_room(self, host: socket.socket, room_name: str, single_player: bool = False) -> str:
        """Create a new game room."""
        room_id = str(random.randint(1000, 9999))
        while room_id in self.rooms:
            room_id = str(random.randint(1000, 9999))
            
        room = Room(
            id=room_id,
            name=room_name,
            host=host,
            guest=None,
            game_state=self.create_game_state(),
            host_ready=False,
            guest_ready=False,
            in_game=False,
            single_player=single_player
        )
        
        # For single player mode, automatically set as ready
        if single_player:
            room.host_ready = True
            room.guest_ready = True
        
        self.rooms[room_id] = room
        self.client_to_room[host] = room_id
        return room_id

    def get_room_list(self) -> List[Dict]:
        """Get list of available rooms."""
        return [
            {
                "id": room.id,
                "name": room.name,
                "players": 2 if room.guest else 1,
                "in_game": room.in_game,
                "single_player": room.single_player
            }
            for room in self.rooms.values()
            if not room.in_game and not room.guest and not room.single_player  # Only show multiplayer rooms that can be joined
        ]

    def join_room(self, client: socket.socket, room_id: str) -> bool:
        """Try to join a room."""
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if not room.guest and not room.in_game:
                room.guest = client
                self.client_to_room[client] = room_id
                return True
        return False

    def handle_client(self, client: socket.socket):
        """Handle client connection in lobby and game."""
        try:
            while True:
                try:
                    data = pickle.loads(client.recv(4096))
                    cmd = data.get("command")
                    
                    with self.lock:
                        if cmd == "list_rooms":
                            # Send room list
                            response = {"command": "room_list", "rooms": self.get_room_list()}
                            client.send(pickle.dumps(response))
                            
                        elif cmd == "create_room":
                            # Create new room
                            room_id = self.create_room(client, data["room_name"], data["single_player"])
                            response = {"command": "room_created", "room_id": room_id}
                            client.send(pickle.dumps(response))
                            
                        elif cmd == "join_room":
                            # Try to join room
                            success = self.join_room(client, data["room_id"])
                            if success:
                                room = self.rooms[data["room_id"]]
                                # Notify host
                                host_msg = {"command": "player_joined"}
                                room.host.send(pickle.dumps(host_msg))
                                # Notify guest
                                guest_msg = {"command": "joined_room", "room_id": room.id}
                                client.send(pickle.dumps(guest_msg))
                            else:
                                error_msg = {"command": "error", "message": "Could not join room"}
                                client.send(pickle.dumps(error_msg))
                                
                        elif cmd == "ready":
                            # Handle player ready
                            room_id = self.client_to_room.get(client)
                            if room_id:
                                room = self.rooms[room_id]
                                if client == room.host:
                                    room.host_ready = True
                                elif client == room.guest:
                                    room.guest_ready = True
                                    
                                # If both ready, start game
                                if room.host_ready and room.guest_ready:
                                    room.in_game = True
                                    start_msg = {"command": "start_game", "player_number": 1}
                                    room.host.send(pickle.dumps(start_msg))
                                    start_msg["player_number"] = 2
                                    room.guest.send(pickle.dumps(start_msg))
                                    
                        elif cmd == "game_input":
                            # Handle game input
                            room_id = self.client_to_room.get(client)
                            if room_id:
                                room = self.rooms[room_id]
                                if room.in_game:
                                    self.handle_game_input(room, client, data)
                                    
                except (EOFError, pickle.UnpicklingError):
                    pass
                    
        except (ConnectionResetError, BrokenPipeError):
            self.handle_disconnect(client)

    def handle_game_input(self, room: Room, client: socket.socket, data: Dict):
        """Handle game input and update game state."""
        is_host = client == room.host
        game_state = room.game_state
        
        # Handle chat messages
        if "chat" in data:
            message = f"Player {1 if is_host else 2}: {data['chat']}"
            game_state.chat_messages.append(message)
            
        # Handle game controls
        if is_host:
            if "direction" in data:
                game_state.snake1_direction = data["direction"]
            if "shoot" in data and data["shoot"] and game_state.snake1_projectiles > 0:
                game_state.projectiles.append(
                    (game_state.snake1_pos[0][0],
                     game_state.snake1_pos[0][1],
                     game_state.snake1_direction[0],
                     game_state.snake1_direction[1])
                )
                game_state.snake1_projectiles -= 1
        else:
            if "direction" in data:
                game_state.snake2_direction = data["direction"]
            if "shoot" in data and data["shoot"] and game_state.snake2_projectiles > 0:
                game_state.projectiles.append(
                    (game_state.snake2_pos[0][0],
                     game_state.snake2_pos[0][1],
                     game_state.snake2_direction[0],
                     game_state.snake2_direction[1])
                )
                game_state.snake2_projectiles -= 1
                
        # Send updated game state to both players
        state_msg = {"command": "game_state", "state": game_state}
        room.host.send(pickle.dumps(state_msg))
        if room.guest:
            room.guest.send(pickle.dumps(state_msg))

    def handle_disconnect(self, client: socket.socket):
        """Handle client disconnection."""
        with self.lock:
            room_id = self.client_to_room.get(client)
            if room_id:
                room = self.rooms[room_id]
                if client == room.host:
                    # Notify guest and close room
                    if room.guest:
                        disconnect_msg = {"command": "host_disconnected"}
                        try:
                            room.guest.send(pickle.dumps(disconnect_msg))
                        except:
                            pass
                    del self.rooms[room_id]
                elif client == room.guest:
                    # Notify host
                    room.guest = None
                    room.guest_ready = False
                    room.in_game = False
                    disconnect_msg = {"command": "guest_disconnected"}
                    try:
                        room.host.send(pickle.dumps(disconnect_msg))
                    except:
                        pass
                del self.client_to_room[client]

    def update_games(self):
        """Update all active games."""
        while True:
            with self.lock:
                for room in self.rooms.values():
                    if room.in_game and not room.game_state.game_over:
                        self.update_game_state(room)
            time.sleep(0.15)

    def update_game_state(self, room: Room):
        """Update a single game's state."""
        game_state = room.game_state
        
        # Update snake positions
        if game_state.snake1_stunned <= 0:
            new_head = (
                game_state.snake1_pos[0][0] + game_state.snake1_direction[0],
                game_state.snake1_pos[0][1] + game_state.snake1_direction[1]
            )
            game_state.snake1_pos.insert(0, new_head)
            game_state.snake1_pos.pop()
        else:
            game_state.snake1_stunned -= 1
            
        # Only update snake2 in multiplayer mode
        if not room.single_player:
            if game_state.snake2_stunned <= 0:
                new_head = (
                    game_state.snake2_pos[0][0] + game_state.snake2_direction[0],
                    game_state.snake2_pos[0][1] + game_state.snake2_direction[1]
                )
                game_state.snake2_pos.insert(0, new_head)
                game_state.snake2_pos.pop()
            else:
                game_state.snake2_stunned -= 1
        
        # Update projectiles
        new_projectiles = []
        for p in game_state.projectiles:
            new_x = p[0] + p[2]
            new_y = p[1] + p[3]
            
            # Check if projectile hits snake1
            if any(abs(new_x - x) < 1 and abs(new_y - y) < 1 
                  for x, y in game_state.snake1_pos):
                game_state.snake1_stunned = 30
                continue
                
            # Check if projectile hits snake2 (multiplayer only)
            if not room.single_player:
                if any(abs(new_x - x) < 1 and abs(new_y - y) < 1 
                      for x, y in game_state.snake2_pos):
                    game_state.snake2_stunned = 30
                    continue
                
            # Keep projectile if it's still in bounds
            if 0 <= new_x < 25 and 0 <= new_y < 25:
                new_projectiles.append((new_x, new_y, p[2], p[3]))
                
        game_state.projectiles = new_projectiles
        
        # Recharge projectiles
        if game_state.snake1_projectiles < 5:
            game_state.snake1_projectiles += 1
        if not room.single_player and game_state.snake2_projectiles < 5:
            game_state.snake2_projectiles += 1
        
        # Check collisions with food
        if (abs(game_state.snake1_pos[0][0] - game_state.food_pos[0]) < 1 and
            abs(game_state.snake1_pos[0][1] - game_state.food_pos[1]) < 1):
            game_state.snake1_score += 1
            game_state.food_pos = (random.randint(0, 24), random.randint(0, 24))
            game_state.snake1_pos.append(game_state.snake1_pos[-1])
            
        if not room.single_player:
            if (abs(game_state.snake2_pos[0][0] - game_state.food_pos[0]) < 1 and
                abs(game_state.snake2_pos[0][1] - game_state.food_pos[1]) < 1):
                game_state.snake2_score += 1
                game_state.food_pos = (random.randint(0, 24), random.randint(0, 24))
                game_state.snake2_pos.append(game_state.snake2_pos[-1])
        
        # Check for collisions with walls or self
        if (not 0 <= game_state.snake1_pos[0][0] < 25 or
            not 0 <= game_state.snake1_pos[0][1] < 25 or
            game_state.snake1_pos[0] in game_state.snake1_pos[1:]):
            game_state.game_over = True
            game_state.winner = "Game Over!" if room.single_player else "Player 2"
            
        if not room.single_player:
            if (not 0 <= game_state.snake2_pos[0][0] < 25 or
                not 0 <= game_state.snake2_pos[0][1] < 25 or
                game_state.snake2_pos[0] in game_state.snake2_pos[1:]):
                game_state.game_over = True
                game_state.winner = "Player 1"

    def start(self):
        """Start the server."""
        print("Server is running...")
        # Start game update thread
        threading.Thread(target=self.update_games, daemon=True).start()
        
        while True:
            client, addr = self.server.accept()
            print(f"New connection from {addr}")
            threading.Thread(target=self.handle_client, args=(client,)).start()

if __name__ == "__main__":
    server = LobbyServer()
    server.start() 