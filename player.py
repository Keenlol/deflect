import pygame
import os
from pygame.math import Vector2
from config import Config as C
from animation import Animation
from knife import Knife
import math

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Size attributes
        self.width = 100
        self.height = 100
        
        # Animation system
        animation_states = {
            "idle": True,
            "run": True,
            "jump": False,
            "fall": True,
            "dodge": False,
            "deflect": False,
            "hurt": False,  # Hurt animation is non-looping
            "dead": False   # Death animation is non-looping
        }
        self.anim = Animation(self, "sprites/player", animation_states, animation_speed=0.15)
        self.facing_right = True
        
        # Physics attributes
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)
        self.acceleration = Vector2(0, 0)
        self.on_ground = False
        
        # Input states
        self.space_pressed = False
        self.shift_pressed = False
        self.mouse_clicked = False  # New input state for mouse click
        
        # Knife
        self.knife = Knife(self)
        
        # Movement constants
        self.GRAVITY = 0.8
        self.JUMP_FORCE = -15
        self.MAX_HORIZONTAL_SPEED = 8
        self.MAX_FALL_SPEED = 15
        self.ACCELERATION = 2
        self.DECELERATION = 8
        self.AIR_RESISTANCE = 1
        self.GROUND_FRICTION = 0.5
        
        # Dodge attributes
        self.DODGE_SPEED = 25
        self.DODGE_DURATION = 8
        self.dodge_timer = 0
        self.is_dodging = False
        self.can_dodge = True
        self.DODGE_COOLDOWN = 20
        self.dodge_cooldown_timer = 0
        
        # Double jump attributes
        self.can_double_jump = True
        self.DOUBLE_JUMP_FORCE = -12
        
        # Deflect attributes
        self.DEFLECT_COOLDOWN = 25
        self.deflect_cooldown_timer = 0
        self.can_deflect = True
        self.is_deflecting = False
        self.deflect_direction = True
        
        # Combat attributes
        self.MAX_HEALTH = 100
        self.health = self.MAX_HEALTH
        self.is_invincible = False
        self.invincible_timer = 0
        self.INVINCIBLE_DURATION = 180  # 3 seconds at 60 FPS
        
        # Knockback attributes
        self.is_hurt = False
        self.KNOCKBACK_FORCE = Vector2(-3, -8)
        self.is_dead = False
        
        # Set initial image and rect
        self.image = self.anim.get_current_frame(self.facing_right)
        self.rect = self.image.get_rect(center=(x, y))
    
    def start_dodge(self):
        """Initialize a dodge movement in the direction of the mouse"""
        if self.can_dodge and not self.is_dodging:
            self.is_dodging = True
            self.can_dodge = False
            self.dodge_timer = self.DODGE_DURATION
            self.on_ground = False
            
            mouse_pos = pygame.mouse.get_pos()
            to_mouse = Vector2(mouse_pos) - self.position
            angle = math.degrees(math.atan2(to_mouse.y, to_mouse.x))
            angle = (360 - angle) % 360  # Convert to clockwise and ensure [0,360]
            
            self.facing_right = angle < 90 or angle > 270
            
            angle_rad = math.radians(angle)
            self.velocity = Vector2(
                math.cos(angle_rad) * self.DODGE_SPEED,
                -math.sin(angle_rad) * self.DODGE_SPEED  # Negative because pygame Y is down
            )
            
            # Ensure we don't dodge too vertically
            # if abs(self.velocity.y) > self.DODGE_SPEED * 0.3:  # Limit vertical component
            #     self.velocity.y = self.DODGE_SPEED * 0.3 * (1 if self.velocity.y > 0 else -1)
            
            self.anim.change_state("dodge")
    
    def update_dodge(self):
        """Update dodge state and cooldown"""
        if self.is_dodging:
            self.is_deflecting = False
            self.dodge_timer -= 1
            if self.dodge_timer <= 0:
                self.is_dodging = False
                self.velocity.y *= 0.5

        if not self.can_dodge:
            self.dodge_cooldown_timer -= 1
            if self.dodge_cooldown_timer <= 0 and self.on_ground:
                self.can_dodge = True
                self.dodge_cooldown_timer = self.DODGE_COOLDOWN
    
    def handle_input(self):
        """Handle player input for movement and actions"""
        # Don't handle input if hurt or dead
        if self.is_hurt or self.is_dead:
            return
            
        keys = pygame.key.get_pressed()
        
        # Deflecting (handle this first before movement)
        if self.mouse_clicked and not self.is_dodging and self.can_deflect:
            mouse_pos = pygame.mouse.get_pos()
            self.knife.activate(mouse_pos)
            self.anim.change_state("deflect")
            # Set deflecting state and direction
            self.is_deflecting = True
            self.deflect_direction = mouse_pos[0] > self.position.x
            # Start cooldown
            self.can_deflect = False
            self.deflect_cooldown_timer = self.DEFLECT_COOLDOWN
        if self.mouse_clicked:
            self.mouse_clicked = False
        
        # Don't handle movement input while dodging
        if not self.is_dodging:
            # Reset horizontal acceleration
            self.acceleration.x = 0
            
            # Horizontal movement with acceleration
            if keys[pygame.K_d]:
                self.acceleration.x += self.ACCELERATION
                if not self.is_deflecting:  # Only change facing if not deflecting
                    self.facing_right = True
            if keys[pygame.K_a]:
                self.acceleration.x -= self.ACCELERATION
                if not self.is_deflecting:  # Only change facing if not deflecting
                    self.facing_right = False
        
        # Jumping and double jumping
        if self.space_pressed:
            if self.on_ground:
                self.velocity.y = self.JUMP_FORCE
                self.on_ground = False
                self.can_double_jump = True
                self.is_dodging = False
                self.anim.change_state("jump")
            elif self.can_double_jump and not self.is_dodging:
                self.velocity.y = self.DOUBLE_JUMP_FORCE
                self.can_double_jump = False
                self.anim.change_state("jump")
            self.space_pressed = False  # Reset the press state
        
        # Dodging
        if self.shift_pressed:
            self.start_dodge()
            self.shift_pressed = False  # Reset the press state
    
    def apply_physics(self):
        """Apply physics calculations to the player"""
        # Always apply gravity unless dodging
        if not self.is_dodging:
            if not self.on_ground and not self.is_dodging:
                self.velocity.y += self.GRAVITY
                
            # Only apply friction and acceleration if not hurt
            if not self.is_hurt:
                # Apply acceleration to velocity
                self.velocity += self.acceleration
                
                # Apply friction/air resistance
                if self.on_ground:
                    if abs(self.acceleration.x) < 0.1:  # If not actively moving
                        self.velocity.x *= self.GROUND_FRICTION
                else:
                    self.velocity.x *= self.AIR_RESISTANCE
            
            # Clamp velocities
            self.velocity.x = max(min(self.velocity.x, self.MAX_HORIZONTAL_SPEED), -self.MAX_HORIZONTAL_SPEED)
            self.velocity.y = min(self.velocity.y, self.MAX_FALL_SPEED)
        
        # Update position
        if not (self.is_dead and self.on_ground):
            self.position += self.velocity
        
        # Floor collision (using the bottom of the sprite)
        if self.position.y + self.height/2 > C.WINDOW_HEIGHT - C.FLOOR_HEIGHT:
            self.position.y = C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - self.height/2
            self.velocity.y = 0
            self.on_ground = True
            
            # Handle landing after being hurt
            if self.is_hurt:
                self.is_hurt = False
                if self.health <= 0:
                    self.is_dead = True
                    self.anim.change_state("dead")
                else:
                    self.anim.change_state("idle")
            elif self.anim.current_state == "fall":
                self.anim.change_state("idle")
            
        # Update rect position
        self.rect.center = self.position

        # Update dodge state only if not hurt
        if not self.is_hurt and not self.is_dead:
            self.update_dodge()

    
    def update_animation(self):
        """Update the current animation frame based on player state"""
        # Handle death animation first
        if self.is_dead:
            if self.anim.current_state != "dead":
                self.anim.change_state("dead")
            self.anim.update()
            self.image = self.anim.get_current_frame(self.facing_right)
            return
            
        # Handle hurt animation
        if self.is_hurt:
            if self.anim.current_state != "hurt":
                self.anim.change_state("hurt")
            self.anim.update()
            self.image = self.anim.get_current_frame(self.facing_right)
            return
            
        # Don't change state during dodge animation unless it's finished
        if not self.is_dodging or (self.is_dodging and self.anim.animation_finished):
            if not self.on_ground:
                if self.velocity.y < 0:
                    next_state = "jump"
                else:
                    next_state = "fall"
            else:
                if abs(self.velocity.x) > 0.5:
                    next_state = "run"
                else:
                    next_state = "idle"
                    
            # Handle state transitions
            if next_state != self.anim.current_state:
                # Only change state if current animation is finished or it's a looping animation
                if self.anim.animation_loops[self.anim.current_state] or self.anim.animation_finished:
                    self.anim.change_state(next_state)
        
        # Update animation and image
        self.anim.update()
        
        # Override facing direction during deflect
        if self.is_deflecting:
            self.facing_right = self.deflect_direction
        
        self.image = self.anim.get_current_frame(self.facing_right)
        
        # Update deflect cooldown
        if not self.can_deflect:
            self.deflect_cooldown_timer -= 1
            if self.deflect_cooldown_timer <= 0:
                self.can_deflect = True
        
        # Reset deflecting state when animation ends
        if self.anim.current_state != "deflect":
            self.is_deflecting = False
        
        # Make player blink during invincibility
        if self.is_invincible and (self.invincible_timer // 3) % 2:  # Blink every 4 frames
            self.image.set_alpha(128)
        else:
            self.image.set_alpha(255)
    
    def take_damage(self, amount, source_position=None):
        """Handle player taking damage with knockback"""
        if not self.is_invincible and not self.is_hurt and not self.is_dead:
            self.health -= amount
            self.is_invincible = True
            self.invincible_timer = self.INVINCIBLE_DURATION
            self.is_hurt = True
            
            # Apply knockback
            if source_position:
                knockback_to_right = False if source_position.x > self.position.x else True
            else:
                knockback_to_right = False if self.facing_right else True
            self.velocity = self.KNOCKBACK_FORCE
            self.facing_right = False
            if knockback_to_right:
                self.velocity = self.velocity.reflect(Vector2(1,0))
                self.facing_right = True

            # Change to hurt animation
            self.anim.change_state("hurt")
            
            # Ensure we're not on the ground
            if self.on_ground:
                self.on_ground = False
                self.position.y -= 1  # Slight lift to guarantee we're off ground
            
            # End any dodge
            self.is_dodging = False
    
    def check_projectile_collisions(self):
        """Check for collisions with enemy bullets"""
        if self.is_dodging or self.is_invincible or self.is_dead:
            return
            
        for bullet in self.game.groups['bullets']:
            if not bullet.is_deflected:  # Only check non-deflected bullets
                distance = (bullet.position - self.position).length()
                if distance < self.width/3:
                    self.take_damage(bullet.damage, bullet.position)
                    bullet.kill()

    def check_enemy_collisions(self):
        """Check for collisions with enemies"""
        if self.is_dodging or self.is_invincible or self.is_dead:
            return
            
        for enemy in self.game.groups['enemies']:
            if enemy.is_alive:
                distance = (enemy.position - self.position).length()
                if distance < self.width/2 + enemy.width/3:
                    self.take_damage(enemy.BODY_DAMAGE, enemy.position)
    
    def update(self):
        """Update the player's state"""
        if self.is_invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.is_invincible = False
        
        # Only handle input if not hurt/dead
        if not self.is_hurt and not self.is_dead:
            self.handle_input()
            
        self.apply_physics()
        self.knife.update()
        
        # Only check collisions if alive
        if not self.is_dead:
            self.check_projectile_collisions()
            self.check_enemy_collisions()
            
        self.update_animation()