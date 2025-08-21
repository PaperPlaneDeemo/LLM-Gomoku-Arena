"""
Main Gomoku game runner with multi-model LLM vs LLM gameplay
"""
import os
import time
import logging
import json
import argparse
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from gomoku_board import GomokuBoard
from win_checker import WinChecker
from llm_player import LLMPlayer
from model_config import ModelManager, get_model_display_name

# Load environment variables from .env file (override system env vars)
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class GomokuGame:
    """Main game controller for multi-model LLM vs LLM Gomoku"""
    
    def __init__(self, black_model: str = None, white_model: str = None):
        """
        Initialize the game with models configured from environment variables or command line
        
        Args:
            black_model: Optional model name for black player (e.g., 'gpt-5')
            white_model: Optional model name for white player (e.g., 'gemini-2.5-flash')
        """
        self.board = GomokuBoard()
        self.win_checker = WinChecker(self.board)
        
        # Initialize model manager
        self.model_manager = ModelManager()
        
        # Validate configuration
        config_status = self.model_manager.validate_configuration()
        self._print_configuration_status(config_status, black_model, white_model)
        
        # Create players with their configured models
        try:
            # Use command line models if specified, otherwise use environment variables
            if black_model:
                black_config = self.model_manager.get_model_config_by_name(black_model)
            else:
                black_config = self.model_manager.get_player_config("B")
                
            if white_model:
                white_config = self.model_manager.get_model_config_by_name(white_model)
            else:
                white_config = self.model_manager.get_player_config("W")
            
            self.black_player = LLMPlayer(black_config, "B")
            self.white_player = LLMPlayer(white_config, "W")
            
        except ValueError as e:
            raise ValueError(f"Model configuration error: {e}")
        
        self.current_player = self.black_player  # Black starts first
        self.game_over = False
        self.winner = None
        
        # Initialize game record for JSON export
        self.game_record = {
            "game_info": {
                "timestamp": datetime.now().isoformat(),
                "black_player": {
                    "model": black_config.model_name,
                    "provider": black_config.provider,
                    "display_name": get_model_display_name(black_config.provider, black_config.model_name)
                },
                "white_player": {
                    "model": white_config.model_name,
                    "provider": white_config.provider,
                    "display_name": get_model_display_name(white_config.provider, white_config.model_name)
                }
            },
            "moves": [],
            "result": {
                "winner": None,
                "winner_color": None,
                "total_moves": 0,
                "winning_line": None,
                "game_end_reason": None
            }
        }
    
    def _print_configuration_status(self, config_status, black_model=None, white_model=None):
        """Print the current model configuration status"""
        print("\n🤖 Model Configuration Status")
        print("=" * 50)
        
        # Show command line specified models if available
        if black_model or white_model:
            print("Command Line Configuration:")
            if black_model:
                try:
                    provider = self.model_manager.find_provider_for_model(black_model)
                    display_name = get_model_display_name(provider, black_model)
                    print(f"Black Player: {provider}/{black_model} ({display_name})")
                except ValueError:
                    print(f"Black Player: {black_model} (❌ Not Found)")
            else:
                black_info = config_status["black_player"]
                print(f"Black Player: {black_info['provider']}/{black_info['model']} (from .env)")
                
            if white_model:
                try:
                    provider = self.model_manager.find_provider_for_model(white_model)
                    display_name = get_model_display_name(provider, white_model)
                    print(f"White Player: {provider}/{white_model} ({display_name})")
                except ValueError:
                    print(f"White Player: {white_model} (❌ Not Found)")
            else:
                white_info = config_status["white_player"]
                print(f"White Player: {white_info['provider']}/{white_info['model']} (from .env)")
        else:
            print("Environment Variable Configuration:")
            black_info = config_status["black_player"]
            white_info = config_status["white_player"]
            
            print(f"Black Player: {black_info['provider']}/{black_info['model']}")
            print(f"  Status: {'✅ Configured' if black_info['configured'] else '❌ Not Configured'}")
            
            print(f"White Player: {white_info['provider']}/{white_info['model']}")
            print(f"  Status: {'✅ Configured' if white_info['configured'] else '❌ Not Configured'}")
        
        print(f"\nConfigured Providers: {config_status['configured_providers']}")
        print(f"Total Available Providers: {config_status['total_providers']}")
        print()
        
    def switch_player(self):
        """Switch to the other player"""
        self.current_player = (self.white_player if self.current_player == self.black_player 
                              else self.black_player)
    
    def record_move(self, column: str, row: int, player_color: str):
        """Record a move in the game record"""
        move_number = len(self.game_record["moves"]) + 1
        player_info = (self.game_record["game_info"]["black_player"] 
                      if player_color == "B" 
                      else self.game_record["game_info"]["white_player"])
        
        move_record = {
            "move_number": move_number,
            "player": player_color,
            "player_name": player_info["display_name"],
            "column": column,
            "row": row,
            "coordinate": f"{column}{row}"
        }
        
        self.game_record["moves"].append(move_record)
    
    def display_game_state(self):
        """Display current game state"""
        color_name = "Black" if self.current_player.stone_color == 'B' else 'White'
        print("\n" + "="*60)
        print(f"GOMOKU GAME - {color_name}'s Turn ({self.current_player.display_name})")
        print("="*60)
        print(self.board.display())
        print()
    
    def check_game_end(self, last_move: Optional[tuple] = None) -> bool:
        """
        Check if the game has ended (win or draw)
        
        Args:
            last_move: Tuple of (column, row) of the last move made
            
        Returns:
            True if game is over, False otherwise
        """
        # Check for win condition
        if last_move:
            column, row = last_move
            stone = self.current_player.stone_color
            
            if self.win_checker.check_win(column, row, stone):
                self.winner = stone
                self.game_over = True
                
                # Get the winning line for display
                winning_line = self.win_checker.get_winning_line(column, row, stone)
                color_name = "Black" if stone == "B" else "White"
                
                # Record the game result
                self.game_record["result"]["winner"] = color_name
                self.game_record["result"]["winner_color"] = stone
                self.game_record["result"]["total_moves"] = len(self.game_record["moves"])
                self.game_record["result"]["game_end_reason"] = f"{color_name} achieved 5 in a row"
                if winning_line:
                    self.game_record["result"]["winning_line"] = [
                        {"column": col, "row": row, "coordinate": f"{col}{row}"} 
                        for col, row in winning_line
                    ]
                
                print(f"\n🎉 GAME OVER! {color_name} wins! 🎉")
                if winning_line:
                    line_str = " → ".join([f"{col}{row}" for col, row in winning_line])
                    print(f"Winning line: {line_str}")
                
                return True
        
        # Check for draw (board full)
        if self.win_checker.is_board_full():
            self.game_over = True
            
            # Record the draw result
            self.game_record["result"]["winner"] = "Draw"
            self.game_record["result"]["winner_color"] = None
            self.game_record["result"]["total_moves"] = len(self.game_record["moves"])
            self.game_record["result"]["game_end_reason"] = "Board is full - Draw"
            
            print("\n🤝 GAME OVER! It's a draw! 🤝")
            return True
        
        return False
    
    def play_turn(self) -> bool:
        """
        Play one turn of the game
        
        Returns:
            True if turn was successful, False if there was an error
        """
        color_name = "Black" if self.current_player.stone_color == "B" else "White"
        print(f"\n{color_name} ({self.current_player.display_name}) is thinking...")
        
        logging.debug(f"=== Starting turn for {color_name} ===")
        logging.debug(f"Current board state:\n{self.board.display()}")
        logging.debug(f"Move history: {self.board.move_history}")
        
        # Add a small delay for readability
        time.sleep(1)
        
        try:
            success, message, move_coords = self.current_player.play_turn(self.board, max_retries=3)
            
            logging.debug(f"Turn result - Success: {success}, Message: {message}, Coords: {move_coords}")
            
            if success:
                print(f"✓ {message}")
                
                # Record the successful move
                if move_coords:
                    column, row = move_coords
                    self.record_move(column, row, self.current_player.stone_color)
                
                # Check if this move ends the game
                if self.check_game_end(move_coords):
                    return True
                
                # Switch to the other player
                self.switch_player()
                logging.debug(f"Switched to player: {self.current_player.stone_color}")
                return True
            else:
                print(f"✗ {message}")
                logging.error(f"Turn failed for {color_name}: {message}")
                
                # Check if this is a player forfeit (failed after retries)
                if "loses - Failed to make valid move" in message:
                    self.game_over = True
                    # Set the winner as the opponent
                    self.winner = "W" if self.current_player.stone_color == "B" else "B"
                    winner_name = "White" if self.winner == "W" else "Black"
                    
                    # Record the forfeit result
                    self.game_record["result"]["winner"] = winner_name
                    self.game_record["result"]["winner_color"] = self.winner
                    self.game_record["result"]["total_moves"] = len(self.game_record["moves"])
                    self.game_record["result"]["game_end_reason"] = f"{color_name} forfeited - failed to make valid move after retries"
                    
                    print(f"\n🏆 GAME OVER! {winner_name} wins by forfeit! 🏆")
                    print(f"Reason: {color_name} failed to make a valid move after retries")
                    return True
                else:
                    # Other types of failures still end the game
                    self.game_over = True
                    
                    # Record the error result
                    self.game_record["result"]["winner"] = "Error"
                    self.game_record["result"]["winner_color"] = None
                    self.game_record["result"]["total_moves"] = len(self.game_record["moves"])
                    self.game_record["result"]["game_end_reason"] = f"Game ended due to error: {message}"
                    
                    return False
                
        except Exception as e:
            print(f"✗ Error during {color_name}'s turn: {e}")
            logging.error(f"Exception during {color_name}'s turn: {e}", exc_info=True)
            self.game_over = True
            
            # Record the exception result
            self.game_record["result"]["winner"] = "Error"
            self.game_record["result"]["winner_color"] = None
            self.game_record["result"]["total_moves"] = len(self.game_record["moves"])
            self.game_record["result"]["game_end_reason"] = f"Game ended due to exception: {str(e)}"
            
            return False
    
    def save_game_record(self, filename: str = None) -> str:
        """
        Save the game record to a JSON file
        
        Args:
            filename: Optional custom filename. If not provided, generates timestamp-based name
            
        Returns:
            The filename of the saved file
        """
        if filename is None:
            # Generate filename based on timestamp and players
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            black_model = self.game_record["game_info"]["black_player"]["model"]
            white_model = self.game_record["game_info"]["white_player"]["model"]
            
            # Sanitize model names for filename (replace invalid chars with underscores)
            black_model_safe = black_model.replace("/", "_").replace("\\", "_").replace(":", "_")
            white_model_safe = white_model.replace("/", "_").replace("\\", "_").replace(":", "_")
            
            filename = f"gomoku_game_{timestamp}_{black_model_safe}_vs_{white_model_safe}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.game_record, f, indent=2, ensure_ascii=False)
            
            print(f"📁 Game record saved to: {filename}")
            return filename
        
        except Exception as e:
            print(f"❌ Error saving game record: {e}")
            return None
    
    def play_game(self, max_moves: int = 225) -> str:
        """
        Play a complete game
        
        Args:
            max_moves: Maximum number of moves before declaring a draw
            
        Returns:
            Game result string
        """
        print("🎮 Starting Gomoku Game")
        print(f"Black ({self.black_player.display_name}) vs White ({self.white_player.display_name})")
        print("Goal: Get 5 stones in a row (horizontal, vertical, or diagonal)")
        
        move_count = 0
        
        while not self.game_over and move_count < max_moves:
            self.display_game_state()
            
            if not self.play_turn():
                break
            
            move_count += 1
            
            # Add a pause between moves for better readability
            if not self.game_over:
                time.sleep(0.5)
        
        # Final game state
        self.display_game_state()
        
        # Determine result and ensure it's recorded
        if self.winner:
            winner_name = "Black" if self.winner == "B" else "White"
            result = f"{winner_name} wins!"
        elif move_count >= max_moves:
            # Record max moves reached as draw
            if self.game_record["result"]["winner"] is None:
                self.game_record["result"]["winner"] = "Draw"
                self.game_record["result"]["winner_color"] = None
                self.game_record["result"]["total_moves"] = len(self.game_record["moves"])
                self.game_record["result"]["game_end_reason"] = "Maximum moves reached"
            result = "Draw - Maximum moves reached"
        else:
            result = "Game ended due to error"
        
        print(f"\n📊 FINAL RESULT: {result}")
        print(f"Total moves played: {move_count}")
        
        # Save the game record to JSON
        saved_file = self.save_game_record()
        if saved_file:
            print(f"🎯 Game analysis and replay data saved!")
        
        return result


def create_argument_parser():
    """Create and configure argument parser"""
    # Get available models for help text
    try:
        manager = ModelManager()
        available_models = manager.list_all_available_models()
        models_help = f"Available models: {', '.join(available_models)}"
    except:
        models_help = "Check model_config.py for available models"
    
    parser = argparse.ArgumentParser(
        description="LLM vs LLM Gomoku Game",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python gomoku_game.py                                    # Use .env configuration
  python gomoku_game.py -b gpt-5 -w gemini-2.5-flash     # Specify both models
  python gomoku_game.py -b deepseek-chat                  # Specify only black model
  
{models_help}
        """
    )
    
    parser.add_argument(
        "-b", "--black", 
        type=str, 
        help="Model for black player (first player)"
    )
    
    parser.add_argument(
        "-w", "--white", 
        type=str, 
        help="Model for white player (second player)"
    )
    
    parser.add_argument(
        "--list-models", 
        action="store_true", 
        help="List all available models and exit"
    )
    
    return parser

def main():
    """Main function to run the game"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        # Handle list models command
        if args.list_models:
            manager = ModelManager()
            print("\n🤖 Available Models:")
            print("=" * 50)
            
            for provider, models in manager.PROVIDER_MODELS.items():
                status = "✅ Configured" if provider in manager.configs else "❌ Not Configured"
                print(f"\n{provider.upper()} ({status}):")
                for model in models:
                    display_name = get_model_display_name(provider, model)
                    print(f"  • {model} ({display_name})")
            
            print(f"\n💡 Usage examples:")
            print(f"  python gomoku_game.py -b gpt-5 -w gemini-2.5-flash")
            print(f"  python gomoku_game.py -b deepseek-chat -w glm-4.5")
            return
        
        # Create and run the game
        game = GomokuGame(black_model=args.black, white_model=args.white)
        result = game.play_game()
        
        print(f"\nGame completed with result: {result}")
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file or environment variables")
        print("Copy .env.example to .env and fill in your API keys")
        print("\nUse --list-models to see available models")
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user")
    except Exception as e:
        print(f"\nError running game: {e}")


if __name__ == "__main__":
    main()
