from turtle import Screen
import pygame
import socket
import pickle
import sys
from pygame.math import Vector2
import threading
from save_game import load_game

from single_player import MAX_PROJECTILES, PROJECTILE_COOLDOWN, Projectile

# Initialize Pygame
pygame.init()

# Constants
CELL_SIZE = 30
CELL_NUMBER = 25
SCREEN_SIZE = CELL_SIZE * CELL_NUMBER
CHAT_HEIGHT = 150  # Height of chat area

# Colors
BACKGROUND_COLOR = (40, 40, 40)
FOOD_COLOR = (207, 68, 68)
SCORE_COLOR = (255, 255, 255)
TEXT_COLOR = (255, 255, 255)
PROJECTILE_COLOR = (255, 255, 0)
CHAT_BG_COLOR = (30, 30, 30)
CHAT_INPUT_COLOR = (50, 50, 50)

# Predefined snake colors
SNAKE_COLORS = {
    "Pink": (255, 182, 193),
    "Sky Blue": (135, 206, 235),
    "Green": (50, 168, 82),
    "Purple": (147, 112, 219),
    "Orange": (255, 165, 0),
    "Yellow": (255, 255, 0),
    "Cyan": (0, 255, 255),
    "Red": (255, 0, 0)
}

class Client:
    def __init__(self, host='localhost', start_port=5556):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.single_player = '--single-player' in sys.argv
        
        # Try to read port from file
        try:
            with open('server_port.txt', 'r') as f:
                port = int(f.read().strip())
            print(f"Found server port: {port}")
        except (FileNotFoundError, ValueError) as e:
            print(f"Could not read server port: {e}")
            sys.exit(1)
            
        # Try to connect to server
        try:
            print(f"Connecting to {host}:{port}...")
            self.client.connect((host, port))
            print("Connected to server!")
        except Exception as e:
            print(f"Could not connect to server: {e}")
            sys.exit(1)

        try:
            if self.single_player:
                # Create single player room
                self.client.send(pickle.dumps({
                    "command": "create_room",
                    "room_name": "Single Player",
                    "single_player": True
                }))
                response = pickle.loads(self.client.recv(4096))
                if response.get("command") == "room_created":
                    print("Created single player room")
                    self.player_number = 1
                else:
                    print("Failed to create single player room")
                    sys.exit(1)
            else:
                self.player_number = pickle.loads(self.client.recv(4096))
            print(f"You are Player {self.player_number}")
        except Exception as e:
            print(f"Error during initialization: {e}")
            sys.exit(1)

        # Setup display
        self.screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE + CHAT_HEIGHT))
        pygame.display.set_caption(f'Snake Battle - Player {self.player_number}')
        self.clock = pygame.time.Clock()
        
        # Chat input setup
        self.chat_input = ""
        self.chat_active = False
        self.font = pygame.font.Font(None, 32)
        
        # Select color
        self.my_color = self.color_selection_screen()

    def color_selection_screen(self):
        """Let player choose their snake color."""
        font = pygame.font.Font(None, 48)
        button_size = 80
        gap = 20
        colors_per_row = 4
        
        while True:
            self.screen.fill(BACKGROUND_COLOR)
            
            # Draw title
            title = font.render(f"Select Your Color (Player {self.player_number})", True, TEXT_COLOR)
            title_rect = title.get_rect(center=(SCREEN_SIZE/2, 50))
            self.screen.blit(title, title_rect)
            
            # Draw color buttons
            color_rects = {}
            for i, (color_name, color_value) in enumerate(SNAKE_COLORS.items()):
                row = i // colors_per_row
                col = i % colors_per_row
                x = (SCREEN_SIZE - (button_size * colors_per_row + gap * (colors_per_row - 1))) // 2 + col * (button_size + gap)
                y = 150 + row * (button_size + gap)
                rect = pygame.Rect(x, y, button_size, button_size)
                pygame.draw.rect(self.screen, color_value, rect)
                
                font = pygame.font.Font(None, 24)
                text = font.render(color_name, True, TEXT_COLOR)
                text_rect = text.get_rect(center=rect.center)
                self.screen.blit(text, text_rect)
                color_rects[color_name] = rect
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for color_name, rect in color_rects.items():
                        if rect.collidepoint(mouse_pos):
                            return SNAKE_COLORS[color_name]
                            
            self.clock.tick(60)

    def draw_chat(self, game_state):
        """Draw chat area and messages."""
        # Draw chat background
        chat_rect = pygame.Rect(0, SCREEN_SIZE, SCREEN_SIZE, CHAT_HEIGHT)
        pygame.draw.rect(self.screen, CHAT_BG_COLOR, chat_rect)
        
        # Draw chat input box
        input_rect = pygame.Rect(10, SCREEN_SIZE + CHAT_HEIGHT - 40, SCREEN_SIZE - 20, 30)
        pygame.draw.rect(self.screen, CHAT_INPUT_COLOR, input_rect)
        
        # Draw chat input text
        input_text = self.font.render(self.chat_input, True, TEXT_COLOR)
        self.screen.blit(input_text, (input_rect.x + 5, input_rect.y + 5))
        
        # Draw chat messages
        y_offset = SCREEN_SIZE + 10
        for message in game_state.chat_messages:
            text = self.font.render(message, True, TEXT_COLOR)
            self.screen.blit(text, (10, y_offset))
            y_offset += 25

    def handle_chat_input(self, event):
        """Handle chat input events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.chat_active and self.chat_input:
                    # Send chat message
                    return {"chat": self.chat_input}
                self.chat_active = not self.chat_active
                self.chat_input = ""
            elif event.key == pygame.K_ESCAPE:
                self.chat_active = False
                self.chat_input = ""
            elif self.chat_active:
                if event.key == pygame.K_BACKSPACE:
                    self.chat_input = self.chat_input[:-1]
                else:
                    self.chat_input += event.unicode
        return None

    def draw_game_state(self, game_state):
        """Draw the current game state."""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw game elements
        food_rect = pygame.Rect(
            game_state.food_pos[0] * CELL_SIZE,
            game_state.food_pos[1] * CELL_SIZE,
            CELL_SIZE, CELL_SIZE
        )
        pygame.draw.rect(self.screen, FOOD_COLOR, food_rect, border_radius=10)
        
        # Draw snakes
        for pos in game_state.snake1_pos:
            rect = pygame.Rect(pos[0] * CELL_SIZE, pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.screen, self.my_color if self.player_number == 1 else SNAKE_COLORS["Sky Blue"],
                           rect, border_radius=8)
            
        for pos in game_state.snake2_pos:
            rect = pygame.Rect(pos[0] * CELL_SIZE, pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.screen, SNAKE_COLORS["Sky Blue"] if self.player_number == 1 else self.my_color,
                           rect, border_radius=8)
        
        # Draw projectiles
        for proj in game_state.projectiles:
            pygame.draw.circle(self.screen, PROJECTILE_COLOR,
                             (int(proj[0] * CELL_SIZE), int(proj[1] * CELL_SIZE)), 5)
        
        # Draw scores
        score1 = self.font.render(f'P1: {game_state.snake1_score}', True, 
                           self.my_color if self.player_number == 1 else SNAKE_COLORS["Sky Blue"])
        score2 = self.font.render(f'P2: {game_state.snake2_score}', True,
                           SNAKE_COLORS["Sky Blue"] if self.player_number == 1 else self.my_color)
        self.screen.blit(score1, (20, 20))
        self.screen.blit(score2, (SCREEN_SIZE-120, 20))
        
        # Draw projectile charges
        charges = game_state.snake1_projectiles if self.player_number == 1 else game_state.snake2_projectiles
        for i in range(charges):
            pygame.draw.circle(self.screen, PROJECTILE_COLOR,
                             (20 + i * 20, SCREEN_SIZE - 40), 5)
        
        # Draw stun indicators
        if (self.player_number == 1 and game_state.snake1_stunned > 0) or \
           (self.player_number == 2 and game_state.snake2_stunned > 0):
            text = self.font.render("STUNNED!", True, TEXT_COLOR)
            text_rect = text.get_rect(center=(SCREEN_SIZE/2, 50))
            self.screen.blit(text, text_rect)
        
        # Draw chat area
        self.draw_chat(game_state)
        
        # Draw game over
        if game_state.game_over:
            self.draw_game_over(game_state.winner)
            
        pygame.display.flip()

    def draw_game_over(self, winner):
        """Draw game over screen."""
        overlay = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 64)
        text = font.render(f"{winner} Wins!", True, TEXT_COLOR)
        text_rect = text.get_rect(center=(SCREEN_SIZE/2, SCREEN_SIZE/2))
        self.screen.blit(text, text_rect)
        
        pygame.display.flip()

    def run(self):
        """Main game loop."""
        running = True
        while running:
            data = {}
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                # Handle chat input
                chat_data = self.handle_chat_input(event)
                if chat_data:
                    data.update(chat_data)
            
            # Only handle game controls if chat is not active
            if not self.chat_active:
                keys = pygame.key.get_pressed()
                
                # Handle movement
                if self.player_number == 1:
                    if keys[pygame.K_UP]:
                        data["direction"] = (0, -1)
                    elif keys[pygame.K_DOWN]:
                        data["direction"] = (0, 1)
                    elif keys[pygame.K_LEFT]:
                        data["direction"] = (-1, 0)
                    elif keys[pygame.K_RIGHT]:
                        data["direction"] = (1, 0)
                    data["shoot"] = keys[pygame.K_SPACE]
                else:
                    if keys[pygame.K_w]:
                        data["direction"] = (0, -1)
                    elif keys[pygame.K_s]:
                        data["direction"] = (0, 1)
                    elif keys[pygame.K_a]:
                        data["direction"] = (-1, 0)
                    elif keys[pygame.K_d]:
                        data["direction"] = (1, 0)
                    data["shoot"] = keys[pygame.K_LSHIFT]
            
            try:
                # Send input to server
                self.client.send(pickle.dumps(data))
                
                # Get game state from server
                game_state = pickle.loads(self.client.recv(4096))
                
                # Draw game state
                self.draw_game_state(game_state)
                
            except (ConnectionResetError, BrokenPipeError):
                print("Lost connection to server")
                running = False
                
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:  # Save game
                    self.send_command("save_game")
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                elif self.game_state:  # Only handle game input if we have a game state
                    if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                        direction = {
                            pygame.K_UP: (0, -1),
                            pygame.K_DOWN: (0, 1),
                            pygame.K_LEFT: (-1, 0),
                            pygame.K_RIGHT: (1, 0)
                        }[event.key]
                        self.send_command("game_input", {"direction": direction})
                    elif event.key == pygame.K_SPACE:  # Shoot projectile
                        self.send_command("game_input", {"shoot": True})

    def handle_server_message(self, msg):
        """Handle message from server."""
        if msg["command"] == "start_game":
            print("Game starting!")
            self.game_state = None
        elif msg["command"] == "game_state":
            self.game_state = msg["state"]
        elif msg["command"] == "game_saved":
            print(f"Game saved to: {msg['save_path']}")
        elif msg["command"] == "error":
            print(f"Error: {msg['message']}")

class Snake:
    def __init__(self, pos, color):
        self.body = [Vector2(pos[0], pos[1])]
        self.direction = Vector2(1, 0)
        self.color = color
        self.alive = True
        self.score = 0
        self.stunned = 0
        self.projectiles = MAX_PROJECTILES
        self.projectile_cooldown = 0
        
        # Add initial body segments
        for i in range(2):
            self.body.append(Vector2(self.body[0].x - (i + 1), self.body[0].y))
    
    def draw(self):
        # Draw body segments
        for segment in self.body[1:]:
            rect = pygame.Rect(segment.x * CELL_SIZE, segment.y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(Screen, self.color, rect, border_radius=8)
        
        # Draw head
        head_rect = pygame.Rect(self.body[0].x * CELL_SIZE, self.body[0].y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(Screen, self.color, head_rect, border_radius=8)
        
        # Calculate eye positions based on direction
        eye_color = (40, 40, 40)  # Dark eyes
        eye_size = 6
        eye_offset = 8
        
        # Base eye positions (when facing right)
        left_eye_pos = (
            self.body[0].x * CELL_SIZE + eye_offset,
            self.body[0].y * CELL_SIZE + eye_offset
        )
        right_eye_pos = (
            self.body[0].x * CELL_SIZE + eye_offset,
            self.body[0].y * CELL_SIZE + CELL_SIZE - eye_offset
        )
        
        # Adjust eye positions based on direction
        if self.direction == Vector2(1, 0):  # Right
            left_eye_pos = (self.body[0].x * CELL_SIZE + CELL_SIZE - eye_offset, 
                          self.body[0].y * CELL_SIZE + eye_offset)
            right_eye_pos = (self.body[0].x * CELL_SIZE + CELL_SIZE - eye_offset,
                           self.body[0].y * CELL_SIZE + CELL_SIZE - eye_offset)
        elif self.direction == Vector2(-1, 0):  # Left
            left_eye_pos = (self.body[0].x * CELL_SIZE + eye_offset,
                          self.body[0].y * CELL_SIZE + eye_offset)
            right_eye_pos = (self.body[0].x * CELL_SIZE + eye_offset,
                           self.body[0].y * CELL_SIZE + CELL_SIZE - eye_offset)
        elif self.direction == Vector2(0, -1):  # Up
            left_eye_pos = (self.body[0].x * CELL_SIZE + eye_offset,
                          self.body[0].y * CELL_SIZE + eye_offset)
            right_eye_pos = (self.body[0].x * CELL_SIZE + CELL_SIZE - eye_offset,
                           self.body[0].y * CELL_SIZE + eye_offset)
        else:  # Down
            left_eye_pos = (self.body[0].x * CELL_SIZE + eye_offset,
                          self.body[0].y * CELL_SIZE + CELL_SIZE - eye_offset)
            right_eye_pos = (self.body[0].x * CELL_SIZE + CELL_SIZE - eye_offset,
                           self.body[0].y * CELL_SIZE + CELL_SIZE - eye_offset)
        
        # Draw eyes
        pygame.draw.circle(Screen, eye_color, left_eye_pos, eye_size)
        pygame.draw.circle(Screen, eye_color, right_eye_pos, eye_size)
        
        # Draw tongue
        tongue_color = (255, 100, 100)  # Pink tongue
        tongue_start = (
            self.body[0].x * CELL_SIZE + CELL_SIZE/2,
            self.body[0].y * CELL_SIZE + CELL_SIZE/2
        )
        
        # Calculate tongue end position based on direction
        tongue_length = 10
        tongue_fork = 4
        if self.direction == Vector2(1, 0):  # Right
            tongue_end = (tongue_start[0] + tongue_length, tongue_start[1])
            fork1 = (tongue_end[0], tongue_end[1] - tongue_fork)
            fork2 = (tongue_end[0], tongue_end[1] + tongue_fork)
        elif self.direction == Vector2(-1, 0):  # Left
            tongue_end = (tongue_start[0] - tongue_length, tongue_start[1])
            fork1 = (tongue_end[0], tongue_end[1] - tongue_fork)
            fork2 = (tongue_end[0], tongue_end[1] + tongue_fork)
        elif self.direction == Vector2(0, -1):  # Up
            tongue_end = (tongue_start[0], tongue_start[1] - tongue_length)
            fork1 = (tongue_end[0] - tongue_fork, tongue_end[1])
            fork2 = (tongue_end[0] + tongue_fork, tongue_end[1])
        else:  # Down
            tongue_end = (tongue_start[0], tongue_start[1] + tongue_length)
            fork1 = (tongue_end[0] - tongue_fork, tongue_end[1])
            fork2 = (tongue_end[0] + tongue_fork, tongue_end[1])
        
        # Draw forked tongue
        pygame.draw.line(Screen, tongue_color, tongue_start, tongue_end, 2)
        pygame.draw.line(Screen, tongue_color, tongue_end, fork1, 2)
        pygame.draw.line(Screen, tongue_color, tongue_end, fork2, 2)
    
    def move(self):
        if self.alive and self.stunned <= 0:
            body_copy = self.body[:-1]
            new_head = Vector2(self.body[0].x + self.direction.x, self.body[0].y + self.direction.y)
            body_copy.insert(0, new_head)
            self.body = body_copy[:]
    
    def grow(self):
        self.body.append(self.body[-1])
        self.score += 1
    
    def shoot_projectile(self):
        if self.projectiles > 0 and self.projectile_cooldown <= 0:
            self.projectiles -= 1
            self.projectile_cooldown = PROJECTILE_COOLDOWN
            return Projectile(self.body[0], self.direction, self)
        return None

if __name__ == "__main__":
    single_player = '--single-player' in sys.argv
    if len(sys.argv) > 1 and sys.argv[1] != '--single-player':
        client = Client(host=sys.argv[1])
    else:
        client = Client()
    
    # Create room for single player mode
    if single_player:
        client.client.send(pickle.dumps({
            "command": "create_room",
            "room_name": "Single Player",
            "single_player": True
        }))
        response = pickle.loads(client.client.recv(4096))
        if response.get("command") == "room_created":
            print("Created single player room")
        else:
            print("Failed to create single player room")
            sys.exit(1)
    
    client.run() 