import sys
import serial
import time
import cv2
import numpy as np
import othello_fx
import os

nano = serial.Serial(port='COM9', baudrate=9600, timeout=1)

print("Waiting for Arduino to home...")
while True:
    if nano.in_waiting > 0:
        msg = nano.readline().decode('utf-8', errors='ignore').strip()
        if msg == "ARDUINO_READY":
            print("Arduino is ready!")
            break

alpha_zero_path = os.path.join(os.path.dirname(__file__), 'alpha-zero-general')
if alpha_zero_path not in sys.path:
    sys.path.append(alpha_zero_path)

from OthelloBrain import OthelloBrain

ai_brain = OthelloBrain()
cpu_token_slots = [11, 11, 11]

turn = 0

oboard = np.array([
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  1, -1,  0,  0,  0],
    [ 0,  0,  0, -1,  1,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0]
])

game_over = 0

print("1 - white, -1 - black")
player = int(input())

print("Starting calibration phase...")
saved_camera_matrix = othello_fx.calibrate_camera()

print("Game starting!")

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
time.sleep(1) 

legal_moves, flip_list = othello_fx.find_legal_moves(oboard, player, -player)
print("Sending initial board to Arduino...")
nano.write(bytearray(othello_fx.get_LUT_board(oboard, legal_moves)))
time.sleep(0.5) 

while game_over != 1:
    
    legal_moves, flip_list = othello_fx.find_legal_moves(oboard, player, -player) 
    
    if legal_moves.size == 0:
        game_over = 1
        
    if not game_over:
        print(oboard)
        
        if turn % 2 == 0:
            print("Waiting for player to physically place a piece...")
            valid_move_made = False
            
            while not valid_move_made:
                if nano.in_waiting > 0:
                    try:
                        msg = nano.readline().decode('utf-8', errors='ignore').strip()
                        
                        if "REQUEST_MOVE" in msg:
                            move_result = othello_fx.find_move(oboard, saved_camera_matrix, cap)
                            
                            if move_result is not None:
                                row, col = move_result
                                move_index = row * 8 + col  
                                move = np.array([row, col]).T
                                
                                if othello_fx.legal_move_check(move, legal_moves):
                                    print(f"Move {move} is LEGAL! Updating board...")
                                    
                                    nano.write(f"{move_index}\n".encode('utf-8'))
                                    
                                    oboard = othello_fx.update_board(oboard, player, move, legal_moves, flip_list)
                                    valid_move_made = True
                                    
                                    time.sleep(0.1) 
                                    print("Player move accepted! Updating LEDs...")
                                    nano.write(bytearray(othello_fx.get_LUT_board(oboard, [])))
                                    
                                else:
                                    print(f"DEBUG: Move at Row {row}, Col {col} is ILLEGAL! Rejecting.")
                                    nano.write(b"-1\n")
                            else:
                                nano.write(b"-1\n")
                        elif msg:
                            print(f"Nano: {msg}")
                    except Exception:
                        pass 
                        
        elif turn % 2 == 1:
            print("CPU is thinking...")
            cpu_move = ai_brain.get_best_move(oboard, player)
            cpu_move = np.array(cpu_move)
            
            available_slot = -1
            for i in range(len(cpu_token_slots)):
                if cpu_token_slots[i] > 0:
                    available_slot = i
                    break
                    
            if available_slot != -1:
                cpu_token_slots[available_slot] -= 1
                tokens_left_in_slot = cpu_token_slots[available_slot]
                
                print(f"Robot picking from Slot {available_slot + 1} ({tokens_left_in_slot} left in slot)")
                othello_fx.move_robot_and_place(nano, available_slot, cpu_move[0], cpu_move[1])
                
            else:
                print("WARNING: CPU has run out of physical tokens!")

            oboard = othello_fx.update_board(oboard, player, cpu_move, legal_moves, flip_list)
            print("CPU move is: " + str(cpu_move))
            
            next_legal_moves, _ = othello_fx.find_legal_moves(oboard, -player, player)
            
            nano.write(bytearray(othello_fx.get_LUT_board(oboard, next_legal_moves)))
            print("CPU move sent to LEDs successfully!")
        
        turn += 1
        player = -player

print("Game has ended. GG!")