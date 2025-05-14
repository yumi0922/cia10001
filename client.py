import pygame
import socket
import pickle
import sys
from pygame.math import Vector2

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
    def __init__(self, host='localhost', port=5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((host, port))
            print("Connected to server!")
            self.player_number = pickle.loads(self.client.recv(4096))
            print(f"You are Player {self.player_number}")
        except Exception as e:
            print(f"Could not connect to server: {e}")
            sys.exit()

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

if __name__ == "__main__":
    if len(sys.argv) > 1:
        client = Client(host=sys.argv[1])
    else:
        client = Client()
    client.run() 