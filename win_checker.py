"""
Win condition checking for Gomoku
"""
from typing import Optional, Tuple, List
from gomoku_board import GomokuBoard


class WinChecker:
    """Check win conditions for Gomoku (5 in a row)"""
    
    def __init__(self, board: GomokuBoard):
        self.board = board
    
    def check_win(self, col: str, row: int, stone: str) -> bool:
        """
        Check if placing a stone at given position results in a win
        Returns True if this move creates 5 in a row
        """
        if not self.board._validate_coordinates(col, row):
            return False
        
        row_idx, col_idx = self.board._coord_to_indices(col, row)
        
        # Check all four directions: horizontal, vertical, diagonal1, diagonal2
        directions = [
            (0, 1),   # horizontal
            (1, 0),   # vertical  
            (1, 1),   # diagonal \
            (1, -1)   # diagonal /
        ]
        
        for dr, dc in directions:
            count = 1  # Count the stone we just placed
            
            # Check in positive direction
            count += self._count_consecutive(row_idx, col_idx, dr, dc, stone)
            
            # Check in negative direction
            count += self._count_consecutive(row_idx, col_idx, -dr, -dc, stone)
            
            if count >= 5:
                return True
        
        return False
    
    def _count_consecutive(self, start_row: int, start_col: int, dr: int, dc: int, stone: str) -> int:
        """Count consecutive stones in a given direction"""
        count = 0
        row, col = start_row + dr, start_col + dc
        
        while (0 <= row < self.board.size and 
               0 <= col < self.board.size and 
               self.board.board[row][col] == stone):
            count += 1
            row += dr
            col += dc
        
        return count
    
    def is_board_full(self) -> bool:
        """Check if the board is completely full (draw condition)"""
        for row in self.board.board:
            for cell in row:
                if cell == '.':
                    return False
        return True
    
    def get_winning_line(self, col: str, row: int, stone: str) -> Optional[List[Tuple[str, int]]]:
        """
        Get the coordinates of the winning line if this move creates one
        Returns list of (col, row) tuples for the 5-stone line
        """
        if not self.check_win(col, row, stone):
            return None
        
        row_idx, col_idx = self.board._coord_to_indices(col, row)
        
        directions = [
            (0, 1),   # horizontal
            (1, 0),   # vertical
            (1, 1),   # diagonal \
            (1, -1)   # diagonal /
        ]
        
        for dr, dc in directions:
            line_positions = [(col, row)]  # Start with the placed stone
            
            # Collect stones in positive direction
            self._collect_line(row_idx, col_idx, dr, dc, stone, line_positions)
            
            # Collect stones in negative direction
            self._collect_line(row_idx, col_idx, -dr, -dc, stone, line_positions)
            
            if len(line_positions) >= 5:
                return line_positions[:5]  # Return first 5 stones
        
        return None
    
    def _collect_line(
        self,
        start_row: int,
        start_col: int,
        dr: int,
        dc: int,
        stone: str,
        line_positions: List[Tuple[str, int]],
    ) -> None:
        """Collect consecutive stone positions in a direction"""
        row, col = start_row + dr, start_col + dc
        
        while (0 <= row < self.board.size and 
               0 <= col < self.board.size and 
               self.board.board[row][col] == stone):
            # Convert back to board coordinates
            board_col = self.board.cols[col]
            board_row = self.board.size - row
            line_positions.append((board_col, board_row))
            
            row += dr
            col += dc
