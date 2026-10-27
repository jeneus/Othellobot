import sys
import os

# 1. Find exactly where OthelloBrain.py is located (.../othellobot_sw/rpi_sw)
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Go up one level (..), then into the alpha-zero-general folder
alpha_zero_path = os.path.abspath(os.path.join(current_dir, '..', 'alpha-zero-general'))

# 3. Add it to the system path
if alpha_zero_path not in sys.path:
    sys.path.append(alpha_zero_path)

import numpy as np
from MCTS import MCTS
from othello.OthelloGame import OthelloGame
from othello.pytorch.NNet import NNetWrapper as NNet
from utils import dotdict

class OthelloBrain:
    def __init__(self, board_size=8):
        """Initializes the Neural Net and MCTS once."""
        self.g = OthelloGame(board_size)
        self.nnet = NNet(self.g)
        self.nnet.load_checkpoint('C:/Users/sejun/OneDrive/Documents/Solidworks Files/Othello Robot/alpha-zero-general/pretrained_models/othello/pytorch/', '8x8_100checkpoints_best.pth.tar')        
        self.args = dotdict({'numMCTSSims': 50, 'cpuct': 1.0})
        self.mcts = MCTS(self.g, self.nnet, self.args)

    def get_best_move(self, board_state, player):
            """
            Takes a 2D numpy array and the current player (1 for Black, -1 for White).
            Returns the (row, col) of the best move.
            """
            # 1. Convert board to canonical form (AI always sees itself as 1)
            # Multiplying the board by -1 flips the pieces if the AI is White
            canonical_board = board_state * player 
            
            # 2. Get action probabilities from MCTS using the canonical board
            action_probs = self.mcts.getActionProb(canonical_board, temp=0)
            best_action = np.argmax(action_probs)
            
            # Convert the flat action index back to an (x, y) coordinate
            if best_action == self.g.n ** 2:
                return None # Pass turn
                
            row = best_action // self.g.n
            col = best_action % self.g.n
            
            return (row, col)