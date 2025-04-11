import pygame
from pygame.math import Vector2
from config import Config as C
import math
import random

class Projectile(pygame.sprite.Sprite):
    def __init__(self, position:Vector2, velocity=0.0, 
                 speed_multiplier=0.0, speed_range=(0, math.inf), 
                 gravity=0 ,damage=10, radius=10, surfacesize=10, deflected=False):
        super().__init__()
        # Basic attributes
        self.position = position
        self.velocity = Vector2(velocity)
        self.damage = damage
        self.DEFLECTED_VELOCITY = self.velocity * 1.1
        self.SPEED_RANGE = speed_range
        self.is_deflected = deflected

        # Physics attributes
        self.GRAVITY = gravity
        self.SPEED_MULTIPLIER = speed_multiplier
        
        # State
        self.alive = True

        # Draw
        self.surface_size = surfacesize
        self.radius = radius
        self.image = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(self.position.x, self.position.y))

    def check_bounds(self):
        """Check if projectile is out of bounds or hit ground"""
        # Check if out of screen bounds
        if (self.position.x < -100 or 
            self.position.x > C.WINDOW_WIDTH + 100 or
            self.position.y < -100 or
            self.position.y > C.WINDOW_HEIGHT + 100):
            self.kill()
            return True
            
        # Check if hit ground
        if self.position.y >= C.WINDOW_HEIGHT - C.FLOOR_HEIGHT:
            self.kill()
            return True
            
        return False
    
    def draw(self):
        """Draw projectile, override by child class"""
        pass

    def apply_physics(self):
        self.velocity *= self.SPEED_MULTIPLIER
        self.velocity.y += self.GRAVITY
        self.position += self.velocity
        self.rect.center = self.position

        if self.velocity.length() != 0:
            self.velocity.clamp_magnitude_ip(self.SPEED_RANGE[0], self.SPEED_RANGE[1])


    def update(self):
        """Update projectile position and check bounds"""
        if not self.alive:
            return

        # if round(self.velocity.length(), 1) == 0:
        #     self.kill()

        self.apply_physics()
        self.check_bounds()
        self.draw()


class P_Ball(Projectile):
    def __init__(self, position, velocity, speed_multiplier, damage):

        # Stretch and squash parameters
        self.STRETCH_THRESHOLD = 8  # Speed at which stretching begins
        self.MAX_STRETCH_RATIO = 2.5  # Maximum stretching ratio
        self.MIN_SQUASH_RATIO = 0.85  # Minimum squashing ratio
        radius = 10

        super().__init__(position, velocity, speed_multiplier, [6, 30], 0, damage, 
                         radius=radius, surfacesize=int(radius * 2 * self.MAX_STRETCH_RATIO))
        self.color = (255, 0, 0)  # Default red color
    
        
        self.draw()
    
    def draw(self):
        """Draw the ball with current color, stretching based on velocity"""
        # Clear the surface
        self.image.fill((0, 0, 0, 0))
        center = (self.surface_size // 2, self.surface_size // 2)
        speed = self.velocity.length()
        
        if speed > self.STRETCH_THRESHOLD and speed > 0.1:
            stretch_factor = min(1.0 + (speed - self.STRETCH_THRESHOLD) / 10.0,
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
    
    def update(self):
        """Update projectile position and check bounds"""
        super().update()

    

class Shard(Projectile):
    def __init__(self, position, velocity, damage, deflected=False):
        self.base = random.randint(20, 30)
        self.height = random.randint(20, 45)

        super().__init__(position, velocity, 1.0, [0, 30], 0, damage, 
                         radius=(self.base + self.height) / 4, 
                         surfacesize=int(max(self.base, self.height) * 2),
                         deflected=deflected)
        
        # Rotation attributes
        self.angle = random.uniform(0, 360)
        self.NORMAL_SPIN = 3
        self.DEFLECTED_SPIN = random.uniform(10, 15)
        self.spin_speed = self.NORMAL_SPIN

        self.draw()
    
    def draw(self):
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
        
        # points = [(int(x), int(y)) for x, y in points]
        color = (0, 0, 255) if self.is_deflected else (255, 0, 0)
        shard_surface = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)

        pygame.draw.polygon(self.image, color, points)
        rotated_surface = pygame.transform.rotate(shard_surface, -angle_rad)
        rotated_rect = rotated_surface.get_rect(center=center)
        self.image.blit(rotated_surface, rotated_rect)
    
    def update(self):
        # Update rotation
        self.angle += self.spin_speed
        
        # Apply gravity only if deflected
        if self.is_deflected and self.GRAVITY == 0:
            self.GRAVITY = random.uniform(0.2,0.5)
            self.spin_speed = self.DEFLECTED_SPIN
        
        # Update position
        super().update()
