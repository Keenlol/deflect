from enemy_all import *
import math
import random

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
                        height=100, gravity=0.0, movespeed=random.uniform(1.0, 3.0), 
                        maxhp=80, anim=anim_info)

        # Movement attributes
        self.TARGET_DST = random.randint(300,500)
        self.DST_TOLERANCE = 75
        self.ACCELERATION = random.uniform(0.1, 0.5)  # How quickly speed increases
        self.DECELERATION = random.uniform(0.1, 0.5)  # Multiplier for speed reduction
        self.current_speed = 0  # Track current speed for smooth acceleration
        
        # Bobbing attributes
        self.base_position = Vector2(x, y)  # Center point for horizontal movement and bobbing
        self.position = Vector2(x, y)     # Actual rendered position including bobbing
        self.BOB_FREQUENCY = 0.5  # How many cycles per second
        self.BOB_AMPLITUDE = 20   # How many pixels up/down
        self.bobbing_timer = 0.0

        # Attack attributes (to be implemented later)
        self.attack_timer = 0
        self.attack_phase = 0
        self.is_attacking = False
        self.current_attack = None

    def ai_logic(self, target):
        """Main AI logic for E3"""
        self.facing_right = target.position.x > self.position.x # Use final position for facing
        
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
            
        # Update bobbing
        self.bobbing_timer += 1 / C.FPS
        bob_offset = self.BOB_AMPLITUDE * math.sin(self.bobbing_timer * self.BOB_FREQUENCY * 2 * math.pi)
        
        # Update final position including bobbing
        self.position.x = self.base_position.x
        self.position.y = self.base_position.y + bob_offset
        
        # Update rect position using the final calculated position
        self.rect.center = self.position