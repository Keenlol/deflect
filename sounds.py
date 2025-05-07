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
        
        # Initialize pygame mixer
        pg.mixer.init()
        
        # Set default volumes
        self.music_volume = 0.5
        self.sound_volume = 10.0
        
        # Sound directories
        self.sound_dir = "sounds/effect"
        self.music_dir = "sounds/music"
        
        # Create dictionaries to store loaded sounds
        self.sounds = {}
        self.music = {}
        
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
    
    def play_sound_random(self, sound_names:list):
        sound = random.choice(sound_names)
        self.play_sound(sound)

    def play_sound(self, sound_name):
        """Play a sound effect once
        
        Args:
            sound_name (str): Name of the sound (filename without extension)
        """
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
    
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
        pg.mixer.music.set_volume(self.music_volume)
    
    def set_sound_volume(self, volume):
        """Set volume for all sound effects
        
        Args:
            volume (float): Volume from 0.0 to 1.0
        """
        for sound in self.sounds.values():
            sound.set_volume(self.sound_volume)
    
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