import pygame as pg
from config import Config as C
from player import Player
from enemy_all import *
from enemy1 import E1
from enemy2 import E2
from enemy3 import E3
from ui import HealthBar
from pygame.math import Vector2
import random
from timer import Timer

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
        pg.display.set_caption("Deflect")
        self.clock = pg.time.Clock()
        self.running = True
        
        # Game state
        self.score = 0
        self.game_over = False
        self.game_over_timer = Timer(duration=1.0, owner=self)
        self.freeze_timer = Timer(duration=0, owner=self)
        self.shake_timer = Timer(duration=0, owner=self)
        self.shake_intensity = 0
        self.camera_offset = Vector2(0, 0)
        
        # Enemy spawn system
        self.spawn_timer = Timer(duration=self.get_next_spawn_time(), owner=self)
        self.MIN_SPAWN_DISTANCE = 200  # Minimum distance from player for spawning enemies
        
        self.setup_game()

    def setup_game(self):
        """Initialize or reset the game state"""
        # Reset game state
        self.score = 0
        self.game_over = False
        self.game_over_timer.reset()
        
        # Reset spawn timer
        self.spawn_timer.duration = self.get_next_spawn_time()
        self.spawn_timer.start()
        
        # Organized sprite groups
        self.groups = {
            'all': pg.sprite.Group(),
            'enemies': pg.sprite.Group(),
            'bullets': pg.sprite.Group(),
            'players': pg.sprite.Group(),
            'ui': pg.sprite.Group()
        }
        
        # Clear all groups
        for group in self.groups.values():
            group.empty()
        
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
        return random.uniform(3.0, 10.0)  # 10-20 seconds at 60 FPS
    
    def get_valid_spawn_position(self, enemy_type=1):
        """Get random position for enemy spawn, away from player"""
        # Spawning logic for E1 (floating enemy)
        if enemy_type == 1 or enemy_type == 3:
            while True:
                x = random.randint(100, C.WINDOW_WIDTH - 100)
                y = random.randint(100, C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - 100)
                spawn_pos = Vector2(x, y)
                
                # Check distance from player
                if (spawn_pos - self.player.position).length() >= self.MIN_SPAWN_DISTANCE:
                    return spawn_pos
        
        # Spawning logic for E2 (ground enemy)
        elif enemy_type == 2:
            spawn_right = random.choice([True, False])
            
            if spawn_right:
                x = self.player.position.x + random.randint(250, 600)
                x = max(100, x)
            else:
                x = self.player.position.x - random.randint(250, 600)
                x = min(C.WINDOW_WIDTH - 100, x)
            
            # E2 always spawns on the ground
            y = C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - 50  # 50 pixels above the floor
            
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
                if event.key == pg.K_SPACE:
                    if self.game_over:
                        self.setup_game()  # Reset game on space when game over
                    else:
                        self.player.space_pressed = True
                elif event.key == pg.K_LSHIFT and not self.game_over:
                    self.player.shift_pressed = True
            elif event.type == pg.MOUSEBUTTONDOWN and not self.game_over:
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
        if not self.shake_timer.is_complete and not self.shake_timer.is_paused:
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
        
        # Handle freeze effect
        if not self.freeze_timer.is_complete:
            return
        
        # Start shake after freeze ends
        if self.freeze_timer.just_completed:
            self.shake_timer.start()

        # Handle enemy spawn timer
        if self.spawn_timer.just_completed and not self.game_over:
            self.spawn_enemy()
            self.spawn_timer.duration = self.get_next_spawn_time()
            self.spawn_timer.start()
        
        self.update_camera_shake(dt)
        self.groups['all'].update()
        
        for enemy in self.groups['enemies']:
            enemy.update(self.player)
        
        self.groups['ui'].update()
        
        # Check for game over
        if not self.game_over and self.player.health <= 0:
            self.game_over = True
            self.game_over_timer.start()
        
        # Handle game over timer
        if self.game_over:
            # Game over state is handled by the timer
            pass
        else:
            # Only update score if game is not over
            self.score += 1  # Score for surviving
    
    def draw(self):
        """Draw the game screen"""
        self.screen.fill(C.BLACK)
        
        # Save the original positions of all sprites
        original_positions = {}
        if not self.shake_timer.is_complete:
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
                if not self.shake_timer.is_complete:
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
        ) if not self.shake_timer.is_complete else (
            0, C.WINDOW_HEIGHT - C.FLOOR_HEIGHT, C.WINDOW_WIDTH, C.FLOOR_HEIGHT
        )
        pg.draw.rect(self.screen, C.GRAY, floor_rect)
        
        # Restore original positions
        if not self.shake_timer.is_complete:
            for sprite, pos in original_positions.items():
                sprite.rect.center = (pos.x, pos.y)
        
        # Draw UI elements on top - UI doesn't shake to avoid disorienting the player
        self.groups['ui'].draw(self.screen)
        
        # Draw game over screen
        if self.game_over and self.game_over_timer.is_complete:
            # Create dark overlay
            overlay = pg.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(128)  # 50% transparency
            self.screen.blit(overlay, (0, 0))
            
            # Draw game over text and score
            font = pg.font.Font(None, 74)
            game_over_text = font.render('Game Over', True, (255, 255, 255))
            score_text = font.render(f'Score: {self.score}', True, (255, 255, 255))
            restart_text = font.render('Press SPACE to restart', True, (255, 255, 255))
            
            # Position text
            text_y = C.WINDOW_HEIGHT // 2 - 100
            for text in [game_over_text, score_text, restart_text]:
                text_rect = text.get_rect(center=(C.WINDOW_WIDTH // 2, text_y))
                self.screen.blit(text, text_rect)
                text_y += 80
        
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

    def setup_ui(self):
        """Setup UI elements"""
        # Create health bar
        healthbar_pos = Vector2(20, 20)  # Top-left corner with some padding
        size = 0.3
        healthbar = HealthBar(healthbar_pos, 1000 * size, 300 * size, self.player)  # Adjust size as needed
        self.groups['ui'].add(healthbar)

if __name__ == "__main__":
    game = Game()
    game.run()
