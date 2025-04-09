import pygame
from pygame.math import Vector2
from animation import Animation

class UI(pygame.sprite.Sprite):
    def __init__(self, position: Vector2, width: int, height: int):
        super().__init__()
        self.position = Vector2(position)
        self.width = width
        self.height = height
        
        # Create base surface
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=self.position)
        
        # Layer system
        self.layers = []  # List of surfaces to be blitted in order
        
        # State
        self.visible = True
        self.active = True
    
    def add_layer(self, surface: pygame.Surface, position: Vector2 = None):
        """Add a new layer to be rendered"""
        if position is None:
            position = Vector2(0, 0)
        self.layers.append((surface, position))
    
    def clear_layers(self):
        """Clear all layers"""
        self.layers.clear()
    
    def update(self):
        """Update UI element"""
        if not self.active:
            return
            
        # Clear surface
        self.image.fill((0, 0, 0, 0))
        
        # Draw all layers in order
        for surface, position in self.layers:
            self.image.blit(surface, position)
    
    def set_position(self, position: Vector2):
        """Set UI element position"""
        self.position = Vector2(position)
        self.rect.topleft = self.position

class HealthBar(UI):
    def __init__(self, position: Vector2, width: int, height: int, target=None):
        super().__init__(position, width, height)
        self.target = target  # Reference to the entity whose health we're tracking
        
        # Animation states for both layers
        animation_states = {
            "empty": True,
            "full": True
        }
        
        # Create background layer animation (empty bar)
        self.bg_anim = Animation(self, "sprites/ui_healthbar", animation_states, animation_speed=0)
        self.bg_anim.change_state("empty")
        
        # Create foreground layer animation (full bar)
        self.fg_anim = Animation(self, "sprites/ui_healthbar", animation_states, animation_speed=0)
        self.fg_anim.change_state("full")
        
        # Create mask surface for health percentage
        self.mask_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        self.BAR_MASK_CORRECTION = (0.2,0.988)

        # Initial setup
        self.update_health_mask()
    
    def update_health_mask(self):
        """Update the mask surface based on current health percentage"""
        if not self.target:
            return
            
        # Calculate health percentage
        health_percent = max(0, min(1, self.target.health / self.target.MAX_HEALTH))
        
        # Clear mask surface
        self.mask_surface.fill((0, 0, 0, 0))
        
        pre = self.BAR_MASK_CORRECTION[0]
        post = self.BAR_MASK_CORRECTION[1]
        # Draw the mask rectangle (white part will show the health bar)
        mask_width = int(self.width * (pre + health_percent * (post - pre)))
        pygame.draw.rect(self.mask_surface, (255, 255, 255, 255), 
                        (0, 0, mask_width, self.height))
    
    def update(self):
        """Update health bar appearance"""
        if not self.active or not self.target:
            return
            
        # Update animations
        self.bg_anim.update()
        self.fg_anim.update()
        
        # Clear main surface
        self.image.fill((0, 0, 0, 0))
        
        # Draw background (empty) health bar
        bg_frame = self.bg_anim.get_current_frame()
        self.image.blit(bg_frame, (0, 0))
        
        # Get foreground (full) health bar
        fg_frame = self.fg_anim.get_current_frame()
        
        # Create a copy of the full health bar to mask
        masked_fg = fg_frame.copy()
        
        # Update and apply the mask
        self.update_health_mask()
        masked_fg.blit(self.mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Draw the masked foreground
        self.image.blit(masked_fg, (0, 0))


