from enemy_all import *
import math
from player import *
from timer import Timer

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
        super().__init__(x, y, game, maxhp=60, anim=anim_info)
        
        # Override base attributes
        self.MOVE_SPEED = (0.0, 3.0)
        
        # Movement attributes
        self.direction = 1  # 1 for right, -1 for left
        self.MOVE_DURATION = (0.5, 2.0)  # Seconds
        self.WAIT_DURATION = (1.0, 3.0)  # Seconds
        self.MAX_DISTANCE = 400   # Maximum allowed distance from player
        
        # Create timers with random durations
        self.move_timer = Timer(duration=self.random(self.MOVE_DURATION), 
                               owner=self, 
                               paused=True)
        
        self.wait_timer = Timer(duration=self.random(self.WAIT_DURATION), 
                               owner=self, 
                               paused=True)
        self.wait_timer.start()  # Start in waiting state
        
        # Attack timer - we'll use just one timer for all attack phases
        self.attack_timer = Timer(duration=0, owner=self, paused=True)
        
        # Attack data
        self.attack_infos = {
            'slash': {
                'speed': 10, 
                'dash dur': 0.5, 
                'charge dur': 0.5
                },
            'shard': {
                'count': 10, 
                'delay': 0.5, 
                'radius': 100, 
                'height': 100, 
                'speed': 10
                },
            'rain': {
                'count': 15, 
                'delay': 3/60, 
                'height': 250, 
                'width': 600
                },
            'damage': 30
        }
        
        # Weapon sprite
        self.weapon_anim = Animation(self, "sprites/enemies/e2_slash", {
            "charge": False,
            "slash": False
        }, animation_speed=0.1)
        self.weapon_active = False
        
        # Attack state
        self.is_attacking = False
        self.current_attack = None
        self.shards = []  # Track spawned shards
        self.rain_index = 0
        self.rain_positions = []
        self.is_dashing = False  # Track which phase of an attack we're in
        
    def start_attack(self, target):
        """Initialize a random attack based on distance to target"""
        if abs(target.position.x - self.position.x) < self.MAX_DISTANCE:
            self.current_attack = self.random((self.dash_attack, self.shard_attack), choice=True)
        else:
            self.current_attack = self.random((self.shard_attack, self.rain_attack), choice=True)

        self.is_attacking = True
        self.is_dashing = False
        
        if self.current_attack == self.dash_attack : self.start_dash_attack(target)
        elif self.current_attack == self.shard_attack : self.start_shard_attack(target)
        else : self.start_shard_rain(target)

    def start_dash_attack(self, target):
        """Initialize dash attack"""
        # Set direction and facing based on target
        self.direction = 1 if target.position.x > self.position.x else -1
        self.facing_right = self.direction > 0

        self.anim.change_state("dash")
        self.weapon_anim.change_state("charge")
        self.weapon_active = True
        self.velocity.x = 0
        
        # Start charge phase
        self.attack_timer.start(self.attack_infos['slash']['charge dur'])

    def end_dash_attack(self):
        """End dash attack and return to idle state"""
        self.weapon_active = False
        self.velocity.x = 0
        self.is_attacking = False
        self.current_attack = None
        self.wait_timer.start(self.random(self.WAIT_DURATION))

    def dash_attack(self, target):
        """Update dash attack state"""
        # Maintain the original dash direction
        self.facing_right = self.direction > 0
        
        if not self.is_dashing:  # Charging phase
            if not self.attack_timer.is_completed:
                return False
                
            if self.attack_timer.just_completed:
                # Just finished charging - start dash
                self.weapon_anim.change_state("slash")
                self.anim.change_state("attack2")
                self.velocity.x = self.attack_infos['slash']['speed'] * self.direction
                
                # Start dash phase
                self.attack_timer.start(self.attack_infos['slash']['dash dur'])
                self.is_dashing = True
                return False
                
        elif self.is_dashing:  # Dashing phase
            if self.attack_timer.is_completed:
                self.end_dash_attack()
                return True
                
        return False
    
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
        self.attack_timer.start(self.attack_infos['shard']['delay'])
        self.shards.clear()
        
        # Spawn shards above head
        height = self.attack_infos['shard']['height']
        radius = self.attack_infos['shard']['radius']
        for _ in range(self.attack_infos['shard']['count']):
            spawn_pos = Vector2(
                self.position.x + self.random((-radius, radius)),
                self.position.y - height + self.random((-radius, radius))
            )
            # Initialize with zero velocity
            shard = Shard(position=spawn_pos, 
                          velocity=Vector2(0, 0), 
                          damage=self.attack_infos['damage'],
                          game=self.game)
            self.shards.append(shard)
        
        # Start animation
        self.anim.change_state("attack1")
        self.velocity.x = 0
    
    def shard_attack(self, target):
        """Update shard attack state"""
        if not self.attack_timer.is_completed:
            return False

        if self.attack_timer.just_completed:
            # Launch all shards
            for shard in self.shards:
                to_target = (target.position - shard.position).normalize()
                angle = math.degrees(math.atan2(to_target.y, to_target.x))
                final_angle = math.radians(angle)
                
                launch_speed = self.attack_infos['shard']['speed']
                velocity = Vector2(math.cos(final_angle), math.sin(final_angle)) * launch_speed
                shard.velocity = velocity
            
            self.shards.clear()
            self.is_attacking = False
            self.current_attack = None
            
            self.anim.change_state("idle")
            self.wait_timer.start(self.random(self.WAIT_DURATION))
            return True
            
        return False
    
    def start_shard_rain(self, target):
        """Initialize shard rain attack"""
        self.rain_index = 0
        self.attack_timer.start(self.attack_infos['rain']['delay'])

        self.rain_positions = []
        shard_spacing = self.attack_infos['rain']['width'] / (self.attack_infos['rain']['count'] - 1) if self.attack_infos['rain']['count'] > 1 else 0
        
        start_x = target.position.x - self.attack_infos['rain']['width'] / 2
        for i in range(self.attack_infos['rain']['count']):
            pos_x = start_x + i * shard_spacing
            pos_y = target.position.y - self.attack_infos['rain']['height']
            self.rain_positions.append(Vector2(pos_x, pos_y))
        
        if not self.position.x > target.position.x:
            self.rain_positions.reverse()
        
        self.anim.change_state("attack1")
        self.velocity.x = 0
    
    def rain_attack(self, target):
        """Update shard rain attack state"""
        # Spawn new shard when delay timer completes
        if self.attack_timer.just_completed and self.rain_index < self.attack_infos['rain']['count']:
            spawn_pos = self.rain_positions[self.rain_index]
            
            Shard(position=spawn_pos, 
                velocity=Vector2(0, -4), 
                damage=self.attack_infos['damage'],
                game=self.game,
                gravity=0.3)
            
            self.rain_index += 1
            
            if self.rain_index < self.attack_infos['rain']['count']:
                self.attack_timer.start(self.attack_infos['rain']['delay'])
        
        # End attack when all shards have been spawned
        if self.rain_index >= self.attack_infos['rain']['count']:
            self.anim.change_state("idle")
            self.wait_timer.start(self.random(self.WAIT_DURATION))
            self.is_attacking = False
            self.current_attack = None
            return True
            
        return False
    
    def update_movement(self, target):
        """Update movement state"""
        # If too far from player, override direction to move towards player
        distance_to_player = target.position.x - self.position.x
        if abs(distance_to_player) > self.MAX_DISTANCE:
            self.direction = 1 if distance_to_player > 0 else -1
        
        if abs(self.velocity.x) < 0.1:
            self.velocity.x = self.random((self.MOVE_SPEED[0], self.MOVE_SPEED[1])) * self.direction
        self.anim.change_state("move")
    
    def ai_logic(self, target):
        """Updated movement with all attacks"""
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
            self.anim.change_state("idle")
            return
        
        # Start to move
        if self.wait_timer.just_completed:
            distance_to_player = target.position.x - self.position.x
            if abs(distance_to_player) > self.MAX_DISTANCE:
                self.direction = 1 if distance_to_player > 0 else -1
            else:
                self.direction = self.random((-1, 1), choice=True)
            self.move_timer.start(self.random(self.MOVE_DURATION))
        
        # Moving
        elif not self.move_timer.is_completed:
            self.update_movement(target)
        
        # Finished moving
        elif self.move_timer.just_completed:
            self.start_attack(target)

    def check_deflect_collision(self, player:Player):
        """Check for collision with player's deflect and handle deflection"""
        if (self.is_attacking and self.current_attack == self.dash_attack and
            self.weapon_active and self.is_dashing and not self.is_knocked_back):
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
            angle_rad = math.radians(self.random((0.0,360.0)))
            velocity = Vector2(math.cos(angle_rad), math.sin(angle_rad)) * self.random((15.0, 25.0))
            Shard(position=midpoint + Vector2(0, -0), 
                velocity=velocity, 
                damage=self.attack_infos['damage'], 
                deflected=True,
                game=self.game)

