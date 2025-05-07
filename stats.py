import csv
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
from config import Config as C

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
            'headers': ['timestamp', 'attack_name', 'damage']
        },
        'enemy_lifespan':{
            'file': 'stats_enemy_lifespan.csv',
            'headers': ['timestamp', 'enemy_type', 'lifespan_sec']
        },
        'dmg_deflected':{
            'file': 'stats_dmg_deflected.csv',
            'headers': ['timestamp', 'total_damage_dealt']
        },
    }
    
    FONT_SIZE = {'small':10,
                 'medium': 12,
                 'big': 14}
                 
    # Define color themes for charts
    CHART_THEME = {
        'background': '#0c0c0f',
        'title': '#f1f4fb',
        'text': '#9aa0af',
        'grid': '#2d313d',
        'spine': '#464c5b',
        'table': {
            'cell_bg': '#0c0c0f',
            'header_bg': '#2d313d',
            'edge_color': '#464c5b'
        },
        'heatmap': 'plasma',  # A colormap that looks good on dark backgrounds
        'pie': {
            'edge_color': 'black',
            'colors': ['#5e2222', '#5e3a22', '#5e4922', '#5c5e22', '#225e3d', '#22485e', '#22315e', '#35225e', '#52225e', '#6b2947']  # Bright pastel colors
        },
        'boxplot': 'Set2',
        'histogram': '#1f8fae',  # Dodger blue
        'floor_line': '#f1f4fb'
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
        
        # Custom fonts for charts (will be set by Game class)
        self.title_font = None
        self.text_font = None
        
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

    def create_dodge_stats_tab(self, notebook, data):
        """Create a tab showing dodge statistics table"""
        fsize = self.FONT_SIZE
        theme = self.CHART_THEME

        # Create frame for this tab
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Dodge Stats")
        
        if not data:
            lbl = ttk.Label(tab, text="No dodge data available")
            if self.text_font:
                lbl.configure(font=self.text_font)
            lbl.pack(pady=20)
            return
        
        try:
            # Create a figure for the table with dark background
            fig = plt.Figure(figsize=(4, 3), dpi=80, facecolor=theme['background'])
            ax = fig.add_subplot(111)
            ax.axis('tight')
            ax.axis('off')
            ax.set_facecolor(theme['background'])
            
            # Table data
            table_data = [
                ['Statistic', 'Value'],
                ['Minimum', f"{data['min']:.2f}"],
                ['Maximum', f"{data['max']:.2f}"],
                ['Average', f"{data['avg']:.2f}"],
                ['Std Dev', f"{data['std']:.2f}"]
            ]
            
            # Create the table with dark style
            table = ax.table(cellText=table_data, loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(fsize['big'])
            table.scale(1, 1.5)
            
            # Style the table cells
            for (row, col), cell in table.get_celld().items():
                cell.set_text_props(color=theme['text'])
                cell.set_facecolor(theme['table']['cell_bg'] if row > 0 else theme['table']['header_bg'])
                cell.set_edgecolor(theme['table']['edge_color'])
            
            # Set title with custom font
            fig.suptitle('Dodge Statistics', fontsize=fsize['big'], color=theme['title'])
            
            # Display the figure
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            lbl = ttk.Label(tab, text=f"Error creating chart: {e}")
            if self.text_font:
                lbl.configure(font=self.text_font)
            lbl.pack(pady=20)

    def create_player_position_tab(self, notebook, df):
        """Create a tab showing player position heatmap"""
        fsize = self.FONT_SIZE
        theme = self.CHART_THEME

        # Create frame for this tab
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Player Position")
        
        if df.empty:
            lbl = ttk.Label(tab, text="No player position data available")
            if self.text_font:
                lbl.configure(font=self.text_font)
            lbl.pack(pady=20)
            return
            
        try:
            # Create figure for the heatmap with dark theme
            fig = plt.Figure(figsize=(4, 3), dpi=80, facecolor=theme['background'])
            ax = fig.add_subplot(111)
            ax.set_facecolor(theme['background'])
            
            # Create heatmap using seaborn
            sns.kdeplot(
                x=df['player_x'],
                y=df['player_y'],
                cmap=theme['heatmap'],
                fill=True,
                ax=ax
            )
            
            # Set plot limits to match game window
            ax.set_xlim(0, C.WINDOW_WIDTH)
            ax.set_ylim(0, C.WINDOW_HEIGHT)
            
            # Invert y-axis (because in pygame, y increases downward)
            ax.invert_yaxis()
            
            # Set labels with light text color
            ax.set_xlabel('X Position', fontsize=fsize['medium'], color=theme['text'])
            ax.set_ylabel('Y Position', fontsize=fsize['medium'], color=theme['text'])
            ax.set_title('Player Position Heatmap', fontsize=fsize['big'], color=theme['title'])
            # Make the tick labels white
            ax.tick_params(axis='both', which='major', colors=theme['text'])
            
            # Set grid color for better visibility
            ax.grid(color=theme['grid'], linestyle='-', linewidth=1, alpha=0.5)
            # Add a little marker for the floor
            ax.axhline(y=C.WINDOW_HEIGHT - C.FLOOR_HEIGHT, color=theme['floor_line'], linestyle='--', alpha=0.7)
            
            # Style the spines
            for spine in ax.spines.values():
                spine.set_color(theme['spine'])

            # Display the figure
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            lbl = ttk.Label(tab, text=f"Error creating chart: {e}")
            if self.text_font:
                lbl.configure(font=self.text_font)
            lbl.pack(pady=20)
    
    def create_damage_income_tab(self, notebook, df):
        """Create a tab showing damage income pie chart"""
        fsize = self.FONT_SIZE
        theme = self.CHART_THEME

        # Create frame for this tab
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Damage Income")
        
        if df.empty:
            lbl = ttk.Label(tab, text="No damage income data available")
            if self.text_font:
                lbl.configure(font=self.text_font)
            lbl.pack(pady=20)
            return
            
        try:
            # Create figure for the pie chart with dark background
            fig = plt.Figure(figsize=(4, 3), dpi=80, facecolor=theme['background'])
            ax = fig.add_subplot(111)
            ax.set_facecolor(theme['background'])
            
            # Create pie chart with custom colors
            wedges, texts, autotexts = ax.pie(
                df['damage'],
                labels=df['attack_name'],
                autopct='%1.1f%%',
                startangle=90,
                shadow=False,
                colors=theme['pie']['colors'],
                wedgeprops={'edgecolor': theme['pie']['edge_color']}
            )
            
            # Styling for better readability on dark background
            for text in texts:
                text.set_fontsize(fsize['medium'])
                text.set_color(theme['text'])
            for autotext in autotexts:
                autotext.set_fontsize(fsize['medium'])
                autotext.set_color(theme['text'])
            
            ax.set_title('Damage by Attack Type', fontsize=fsize['big'], color=theme['title'])
            ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular
            
            # Display the figure
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            lbl = ttk.Label(tab, text=f"Error creating chart: {e}")
            if self.text_font:
                lbl.configure(font=self.text_font)
            lbl.pack(pady=20)
    
    def create_enemy_lifespan_tab(self, notebook, df):
        """Create a tab showing enemy lifespan boxplot"""
        fsize = self.FONT_SIZE
        theme = self.CHART_THEME

        # Create frame for this tab
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Enemy Lifespan")
        
        if df.empty:
            lbl = ttk.Label(tab, text="No enemy lifespan data available")
            if self.text_font:
                lbl.configure(font=self.text_font)
            lbl.pack(pady=20)
            return
            
        try:
            # Create figure with dark background
            fig = plt.Figure(figsize=(4, 3), dpi=80, facecolor=theme['background'])
            ax = fig.add_subplot(111)
            ax.set_facecolor(theme['background'])
            
            # Create boxplot using seaborn
            sns.boxplot(
                x='enemy_type',
                y='lifespan_sec',
                data=df,
                ax=ax,
                palette=theme['boxplot']
            )
            
            # Set labels with light text
            ax.set_xlabel('Enemy Type', fontsize=fsize['medium'], color=theme['text'])
            ax.set_ylabel('Lifespan (sec)', fontsize=fsize['medium'], color=theme['text'])
            ax.set_title('Enemy Lifespan', fontsize=fsize['big'], color=theme['title'])
            
            # Style the tick labels and grid
            ax.tick_params(axis='both', which='major', labelsize=fsize['small'], colors=theme['text'])
            ax.grid(color=theme['grid'], linestyle='-', linewidth=1, alpha=0.5, axis='y')
            
            # Style the spines
            for spine in ax.spines.values():
                spine.set_color(theme['spine'])
            
            # Display the figure
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            lbl = ttk.Label(tab, text=f"Error creating chart: {e}")
            if self.text_font:
                lbl.configure(font=self.text_font)
            lbl.pack(pady=20)
    
    def create_damage_deflected_tab(self, notebook, df):
        """Create a tab showing damage deflected histogram"""
        fsize = self.FONT_SIZE
        theme = self.CHART_THEME

        # Create frame for this tab
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Damage Deflected")
        
        if df.empty:
            lbl = ttk.Label(tab, text="No damage deflected data available")
            if self.text_font:
                lbl.configure(font=self.text_font)
            lbl.pack(pady=20)
            return
            
        try:
            # Create figure with dark background
            fig = plt.Figure(figsize=(4, 3), dpi=80, facecolor=theme['background'])
            ax = fig.add_subplot(111)
            ax.set_facecolor(theme['background'])
            
            # Create histogram using seaborn
            sns.histplot(
                data=df,
                x='total_damage_dealt',
                bins=10,  # Adjust number of bins as needed
                kde=True,  # Add kernel density estimate
                ax=ax,
                color=theme['histogram'],
                edgecolor=theme['text'],
                line_kws={'color': theme['text']}
            )
            
            # Set labels with light text
            ax.set_xlabel('Damage Amount', fontsize=fsize['medium'], color=theme['text'])
            ax.set_ylabel('Frequency', fontsize=fsize['medium'], color=theme['text'])
            ax.set_title('Deflected Damage Distribution', fontsize=fsize['big'], color=theme['title'])
            
            # Style the tick labels and grid
            ax.tick_params(axis='both', which='major', labelsize=fsize['small'], colors=theme['text'])
            ax.grid(color=theme['grid'], linestyle='-', linewidth=1, alpha=0.5, axis='y')
            
            # Style the spines
            for spine in ax.spines.values():
                spine.set_color(theme['spine'])
            
            # Display the figure
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            lbl = ttk.Label(tab, text=f"Error creating chart: {e}")
            if self.text_font:
                lbl.configure(font=self.text_font)
            lbl.pack(pady=20)
    