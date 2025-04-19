class Timer:
    """
    A versatile timer class with built-in class-level management.
    
    Handles timer scenarios like cooldowns, periodic events, and delayed actions.
    All timers count down from duration to 0.
    """
    # Class attribute to store all timer instances
    all_timers = []
    
    def __init__(self, duration, auto_reset=False, paused=False, owner=None):
        """
        Initialize a timer with configurable behavior.
        
        Args:
            duration: Time duration in seconds
            auto_reset: Whether the timer should automatically restart when complete
            paused: Whether the timer starts paused
            owner: Object that owns this timer (e.g., enemy or player instance)
            name: Identifier for the timer (e.g., "attack_cooldown")
        """
        self.duration = duration                # Time in seconds
        self.__current = duration                 # Current time remaining - always counting down
        self.__auto_reset = auto_reset
        self.__paused = paused
        self.__owner = owner
        self.completed = False                    # Tracks if timer has completed
        self.__just_completed = False             # Flag to track if timer just completed ONCE
        
        # Register this timer in the class-level list
        Timer.all_timers.append(self)
        
    def update(self, dt):
        """
        Update the timer state.
        
        Args:
            dt: Delta time in seconds
            
        Returns:
            bool: True if timer just completed, False otherwise
        """
        
        if self.__paused:
            return False
            
        if self.duration <= 0:
            return False
            
        # Store previous value to detect completion
        prev_value = self.__current
            
        # Count down
        self.__current = max(0, self.__current - dt)
        
        # Check if timer just completed
        if prev_value > 0 and self.__current == 0:
            self.completed = True
            self.__just_completed = True
            
            # Handle auto-reset
            if self.__auto_reset:
                self.__current = self.duration
                
            return True  # Timer just completed
                
        return False
    
    def reset(self, duration=None):
        """Reset the timer to its initial duration."""
        if duration is not None:
            self.duration = duration
        self.__current = self.duration
        return self
    
    def start(self, duration=None):
        """Start or restart the timer from full duration."""
        self.__paused = False
        if duration is not None:
            self.duration = duration
        self.__current = self.duration
        return self
    
    def stop(self):
        """Stop and reset the timer."""
        self.__paused = True
        self.reset()
        return self
    
    def pause(self):
        """Pause the timer without resetting."""
        self.__paused = True
        return self
    
    def resume(self):
        """Resume a paused timer."""
        self.__paused = False
        return self
        
    def destroy(self):
        """Remove this timer from the global list."""
        if self in Timer.all_timers:
            Timer.all_timers.remove(self)

    @property
    def owner(self):
        """Get the owner"""
        return self.__owner

    @property
    def remaining(self):
        """Get remaining time."""
        return self.__current
    
    @property
    def elapsed(self):
        """Get elapsed time."""
        return self.duration - self.__current
    
    @property
    def progress(self):
        """Get the timer's progress as a value from 0.0 to 1.0."""
        if self.duration <= 0:
            return 1.0
        return 1.0 - (self.__current / self.duration)
    
    @property
    def is_active(self):
        """Check if the timer is active (not paused and not complete)."""
        return not self.__paused and not self.is_completed

    @property
    def is_paused(self):
        """Check if the timer is puased"""

    @property
    def is_completed(self):
        """Check if the timer has completed (current time is 0)."""
        return self.__current == 0
    
    @property
    def just_completed(self):
        """just like is_completed() but only trigger once."""
        prev = self.__just_completed
        self.__just_completed = False

        return prev

    # Class methods to manage all timers
    @classmethod
    def update_all(cls, dt):
        """Update all timer instances."""
        completed_timers = []
        for timer in cls.all_timers:
            if timer.update(dt):
                completed_timers.append(timer)
        return completed_timers
    
    @classmethod
    def remove_owner_timers(cls, owner):
        """Remove all timers belonging to a specific owner."""
        for timer in list(cls.all_timers):
            if timer.owner == owner:
                cls.all_timers.remove(timer)
    
    @classmethod
    def get_by_owner(cls, owner):
        """Get all timers belonging to a specific owner."""
        return [timer for timer in cls.all_timers if timer.owner == owner]
