import pygame
import sys
from pygame.math import Vector2
from single_player import Snake, CELL_SIZE, CELL_NUMBER, SCREEN_SIZE, BACKGROUND_COLOR, screen, clock

class MultiplayerGame:
    def __init__(self):
        # Create two snakes with different starting positions and colors
        self.snake1 = Snake((5, 5), (255, 66, 161))  # Pink snake
        self.snake2 = Snake((CELL_NUMBER-5, CELL_NUMBER-5), (0, 255, 255))  # Cyan snake
        self.game_over = False
        self.winner = None
        
    def update(self):
        if not self.game_over:
            # Update both snakes
            if self.snake1.stunned > 0:
                self.snake1.stunned -= 1
            else:
                self.snake1.move()
                
            if self.snake2.stunned > 0:
                self.snake2.stunned -= 1
            else:
                self.snake2.move()
            
            # Check collisions
            self.check_collisions()
    
    def check_collisions(self):
        # Wall collisions
        for snake in [self.snake1, self.snake2]:
            if not (0 <= snake.body[0].x < CELL_NUMBER and 
                    0 <= snake.body[0].y < CELL_NUMBER):
                self.game_over = True
                self.winner = self.snake2 if snake == self.snake1 else self.snake1
        
        # Snake collisions with self
        if self.snake1.body[0] in self.snake1.body[1:]:
            self.game_over = True
            self.winner = self.snake2
        if self.snake2.body[0] in self.snake2.body[1:]:
            self.game_over = True
            self.winner = self.snake1
            
        # Snake collisions with each other
        if self.snake1.body[0] in self.snake2.body or self.snake2.body[0] in self.snake1.body:
            self.game_over = True
            # If head-on collision, no winner
            if self.snake1.body[0] == self.snake2.body[0]:
                self.winner = None
            else:
                # Winner is the snake that didn't collide with the other's body
                self.winner = self.snake2 if self.snake1.body[0] in self.snake2.body else self.snake1
    
    def draw(self):
        screen.fill(BACKGROUND_COLOR)
        
        # Draw both snakes
        self.snake1.draw()
        self.snake2.draw()
        
        # Draw game over screen if needed
        if self.game_over:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def draw_game_over(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE))
        overlay.fill(BACKGROUND_COLOR)
        overlay.set_alpha(200)
        screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 64)
        
        # Draw game over message
        game_over_text = font.render('GAME OVER', True, (255, 255, 255))
        text_rect = game_over_text.get_rect(center=(SCREEN_SIZE/2, SCREEN_SIZE/2 - 50))
        screen.blit(game_over_text, text_rect)
        
        # Draw winner message
        if self.winner:
            winner_color = self.winner.color
            winner_text = "Pink Snake Wins!" if winner_color == self.snake1.color else "Blue Snake Wins!"
        else:
            winner_text = "It's a Tie!"
            winner_color = (255, 255, 255)
        
        winner_surface = font.render(winner_text, True, winner_color)
        winner_rect = winner_surface.get_rect(center=(SCREEN_SIZE/2, SCREEN_SIZE/2 + 50))
        screen.blit(winner_surface, winner_rect)
        
        # Draw restart instruction
        restart_font = pygame.font.Font(None, 36)
        restart_text = restart_font.render('Press SPACE to restart or ESC for menu', True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(SCREEN_SIZE/2, SCREEN_SIZE/2 + 120))
        screen.blit(restart_text, restart_rect)

def run_multiplayer_game():
    game = MultiplayerGame()
    
    SCREEN_UPDATE = pygame.USEREVENT
    pygame.time.set_timer(SCREEN_UPDATE, 150)  # Same speed as single player
    
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
                        game = MultiplayerGame()  # Reset game
                    elif event.key == pygame.K_ESCAPE:
                        return  # Return to mode selection
                else:
                    # Snake 1 controls (WASD)
                    if not game.snake1.stunned:
                        if event.key == pygame.K_w and game.snake1.direction.y != 1:
                            game.snake1.direction = Vector2(0, -1)
                        if event.key == pygame.K_s and game.snake1.direction.y != -1:
                            game.snake1.direction = Vector2(0, 1)
                        if event.key == pygame.K_a and game.snake1.direction.x != 1:
                            game.snake1.direction = Vector2(-1, 0)
                        if event.key == pygame.K_d and game.snake1.direction.x != -1:
                            game.snake1.direction = Vector2(1, 0)
                    
                    # Snake 2 controls (Arrow keys)
                    if not game.snake2.stunned:
                        if event.key == pygame.K_UP and game.snake2.direction.y != 1:
                            game.snake2.direction = Vector2(0, -1)
                        if event.key == pygame.K_DOWN and game.snake2.direction.y != -1:
                            game.snake2.direction = Vector2(0, 1)
                        if event.key == pygame.K_LEFT and game.snake2.direction.x != 1:
                            game.snake2.direction = Vector2(-1, 0)
                        if event.key == pygame.K_RIGHT and game.snake2.direction.x != -1:
                            game.snake2.direction = Vector2(1, 0)
                    
                    if event.key == pygame.K_ESCAPE:
                        return  # Return to mode selection
        
        game.draw()
        clock.tick(60)  # Fixed speed for multiplayer 