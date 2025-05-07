from enemy_all import *
import math
from player import *
from timer import Timer
from sounds import Sounds

class E2(Enemy):
    # Constants
    MAX_DISTANCE = 400   # Maximum allowed distance from player
    
    # Attack data
    ATTACK_INFO = {
        'slash': {'speed': 10, 'dash_dur': 0.5, 'charge_dur': 0.5},
        'shard': {'count': 12, 'delay': 0.5, 'radius': 100, 'height': 150, 'speed': 10},
        'rain': {'count': 15, 'delay': 3/60, 'height': 250, 'width': 600},
        'damage': 30
    }
    
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
        super().__init__(x, y, game, maxhp=60, anim=anim_info, name='Fencer')
        
        # Override base attributes
        self.MOVE_SPEED = (0.0, 3.0)
        
        # Movement attributes
        self.direction = 1  # 1 for right, -1 for left
        
        # Initialize timers
        self.init_timers()
                
        # Weapon sprite
        self.weapon_anim = Animation(self, "sprites/enemies/e2_slash", {
            "charge": False,
            "slash": False
        }, animation_speed=0.1)
        self.weapon_active = False
        
        # Attack state tracking
        self.shards = []
        self.rain_index = 0
        self.rain_positions = []
        self.is_dashing = False
        
        # Start in waiting state
        self.start_waiting()
        
    def start_attack(self, target):
        if abs(target.position.x - self.position.x) < self.MAX_DISTANCE:
            self.current_attack = self.random((self.dash_attack, self.shard_attack), choice=True)
        else:
            self.current_attack = self.random((self.shard_attack, self.rain_attack), choice=True)

        self.is_attacking = True
        self.is_dashing = False
        
        if self.current_attack == self.dash_attack:
            self.start_dash_attack(target)
        elif self.current_attack == self.shard_attack:
            self.start_shard_attack(target)
        else:
            self.start_shard_rain(target)

    def start_dash_attack(self, target):
        # Set direction and facing based on target
        self.direction = 1 if target.position.x > self.position.x else -1
        self.facing_right = self.direction > 0

        self.anim.change_state("dash")
        self.weapon_anim.change_state("charge")
        self.weapon_active = True
        self.velocity.x = 0
        
        # Start charge phase
        self.attack_timer.start(self.ATTACK_INFO['slash']['charge_dur'])
        Sounds().play_sound('e2_charge')

    def end_dash_attack(self):
        self.weapon_active = False
        self.velocity.x = 0
        self.is_attacking = False
        self.current_attack = None
        self.start_waiting()

    def dash_attack(self, target):
        # Maintain the original dash direction
        self.facing_right = self.direction > 0
        
        if not self.is_dashing:  # Charging phase
            if not self.attack_timer.is_completed:
                return False
                
            if self.attack_timer.just_completed:
                # Just finished charging - start dash
                self.weapon_anim.change_state("slash")
                self.anim.change_state("attack2")
                self.velocity.x = self.ATTACK_INFO['slash']['speed'] * self.direction
                
                # Start dash phase
                self.attack_timer.start(self.ATTACK_INFO['slash']['dash_dur'])
                self.is_dashing = True

                Sounds().play_sound('e2_slash')
                return False
                
        elif self.is_dashing:  # Dashing phase
            if self.attack_timer.is_completed:
                self.end_dash_attack()
                return True
                
        return False
    
    def draw_weapon(self, surface):
        if self.weapon_active:
            weapon_frame = self.weapon_anim.get_current_frame(self.facing_right)
            # Position the weapon relative to the enemy
            weapon_pos = Vector2(self.rect.center)
            offset = Vector2(50 if self.facing_right else -50, 0)  # Adjust offset as needed
            weapon_pos += offset
            
            weapon_rect = weapon_frame.get_rect(center=weapon_pos)
            surface.blit(weapon_frame, weapon_rect)
    
    def start_shard_attack(self, target):
        self.attack_timer.start(self.ATTACK_INFO['shard']['delay'])
        self.shards.clear()
        
        # Create shards in a circular formation
        radius = self.ATTACK_INFO['shard']['radius']
        shard_count = self.ATTACK_INFO['shard']['count']
        
        # Calculate center position (above the enemy's head)
        center_pos = Vector2(
            self.position.x,
            self.position.y - self.ATTACK_INFO['shard']['height']
        )
        
        # Create shards arranged in a circle
        for i in range(shard_count):
            # Calculate angle for uniform distribution around the circle
            angle = (2 * math.pi * i) / shard_count
            
            # Calculate position on the circle
            spawn_pos = Vector2(
                center_pos.x + radius * math.cos(angle),
                center_pos.y + radius * math.sin(angle)
            )
            
            # Initialize with zero velocity
            shard = Shard(position=spawn_pos, 
                          velocity=Vector2(0, 0), 
                          game=self.game,
                          damage=self.ATTACK_INFO['damage'],
                          attack_name='Fencer Forward-Shards')
            self.shards.append(shard)
        
        self.anim.change_state("attack1")
        self.velocity.x = 0
        Sounds().play_sound_random(['e2_shards_spawn1','e2_shards_spawn2'])
    
    def shard_attack(self, target):
        if not self.attack_timer.is_completed:
            return False

        if self.attack_timer.just_completed:
            # Launch all shards
            Sounds().play_sound('e2_shards_push')
            for shard in self.shards:
                to_target = (target.position - shard.position).normalize()
                angle = math.degrees(math.atan2(to_target.y, to_target.x))
                final_angle = math.radians(angle)
                
                launch_speed = self.ATTACK_INFO['shard']['speed']
                velocity = Vector2(math.cos(final_angle), math.sin(final_angle)) * launch_speed
                shard.velocity = velocity
            
            self.shards.clear()
            self.is_attacking = False
            self.current_attack = None
            
            self.anim.change_state("idle")
            self.start_waiting()
            return True
            
        return False
    
    def start_shard_rain(self, target):
        self.rain_index = 0
        self.attack_timer.start(self.ATTACK_INFO['rain']['delay'])

        self.rain_positions = []
        shard_spacing = self.ATTACK_INFO['rain']['width'] / (self.ATTACK_INFO['rain']['count'] - 1) if self.ATTACK_INFO['rain']['count'] > 1 else 0
        
        start_x = target.position.x - self.ATTACK_INFO['rain']['width'] / 2
        for i in range(self.ATTACK_INFO['rain']['count']):
            pos_x = start_x + i * shard_spacing
            pos_y = target.position.y - self.ATTACK_INFO['rain']['height']
            self.rain_positions.append(Vector2(pos_x, pos_y))
        
        if not self.position.x > target.position.x:
            self.rain_positions.reverse()
        
        self.anim.change_state("attack1")
        self.velocity.x = 0
    
    def rain_attack(self, target):
        # Spawn new shard when delay timer completes
        if self.attack_timer.just_completed and self.rain_index < self.ATTACK_INFO['rain']['count']:
            spawn_pos = self.rain_positions[self.rain_index]
            
            Shard(position=spawn_pos, 
                 velocity=Vector2(0, -4), 
                 game=self.game,
                 damage=self.ATTACK_INFO['damage'],
                 gravity=0.3,
                 attack_name='Fencer Raining-Shards')
            
            self.rain_index += 1
            Sounds().play_sound_random(['e2_shards_spawn1','e2_shards_spawn2'])
            if self.rain_index < self.ATTACK_INFO['rain']['count']:
                self.attack_timer.start(self.ATTACK_INFO['rain']['delay'])
        
        # End attack when all shards have been spawned
        if self.rain_index >= self.ATTACK_INFO['rain']['count']:
            self.anim.change_state("idle")
            self.start_waiting()
            self.is_attacking = False
            self.current_attack = None
            return True
            
        return False
    
    def update_movement(self, target):
        # If too far from player, override direction to move towards player
        distance_to_player = target.position.x - self.position.x
        if abs(distance_to_player) > self.MAX_DISTANCE:
            self.direction = 1 if distance_to_player > 0 else -1
        
        if abs(self.velocity.x) < 0.1:
            self.velocity.x = self.random((self.MOVE_SPEED[0], self.MOVE_SPEED[1])) * self.direction
        self.anim.change_state("move")
    
    def ai_logic(self, target):
        self.weapon_anim.update()
        self.check_deflect_collision(target)
        
        # Handle attack state
        if self.is_attacking and self.current_attack:
            if self.current_attack != self.dash_attack:
                self.facing_right = target.position.x > self.position.x
            self.current_attack(target)
            return
        
        self.facing_right = target.position.x > self.position.x
        
        # Waiting
        if not self.wait_timer.is_completed:
            self.velocity.x = 0
            return
        
        # Start to move
        if self.wait_timer.just_completed:
            distance_to_player = target.position.x - self.position.x
            if abs(distance_to_player) > self.MAX_DISTANCE:
                self.direction = 1 if distance_to_player > 0 else -1
            else:
                self.direction = self.random((-1, 1), choice=True)
            self.start_movement()
        
        # Moving
        elif not self.move_timer.is_completed:
            self.update_movement(target)
        
        # Finished moving
        elif self.move_timer.just_completed:
            self.start_attack(target)

    def check_deflect_collision(self, player:Player):
        if (self.is_attacking and self.current_attack == self.dash_attack and
            self.weapon_active and self.is_dashing and not self.is_knocked_back):
            if player.knife.active and player.knife.anim.current_state == "deflect":
                if (self.position - player.knife.position).length() <= player.knife.width:
                    knockback_dir = self.position - player.position
                    knockback_amount = self.ATTACK_INFO['slash']['speed']
                    self.start_knockback(knockback_dir, knockback_amount)
                    self.end_dash_attack()
                    self.game.freeze_and_shake(10, 7, 7)
                    self.spawn_shards(player.position)
                    Sounds().play_sound_random(['deflect1', 'deflect2', 'deflect3'])
    
    def spawn_shards(self, player_position):
        midpoint = (self.position + player_position) / 2

        for _ in range(self.ATTACK_INFO['shard']['count']):
            angle_rad = math.radians(self.random((0.0, 360.0)))
            velocity = Vector2(math.cos(angle_rad), math.sin(angle_rad)) * self.random((15.0, 25.0))
            Shard(position=midpoint + Vector2(0, -0), 
                 velocity=velocity, 
                 game=self.game,
                 damage=self.ATTACK_INFO['damage'], 
                 deflected=True)
            Sounds().play_sound('deflect_sword')

