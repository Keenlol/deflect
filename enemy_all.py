import pygame
import os
from pygame.math import Vector2
from config import Config as C
from projectile import *
from animation import Animation

import random
import math
import copy

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, game, anim={"path":"", "loops": {}, "speed": 0.2}, 
                 width=100, height=100, maxhp=100, movespeed=3, 
                 gravity=0.8, maxfallspeed=15, hurtduration = 10, bodydamage = 30):
        super().__init__()
        # Size attributes (can be overridden by child classes)
        self.width = width
        self.height = height
        self.anim = Animation(self, anim['path'], anim['loops'], anim['speed'])
        self.facing_right = True
        
        # Physics attributes
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)
        self.on_ground = False
        
        # Combat attributes
        self.MAX_HEALTH = maxhp
        self.health = self.MAX_HEALTH
        self.is_hurt = False
        self.HURT_DURATION = hurtduration
        self.hurt_timer = 0
        self.BODY_DAMAGE = bodydamage
        self.attack_timer = 0
        self.is_attacking = False
        
        # Movement attributes
        self.MOVE_SPEED = movespeed
        self.GRAVITY = gravity
        self.MAX_FALL_SPEED = maxfallspeed
        
        # State attributes
        self.is_alive = True
        
        # Game reference
        self.game = game
        self.target = game.player

        # Knockback
        self.knockback_velocity = Vector2(0, 0)
        self.is_knocked_back = False
        self.KNOCKBACK_DECAY = 0.95

        self.image = self.anim.get_current_frame(self.facing_right)
        self.rect = pygame.Rect(x, y, self.width, self.height)  
    
    @staticmethod
    def get_random(value_range:tuple):
        if isinstance(value_range[0], int):
            return random.randint(value_range[0], value_range[1])
        return value_range[0] + random.random() * (value_range[1] - value_range[0])

    def update_animation(self):
        """Update the current animation frame"""
        self.anim.update()
        self.image = self.anim.get_current_frame(self.facing_right)

    def take_damage(self, amount):
        """Handle enemy taking damage"""
        self.health -= amount
        self.game.freeze_and_shake(0, 3, 5)
        if self.is_alive:
            if self.health <= 0:
                self.health = 0
                self.is_alive = False
                self.anim.change_state("death")
            else:
                self.is_hurt = True
                self.hurt_timer = self.HURT_DURATION
                self.anim.change_state("hurt")
        
    def attack(self, target):
        """Base attack method to be overridden by child classes"""
        pass
    
    def ai_logic(self, target):
        """Base movement method to be overridden by child classes"""
        pass
    
    def apply_physics(self):
        """Apply basic physics"""
        # Apply gravity
        if not self.on_ground:
            self.velocity.y += self.GRAVITY
            self.velocity.y = min(self.velocity.y, self.MAX_FALL_SPEED)
        
        # Update position
        self.position += self.velocity
        
        # Floor collision
        if self.position.y + self.height/2 > C.WINDOW_HEIGHT - C.FLOOR_HEIGHT:
            self.position.y = C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - self.height/2
            self.velocity.y = 0
            self.on_ground = True
        else:
            self.on_ground = False
        
        # Update rect position
        self.rect.center = self.position
    
    def check_projectile_collisions(self):
        """Check for collisions with deflected bullets"""
        for bullet in self.game.groups['bullets']:
            if bullet.is_deflected:  # Only check deflected bullets
                distance = (bullet.position - self.position).length()
                if distance < self.width/2:  # Using sprite width as collision radius
                    self.take_damage(bullet.damage)
                    self.start_knockback(bullet.velocity, bullet.velocity.length() * 0.1)
                    bullet.kill()

    def start_knockback(self, direction, amount):
        """Start a knockback effect on the enemy
        
        Args:
            direction: Vector2 indicating the knockback direction (doesn't need to be normalized)
            amount: The knockback force amount
        """

        # Calculate knockback vector
        if direction.length() > 0:  # Avoid division by zero
            direction = direction.normalize()
        else:
            direction = Vector2(1, 0)  # Default direction if none provided
        
        # Set knockback velocity
        self.knockback_velocity = direction * amount
        self.is_knocked_back = True
    
    def update_knockback(self):
        """Update the knockback effect"""
        if hasattr(self, 'is_knocked_back') and self.is_knocked_back:
            # Apply knockback velocity to position
            self.position += self.knockback_velocity
            
            # Apply decay to knockback velocity
            self.knockback_velocity *= self.KNOCKBACK_DECAY
            
            # If knockback velocity becomes negligible, end knockback
            if self.knockback_velocity.length() < 0.1:
                self.knockback_velocity = Vector2(0, 0)
                self.is_knocked_back = False
        
    def update(self, target=None):
        """Update enemy state"""
        if not self.is_alive:
            self.update_animation()
            if self.anim.current_state == "death" and self.anim.animation_finished:
                self.kill()
            return
            
        # Handle hurt state
        if self.is_hurt:
            self.hurt_timer -= 1
            if self.hurt_timer <= 0:
                self.is_hurt = False
        
        if target and not self.is_hurt:  # Only ai_logic/attack if not hurt
            self.ai_logic(target)
        
        # Update knockback before applying regular physics
        self.update_knockback()
        self.apply_physics()
        self.update_animation()
        self.check_projectile_collisions()

    def kill(self):
        """Override kill method to add score"""
        if hasattr(self, 'game') and self.is_alive:
            self.game.add_score(100)  # Add score for killing enemy
        super().kill()

