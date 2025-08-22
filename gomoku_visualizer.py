"""
Gomoku Game Visualizer
A GUI tool to visualize and replay LLM vs LLM Gomoku games from JSON files
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import glob
from typing import Dict, List, Optional, Tuple
import sys


class GomokuVisualizer:
    """GUI application for visualizing Gomoku game replays"""
    
    def __init__(self, root):
        self.root = root
        # Auto-detect best default folder
        self.current_folder = self._detect_default_folder()
        self.root.title(f"LLM Gomoku Game Visualizer - {self.current_folder}")
        self.root.geometry("1150x1000")  # Increased size to accommodate larger board with additional labels
        self.root.minsize(950, 800)  # Adjusted minimum size
        
        # Game data
        self.game_data = None
        self.current_move_index = 0
        self.board_size = 15
        self.cell_size = 38  # Reduced from 45 to fit better with smaller window
        
        # Colors
        self.colors = {
            'empty': '#DEB887',  # Burlywood
            'black': '#000000',
            'white': '#FFFFFF',
            'board_line': '#8B4513',  # Saddle brown
            'winning_stone': '#FF0000',  # Red highlight for winning stones
            'last_move': '#00FF00'  # Green highlight for last move
        }
        
        # Board state for current move
        self.board_state = [['.' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.move_numbers = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]  # Track move numbers
        self.winning_positions = []
        
        # GUI elements
        self.canvas = None
        self.info_frame = None
        self.control_frame = None
        
        self.setup_gui()
        self.load_available_games()
    
    def _detect_default_folder(self):
        """Auto-detect the best default folder based on available games"""
        folders_to_check = ["r1", "round1"]
        
        for folder in folders_to_check:
            if os.path.exists(folder):
                pattern = os.path.join(folder, "*", "*.json")
                json_files = glob.glob(pattern)
                if json_files:
                    return folder
        
        # Fallback to round1 if no folder has games
        return "round1"
    
    def setup_gui(self):
        """Set up the main GUI layout"""
        # Create main frames
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=(5, 2))  # Less bottom padding
        
        middle_frame = ttk.Frame(self.root)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=2)  # Reduced padding
        
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(2, 10))  # Ensure bottom has padding
        
        # Folder selection
        folder_frame = ttk.Frame(top_frame)
        folder_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(folder_frame, text="Folder:").pack(side=tk.LEFT)
        self.folder_var = tk.StringVar(value=self.current_folder)
        self.folder_combobox = ttk.Combobox(folder_frame, textvariable=self.folder_var, 
                                          values=["round1", "r1"], state="readonly", width=10)
        self.folder_combobox.pack(side=tk.LEFT, padx=(5, 0))
        self.folder_combobox.bind('<<ComboboxSelected>>', self.on_folder_changed)
        
        # File selection
        ttk.Label(top_frame, text="Select Game:").pack(side=tk.LEFT, padx=(10, 0))
        self.game_combobox = ttk.Combobox(top_frame, width=60, state="readonly")
        self.game_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.game_combobox.bind('<<ComboboxSelected>>', self.on_game_selected)
        
        # Game info frame
        self.info_frame = ttk.LabelFrame(middle_frame, text="Game Information")
        self.info_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Board canvas
        canvas_frame = ttk.LabelFrame(middle_frame, text="Game Board")
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(
            canvas_frame, 
            width=(self.board_size - 1) * self.cell_size + 100,  # Increased from 90 to 100 for better balance
            height=(self.board_size - 1) * self.cell_size + 90,   # Keep at 90 for letters
            bg='white'
        )
        self.canvas.pack(padx=5, pady=5)  # Reduced padding to save space
        
        # Control buttons
        self.control_frame = ttk.Frame(bottom_frame)
        self.control_frame.pack(fill=tk.X)
        
        # Navigation buttons with keyboard shortcuts
        self.btn_first = ttk.Button(self.control_frame, text="<< First (⌘+← / 1)", command=self.go_to_first)
        self.btn_first.pack(side=tk.LEFT, padx=2)
        
        self.btn_prev = ttk.Button(self.control_frame, text="< Previous (← / A)", command=self.previous_move)
        self.btn_prev.pack(side=tk.LEFT, padx=2)
        
        self.btn_next = ttk.Button(self.control_frame, text="Next (→ / D / Space) >", command=self.next_move)
        self.btn_next.pack(side=tk.LEFT, padx=2)
        
        self.btn_last = ttk.Button(self.control_frame, text="Last (⌘+→ / 0) >>", command=self.go_to_last)
        self.btn_last.pack(side=tk.LEFT, padx=2)
        
        # Move counter
        self.move_label = ttk.Label(self.control_frame, text="Move: 0/0")
        self.move_label.pack(side=tk.RIGHT, padx=10)
        
        # Initialize empty board
        self.draw_board()
        self.update_buttons()
        
        # Bind keyboard shortcuts
        self.setup_keyboard_shortcuts()
    
    def setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for navigation"""
        # Make sure the root window can receive focus for key events
        self.root.focus_set()
        
        # Bind keyboard shortcuts
        self.root.bind('<Left>', lambda e: self.previous_move())
        self.root.bind('<Right>', lambda e: self.next_move())
        
        # Mac equivalent shortcuts for Home/End
        self.root.bind('<Command-Left>', lambda e: self.go_to_first())   # ⌘+← 
        self.root.bind('<Command-Right>', lambda e: self.go_to_last())   # ⌘+→
        
        # Alternative number keys for quick access
        self.root.bind('<1>', lambda e: self.go_to_first())     # 1 for first
        self.root.bind('<0>', lambda e: self.go_to_last())      # 0 for last
        
        # WASD style navigation
        self.root.bind('<a>', lambda e: self.previous_move())  # A for previous
        self.root.bind('<d>', lambda e: self.next_move())     # D for next
        self.root.bind('<space>', lambda e: self.next_move()) # Space for next
    
    def load_available_games(self):
        """Load all available JSON game files from the current folder"""
        # Look for JSON files in the selected folder
        json_files = []
        folder_path = self.current_folder
        
        if os.path.exists(folder_path):
            # Get all JSON files in the folder subdirectories
            pattern = os.path.join(folder_path, "*", "*.json")
            json_files = glob.glob(pattern)
        
        if not json_files:
            # Fallback: look in current directory
            json_files = glob.glob("*.json")
        
        # Create display names for combobox
        game_options = []
        self.game_files = {}
        
        for file_path in sorted(json_files):
            # Extract meaningful name from filename
            filename = os.path.basename(file_path)
            # Remove .json extension
            display_name = filename.replace('.json', '')
            # Replace underscores with spaces for better readability
            display_name = display_name.replace('_', ' ')
            
            game_options.append(display_name)
            self.game_files[display_name] = file_path
        
        if game_options:
            self.game_combobox['values'] = game_options
            # Auto-select first game only if combobox is empty
            if not self.game_combobox.get():
                self.game_combobox.set(game_options[0])
                self.load_game(self.game_files[game_options[0]])
        else:
            self.game_combobox['values'] = []
            self.game_combobox.set("")
            # Clear the board and info if no games found
            self.game_data = None
            self.current_move_index = 0
            self.reset_board()
            self.draw_board()
            self.update_buttons()
            # Clear game info
            for widget in self.info_frame.winfo_children():
                widget.destroy()
            ttk.Label(self.info_frame, text=f"No games found in '{folder_path}' folder", 
                     font=('Arial', 10, 'italic')).pack(anchor=tk.W, padx=5, pady=10)
    
    def on_folder_changed(self, event):
        """Handle folder selection change"""
        new_folder = self.folder_var.get()
        if new_folder != self.current_folder:
            self.current_folder = new_folder
            # Update window title to show current folder
            self.root.title(f"LLM Gomoku Game Visualizer - {new_folder}")
            # Clear current game selection
            self.game_combobox.set("")
            # Reload games from new folder
            self.load_available_games()
    
    def on_game_selected(self, event):
        """Handle game selection from combobox"""
        selected_game = self.game_combobox.get()
        if selected_game in self.game_files:
            self.load_game(self.game_files[selected_game])
    
    def load_game(self, file_path: str):
        """Load game data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.game_data = json.load(f)
            
            self.current_move_index = 0
            self.reset_board()
            self.update_info_display()
            self.update_board_to_move(0)
            self.update_buttons()
            
        except Exception as e:
            messagebox.showerror("Error Loading Game", f"Failed to load game file:\n{str(e)}")
    
    def reset_board(self):
        """Reset board to empty state"""
        self.board_state = [['.' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.move_numbers = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.winning_positions = []
    
    def coord_to_indices(self, col: str, row: int) -> Tuple[int, int]:
        """Convert board coordinates to array indices"""
        cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
        col_idx = cols.index(col)
        row_idx = self.board_size - row  # Convert to 0-based from bottom
        return row_idx, col_idx
    
    def update_info_display(self):
        """Update the game information display"""
        # Clear existing info
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        
        if not self.game_data:
            return
        
        game_info = self.game_data.get('game_info', {})
        result = self.game_data.get('result', {})
        
        # Game timestamp
        timestamp = game_info.get('timestamp', 'Unknown')[:19]  # Remove microseconds
        ttk.Label(self.info_frame, text=f"Game Time: {timestamp}").pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Separator(self.info_frame, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        
        # Player information
        black_player = game_info.get('black_player', {})
        white_player = game_info.get('white_player', {})
        
        ttk.Label(self.info_frame, text="PLAYERS", font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=5, pady=2)
        
        # Black player
        black_frame = ttk.Frame(self.info_frame)
        black_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(black_frame, text="⚫ Black:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        ttk.Label(black_frame, text=f"   {black_player.get('display_name', 'Unknown')}").pack(anchor=tk.W)
        ttk.Label(black_frame, text=f"   Model: {black_player.get('model', 'Unknown')}").pack(anchor=tk.W)
        ttk.Label(black_frame, text=f"   Provider: {black_player.get('provider', 'Unknown')}").pack(anchor=tk.W)
        
        # White player
        white_frame = ttk.Frame(self.info_frame)
        white_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(white_frame, text="⚪ White:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        ttk.Label(white_frame, text=f"   {white_player.get('display_name', 'Unknown')}").pack(anchor=tk.W)
        ttk.Label(white_frame, text=f"   Model: {white_player.get('model', 'Unknown')}").pack(anchor=tk.W)
        ttk.Label(white_frame, text=f"   Provider: {white_player.get('provider', 'Unknown')}").pack(anchor=tk.W)
        
        ttk.Separator(self.info_frame, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        
        # Game result
        ttk.Label(self.info_frame, text="GAME RESULT", font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=5, pady=2)
        
        winner = result.get('winner', 'In Progress')
        total_moves = result.get('total_moves', len(self.game_data.get('moves', [])))
        
        ttk.Label(self.info_frame, text=f"Winner: {winner}").pack(anchor=tk.W, padx=5, pady=1)
        ttk.Label(self.info_frame, text=f"Total Moves: {total_moves}").pack(anchor=tk.W, padx=5, pady=1)
        
        # Game end reason
        end_reason = result.get('game_end_reason', 'Game in progress')
        
        reason_frame = ttk.Frame(self.info_frame)
        reason_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(reason_frame, text="Reason:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        
        # Wrap long text
        reason_text = tk.Text(reason_frame, height=3, width=25, wrap=tk.WORD)
        reason_text.pack(fill=tk.X, pady=2)
        reason_text.insert(tk.END, end_reason)
        reason_text.config(state=tk.DISABLED)
        
        # Current turn info
        if self.game_data.get('moves'):
            ttk.Separator(self.info_frame, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
            ttk.Label(self.info_frame, text="CURRENT TURN", font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=5, pady=2)
            self.update_current_turn_info()
    
    def update_current_turn_info(self):
        """Update current turn information in the info panel"""
        # Remove existing current turn info
        children = self.info_frame.winfo_children()
        for i, child in enumerate(children):
            if hasattr(child, 'current_turn_marker'):
                for j in range(i, len(children)):
                    if children[j].winfo_exists():
                        children[j].destroy()
                break
        
        if not self.game_data or not self.game_data.get('moves'):
            return
        
        moves = self.game_data['moves']
        
        # Create frame for current turn info
        turn_frame = ttk.Frame(self.info_frame)
        turn_frame.pack(fill=tk.X, padx=5, pady=2)
        turn_frame.current_turn_marker = True  # Mark this frame
        
        if self.current_move_index < len(moves):
            current_move = moves[self.current_move_index]
            
            player_symbol = "⚫" if current_move['player'] == 'B' else "⚪"
            player_name = current_move['player_name']
            coordinate = current_move['coordinate']
            move_num = current_move['move_number']
            
            ttk.Label(turn_frame, text=f"{player_symbol} {player_name}").pack(anchor=tk.W)
            ttk.Label(turn_frame, text=f"Move {move_num}: {coordinate}").pack(anchor=tk.W)
        else:
            ttk.Label(turn_frame, text="Game Complete").pack(anchor=tk.W)
    
    def draw_board(self):
        """Draw the Gomoku board with 15x15 grid lines"""
        self.canvas.delete("all")
        
        # Board background - center the board in the canvas
        board_x = 50  # Increased to 50 to balance the wider canvas
        board_y = 45  # Keep at 45 for vertical centering
        # Calculate board size based on 14 intervals between 15 lines
        board_width = (self.board_size - 1) * self.cell_size
        board_height = (self.board_size - 1) * self.cell_size
        
        # Create background without border (棋盘背景，无边框)
        self.canvas.create_rectangle(
            board_x, board_y, 
            board_x + board_width, board_y + board_height,
            fill=self.colors['empty'], outline=""
        )
        
        # Draw 15 grid lines (0 to 14 indices, representing A-O and 1-15)
        for i in range(self.board_size):
            # Vertical lines (A to O)
            x = board_x + i * self.cell_size
            self.canvas.create_line(
                x, board_y, x, board_y + board_height,
                fill=self.colors['board_line'], width=1
            )
            
            # Horizontal lines (1 to 15)
            y = board_y + i * self.cell_size
            self.canvas.create_line(
                board_x, y, board_x + board_width, y,
                fill=self.colors['board_line'], width=1
            )
        
        # Column labels (A-O) - aligned with grid intersections - 上方
        cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
        for i, col in enumerate(cols):
            x = board_x + i * self.cell_size  # Align with grid lines
            self.canvas.create_text(x, board_y - 20, text=col, font=('Arial', 12, 'bold'), fill='black')
        
        # Column labels (A-O) - aligned with grid intersections - 下方（从左到右A-O）
        for i, col in enumerate(cols):
            x = board_x + i * self.cell_size  # Align with grid lines
            self.canvas.create_text(x, board_y + board_height + 20, text=col, font=('Arial', 12, 'bold'), fill='black')
        
        # Row labels (1-15) - aligned with grid intersections - 左侧
        for i in range(self.board_size):
            row_num = self.board_size - i
            y = board_y + i * self.cell_size  # Align with grid lines
            self.canvas.create_text(board_x - 25, y, text=str(row_num), font=('Arial', 12, 'bold'), fill='black')
        
        # Row labels (1-15) - aligned with grid intersections - 右侧（从下到上1-15）
        for i in range(self.board_size):
            row_num = self.board_size - i
            y = board_y + i * self.cell_size  # Align with grid lines
            self.canvas.create_text(board_x + board_width + 25, y, text=str(row_num), font=('Arial', 12, 'bold'), fill='black')
        
        # Draw stones
        self.draw_stones()
    
    def draw_stones(self):
        """Draw stones on the board"""
        board_x = 50  # Match the board drawing coordinates
        board_y = 45  # Match the board drawing coordinates
        stone_radius = self.cell_size // 2.5  # Increased from // 3 to make stones larger
        
        last_move_pos = None
        if (self.game_data and self.current_move_index > 0 and 
            self.current_move_index <= len(self.game_data.get('moves', []))):
            last_move = self.game_data['moves'][self.current_move_index - 1]
            last_move_pos = (last_move['column'], last_move['row'])
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                stone = self.board_state[row][col]
                if stone in ['B', 'W']:
                    # Calculate position - place stones on grid line intersections
                    x = board_x + col * self.cell_size
                    y = board_y + row * self.cell_size
                    
                    # Determine colors
                    stone_color = self.colors['black'] if stone == 'B' else self.colors['white']
                    outline_color = self.colors['white'] if stone == 'B' else self.colors['black']
                    
                    # Check if this is a winning stone
                    cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
                    current_col = cols[col]
                    current_row = self.board_size - row
                    
                    is_winning = (current_col, current_row) in self.winning_positions
                    is_last_move = (current_col, current_row) == last_move_pos
                    
                    # Draw stone
                    oval = self.canvas.create_oval(
                        x - stone_radius, y - stone_radius,
                        x + stone_radius, y + stone_radius,
                        fill=stone_color, outline=outline_color, width=2
                    )
                    
                    # Draw move number on the stone
                    move_num = self.move_numbers[row][col]
                    if move_num > 0:
                        # Choose text color based on stone color
                        text_color = self.colors['white'] if stone == 'B' else self.colors['black']
                        
                        # Determine font size based on move number
                        if move_num < 10:
                            font_size = 14
                        elif move_num < 100:
                            font_size = 12
                        else:
                            font_size = 10
                        
                        self.canvas.create_text(
                            x, y, 
                            text=str(move_num),
                            fill=text_color,
                            font=('Arial', font_size, 'bold')
                        )
                    
                    # Highlight winning stones or last move
                    if is_winning:
                        self.canvas.create_oval(
                            x - stone_radius - 3, y - stone_radius - 3,
                            x + stone_radius + 3, y + stone_radius + 3,
                            outline=self.colors['winning_stone'], width=3, fill=""
                        )
                    elif is_last_move:
                        self.canvas.create_oval(
                            x - stone_radius - 2, y - stone_radius - 2,
                            x + stone_radius + 2, y + stone_radius + 2,
                            outline=self.colors['last_move'], width=2, fill=""
                        )
    
    def update_board_to_move(self, move_index: int):
        """Update board state to show position after given move index"""
        self.reset_board()
        
        if not self.game_data or not self.game_data.get('moves'):
            self.draw_board()
            return
        
        moves = self.game_data['moves']
        
        # Apply moves up to the current index
        for i in range(move_index):
            if i < len(moves):
                move = moves[i]
                col = move['column']
                row = move['row']
                player = move['player']
                move_num = move.get('move_number', i + 1)  # Get move number or use index + 1
                
                row_idx, col_idx = self.coord_to_indices(col, row)
                self.board_state[row_idx][col_idx] = player
                self.move_numbers[row_idx][col_idx] = move_num
        
        # Check if we're at the end and there's a winning line
        if (move_index == len(moves) and 
            self.game_data.get('result', {}).get('winning_line')):
            winning_line = self.game_data['result']['winning_line']
            self.winning_positions = [(pos['column'], pos['row']) for pos in winning_line]
        else:
            self.winning_positions = []
        
        self.current_move_index = move_index
        self.draw_board()
        self.update_buttons()
        self.update_current_turn_info()
        
        # Update move counter
        total_moves = len(moves)
        self.move_label.config(text=f"Move: {move_index}/{total_moves}")
    
    def update_buttons(self):
        """Update button states based on current position"""
        if not self.game_data:
            # Disable all buttons if no game loaded
            self.btn_first.config(state=tk.DISABLED)
            self.btn_prev.config(state=tk.DISABLED)
            self.btn_next.config(state=tk.DISABLED)
            self.btn_last.config(state=tk.DISABLED)
            return
        
        total_moves = len(self.game_data.get('moves', []))
        
        # First and Previous buttons
        if self.current_move_index <= 0:
            self.btn_first.config(state=tk.DISABLED)
            self.btn_prev.config(state=tk.DISABLED)
        else:
            self.btn_first.config(state=tk.NORMAL)
            self.btn_prev.config(state=tk.NORMAL)
        
        # Next and Last buttons
        if self.current_move_index >= total_moves:
            self.btn_next.config(state=tk.DISABLED)
            self.btn_last.config(state=tk.DISABLED)
        else:
            self.btn_next.config(state=tk.NORMAL)
            self.btn_last.config(state=tk.NORMAL)
    
    def go_to_first(self):
        """Go to start of game"""
        self.update_board_to_move(0)
    
    def previous_move(self):
        """Go to previous move"""
        if self.current_move_index > 0:
            self.update_board_to_move(self.current_move_index - 1)
    
    def next_move(self):
        """Go to next move"""
        if self.game_data and self.current_move_index < len(self.game_data.get('moves', [])):
            self.update_board_to_move(self.current_move_index + 1)
    
    def go_to_last(self):
        """Go to end of game"""
        if self.game_data:
            total_moves = len(self.game_data.get('moves', []))
            self.update_board_to_move(total_moves)


def main():
    """Main function to run the visualizer"""
    root = tk.Tk()
    app = GomokuVisualizer(root)
    
    # Center the window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()
