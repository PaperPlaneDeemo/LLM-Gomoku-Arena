# LLM Gomoku Arena

A simple implementation of Gomoku (Five-in-a-Row) where different LLM models compete against each other using function calling.

*Inspired by [Kaggle's Game Arena](https://github.com/google-deepmind/game_arena/)*

## Features

- **Command Line Interface** - Quickly start games with any model combination
- **JSON Game Records** - Automatic save of game history and moves
- **Move Validation** - 4-attempt retry mechanism for invalid moves
- **15x15 Gomoku Board** - Traditional coordinate system (A-O columns, 1-15 rows)

## Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Configure API Keys
```bash
# Copy and edit the environment file
cp .env.example .env
# Add your API keys to .env
```

### 3. Run a Game

**Using command line (recommended):**
```bash
# Quick game with specific models
uv run gomoku_game.py -b gpt-5 -w gemini-2.5-flash

# List all available models
uv run gomoku_game.py --list-models

# Use environment configuration
uv run gomoku_game.py
```


## Game Rules

- **Objective:** Get 5 stones in a row (horizontal, vertical, or diagonal)
- **Board:** 15x15 grid with coordinates A-O (columns) and 1-15 (rows)
- **Players:** Black goes first, White goes second
- **Invalid moves:** Players get 4 attempts, then forfeit

## Architecture

### Core Components
- **`GomokuBoard`** - Game board and move validation
- **`WinChecker`** - Win condition detection
- **`LLMPlayer`** - AI player with function calling
- **`GomokuGame`** - Game controller and JSON recording
- **`ModelManager`** - Multi-provider configuration

### Function Calling
LLMs use OpenAI-compatible function calling to place stones:
```json
{
  "name": "place_stone",
  "parameters": {
    "column": "H", 
    "row": 8
  }
}
```

## JSON Game Records

Every game automatically saves a JSON file with:
- Player models and providers
- Complete move history
- Game result and winner
- Winning line coordinates
- Timestamps and metadata
