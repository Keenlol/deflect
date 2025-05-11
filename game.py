import pygame as pg
from config import Config as C
from player import Player
from enemy_all import *
from enemy1 import E1
from enemy2 import E2
from enemy3 import E3
from ui import HealthBar, Button, TextDisplay
from pygame.math import Vector2
import random
from timer import Timer
import sys
from stats import Stats
import tkinter as tk
from tkinter import ttk, font
import pandas as pd
from sounds import Sounds
from datetime import datetime, timedelta

class Game:
    # Game States
    STATE_MENU = 0
    STATE_PLAYING = 1
    STATE_GAMEOVER = 2
    STATE_PAUSED = 3
    STATE_STATISTICS = 4
    
    # Spawn rate configuration
    INITIAL_SPAWN_RANGE = (8.0, 10.0) # Seconds
    FINAL_SPAWN_RANGE = (2.0, 4.0) # Seconds
    DIFFICULTY_PEAK_TIME = 120 # Seconds
    
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
        pg.display.set_caption("Deflect")
        self.clock = pg.time.Clock()
        self.running = True
        
        # Load background images
        self.bg_game = pg.image.load("sprites/others/background.png").convert()
        self.bg_controls = pg.image.load("sprites/others/controls.png").convert()
        
        # Music : management
        self.current_music = None
        
        # Game state
        self.game_state = Game.STATE_MENU  # Start in menu state
        self.score = 0
        self.game_over = False
        self.game_over_timer = Timer(duration=1.5, owner=self)  # Increased delay
        self.freeze_timer = Timer(duration=0, owner=self)
        self.shake_timer = Timer(duration=0, owner=self)
        self.player_stats_timer = Timer(duration=5.0, owner=self, auto_reset=True)
        self.shake_intensity = 0
        self.camera_offset = Vector2(0, 0)
        
        # Stats tracking
        self.enemies_killed = 0
        self.elapsed_timer = Timer(duration=0, owner=self, mode=Timer.MODE_COUNTUP)
        self.elapsed_time = timedelta(seconds=0)
        
        # Enemy spawn system
        self.spawn_timer = Timer(duration=self.get_next_spawn_time(), owner=self)
        self.MIN_SPAWN_DISTANCE = 200  # Minimum distance from player for spawning enemies
        
        # Organized sprite groups
        self.groups = {
            'all': pg.sprite.Group(),
            'enemies': pg.sprite.Group(),
            'bullets': pg.sprite.Group(),
            'players': pg.sprite.Group(),
            'ui': pg.sprite.Group(),
            'menu': pg.sprite.Group(),
            'pause': pg.sprite.Group(),
            'gameover': pg.sprite.Group(),
            'sparks': pg.sprite.Group()
        }
        
        # Stats related attributes
        self.stats_button = None
        self.stats_data = {}
        
        self.setup_home_menu()
        self.play_menu_music()

    def add_score(self, score_add):
        self.score = round(self.score + score_add)

    def toggle_audio(self):
        """Toggle the audio volume between 0% and 100% in 10% increments"""
        sounds = Sounds()
        new_volume_percent = sounds.adjust_volume(0.1)
        
        # Update button text to show new volume
        # Find and update volume buttons in all menus
        for button in self.groups['menu'].sprites() + self.groups['pause'].sprites():
            if hasattr(button, 'is_volume_button') and button.is_volume_button:
                button.text = f"SFX : {new_volume_percent}%"
                button.render()
    
    def toggle_music_volume(self):
        """Toggle the music volume between 0% and 100% in 10% increments"""
        sounds = Sounds()
        new_volume_percent = sounds.adjust_music_volume(0.1)
        
        # Update button text to show new volume
        for button in self.groups['menu'].sprites() + self.groups['pause'].sprites():
            if hasattr(button, 'is_music_button') and button.is_music_button:
                button.text = f"Music : {new_volume_percent}%"
                button.render()
    
    def play_menu_music(self):
        """Play the menu music"""
        if self.current_music != "Spire":
            sounds = Sounds()
            sounds.play_music("Spire", loops=-1)  # Loop indefinitely
            self.current_music = "Spire"
    
    def play_game_music(self):
        """Play the gameplay music"""
        if self.current_music != "Clover":
            sounds = Sounds()
            sounds.play_music("Clover", loops=-1)  # Loop indefinitely
            self.current_music = "Clover"
    
    def stop_music(self):
        """Stop the currently playing music"""
        sounds = Sounds()
        sounds.stop_music()
        self.current_music = None

    def setup_home_menu(self):
        """Setup the home menu with buttons"""
        # Clear the menu group
        self.groups['menu'].empty()
        
        button_width = C.BUTTON_WIDTH
        button_height = C.BUTTON_HEIGHT
        button_spacing = C.BUTTON_SPACING
        left_margin = 150
        start_y = (C.WINDOW_HEIGHT - (button_height * 6 + button_spacing * 5)) // 2 + 80
        button_x = left_margin + button_width//2
        offset = button_height + button_spacing
        
        # BUTTONS
        # Play
        play_button = Button(
            position=Vector2(button_x, start_y),
            width=button_width,
            height=button_height,
            text="Play",
            callback=self.start_game,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['blue'],
            text_size=C.BUTTON_FONT_SIZE
        )
        
        # Statistics
        stats_button = Button(
            position=Vector2(button_x, start_y + offset),
            width=button_width,
            height=button_height,
            text="Statistics",
            callback=self.show_statistics,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['yellow'],
            text_size=C.BUTTON_FONT_SIZE
        )
        
        # SFX :
        current_volume = Sounds().get_volume_percent()
        audio_button = Button(
            position=Vector2(button_x, start_y + 2 * offset),
            width=button_width,
            height=button_height,
            text=f"SFX : {current_volume}%",
            callback=self.toggle_audio,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['green'],
            text_size=C.BUTTON_FONT_SIZE
        )
        audio_button.is_volume_button = True  # Add custom attribute to identify volume buttons
        
        # Music :
        current_music_volume = Sounds().get_music_percent()
        music_button = Button(
            position=Vector2(button_x, start_y + 3 * offset),
            width=button_width,
            height=button_height,
            text=f"Music : {current_music_volume}%",
            callback=self.toggle_music_volume,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['green'],
            text_size=C.BUTTON_FONT_SIZE
        )
        music_button.is_music_button = True  # Add custom attribute to identify music buttons
        
        # Clear Data
        clear_button = Button(
            position=Vector2(button_x, start_y + 4 * offset),
            width=button_width,
            height=button_height,
            text="Clear Data",
            callback=self.clear_all_stats,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['red'],
            text_size=C.BUTTON_FONT_SIZE
        )
        
        # Quit
        quit_button = Button(
            position=Vector2(button_x, start_y + 5 * offset),
            width=button_width,
            height=button_height,
            text="Quit",
            callback=self.quit_game,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['red'],
            text_size=C.BUTTON_FONT_SIZE
        )
        
        # Add buttons to menu group
        self.groups['menu'].add(play_button)
        self.groups['menu'].add(stats_button)
        self.groups['menu'].add(audio_button)
        self.groups['menu'].add(music_button)
        self.groups['menu'].add(clear_button)
        self.groups['menu'].add(quit_button)
        
        # Play menu music
        self.play_menu_music()

    def setup_pause_menu(self):
        """Setup the pause menu with buttons"""
        # Clear the pause menu group
        self.groups['pause'].empty()
        
        button_width = C.BUTTON_WIDTH
        button_height = C.BUTTON_HEIGHT
        button_spacing = C.BUTTON_SPACING
        start_y = (C.WINDOW_HEIGHT - (button_height * 6 + button_spacing * 5)) // 2 + 80
        offset = button_height + button_spacing
        
        # BUTTONS
        # Resume
        resume_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y),
            width=button_width,
            height=button_height,
            text="Resume",
            callback=self.resume_game,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['blue'],
            text_size=C.BUTTON_FONT_SIZE
        )
        
        # Retry
        retry_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + offset),
            width=button_width,
            height=button_height,
            text="Retry",
            callback=self.start_game,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['blue'],
            text_size=C.BUTTON_FONT_SIZE
        )
        
        # Statistics
        stats_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + 2 * offset),
            width=button_width,
            height=button_height,
            text="Statistics",
            callback=self.show_statistics,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['yellow'],
            text_size=C.BUTTON_FONT_SIZE
        )
        
        # SFX :
        current_volume = Sounds().get_volume_percent()
        audio_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + 3 * offset),
            width=button_width,
            height=button_height,
            text=f"SFX : {current_volume}%",
            callback=self.toggle_audio,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['green'],
            text_size=C.BUTTON_FONT_SIZE
        )
        audio_button.is_volume_button = True  # Add custom attribute to identify volume buttons
        
        # Music :
        current_music_volume = Sounds().get_music_percent()
        music_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + 4 * offset),
            width=button_width,
            height=button_height,
            text=f"Music : {current_music_volume}%",
            callback=self.toggle_music_volume,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['green'],
            text_size=C.BUTTON_FONT_SIZE
        )
        music_button.is_music_button = True  # Add custom attribute to identify music buttons
        
        # Menu
        menu_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + 5 * offset),
            width=button_width,
            height=button_height,
            text="Menu",
            callback=self.return_to_menu,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['red'],
            text_size=C.BUTTON_FONT_SIZE
        )
        
        # Add buttons to pause menu group
        self.groups['pause'].add(resume_button)
        self.groups['pause'].add(retry_button)
        self.groups['pause'].add(stats_button)
        self.groups['pause'].add(audio_button)
        self.groups['pause'].add(music_button)
        self.groups['pause'].add(menu_button)
    
    def setup_gameover_menu(self):
        """Setup the game over menu with buttons"""
        # Clear the game over menu group
        self.groups['gameover'].empty()
        
        # Define button dimensions
        button_width = C.BUTTON_WIDTH
        button_height = C.BUTTON_HEIGHT
        button_spacing = C.BUTTON_SPACING
        start_y = C.WINDOW_HEIGHT//2 + 80
        offset = button_height + button_spacing

        # BUTTONS
        # Retry
        retry_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y),
            width=button_width,
            height=button_height,
            text="Retry",
            callback=self.start_game,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['blue'],
            text_size=C.BUTTON_FONT_SIZE
        )
        
        # Statistics
        stats_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + offset),
            width=button_width,
            height=button_height,
            text="Statistics",
            callback=self.show_statistics,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['yellow'],
            text_size=C.BUTTON_FONT_SIZE
        )
        
        # Menu
        menu_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + 2*offset),
            width=button_width,
            height=button_height,
            text="Menu",
            callback=self.return_to_menu,
            idle_color=C.BUTTON_IDLE_COLOR,
            hover_color=C.BUTTON_HOVER_COLOR['red'],
            text_size=C.BUTTON_FONT_SIZE
        )
        
        # Add buttons to game over menu group
        self.groups['gameover'].add(retry_button)
        self.groups['gameover'].add(stats_button)
        self.groups['gameover'].add(menu_button)
    
    def toggle_pause(self):
        """Toggle between playing and paused states"""
        if self.game_state == Game.STATE_PLAYING:
            self.game_state = Game.STATE_PAUSED
            self.elapsed_timer.pause()
            self.setup_pause_menu()
            Sounds().pause_music()
        elif self.game_state == Game.STATE_PAUSED:
            self.game_state = Game.STATE_PLAYING
            self.elapsed_timer.resume()
            Sounds().unpause_music()
    
    def resume_game(self):
        """Resume the game from pause - callback for Resume button"""
        self.game_state = Game.STATE_PLAYING
        self.elapsed_timer.resume()
        Sounds().unpause_music()
    
    def return_to_menu(self):
        """Return to main menu - callback for Menu button"""
        self.game_state = Game.STATE_MENU
        self.setup_home_menu()
        self.play_menu_music()
    
    def start_game(self):
        """Start the game - callback for Play button"""
        self.game_state = Game.STATE_PLAYING
        self.setup_game()
        self.play_game_music()
    
    def show_statistics(self):
        """Prepare statistics data and schedule window creation for next frame"""
        # Find the statistics button to change its text
        stats_button = None
        button_groups = [self.groups['menu'], self.groups['pause'], self.groups['gameover']]
        
        for group in button_groups:
            for button in group:
                if isinstance(button, Button) and button.callback == self.show_statistics:
                    stats_button = button
                    break
            if stats_button:
                break
        
        self.stats_button = stats_button
        
        # Schedule stats window creation for next frame
        if self.game_state != Game.STATE_STATISTICS:
            self.previous_state = self.game_state
            self.game_state = Game.STATE_STATISTICS

            try:
                self.stats_data = Stats().preprocess_stats_data()
            except Exception as e:
                print(f"Error loading statistics data: {e}")
                self.game_state = self.previous_state
                return
        else:
            self.game_state = self.previous_state

    
    def render_stats_waiting_message(self):
        """Render a message that statistics are being opened in another window"""
        # Create dark background
        self.screen.fill(C.BACKGROUND_COLOR)
        
        # Load font
        try:
            font = pg.font.Font("fonts/Jua-Regular.ttf", 32)
        except:
            font = pg.font.Font(None, 32)
        
        # Create message text
        message = "Statistics are opened in another window"
        sub_message = "Close it to continue the game"
        
        text_surface = font.render(message, True, (255, 255, 255))
        sub_text_surface = font.render(sub_message, True, (200, 200, 200))
        
        # Position the text in the center of the screen
        text_rect = text_surface.get_rect(center=(C.WINDOW_WIDTH // 2, C.WINDOW_HEIGHT // 2 - 20))
        sub_text_rect = sub_text_surface.get_rect(center=(C.WINDOW_WIDTH // 2, C.WINDOW_HEIGHT // 2 + 20))
        
        # Draw the text
        self.screen.blit(text_surface, text_rect)
        self.screen.blit(sub_text_surface, sub_text_rect)

    def quit_game(self):
        """Quit the game - callback for Quit button"""
        self.running = False
    
    def setup_game(self):
        """Initialize or reset the game state"""
        # Reset game state
        self.score = 0
        self.game_over = False
        self.game_over_timer.reset()
        
        # Reset stats tracking
        self.enemies_killed = 0
        
        # Reset and start the elapsed timer
        self.elapsed_timer.reset()
        self.elapsed_timer.start()
        self.elapsed_time = timedelta(seconds=0)
        
        # Reset spawn timer
        self.spawn_timer.duration = self.get_next_spawn_time()
        self.spawn_timer.start()
        
        # Clear gameplay groups
        for group_name in ['all', 'enemies', 'bullets', 'players', 'ui', 'gameover']:
            self.groups[group_name].empty()
        
        # Create player
        self.player = Player(game=self, 
                             x=C.WINDOW_WIDTH // 2, 
                             y=C.WINDOW_HEIGHT - C.FLOOR_HEIGHT)
        
        self.groups['players'].add(self.player)
        self.groups['all'].add(self.player)
        self.groups['all'].add(self.player.knife)
        
        # Create UI elements
        self.setup_ui()
        
        # Spawn initial enemy
        self.spawn_enemy()
    
    def get_next_spawn_time(self):
        """Calculate spawn time based on elapsed game time"""
        # Calculate elapsed seconds from timer instead of datetime
        elapsed_seconds = self.elapsed_timer.elapsed
            
        # Calculate the difficulty progress (0 to 1)
        difficulty_progress = min(1.0, elapsed_seconds / self.DIFFICULTY_PEAK_TIME)
        
        # Interpolate between initial and final spawn times
        min_spawn = self.INITIAL_SPAWN_RANGE[0] - (self.INITIAL_SPAWN_RANGE[0] - self.FINAL_SPAWN_RANGE[0]) * difficulty_progress
        max_spawn = self.INITIAL_SPAWN_RANGE[1] - (self.INITIAL_SPAWN_RANGE[1] - self.FINAL_SPAWN_RANGE[1]) * difficulty_progress
        
        return random.uniform(min_spawn, max_spawn)
    
    def format_time(self, td):
        """Format timedelta to 'MM:SS' format"""
        total_seconds = int(td.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02}:{seconds:02}"
    
    def update_elapsed_time(self):
        """Update the elapsed time based on timer"""
        if not self.game_over:
            # Convert seconds to timedelta
            self.elapsed_time = timedelta(seconds=self.elapsed_timer.elapsed)

    def spawn_enemy(self):
        """Spawn an enemy at a valid position"""
        enemy_type = random.choice([1,2,3])  # 1 for E1, 2 for E2, 3 for E3
        spawn_pos = self.get_valid_spawn_position(enemy_type)

        if enemy_type == 1:
            enemy = E1(spawn_pos.x, spawn_pos.y, self)
        elif enemy_type == 2:
            enemy = E2(spawn_pos.x, spawn_pos.y, self)
        elif enemy_type == 3:
            enemy = E3(spawn_pos.x, spawn_pos.y, self)
            
        self.groups['enemies'].add(enemy)
        self.groups['all'].add(enemy)
    
    def handle_events(self):
        """Handle game events"""
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    # Toggle pause menu if playing or already paused
                    if self.game_state == Game.STATE_PLAYING or self.game_state == Game.STATE_PAUSED:
                        self.toggle_pause()
                elif self.game_state == Game.STATE_PLAYING:
                    if event.key == pg.K_SPACE:
                            self.player.space_pressed = True
                    elif event.key == pg.K_LSHIFT and not self.game_over:
                        self.player.shift_pressed = True
            elif event.type == pg.MOUSEBUTTONDOWN:
                if self.game_state == Game.STATE_PLAYING and not self.game_over:
                    if event.button == 1:  # Left click
                        self.player.mouse_clicked = True
    
    def freeze_and_shake(self, freeze_duration=3, shake_duration=7, shake_intensity=20):
        """Freeze the game and then apply camera shake
        
        Args:
            freeze_duration: Number of frames to freeze the game
            shake_duration: Number of frames to shake the camera
            shake_intensity: Maximum pixel offset for the shake
        """
        # Convert frames to seconds
        freeze_sec = freeze_duration / C.FPS
        shake_sec = shake_duration / C.FPS
        
        # Set freeze timer
        self.freeze_timer.duration = freeze_sec
        self.freeze_timer.start()
        
        # Set up shake timer
        self.shake_timer.duration = shake_sec
        self.shake_intensity = shake_intensity
    
    def update_camera_shake(self, dt):
        """Update the camera shake effect"""
        if not self.shake_timer.is_completed and not self.shake_timer.is_paused:
            # The shake gets weaker as the timer progresses
            remaining_ratio = 1.0 - self.shake_timer.progress
            self.camera_offset.x = random.uniform(-self.shake_intensity, self.shake_intensity) * remaining_ratio
            self.camera_offset.y = random.uniform(-self.shake_intensity, self.shake_intensity) * remaining_ratio
        else:
            # Reset camera offset when shake is complete
            self.camera_offset = Vector2(0, 0)

    def update(self):
        """Update game state"""
        dt = 1 / C.FPS
        
        # Update all timers
        Timer.update_all(dt)
        
        # Sparks effect play beyond freeze effect
        self.groups['sparks'].update()
        
        # Update based on game state
        if self.game_state == Game.STATE_MENU:
            self.groups['menu'].update()
            if self.current_music != "Spire":
                self.play_menu_music()
        elif self.game_state == Game.STATE_PAUSED:
            self.groups['pause'].update()
        elif self.game_state == Game.STATE_GAMEOVER:
            self.groups['gameover'].update()
        elif self.game_state == Game.STATE_STATISTICS:
            self.render_stats_waiting_message()
            pg.event.pump()  
            self.create_stats_window()
            return
        elif self.game_state == Game.STATE_PLAYING:
            if not self.game_over and self.current_music != "Clover":
                self.play_game_music()
                
            self.update_elapsed_time()
            
            if not self.freeze_timer.is_completed:
                self.draw()
                return
            
            if self.freeze_timer.just_completed:
                self.shake_timer.start()

            if self.spawn_timer.is_completed and not self.game_over:
                self.spawn_enemy()
                self.spawn_timer.duration = self.get_next_spawn_time()
                self.spawn_timer.start()
            
            self.update_camera_shake(dt)
            self.groups['all'].update()
            
            for enemy in self.groups['enemies']:
                enemy.update()
            
            self.groups['ui'].update()
            if self.player_stats_timer.just_completed:
                Stats().record('player_pos',
                               player_x=self.player.position.x,
                               player_y=self.player.position.y)

            # Check for game over
            if not self.game_over and self.player.health <= 0:
                self.game_over = True
                self.game_over_timer.start()
                self.elapsed_timer.pause()
                self.stop_music()
            
            # Game over timer complete - switch to game over state
            if self.game_over and self.game_over_timer.is_completed:
                self.game_state = Game.STATE_GAMEOVER
                self.setup_gameover_menu()
    
    def draw(self):
        """Draw the game screen"""
        self.screen.fill(C.BACKGROUND_COLOR)
        
        if self.game_state == Game.STATE_MENU:
            # Draw controls background
            self.screen.blit(self.bg_controls, (0, 0))
            
            # Draw menu background here if needed
            # For example, a title or artwork on the right side
            title_font = pg.font.Font("fonts/Coiny-Regular.ttf", C.TITLE_FONT_SIZE)
            if title_font is None:
                title_font = pg.font.Font(None, C.TITLE_FONT_SIZE)

            button_width = C.BUTTON_WIDTH
            left_margin = 150

            title_text = title_font.render("DEFLECT", True, (255, 255, 255))
            title_rect = title_text.get_rect(center=(left_margin + button_width//2, C.WINDOW_HEIGHT // 2 - 250))
            self.screen.blit(title_text, title_rect)
            
            # Draw menu buttons
            self.groups['menu'].draw(self.screen)
        
        elif self.game_state == Game.STATE_PLAYING or self.game_state == Game.STATE_GAMEOVER or self.game_state == Game.STATE_PAUSED:
            # Draw game background (with camera shake if active)
            if not self.shake_timer.is_completed:
                self.screen.blit(self.bg_game, (self.camera_offset.x, self.camera_offset.y))
            else:
                self.screen.blit(self.bg_game, (0, 0))
            
            # Save the original positions of all sprites
            original_positions = {}
            if not self.shake_timer.is_completed:
                for sprite in self.groups['all']:
                    if hasattr(sprite, 'rect') and hasattr(sprite, 'position'):
                        original_positions[sprite] = Vector2(sprite.rect.center)
                        # Apply camera shake offset to sprite's position
                        sprite.rect.center = (
                            sprite.rect.center[0] + self.camera_offset.x,
                            sprite.rect.center[1] + self.camera_offset.y
                        )
            
            # Draw all game sprites
            self.groups['all'].draw(self.screen)
            
            # Draw E2 weapons with camera shake
            for enemy in self.groups['enemies']:
                if isinstance(enemy, E2):
                    if not self.shake_timer.is_completed:
                        # Apply shake to weapon drawing
                        original_pos = enemy.position
                        enemy.position += self.camera_offset
                        enemy.draw_weapon(self.screen)
                        enemy.position = original_pos
                    else:
                        enemy.draw_weapon(self.screen)
            
            # Draw floor with camera shake
            floor_rect = (
                0 + int(self.camera_offset.x), 
                C.WINDOW_HEIGHT - C.FLOOR_HEIGHT + int(self.camera_offset.y), 
                C.WINDOW_WIDTH, 
                C.FLOOR_HEIGHT
            ) if not self.shake_timer.is_completed else (
                0, C.WINDOW_HEIGHT - C.FLOOR_HEIGHT, C.WINDOW_WIDTH, C.FLOOR_HEIGHT
            )
            pg.draw.rect(self.screen, C.FLOOR_COLOR, floor_rect)
            
            # Restore original positions
            if not self.shake_timer.is_completed:
                for sprite, pos in original_positions.items():
                    sprite.rect.center = (pos.x, pos.y)
            
            # Draw sparks with camera shake (always drawn even during freeze)
            # Save and apply shake to sparks if needed
            spark_positions = {}
            if not self.shake_timer.is_completed:
                for spark in self.groups['sparks']:
                    if hasattr(spark, 'rect') and hasattr(spark, 'position'):
                        spark_positions[spark] = Vector2(spark.rect.center)
                        # Apply camera shake offset to spark's position
                        spark.rect.center = (
                            spark.rect.center[0] + self.camera_offset.x,
                            spark.rect.center[1] + self.camera_offset.y
                        )
                        
            # Draw all sparks
            self.groups['sparks'].draw(self.screen)
            
            # Restore spark positions
            if not self.shake_timer.is_completed:
                for spark, pos in spark_positions.items():
                    spark.rect.center = (pos.x, pos.y)
            
            # Draw UI elements on top - UI doesn't shake to avoid disorienting the player
            self.groups['ui'].draw(self.screen)
            
            # Draw pause overlay and menu if paused
            if self.game_state == Game.STATE_PAUSED:
                # Create semi-transparent overlay
                overlay = pg.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
                overlay.fill(C.BACKGROUND_COLOR)
                overlay.set_alpha(200)
                self.screen.blit(overlay, (0, 0))
                
                # Draw "PAUSED" text
                pause_font = pg.font.Font("fonts/Coiny-Regular.ttf", C.TITLE_FONT_SIZE)
                if pause_font is None:
                    pause_font = pg.font.Font(None, C.TITLE_FONT_SIZE)
                
                pause_text = pause_font.render("PAUSED", True, (255, 255, 255))
                pause_rect = pause_text.get_rect(center=(C.WINDOW_WIDTH // 2, C.WINDOW_HEIGHT // 2 - 220))
                self.screen.blit(pause_text, pause_rect)
                
                # Draw pause menu buttons
                self.groups['pause'].draw(self.screen)
            
            # Draw game over screen
            if self.game_state == Game.STATE_GAMEOVER:
                # Create dark overlay
                overlay = pg.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
                overlay.fill(C.BACKGROUND_COLOR)
                overlay.set_alpha(200)
                self.screen.blit(overlay, (0, 0))
                
                # Draw game over text and stats
                title_font = pg.font.Font("fonts/Coiny-Regular.ttf", C.TITLE_FONT_SIZE)
                if title_font is None:
                    title_font = pg.font.Font(None, C.TITLE_FONT_SIZE)
                
                stats_font = pg.font.Font("fonts/Jua-Regular.ttf", 36)
                if stats_font is None:
                    stats_font = pg.font.Font(None, 36)
                
                score = self.score + (self.elapsed_time.seconds * 10)

                game_over_text = title_font.render('GAME OVER', True, (255, 255, 255))
                score_text = stats_font.render(f'SCORE  ----------  {score: <7}', True, (255, 255, 255))
                time_text = stats_font.render(f'  TIME  ----------  {self.format_time(self.elapsed_time): <6}', True, (255, 255, 255))
                kills_text = stats_font.render(f'KILLS  ----------  {self.enemies_killed: <8}', True, (255, 255, 255))
                
                # Position text
                text_y = C.WINDOW_HEIGHT // 2 - 220
                text_x = C.WINDOW_WIDTH // 2
                spacing = 50
                self.screen.blit(game_over_text, game_over_text.get_rect(center=(text_x, text_y)))
                self.screen.blit(score_text, score_text.get_rect(center=(text_x + 5, text_y + spacing*2)))
                self.screen.blit(time_text, time_text.get_rect(center=(text_x + 5, text_y + spacing*3)))
                self.screen.blit(kills_text, kills_text.get_rect(center=(text_x + 5, text_y + spacing*4)))
                
                # Draw game over menu buttons
                self.groups['gameover'].draw(self.screen)
        
        # Refresh display
        pg.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(C.FPS)
        
        pg.quit()
        sys.exit()

    def setup_ui(self):
        """Setup UI elements"""
        # Create health bar
        text_x = C.WINDOW_WIDTH//2 + 200
        spacing = 200
        text_y = C.WINDOW_HEIGHT - C.FLOOR_HEIGHT//2

        healthbar_pos = Vector2(350, text_y)  # Center position
        size = 0.3
        healthbar = HealthBar(healthbar_pos, 1000 * size, 300 * size, self.player)  # Adjust size as needed
        self.groups['ui'].add(healthbar)

        # Create score display
        score_display = TextDisplay(
            position=Vector2(text_x + spacing - 40, text_y),
            width=200,
            height=40,
            text_prefix="SCORE ",
            value_getter=lambda: str(self.score + (self.elapsed_time.seconds * 10)),
            font_path="fonts/Jua-Regular.ttf",
            font_size=32,
            color=(255, 255, 255)
        )
        self.groups['ui'].add(score_display)
        
        # Create time display
        time_display = TextDisplay(
            position=Vector2(text_x - spacing, text_y),
            width=200,
            height=40,
            text_prefix="TIME ",
            value_getter=lambda: self.format_time(self.elapsed_time),
            font_path="fonts/Jua-Regular.ttf",
            font_size=32,
            color=(255, 255, 255)
        )
        self.groups['ui'].add(time_display)
        
        # Create enemies killed display
        kills_display = TextDisplay(
            position=Vector2(text_x, text_y),
            width=200,
            height=40,
            text_prefix="KILLS ",
            value_getter=lambda: str(self.enemies_killed),
            font_path="fonts/Jua-Regular.ttf",
            font_size=32,
            color=(255, 255, 255)
        )
        self.groups['ui'].add(kills_display)

    def clear_all_stats(self):
        """Clear all statistics data"""
        stats = Stats()
        stats.clear_stats()
        for button in self.groups['menu']:
            if button.text == 'Clear Data':
                button.text = 'Cleared!'
                button.idle_color = (111, 118, 130)
                button.hover_color = (111, 118, 130)

    def get_valid_spawn_position(self, enemy_type=1):
        """Get random position for enemy spawn, away from player"""
        # E1
        if enemy_type == 1 or enemy_type == 3:
            y = random.randint(-200, C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - 100)

        # E2
        elif enemy_type == 2:
            y = C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - 50

        # Spawn outside canvas
        middle_offset = C.WINDOW_WIDTH/2 + 100
        if y <= -100:
            x = random.randint(-100, C.WINDOW_WIDTH + 100)
        else:
            x = int(C.WINDOW_WIDTH/2 + random.choice((-middle_offset, middle_offset)))

        return Vector2(x, y)

    def create_stats_window(self):
        """Create and show the statistics window"""
        # Define the callback for when the window is closed
        def on_stats_window_close():
            self.game_state = self.previous_state
        
        # Create and show the statistics window
        stats = Stats()
        stats.create_stats_window(on_close_callback=on_stats_window_close)

if __name__ == "__main__":
    game = Game()
    game.run()
