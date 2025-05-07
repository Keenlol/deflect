import pygame
from pygame.math import Vector2
from animation import Animation
from config import *
import math
import random
from projectile import *
import uuid
from stats import Stats
from datetime import datetime
from sounds import Sounds

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
        self.current_deflect_id = None
        
        # Deflection damage tracking
        self.deflection_damage = {}
        self.DEFLECTION_FINALIZE_DELAY = 5.0
    
    def update(self):
        """Update the knife's state and position"""
        if self.active:
            self.anim.update()
            self.original_image = self.anim.get_current_frame(self.facing_right)
            
            # Calculate display angle (Pygame rotation is clockwise from up)
            display_angle = self.angle
            if not self.facing_right:
                display_angle += 180

            # Rotate image
            self.image = pygame.transform.rotate(self.original_image, display_angle)
            self.rect = self.image.get_rect()
            
            self.check_projectile_collisions()
            
            if self.anim.animation_finished:
                self.active = False
                self.current_deflect_id = None
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
        
        self.check_completed_deflections()
    
    def check_completed_deflections(self):
        """Check for deflections that have been completed and need their total damage recorded."""
        keys_to_remove = []
        current_time = datetime.now()
        
        for deflect_id, data in self.deflection_damage.items():
            # Skip current active deflection
            if deflect_id == self.current_deflect_id:
                continue
            time_elapsed = current_time - data["timestamp"]
            
            # If sufficient time has passed and this deflection has hits that haven't been recorded yet
            if time_elapsed.total_seconds() >= self.DEFLECTION_FINALIZE_DELAY and not data["recorded"]:
                if data["hit_count"] > 0:
                    # Record the combined damage for this deflection batch
                    Stats().record('dmg_deflected', total_damage_dealt=data["total_damage_dealt"])
                
                # Mark as recorded either way, and ready for removal
                data["recorded"] = True
                keys_to_remove.append(deflect_id)
            
            # If it's been a very long time, clean it up regardless
            elif time_elapsed.total_seconds() >= self.DEFLECTION_FINALIZE_DELAY * 2:
                keys_to_remove.append(deflect_id)
        
        # Clean up completed deflections
        for key in keys_to_remove:
            del self.deflection_damage[key]

    def activate(self, mouse_pos):
        """Activate the knife and set its position and rotation towards the mouse"""
        if not self.active:
            self.active = True
            self.anim.change_state("deflect")
            
            self.current_deflect_id = str(uuid.uuid4())
            self.deflection_damage[self.current_deflect_id] = {
                "total_damage_dealt": 0,
                "hit_count": 0,
                "recorded": False,
                "timestamp": datetime.now()
            }
            
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

        # Set the deflect_id on the bullet to track which deflection batch it belongs to
        bullet._Projectile__tag['deflect_id'] = self.current_deflect_id
        bullet._Projectile__tag['damage_recorded'] = False

        bullet.is_deflected = True
        bullet.SPEED_RANGE[0] *= self.DEFLECTED_SPEED_MUL
        bullet.SPEED_RANGE[1] *= self.DEFLECTED_SPEED_MUL
        bullet.velocity = Vector2(math.cos(angle_rad), -math.sin(angle_rad)) * (bullet.velocity.length() * self.DEFLECTED_SPEED_MUL)
        bullet.draw()
        Sounds().play_sound_random(['deflect1', 'deflect2', 'deflect3'])
    
    def record_deflected_damage(self, deflect_id, damage):
        """Record damage done by deflected projectiles in the same batch"""
        if deflect_id in self.deflection_damage:
            self.deflection_damage[deflect_id]["total_damage_dealt"] += damage
            self.deflection_damage[deflect_id]["hit_count"] += 1
