import pygame
import os
from config import Config as C

class Animation:
    def __init__(self, sprite_owner, base_path, states, animation_speed=0.1):
        """
        Initialize animation system
        
        Args:
            sprite_owner: The sprite this animation belongs to
            base_path: Path to animation folder (e.g., 'sprites/player' or 'sprites/enemies/e1')
            states: Dictionary of animation states and whether they loop (e.g., {'idle': True})
            animation_speed: Speed of animation playback
        """
        # Owner reference and basic attributes
        self.owner = sprite_owner
        self.base_path = base_path
        
        # Animation state handling
        self.animations = {}  # Stores animation frames for each state
        self.animation_loops = states  # Which animations should loop
        self.current_state = list(states.keys())[0]  # Default to first state
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = animation_speed
        self.animation_finished = False
        
        # Load all animations
        self.load_animations()
    
    def load_animations(self):
        """Load all animation frames from their respective folders"""
        for state in self.animation_loops.keys():
            self.animations[state] = []
            path = os.path.join(self.base_path, state)
            
            try:
                files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
                for file in files:
                    try:
                        img = pygame.image.load(os.path.join(path, file)).convert_alpha()
                        img = pygame.transform.scale(img, (self.owner.width, self.owner.height))
                        self.animations[state].append(img)
                    except pygame.error:
                        print(f"Error loading animation frame: {file} in {state}")
                        continue
                        
                # Create default frame if no frames were loaded
                if not self.animations[state]:
                    default_frame = pygame.Surface((self.owner.width, self.owner.height))
                    default_frame.fill((255, 255, 255))  # White default
                    self.animations[state].append(default_frame)
                    
            except FileNotFoundError:
                print(f"Animation folder not found: {path}")
                default_frame = pygame.Surface((self.owner.width, self.owner.height))
                default_frame.fill((255, 255, 255))  # White default
                self.animations[state].append(default_frame)
    
    def change_state(self, new_state):
        """Change animation state and reset frame counter"""
        if new_state in self.animation_loops and new_state != self.current_state:
            self.current_state = new_state
            self.current_frame = 0
            self.animation_timer = 0
            self.animation_finished = False
    
    def update(self):
        """Update animation frame"""
        if not self.animations[self.current_state]:
            return
            
        self.animation_timer += 1
        
        if self.animation_timer >= C.FPS * self.animation_speed:
            self.animation_timer = 0
            if self.animation_loops[self.current_state]:
                # Looping animations
                self.current_frame = (self.current_frame + 1) % len(self.animations[self.current_state])
            else:
                # Non-looping animations
                if not self.animation_finished:
                    if self.current_frame < len(self.animations[self.current_state]) - 1:
                        self.current_frame += 1
                    else:
                        self.animation_finished = True
        
        # Ensure current_frame is within bounds
        self.current_frame = min(self.current_frame, len(self.animations[self.current_state]) - 1)
    
    def get_current_frame(self, facing_right=True):
        """Get current animation frame with proper facing direction"""
        frame = self.animations[self.current_state][self.current_frame]
        if not facing_right:
            frame = pygame.transform.flip(frame, True, False)
        return frame