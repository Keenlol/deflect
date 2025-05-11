from enemy_all import *

class E3(Enemy):
    # Movement constants
    TARGET_DISTANCE = (300, 500)
    DISTANCE_TOLERANCE = 75
    ACCELERATION_RANGE = (0.01, 0.05)
    DECELERATION = 0.05
    
    # Bobbing constants
    BOB_FREQUENCY = 0.5  # How many cycles per second
    BOB_AMPLITUDE = 15   # How many pixels up/down
    
    # Timer durations
    AIM_DURATION = 1.5  # Fixed aim duration
    AIM_COOLDOWN = (3.0, 5.0)  # Random cooldown between aims
    
    # Attack info
    ATTACK_INFO = {
        'bounce': {
            'speed': 20, 
            'bounce_limit': 5, 
            'damage': 35, 
            'size': 8
        },
        'bomb': {
            'initial_speed': 40,
            'speed_mul': 0.9,  # Slows down over time
            'explosion_threshold': 1.5,  # Speed threshold for explosion
            'explosion_count': 18,  # Number of lasers in explosion
            'explosion_speed': 15,
            'explosion_speed_mul': 0.95,
            'initial_damage': 20,
            'explosion_damage': 3,
            'initial_size': 12,
            'explosion_size': 8
        },
        'homing': {
            'count': 5,  # Number of homing lasers to fire
            'delay': 0.1,  # Delay between shots in seconds
            'speed': (7.0, 9.0),
            'turn_rate': (0.5, 4.0),  # Degrees per frame
            'damage': 25,
            'size': 8
        }
    }
    
    def __init__(self, x, y, game):
        # Animation setup
        loops = {
            "idle": True,
            "aim": True,
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
                         height=100, gravity=0.0, movespeed=self.random((0.5, 2.0)), 
                         maxhp=40, anim=anim_info, name='Gunman')

        # Movement attributes
        self.target_dst = self.random(self.TARGET_DISTANCE)
        self.acceleration = self.random(self.ACCELERATION_RANGE)
        self.current_speed = 0  # Track current speed for smooth acceleration
        
        # Initialize timers
        self._init_timers()
        self.aim_timer = Timer(duration=self.AIM_DURATION, owner=self, paused=True)
        self.aim_cooldown_timer = Timer(duration=self.random(self.AIM_COOLDOWN), owner=self, paused=True)
        self.aim_cooldown_timer.start()
        
        # Bobbing setup
        self.bobbing_timer = Timer(duration=1/self.BOB_FREQUENCY, owner=self, auto_reset=True)
        self.bobbing_timer.start()
        self.bob_offset = 0
        
        # Attack state tracking
        self.shots_fired = 0
        self.is_aiming = False
        
    def _update_animation(self):
        super()._update_animation()
        if self.is_alive:
            # Calculate bobbing effect using timer progress
            self.bob_offset = self.BOB_AMPLITUDE * math.sin(self.bobbing_timer.progress * 2 * math.pi)
            
            # Apply bobbing to position only for rendering, not physics
            self.rect.center = (self.position.x, self.position.y + self.bob_offset)

    def ai_logic(self, target):
        self.facing_right = True if target.position.x > self.position.x else False
        
        # Handle aiming and attacking
        if self.is_aiming:
            # Stop movement while aiming
            self.current_speed = 0
            self.velocity = Vector2(0, 0)
            self._anim.change_state("aim")
            
            # Check if aim duration is complete
            if self.aim_timer.just_completed:
                self.is_aiming = False
                self.is_attacking = True
                self._anim.change_state("attack")
                # Reset shots_fired before selecting an attack
                self.shots_fired = 0
                # Randomly choose between the three attacks
                self.current_attack = self.random((self.fire_laser, self.fire_bomb, self.fire_homing), choice=True)
                self.current_attack(target)
        elif self.is_attacking:
            # Stay still during attack
            self.current_speed = 0
            self.velocity = Vector2(0, 0)
            
            # If we have a current attack that returns false, continue it
            if self.current_attack and not self.current_attack(target):
                return
                
            # Attack animation will play and then return to idle
            if self._anim.animation_finished:
                self.is_attacking = False
                self.aim_cooldown_timer.start(self.random(self.AIM_COOLDOWN))
                self.current_attack = None
        else:
            # Normal movement when not aiming or attacking
            to_player = target.position - self.position
            current_distance = to_player.length()
            
            # Handle horizontal movement based on distance
            if abs(current_distance - self.target_dst) > self.DISTANCE_TOLERANCE:
                direction = to_player.normalize()
                
                if current_distance < self.target_dst:
                    direction = -direction
                
                self.current_speed = min(self.current_speed + self.acceleration, self.MOVE_SPEED)
                
                self.velocity = direction * self.current_speed
                self.position += self.velocity
                
                self._anim.change_state("idle")
            else:
                self.current_speed *= (1 - self.DECELERATION)
                
                if self.current_speed < 0.1:
                    self.current_speed = 0
                    self.velocity = Vector2(0, 0)
                else:
                    self.velocity = self.velocity.normalize() * self.current_speed
                    self.position += self.velocity
                    
                self._anim.change_state("idle")
            
            # Check if it's time to start aiming
            if self.aim_cooldown_timer.just_completed:
                Sounds().play_sound('e3_aim')
                self.is_aiming = True
                self.aim_timer.start()

    def fire_bomb(self, target):
        if self.shots_fired > 0:
            return True
            
        to_target = target.position - self.position
        direction = to_target.normalize()
        
        bomb_info = self.ATTACK_INFO['bomb']
        gun_position = Vector2(self.position.x + (self.width/2 if self.facing_right else -self.width/2), 
                             self.position.y)

        Laser(position=gun_position, 
              velocity=direction * bomb_info['initial_speed'],
              game=self.game,
              damage=bomb_info['initial_damage'], 
              radius=bomb_info['initial_size'],
              speed_multiplier=bomb_info['speed_mul'],
              laser_type='bomb',
              bomb_info=bomb_info,
              attack_name='Gunman Exploding-Laser')

        self.shots_fired = 1
        Sounds().play_sound_random(['e3_shoot1', 'e3_shoot2'])
        return True

    def fire_homing(self, target):
        homing_info = self.ATTACK_INFO['homing']
        
        if not self._attack_timer.is_completed:
            return False
        
        if self.shots_fired >= homing_info['count']:
            self.shots_fired = 0
            return True
        
        to_target = target.position - self.position
        direction = to_target.normalize()
        
        gun_position = Vector2(self.position.x + (self.width/2 if self.facing_right else -self.width/2), 
                             self.position.y)
        Sounds().play_sound_random(['e3_shoot1', 'e3_shoot2'])
        Laser(position=gun_position, 
              velocity=direction * self.random(homing_info['speed']),
              game=self.game,
              damage=homing_info['damage'], 
              radius=homing_info['size'], 
              laser_type='homing', 
              target=target,
              turn_rate=self.random(homing_info['turn_rate']),
              attack_name='Gunman Homing-Laser')
        
        self.shots_fired += 1
        self._attack_timer.start(homing_info['delay'])
        Sounds().play_sound_random(['e3_shoot1', 'e3_shoot2'])
        return False

    def fire_laser(self, target):
        if self.shots_fired > 0:
            return True

        to_target = target.position - self.position
        direction = to_target.normalize()

        if self.facing_right:
            gun_position = Vector2(self.position.x + self.width/2, self.position.y)
        else:
            gun_position = Vector2(self.position.x - self.width/2, self.position.y)
            
        bounce_info = self.ATTACK_INFO['bounce']
        Laser(position=gun_position, 
              velocity=direction * bounce_info['speed'], 
              game=self.game,
              damage=bounce_info['damage'], 
              radius=bounce_info['size'], 
              bounce_limit=bounce_info['bounce_limit'],
              attack_name='Gunman Bouncing-Laser')

        self.shots_fired = 1
        Sounds().play_sound_random(['e3_shoot1', 'e3_shoot2'])
        return True
