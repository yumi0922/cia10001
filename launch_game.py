import pygame
import sys
import subprocess
import threading
from server import LobbyServer
import math
import os
import numpy
from scipy.io import wavfile

# Create assets directory if it doesn't exist
os.makedirs('assets', exist_ok=True)

# Initialize Pygame mixer for audio
pygame.mixer.init()

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.current_music = None
        self.volume = 0.7
        
        # Create default background music
        self.create_background_music()
        
        # Create sound effects
        self.create_sound_effects()
        
    def create_background_music(self):
        """Generate a simple background music using Pygame."""
        sample_rate = 44100
        duration = 4.0  # seconds
        n_samples = int(sample_rate * duration)
        
        # Create a synthesized melody
        buffer = numpy.zeros((n_samples, 2), dtype=numpy.int16)
        max_amplitude = numpy.iinfo(numpy.int16).max
        
        # Generate a simple melody
        frequencies = [262, 330, 392, 523]  # C4, E4, G4, C5
        for i, freq in enumerate(frequencies):
            t = numpy.linspace(0, duration/4, n_samples//4, False)
            tone = numpy.sin(2 * numpy.pi * freq * t) * max_amplitude * 0.5
            start = i * (n_samples//4)
            end = start + (n_samples//4)
            buffer[start:end, 0] = tone
            buffer[start:end, 1] = tone
        
        # Save as WAV file
        wavfile.write('assets/background_music.wav', sample_rate, buffer)
    
    def create_sound_effects(self):
        """Generate simple sound effects using Pygame."""
        sample_rate = 44100
        max_amplitude = numpy.iinfo(numpy.int16).max
        
        # Hover sound
        duration = 0.1
        t = numpy.linspace(0, duration, int(sample_rate * duration), False)
        hover_tone = numpy.sin(2 * numpy.pi * 440 * t) * max_amplitude * 0.3
        hover_buffer = numpy.column_stack((hover_tone, hover_tone))
        wavfile.write('assets/hover.wav', sample_rate, hover_buffer.astype(numpy.int16))
        
        # Click sound
        duration = 0.15
        t = numpy.linspace(0, duration, int(sample_rate * duration), False)
        click_tone = numpy.sin(2 * numpy.pi * 880 * t) * max_amplitude * 0.3
        click_buffer = numpy.column_stack((click_tone, click_tone))
        wavfile.write('assets/click.wav', sample_rate, click_buffer.astype(numpy.int16))
    
    def load_sounds(self):
        """Load all sound files."""
        try:
            # Load background music
            pygame.mixer.music.load('assets/background_music.wav')
            pygame.mixer.music.set_volume(self.volume)
            
            # Load sound effects
            self.sounds['hover'] = pygame.mixer.Sound('assets/hover.wav')
            self.sounds['click'] = pygame.mixer.Sound('assets/click.wav')
            
            for sound in self.sounds.values():
                sound.set_volume(self.volume)
        except Exception as e:
            print(f"Error loading sounds: {e}")
    
    def play_music(self):
        """Play background music in a loop."""
        try:
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
        except Exception as e:
            print(f"Error playing music: {e}")
    
    def stop_music(self):
        """Stop background music."""
        pygame.mixer.music.stop()
    
    def play_sound(self, sound_name):
        """Play a sound effect."""
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"Error playing sound {sound_name}: {e}")

# Neon color palette
NEON_PINK = (255, 16, 240)
NEON_BLUE = (0, 240, 255)
NEON_GREEN = (57, 255, 20)
NEON_YELLOW = (255, 255, 20)
NEON_PURPLE = (191, 62, 255)
NEON_ORANGE = (255, 153, 0)

def create_gradient_background(surface, time):
    """Create an animated gradient background."""
    height = surface.get_height()
    width = surface.get_width()
    for y in range(height):
        ratio = y / height
        # Create shifting colors based on time
        color1 = (
            int((math.sin(time * 0.5) * 0.5 + 0.5) * 100),
            int((math.sin(time * 0.3) * 0.5 + 0.5) * 50),
            int((math.sin(time * 0.7) * 0.5 + 0.5) * 100)
        )
        color2 = (
            int((math.cos(time * 0.6) * 0.5 + 0.5) * 50),
            int((math.cos(time * 0.4) * 0.5 + 0.5) * 100),
            int((math.cos(time * 0.8) * 0.5 + 0.5) * 100)
        )
        color = [
            color1[i] * (1 - ratio) + color2[i] * ratio
            for i in range(3)
        ]
        pygame.draw.line(surface, color, (0, y), (width, y))

def create_rainbow_text(text, font, time):
    """Create rainbow colored text with neon effect."""
    colors = [
        NEON_PINK,
        NEON_ORANGE,
        NEON_YELLOW,
        NEON_GREEN,
        NEON_BLUE,
        NEON_PURPLE
    ]
    text_surfaces = []
    for i, char in enumerate(text):
        color_index = (i + int(time * 2)) % len(colors)
        # Create main text
        text_surface = pygame.Surface((font.size(char)[0] + 4, font.size(char)[1] + 4), pygame.SRCALPHA)
        # Create glow effect
        for offset in range(3, 0, -1):
            glow = font.render(char, True, (*colors[color_index][:3], 100))
            text_surface.blit(glow, (offset, offset))
        # Create main text
        main = font.render(char, True, colors[color_index])
        text_surface.blit(main, (2, 2))
        text_surfaces.append(text_surface)
    return text_surfaces

def draw_rainbow_title(screen, text_surfaces, time, base_y=40):
    """Draw the rainbow title with wave animation."""
    total_width = sum(surface.get_width() for surface in text_surfaces)
    x = (screen.get_width() - total_width) // 2
    for i, surface in enumerate(text_surfaces):
        offset = math.sin(time * 3 + i * 0.5) * 10
        screen.blit(surface, (x, base_y + offset))
        x += surface.get_width()

def create_button_surface(width, height, text, font, color, time):
    """Create a stylish button surface with neon glow effect."""
    surface = pygame.Surface((width + 8, height + 8), pygame.SRCALPHA)
    
    # Create pulsing glow effect
    glow_intensity = (math.sin(time * 4) * 0.5 + 0.5) * 255
    for i in range(4, 0, -1):
        pygame.draw.rect(surface, (*color[:3], int(glow_intensity / i)),
                        pygame.Rect(4-i, 4-i, width+i*2, height+i*2),
                        border_radius=15)
    
    # Main button
    pygame.draw.rect(surface, color, pygame.Rect(4, 4, width, height),
                    border_radius=15)
    
    # Add gradient highlight
    for i in range(height//3):
        alpha = 100 - i * 3
        if alpha > 0:
            pygame.draw.rect(surface, (255, 255, 255, alpha),
                           pygame.Rect(4, 4+i, width, 2),
                           border_radius=15)
    
    # Add text with glow
    text_surface = font.render(text, True, (255, 255, 255))
    text_glow = font.render(text, True, (*color[:3], 150))
    
    text_rect = text_surface.get_rect(center=(width//2 + 4, height//2 + 4))
    surface.blit(text_glow, text_rect.move(2, 2))
    surface.blit(text_surface, text_rect)
    
    return surface

def start_server():
    server = LobbyServer()
    server.start()

def launch_client():
    subprocess.Popen([sys.executable, 'client.py'])

def main():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption('Snake Game Launcher')
    clock = pygame.time.Clock()
    
    # Initialize sound manager
    sound_manager = SoundManager()
    sound_manager.load_sounds()
    sound_manager.play_music()
    
    # Track button hover state to play sound only once
    button_hover_states = {i: False for i in range(3)}
    
    # Fonts
    title_font = pygame.font.Font(None, 48)
    button_font = pygame.font.Font(None, 36)
    
    # Button dimensions
    button_width = 200
    button_height = 50
    button_spacing = 20
    
    # Create buttons with neon colors
    buttons = [
        {
            'rect': pygame.Rect((400 - button_width) // 2, 80, button_width, button_height),
            'text': 'Single Player',
            'color': NEON_GREEN,
            'surface': None
        },
        {
            'rect': pygame.Rect((400 - button_width) // 2, 150, button_width, button_height),
            'text': 'Multiplayer',
            'color': NEON_BLUE,
            'surface': None
        },
        {
            'rect': pygame.Rect((400 - button_width) // 2, 220, button_width, button_height),
            'text': 'Quit',
            'color': NEON_PINK,
            'surface': None
        }
    ]
    
    running = True
    start_time = pygame.time.get_ticks()
    
    while running:
        current_time = (pygame.time.get_ticks() - start_time) / 1000
        
        # Create animated gradient background
        create_gradient_background(screen, current_time)
        
        # Create and draw animated rainbow title
        title_surfaces = create_rainbow_text('Snake Game', title_font, current_time)
        draw_rainbow_title(screen, title_surfaces, current_time)
        
        # Draw buttons with hover effect and sound
        mouse_pos = pygame.mouse.get_pos()
        for i, button in enumerate(buttons):
            # Update button surface with current time for animation
            button['surface'] = create_button_surface(
                button_width, button_height,
                button['text'], button_font,
                button['color'], current_time
            )
            
            # Handle hover state and sound
            is_hovered = button['rect'].collidepoint(mouse_pos)
            if is_hovered and not button_hover_states[i]:
                sound_manager.play_sound('hover')
                button_hover_states[i] = True
            elif not is_hovered:
                button_hover_states[i] = False
            
            if is_hovered:
                # Scale up button when hovered
                scaled_surface = pygame.transform.scale(
                    button['surface'],
                    (int(button_width * 1.1) + 8, int(button_height * 1.1) + 8)
                )
                scaled_rect = scaled_surface.get_rect(center=button['rect'].center)
                screen.blit(scaled_surface, scaled_rect)
            else:
                screen.blit(button['surface'], 
                          (button['rect'].x - 4, button['rect'].y - 4))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button['rect'].collidepoint(event.pos):
                        sound_manager.play_sound('click')
                        if button['text'] == 'Single Player':
                            server_thread = threading.Thread(target=start_server, daemon=True)
                            server_thread.start()
                            launch_client()
                            running = False
                        elif button['text'] == 'Multiplayer':
                            server_thread = threading.Thread(target=start_server, daemon=True)
                            server_thread.start()
                            launch_client()
                            launch_client()
                            running = False
                        elif button['text'] == 'Quit':
                            running = False
        
        clock.tick(60)
    
    # Stop music before quitting
    sound_manager.stop_music()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main() 