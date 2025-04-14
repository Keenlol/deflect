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
        
        # Laser attack attributes
        self.attack_infos = {
            'bounce': {'speed': 20, 'bounce_limit': 5, 'damage': 20, 'size': 20}
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
                self.fire_laser(target)
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