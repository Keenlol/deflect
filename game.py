import pygame as pg
from config import Config as C
from player import Player
from enemy_all import *
from enemy1 import E1
from enemy2 import E2
from enemy3 import E3
from ui import HealthBar, Button
from pygame.math import Vector2
import random
from timer import Timer
import sys
from stats import Stats
import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

class Game:
    # Game States
    STATE_MENU = 0
    STATE_PLAYING = 1
    STATE_GAMEOVER = 2
    STATE_PAUSED = 3  # New state for pause menu
    STATE_STATISTICS = 4  # New state for statistics window
    
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
        pg.display.set_caption("Deflect")
        self.clock = pg.time.Clock()
        self.running = True
        
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
            'menu': pg.sprite.Group(),  # Menu elements
            'pause': pg.sprite.Group(),  # Pause menu elements
            'gameover': pg.sprite.Group()  # Game over menu elements
        }
        
        # Stats related attributes
        self.stats_button = None
        self.stats_data = {}  # To hold processed statistical data
        self.pending_stats_window = False
        
        # Setup the home menu
        self.setup_home_menu()

    def setup_home_menu(self):
        """Setup the home menu with buttons"""
        # Clear the menu group
        self.groups['menu'].empty()
        
        # Define button dimensions
        button_width = 300
        button_height = 80
        button_spacing = 30
        left_margin = 150
        
        # Calculate starting Y position (center of screen)
        start_y = (C.WINDOW_HEIGHT - (button_height * 3 + button_spacing * 2)) // 2
        
        # Create Play button
        play_button = Button(
            position=Vector2(left_margin + button_width//2, start_y + button_height//2),
            width=button_width,
            height=button_height,
            text="Play",
            callback=self.start_game,
            idle_color=(207, 218, 227),
            hover_color=(94, 175, 255),
            text_size=64
        )
        
        # Create Statistics button
        stats_button = Button(
            position=Vector2(left_margin + button_width//2, start_y + button_height + button_spacing + button_height//2),
            width=button_width,
            height=button_height,
            text="Statistics",
            callback=self.show_statistics,
            idle_color=(207, 218, 227),
            hover_color=(255, 205, 120),
            text_size=64
        )
        
        # Create Quit button
        quit_button = Button(
            position=Vector2(left_margin + button_width//2, start_y + 2 * (button_height + button_spacing) + button_height//2),
            width=button_width,
            height=button_height,
            text="Quit",
            callback=self.quit_game,
            idle_color=(207, 218, 227),
            hover_color=(224, 79, 74),
            text_size=64
        )
        
        # Add buttons to menu group
        self.groups['menu'].add(play_button)
        self.groups['menu'].add(stats_button)
        self.groups['menu'].add(quit_button)
    
    def setup_pause_menu(self):
        """Setup the pause menu with buttons"""
        # Clear the pause menu group
        self.groups['pause'].empty()
        
        # Define button dimensions
        button_width = 300
        button_height = 70
        button_spacing = 20
        
        # Calculate starting Y position (center of screen)
        start_y = (C.WINDOW_HEIGHT - (button_height * 4 + button_spacing * 3)) // 2
        
        # Create Resume button
        resume_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + button_height//2),
            width=button_width,
            height=button_height,
            text="Resume",
            callback=self.resume_game,
            idle_color=(207, 218, 227),
            hover_color=(94, 175, 255),
            text_size=56
        )
        
        # Create Retry button
        retry_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + button_height + button_spacing + button_height//2),
            width=button_width,
            height=button_height,
            text="Retry",
            callback=self.retry_game,
            idle_color=(207, 218, 227),
            hover_color=(94, 175, 255),
            text_size=56
        )
        
        # Create Statistics button
        stats_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + 2*(button_height + button_spacing) + button_height//2),
            width=button_width,
            height=button_height,
            text="Statistics",
            callback=self.show_statistics,
            idle_color=(207, 218, 227),
            hover_color=(255, 205, 120),
            text_size=56
        )
        
        # Create Menu button
        menu_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + 3*(button_height + button_spacing) + button_height//2),
            width=button_width,
            height=button_height,
            text="Menu",
            callback=self.return_to_menu,
            idle_color=(207, 218, 227),
            hover_color=(224, 79, 74),
            text_size=56
        )
        
        # Add buttons to pause menu group
        self.groups['pause'].add(resume_button)
        self.groups['pause'].add(retry_button)
        self.groups['pause'].add(stats_button)
        self.groups['pause'].add(menu_button)
    
    def setup_gameover_menu(self):
        """Setup the game over menu with buttons"""
        # Clear the game over menu group
        self.groups['gameover'].empty()
        
        # Define button dimensions
        button_width = 300
        button_height = 70
        button_spacing = 20
        
        # Calculate starting Y position for buttons (below score text)
        start_y = C.WINDOW_HEIGHT//2 + 30
        
        # Create Retry button
        retry_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y),
            width=button_width,
            height=button_height,
            text="Retry",
            callback=self.retry_game,
            idle_color=(207, 218, 227),
            hover_color=(94, 175, 255),
            text_size=56
        )
        
        # Create Statistics button
        stats_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + button_height + button_spacing),
            width=button_width,
            height=button_height,
            text="Statistics",
            callback=self.show_statistics,
            idle_color=(207, 218, 227),
            hover_color=(255, 205, 120),
            text_size=56
        )
        
        # Create Menu button
        menu_button = Button(
            position=Vector2(C.WINDOW_WIDTH//2, start_y + 2*(button_height + button_spacing)),
            width=button_width,
            height=button_height,
            text="Menu",
            callback=self.return_to_menu,
            idle_color=(207, 218, 227),
            hover_color=(224, 79, 74),
            text_size=56
        )
        
        # Add buttons to game over menu group
        self.groups['gameover'].add(retry_button)
        self.groups['gameover'].add(stats_button)
        self.groups['gameover'].add(menu_button)
    
    def toggle_pause(self):
        """Toggle between playing and paused states"""
        if self.game_state == Game.STATE_PLAYING:
            self.game_state = Game.STATE_PAUSED
            self.setup_pause_menu()
        elif self.game_state == Game.STATE_PAUSED:
            self.game_state = Game.STATE_PLAYING
    
    def resume_game(self):
        """Resume the game from pause - callback for Resume button"""
        self.game_state = Game.STATE_PLAYING
    
    def retry_game(self):
        """Restart the current game - callback for Retry button"""
        self.game_state = Game.STATE_PLAYING
        self.setup_game()
    
    def return_to_menu(self):
        """Return to main menu - callback for Menu button"""
        self.game_state = Game.STATE_MENU
        self.setup_home_menu()
    
    def start_game(self):
        """Start the game - callback for Play button"""
        self.game_state = Game.STATE_PLAYING
        self.setup_game()
    
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
            
            # Change button text to "X"
            if self.stats_button:
                self.stats_button.text = "X"
            
            # Pre-load data to avoid lag
            try:
                self.preload_stats_data()
            except Exception as e:
                print(f"Error loading statistics data: {e}")
                self.game_state = self.previous_state
                return
        else:
            # If already in stats mode, exit it
            self.game_state = self.previous_state
            
            # Reset button text
            if self.stats_button:
                self.stats_button.text = "Statistics"
    
    def preload_stats_data(self):
        """Pre-process all statistics data to avoid lag when creating charts"""
        stats = Stats()
        self.stats_data = {}
        
        # Process dodge attack data
        dodge_data = stats.get_stats('dodged_attack')
        if dodge_data:
            df = pd.DataFrame(dodge_data)
            df['damage_evaded'] = pd.to_numeric(df['damage_evaded'])
            self.stats_data['dodge'] = {
                'min': df['damage_evaded'].min(),
                'max': df['damage_evaded'].max(),
                'avg': df['damage_evaded'].mean(),
                'std': df['damage_evaded'].std()
            }
        
        # Process player position data
        pos_data = stats.get_stats('player_pos')
        if pos_data:
            df = pd.DataFrame(pos_data)
            df['player_x'] = pd.to_numeric(df['player_x'])
            df['player_y'] = pd.to_numeric(df['player_y'])
            self.stats_data['position'] = df
        
        # Process damage income data
        dmg_data = stats.get_stats('dmg_income')
        if dmg_data:
            df = pd.DataFrame(dmg_data)
            df['damage'] = pd.to_numeric(df['damage'])
            damage_by_attack = df.groupby('attack_name')['damage'].sum().reset_index()
            damage_by_attack = damage_by_attack.sort_values('damage', ascending=False)
            
            # Limit to top categories
            if len(damage_by_attack) > 8:
                other_damage = damage_by_attack.iloc[8:]['damage'].sum()
                top_attacks = damage_by_attack.iloc[:8]
                # Create a new row for "Other"
                other_row = pd.DataFrame([{'attack_name': 'Other', 'damage': other_damage}])
                top_attacks = pd.concat([top_attacks, other_row], ignore_index=True)
            else:
                top_attacks = damage_by_attack
                
            self.stats_data['damage_income'] = top_attacks
        
        # Process enemy lifespan data
        lifespan_data = stats.get_stats('enemy_lifespan')
        if lifespan_data:
            df = pd.DataFrame(lifespan_data)
            df['lifespan_sec'] = pd.to_numeric(df['lifespan_sec'])
            self.stats_data['enemy_lifespan'] = df
        
        # Process damage deflected data
        deflect_data = stats.get_stats('dmg_deflected')
        if deflect_data:
            df = pd.DataFrame(deflect_data)
            df['total_damage_dealt'] = pd.to_numeric(df['total_damage_dealt'])
            self.stats_data['deflected'] = df
    
    def create_stats_window(self):
        """Create and show the statistics window using the preloaded data"""
        import matplotlib
        matplotlib.use('Agg')  # Use Agg backend to avoid threading issues
        
        # Create the root window
        root = tk.Tk()
        root.title("Game Statistics")
        root.geometry("400x400")
        root.resizable(True, True)
        root.configure(background='black')  # Set dark background
        
        # Configure ttk style for dark theme
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background='black', borderwidth=0)
        style.configure('TNotebook.Tab', background='black', foreground='white', padding=[10, 2])
        style.map('TNotebook.Tab', background=[('selected', '#333333')])
        style.configure('TFrame', background='black')
        style.configure('TLabel', background='black', foreground='white')
        
        # Set the window close event to restore the game state
        def on_window_close():
            if self.stats_button:
                self.stats_button.text = "Statistics"
            self.game_state = self.previous_state
            root.destroy()
            
        root.protocol("WM_DELETE_WINDOW", on_window_close)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Add tabs based on available data
        if 'dodge' in self.stats_data:
            Stats().create_dodge_stats_tab(notebook, self.stats_data['dodge'])
            
        if 'position' in self.stats_data:
            Stats().create_player_position_tab(notebook, self.stats_data['position'])
            
        if 'damage_income' in self.stats_data:
            Stats().create_damage_income_tab(notebook, self.stats_data['damage_income'])
            
        if 'enemy_lifespan' in self.stats_data:
            Stats().create_enemy_lifespan_tab(notebook, self.stats_data['enemy_lifespan'])
            
        if 'deflected' in self.stats_data:
            Stats().create_damage_deflected_tab(notebook, self.stats_data['deflected'])
        
        # Run the Tkinter main loop
        root.mainloop()

    def quit_game(self):
        """Quit the game - callback for Quit button"""
        self.running = False
    
    def setup_game(self):
        """Initialize or reset the game state"""
        # Reset game state
        self.score = 0
        self.game_over = False
        self.game_over_timer.reset()
        
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
        """Get random time for next enemy spawn"""
        return random.uniform(3.0, 4.0)  # 10-20 seconds at 60 FPS
    
    def get_valid_spawn_position(self, enemy_type=1):
        """Get random position for enemy spawn, away from player"""
        # Spawning logic for E1 (floating enemy)
        if enemy_type == 1 or enemy_type == 3:
            y = random.randint(-200, C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - 100)

        # Spawning logic for E2 (ground enemy)
        elif enemy_type == 2:
            y = C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - 50

        middle_offset = C.WINDOW_WIDTH/2 + 100
        if y <= -100:
            x = random.randint(-100, C.WINDOW_WIDTH + 100)
        else:
            x = int(C.WINDOW_WIDTH/2 + random.choice((-middle_offset, middle_offset)))

        return Vector2(x, y)
    
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
    
    def add_score(self, amount):
        """Add to the player's score"""
        self.score += amount
    
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
                        if self.game_over:
                            self.setup_game()  # Reset game on space when game over
                        else:
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
        # Shake timer will start after freeze ends
    
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
        
        # Update based on game state
        if self.game_state == Game.STATE_MENU:
            self.groups['menu'].update()
        elif self.game_state == Game.STATE_PAUSED:
            self.groups['pause'].update()
        elif self.game_state == Game.STATE_GAMEOVER:
            self.groups['gameover'].update()
        elif self.game_state == Game.STATE_STATISTICS:
            # Exit pygame event loop temporarily to show tkinter window
            pg.event.pump()  # Process any pending events
            self.create_stats_window()  # This will block until the window is closed
        elif self.game_state == Game.STATE_PLAYING:
            # freeze effect
            if not self.freeze_timer.is_completed:
                return
            
            # Start shake after freeze ends
            if self.freeze_timer.just_completed:
                self.shake_timer.start()

            # Enemy spawn timer
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
            
            # Game over timer complete - switch to game over state
            if self.game_over and self.game_over_timer.is_completed:
                self.game_state = Game.STATE_GAMEOVER
                self.setup_gameover_menu()
            elif not self.game_over:
                # Only update score if game is not over
                self.score += 1  # Score for surviving
    
    def draw(self):
        """Draw the game screen"""
        self.screen.fill(C.BLACK)
        
        if self.game_state == Game.STATE_MENU:
            # Draw menu background here if needed
            # For example, a title or artwork on the right side
            title_font = pg.font.Font("fonts/Jua-Regular.ttf", 80)
            if title_font is None:
                title_font = pg.font.Font(None, 80)
            
            title_text = title_font.render("DEFLECT", True, (255, 255, 255))
            title_rect = title_text.get_rect(center=(C.WINDOW_WIDTH - 350, 200))
            self.screen.blit(title_text, title_rect)
            
            # Draw menu buttons
            self.groups['menu'].draw(self.screen)
        
        elif self.game_state == Game.STATE_PLAYING or self.game_state == Game.STATE_GAMEOVER or self.game_state == Game.STATE_PAUSED:
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
            pg.draw.rect(self.screen, C.GRAY, floor_rect)
            
            # Restore original positions
            if not self.shake_timer.is_completed:
                for sprite, pos in original_positions.items():
                    sprite.rect.center = (pos.x, pos.y)
            
            # Draw UI elements on top - UI doesn't shake to avoid disorienting the player
            self.groups['ui'].draw(self.screen)
            
            # Draw pause overlay and menu if paused
            if self.game_state == Game.STATE_PAUSED:
                # Create semi-transparent overlay
                overlay = pg.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
                overlay.fill((0, 0, 0))
                overlay.set_alpha(150)  # Semi-transparent
                self.screen.blit(overlay, (0, 0))
                
                # Draw "PAUSED" text
                pause_font = pg.font.Font("fonts/Jua-Regular.ttf", 90)
                if pause_font is None:
                    pause_font = pg.font.Font(None, 90)
                
                pause_text = pause_font.render("PAUSED", True, (255, 255, 255))
                pause_rect = pause_text.get_rect(center=(C.WINDOW_WIDTH // 2, 100))
                self.screen.blit(pause_text, pause_rect)
                
                # Draw pause menu buttons
                self.groups['pause'].draw(self.screen)
            
            # Draw game over screen
            if self.game_state == Game.STATE_GAMEOVER:
                # Create dark overlay
                overlay = pg.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
                overlay.fill((0, 0, 0))
                overlay.set_alpha(160)  # 60% transparency
                self.screen.blit(overlay, (0, 0))
                
                # Draw game over text and score
                font = pg.font.Font("fonts/Jua-Regular.ttf", 74)
                if font is None:
                    font = pg.font.Font(None, 74)
                
                game_over_text = font.render('Game Over', True, (255, 255, 255))
                score_text = font.render(f'Score: {self.score}', True, (255, 255, 255))
                
                # Position text
                text_y = C.WINDOW_HEIGHT // 2 - 150
                self.screen.blit(game_over_text, game_over_text.get_rect(center=(C.WINDOW_WIDTH // 2, text_y)))
                text_y += 80
                self.screen.blit(score_text, score_text.get_rect(center=(C.WINDOW_WIDTH // 2, text_y)))
                
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
        healthbar_pos = Vector2(170, 50)  # Center position
        size = 0.3
        healthbar = HealthBar(healthbar_pos, 1000 * size, 300 * size, self.player)  # Adjust size as needed
        self.groups['ui'].add(healthbar)

if __name__ == "__main__":
    game = Game()
    game.run()
