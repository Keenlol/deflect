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
        self.game_over_timer = 0
        self.GAME_OVER_DELAY = 60  # 1 second at 60 FPS
        
        # Freeze effect attributes
        self.freeze_active = False
        self.freeze_duration = 0
        self.freeze_timer = 0
        
        # Camera shake effect attributes
        self.shake_duration = 0
        self.shake_timer = 0
        self.shake_intensity = 0
        self.camera_offset = Vector2(0, 0)
        
        # Enemy spawn system
        self.spawn_timer = 0
        self.next_spawn_time = self.get_next_spawn_time()
        self.MIN_SPAWN_DISTANCE = 200
        
        self.setup_game()

    def setup_game(self):
        """Initialize or reset the game state"""
        # Reset game state
        self.score = 0
        self.game_over = False
        self.game_over_timer = 0
        self.spawn_timer = 0
        self.next_spawn_time = self.get_next_spawn_time()
        
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
        return random.randint(200, 600)  # 10-20 seconds at 60 FPS
    
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
        enemy_type = random.choice([1,2,3])  # 1 for E1, 2 for E2
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
        # self.freeze_active = True
        self.freeze_timer = freeze_duration
        
        # Set up shake to start after freeze ends
        self.shake_duration = shake_duration
        self.shake_intensity = shake_intensity
        self.shake_timer = 0  # Will be set to shake_duration when freeze ends
    
    def update_camera_shake(self):
        """Update the camera shake effect"""
        if self.shake_timer > 0:
            self.shake_timer -= 1
            # The shake gets weaker as the timer runs down
            remaining_intensity = self.shake_intensity * (self.shake_timer / self.shake_duration)
            self.camera_offset.x = random.uniform(-remaining_intensity, remaining_intensity)
            self.camera_offset.y = random.uniform(-remaining_intensity, remaining_intensity)

    def update(self):
        """Update game state"""
        # Handle freeze effect
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            if self.freeze_timer <= 0:
                self.shake_timer = self.shake_duration
            return

        self.update_camera_shake()
        self.groups['all'].update()
        
        for enemy in self.groups['enemies']:
            enemy.update(self.player)
        
        self.groups['ui'].update()
        
        # Check for game over
        if not self.game_over and self.player.health <= 0:
            self.game_over = True
            self.game_over_timer = self.GAME_OVER_DELAY
        
        # Handle game over timer
        if self.game_over:
            if self.game_over_timer > 0:
                self.game_over_timer -= 1
        else:
            # Only update score and spawn enemies if game is not over
            self.score += 1  # Score for surviving
            
            # Enemy spawn system
            self.spawn_timer += 1
            if self.spawn_timer >= self.next_spawn_time:
                self.spawn_enemy()
                self.spawn_timer = 0
                self.next_spawn_time = self.get_next_spawn_time()
            
    
    def draw(self):
        """Draw the game screen"""
        self.screen.fill(C.BLACK)
        
        # Save the original positions of all sprites
        original_positions = {}
        if self.shake_timer > 0:
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
                if self.shake_timer > 0:
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
        ) if self.shake_timer > 0 else (
            0, C.WINDOW_HEIGHT - C.FLOOR_HEIGHT, C.WINDOW_WIDTH, C.FLOOR_HEIGHT
        )
        pg.draw.rect(self.screen, C.GRAY, floor_rect)
        
        # Restore original positions
        if self.shake_timer > 0:
            for sprite, pos in original_positions.items():
                sprite.rect.center = (pos.x, pos.y)
        
        # Draw UI elements on top - UI doesn't shake to avoid disorienting the player
        self.groups['ui'].draw(self.screen)
        
        # Draw game over screen
        if self.game_over and self.game_over_timer <= 0:
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
