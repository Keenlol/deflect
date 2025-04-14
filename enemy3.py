from enemy_all import *
import math
import random
from projectile import Laser

class E3(Enemy):
    def __init__(self, x, y, game):
        # Animation setup
        loops = {
            "idle": True,
            "aim": False,
            "attack": False,
            "hurt": False,
            "death": False
        }

        anim_info = {
            'path': 'sprites/enemies/e3',
            'loops': loops,
            'speed': 0.2
        }

        super().__init__(x, y, game, width=100, 
                         height=100, gravity=0.0, movespeed=random.uniform(0.5, 2.0), 
                         maxhp=80, anim=anim_info)

        # Movement attributes
        self.TARGET_DST = random.randint(300,500)
        self.DST_TOLERANCE = 75
        self.ACCELERATION = random.uniform(0.01, 0.2)  # How quickly speed increases
        self.DECELERATION = 0.05 # Multiplier for speed reduction
        self.current_speed = 0  # Track current speed for smooth acceleration
        
        # Bobbing attributes
        self.base_position = Vector2(x, y)  # Center point for horizontal movement and bobbing
        self.BOB_FREQUENCY = 0.5  # How many cycles per second
        self.BOB_AMPLITUDE = 20   # How many pixels up/down
        self.bobbing_timer = 0.0

        # Attack attributes
        self.attack_timer = 0
        self.attack_phase = 0
        self.is_attacking = False
        self.current_attack = None
        self.aim_timer = 0
        self.aim_duration = 2.0  # Fixed aim duration
        self.aim_cooldown = random.uniform(3.0, 5.0)  # Random cooldown between aims
        self.aim_cooldown_timer = 0
        self.is_aiming = False
        self.aim_angle = 0  # Angle to aim at player
        
        # Attack attributes
        self.attack_infos = {
            'bounce': {
                'speed': 20, 
                'bounce_limit': 5, 
                'damage': 20, 
                'size': 8
            },
            'bomb': {
                'initial_speed': 15,
                'speed_mul': 0.95,  # Slows down over time
                'explosion_threshold': 2.0,  # Speed threshold for explosion
                'explosion_count': 12,  # Number of lasers in explosion
                'explosion_speed': 10,
                'explosion_speed_mul': 0.97,
                'initial_damage': 15,
                'explosion_damage': 10,
                'initial_size': 12,
                'explosion_size': 6
            },
            'homing': {
                'count': 3,  # Number of homing lasers to fire
                'delay': 0.3,  # Delay between shots in seconds
                'speed': 8,
                'turn_rate': 3.0,  # Degrees per frame
                'damage': 25,
                'size': 8
            }
        }

    def ai_logic(self, target):
        """Main AI logic for E3"""
        # Calculate direction to player for aiming
        to_player = target.position - self.base_position
        self.aim_angle = math.atan2(to_player.y, to_player.x)
        
        # Always face the player based on aim angle
        self.facing_right = math.cos(self.aim_angle) > 0
        
        # Handle aiming and attacking
        if self.is_aiming:
            # Stop movement while aiming
            self.current_speed = 0
            self.velocity = Vector2(0, 0)
            
            # Update aim timer
            self.aim_timer += 1/C.FPS
            
            # Check if aim duration is complete
            if self.aim_timer >= self.aim_duration:
                self.is_aiming = False
                self.is_attacking = True
                self.anim.change_state("attack")
                # Randomly choose between the three attacks
                attack_func = random.choice([self.fire_laser, self.fire_bomb, self.fire_homing])
                attack_func(target)
        elif self.is_attacking:
            # Stay still during attack
            self.current_speed = 0
            self.velocity = Vector2(0, 0)
            
            # Attack animation will play and then return to idle
            if self.anim.animation_finished:
                self.is_attacking = False
                self.aim_cooldown_timer = 0
        else:
            # Normal movement when not aiming or attacking
            to_player = target.position - self.base_position
            current_distance = to_player.length()
            
            # Handle horizontal movement based on distance
            if abs(current_distance - self.TARGET_DST) > self.DST_TOLERANCE:
                direction = to_player.normalize()
                
                if current_distance < self.TARGET_DST:
                    direction = -direction
                
                self.current_speed = min(self.current_speed + self.ACCELERATION, self.MOVE_SPEED)
                
                self.velocity = direction * self.current_speed
                self.base_position += self.velocity
                
                self.anim.change_state("idle")
            else:
                self.current_speed *= (1 - self.DECELERATION)
                
                if self.current_speed < 0.1:
                    self.current_speed = 0
                    self.velocity = Vector2(0, 0)
                else:
                    self.velocity = self.velocity.normalize() * self.current_speed
                    self.base_position += self.velocity
                    
                self.anim.change_state("idle")
            
            # Check if it's time to start aiming
            self.aim_cooldown_timer += 1/C.FPS
            if self.aim_cooldown_timer >= self.aim_cooldown:
                self.is_aiming = True
                self.aim_timer = 0
                self.anim.change_state("aim")
                # Randomize next aim cooldown
                self.aim_cooldown = random.uniform(3.0, 5.0)
        
        # Update bobbing
        self.bobbing_timer += 1 / C.FPS
        bob_offset = self.BOB_AMPLITUDE * math.sin(self.bobbing_timer * self.BOB_FREQUENCY * 2 * math.pi)
        
        # Update final position including bobbing
        self.position.x = self.base_position.x
        self.position.y = self.base_position.y + bob_offset
        
        # Update rect position using the final calculated position
        self.rect.center = self.position
    
    def fire_bomb(self, target):
        """Fire a bomb that explodes into multiple lasers"""
        # Calculate direction to target
        to_target = target.position - self.position
        direction = to_target.normalize()
        
        # Get bomb properties
        bomb_info = self.attack_infos['bomb']
        
        # Create initial bomb projectile
        gun_position = Vector2(self.position.x + (self.width/2 if self.facing_right else -self.width/2), 
                             self.position.y)
        
        # Create the bomb with a callback for explosion
        def on_slow_callback(bomb):
            # Create explosion lasers in all directions
            for i in range(bomb_info['explosion_count']):
                angle = (360 / bomb_info['explosion_count']) * i
                rad_angle = math.radians(angle)
                explosion_dir = Vector2(math.cos(rad_angle), math.sin(rad_angle))
                
                # Create explosion laser
                explosion_laser = Laser(
                    Vector2(bomb.position),  # Use bomb's position
                    explosion_dir * bomb_info['explosion_speed'],
                    bomb_info['explosion_damage'],
                    bomb_info['explosion_size']
                )
                # If the bomb was deflected, all explosion lasers should be deflected too
                explosion_laser.is_deflected = bomb.is_deflected
                explosion_laser.SPEED_MULTIPLIER = bomb_info['explosion_speed_mul']
                
                # Add to game groups
                self.game.groups['bullets'].add(explosion_laser)
                self.game.groups['all'].add(explosion_laser)
            
            # Remove the original bomb
            bomb.kill()

        # Create initial bomb laser
        bomb = Laser(gun_position, direction * bomb_info['initial_speed'],
                    bomb_info['initial_damage'], bomb_info['initial_size'])
        bomb.SPEED_MULTIPLIER = bomb_info['speed_mul']
        bomb.explosion_threshold = bomb_info['explosion_threshold']
        bomb.update = lambda: self._update_bomb(bomb, on_slow_callback)
        
        # Add to game groups
        self.game.groups['bullets'].add(bomb)
        self.game.groups['all'].add(bomb)
        
        return True  # Attack is complete after firing

    def _update_bomb(self, bomb, on_slow_callback):
        """Custom update method for bomb projectiles"""
        # Apply normal physics
        bomb.apply_physics()
        
        # Check if speed is below threshold
        if bomb.velocity.length() < bomb.explosion_threshold:
            on_slow_callback(bomb)
            return
        
        # Normal bounds check and draw
        bomb.check_bounds()
        bomb.draw()

    def fire_homing(self, target):
        """Fire multiple homing lasers with delay"""
        if not hasattr(self, '_homing_state'):
            self._homing_state = {
                'shots_fired': 0,
                'delay': 0
            }
        
        homing_info = self.attack_infos['homing']
        
        # Check if we need to wait
        if self._homing_state['delay'] > 0:
            self._homing_state['delay'] -= 1/C.FPS
            return False
        
        if self._homing_state['shots_fired'] >= homing_info['count']:
            # Reset for next use
            self._homing_state = {
                'shots_fired': 0,
                'delay': 0
            }
            return True
        
        # Calculate initial direction
        to_target = target.position - self.position
        direction = to_target.normalize()
        
        # Create homing laser
        gun_position = Vector2(self.position.x + (self.width/2 if self.facing_right else -self.width/2), 
                             self.position.y)
        
        laser = Laser(gun_position, direction * homing_info['speed'],
                     homing_info['damage'], homing_info['size'])
        
        # Add homing behavior
        laser.target = target
        laser.original_target = target  # Keep track of original target for deflection logic
        laser.turn_rate = homing_info['turn_rate']
        laser.update = lambda: self._update_homing_laser(laser)
        
        # Add to game groups
        self.game.groups['bullets'].add(laser)
        self.game.groups['all'].add(laser)
        
        # Update firing state
        self._homing_state['shots_fired'] += 1
        self._homing_state['delay'] = homing_info['delay']
        
        return False

    def _update_homing_laser(self, laser):
        """Custom update method for homing lasers"""
        if not laser.alive:
            return
            
        # If deflected, switch target to a random enemy
        if laser.is_deflected and (not hasattr(laser, 'deflected_retargeted') or not laser.deflected_retargeted):
            # Get all enemies
            enemies = [sprite for sprite in self.game.groups['enemies'] 
                      if sprite.alive and sprite != laser.original_target]
            if enemies:
                laser.target = random.choice(enemies)
                laser.deflected_retargeted = True
            
        if not laser.target or not laser.target.alive:
            # If target is dead/none, just continue in current direction
            laser.apply_physics()
            laser.check_bounds()
            laser.draw()
            return
            
        # Calculate angle to target
        to_target = laser.target.position - laser.position
        target_angle = math.degrees(math.atan2(to_target.y, to_target.x))
        current_angle = math.degrees(math.atan2(laser.velocity.y, laser.velocity.x))
        
        # Calculate angle difference and clamp to turn rate
        angle_diff = (target_angle - current_angle + 180) % 360 - 180
        turn_amount = max(-laser.turn_rate, min(laser.turn_rate, angle_diff))
        
        # Update velocity direction
        new_angle = math.radians(current_angle + turn_amount)
        speed = laser.velocity.length()
        laser.velocity = Vector2(math.cos(new_angle), math.sin(new_angle)) * speed
        
        # Normal physics and checks
        laser.apply_physics()
        laser.check_bounds()
        laser.draw()

    def fire_laser(self, target):
        """Fire a laser at the target"""
        # Calculate direction to target
        to_target = target.position - self.position
        direction = to_target.normalize()
        
        # Create projectile
        # Position at the edge of the enemy (assuming gun is on the right side)
        # Adjust based on facing direction
        if self.facing_right:
            gun_position = Vector2(self.position.x + self.width/2, self.position.y)
        else:
            gun_position = Vector2(self.position.x - self.width/2, self.position.y)
            
        # Create a laser projectile with bounce properties
        bounce_info = self.attack_infos['bounce']
        laser = Laser(gun_position, direction * bounce_info['speed'], 
                     bounce_info['damage'], bounce_info['size'], 
                     bounce_info['bounce_limit'])
        
        # Add to game groups
        self.game.groups['bullets'].add(laser)
        self.game.groups['all'].add(laser)