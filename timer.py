class Timer:
    """
    A versatile timer class with built-in class-level management.
    
    Handles timer scenarios like cooldowns, periodic events, and delayed actions.
    By default, timers count down from duration to 0.
    Can also be set to count up mode for elapsed time tracking.
    """
    # Class attribute to store all timer instances
    all_timers = []
    
    # Timer modes
    MODE_COUNTDOWN = 0  # Default mode: count down from duration to 0
    MODE_COUNTUP = 1    # Count up from 0 indefinitely
    
    def __init__(self, duration, auto_reset=False, paused=False, owner=None, mode=MODE_COUNTDOWN):
        """
        Initialize a timer with configurable behavior.
        
        Args:
            duration: Time duration in seconds
            auto_reset: Whether the timer should automatically restart when complete
            paused: Whether the timer starts paused
            owner: Object that owns this timer (e.g., enemy or player instance)
            mode: Timer mode (MODE_COUNTDOWN or MODE_COUNTUP)
        """
        self.duration = duration                # Time in seconds
        self.__current = 0 if mode == Timer.MODE_COUNTUP else duration  # Start from 0 for count up mode
        self.__auto_reset = auto_reset
        self.__paused = paused
        self.__owner = owner
        self.__mode = mode
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
            
        if self.__mode == Timer.MODE_COUNTDOWN:
            # COUNTDOWN MODE
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
        
        elif self.__mode == Timer.MODE_COUNTUP:
            # COUNTUP MODE - simply add time
            self.__current += dt
            # No completion concept for count-up timers
            
        return False
    
    def reset(self, duration=None):
        """Reset the timer to its initial state (duration for countdown, 0 for countup)."""
        if duration is not None:
            self.duration = duration
        self.__current = 0 if self.__mode == Timer.MODE_COUNTUP else self.duration
        return self
    
    def start(self, duration=None):
        """Start or restart the timer."""
        self.__paused = False
        if duration is not None:
            self.duration = duration
        self.__current = 0 if self.__mode == Timer.MODE_COUNTUP else self.duration
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
    def mode(self):
        """Get the timer mode"""
        return self.__mode

    @property
    def remaining(self):
        """Get remaining time (only relevant for countdown timers)."""
        if self.__mode == Timer.MODE_COUNTDOWN:
            return self.__current
        return 0  # No concept of remaining time for count-up timers
    
    @property
    def elapsed(self):
        """Get elapsed time."""
        if self.__mode == Timer.MODE_COUNTUP:
            return self.__current  # For count-up, current value is the elapsed time
        return self.duration - self.__current  # For countdown, elapsed is duration minus current
    
    @property
    def progress(self):
        """Get the timer's progress as a value from 0.0 to 1.0."""
        if self.__mode == Timer.MODE_COUNTUP:
            # No real concept of progress for unlimited countup timers
            # Return 0 if no duration specified, otherwise calculate progress
            if self.duration <= 0:
                return 0.0
            return min(1.0, self.__current / self.duration)
        else:
            # Countdown timer progress
            if self.duration <= 0:
                return 1.0
            return 1.0 - (self.__current / self.duration)
    
    @property
    def is_active(self):
        """Check if the timer is active (not paused and not complete)."""
        if self.__mode == Timer.MODE_COUNTUP:
            return not self.__paused  # Count-up timers are always active unless paused
        return not self.__paused and not self.is_completed

    @property
    def is_paused(self):
        """Check if the timer is paused"""
        return self.__paused

    @property
    def is_completed(self):
        """Check if the timer has completed (only relevant for countdown timers)."""
        if self.__mode == Timer.MODE_COUNTUP:
            return False  # Count-up timers never complete
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
