import csv
import os
from datetime import datetime

class Stats:
    """
    A singleton class for recording game statistics to CSV files.
    Manages creating, recording, and deleting statistics for different game aspects.
    All statistics are stored in separate CSV files within the /stats/ directory.
    """
    __instance = None
    
    # Define CSV file paths with their column headers
    CSV_CONFIGS = {
        'dodged_attack':{
            'file': 'stats_dodged_attack.csv',
            'headers': ['timestamp', 'damage_evaded']
        },
        'player_pos':{
            'file': 'stats_player_pos.csv',
            'headers': ['timestamp', 'player_x', 'player_y']
        },
        'dmg_income':{
            'file': 'stats_dmg_income.csv',
            'headers': ['timestamp', 'attack_type']
        },
        'enemy_lifespan':{
            'file': 'stats_enemy_lifespan.csv',
            'headers': ['timestamp', 'enemy_type', 'lifespan_sec']
        },
        'dmg_deflected':{
            'file': 'stats_dmg_deflected.csv',
            'headers': ['timestamp', 'total_damage']
        },
    }
    
    def __new__(cls):
        """Ensure only one instance of Stats exists (singleton pattern)"""
        if cls.__instance is None:
            cls.__instance = super(Stats, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
    
    def __init__(self):
        """Initialize the Stats class if not already initialized"""
        if self.__initialized:
            return
            
        self.__initialized = True
        self.stats_dir = "stats"
        
        # Create the stats directory if it doesn't exist
        if not os.path.exists(self.stats_dir):
            os.makedirs(self.stats_dir)
            
        # Initialize all CSV files with headers if they don't exist
        for stat_type, config in self.CSV_CONFIGS.items():
            file_path = os.path.join(self.stats_dir, config['file'])
            if not os.path.exists(file_path):
                self._create_csv(file_path, config['headers'])
    
    def _create_csv(self, file_path, headers):
        """Create a new CSV file with the specified headers"""
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
    
    def record(self, stat_type, **data):
        """
        Record a new row of data to the specified statistics type.
        
        Args:
            stat_type (str): The type of statistic to record (must be one in CSV_CONFIGS)
            **data: The data to record as key-value pairs
        """
        if stat_type not in self.CSV_CONFIGS:
            raise ValueError(f"Unknown stat type: {stat_type}. Available types: {list(self.CSV_CONFIGS.keys())}")
        
        # Get file path and headers
        config = self.CSV_CONFIGS[stat_type]
        file_path = os.path.join(self.stats_dir, config['file'])
        headers = config['headers']
        
        # Add timestamp if not provided
        if 'timestamp' in headers and 'timestamp' not in data:
            data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare row with values in the correct order
        row = []
        for header in headers:
            if header in data:
                row.append(data[header])
            else:
                row.append('')  # Use empty string for missing data
        
        # Append the data to the CSV file
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(row)
    
    def get_stats(self, stat_type, limit=None):
        """
        Get statistics data from a CSV file.
        
        Args:
            stat_type (str): The type of statistic to retrieve
            limit (int, optional): Maximum number of rows to return (most recent first)
            
        Returns:
            list: List of dictionaries containing the stats data
        """
        if stat_type not in self.CSV_CONFIGS:
            raise ValueError(f"Unknown stat type: {stat_type}")
        
        file_path = os.path.join(self.stats_dir, self.CSV_CONFIGS[stat_type]['file'])
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # Get headers
            
            # Read all rows
            rows = list(reader)
            
            # Convert rows to dictionaries
            result = []
            for row in rows:
                row_dict = {headers[i]: row[i] for i in range(len(headers))}
                result.append(row_dict)
            
            # Return limited number of rows if specified
            if limit is not None and limit > 0:
                return result[-limit:]
            return result
    
    def clear_stats(self, stat_type=None):
        """
        Clear statistics data for the specified type or all types if none specified.
        
        Args:
            stat_type (str, optional): The type of statistic to clear
        """
        if stat_type is not None:
            if stat_type not in self.CSV_CONFIGS:
                raise ValueError(f"Unknown stat type: {stat_type}")
            
            # Recreate specific CSV file with just headers
            config = self.CSV_CONFIGS[stat_type]
            file_path = os.path.join(self.stats_dir, config['file'])
            self._create_csv(file_path, config['headers'])
        else:
            # Recreate all CSV files with just headers
            for stat_type, config in self.CSV_CONFIGS.items():
                file_path = os.path.join(self.stats_dir, config['file'])
                self._create_csv(file_path, config['headers'])
    
    def add_stat_type(self, stat_type, file_name, headers):
        """
        Add a new statistic type configuration.
        
        Args:
            stat_type (str): The identifier for the statistic type
            file_name (str): The CSV file name
            headers (list): List of column headers
        """
        if stat_type in self.CSV_CONFIGS:
            raise ValueError(f"Stat type {stat_type} already exists")
        
        self.CSV_CONFIGS[stat_type] = {
            'file': file_name,
            'headers': headers
        }
        
        # Create the new CSV file
        file_path = os.path.join(self.stats_dir, file_name)
        if not os.path.exists(file_path):
            self._create_csv(file_path, headers)
    
    def get_available_stat_types(self):
        """
        Get all available statistic types.
        
        Returns:
            list: List of available statistic types
        """
        return list(self.CSV_CONFIGS.keys())