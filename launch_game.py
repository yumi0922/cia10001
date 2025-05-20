import pygame
import sys
import subprocess
import threading
from server import LobbyServer
import math
import os
import numpy
from scipy.io import wavfile
from scipy import signal
import time
import random
from pygame import gfxdraw
from save_game import list_saves, load_game
import single_player
import snake_game
from client import SnakeClient

# Create assets directory if it doesn't exist
os.makedirs('assets', exist_ok=True)

# Initialize Pygame mixer for audio
pygame.mixer.init()

# Colors
NEON_GREEN = (57, 255, 20)
NEON_BLUE = (0, 255, 255)
NEON_PINK = (255, 66, 161)

# Global variables
server_started = False

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.current_music = None
        self.volume = 0.3
        
        # Create default background music
        self.create_background_music()
        
        # Create sound effects
        self.create_sound_effects()
        
    def create_background_music(self):
        """Generate retro 80s synthwave style background music."""
        sample_rate = 44100
        duration = 8.0  # Longer loop for full melody
        n_samples = int(sample_rate * duration)
        
        # Create stereo buffer
        buffer = numpy.zeros((n_samples, 2), dtype=numpy.float64)
        max_amplitude = numpy.iinfo(numpy.int16).max * 0.15  # Keeping volume low
        
        # 80s style synth melody (A minor scale)
        main_melody = [
            440.00,  # A4
            493.88,  # B4
            523.25,  # C5
            587.33,  # D5
            659.25,  # E5
            587.33,  # D5
            523.25,  # C5
            493.88   # B4
        ]
        
        # Arpeggio notes (Am - F - C - G progression)
        arpeggio = [
            [440.00, 523.25, 659.25],  # Am
            [349.23, 440.00, 523.25],  # F
            [523.25, 659.25, 783.99],  # C
            [392.00, 493.88, 587.33]   # G
        ]
        
        # Duration settings
        melody_duration = duration / len(main_melody)
        samples_per_note = int(sample_rate * melody_duration)
        arp_samples = samples_per_note // 4  # Faster arpeggio
        
        # Generate main melody with saw wave
        for note_idx, freq in enumerate(main_melody):
            t = numpy.linspace(0, melody_duration, samples_per_note, False)
            start_idx = note_idx * samples_per_note
            end_idx = start_idx + samples_per_note
            
            # Create saw wave for main melody
            saw = 2 * (t * freq - numpy.floor(0.5 + t * freq))
            
            # Add subtle detuning for thickness
            detune = 1.003  # 3 cents sharp
            saw2 = 2 * (t * freq * detune - numpy.floor(0.5 + t * freq * detune))
            
            # Mix waves
            note = (saw + saw2) * 0.5
            
            # Add envelope
            envelope = numpy.ones_like(t)
            attack = int(samples_per_note * 0.1)
            decay = int(samples_per_note * 0.3)
            envelope[:attack] = numpy.linspace(0, 1, attack)
            envelope[-decay:] = numpy.linspace(1, 0, decay)
            
            note = note * envelope * 0.3  # Reduce melody volume
            
            # Add to both channels
            buffer[start_idx:end_idx, 0] += note
            buffer[start_idx:end_idx, 1] += note
        
        # Generate arpeggios
        for chord_idx, chord in enumerate(arpeggio):
            for note_idx, freq in enumerate(chord * 2):  # Repeat each chord
                t = numpy.linspace(0, melody_duration/8, arp_samples, False)
                start_idx = (chord_idx * samples_per_note) + (note_idx * arp_samples)
                end_idx = start_idx + arp_samples
                
                if end_idx <= n_samples:  # Ensure we don't exceed buffer
                    # Square wave for arpeggio
                    note = numpy.sign(numpy.sin(2 * numpy.pi * freq * t))
                    
                    # Quick envelope
                    envelope = numpy.exp(-3 * t)
                    note = note * envelope * 0.2  # Reduce arpeggio volume
                    
                    # Pan arpeggios slightly
                    pan_left = 0.7 if note_idx % 2 == 0 else 0.3
                    pan_right = 0.3 if note_idx % 2 == 0 else 0.7
                    buffer[start_idx:end_idx, 0] += note * pan_left
                    buffer[start_idx:end_idx, 1] += note * pan_right
        
        # Add bass line
        bass_freq = 110.00  # A2
        for i in range(0, n_samples, samples_per_note):
            t = numpy.linspace(0, melody_duration, samples_per_note, False)
            
            # Sine wave for bass
            bass = numpy.sin(2 * numpy.pi * bass_freq * t)
            
            # Bass envelope
            envelope = numpy.exp(-2 * (t / melody_duration))
            bass = bass * envelope * 0.4  # Reduce bass volume
            
            end_idx = min(i + samples_per_note, n_samples)
            buffer[i:end_idx, 0] += bass[:end_idx-i]
            buffer[i:end_idx, 1] += bass[:end_idx-i]
        
        # Normalize
        buffer = buffer / numpy.max(numpy.abs(buffer))
        
        # Add subtle reverb
        reverb_delay = int(sample_rate * 0.08)
        reverb = numpy.zeros_like(buffer)
        reverb[reverb_delay:] = buffer[:-reverb_delay] * 0.2
        buffer += reverb
        
        # Scale to int16 range
        buffer = numpy.clip(buffer * max_amplitude, -32768, 32767)
        
        # Convert to int16
        buffer = buffer.astype(numpy.int16)
        
        # Save as WAV file
        wavfile.write('assets/background_music.wav', sample_rate, buffer)
    
    def create_sound_effects(self):
        """Generate gentle sound effects using Pygame."""
        sample_rate = 44100
        max_amplitude = numpy.iinfo(numpy.int16).max * 0.2  # reduced volume
        
        # Hover sound - gentle rising tone
        duration = 0.15
        samples = int(sample_rate * duration)
        t = numpy.linspace(0, duration, samples, False)
        # Create a smooth transition from 300Hz to 400Hz
        freq = numpy.linspace(300, 400, samples)
        hover_tone = numpy.sin(2 * numpy.pi * freq * t) * max_amplitude
        # Apply fade in/out
        fade_in = numpy.linspace(0, 1, samples//3)
        sustain = numpy.ones(samples//3)
        fade_out = numpy.linspace(1, 0, samples - len(fade_in) - len(sustain))
        fade = numpy.concatenate([fade_in, sustain, fade_out])
        hover_tone *= fade
        hover_buffer = numpy.column_stack((hover_tone, hover_tone))
        wavfile.write('assets/hover.wav', sample_rate, hover_buffer.astype(numpy.int16))
        
        # Click sound - soft pop
        duration = 0.1
        samples = int(sample_rate * duration)
        t = numpy.linspace(0, duration, samples, False)
        # Create a gentle pop sound using frequency modulation
        freq = 600 * numpy.exp(-t * 20)  # exponentially decreasing frequency
        click_tone = numpy.sin(2 * numpy.pi * freq * t) * max_amplitude
        # Apply quick fade out
        fade = numpy.exp(-t * 10)
        click_tone *= fade
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
    global server_started
    if not server_started:
        try:
            server = LobbyServer()
            server_started = True
            server.start()
        except Exception as e:
            print(f"Error starting server: {e}")

def launch_client(single_player=False):
    try:
        if single_player:
            subprocess.Popen([sys.executable, 'single_player.py'])
        else:
            subprocess.Popen([sys.executable, 'client.py'])
    except Exception as e:
        print(f"Error launching client: {e}")

def create_buttons():
    """Create menu buttons."""
    buttons = [
        {'text': 'Single Player', 'color': (0, 255, 255)},  # Cyan
        {'text': 'Multiplayer', 'color': (255, 66, 161)},  # Pink
        {'text': 'Load Game', 'color': (57, 255, 20)},  # Green
        {'text': 'Exit', 'color': (255, 0, 77)}  # Red
    ]
    
    # Calculate button positions
    button_spacing = 20
    total_height = (button_height * len(buttons)) + (button_spacing * (len(buttons) - 1))
    start_y = (SCREEN_SIZE - total_height) // 2
    
    for i, button in enumerate(buttons):
        x = (SCREEN_SIZE - button_width) // 2
        y = start_y + (button_height + button_spacing) * i
        button['rect'] = pygame.Rect(x, y, button_width, button_height)
        button['hover_rect'] = None
    
    return buttons

def load_game_menu(screen):
    """Show load game menu with available saves."""
    saves = list_saves()
    if not saves:
        return None
    
    running = True
    font = pygame.font.Font(None, 36)
    saves_per_page = 5
    current_page = 0
    
    while running:
        screen.fill(BACKGROUND_COLOR)
        
        # Calculate page info
        total_pages = (len(saves) + saves_per_page - 1) // saves_per_page
        start_idx = current_page * saves_per_page
        end_idx = min(start_idx + saves_per_page, len(saves))
        current_saves = saves[start_idx:end_idx]
        
        # Draw title
        title = font.render('Load Game', True, (0, 231, 255))
        title_rect = title.get_rect(center=(SCREEN_SIZE/2, 50))
        screen.blit(title, title_rect)
        
        # Draw save entries
        for i, save in enumerate(current_saves):
            # Create save entry surface
            entry_height = 80
            entry_rect = pygame.Rect(100, 100 + i * (entry_height + 10), SCREEN_SIZE - 200, entry_height)
            pygame.draw.rect(screen, (60, 60, 70), entry_rect, border_radius=10)
            
            # Draw save info
            mode_color = (0, 255, 255) if save['mode'] == 'single_player' else (255, 66, 161)
            mode_text = font.render(f"Mode: {save['mode']}", True, mode_color)
            screen.blit(mode_text, (entry_rect.x + 20, entry_rect.y + 10))
            
            date_text = font.render(f"Date: {save['timestamp'][:19]}", True, (200, 200, 200))
            screen.blit(date_text, (entry_rect.x + 20, entry_rect.y + 40))
            
            # Highlight on hover
            mouse_pos = pygame.mouse.get_pos()
            if entry_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (80, 80, 90), entry_rect, 3, border_radius=10)
        
        # Draw navigation buttons if multiple pages
        if total_pages > 1:
            nav_y = SCREEN_SIZE - 80
            if current_page > 0:
                prev_btn = pygame.Rect(100, nav_y, 100, 40)
                pygame.draw.rect(screen, (60, 60, 70), prev_btn, border_radius=5)
                prev_text = font.render('Prev', True, (200, 200, 200))
                screen.blit(prev_text, prev_text.get_rect(center=prev_btn.center))
            
            if current_page < total_pages - 1:
                next_btn = pygame.Rect(SCREEN_SIZE - 200, nav_y, 100, 40)
                pygame.draw.rect(screen, (60, 60, 70), next_btn, border_radius=5)
                next_text = font.render('Next', True, (200, 200, 200))
                screen.blit(next_text, next_text.get_rect(center=next_btn.center))
            
            # Page indicator
            page_text = font.render(f'Page {current_page + 1}/{total_pages}', True, (200, 200, 200))
            screen.blit(page_text, page_text.get_rect(center=(SCREEN_SIZE/2, nav_y + 20)))
        
        # Draw back button
        back_btn = pygame.Rect(20, 20, 80, 40)
        pygame.draw.rect(screen, (60, 60, 70), back_btn, border_radius=5)
        back_text = font.render('Back', True, (200, 200, 200))
        screen.blit(back_text, back_text.get_rect(center=back_btn.center))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Check save entry clicks
                for i, save in enumerate(current_saves):
                    entry_rect = pygame.Rect(100, 100 + i * (entry_height + 10), SCREEN_SIZE - 200, entry_height)
                    if entry_rect.collidepoint(mouse_pos):
                        return save
                
                # Check navigation buttons
                if total_pages > 1:
                    if current_page > 0:
                        prev_btn = pygame.Rect(100, nav_y, 100, 40)
                        if prev_btn.collidepoint(mouse_pos):
                            current_page -= 1
                    
                    if current_page < total_pages - 1:
                        next_btn = pygame.Rect(SCREEN_SIZE - 200, nav_y, 100, 40)
                        if next_btn.collidepoint(mouse_pos):
                            current_page += 1
                
                # Check back button
                if back_btn.collidepoint(mouse_pos):
                    return None
        
        clock.tick(60)
    
    return None

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption('Snake Game')
    
    # Initialize sound manager
    sound_manager = SoundManager()
    
    # Create buttons
    buttons = create_buttons()
    button_hover_states = [False] * len(buttons)
    
    # Animation timing
    start_time = pygame.time.get_ticks()
    running = True
    
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
            
            # Check if mouse is over either the regular or hover rect
            is_hovered = (button['rect'].collidepoint(mouse_pos) or 
                         (button['hover_rect'] and button['hover_rect'].collidepoint(mouse_pos)))
            
            if is_hovered and not button_hover_states[i]:
                sound_manager.play_sound('hover')
                button_hover_states[i] = True
            elif not is_hovered:
                button_hover_states[i] = False
            
            if is_hovered:
                # Scale up button when hovered
                scaled_surface = pygame.transform.scale(
                    button['surface'],
                    (int(button_width * 1.1), int(button_height * 1.1))
                )
                scaled_rect = scaled_surface.get_rect(center=button['rect'].center)
                button['hover_rect'] = scaled_rect
                screen.blit(scaled_surface, scaled_rect)
            else:
                button['hover_rect'] = None
                screen.blit(button['surface'], button['rect'])
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if (button['rect'].collidepoint(mouse_pos) or 
                        (button['hover_rect'] and button['hover_rect'].collidepoint(mouse_pos))):
                        sound_manager.play_sound('click')
                        
                        if button['text'] == 'Single Player':
                            single_player.main()
                        elif button['text'] == 'Multiplayer':
                            snake_game.main()
                        elif button['text'] == 'Load Game':
                            save_data = load_game_menu(screen)
                            if save_data:
                                loaded_game = load_game(save_data['filepath'])
                                if loaded_game['mode'] == 'single_player':
                                    single_player.load_saved_game(loaded_game)
                                else:
                                    snake_game.load_saved_game(loaded_game)
                        elif button['text'] == 'Exit':
                            running = False
        
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main() 