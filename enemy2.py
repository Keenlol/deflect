from enemy_all import *
import random as rdm
import math
from player import *

class E2(Enemy):
    def __init__(self, x, y, game):
        loops = {
            "idle": True,
            "move": True,
            "hurt": False,
            "death": False,
            "dash": False,
            "attack2": False,
            "attack1": False
        }
        anim_info = {'path': 'sprites/enemies/e2', 
                     'loops': loops,
                     'speed': 0.2}
        super().__init__(x, y, game, maxhp=100, anim=anim_info)
        # Override base attributes
        self.MOVE_SPEED = (0.0, 3.0)
        
        # Movement attributes
        self.direction = 1  # 1 for right, -1 for left
        self.MOVE_DURATION = (30, 120) #Frames
        self.move_timer = self.get_random(self.MOVE_DURATION)
        self.WAIT_DURATION = (60, 180) #Frames
        self.wait_timer = self.get_random(self.WAIT_DURATION)
        self.MAX_DISTANCE = 400   # Maximum allowed distance from player

        # Attack attributes
        self.is_dashing = False
        self.is_charging = False
        self.dash_timer = 0
        self.charge_timer = 0
        
        self.attack_infos = {'slash': {'speed':10, 'dash dur':30, 'charge dur':30},
                            'shard': {'count':10, 'delay': 30, 'radius': 100, 'height': 100}}
        # Weapon sprite
        self.weapon_anim = Animation(self, "sprites/enemies/e2_slash", {
            "charge": False,
            "slash": False
        }, animation_speed=0.1)
        self.weapon_active = False
        
        # Shard attack attributes
        self.is_shard_attacking = False
        self.shard_timer = 0
        self.shards = []  # Track spawned shards
        
    def start_dash_attack(self, target):
        """Initialize dash attack"""
        self.is_dashing = True
        self.is_charging = True
        self.charge_timer = self.attack_infos['slash']['charge dur']
        self.dash_timer = self.attack_infos['slash']['dash dur']

        # Set direction and facing based on target
        self.direction = 1 if target.position.x > self.position.x else -1
        self.facing_right = self.direction > 0

        # Start animations
        self.anim.change_state("dash")
        self.weapon_anim.change_state("charge")
        self.weapon_active = True
        
        # Reset velocity
        self.velocity.x = 0

    def end_dash_attack(self):
        self.is_dashing = False
        self.weapon_active = False
        self.velocity.x = 0
        self.wait_timer = self.get_random(self.WAIT_DURATION)

    def update_dash_attack(self, target):
        """Update dash attack state"""
        if self.is_charging:
            # Charging phase
            self.charge_timer -= 1
            if self.charge_timer <= 0:
                # Start dash
                self.is_charging = False
                self.weapon_anim.change_state("slash")
                self.anim.change_state("attack2")
                self.velocity.x = self.attack_infos['slash']['speed'] * self.direction
        else:
            # Dashing phase
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.end_dash_attack()

    
    def draw_weapon(self, surface):
        """Draw the weapon animation"""
        if self.weapon_active:
            weapon_frame = self.weapon_anim.get_current_frame(self.facing_right)
            # Position the weapon relative to the enemy
            weapon_pos = Vector2(self.rect.center)
            offset = Vector2(50 if self.facing_right else -50, 0)  # Adjust offset as needed
            weapon_pos += offset
            
            weapon_rect = weapon_frame.get_rect(center=weapon_pos)
            surface.blit(weapon_frame, weapon_rect)
    
    def start_shard_attack(self, target):
        """Initialize shard attack"""
        self.is_shard_attacking = True
        self.shard_timer = self.attack_infos['shard']['delay']
        self.shards.clear()
        
        # Spawn shards above head
        height = self.attack_infos['shard']['height']
        radius = self.attack_infos['shard']['radius']
        for _ in range(self.attack_infos['shard']['count']):
            spawn_pos = Vector2(
                self.position.x + rdm.uniform(-radius, radius),
                self.position.y - height + rdm.uniform(-radius, radius)
            )
            # Initialize with zero velocity
            shard = Shard(spawn_pos, Vector2(0, 0), 33)
            self.shards.append(shard)
            self.game.groups['bullets'].add(shard)
            self.game.groups['all'].add(shard)
        
        # Start animation
        self.anim.change_state("attack1")
    
    def update_shard_attack(self, target):
        """Update shard attack state"""
        if self.shard_timer > 0:
            self.shard_timer -= 1
            if self.shard_timer <= 0:
                # Launch all shards
                for shard in self.shards:
                    # Calculate direction to target with spread
                    to_target = (target.position - shard.position).normalize()
                    angle = math.degrees(math.atan2(to_target.y, to_target.x))
                    final_angle = math.radians(angle)
                    
                    # Set velocity
                    launch_speed = 9  # Slightly random speed
                    velocity = Vector2(math.cos(final_angle), math.sin(final_angle)) * launch_speed
                    shard.velocity = velocity
                
                self.shards.clear()
                self.is_shard_attacking = False
                self.wait_timer = self.get_random(self.WAIT_DURATION)
    
    def ai_logic(self, target):
        """Updated movement with both attacks"""
        # Handle attacks
        if not self.is_hurt:
            if self.is_dashing:
                self.facing_right = self.direction > 0
                self.update_dash_attack(target)
                return
            elif self.is_shard_attacking:
                self.update_shard_attack(target)
                return
            
        # Normal movement
        # Always face the player when not dashing
        self.facing_right = target.position.x > self.position.x
        
        # Calculate distance to player
        distance_to_player = target.position.x - self.position.x
        
        # Update timers
        if self.wait_timer > 0:
            # Waiting state
            self.wait_timer -= 1
            self.velocity.x = 0
            self.anim.change_state("idle")
            
            # When wait is over, start moving in a random direction
            if self.wait_timer <= 0:
                # If too far from player, force direction towards player
                if abs(distance_to_player) > self.MAX_DISTANCE:
                    self.direction = 1 if distance_to_player > 0 else -1
                else:
                    self.direction = rdm.choice([-1, 1])
                
                self.move_timer = self.get_random(self.MOVE_DURATION)
                
        elif self.move_timer > 0:
            # Moving state
            self.move_timer -= 1
            
            # If too far from player, override direction to ai_logic towards player
            if abs(distance_to_player) > self.MAX_DISTANCE:
                self.direction = 1 if distance_to_player > 0 else -1
            
            if abs(self.velocity.x) < 0.1:
                self.velocity.x = rdm.randrange(self.MOVE_SPEED[0], self.MOVE_SPEED[1]) * self.direction
            self.anim.change_state("move")
            
            # When movement is over, check if we should attack
            if self.move_timer <= 0:
                distance_to_player = target.position.x - self.position.x
                if abs(distance_to_player) < 450:
                    self.start_dash_attack(target)
                else :
                    self.start_shard_attack(target)
    
    def update(self, target=None):
        self.weapon_anim.update()
        self.check_deflect_collision(self.target)
        super().update(target)

    def check_deflect_collision(self, player:Player):
        """Check for collision with player's deflect and handle deflection"""
        if self.is_dashing and self.weapon_active and not self.is_charging and not self.is_knocked_back:
            if player.knife.active and player.knife.anim.current_state == "deflect":
                if (self.position - player.knife.position).length() <= player.knife.width:
                    knockback_dir = self.position - player.position
                    knockback_amount = self.attack_infos['slash']['speed']
                    self.start_knockback(knockback_dir, knockback_amount)
                    self.end_dash_attack()
                    self.game.freeze_and_shake(10, 7, 7)
                    self.spawn_shards(player.position)
    
    def spawn_shards(self, player_position):
        """Spawn shards at the midpoint between enemy and player with evenly distributed angles"""
        midpoint = (self.position + player_position) / 2

        for _ in range(self.attack_infos['shard']['count']):
            angle_rad = math.radians(random.uniform(0,360))
            velocity = Vector2(math.cos(angle_rad), math.sin(angle_rad)) * rdm.uniform(15, 25)
            shard = Shard(midpoint + Vector2(0, -0), velocity, 33, deflected=True)
            self.game.groups['bullets'].add(shard)
            self.game.groups['all'].add(shard)

