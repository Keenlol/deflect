import pygame
import os
from pygame.math import Vector2
from config import Config as C
from projectile import *
from animation import Animation
from timer import Timer
from datetime import datetime
from stats import Stats
from sounds import Sounds

import random
import math
import copy

class Enemy(pygame.sprite.Sprite):
    MOVE_DURATION = (1.0, 3.0)  
    WAIT_DURATION = (1.0, 3.0)
    HURT_DURATION = 1/6
    KNOCKBACK_DECAY = 0.95
    
    def __init__(self, x, y, game, anim={"path":"", "loops": {}, "speed": 0.2}, 
                 width=100, height=100, maxhp=100, movespeed=3, 
                 gravity=0.8, maxfallspeed=15, bodydamage=30, name=''):
        super().__init__()
        self.__tag = {'name': name,
                      'spawn_time': datetime.now()}

        # Basic attributes
        self.width = width
        self.height = height
        self.anim = Animation(self, anim['path'], anim['loops'], anim['speed'])
        self.facing_right = True
        
        # Physics attributes
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)
        self.on_ground = False
        
        # Combat attributes
        self.MAX_HEALTH = maxhp
        self.health = self.MAX_HEALTH
        self.is_hurt = False
        self.BODY_DAMAGE = bodydamage
        self.is_attacking = False
        
        # Movement attributes
        self.MOVE_SPEED = movespeed
        self.GRAVITY = gravity
        self.MAX_FALL_SPEED = maxfallspeed
        
        # Timer attributes
        self.move_timer = None
        self.wait_timer = None
        self.attack_timer = None
        self.hurt_timer = Timer(duration=self.HURT_DURATION, owner=self, paused=True)
        
        # Attack attributes
        self.current_attack = None
        self.attack_infos = {}
        
        # State attributes
        self.is_alive = True
        self.is_knocked_back = False
        
        # Game reference
        self.game = game
        self.target = game.player

        # Knockback
        self.knockback_velocity = Vector2(0, 0)

        self.image = self.anim.get_current_frame(self.facing_right)
        self.rect = pygame.Rect(x, y, self.width, self.height)

    @property
    def name(self):
        return self.__tag['name']
    
    @property
    def lifespan(self):
        difference = datetime.now() - self.__tag['spawn_time']
        return difference.total_seconds()

    def init_timers(self, move_duration=None, wait_duration=None, attack_duration=0):
        """Initialize common timers with appropriate durations"""
        move_dur = move_duration if move_duration is not None else self.MOVE_DURATION
        wait_dur = wait_duration if wait_duration is not None else self.WAIT_DURATION
        
        self.move_timer = Timer(duration=self.random(move_dur), owner=self, paused=True)
        self.wait_timer = Timer(duration=self.random(wait_dur), owner=self, paused=True)
        self.attack_timer = Timer(duration=attack_duration, owner=self, paused=True)
    
    def start_waiting(self, duration=None):
        """Start waiting timer with optional custom duration"""
        wait_dur = duration if duration is not None else self.random(self.WAIT_DURATION)
        self.wait_timer.start(wait_dur)
        self.anim.change_state("idle")
    
    def start_movement(self, duration=None):
        """Start movement timer with optional custom duration"""
        move_dur = duration if duration is not None else self.random(self.MOVE_DURATION)
        self.move_timer.start(move_dur)
        self.anim.change_state("move")
    
    @staticmethod
    def random(values:tuple, choice=False):
        if not choice:
            if isinstance(values[0], int):
                return random.randint(values[0], values[1])
            return random.uniform(values[0], values[1])
        else:
            return random.choice(values)

    def update_animation(self):
        self.anim.update()
        self.image = self.anim.get_current_frame(self.facing_right)

    def take_damage(self, amount):
        Sounds().play_sound_random(['enemy_damaged1', 'enemy_damaged2'])
        self.health -= amount
        self.game.freeze_and_shake(0, 3, 5)
        if self.is_alive:
            if self.health <= 0:
                self.health = 0
                self.is_alive = False
                self.anim.change_state("death")
            else:
                self.is_hurt = True
                self.hurt_timer.start()
                self.anim.change_state("hurt")
        
    def attack(self, target):
        """Base attack method to be overridden by child classes"""
        pass
    
    def ai_logic(self, target):
        """Base movement method to be overridden by child classes"""
        pass
    
    def apply_physics(self):
        # Apply gravity
        if not self.on_ground:
            self.velocity.y += self.GRAVITY
            self.velocity.y = min(self.velocity.y, self.MAX_FALL_SPEED)
        
        self.position += self.velocity
        
        # Floor collision
        if self.position.y + self.height/2 > C.WINDOW_HEIGHT - C.FLOOR_HEIGHT:
            self.position.y = C.WINDOW_HEIGHT - C.FLOOR_HEIGHT - self.height/2
            self.velocity.y = 0
            self.on_ground = True
        else:
            self.on_ground = False
        
        self.rect.center = self.position
    
    def check_projectile_collisions(self):
        for bullet in self.game.groups['bullets']:
            if bullet.is_deflected:
                distance = (bullet.position - self.position).length()
                if distance < self.width/2:
                    self.take_damage(bullet.damage)
                    self.start_knockback(bullet.velocity, bullet.velocity.length() * 0.1)
                    
                    # If the bullet has a deflect_id, record the damage for this deflection batch
                    if hasattr(bullet, '_Projectile__tag') and 'deflect_id' in bullet._Projectile__tag:
                        deflect_id = bullet._Projectile__tag['deflect_id']
                        # Find player knife to add damage to deflection batch
                        if self.game and self.game.player and self.game.player.knife:
                            self.game.player.knife.record_deflected_damage(deflect_id, bullet.damage)
                    
                    bullet.kill()

    def start_knockback(self, direction, amount):
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = Vector2(1, 0)
        
        self.knockback_velocity = direction * amount
        self.is_knocked_back = True
    
    def update_knockback(self):
        if self.is_knocked_back:
            self.position += self.knockback_velocity
            self.knockback_velocity *= self.KNOCKBACK_DECAY
            
            if self.knockback_velocity.length() < 0.1:
                self.knockback_velocity = Vector2(0, 0)
                self.is_knocked_back = False
    
    def update(self):
        if not self.is_alive:
            self.update_animation()
            if self.anim.current_state == "death" and self.anim.animation_finished:
                self.kill()
            return
            
        if self.is_hurt and self.hurt_timer.is_completed:
            self.is_hurt = False
            self.anim.change_state("idle")
        
        if self.target and not self.is_hurt:
            self.ai_logic(self.target)
        
        self.update_knockback()
        self.apply_physics()
        self.check_projectile_collisions()
        self.update_animation()

    def kill(self):
        self.game.score += 150
        self.game.enemies_killed += 1
        Stats().record(stat_type='enemy_lifespan',
                     enemy_type=self.name,
                     lifespan_sec=self.lifespan)
        super().kill()

    # def die(self):
    #     """Die and perform cleanup"""
    #     self.alive = False
    #     self.health = 0
    #     self.anim.change_state("death")
        
    #     # Record death time for lifespan statistics
    #     if not self.death_recorded:
    #         self.death_recorded = True
            
    #         # Record death time and calculate lifespan
    #         now = datetime.now()
    #         lifespan_sec = (now - self.spawn_time).total_seconds()
            
    #         # Record statistics
    #         Stats().record('enemy_lifespan', 
    #                       enemy_type=self.name,
    #                       lifespan_sec=lifespan_sec)
            
    #         # Register the kill with the game
    #         if self.game:
    #             self.game.enemies_killed += 1

