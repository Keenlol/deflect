import pygame
from pygame.math import Vector2
from config import Config as C
import math
import random
from datetime import datetime
from sounds import Sounds

class Projectile(pygame.sprite.Sprite):
    def __init__(self, 
                 position=Vector2(0, 0),        # Starting position
                 velocity=Vector2(0, 0),        # Initial velocity vector
                 game=None,                     # Game reference
                 damage=10,                     # Damage dealt
                 radius=10,                     # Collision radius 
                 speed_multiplier=1.0,          # Speed change per frame
                 speed_range=(0, math.inf),     # Min/max speed
                 gravity=0,                     # Gravity effect
                 surfacesize=None,              # Size of surface for drawing
                 deflected=False,
                 attack_name=''):              # Whether this is deflected
        super().__init__()
        
        self.__tag = {'attack_name': attack_name,
                      'deflect_timestamp': None,
                      'deflect_id': None,
                      'damage_recorded': False,
                      'dodge_counted_by': None}

        # Basic attributes
        self.position = position
        self.velocity = velocity
        self.damage = damage
        self.radius = radius
        self.DEFLECTED_VELOCITY = self.velocity * 1.1
        self.SPEED_RANGE = speed_range
        self.is_deflected = deflected
        self.COLOR_SET = {'red': (230, 49, 49), 'blue': (0, 100, 255)}
        self.color = self.COLOR_SET['blue'] if self.is_deflected else self.COLOR_SET['red']
        self.game = game

        # Physics attributes
        self.GRAVITY = gravity
        self.SPEED_MULTIPLIER = speed_multiplier
        
        # State
        self.alive = True

        # Draw
        self.surface_size = surfacesize if surfacesize is not None else radius * 2
        self.image = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(self.position.x, self.position.y))

        # Add to game groups if game is provided
        if self.game:
            self.game.groups['bullets'].add(self)
            self.game.groups['all'].add(self)


    @property
    def is_deflected(self):
        return self.__is_deflected
    
    @is_deflected.setter
    def is_deflected(self, value):
        self.__is_deflected = value
        if value:
            self.__tag['deflect_timestamp'] = datetime.now()
        self.deflect_action()

    @property
    def attack_name(self):
        return self.__tag['attack_name']

    @property
    def deflect_id(self):
        return self.__tag['deflect_id']
    
    @deflect_id.setter
    def deflect_id(self, value):
        self.__tag['deflect_id'] = value
    
    @property
    def damage_recorded(self):
        return self.__tag['damage_recorded']
    
    @damage_recorded.setter
    def damage_recorded(self, value:bool):
        self.__tag['damage_recorded'] = value

    @property
    def dodge_counted_by(self):
        return self.__tag['dodge_counted_by']
    
    @dodge_counted_by.setter
    def dodge_counted_by(self, value):
        self.__tag['dodge_counted_by'] = value

    @property
    def speed(self):
        return self.velocity.length()

    def deflect_action(self):
        """ Do something when deflected, in case extra actions are needed"""
        pass

    def check_bounds(self):
        """Check if projectile is out of screen bounds or has hit the ground"""
        # Check if projectile is out of screen bounds
        if (self.position.x < -100 or 
            self.position.x > C.WINDOW_WIDTH + 100 or 
            self.position.y > C.WINDOW_HEIGHT + 100):
            return True
            
        # Check if projectile has hit the ground
        if self.position.y + self.radius/2 > C.WINDOW_HEIGHT - C.FLOOR_HEIGHT + 100:
            return True
            
        return False
    
    def draw(self):
        """Draw projectile, override by child class"""
        self.color = self.COLOR_SET['blue'] if self.is_deflected else self.COLOR_SET['red']

    def apply_physics(self):
        """Apply physics to projectile"""
        self.velocity *= self.SPEED_MULTIPLIER
        self.velocity.y += self.GRAVITY
        self.position += self.velocity
        self.rect.center = self.position

        if self.speed != 0:
            self.velocity.clamp_magnitude_ip(self.SPEED_RANGE[0], self.SPEED_RANGE[1])

    def update(self):
        """Update projectile position and check bounds"""
        if not self.alive:
            return

        # if round(self.velocity.length(), 1) == 0:
        #     self.kill()

        self.apply_physics()
        if self.check_bounds():
            self.kill()
        self.draw()


class P_Ball(Projectile):
    def __init__(self, 
                 position=Vector2(0, 0),
                 velocity=Vector2(0, 0),
                 game=None,
                 damage=33,
                 radius=10,
                 speed_multiplier=1.0,
                 deflected=False,
                 attack_name=''):
        
        self.STRETCH_THRESHOLD = 8
        self.MAX_STRETCH_RATIO = 2.5
        self.MIN_SQUASH_RATIO = 0.85

        surfacesize = int(radius * 2 * self.MAX_STRETCH_RATIO)
        
        super().__init__(
            position=position,
            velocity=velocity,
            game=game,
            damage=damage,
            radius=radius,
            speed_multiplier=speed_multiplier,
            speed_range=[6, 30],
            gravity=0,
            surfacesize=surfacesize,
            deflected=deflected,
            attack_name=attack_name
        )
        
        self.draw()
    
    def draw(self):
        """Draw the ball with current color, stretching based on velocity"""
        # Call parent draw for color updates
        super().draw()

        # Clear the surface
        self.image.fill((0, 0, 0, 0))
        center = (self.surface_size // 2, self.surface_size // 2)
        
        if self.speed > self.STRETCH_THRESHOLD and self.speed > 0.1:
            stretch_factor = min(1.0 + (self.speed - self.STRETCH_THRESHOLD) / 10.0,
                                 self.MAX_STRETCH_RATIO)
            squash_factor = max(1.0 / stretch_factor,
                                self.MIN_SQUASH_RATIO)
            
            angle_rad = math.atan2(self.velocity.y, self.velocity.x)
            angle_deg = math.degrees(angle_rad)
            
            a = self.radius * stretch_factor
            b = self.radius * squash_factor

            ellipse_surface = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)
            ellipse_rect = pygame.Rect(
                center[0] - a,
                center[1] - b,
                a * 2,
                b * 2
            )
            
            pygame.draw.ellipse(ellipse_surface, self.color, ellipse_rect)
            rotated_surface = pygame.transform.rotate(ellipse_surface, -angle_deg)
            rotated_rect = rotated_surface.get_rect(center=center)
            self.image.blit(rotated_surface, rotated_rect)
        else:
            pygame.draw.circle(self.image, self.color, center, self.radius)


class Shard(Projectile):
    def __init__(self, 
                 position=Vector2(0, 0),
                 velocity=Vector2(0, 0),
                 game=None,
                 damage=33,
                 gravity=0,
                 deflected=False,
                 attack_name=''):
        
        # Shard-specific attributes
        self.base = random.randint(20, 30)
        self.height = random.randint(20, 45)
        radius = (self.base + self.height) / 4
        surfacesize = int(max(self.base, self.height) * 2)

        # Call parent constructor with calculated parameters
        super().__init__(
            position=position, 
            velocity=velocity, 
            game=game,
            damage=damage,
            radius=radius,
            speed_multiplier=1.0, 
            speed_range=[0, 30],
            gravity=gravity,
            surfacesize=surfacesize,
            deflected=deflected,
            attack_name=attack_name
        )
        
        # Rotation attributes
        self.angle = random.uniform(0, 360)
        self.NORMAL_SPIN = 3
        self.DEFLECTED_SPIN = random.uniform(10, 15)
        self.spin_speed = self.NORMAL_SPIN

        # Spawn animation attributes
        self.spawn_animation = True
        self.spawn_scale = 2.0  # Start 80% larger
        self.scale_decrease_rate = 0.07  # How fast it returns to normal size
        self.min_scale = 1.0  # Normal size
        
        # Save original base and height values
        self.original_base = self.base
        self.original_height = self.height
        
        # Apply initial scale
        self._apply_scale()
        
        self.draw()
    
    def _apply_scale(self):
        """Apply the current scale to base and height"""
        self.base = self.original_base * self.spawn_scale
        self.height = self.original_height * self.spawn_scale
        # Update radius based on new dimensions
        self.radius = (self.base + self.height) / 4
    
    def draw(self):
        """Draw the shard as a triangle"""
        super().draw()

        self.image.fill((0, 0, 0, 0))
        center = (self.surface_size/2, self.surface_size/2)
        angle_rad = math.radians(self.angle)
        
        points = [
            (center[0] + math.sin(angle_rad) * self.height/2,
             center[1] - math.cos(angle_rad) * self.height/2),
            (center[0] - math.cos(angle_rad) * self.base/2,
             center[1] - math.sin(angle_rad) * self.base/2),
            (center[0] + math.cos(angle_rad) * self.base/2,
             center[1] + math.sin(angle_rad) * self.base/2)
        ]
        
        shard_surface = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, self.color, points)
        rotated_surface = pygame.transform.rotate(shard_surface, -angle_rad)
        rotated_rect = rotated_surface.get_rect(center=center)
        self.image.blit(rotated_surface, rotated_rect)
    
    def update(self):
        """Update shard position, rotation, and check bounds"""
        # Update rotation
        self.angle += self.spin_speed
        
        # Apply gravity only if deflected
        if self.is_deflected and self.GRAVITY == 0:
            self.GRAVITY = random.uniform(0.2, 0.5)
            self.spin_speed = self.DEFLECTED_SPIN
        
        # Update spawn animation
        if self.spawn_animation:
            self.spawn_scale -= self.scale_decrease_rate
            if self.spawn_scale <= self.min_scale:
                self.spawn_scale = self.min_scale
                self.spawn_animation = False
            self._apply_scale()

        super().update()

class Laser(Projectile):
    def __init__(self, 
                 position=Vector2(0, 0),
                 velocity=Vector2(0, 0),
                 game=None,
                 damage=33,
                 radius=10,
                 speed_multiplier=1.0,
                 bounce_limit=0,
                 deflected=False,
                 laser_type='normal',
                 target=None,
                 turn_rate=0.0,
                 bomb_info={},
                 attack_name=''):
        
        # Laser-specific attributes
        self.STRETCH_THRESHOLD = 5
        self.bounces = bounce_limit + 1
        self.target = target
        self.laser_type = laser_type
        self.turn_rate = turn_rate
        self.bomb_info = bomb_info
        
        # Calculate surface size based on laser length
        surfacesize = int(radius * 20)
        
        # Call parent constructor with laser-specific parameters
        super().__init__(
            position=position, 
            velocity=velocity,
            game=game, 
            damage=damage,
            radius=radius, 
            speed_multiplier=speed_multiplier,
            speed_range=[0, math.inf],
            gravity=0,
            surfacesize=surfacesize,
            deflected=deflected,
            attack_name=attack_name
        )
        
        # Set up the surface for drawing
        self.draw()
    
    def draw(self):
        """Draw the laser as a rectangle that stretches based on velocity"""
        super().draw()
        
        # Clear the surface
        self.image.fill((0, 0, 0, 0))
        center = (self.surface_size // 2, self.surface_size // 2)
        
        # Stretch and squash based on velocity
        stretch_factor = (self.speed / self.STRETCH_THRESHOLD)
        
        angle_rad = math.atan2(self.velocity.y, self.velocity.x)
        angle_deg = math.degrees(angle_rad)
        
        a = self.radius * stretch_factor
        b = self.radius
        
        # Create a rectangle surface
        rect_surface = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)
        rect = pygame.Rect(
            center[0] - a,
            center[1] - b,
            a * 2,
            b * 2
        )
        
        # Draw the rectangle
        pygame.draw.rect(rect_surface, self.color, rect)
        
        # Rotate the rectangle
        rotated_surface = pygame.transform.rotate(rect_surface, -angle_deg)
        rotated_rect = rotated_surface.get_rect(center=center)
        self.image.blit(rotated_surface, rotated_rect)
    
    def check_bounds(self):
        """Check if projectile is out of bounds and handle bouncing if enabled"""
        if self.bounces > 0:
            bounces = self.position.x <= 0 or self.position.x >= C.WINDOW_WIDTH or self.position.y <= 0 or self.position.y >= C.WINDOW_HEIGHT - C.FLOOR_HEIGHT
            if self.attack_name == 'Gunman Bouncing-Laser' and bounces:
                Sounds().play_sound_random(['e3_bounce1', 'e3_bounce2'])
            # Bounce off left edge
            if self.position.x <= 0:
                self.position.x = 0
                self.velocity.x = abs(self.velocity.x)  # Bounce right
                self.bounces -= 1

            # Bounce off right edge
            elif self.position.x >= C.WINDOW_WIDTH:
                self.position.x = C.WINDOW_WIDTH
                self.velocity.x = -abs(self.velocity.x)  # Bounce left
                self.bounces -= 1
                
            # Bounce off top edge
            elif self.position.y <= 0:
                self.position.y = 0
                self.velocity.y = abs(self.velocity.y)  # Bounce down
                self.bounces -= 1
                
            # Bounce off ground
            elif self.position.y >= C.WINDOW_HEIGHT - C.FLOOR_HEIGHT:
                self.position.y = C.WINDOW_HEIGHT - C.FLOOR_HEIGHT
                self.velocity.y = -abs(self.velocity.y)  # Bounce up
                self.bounces -= 1
                
            # Check if max bounces reached
            if self.bounces <= 0:
                return True
                
        return False

    def deflect_action(self):
        """Retarget homing laser when deflected"""
        if self.laser_type == 'homing' and self.is_deflected and self.game:
            enemies = [sprite for sprite in self.game.groups['enemies'] 
                      if sprite.alive]
            if enemies:
                self.target = random.choice(enemies)

    def update_homing_laser(self):
        """Update homing laser to track its target"""
        if not self.target or not self.target.alive:
            return
            
        # Calculate angle to target
        to_target = self.target.position - self.position
        target_angle = math.degrees(math.atan2(to_target.y, to_target.x))
        current_angle = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
        
        # Calculate angle difference and clamp to turn rate
        angle_diff = (target_angle - current_angle + 180) % 360 - 180
        turn_amount = max(-self.turn_rate, min(self.turn_rate, angle_diff))
        
        # Update velocity direction
        new_angle = math.radians(current_angle + turn_amount)
        self.velocity = Vector2(math.cos(new_angle), math.sin(new_angle)) * self.speed

    def explodes(self):
        """Create explosion effect for bomb-type lasers"""
        # Create explosion lasers in all directions
        b_info = self.bomb_info

        for i in range(b_info['explosion_count']):
            angle = (360 / b_info['explosion_count']) * i
            rad_angle = math.radians(angle)
            explosion_dir = Vector2(math.cos(rad_angle), math.sin(rad_angle))
            
            Laser(position=Vector2(self.position),
                velocity=explosion_dir * b_info['explosion_speed'],
                game=self.game,
                damage=b_info['explosion_damage'],
                radius=b_info['explosion_size'],
                speed_multiplier=b_info['explosion_speed_mul'],
                deflected=self.is_deflected,
                attack_name=self.attack_name)
        
    def update(self):
        """Update laser position, special behaviors, and check bounds"""
        if self.laser_type == 'homing':
            self.update_homing_laser()
            
        super().update()
        
        if self.velocity.length() <= 1:
            self.kill()

    def kill(self) -> None:
        """Handle special effects when laser is destroyed"""
        if self.laser_type == 'bomb':
            self.explodes()
            Sounds().play_sound('e3_explode')
        return super().kill()        
