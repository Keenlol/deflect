# 🗡️ Deflect

**A 2D action survival game where defense is your only offense.**  
By Chetphisuth Tongpa (ID: 6710545491)
> 💡 Final project of SKE   Computer Programming II 2025 course at Kasetsart University, made for educational purposes only.

## 🎮 Game Overview

_Deflect_ is a fast-paced 2D side-scrolling survival game where players can't directly attack — instead, they must **deflect** enemy attacks to damage them.

![Gameplay screenshot](screenshots/gameplay/gameplay2.png)

## ⚙️ Core Mechanics

- **Deflect**: Return the enemies's attack by slashing them.
- **Dodge**: Dash forward and avoid every attacks in the way.
- **Double Jump**: Perform another jump in the air.
- **Passive Healing**: Stay out of the fight and recover.
- **Endless**: Survive for as long as you can!

## 🕹️ Controls

| Action        | Key/Mouse         |
|---------------|-------------------|
| Move Left     | `A`               |
| Move Right    | `D`               |
| Jump / Double Jump | `W` or `SPACE` |
| Dodge (Aim with mouse) | `SHIFT`           |
| Deflect (Aim with mouse) | `Left Mouse Click`|

## 🔧 Installation

Follow these steps to set up and run the game locally:

1.  **Prerequisites:**
    *   Ensure you have Python 3.7 or later installed. You can download it from [python.org](https://www.python.org/).
    *   Ensure you have `pip` (Python's package installer) available. It usually comes with Python.
    *   Note that the game is developed **on Windows**, so macOS users might potentailly have unintended side effects.

2.  **Clone the Repository:**
    Clone the project repository to your local machine:
    ```bash
    git clone https://github.com/Keenlol/deflect.git
    cd deflect
    ```

3.  **Install Dependencies:**
    Install the required Python libraries using pip and the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Game:**
    Execute the main game script:
    ```bash
    python game.py
    ```

The game window should now open and you can start playing. It can take sometime to load.

## ℹ️ Credits
- **Sound Effects**: from the game [*Absolver*](https://store.steampowered.com/app/473690/Absolver/) and [*Mortal Kombat X*](https://store.steampowered.com/app/307780/Mortal_Kombat_X/). (use with modifications)
- **Music**: [*"Colver" by Amos Roddy*](https://open.spotify.com/track/0OKm1zL4sWhwa7yi6aEKQ0?si=9d205133b47d4a62) and [*"Spire" by ToyTree*](https://open.spotify.com/track/1cIVDBzfDZ8wFYPDNxqR5d?si=1e099d260b0d4eed). (direct use)
- **Fonts**: [*"Jua"*](https://fonts.google.com/specimen/Jua) and [*"Coiny"*](https://fonts.google.com/specimen/Coiny). (direct use)
- **Libraries**: [*pygame*](https://www.pygame.org/news), [*matplotlib*](https://matplotlib.org/), [*seaborn*](https://seaborn.pydata.org/),  [*pandas*](https://pandas.pydata.org/) and [*numpy*](https://numpy.org/)
