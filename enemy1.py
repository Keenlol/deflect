from enemy_all import *
from timer import Timer

class E1(Enemy):
    def __init__(self, x, y, game):

        loops = {
            "idle": True,
            "move": True,
            "attack": False,
            "hurt": False,
            "death": False
        }

        anim_info = {'path':'sprites/enemies/e1',
                'loops': loops,
                'speed': 0.2}

        super().__init__(x, y, game, width=100, 
                         height=100, gravity=0.0, movespeed=0.1, 
                         maxhp=40, anim=anim_info)

        # Movement attributes
        self.start_pos = Vector2(x, y)
        self.target_pos = Vector2(x, y)
        self.MOVE_DURATION = (1.0, 3.0)
        self.WAIT_DURATION = (1.0, 3.0)
        
        self.move_timer = Timer(duration=self.random(self.MOVE_DURATION), 
                                owner=self, 
                                paused=True)
        
        self.wait_timer = Timer(duration=self.random(self.WAIT_DURATION), 
                                owner=self, 
                                paused=True)
        
        self.attack_timer = Timer(duration=0, owner=self, paused=True)
        
        self.needs_new_target = True
        self.ATTACK_INFOS = {'radial': {'speed': 8, 'speed_mul': 1, 'delay': 5/60},
                                'burst': {'speed': 20, 'speed_mul': 0.95, 'delay': 10/60, 'spread':20},
                                'follow': {'speed': 0.1, 'speed_mul': 1.05, 'delay': 5/60},
                                'damage': 33,
                                'radius': 10}
        
        # Attack pattern attributes
        self.attack_phase = 0
        self.is_attacking = False
        self.current_attack = None
        self.shots_fired = 0

        self.wait_timer.start()

    def ease_in_out_sine(self, t):
        """Sine easing function for smooth movement"""
        return -(math.cos(math.pi * t) - 1) / 2
    
    def pick_new_position(self, target):
        """Pick a new random position near the target"""
        while True:  # Keep trying until we get a valid position
            # First, get a base position relative to player
            base_y = target.position.y - self.random((100, 300))  # Tend to stay above player
            
            # Get horizontal offset (left or right of player)
            offset_x = self.random((-1, 1), choice=True) * self.random((200, 400))
            
            # Set new target position
            new_pos_x = target.position.x + offset_x
            new_pos_y = base_y
            
            # Ensure minimum height from ground
            min_height = C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - self.height - 100
            if new_pos_y > min_height:
                new_pos_y = min_height
            
            # Ensure maximum height (optional, remove if you want it to go higher)
            max_height = 100
            if new_pos_y < max_height:
                new_pos_y = max_height
            
            # Set the position
            self.target_pos.x = new_pos_x
            self.target_pos.y = new_pos_y
            
            # If position is valid (not too close to current position), break
            if Vector2(self.target_pos - self.position).length() > 100:
                break
        
        # Reset flag
        self.needs_new_target = False
    
    def shoot_radial(self, target=None):
        """Shoot projectiles in a radial pattern"""

        pr = self.ATTACK_INFOS['radial']
        def shoot_radial_layer(inerval_deg, offset_deg=0):
            for angle in range(0, 360, inerval_deg):
                rad_angle = math.radians(angle + offset_deg)
                velocity = Vector2(math.cos(rad_angle), math.sin(rad_angle)) * pr['speed']
                projectile = P_Ball(position=copy.deepcopy(self.position), 
                                    velocity=velocity, 
                                    speed_multiplier=pr['speed_mul'], 
                                    damage=self.ATTACK_INFOS['damage'],
                                    game=self.game)
                self.game.groups['bullets'].add(projectile)
                self.game.groups['all'].add(projectile)

        if self.attack_phase == 0:
            # First round
            shoot_radial_layer(15, 0)
            self.attack_phase = 1
            self.attack_timer.start(pr['delay'])
            return False
            
        elif self.attack_phase == 1:
            if not self.attack_timer.is_completed:
                return False
            shoot_radial_layer(15, 7.5)
            
            return True
    
    def shoot_burst(self, target):
        """Shoot burst of projectiles towards target"""
        if self.shots_fired >= 3:
            return True
            
        if not self.attack_timer.is_completed:
            return False
            
        # Calculate base direction to target
        to_target = target.position - self.position
        base_angle = math.degrees(math.atan2(to_target.y, to_target.x))
        pb = self.ATTACK_INFOS['burst']
        # Fire 4 projectiles with spread
        for _ in range(4):
            spread = self.random((-pb['spread'], pb['spread']))
            angle = math.radians(base_angle + spread)
            velocity = Vector2(math.cos(angle), math.sin(angle)) * pb['speed']
            projectile = P_Ball(position=copy.deepcopy(self.position), 
                                velocity=velocity, 
                                speed_multiplier=pb['speed_mul'], 
                                damage=self.ATTACK_INFOS['damage'],
                                game=self.game)
            self.game.groups['bullets'].add(projectile)
            self.game.groups['all'].add(projectile)
        
        self.shots_fired += 1
        self.attack_timer.start(pb['delay'])
        return False
    
    def shoot_follow(self, target):
        """Rapid fire projectiles that follow the target"""
        if self.shots_fired >= 10:
            return True
            
        if not self.attack_timer.is_completed:
            return False
            
        # Calculate direction to target's current position
        to_target = target.position - self.position
        pf = self.ATTACK_INFOS['follow']

        if to_target.length() > 0:
            direction = to_target.normalize()
            velocity = direction * pf['speed']
            projectile = P_Ball(position=copy.deepcopy(self.position), 
                                velocity=velocity, 
                                speed_multiplier=pf['speed_mul'], 
                                damage=self.ATTACK_INFOS['damage'],
                                game=self.game)
            self.game.groups['bullets'].add(projectile)
            self.game.groups['all'].add(projectile)
        
        self.shots_fired += 1
        self.attack_timer.start(pf['delay'])
        return False
    
    def start_attack(self):
        """Initialize a random attack pattern"""
        self.is_attacking = True
        self.attack_phase = 0
        self.attack_timer.reset()
        self.shots_fired = 0
        self.current_attack = self.random((self.shoot_radial, self.shoot_burst, self.shoot_follow), choice=True)
        self.anim.change_state("attack")
    
    def ai_logic(self, target):
        """Move towards target position with easing"""
        self.facing_right = target.position.x > self.position.x
        
        # Handle attacking state
        if self.is_attacking:
            if self.current_attack(target):
                self.is_attacking = False
                self.wait_timer.start(self.random(self.WAIT_DURATION))
                self.needs_new_target = True
            return
        
        # Waiting
        if not self.wait_timer.is_completed:
            self.anim.change_state("idle")
            return
        
        # Start Moving
        if self.needs_new_target:
            self.pick_new_position(target)
            self.start_pos = Vector2(self.position)
            self.move_timer.start(self.random(self.MOVE_DURATION))
            self.needs_new_target = False
            
        # Moving
        if not self.move_timer.is_completed:
            t = self.move_timer.progress
            eased_t = self.ease_in_out_sine(t)
            self.position = self.start_pos.lerp(self.target_pos, eased_t)
            self.velocity = (self.target_pos - self.start_pos).normalize() * self.MOVE_SPEED
            self.anim.change_state("move")
            
        # Finished moving
        if self.move_timer.is_completed and not self.is_attacking:
            self.start_attack()
        
        self.rect.center = self.position

