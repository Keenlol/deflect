from enemy_all import *
from timer import Timer
from sounds import Sounds

class E1(Enemy):
    # Attack properties
    ATTACK_INFO = {
        'radial': {'speed': 8, 'speed_mul': 1, 'delay': 5/60, 'damage': 25},
        'burst': {'speed': 20, 'speed_mul': 0.95, 'delay': 10/60, 'spread': 20, 'damage': 30},
        'follow': {'speed': 0.1, 'speed_mul': 1.05, 'delay': 5/60, 'damage': 35},
        'radius': 10
    }
    
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
                         maxhp=40, anim=anim_info, name='Wizard')

        # Movement attributes
        self.start_pos = Vector2(x, y)
        self.target_pos = Vector2(x, y)
        
        # Initialize timers
        self.init_timers()
        
        # Attack attributes
        self.needs_new_pos = True
        self.attack_phase = 0
        self.shots_fired = 0

        # Start in waiting state
        self.start_waiting()

    def ease_in_out_sine(self, t):
        """Sine easing function for smooth movement"""
        return -(math.cos(math.pi * t) - 1) / 2
    
    def pick_new_position(self, target):
        """Pick a new random position near the target"""
        while True:
            base_y = target.position.y - self.random((100, 300))  # Tend to stay above player
            offset_x = self.random((-1, 1), choice=True) * self.random((200, 400))
            
            new_pos_x = target.position.x + offset_x
            new_pos_y = base_y
            
            min_height = C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - self.height - 100
            if new_pos_y > min_height:
                new_pos_y = min_height
            
            max_height = 100
            if new_pos_y < max_height:
                new_pos_y = max_height
            
            self.target_pos.x = new_pos_x
            self.target_pos.y = new_pos_y
            
            if Vector2(self.target_pos - self.position).length() > 100:
                break
        
        self.needs_new_pos = False
    
    def shoot_radial(self, target=None):
        """Shoot projectiles in a radial pattern"""
        pr = self.ATTACK_INFO['radial']
        def shoot_radial_layer(inerval_deg, offset_deg=0):
            Sounds().play_sound('e1_radial')
            for angle in range(0, 360, inerval_deg):
                rad_angle = math.radians(angle + offset_deg)
                velocity = Vector2(math.cos(rad_angle), math.sin(rad_angle)) * pr['speed']
                P_Ball(position=copy.deepcopy(self.position), 
                       velocity=velocity, 
                       game=self.game,
                       damage=self.ATTACK_INFO['radial']['damage'],
                       speed_multiplier=pr['speed_mul'],
                       attack_name='Wizard Radial-Cast')

        # First layer
        if self.attack_phase == 0:
            shoot_radial_layer(15, 0)
            self.attack_phase = 1
            self.attack_timer.start(pr['delay'])
            return False
        
        # Second layer
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
        pb = self.ATTACK_INFO['burst']

        # Fire 4 projectiles with spread
        for _ in range(4):
            spread = self.random((-pb['spread'], pb['spread']))
            angle = math.radians(base_angle + spread)
            velocity = Vector2(math.cos(angle), math.sin(angle)) * pb['speed']
            P_Ball(position=copy.deepcopy(self.position), 
                   velocity=velocity, 
                   game=self.game,
                   damage=self.ATTACK_INFO['burst']['damage'],
                   speed_multiplier=pb['speed_mul'],
                   attack_name='Wizard Burst-Cast ')
        
        self.shots_fired += 1
        self.attack_timer.start(pb['delay'])
        Sounds().play_sound_random(['e1_cast1', 'e1_cast2'])
        return False
    
    def shoot_follow(self, target):
        """Rapid fire projectiles that follow the target"""
        if self.shots_fired >= 10:
            return True
            
        if not self.attack_timer.is_completed:
            return False

        # Calculate direction to target's current position
        to_target = target.position - self.position
        pf = self.ATTACK_INFO['follow']

        if to_target.length() > 0:
            direction = to_target.normalize()
            velocity = direction * pf['speed']
            P_Ball(position=copy.deepcopy(self.position), 
                   velocity=velocity, 
                   game=self.game,
                   damage=self.ATTACK_INFO['follow']['damage'],
                   speed_multiplier=pf['speed_mul'],
                   attack_name='Wizard Track-Cast')
        
        self.shots_fired += 1
        self.attack_timer.start(pf['delay'])
        Sounds().play_sound_random(['e1_cast1', 'e1_cast2'])
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
                self.start_waiting()
                self.needs_new_pos = True
            return
        
        # Waiting
        if not self.wait_timer.is_completed:
            self.anim.change_state("idle")
            return
        
        # Start Moving
        if self.needs_new_pos:
            self.pick_new_position(target)
            self.start_pos = Vector2(self.position)
            self.start_movement()
            self.needs_new_pos = False
            
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

