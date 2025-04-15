from enemy_all import *

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
        self.move_timer = 0
        self.move_duration = 3.0  # seconds to reach target
        self.wait_timer = 0
        self.WAIT_TIME_MIN = 1.0
        self.WAIT_TIME_MAX = 5.0
        self.needs_new_target = True
        
        # Remove acceleration/deceleration as we'll use easing instead

        self.attack_info = {'radial': {'speed': 8, 'speed_mul': 1, 'delay': 5},
                                'burst': {'speed': 20, 'speed_mul': 0.95, 'delay': 10, 'spread':20},
                                'follow': {'speed': 0.1, 'speed_mul': 1.05, 'delay': 5},
                                'damage': 33,
                                'radius': 10}
        
        # Attack pattern attributes
        self.attack_timer = 0
        self.attack_phase = 0
        self.is_attacking = False
        self.current_attack = None
        self.shots_fired = 0

    def ease_in_out_sine(self, t):
        """Sine easing function for smooth movement"""
        return -(math.cos(math.pi * t) - 1) / 2
    
    def pick_new_position(self, target):
        """Pick a new random position near the target"""
        while True:  # Keep trying until we get a valid position
            # First, get a base position relative to player
            base_y = target.position.y - random.uniform(100, 300)  # Tend to stay above player
            
            # Get horizontal offset (left or right of player)
            offset_x = random.choice([-1, 1]) * random.uniform(200, 400)
            
            # Set new target position
            new_pos_x = target.position.x + offset_x
            new_pos_y = base_y
            
            # Ensure minimum height from ground
            min_height = C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - self.height - 100
            if new_pos_y > min_height:
                new_pos_y = min_height
            
            # Ensure maximum height (optional, remove if you want it to go higher)
            max_height = 100  # 100 pixels from top of screen
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

        pr = self.attack_info['radial']
        def shoot_radial_layer(inerval_deg, offset_deg=0):
            for angle in range(0, 360, inerval_deg):
                rad_angle = math.radians(angle + offset_deg)
                velocity = Vector2(math.cos(rad_angle), math.sin(rad_angle)) * pr['speed']
                projectile = P_Ball(copy.deepcopy(self.position), velocity, pr['speed_mul'], self.attack_info['damage'])
                self.game.groups['bullets'].add(projectile)
                self.game.groups['all'].add(projectile)

        if self.attack_phase == 0:
            # First round
            shoot_radial_layer(15, 0)
            self.attack_phase = 1
            self.attack_timer = pr['delay']
            return False
            
        elif self.attack_phase == 1:
            if self.attack_timer > 0:
                self.attack_timer -= 1
                return False
            shoot_radial_layer(15, 7.5)
            
            return True
    
    def shoot_burst(self, target):
        """Shoot burst of projectiles towards target"""
        if self.shots_fired >= 3:
            return True
            
        if self.attack_timer > 0:
            self.attack_timer -= 1
            return False
            
        # Calculate base direction to target
        to_target = target.position - self.position
        base_angle = math.degrees(math.atan2(to_target.y, to_target.x))
        pb = self.attack_info['burst']
        # Fire 4 projectiles with spread
        for _ in range(4):
            spread = random.uniform(-pb['spread'], pb['spread'])
            angle = math.radians(base_angle + spread)
            velocity = Vector2(math.cos(angle), math.sin(angle)) * pb['speed']
            projectile = P_Ball(copy.deepcopy(self.position), velocity, pb['speed_mul'], self.attack_info['damage'])
            self.game.groups['bullets'].add(projectile)
            self.game.groups['all'].add(projectile)
        
        self.shots_fired += 1
        self.attack_timer = pb['delay']
        return False
    
    def shoot_follow(self, target):
        """Rapid fire projectiles that follow the target"""
        if self.shots_fired >= 10:
            return True
            
        if self.attack_timer > 0:
            self.attack_timer -= 1
            return False
            
        # Calculate direction to target's current position
        to_target = target.position - self.position
        pf = self.attack_info['follow']

        if to_target.length() > 0:
            direction = to_target.normalize()
            velocity = direction * pf['speed']
            projectile = P_Ball(copy.deepcopy(self.position), velocity, pf['speed_mul'], self.attack_info['damage'])
            self.game.groups['bullets'].add(projectile)
            self.game.groups['all'].add(projectile)
        
        self.shots_fired += 1
        self.attack_timer = pf['delay']
        return False
    
    def start_attack(self):
        """Initialize a random attack pattern"""
        self.is_attacking = True
        self.attack_phase = 0
        self.attack_timer = 0
        self.shots_fired = 0
        self.current_attack = random.choice([self.shoot_radial, self.shoot_burst, self.shoot_follow])
        self.anim.change_state("attack")
    
    def ai_logic(self, target):
        """Move towards target position with easing"""
        # Always face the player
        self.facing_right = target.position.x > self.position.x
        
        # Handle attacking state
        if self.is_attacking:
            if self.current_attack(target):
                self.is_attacking = False
                self.wait_timer = random.uniform(self.WAIT_TIME_MIN, self.WAIT_TIME_MAX)
                self.needs_new_target = True
            return
        
        # Handle waiting
        if self.wait_timer > 0:
            self.wait_timer -= 1/C.FPS
            self.anim.change_state("idle")
            return
        
        # Start new movement
        if self.needs_new_target:
            self.pick_new_position(target)
            self.start_pos = Vector2(self.position)
            self.move_timer = 0
            self.needs_new_target = False
            
        # Update movement
        if self.move_timer < self.move_duration:
            # Calculate progress with sine easing
            t = self.move_timer / self.move_duration
            eased_t = self.ease_in_out_sine(t)
            
            # Interpolate position
            self.position = self.start_pos.lerp(self.target_pos, eased_t)
            
            # Calculate velocity for animation purposes
            self.velocity = (self.target_pos - self.start_pos).normalize() * self.MOVE_SPEED
            
            self.move_timer += 1/C.FPS
            self.anim.change_state("move")
            
            # Check if we've reached the target
            if self.move_timer >= self.move_duration:
                self.start_attack()
        
        # Update rect position
        self.rect.center = self.position
