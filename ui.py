import pygame
from pygame.math import Vector2
from animation import Animation
import math
from config import Config as C

class UI(pygame.sprite.Sprite):
    def __init__(self, position: Vector2, width: int, height: int):
        super().__init__()
        self.position = Vector2(position)
        self.width = width
        self.height = height
        
        # Create base surface
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.position)
        
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
        """Set UI element position (center)"""
        self.position = Vector2(position)
        self.rect.center = self.position

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

class Button(UI):
    def __init__(self, position: Vector2, width: int, height: int, text: str, 
                 callback=None, idle_color=(200, 200, 200), hover_color=(255, 255, 255),
                 bg_color=(0, 0, 0, 0), text_size=32):
        super().__init__(position, width, height)
        
        # Button specific attributes
        self.original_width = width
        self.original_height = height
        self.text = text
        self.callback = callback
        self.idle_color = idle_color        # Text color when not hovered
        self.hover_color = hover_color      # Text color when hovered
        self.bg_color = bg_color            # Background color (with alpha)
        self.text_size = text_size
        
        # Animation properties
        self.is_hovered = False
        self.hover_progress = 0.0  # 0.0 to 1.0
        self.hover_direction = 0   # 1 for hovering, -1 for un-hovering, 0 for idle
        self.hover_duration = 0.25  # seconds for hover animation (reduced by half)
        self.unhover_duration = 0.5  # seconds for un-hover animation (reduced by half)
        self.hover_scale = 1.1     # scale factor when fully hovered
        
        # Initialize font - use cached font if possible
        if not hasattr(Button, 'font_cache'):
            Button.font_cache = {}
        
        if text_size not in Button.font_cache:
            try:
                Button.font_cache[text_size] = pygame.font.Font("fonts/Jua-Regular.ttf", text_size)
            except FileNotFoundError:
                # Fallback to default font if file not found
                Button.font_cache[text_size] = pygame.font.Font(None, text_size)
        
        self.font = Button.font_cache[text_size]
        
        # Initial render
        self.render()
    
    def circ_ease_out(self, t):
        """Circular easing out function for smooth animations"""
        t = max(0, min(1, t))  # Clamp t between 0 and 1
        return math.sqrt(1 - pow(t - 1, 2))
    
    def render(self):
        """Render the button with current state"""
        # Clear the surface
        self.image.fill((0, 0, 0, 0))
        
        # Calculate current size and color based on hover progress
        ease_factor = 0
        if self.hover_progress > 0:
            # Apply ease-out function to the progress for both hovering and un-hovering
            ease_factor = self.circ_ease_out(self.hover_progress)
            
            # Calculate current scale
            current_scale = 1.0 + (self.hover_scale - 1.0) * ease_factor
            
            current_width = int(self.original_width * current_scale)
            current_height = int(self.original_height * current_scale)
            
            # Create button surface at the new size
            button_surface = pygame.Surface((current_width, current_height), pygame.SRCALPHA)
            
            # Fill with background color (could be transparent)
            button_surface.fill(self.bg_color)
            
            # Interpolate text color based on hover progress
            current_color = [
                self.idle_color[i] + (self.hover_color[i] - self.idle_color[i]) * ease_factor
                for i in range(3)
            ]
            
            # Render text and center it
            text_surface = self.font.render(self.text, True, current_color)
            text_rect = text_surface.get_rect(center=(current_width // 2, current_height // 2))
            button_surface.blit(text_surface, text_rect)
            
            # Blit the button to the main surface with proper centering
            button_rect = button_surface.get_rect(center=(self.width // 2, self.height // 2))
            self.image.blit(button_surface, button_rect)
            
            # Update rect to accommodate the new size for hit detection while keeping center
            self.rect.width = current_width
            self.rect.height = current_height
            # Keep the center position
            self.rect.center = self.position
        else:
            # Normal state (no hover)
            button_rect = pygame.Rect(0, 0, self.original_width, self.original_height)
            button_rect.center = (self.width // 2, self.height // 2)
            
            # Fill background if specified
            if self.bg_color[3] > 0:  # If has any opacity
                pygame.draw.rect(self.image, self.bg_color, button_rect)
            
            # Render text and center it
            text_surface = self.font.render(self.text, True, self.idle_color)
            text_rect = text_surface.get_rect(center=button_rect.center)
            self.image.blit(text_surface, text_rect)
            
            # Reset rect to original size while maintaining center
            self.rect.width = self.original_width
            self.rect.height = self.original_height
            self.rect.center = self.position
    
    def update(self):
        if not self.active:
            return
        
        # Get mouse position and check if hovering
        mouse_pos = pygame.mouse.get_pos()
        previous_hover_state = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Check for hover state change
        if self.is_hovered != previous_hover_state:
            # State changed, update animation direction
            self.hover_direction = 1 if self.is_hovered else -1
        
        # Update hover animation progress
        if self.hover_direction != 0:
            # Calculate time delta (assume 60 FPS for simplicity)
            dt = 1 / C.FPS
            
            # Update progress based on direction and appropriate duration
            duration = self.hover_duration if self.hover_direction > 0 else self.unhover_duration
            self.hover_progress += self.hover_direction * (dt / duration)
            
            # Clamp progress between 0 and 1
            self.hover_progress = max(0, min(1, self.hover_progress))
            
            # Check if animation completed
            if self.hover_progress == 0 or self.hover_progress == 1:
                self.hover_direction = 0
        
        # Handle mouse clicks - only register on button release
        mouse_buttons = pygame.mouse.get_pressed()
        if self.is_hovered and not mouse_buttons[0] and hasattr(self, 'was_pressed') and self.was_pressed and self.callback:
            self.callback()
            
        # Track if button was pressed
        self.was_pressed = self.is_hovered and mouse_buttons[0]
        
        # Re-render button with current state
        self.render()


