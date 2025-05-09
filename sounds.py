import pygame as pg
import os
import random

class Sounds:
    """
    A singleton class for managing game sounds and music using pygame.mixer.
    Loads all sounds at initialization for efficient playback during gameplay.
    """
    __instance = None
    
    def __new__(cls):
        """Ensure only one instance of Sounds exists (singleton pattern)"""
        if cls.__instance is None:
            cls.__instance = super(Sounds, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
    
    def __init__(self):
        """Initialize the sound system if not already initialized"""
        if self.__initialized:
            return
            
        self.__initialized = True
        
        # Initialize pygame mixer with more channels
        pg.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        pg.mixer.set_num_channels(32)  # Increase number of channels
        
        # Set default volumes
        self.music_volume = 0.5
        self.sound_volume = 0.50  # Changed from 100 to 0.5 (0-1 range)
        
        # Sound directories
        self.sound_dir = "sounds/effect"
        self.music_dir = "sounds/music"
        
        # Create dictionaries to store loaded sounds
        self.sounds = {}
        self.music = {}
        
        # Channel management
        self.channels = [pg.mixer.Channel(i) for i in range(pg.mixer.get_num_channels())]
        self.channel_usage = {}  # Track which sounds are using which channels
        
        # Make sure directories exist
        os.makedirs(self.sound_dir, exist_ok=True)
        os.makedirs(self.music_dir, exist_ok=True)
        
        # Load all sounds
        self._load_all_sounds()
    
    def _load_all_sounds(self):
        """Load all sound files from the sound and music directories"""
        # Load sound effects
        for filename in os.listdir(self.sound_dir):
            if filename.endswith(('.wav', '.ogg', '.mp3')) and os.path.isfile(os.path.join(self.sound_dir, filename)):
                name = os.path.splitext(filename)[0]
                self.sounds[name] = pg.mixer.Sound(os.path.join(self.sound_dir, filename))
                self.sounds[name].set_volume(self.sound_volume)
        
        # Load music files (store the file paths)
        for filename in os.listdir(self.music_dir):
            if filename.endswith(('.wav', '.ogg', '.mp3')) and os.path.isfile(os.path.join(self.music_dir, filename)):
                name = os.path.splitext(filename)[0]
                self.music[name] = os.path.join(self.music_dir, filename)
    
    def _get_available_channel(self):
        """Get an available channel for playing a sound"""
        # First try to find a completely free channel
        for i, channel in enumerate(self.channels):
            if not channel.get_busy():
                return i
        
        # If no free channels, find the oldest playing sound and use its channel
        if self.channel_usage:
            oldest_channel = min(self.channel_usage.items(), key=lambda x: x[1])[0]
            return oldest_channel
        
        # If all else fails, use channel 0
        return 0
    
    def play_sound_random(self, sound_names:list):
        """Play a random sound from the given list of sound names"""
        sound = random.choice(sound_names)
        self.play_sound(sound)

    def play_sound(self, sound_name):
        """Play a sound effect once
        
        Args:
            sound_name (str): Name of the sound (filename without extension)
        """
        if sound_name in self.sounds:
            channel_num = self._get_available_channel()
            self.channels[channel_num].play(self.sounds[sound_name])
            self.channel_usage[channel_num] = pg.time.get_ticks()
    
    def play_music(self, music_name, loops=-1):
        """Play music in loop or specified number of times
        
        Args:
            music_name (str): Name of the music track (filename without extension)
            loops (int): Number of times to loop (-1 for infinite)
        """
        if music_name in self.music:
            pg.mixer.music.load(self.music[music_name])
            pg.mixer.music.set_volume(self.music_volume)
            pg.mixer.music.play(loops)
    
    def stop_music(self):
        """Stop currently playing music"""
        pg.mixer.music.stop()
    
    def pause_music(self):
        """Pause currently playing music"""
        pg.mixer.music.pause()
    
    def unpause_music(self):
        """Unpause currently playing music"""
        pg.mixer.music.unpause()
    
    def fade_out_music(self, time_ms=1000):
        """Fade out the music over the specified time
        
        Args:
            time_ms (int): Fade out time in milliseconds
        """
        pg.mixer.music.fadeout(time_ms)
    
    def set_music_volume(self, volume):
        """Set music volume
        
        Args:
            volume (float): Volume from 0.0 to 1.0
        """
        self.music_volume = max(0.0, min(1.0, volume))
        pg.mixer.music.set_volume(self.music_volume)
    
    def set_sound_volume(self, volume):
        """Set volume for all sound effects
        
        Args:
            volume (float): Volume from 0.0 to 1.0
        """
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sound_volume)
            
    def get_volume_percent(self):
        """Get the current sound volume as a percentage (0-100)"""
        return round(self.sound_volume * 100)
    
    def get_music_percent(self):
        """Get the current music volume as a percentage (0-100)"""
        return round(self.music_volume * 100)
    
    def adjust_volume(self, increment=0.1):
        """Adjust sound volume by increment and cycle back to 0 if over 1.0
        
        Args:
            increment (float): Amount to increase volume by (0.0 to 1.0)
        """
        new_volume = self.sound_volume + increment
        if new_volume > 1.0:
            new_volume = 0.0
        self.set_sound_volume(new_volume)
        return self.get_volume_percent()
    
    def adjust_music_volume(self, increment=0.1):
        """Adjust music volume by increment and cycle back to 0 if over 1.0
        
        Args:
            increment (float): Amount to increase volume by (0.0 to 1.0)
        """
        new_volume = self.music_volume + increment
        if new_volume > 1.0:
            new_volume = 0.0
        self.set_music_volume(new_volume)
        return self.get_music_percent()
    
    def load_new_sound(self, name, file_path):
        """Load a new sound file during gameplay
        
        Args:
            name (str): Name to assign to the sound
            file_path (str): Path to the sound file
        """
        if os.path.exists(file_path):
            self.sounds[name] = pg.mixer.Sound(file_path)
            self.sounds[name].set_volume(self.sound_volume)
    
    def load_new_music(self, name, file_path):
        """Load a new music file during gameplay
        
        Args:
            name (str): Name to assign to the music
            file_path (str): Path to the music file
        """
        if os.path.exists(file_path):
            self.music[name] = file_path