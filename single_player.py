import pygame
import sys
import random
from pygame.math import Vector2
import math
from save_game import save_single_player_game, load_game

# Initialize Pygame
pygame.init()

# Constants
CELL_SIZE = 30
CELL_NUMBER = 25
SCREEN_SIZE = CELL_SIZE * CELL_NUMBER

# Colors - Synthwave palette
BACKGROUND_COLOR = (25, 25, 35)  # Darker background
GRID_COLOR = (45, 45, 55)  # Subtle grid lines
FOOD_COLOR = (255, 223, 0)  # Bright neon yellow/gold
SCORE_COLOR = (0, 255, 255)  # Cyan
TEXT_COLOR = (255, 255, 255)  # White
PROJECTILE_COLOR = (255, 213, 0)  # Neon yellow
GRID_SPACING = 30  # Same as CELL_SIZE

# Predefined snake colors - Neon palette
SNAKE_COLORS = {
    "Neon Pink": (255, 66, 161),
    "Cyber Blue": (0, 255, 255),
    "Electric Green": (57, 255, 20),
    "Neon Purple": (191, 62, 255),
    "Hot Orange": (255, 153, 0),
    "Digital Cyan": (0, 231, 255),
    "Laser Red": (255, 0, 77)
}

# Game settings
PROJECTILE_SPEED = 15
PROJECTILE_COOLDOWN = 60  # Frames between shots
STUN_DURATION = 30  # Frames to stay stunned
MAX_PROJECTILES = 5  # Maximum projectiles

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
            pygame.draw.rect(screen, self.color, rect, border_radius=8)
        
        # Draw head
        head_rect = pygame.Rect(self.body[0].x * CELL_SIZE, self.body[0].y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, self.color, head_rect, border_radius=8)
        
        # Calculate eye positions based on direction
        eye_color = (40, 40, 40)  # Dark eyes
        eye_size = 8  # Bigger eyes
        eye_offset = 8
        cheek_color = (255, 182, 193)  # Pink cheeks
        cheek_size = 6
        
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
            cheek_pos = (self.body[0].x * CELL_SIZE + CELL_SIZE - 4, 
                        self.body[0].y * CELL_SIZE + CELL_SIZE//2)
        elif self.direction == Vector2(-1, 0):  # Left
            left_eye_pos = (self.body[0].x * CELL_SIZE + eye_offset,
                          self.body[0].y * CELL_SIZE + eye_offset)
            right_eye_pos = (self.body[0].x * CELL_SIZE + eye_offset,
                           self.body[0].y * CELL_SIZE + CELL_SIZE - eye_offset)
            cheek_pos = (self.body[0].x * CELL_SIZE + 4,
                        self.body[0].y * CELL_SIZE + CELL_SIZE//2)
        elif self.direction == Vector2(0, -1):  # Up
            left_eye_pos = (self.body[0].x * CELL_SIZE + eye_offset,
                          self.body[0].y * CELL_SIZE + eye_offset)
            right_eye_pos = (self.body[0].x * CELL_SIZE + CELL_SIZE - eye_offset,
                           self.body[0].y * CELL_SIZE + eye_offset)
            cheek_pos = (self.body[0].x * CELL_SIZE + CELL_SIZE//2,
                        self.body[0].y * CELL_SIZE + 4)
        else:  # Down
            left_eye_pos = (self.body[0].x * CELL_SIZE + eye_offset,
                          self.body[0].y * CELL_SIZE + CELL_SIZE - eye_offset)
            right_eye_pos = (self.body[0].x * CELL_SIZE + CELL_SIZE - eye_offset,
                           self.body[0].y * CELL_SIZE + CELL_SIZE - eye_offset)
            cheek_pos = (self.body[0].x * CELL_SIZE + CELL_SIZE//2,
                        self.body[0].y * CELL_SIZE + CELL_SIZE - 4)
        
        # Draw eyes with shine
        pygame.draw.circle(screen, eye_color, left_eye_pos, eye_size)
        pygame.draw.circle(screen, eye_color, right_eye_pos, eye_size)
        
        # Add shine to eyes (small white circles)
        shine_offset = 2
        pygame.draw.circle(screen, (255, 255, 255), 
                         (left_eye_pos[0] - shine_offset, left_eye_pos[1] - shine_offset), 3)
        pygame.draw.circle(screen, (255, 255, 255), 
                         (right_eye_pos[0] - shine_offset, right_eye_pos[1] - shine_offset), 3)
        
        # Draw rosy cheeks
        pygame.draw.circle(screen, cheek_color, 
                         (left_eye_pos[0], left_eye_pos[1] + cheek_size), cheek_size)
        pygame.draw.circle(screen, cheek_color, 
                         (right_eye_pos[0], right_eye_pos[1] + cheek_size), cheek_size)
        
        # Draw tongue (more playful, curvy tongue)
        tongue_color = (255, 105, 180)  # Brighter pink tongue
        tongue_start = (
            self.body[0].x * CELL_SIZE + CELL_SIZE/2,
            self.body[0].y * CELL_SIZE + CELL_SIZE/2
        )
        
        # Calculate tongue end position based on direction
        tongue_length = 12  # Slightly longer tongue
        tongue_fork = 5  # Bigger fork
        if self.direction == Vector2(1, 0):  # Right
            tongue_end = (tongue_start[0] + tongue_length, tongue_start[1])
            # Add a slight curve to the tongue
            control_point = (tongue_end[0] - 4, tongue_end[1] - 2)
            fork1 = (tongue_end[0] + 2, tongue_end[1] - tongue_fork)
            fork2 = (tongue_end[0] + 2, tongue_end[1] + tongue_fork)
        elif self.direction == Vector2(-1, 0):  # Left
            tongue_end = (tongue_start[0] - tongue_length, tongue_start[1])
            control_point = (tongue_end[0] + 4, tongue_end[1] - 2)
            fork1 = (tongue_end[0] - 2, tongue_end[1] - tongue_fork)
            fork2 = (tongue_end[0] - 2, tongue_end[1] + tongue_fork)
        elif self.direction == Vector2(0, -1):  # Up
            tongue_end = (tongue_start[0], tongue_start[1] - tongue_length)
            control_point = (tongue_end[0] - 2, tongue_end[1] + 4)
            fork1 = (tongue_end[0] - tongue_fork, tongue_end[1] - 2)
            fork2 = (tongue_end[0] + tongue_fork, tongue_end[1] - 2)
        else:  # Down
            tongue_end = (tongue_start[0], tongue_start[1] + tongue_length)
            control_point = (tongue_end[0] - 2, tongue_end[1] - 4)
            fork1 = (tongue_end[0] - tongue_fork, tongue_end[1] + 2)
            fork2 = (tongue_end[0] + tongue_fork, tongue_end[1] + 2)
        
        # Draw curvy tongue
        points = [tongue_start, control_point, tongue_end]
        pygame.draw.lines(screen, tongue_color, False, points, 3)
        # Draw forked ends with rounded tips
        pygame.draw.circle(screen, tongue_color, fork1, 2)
        pygame.draw.circle(screen, tongue_color, fork2, 2)
        pygame.draw.line(screen, tongue_color, tongue_end, fork1, 3)
        pygame.draw.line(screen, tongue_color, tongue_end, fork2, 3)
    
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

class Food:
    def __init__(self):
        self.pos = None
        self.randomize()
    
    def randomize(self):
        """Randomize food position, ensuring it doesn't spawn on snake."""
        if not hasattr(self, 'game'):
            self.pos = Vector2(random.randint(0, CELL_NUMBER-1), random.randint(0, CELL_NUMBER-1))
            return
            
        # Get list of all occupied positions (snake body)
        occupied_positions = [Vector2(segment.x, segment.y) for segment in self.game.snake.body]
        
        # Generate all possible positions
        all_positions = [Vector2(x, y) for x in range(CELL_NUMBER) for y in range(CELL_NUMBER)]
        
        # Remove occupied positions
        available_positions = [pos for pos in all_positions if pos not in occupied_positions]
        
        if available_positions:
            # Choose random available position
            self.pos = random.choice(available_positions)
        else:
            # Fallback if no positions available (shouldn't happen in normal gameplay)
            self.pos = Vector2(random.randint(0, CELL_NUMBER-1), random.randint(0, CELL_NUMBER-1))
    
    def draw(self):
        if self.pos is not None:  # Only draw if position is set
            rect = pygame.Rect(self.pos.x * CELL_SIZE, self.pos.y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, FOOD_COLOR, rect, border_radius=10)

class Projectile:
    def __init__(self, pos, direction, owner):
        self.pos = Vector2(pos)
        self.direction = Vector2(direction)
        self.owner = owner
    
    def move(self):
        self.pos += self.direction
    
    def draw(self):
        pos = (int(self.pos.x * CELL_SIZE + CELL_SIZE/2), 
               int(self.pos.y * CELL_SIZE + CELL_SIZE/2))
        pygame.draw.circle(screen, PROJECTILE_COLOR, pos, 5)

def color_selection_screen():
    """Let player choose their snake color."""
    font = pygame.font.Font(None, 48)
    button_size = 80
    gap = 20
    colors_per_row = 4
    
    while True:
        screen.fill(BACKGROUND_COLOR)
        
        # Draw title
        title = font.render("Select Your Snake Color", True, TEXT_COLOR)
        title_rect = title.get_rect(center=(SCREEN_SIZE/2, 50))
        screen.blit(title, title_rect)
        
        # Draw color buttons
        color_rects = {}
        for i, (color_name, color_value) in enumerate(SNAKE_COLORS.items()):
            row = i // colors_per_row
            col = i % colors_per_row
            x = (SCREEN_SIZE - (button_size * colors_per_row + gap * (colors_per_row - 1))) // 2 + col * (button_size + gap)
            y = 150 + row * (button_size + gap)
            rect = pygame.Rect(x, y, button_size, button_size)
            pygame.draw.rect(screen, color_value, rect)
            
            # Draw color name
            name_font = pygame.font.Font(None, 24)
            text = name_font.render(color_name, True, TEXT_COLOR)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
            
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
        
        clock.tick(60)

class Game:
    def __init__(self):
        # Let player choose color before starting
        snake_color = color_selection_screen()
        self.snake = Snake((5, 5), snake_color)
        self.food = Food()
        self.food.game = self  # Give food reference to game instance
        self.projectiles = []
        self.font = pygame.font.Font(None, 40)
        self.game_over = False
        self.level = 1
        self.base_speed = 2  # Reduced from 4 to 2 for slower initial speed
        self.points_to_next_level = 5
        self.glow_effect = 0  # For pulsing effects
        
    def get_current_speed(self):
        """Calculate game speed based on current level"""
        # More gradual speed increase (0.5 FPS per level instead of 1)
        # Cap speed at 10 instead of 15 for better control
        return min(self.base_speed + (self.level - 1) * 0.5, 10)
    
    def check_level_up(self):
        """Check if player should advance to next level"""
        if self.snake.score >= self.level * self.points_to_next_level:
            self.level += 1
            # Play level up sound or add visual effect here if desired
            return True
        return False
    
    def update(self):
        if not self.game_over:
            # Update snake
            if self.snake.stunned > 0:
                self.snake.stunned -= 1
            else:
                self.snake.move()
            
            # Check for level up
            self.check_level_up()
            
            # Update projectiles
            if self.snake.projectile_cooldown > 0:
                self.snake.projectile_cooldown -= 1
            if self.snake.projectiles < MAX_PROJECTILES and random.random() < 0.01:
                self.snake.projectiles += 1
            
            for proj in self.projectiles[:]:
                proj.move()
                if (proj.pos.x < 0 or proj.pos.x >= CELL_NUMBER or 
                    proj.pos.y < 0 or proj.pos.y >= CELL_NUMBER):
                    self.projectiles.remove(proj)
            
            # Check collisions
            self.check_collisions()
    
    def check_collisions(self):
        # Food collision
        if self.snake.body[0] == self.food.pos:
            self.snake.grow()
            self.food.randomize()
            # Verify food isn't on snake after randomizing
            while self.food.pos in self.snake.body:
                self.food.randomize()
        
        # Wall collision
        if not (0 <= self.snake.body[0].x < CELL_NUMBER and 
                0 <= self.snake.body[0].y < CELL_NUMBER):
            self.game_over = True
        
        # Self collision
        if self.snake.body[0] in self.snake.body[1:]:
            self.game_over = True
    
    def draw_grid(self):
        """Draw a subtle grid background."""
        for x in range(0, SCREEN_SIZE, GRID_SPACING):
            alpha = abs(math.sin(self.glow_effect + x * 0.01)) * 30 + 20
            grid_surface = pygame.Surface((2, SCREEN_SIZE), pygame.SRCALPHA)
            grid_surface.fill((GRID_COLOR[0], GRID_COLOR[1], GRID_COLOR[2], int(alpha)))
            screen.blit(grid_surface, (x, 0))
            
        for y in range(0, SCREEN_SIZE, GRID_SPACING):
            alpha = abs(math.sin(self.glow_effect + y * 0.01)) * 30 + 20
            grid_surface = pygame.Surface((SCREEN_SIZE, 2), pygame.SRCALPHA)
            grid_surface.fill((GRID_COLOR[0], GRID_COLOR[1], GRID_COLOR[2], int(alpha)))
            screen.blit(grid_surface, (0, y))
    
    def draw_neon_text(self, text, color, position, size=40, is_hud=False):
        """Draw text with a neon glow effect. HUD elements have reduced glow."""
        font = pygame.font.Font(None, size)
        
        # Base text
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=position)
        
        # Glow effect - reduced for HUD elements
        if is_hud:
            glow_size = int(abs(math.sin(self.glow_effect * 2)) * 8) + 5  # Reduced glow size
            glow_steps = 3  # Fewer glow layers
        else:
            glow_size = int(abs(math.sin(self.glow_effect * 2)) * 15) + 10
            glow_steps = 5
        
        for i in range(glow_size, 0, -glow_size//glow_steps):
            alpha = int((1 - i/glow_size) * (80 if is_hud else 100))
            glow = font.render(text, True, (*color[:3], alpha))
            glow_rect = glow.get_rect(center=position)
            screen.blit(glow, (glow_rect.x - i//2, glow_rect.y - i//2))
        
        # Draw the sharp text on top
        screen.blit(text_surface, text_rect)
    
    def draw_glitch_text(self, text, color, position, size=64, scramble=False):
        """Draw text with a glitch effect."""
        font = pygame.font.Font(None, size)
        
        # Create stronger offset for chromatic aberration
        offset = math.sin(self.glow_effect * 3) * 6  # Increased from 4 to 6
        
        # Scramble text if enabled
        if scramble:
            chars = list(text)
            scramble_chance = 0.3
            for i in range(len(chars)):
                if random.random() < scramble_chance:
                    chars[i] = chr(random.randint(33, 126))
            scrambled_text = ''.join(chars)
        else:
            scrambled_text = text
        
        # Draw glitch layers with stronger separation
        glitch_colors = [
            (255, 0, 77),   # Red channel
            (0, 255, 255),  # Cyan channel
            (255, 255, 255) # Base text
        ]
        
        offsets = [
            (offset * 1.2, -offset * 1.2),  # Increased separation
            (-offset * 0.8, offset * 0.8),   # Increased separation
            (0, 0)
        ]
        
        # Random glitch offset
        glitch_x = random.randint(-3, 3) if scramble else 0
        glitch_y = random.randint(-3, 3) if scramble else 0
        
        # Draw each layer with offset
        for color, (x_offset, y_offset) in zip(glitch_colors, offsets):
            display_text = scrambled_text if scramble and random.random() < 0.3 else text
            
            text_surface = font.render(display_text, True, color)
            text_rect = text_surface.get_rect(center=position)
            text_rect.x += x_offset + glitch_x
            text_rect.y += y_offset + glitch_y
            screen.blit(text_surface, text_rect)
            
            # Add random noise lines for scrambled text
            if scramble and random.random() < 0.2:
                noise_height = random.randint(1, 3)
                noise_surface = pygame.Surface((text_rect.width, noise_height))
                noise_surface.fill(color)
                noise_y = text_rect.y + random.randint(0, text_rect.height)
                screen.blit(noise_surface, (text_rect.x, noise_y))

    def draw_hud_text(self, text, color, position, size=36):
        """Draw HUD text with a bubbly/rounded style and stronger glow effect."""
        # Create multiple layers of glow with increasing size
        base_font = pygame.font.Font(None, size)
        
        # Stronger outer glow
        for glow_size in range(8, 0, -2):
            glow_color = (*color, 40)  # Lower alpha for outer glow
            glow_surface = base_font.render(text, True, glow_color)
            glow_rect = glow_surface.get_rect(center=position)
            # Apply offset in all directions
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                offset_pos = (glow_rect.x + dx * glow_size, glow_rect.y + dy * glow_size)
                screen.blit(glow_surface, offset_pos)
        
        # Medium glow layer
        for glow_size in range(4, 0, -1):
            glow_color = (*color, 60)
            glow_surface = base_font.render(text, True, glow_color)
            glow_rect = glow_surface.get_rect(center=position)
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                offset_pos = (glow_rect.x + dx * glow_size, glow_rect.y + dy * glow_size)
                screen.blit(glow_surface, offset_pos)
        
        # Inner glow
        glow_color = (*color, 120)
        glow_surface = base_font.render(text, True, glow_color)
        glow_rect = glow_surface.get_rect(center=position)
        screen.blit(glow_surface, (glow_rect.x - 1, glow_rect.y - 1))
        screen.blit(glow_surface, (glow_rect.x + 1, glow_rect.y + 1))
        
        # Main text
        text_surface = base_font.render(text, True, (255, 255, 255))  # White core
        text_rect = text_surface.get_rect(center=position)
        screen.blit(text_surface, text_rect)

    def draw(self):
        screen.fill(BACKGROUND_COLOR)
        self.glow_effect += 0.05
        
        # Draw animated grid
        self.draw_grid()
        
        # Draw game elements
        self.food.draw()
        self.snake.draw()
        
        # Draw projectiles with glow
        for proj in self.projectiles:
            proj.draw()
            # Add glow effect to projectiles
            glow_size = int(abs(math.sin(self.glow_effect * 3)) * 8) + 5
            for i in range(glow_size, 0, -1):
                alpha = int((1 - i/glow_size) * 100)
                pygame.draw.circle(screen, (*PROJECTILE_COLOR, alpha),
                                 (int(proj.pos.x * CELL_SIZE + CELL_SIZE/2),
                                  int(proj.pos.y * CELL_SIZE + CELL_SIZE/2)), 5 + i)
        
        # Draw HUD with enhanced bubbly style
        hud_color = (0, 231, 255)  # Adjusted cyan color to match screenshot
        self.draw_hud_text(f'Score: {self.snake.score}', hud_color, (100, 30), 42)
        self.draw_hud_text(f'Level: {self.level}', hud_color, (SCREEN_SIZE - 100, 30), 42)
        
        # Draw progress to next level
        points_needed = (self.level * self.points_to_next_level) - self.snake.score
        if points_needed > 0:
            self.draw_hud_text(f'Next Level: {points_needed}', hud_color, (SCREEN_SIZE // 2, 30), 42)
        
        # Draw projectile charges with glow
        charge_color = PROJECTILE_COLOR
        for i in range(self.snake.projectiles):
            glow_size = int(abs(math.sin(self.glow_effect + i * 0.5)) * 4) + 3
            for j in range(glow_size, 0, -1):
                alpha = int((1 - j/glow_size) * 150)
                pygame.draw.circle(screen, (*charge_color, alpha),
                                 (20 + i * 20, SCREEN_SIZE - 30), 5 + j)
        
        # Draw stun indicator
        if self.snake.stunned > 0:
            self.draw_glitch_text('STUNNED!', (255, 0, 0), (SCREEN_SIZE/2, 50))
        
        # Draw game over
        if self.game_over:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def draw_game_over(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE))
        overlay.fill(BACKGROUND_COLOR)
        overlay.set_alpha(200)
        screen.blit(overlay, (0, 0))
        
        # Draw game over text with enhanced glitch effect
        self.draw_glitch_text('GAME OVER', (255, 255, 255), 
                            (SCREEN_SIZE/2, SCREEN_SIZE/2 - 80), 82)
        
        # Stats with HUD style - using the same bubbly glow effect as the HUD
        hud_color = (0, 231, 255)  # Same cyan color as HUD
        self.draw_hud_text(f'Final Score: {self.snake.score}', hud_color,
                          (SCREEN_SIZE/2, SCREEN_SIZE/2), 48)
        self.draw_hud_text(f'Level Reached: {self.level}', hud_color,
                          (SCREEN_SIZE/2, SCREEN_SIZE/2 + 50), 48)
        
        # Restart text with glitch effect
        self.draw_glitch_text('Press SPACE to restart', (255, 255, 255), 
                            (SCREEN_SIZE/2, SCREEN_SIZE/2 + 120), 36)
        self.draw_glitch_text('Press S to save game', (255, 255, 255),
                            (SCREEN_SIZE/2, SCREEN_SIZE/2 + 160), 36)

# Setup display
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
pygame.display.set_caption('Snake Game')
clock = pygame.time.Clock()

def mode_selection_screen():
    """Let player choose between single player and multiplayer modes."""
    font = pygame.font.Font(None, 64)
    button_font = pygame.font.Font(None, 48)
    
    # Button dimensions and positions
    button_width = 300
    button_height = 80
    gap = 40
    
    single_player_rect = pygame.Rect(
        (SCREEN_SIZE - button_width) // 2,
        SCREEN_SIZE // 2 - button_height - gap // 2,
        button_width,
        button_height
    )
    
    multiplayer_rect = pygame.Rect(
        (SCREEN_SIZE - button_width) // 2,
        SCREEN_SIZE // 2 + gap // 2,
        button_width,
        button_height
    )
    
    while True:
        screen.fill(BACKGROUND_COLOR)
        
        # Draw title with neon effect
        title = font.render("Snake Game", True, (0, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_SIZE/2, 100))
        
        # Add glow to title
        for i in range(20, 0, -4):
            glow = font.render("Snake Game", True, (0, 255, 255, int(255 * (1 - i/20))))
            glow_rect = glow.get_rect(center=(SCREEN_SIZE/2, 100))
            screen.blit(glow, (glow_rect.x - i//2, glow_rect.y - i//2))
        screen.blit(title, title_rect)
        
        # Draw buttons with hover effect
        mouse_pos = pygame.mouse.get_pos()
        
        # Single Player button
        hover_sp = single_player_rect.collidepoint(mouse_pos)
        sp_color = (0, 255, 255) if hover_sp else (0, 200, 200)
        pygame.draw.rect(screen, sp_color, single_player_rect, border_radius=15)
        sp_text = button_font.render("Single Player", True, (255, 255, 255))
        sp_text_rect = sp_text.get_rect(center=single_player_rect.center)
        screen.blit(sp_text, sp_text_rect)
        
        # Multiplayer button
        hover_mp = multiplayer_rect.collidepoint(mouse_pos)
        mp_color = (0, 255, 255) if hover_mp else (0, 200, 200)
        pygame.draw.rect(screen, mp_color, multiplayer_rect, border_radius=15)
        mp_text = button_font.render("Multiplayer", True, (255, 255, 255))
        mp_text_rect = mp_text.get_rect(center=multiplayer_rect.center)
        screen.blit(mp_text, mp_text_rect)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if single_player_rect.collidepoint(event.pos):
                    return "single"
                if multiplayer_rect.collidepoint(event.pos):
                    return "multi"
        
        clock.tick(60)

def main():
    while True:
        # Show mode selection screen
        mode = mode_selection_screen()
        
        if mode == "single":
            game = Game()
            SCREEN_UPDATE = pygame.USEREVENT
            pygame.time.set_timer(SCREEN_UPDATE, 150)

            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == SCREEN_UPDATE:
                        game.update()
                    if event.type == pygame.KEYDOWN:
                        if game.game_over:
                            if event.key == pygame.K_SPACE:
                                game = Game()  # Reset game
                            elif event.key == pygame.K_s:
                                save_path = save_single_player_game(game.snake, game.level, game.snake.score)
                                print(f"Game saved to: {save_path}")
                            elif event.key == pygame.K_ESCAPE:  # Return to mode selection
                                running = False
                        elif not game.snake.stunned:
                            if event.key == pygame.K_UP and game.snake.direction.y != 1:
                                game.snake.direction = Vector2(0, -1)
                            if event.key == pygame.K_DOWN and game.snake.direction.y != -1:
                                game.snake.direction = Vector2(0, 1)
                            if event.key == pygame.K_LEFT and game.snake.direction.x != 1:
                                game.snake.direction = Vector2(-1, 0)
                            if event.key == pygame.K_RIGHT and game.snake.direction.x != -1:
                                game.snake.direction = Vector2(1, 0)
                            if event.key == pygame.K_SPACE:
                                proj = game.snake.shoot_projectile()
                                if proj:
                                    game.projectiles.append(proj)
                            if event.key == pygame.K_s and not game.game_over:  # Save during gameplay
                                save_path = save_single_player_game(game.snake, game.level, game.snake.score)
                                print(f"Game saved to: {save_path}")
                            elif event.key == pygame.K_ESCAPE:  # Return to mode selection
                                running = False

                game.draw()
                clock.tick(game.get_current_speed())
        else:
            # Import and run multiplayer game
            from multiplayer import run_multiplayer_game
            run_multiplayer_game()

def load_saved_game(save_data):
    """Load a saved single player game."""
    if save_data['mode'] != 'single_player':
        print("Error: Not a single player save file")
        return
        
    game = Game()
    snake_data = save_data['snake_data']
    
    # Restore snake state
    game.snake.body = [Vector2(x, y) for x, y in snake_data['body']]
    game.snake.direction = Vector2(snake_data['direction'][0], snake_data['direction'][1])
    game.snake.color = snake_data['color']
    game.snake.score = snake_data['score']
    game.snake.projectiles = snake_data['projectiles_available']
    game.snake.projectile_cooldown = snake_data['projectile_cooldown']
    
    # Restore game state
    game.level = snake_data['level']
    
    # Start game loop
    SCREEN_UPDATE = pygame.USEREVENT
    pygame.time.set_timer(SCREEN_UPDATE, 150)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == SCREEN_UPDATE:
                game.update()
            if event.type == pygame.KEYDOWN:
                if game.game_over:
                    if event.key == pygame.K_SPACE:
                        game = Game()
                    elif event.key == pygame.K_s:
                        save_path = save_single_player_game(game.snake, game.level, game.snake.score)
                        print(f"Game saved to: {save_path}")
                elif not game.snake.stunned:
                    if event.key == pygame.K_UP and game.snake.direction.y != 1:
                        game.snake.direction = Vector2(0, -1)
                    if event.key == pygame.K_DOWN and game.snake.direction.y != -1:
                        game.snake.direction = Vector2(0, 1)
                    if event.key == pygame.K_LEFT and game.snake.direction.x != 1:
                        game.snake.direction = Vector2(-1, 0)
                    if event.key == pygame.K_RIGHT and game.snake.direction.x != -1:
                        game.snake.direction = Vector2(1, 0)
                    if event.key == pygame.K_SPACE:
                        proj = game.snake.shoot_projectile()
                        if proj:
                            game.projectiles.append(proj)
                    if event.key == pygame.K_s:
                        save_path = save_single_player_game(game.snake, game.level, game.snake.score)
                        print(f"Game saved to: {save_path}")
        
        game.draw()
        clock.tick(game.get_current_speed())

if __name__ == "__main__":
    main() 