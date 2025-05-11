import pygame
from pygame.math import Vector2
from config import Config as C
from animation import Animation
from knife import Knife
import math
from timer import Timer
from stats import Stats
from sounds import Sounds

class Player(pygame.sprite.Sprite):
    GRAVITY = 0.8
    JUMP_FORCE = -15
    MAX_HORIZONTAL_SPEED = 8
    MAX_FALL_SPEED = 15
    ACCELERATION = 2
    DECELERATION = 8
    AIR_RESISTANCE = 1
    GROUND_FRICTION = 0.5
    MAX_HEALTH = 100
    DOUBLE_JUMP_FORCE = -12
    KNOCKBACK_FORCE = Vector2(-3, -8)

    def __init__(self, game, x=0, y=0):
        super().__init__()
        self.game = game
        self.width = 100
        self.height = 100
        
        # Private tag for stats tracking
        self.__tag = {
            'dodge_start_position': None,
            'dodge_damage_evaded': 0,
            'dodge_counted_enemies': set(),
            'last_processed_bullets': set()  # Cache for processed bullets
        }
        
        # Animation system
        animation_states = {
            "idle": True,
            "run": True,
            "jump": False,
            "fall": False,
            "dodge": False,
            "deflect": False,
            "hurt": False,  # Hurt animation is non-looping
            "dead": False   # Death animation is non-looping
        }
        self._anim = Animation(self, "sprites/player", animation_states, animation_speed=0.08)
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

        # Dodge attributes
        self.DODGE_SPEED = 25
        self.__dodge_timer = Timer(duration=0.14, owner=self)
        self.is_dodging = False
        self.__can_dodge = True
        self.__dodge_cooldown_timer = Timer(duration=0.33, owner=self, paused=True)
        
        # Double jump attributes
        self.__can_double_jump = True
        
        # Deflect attributes
        self.knife = Knife(self)
        self.__deflect_cooldown_timer = Timer(duration=0.5, owner=self, paused=True)
        self.__can_deflect = True
        self.is_deflecting = False
        self.__deflect_direction = True
        
        # Combat attributes
        self.__self_heal_timer = Timer(duration=1.0, owner=self, paused=False, auto_reset=True)
        self.health = self.MAX_HEALTH
        self.__is_invincible = False
        self.__invincible_timer = Timer(duration=3.0, owner=self, paused=True)
        
        self.is_hurt = False
        self.is_alive = True
        
        # Set initial image and rect
        self.image = self._anim.get_current_frame(self.facing_right)
        self.rect = self.image.get_rect(center=(x, y))
    
    @property
    def dodge_start_position(self):
        return self.__tag['dodge_start_position']
        
    @dodge_start_position.setter
    def dodge_start_position(self, value):
        self.__tag['dodge_start_position'] = value
        
    @property
    def dodge_damage_evaded(self):
        return self.__tag['dodge_damage_evaded']
        
    @dodge_damage_evaded.setter
    def dodge_damage_evaded(self, value):
        self.__tag['dodge_damage_evaded'] = value
        
    @property
    def dodge_counted_enemies(self):
        return self.__tag['dodge_counted_enemies']
    
    @property
    def last_processed_bullets(self):
        return self.__tag['last_processed_bullets']

    def update(self):
        """Update the player's state"""
        # Check for timer completions
        if self.__self_heal_timer.just_completed and self.is_alive:
            self.health += 1
            self.health = min(self.health, self.MAX_HEALTH)

        if self.__dodge_timer.is_completed and self.is_dodging:
            self.is_dodging = False
            self.velocity.y *= 0.5
            
            # Record dodge statistics when dodge ends (record even if damage_evaded is 0)
            Stats().record('dodged_attack', damage_evaded=self.dodge_damage_evaded)
            self.dodge_start_position = None
            self.dodge_counted_enemies.clear()
            self.last_processed_bullets.clear()
            
        if self.__dodge_cooldown_timer.is_completed and self.on_ground and not self.__can_dodge:
            self.__can_dodge = True
            
        if self.__deflect_cooldown_timer.is_completed and not self.__can_deflect:
            self.__can_deflect = True
            
        if self.__invincible_timer.is_completed and self.__is_invincible:
            self.__is_invincible = False
            
        # Only handle input if not hurt/dead
        if not self.is_hurt and self.is_alive:
            self.__handle_input()
            
        self.__apply_physics()
        self.knife.update()
        
        # Only check collisions if alive
        if self.is_alive:
            self.__check_projectile_collisions()
            self.__check_enemy_collisions()
            
        self.__update_animation()

    def take_damage(self, amount, source_position=None):
        """Handle player taking damage with knockback"""
        if not self.__is_invincible and not self.is_hurt and self.is_alive:
            self.health -= amount
            self.__is_invincible = True
            self.__invincible_timer.start()
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
            self._anim.change_state("hurt")
            
            # Ensure we're not on the ground
            if self.on_ground:
                self.on_ground = False
                self.position.y -= 1  # Slight lift to guarantee we're off ground
            
            # End any dodge and record evaded damage (even if damage_evaded is 0)
            if self.is_dodging:
                Stats().record('dodged_attack', damage_evaded=self.dodge_damage_evaded)
                self.dodge_start_position = None
                self.dodge_counted_enemies.clear()
                self.last_processed_bullets.clear()
            
            self.is_dodging = False
            self.__dodge_timer.stop()
            self.game.freeze_and_shake(10, 10, 20)
            Sounds().play_sound('player_damaged')
    

    def __start_dodge(self):
        """Initialize a dodge movement in the direction of the mouse"""
        if self.__can_dodge and not self.is_dodging:
            self.is_dodging = True
            self.__can_dodge = False
            self.__dodge_timer.start()
            self.__dodge_cooldown_timer.start()
            self.on_ground = False
            
            # Store position at start of dodge for damage evasion tracking
            self.dodge_start_position = Vector2(self.position)
            self.dodge_damage_evaded = 0
            self.dodge_counted_enemies.clear()
            self.last_processed_bullets.clear()
            
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
            
            self._anim.change_state("dodge")
            Sounds().play_sound_random(['dodge1', 'dodge2'])
    
    def __handle_input(self):
        """Handle player input for movement and actions"""
        # Don't handle input if hurt or dead
        if self.is_hurt or not self.is_alive:
            return
            
        keys = pygame.key.get_pressed()
        
        # Deflecting
        if self.mouse_clicked and not self.is_dodging and self.__can_deflect:
            Sounds().play_sound_random(['slash1', 'slash2', 'slash3'])
            mouse_pos = pygame.mouse.get_pos()
            self.knife.activate(mouse_pos)
            self._anim.change_state("deflect")
            # Set deflecting state and direction
            self.is_deflecting = True
            self.__deflect_direction = mouse_pos[0] > self.position.x
            # Start cooldown
            self.__can_deflect = False
            self.__deflect_cooldown_timer.start()
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
                self.__can_double_jump = True
                self.is_dodging = False
                self._anim.change_state("jump")
            elif self.__can_double_jump and not self.is_dodging:
                self.velocity.y = self.DOUBLE_JUMP_FORCE
                self.__can_double_jump = False
                self._anim.change_state("jump")
            self.space_pressed = False  # Reset the press state
        
        # Dodging
        if self.shift_pressed:
            self.__start_dodge()
            self.shift_pressed = False  # Reset the press state
    
    def __apply_physics(self):
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
        if self.is_alive or not self.on_ground:
            self.position += self.velocity
            
            # Prevent walking off screen horizontally
            half_width = int((self.width / 2) - 20)
            if self.position.x - half_width < 0:
                self.position.x = half_width
            elif self.position.x > C.WINDOW_WIDTH - half_width:
                self.position.x = C.WINDOW_WIDTH - half_width
        
        # Floor collision (using the bottom of the sprite)
        if self.position.y + self.height/2 > C.WINDOW_HEIGHT - C.FLOOR_HEIGHT:
            self.position.y = C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - self.height/2
            self.velocity.y = 0
            self.on_ground = True
            
            # Handle landing after being hurt
            if self.is_hurt:
                self.is_hurt = False
                if self.health <= 0:
                    self.is_alive = False
                    self._anim.change_state("dead")
                    self.__self_heal_timer.pause()
                else:
                    self._anim.change_state("idle")
            elif self._anim.current_state == "fall":
                self._anim.change_state("idle")
            
        # Update rect position
        self.rect.center = self.position
    
    def __update_animation(self):
        """Update the current animation frame based on player state"""
        # Handle death animation first
        if not self.is_alive:
            if self._anim.current_state != "dead":
                self._anim.change_state("dead")
            self._anim.update()
            self.image = self._anim.get_current_frame(self.facing_right)
            return
            
        # Handle hurt animation
        if self.is_hurt:
            if self._anim.current_state != "hurt":
                self._anim.change_state("hurt")
            self._anim.update()
            self.image = self._anim.get_current_frame(self.facing_right)
            return
            
        # Don't change state during dodge animation unless it's finished
        if not self.is_dodging or (self.is_dodging and self._anim.animation_finished):
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
            if next_state != self._anim.current_state:
                # Only change state if current animation is finished or it's a looping animation
                if self._anim.animation_loops[self._anim.current_state] or self._anim.animation_finished:
                    self._anim.change_state(next_state)
        
        # Update animation and image
        self._anim.update()
        
        # Override facing direction during deflect
        if self.is_deflecting:
            self.facing_right = self.__deflect_direction
        
        self.image = self._anim.get_current_frame(self.facing_right)
        
        # Reset deflecting state when animation ends
        if self._anim.current_state != "deflect":
            self.is_deflecting = False
        
        # Make player blink during invincibility
        if self.__is_invincible and int(self.__invincible_timer.progress * 20) % 2:  # Blink effect
            self.image.set_alpha(100)
        else:
            self.image.set_alpha(255)

    def __check_projectile_collisions(self):
        """Check for collisions with enemy bullets"""
        if self.__is_invincible or not self.is_alive:
            return
        
        # Define a maximum check distance to avoid unnecessary calculations
        max_check_dist = self.width * 1.5  # Larger buffer to account for fast moving projectiles
        dodge_pos = self.dodge_start_position
        current_pos = self.position
        collision_width = self.width/3
        dodge_width = self.width
        bullet_cache = self.last_processed_bullets
        
        for bullet in self.game.groups['bullets']:
            # Skip if this bullet was already processed
            if bullet in bullet_cache:
                continue
                
            if not bullet.is_deflected:  # Only check non-deflected bullets
                bullet_pos = bullet.position
                
                # Skip distant projectiles with quick bounding box check
                dx = abs(bullet_pos.x - current_pos.x)
                dy = abs(bullet_pos.y - current_pos.y)
                
                # Skip if bullet is too far from both current and dodge start positions
                if dx > max_check_dist or dy > max_check_dist:
                    if not self.is_dodging or not dodge_pos or \
                       abs(bullet_pos.x - dodge_pos.x) > max_check_dist or \
                       abs(bullet_pos.y - dodge_pos.y) > max_check_dist:
                        continue
                
                # Check collision with player's current position if not dodging
                if not self.is_dodging:
                    # Use squared distance for performance (avoids square root)
                    dx = bullet_pos.x - current_pos.x
                    dy = bullet_pos.y - current_pos.y
                    dist_sq = dx*dx + dy*dy
                    collision_width_sq = collision_width * collision_width
                    
                    if dist_sq < collision_width_sq:
                        damage = bullet.damage * bullet.speed if bullet.attack_name == 'Gunman Exploding-Laser' else bullet.damage
                        self.take_damage(damage, bullet_pos)
                        Stats().record('dmg_income',
                                      attack_name=bullet.attack_name,
                                      damage=bullet.damage)
                        bullet.kill()
                        continue
                
                # If player is dodging, check for dodge evasion (collision with original position)
                elif dodge_pos:
                    try:
                        # Skip already counted projectiles
                        if bullet.dodge_counted_by != id(self):
                            dx = bullet_pos.x - dodge_pos.x
                            dy = bullet_pos.y - dodge_pos.y
                            dist_sq = dx*dx + dy*dy
                            dodge_width_sq = dodge_width * dodge_width
                            
                            if dist_sq < dodge_width_sq:
                                self.dodge_damage_evaded += bullet.damage
                                bullet.dodge_counted_by = id(self)
                                # Add to processed set
                                bullet_cache.add(bullet)
                    except (AttributeError, KeyError):
                        pass

    def __check_enemy_collisions(self):
        """Check for collisions with enemies"""
        if self.__is_invincible or not self.is_alive:
            return
        
        # IT WOULDN'T HAVE TO BE THIS MUCH IF THERE WERE NO STATS TRACKING
        # AHHHHH

        # Store values locally for better performance
        dodge_pos = self.dodge_start_position
        current_pos = self.position 
        is_dodging = self.is_dodging
        dodge_counted = self.dodge_counted_enemies
        player_radius = self.width/2
            
        for enemy in self.game.groups['enemies']:
            if enemy.is_alive:
                enemy_pos = enemy.position
                enemy_radius = enemy.width/3
                collision_dist = player_radius + enemy_radius
                
                # Check evasion if dodging
                if is_dodging and dodge_pos and enemy not in dodge_counted:
                    dx = enemy_pos.x - dodge_pos.x
                    dy = enemy_pos.y - dodge_pos.y
                    dist_sq = dx*dx + dy*dy
                    collision_dist_sq = collision_dist * collision_dist
                    
                    if dist_sq < collision_dist_sq:
                        self.dodge_damage_evaded += enemy.BODY_DAMAGE
                        dodge_counted.add(enemy)
                
                # Check actual collision if not dodging
                if not is_dodging:
                    dx = enemy_pos.x - current_pos.x
                    dy = enemy_pos.y - current_pos.y
                    dist_sq = dx*dx + dy*dy
                    collision_dist_sq = collision_dist * collision_dist
                    
                    if dist_sq < collision_dist_sq:
                        if enemy.name == 'Fencer' and enemy.is_dashing:
                            self.take_damage(enemy.ATTACK_INFO['slash']['damage'], enemy_pos)
                            Stats().record('dmg_income',
                                            attack_name='Fencer Slash',
                                            damage=enemy.BODY_DAMAGE)
                        else:
                            self.take_damage(enemy.BODY_DAMAGE, enemy_pos)
                            Stats().record('dmg_income',
                                            attack_name=enemy.name + ' ' + 'Body',
                                            damage=enemy.BODY_DAMAGE)

