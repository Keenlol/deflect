import pygame
from pygame.math import Vector2
from animation import Animation
from config import *
import math
import random
from projectile import *

class Knife(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.width = 180
        self.height = 180
        
        # Animation system
        animation_states = {
            "deflect": False
        }
        self.anim = Animation(self, "sprites/knife", animation_states, animation_speed=0.05)
        self.facing_right = True
        
        # Set initial image and rect
        self.image = self.anim.get_current_frame(self.facing_right)
        self.original_image = self.image
        self.rect = self.image.get_rect()
        
        # Positioning and hitbox
        self.position = Vector2(self.player.position)
        self.OFFSET = 50
        
        # Deflection attributes
        self.active = False
        self.angle = 0
        self.DEFLECTED_SPEED_MUL = 2
        # Add to game's sprite group
        # self.player.game.all_sprites.add(self)
    
    def update(self):
        """Update the knife's state and position"""
        if self.active:
            # Update animation
            self.anim.update()
            self.original_image = self.anim.get_current_frame(self.facing_right)
            
            # Calculate display angle (Pygame rotation is clockwise from up)
            display_angle = self.angle  # Convert our angle to Pygame's system
            if not self.facing_right:
                display_angle += 180

            # Rotate image
            self.image = pygame.transform.rotate(self.original_image, display_angle)
            self.rect = self.image.get_rect()
            
            # Check for bullet collisions when active
            self.check_projectile_collisions()
            
            # Check if animation is finished
            if self.anim.animation_finished:
                self.active = False
        else:
            # When inactive, use transparent surface
            self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Calculate offset using standard angle
        angle_rad = math.radians(self.angle)
        offset_vector = Vector2(
            math.cos(angle_rad) * self.OFFSET,
            -math.sin(angle_rad) * self.OFFSET  # Negative because pygame Y is down
        )

        self.position = self.player.position + offset_vector
        self.rect.center = self.position
    
    def activate(self, mouse_pos):
        """Activate the knife and set its position and rotation towards the mouse"""
        if not self.active:
            self.active = True
            self.anim.change_state("deflect")
            
            # Calculate direction to mouse
            to_mouse = Vector2(mouse_pos) - self.player.position
            
            # Calculate angle in [0,360] system
            # atan2 returns [-π,π], we convert to [0,2π] then to degrees
            self.angle = math.degrees(math.atan2(to_mouse.y, to_mouse.x))
            self.angle = (360 - self.angle) % 360  # Convert to clockwise and ensure [0,360]
            
            # Set facing direction based on angle
            self.facing_right = self.angle < 90 or self.angle > 270
            
            # Reset animation
            self.anim.animation_finished = False
            self.anim.current_frame = 0

    def check_projectile_collisions(self):
        """Check for collisions with bullets using circle hitbox"""
        if not self.active or self.anim.animation_finished:
            return
        
        # Get center point of knife for circle collision
        
        # Check all bullets
        for bullet in self.player.game.groups['bullets']:
            if not bullet.is_deflected:  # Only check non-deflected bullets
                distance = (bullet.position - self.position).length()
                if distance <= self.width/2:
                    self.deflect_bullet(bullet)
    
    def deflect_bullet(self, bullet):
        """Deflect a bullet in the direction the knife is facing"""
        self.player.game.freeze_and_shake(5, 5, 8)
        
        error_deg = 10
        if isinstance(bullet, Shard): error_deg = 45
        angle_rad = math.radians(self.angle + random.randrange(-error_deg, error_deg))

        bullet.is_deflected = True
        bullet.SPEED_RANGE[0] *= self.DEFLECTED_SPEED_MUL
        bullet.SPEED_RANGE[1] *= self.DEFLECTED_SPEED_MUL
        bullet.velocity = Vector2(math.cos(angle_rad), -math.sin(angle_rad)) * (bullet.velocity.length() * self.DEFLECTED_SPEED_MUL)
        bullet.draw()
