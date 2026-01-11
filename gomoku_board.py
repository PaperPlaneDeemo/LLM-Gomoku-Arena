"""
Gomoku board representation and management
"""
from typing import Optional, Tuple
import logging

BOARD_SIZE = 15
BOARD_COLUMNS = tuple("ABCDEFGHIJKLMNO")
BOARD_COL_TO_INDEX = {col: idx for idx, col in enumerate(BOARD_COLUMNS)}


class GomokuBoard:
    """15x15 Gomoku board with coordinate system A-O (cols) and 1-15 (rows)"""
    
    def __init__(self):
        # Initialize 15x15 board with empty spaces
        self.size = BOARD_SIZE
        self.board = [['.' for _ in range(self.size)] for _ in range(self.size)]
        self.move_history = []
        
        # Column mapping A-O (15 columns for 15x15 board)
        self.cols = BOARD_COLUMNS
        self.col_to_idx = BOARD_COL_TO_INDEX
    
    def _validate_coordinates(self, col: str, row: int) -> bool:
        """Validate if coordinates are within board bounds"""
        if col not in self.col_to_idx:
            return False
        if row < 1 or row > self.size:
            return False
        return True
    
    def _coord_to_indices(self, col: str, row: int) -> Tuple[int, int]:
        """Convert board coordinates to array indices"""
        col_idx = self.col_to_idx[col]
        row_idx = self.size - row  # Convert to 0-based from bottom
        return row_idx, col_idx
    
    def is_valid_move(self, col: str, row: int) -> Tuple[bool, str]:
        """
        Check if a move is valid
        Returns: (is_valid, error_message)
        """
        # Check coordinates are valid
        if not self._validate_coordinates(col, row):
            return False, (
                f"Invalid coordinates: {col}{row}. "
                f"Column must be {BOARD_COLUMNS[0]}-{BOARD_COLUMNS[-1]}, row must be 1-{self.size}"
            )
        
        # Check if position is empty
        row_idx, col_idx = self._coord_to_indices(col, row)
        if self.board[row_idx][col_idx] != '.':
            return False, f"Position {col}{row} is already occupied"
        
        return True, ""
    
    def place_stone(self, col: str, row: int, stone: str) -> bool:
        """
        Place a stone on the board
        stone: 'B' for black, 'W' for white
        Returns: True if successful, False otherwise
        """
        logging.debug(f"Attempting to place {stone} stone at {col}{row}")
        
        is_valid, error_msg = self.is_valid_move(col, row)
        if not is_valid:
            logging.error(f"Invalid move: {error_msg}")
            print(f"Invalid move: {error_msg}")
            return False
        
        if stone not in ['B', 'W']:
            logging.error(f"Invalid stone type: {stone}. Must be 'B' or 'W'")
            print(f"Invalid stone type: {stone}. Must be 'B' or 'W'")
            return False
        
        row_idx, col_idx = self._coord_to_indices(col, row)
        logging.debug(f"Converting {col}{row} to array indices: [{row_idx}][{col_idx}]")
        logging.debug(f"Current value at [{row_idx}][{col_idx}]: '{self.board[row_idx][col_idx]}'")
        
        self.board[row_idx][col_idx] = stone
        self.move_history.append((col, row, stone))
        
        logging.debug(f"Successfully placed {stone} at {col}{row}")
        logging.debug(f"Updated move history: {self.move_history}")
        
        return True
    
    def get_stone(self, col: str, row: int) -> Optional[str]:
        """Get the stone at given coordinates"""
        if not self._validate_coordinates(col, row):
            return None
        
        row_idx, col_idx = self._coord_to_indices(col, row)
        stone = self.board[row_idx][col_idx]
        return stone if stone != '.' else None
    
    def display(self) -> str:
        """Display the board in the specified format"""
        lines = []
        
        for row_num in range(self.size, 0, -1):  # 15 to 1
            row_idx = self.size - row_num
            line = f"{row_num:2d} "
            
            for col_idx in range(self.size):
                line += self.board[row_idx][col_idx] + " "
            
            lines.append(line.rstrip())
        
        # Add column headers
        header = "   " + " ".join(self.cols)
        lines.append(header)
        
        return "\n".join(lines)
    
    def get_last_move(self) -> Optional[Tuple[str, int, str]]:
        """Get the last move played"""
        return self.move_history[-1] if self.move_history else None
