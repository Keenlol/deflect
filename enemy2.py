from enemy_all import *
import random as rdm
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
        self.move_timer = Timer(duration=self.get_random(self.MOVE_DURATION), 
                               owner=self, 
                               paused=True)
        
        self.wait_timer = Timer(duration=self.get_random(self.WAIT_DURATION), 
                               owner=self, 
                               paused=True)
        self.wait_timer.start()  # Start in waiting state
        
        # Attack timers
        self.charge_timer = Timer(duration=0, owner=self, paused=True)
        self.dash_timer = Timer(duration=0, owner=self, paused=True)
        self.shard_timer = Timer(duration=0, owner=self, paused=True)
        self.rain_timer = Timer(duration=0, owner=self, paused=True)
        
        # Attack data
        self.attack_infos = {
            'slash': {'speed': 10, 'dash dur': 0.5, 'charge dur': 0.5},
            'shard': {'count': 10, 'delay': 0.5, 'radius': 100, 'height': 100},
            'rain': {'count': 15, 'delay': 3/60, 'height': 300, 'width': 600},
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
        
    def start_attack(self, target):
        """Initialize a random attack based on distance to target"""
        self.is_attacking = True
        
        distance_to_player = target.position.x - self.position.x
        
        # Randomly choose between attacks with different probabilities based on distance
        if abs(distance_to_player) < 450:
            # Close range - prefer dash attack (60% chance)
            attack_choice = rdm.random()
            if attack_choice < 0.6:
                self.current_attack = self.dash_attack
                self.start_dash_attack(target)
            elif attack_choice < 0.8:
                self.current_attack = self.shard_attack
                self.start_shard_attack(target)
            else:
                self.current_attack = self.rain_attack
                self.start_shard_rain(target)
        else:
            # Long range - prefer projectile attacks (80% chance)
            attack_choice = rdm.random()
            if attack_choice < 0.5:
                self.current_attack = self.shard_attack
                self.start_shard_attack(target)
            elif attack_choice < 0.8:
                self.current_attack = self.rain_attack
                self.start_shard_rain(target)
            else:
                # Move closer to player
                self.direction = 1 if distance_to_player > 0 else -1
                self.move_timer.start(self.get_random(self.MOVE_DURATION))
                self.is_attacking = False
                self.current_attack = None
    
    def start_dash_attack(self, target):
        """Initialize dash attack"""
        # Set timers duration and start charge timer
        self.dash_timer.duration = self.attack_infos['slash']['dash dur']
        self.charge_timer.start(self.attack_infos['slash']['charge dur'])

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
        """End dash attack and return to idle state"""
        self.weapon_active = False
        self.velocity.x = 0
        self.is_attacking = False
        self.current_attack = None
        
        # Set new random wait duration and start wait timer
        self.wait_timer.start(self.get_random(self.WAIT_DURATION))

    def dash_attack(self, target):
        """Update dash attack state"""
        # Always maintain the original dash direction
        self.facing_right = self.direction > 0
        
        # Charging phase
        if not self.charge_timer.is_completed:
            return False
            
        # Just finished charging - start dash
        if self.charge_timer.just_completed:
            self.weapon_anim.change_state("slash")
            self.anim.change_state("attack2")
            self.velocity.x = self.attack_infos['slash']['speed'] * self.direction
            
            # Start dash timer
            self.dash_timer.start()
        
        # Dashing phase - wait for timer to complete
        if self.dash_timer.is_completed:
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
        self.shard_timer.start(self.attack_infos['shard']['delay'])
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
            shard = Shard(spawn_pos, Vector2(0, 0), self.attack_infos['damage'])
            self.shards.append(shard)
            self.game.groups['bullets'].add(shard)
            self.game.groups['all'].add(shard)
        
        # Start animation
        self.anim.change_state("attack1")
        self.velocity.x = 0
    
    def shard_attack(self, target):
        """Update shard attack state"""
        if not self.shard_timer.is_completed:
            return False
            
        if self.shard_timer.just_completed:
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
            self.is_attacking = False
            self.current_attack = None
            
            # Reset animation to prevent getting stuck
            self.anim.change_state("idle")
            
            # Set new random wait duration and start timer
            self.wait_timer.start(self.get_random(self.WAIT_DURATION))
            return True
            
        return False
    
    def start_shard_rain(self, target):
        """Initialize shard rain attack"""
        self.rain_timer.start(self.attack_infos['rain']['delay'])
        self.rain_index = 0

        # Determine spawn direction (left-to-right or right-to-left)
        self.rain_left_to_right = self.position.x > target.position.x
        
        # Calculate positions for all shards
        self.rain_positions = []
        shard_spacing = self.attack_infos['rain']['width'] / (self.attack_infos['rain']['count'] - 1) if self.attack_infos['rain']['count'] > 1 else 0
        
        start_x = target.position.x - self.attack_infos['rain']['width'] / 2
        for i in range(self.attack_infos['rain']['count']):
            pos_x = start_x + i * shard_spacing
            pos_y = target.position.y - self.attack_infos['rain']['height']
            self.rain_positions.append(Vector2(pos_x, pos_y))
        
        # Reverse positions if needed based on enemy position
        if not self.rain_left_to_right:
            self.rain_positions.reverse()
        
        # Start animation
        self.anim.change_state("attack1")
        self.velocity.x = 0
    
    def rain_attack(self, target):
        """Update shard rain attack state"""
        # Spawn new shard when delay timer completes
        if self.rain_timer.just_completed and self.rain_index < self.attack_infos['rain']['count']:
            # Get next position
            spawn_pos = self.rain_positions[self.rain_index]
            
            # Create shard with downward velocity
            shard = Shard(spawn_pos, Vector2(0, -2), self.attack_infos['damage'])
            shard.GRAVITY = 0.2
            
            # Add to game
            self.game.groups['bullets'].add(shard)
            self.game.groups['all'].add(shard)
            
            # Increment index and restart timer
            self.rain_index += 1
            self.rain_timer.start()
        
        # End attack when all shards have been spawned
        if self.rain_index >= self.attack_infos['rain']['count']:
            # Reset animation to prevent getting stuck
            self.anim.change_state("idle")
            
            # Set new random wait duration and start timer
            self.wait_timer.start(self.get_random(self.WAIT_DURATION))
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
            self.velocity.x = rdm.randrange(self.MOVE_SPEED[0], self.MOVE_SPEED[1]) * self.direction
        self.anim.change_state("move")
    
    def ai_logic(self, target):
        """Updated movement with all attacks"""
        self.weapon_anim.update()
        self.check_deflect_collision(target)
        
        # Handle attack state
        if self.is_attacking and self.current_attack:
            # Let the attack continue - facing handled inside dash_attack
            if self.current_attack != self.dash_attack:
                self.facing_right = target.position.x > self.position.x
            
            self.current_attack(target)
            return
        
        # Always face the player when not attacking
        self.facing_right = target.position.x > self.position.x
        
        # Handle wait state
        if not self.wait_timer.is_completed:
            self.velocity.x = 0
            self.anim.change_state("idle")
            return
        
        # Start moving after wait
        if self.wait_timer.just_completed:
            # Choose direction based on player position
            distance_to_player = target.position.x - self.position.x
            if abs(distance_to_player) > self.MAX_DISTANCE:
                self.direction = 1 if distance_to_player > 0 else -1
            else:
                self.direction = rdm.choice([-1, 1])
                
            # Start movement
            self.move_timer.start(self.get_random(self.MOVE_DURATION))
        
        # Handle movement state
        elif not self.move_timer.is_completed:
            self.update_movement(target)
        
        # Choose attack when movement completes
        elif self.move_timer.just_completed:
            self.start_attack(target)

    def check_deflect_collision(self, player:Player):
        """Check for collision with player's deflect and handle deflection"""
        if (self.is_attacking and self.current_attack == self.dash_attack and
            self.weapon_active and self.charge_timer.is_completed and not self.is_knocked_back):
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
            shard = Shard(midpoint + Vector2(0, -0), velocity, self.attack_infos['damage'], deflected=True)
            self.game.groups['bullets'].add(shard)
            self.game.groups['all'].add(shard)

