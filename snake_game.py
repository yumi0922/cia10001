import pygame
import random
import sys
from pygame.math import Vector2
import math

# Initialize Pygame
pygame.init()

# Constants
CELL_SIZE = 30
CELL_NUMBER = 25
SCREEN_SIZE = CELL_SIZE * CELL_NUMBER

# Colors
BACKGROUND_COLOR = (40, 40, 40)
FOOD_COLOR = (207, 68, 68)
SCORE_COLOR = (255, 255, 255)
TEXT_COLOR = (255, 255, 255)
PROJECTILE_COLOR = (255, 255, 0)  # Yellow projectiles

# Game settings
PROJECTILE_SPEED = 15
PROJECTILE_COOLDOWN = 60  # Frames between shots
STUN_DURATION = 30  # Frames to stay stunned
MAX_PROJECTILES = 5  # Maximum projectiles per player increased to 5

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

# Setup the display
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
pygame.display.set_caption('2-Player Snake Battle')
clock = pygame.time.Clock()

def draw_color_button(color_name, color_value, rect, selected=False):
    pygame.draw.rect(screen, color_value, rect)
    if selected:
        pygame.draw.rect(screen, TEXT_COLOR, rect, 3)  # Highlight selected color
    font = pygame.font.Font(None, 24)
    text = font.render(color_name, True, TEXT_COLOR)
    text_rect = text.get_rect(center=rect.center)
    screen.blit(text, text_rect)
    return rect

def color_selection_screen():
    font = pygame.font.Font(None, 48)
    button_size = 80
    gap = 20
    colors_per_row = 4
    
    player1_color = None
    player2_color = None
    selecting_player1 = True
    
    while True:
        screen.fill(BACKGROUND_COLOR)
        
        # Draw title
        title = font.render(f"Select color for Player {'1' if selecting_player1 else '2'}", True, TEXT_COLOR)
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
            
            # Don't show already selected color for player 2
            if selecting_player1 or (not selecting_player1 and color_value != player1_color):
                selected = (selecting_player1 and color_value == player1_color) or \
                          (not selecting_player1 and color_value == player2_color)
                color_rects[color_name] = draw_color_button(color_name, color_value, rect, selected)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for color_name, rect in color_rects.items():
                    if rect.collidepoint(mouse_pos):
                        if selecting_player1:
                            player1_color = SNAKE_COLORS[color_name]
                            selecting_player1 = False
                            break
                        else:
                            player2_color = SNAKE_COLORS[color_name]
                            return player1_color, player2_color

        clock.tick(60)

class Projectile:
    def __init__(self, pos, direction, owner):
        self.pos = Vector2(pos)
        self.direction = Vector2(direction).normalize()
        self.owner = owner
        self.radius = 5
        
    def move(self):
        self.pos += self.direction * PROJECTILE_SPEED
        
    def draw(self):
        pygame.draw.circle(screen, PROJECTILE_COLOR, 
                         (int(self.pos.x * CELL_SIZE), int(self.pos.y * CELL_SIZE)), 
                         self.radius)
        
    def check_collision(self, snake):
        for block in snake.body:
            distance = math.hypot(
                self.pos.x - block.x,
                self.pos.y - block.y
            )
            if distance < 1:  # Hit within one cell
                return True
        return False

class Snake:
    def __init__(self, start_pos, color):
        self.body = [Vector2(start_pos[0], start_pos[1]), 
                    Vector2(start_pos[0]-1, start_pos[1]), 
                    Vector2(start_pos[0]-2, start_pos[1])]
        self.direction = Vector2(1, 0)
        self.new_block = False
        self.color = color
        self.score = 0
        self.alive = True
        self.projectile_cooldown = 0
        self.projectiles_available = MAX_PROJECTILES
        self.stunned = 0  # Frames remaining being stunned
        
    def draw(self):
        for block in self.body:
            block_rect = pygame.Rect(block.x * CELL_SIZE, block.y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, self.color, block_rect, border_radius=8)
            
        # Draw projectile charges
        for i in range(self.projectiles_available):
            pygame.draw.circle(screen, PROJECTILE_COLOR,
                             (20 + i * 20, SCREEN_SIZE - 20),
                             5)
            
    def move(self):
        if not self.alive or self.stunned > 0:
            self.stunned = max(0, self.stunned - 1)
            return
            
        if self.new_block:
            body_copy = self.body[:]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy
            self.new_block = False
        else:
            body_copy = self.body[:-1]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy
            
    def grow(self):
        self.new_block = True
        self.score += 1
        
    def shoot_projectile(self):
        if (self.projectile_cooldown <= 0 and 
            self.projectiles_available > 0 and 
            self.alive and 
            self.stunned <= 0):
            self.projectile_cooldown = PROJECTILE_COOLDOWN
            self.projectiles_available -= 1
            return Projectile(self.body[0], self.direction, self)
        return None
        
    def update(self):
        self.projectile_cooldown = max(0, self.projectile_cooldown - 1)
        if self.projectile_cooldown <= 0 and self.projectiles_available < MAX_PROJECTILES:
            self.projectiles_available += 1
            self.projectile_cooldown = PROJECTILE_COOLDOWN

class Food:
    def __init__(self):
        self.randomize()
        
    def draw(self):
        food_rect = pygame.Rect(self.pos.x * CELL_SIZE, self.pos.y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, FOOD_COLOR, food_rect, border_radius=10)
        
    def randomize(self):
        self.x = random.randint(0, CELL_NUMBER - 1)
        self.y = random.randint(0, CELL_NUMBER - 1)
        self.pos = Vector2(self.x, self.y)

class Game:
    def __init__(self, player1_color, player2_color):
        self.snake1 = Snake((5, 5), player1_color)
        self.snake2 = Snake((CELL_NUMBER-5, CELL_NUMBER-5), player2_color)
        self.food = Food()
        self.font = pygame.font.Font(None, 40)
        self.projectiles = []
        
    def update(self):
        self.snake1.update()
        self.snake2.update()
        self.snake1.move()
        self.snake2.move()
        self.check_collision()
        self.check_fail()
        
        # Update projectiles
        for proj in self.projectiles[:]:
            proj.move()
            # Check if projectile hits the other snake
            target_snake = self.snake2 if proj.owner == self.snake1 else self.snake1
            if proj.check_collision(target_snake):
                target_snake.stunned = STUN_DURATION
                self.projectiles.remove(proj)
            # Remove projectiles that go off screen
            elif (proj.pos.x < 0 or proj.pos.x > CELL_NUMBER or 
                  proj.pos.y < 0 or proj.pos.y > CELL_NUMBER):
                self.projectiles.remove(proj)
        
    def draw(self):
        screen.fill(BACKGROUND_COLOR)
        self.food.draw()
        self.snake1.draw()
        self.snake2.draw()
        
        # Draw projectiles
        for proj in self.projectiles:
            proj.draw()
            
        self.draw_scores()
        
        # Draw stun indicators
        if self.snake1.stunned > 0:
            self.draw_stun_indicator(self.snake1)
        if self.snake2.stunned > 0:
            self.draw_stun_indicator(self.snake2)
            
        pygame.display.update()
        
    def draw_stun_indicator(self, snake):
        text = self.font.render("STUNNED!", True, snake.color)
        pos = (SCREEN_SIZE//4 if snake == self.snake1 else 3*SCREEN_SIZE//4, 50)
        text_rect = text.get_rect(center=pos)
        screen.blit(text, text_rect)
        
    def check_collision(self):
        # Check food collision for both snakes
        if self.food.pos == self.snake1.body[0] and self.snake1.alive:
            self.food.randomize()
            self.snake1.grow()
        if self.food.pos == self.snake2.body[0] and self.snake2.alive:
            self.food.randomize()
            self.snake2.grow()
            
    def check_fail(self):
        # Check wall collision for both snakes
        for snake in [self.snake1, self.snake2]:
            if not snake.alive:
                continue
                
            if not 0 <= snake.body[0].x < CELL_NUMBER or not 0 <= snake.body[0].y < CELL_NUMBER:
                snake.alive = False
                
            # Check self collision
            for block in snake.body[1:]:
                if block == snake.body[0]:
                    snake.alive = False
                    
            # Check collision with other snake
            other_snake = self.snake2 if snake == self.snake1 else self.snake1
            for block in other_snake.body:
                if block == snake.body[0]:
                    snake.alive = False
                    
        # Check if game is over (both snakes dead)
        if not self.snake1.alive and not self.snake2.alive:
            self.game_over()
                
    def game_over(self):
        # Display winner before quitting
        screen.fill(BACKGROUND_COLOR)
        if self.snake1.score > self.snake2.score:
            winner_text = "Player 1 Wins!"
        elif self.snake2.score > self.snake1.score:
            winner_text = "Player 2 Wins!"
        else:
            winner_text = "It's a Tie!"
            
        text = self.font.render(winner_text, True, SCORE_COLOR)
        text_rect = text.get_rect(center=(SCREEN_SIZE/2, SCREEN_SIZE/2))
        screen.blit(text, text_rect)
        pygame.display.update()
        pygame.time.wait(2000)  # Show result for 2 seconds
        pygame.quit()
        sys.exit()
        
    def draw_scores(self):
        # Player 1 score (top left)
        score1_text = self.font.render(f'P1: {self.snake1.score}', True, self.snake1.color)
        score1_rect = score1_text.get_rect(topleft=(20, 20))
        screen.blit(score1_text, score1_rect)
        
        # Player 2 score (top right)
        score2_text = self.font.render(f'P2: {self.snake2.score}', True, self.snake2.color)
        score2_rect = score2_text.get_rect(topright=(SCREEN_SIZE-20, 20))
        screen.blit(score2_text, score2_rect)

# Main game
def main():
    # Get player color choices
    player1_color, player2_color = color_selection_screen()
    
    # Start the game with selected colors
    game = Game(player1_color, player2_color)
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
                # Player 1 controls (Arrow keys + SPACE)
                if game.snake1.alive and game.snake1.stunned <= 0:
                    if event.key == pygame.K_UP and game.snake1.direction.y != 1:
                        game.snake1.direction = Vector2(0, -1)
                    if event.key == pygame.K_DOWN and game.snake1.direction.y != -1:
                        game.snake1.direction = Vector2(0, 1)
                    if event.key == pygame.K_LEFT and game.snake1.direction.x != 1:
                        game.snake1.direction = Vector2(-1, 0)
                    if event.key == pygame.K_RIGHT and game.snake1.direction.x != -1:
                        game.snake1.direction = Vector2(1, 0)
                    if event.key == pygame.K_SPACE:  # Shoot projectile
                        proj = game.snake1.shoot_projectile()
                        if proj:
                            game.projectiles.append(proj)
                
                # Player 2 controls (WASD + SHIFT)
                if game.snake2.alive and game.snake2.stunned <= 0:
                    if event.key == pygame.K_w and game.snake2.direction.y != 1:
                        game.snake2.direction = Vector2(0, -1)
                    if event.key == pygame.K_s and game.snake2.direction.y != -1:
                        game.snake2.direction = Vector2(0, 1)
                    if event.key == pygame.K_a and game.snake2.direction.x != 1:
                        game.snake2.direction = Vector2(-1, 0)
                    if event.key == pygame.K_d and game.snake2.direction.x != -1:
                        game.snake2.direction = Vector2(1, 0)
                    if event.key == pygame.K_LSHIFT:  # Shoot projectile
                        proj = game.snake2.shoot_projectile()
                        if proj:
                            game.projectiles.append(proj)
        
        game.draw()
        clock.tick(60)

if __name__ == "__main__":
    main()
    