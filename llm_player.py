"""
LLM Player using multi-model API with function calling for Gomoku
"""
import json
import logging
import openai
from typing import Dict, Any, Optional, Tuple
from gomoku_board import GomokuBoard
from model_config import ModelConfig, get_model_display_name

# Set up debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class LLMPlayer:
    """LLM player that uses multi-model API with function calling to play Gomoku"""
    
    def __init__(self, model_config: ModelConfig, stone_color: str = "B"):
        """
        Initialize LLM player
        
        Args:
            model_config: Model configuration including provider, model name, API key, and base URL
            stone_color: 'B' for black, 'W' for white
        """
        self.model_config = model_config
        self.client = model_config.create_client()
        self.model = model_config.model_name
        self.stone_color = stone_color
        self.opponent_color = "W" if stone_color == "B" else "B"
        
        # Get display name for logging
        self.display_name = get_model_display_name(model_config.provider, model_config.model_name)
        
        logging.info(f"Initialized {stone_color} player with {self.display_name} ({model_config.provider})")
        
        # Function calling schema for placing stones
        self.place_stone_schema = {
            "type": "function",
            "function": {
                "name": "place_stone",
                "description": "Place a stone on the Gomoku board at specified coordinates",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "column": {
                            "type": "string", 
                            "description": "Column letter (A-O)",
                            "enum": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"]
                        },
                        "row": {
                            "type": "integer",
                            "description": "Row number (1-15)",
                            "minimum": 1,
                            "maximum": 15
                        }
                    },
                    "required": ["column", "row"]
                }
            }
        }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        color_name = "Black" if self.stone_color == "B" else "White"
        opponent_name = "White" if self.stone_color == "B" else "Black"
        
        base_prompt = f"""You are playing Gomoku (Five-in-a-Row) as {color_name} stones. 

RULES:
- The board is 15x15 with coordinates A-O (columns) and 1-15 (rows)
- Goal: Get 5 of your stones in a row (horizontal, vertical, or diagonal)
- You play {color_name} stones ('{self.stone_color}'), opponent plays {opponent_name} stones ('{self.opponent_color}')
- '.' represents empty spaces

IMPORTANT MOVE RULES:
- You can ONLY place stones on empty positions marked with '.'
- You CANNOT place stones on positions already occupied by 'B' or 'W'

Always use the place_stone function to make your move."""
        
        return base_prompt
    
    def _get_board_state_message(self, board: GomokuBoard) -> str:
        """Generate message describing current board state"""
        board_display = board.display()
        
        message = f"Current board state:\n{board_display}\n\n"
        
        if board.move_history:
            last_move = board.get_last_move()
            if last_move:
                col, row, stone = last_move
                color_name = "Black" if stone == "B" else "White"
                message += f"Last move: {color_name} played at {col}{row}\n"
        else:
            message += "Board is empty. You have the first move.\n"
        
        message += f"\nYou are playing {self.stone_color} stones. Make your move using the place_stone function."
        
        return message
    
    def get_move(self, board: GomokuBoard) -> Optional[Tuple[str, int]]:
        """
        Get a move from the LLM using function calling
        
        Returns:
            Tuple of (column, row) if successful, None if failed
        """
        try:
            board_message = self._get_board_state_message(board)
            logging.debug(f"[{self.display_name}] Sending board state to LLM:")
            logging.debug(f"[{self.display_name}] {board_message}")
            
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": board_message}
            ]
            
            logging.debug(f"[{self.display_name}] Making API call to model: {self.model}")
            
            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": messages,
                "tools": [self.place_stone_schema]
            }
            
            # Special handling for different models
            if self.model == "deepseek-v3-1-250821":
                # deepseek-v3-1-250821 has issues with forced tool choice, use auto instead
                api_params["tool_choice"] = "auto"
                logging.debug(f"[{self.display_name}] Using tool_choice='auto' for deepseek-v3-1-250821")
            else:
                # Default forced tool choice for other models
                api_params["tool_choice"] = {"type": "function", "function": {"name": "place_stone"}}
            
            # Add thinking parameter for GLM-4.5 model only
            if self.model == "glm-4.5":
                api_params["extra_body"] = {"thinking": {"type": "enabled"}}
                logging.debug(f"[{self.display_name}] Added thinking parameter via extra_body for model: {self.model}")
            
            response = self.client.chat.completions.create(**api_params)
            
            # Parse the tool call
            tool_call = response.choices[0].message.tool_calls[0]
            function_args = json.loads(tool_call.function.arguments)
            
            column = function_args["column"]
            row = function_args["row"]
            
            logging.debug(f"[{self.display_name}] LLM chose move: {column}{row}")
            logging.debug(f"[{self.display_name}] Raw function args: {function_args}")
            
            return column, row
            
        except Exception as e:
            logging.error(f"[{self.display_name}] Error getting move from LLM: {e}")
            print(f"Error getting move from LLM: {e}")
            return None
    
    def validate_and_execute_move(self, board: GomokuBoard, column: str, row: int) -> Tuple[bool, str]:
        """
        Validate and execute a move from the LLM
        
        Returns:
            Tuple of (success, message)
        """
        logging.debug(f"[{self.display_name}] Validating move: {column}{row}")
        
        # Check what's currently at this position
        current_stone = board.get_stone(column, row)
        logging.debug(f"[{self.display_name}] Current stone at {column}{row}: {current_stone}")
        
        # Validate the move
        is_valid, error_msg = board.is_valid_move(column, row)
        logging.debug(f"[{self.display_name}] Move validation result: {is_valid}, {error_msg}")
        
        if not is_valid:
            logging.error(f"[{self.display_name}] Invalid move: {column}{row} - {error_msg}")
            return False, f"Invalid move {column}{row}: {error_msg}"
        
        # Execute the move
        logging.debug(f"[{self.display_name}] Executing move: {column}{row}")
        success = board.place_stone(column, row, self.stone_color)
        
        if success:
            color_name = "Black" if self.stone_color == "B" else "White"
            logging.debug(f"[{self.display_name}] Move successful: {column}{row}")
            return True, f"{color_name} ({self.display_name}) plays {column}{row}"
        else:
            logging.error(f"[{self.display_name}] Failed to place stone at {column}{row}")
            return False, f"Failed to place stone at {column}{row}"
    
    def play_turn(self, board: GomokuBoard, max_retries: int = 3) -> Tuple[bool, str, Optional[Tuple[str, int]]]:
        """
        Play a complete turn: get move from LLM, validate, and execute
        Includes retry mechanism for invalid moves
        
        Args:
            board: Current game board
            max_retries: Maximum number of retries for invalid moves (default: 3)
        
        Returns:
            Tuple of (success, message, move_coordinates)
        """
        color_name = "Black" if self.stone_color == "B" else "White"
        
        for attempt in range(max_retries + 1):  # +1 because we try once, then retry
            is_retry = attempt > 0
            attempt_msg = f" (Retry {attempt})" if is_retry else ""
            
            logging.debug(f"[{self.display_name}] Attempt {attempt + 1}/{max_retries + 1}{attempt_msg}")
            
            # Get move from LLM
            move_result = self.get_move(board)
            
            if move_result is None:
                error_msg = f"Failed to get move from LLM{attempt_msg}"
                logging.error(f"[{self.display_name}] {error_msg}")
                if attempt == max_retries:  # Last attempt failed
                    return False, error_msg, None
                continue  # Try again
            
            column, row = move_result
            
            # Validate and execute the move
            success, message = self.validate_and_execute_move(board, column, row)
            
            if success:
                success_msg = f"{message}{attempt_msg}"
                logging.debug(f"[{self.display_name}] Move successful on attempt {attempt + 1}")
                return True, success_msg, (column, row)
            else:
                # Move failed - log the attempt
                fail_msg = f"{message}{attempt_msg}"
                logging.warning(f"[{self.display_name}] Attempt {attempt + 1} failed: {message}")
                
                if attempt == max_retries:  # Last attempt failed
                    final_msg = f"{color_name} ({self.display_name}) loses - Failed to make valid move after {max_retries + 1} attempts"
                    logging.error(f"[{self.display_name}] All attempts exhausted: {final_msg}")
                    return False, final_msg, None
                
                # Not the last attempt, continue to retry
                logging.info(f"[{self.display_name}] Will retry... ({max_retries - attempt} attempts remaining)")
        
        # This should never be reached, but just in case
        return False, f"{color_name} loses - Unexpected error in retry logic", None
