#this file contains all functions relevant to the operation of an Othello game

import numpy as np
import cv2

MAX_INNER_INDEX = 6

LUT = [
    # Row 0 (Top left is index 0)
    49, 48, 63, 62, 1, 0, 15, 14,
    # Row 1
    50, 51, 60, 61, 2, 3, 12, 13,
    # Row 2
    53, 52, 59, 58, 5, 4, 11, 10,
    # Row 3
    54, 55, 56, 57, 6, 7, 8, 9,
    # Row 4 (BL 90 CCW | BR 180)
    46, 45, 42, 41, 25, 24, 23, 22,
    # Row 5
    47, 44, 43, 40, 26, 27, 20, 21,
    # Row 6
    32, 35, 36, 39, 29, 28, 19, 18,
    # Row 7
    33, 34, 37, 38, 30, 31, 16, 17
]

#returns the starting player (-1) and the other
def who_goes_first(input):
    return input, -input, -input

#receives current (static) state of the board, active player, and opposing player
#returns np array in shape (x, 2) and a list with flippers
def find_legal_moves(oboard, ap, op):

    #define array of all legal moves as 2D coordinates (x,y) 
    legal_coord = np.zeros(shape = (0, 2), dtype=np.int_)

    #find all [x,y] coordinates of opposing player's tokens
    op_coord = np.array(np.where(oboard == op)).T

    #define array that will contain all tokens that would need to be flipped
    flip_coord = []

    #find all [x,y] coordinates of unoccupied cells
    unoc_coord = np.array(np.where(oboard == 0)).T
    
    MAX_INNER_INDEX = 8 # Assuming standard 8x8 board

    #check number of aligned tokens capped at number of opposite colored tokens
    for line_len in range(1, min(len(op_coord), MAX_INNER_INDEX) + 1):
        #for each opposing color token, do the following:
        for xy in op_coord:
            
            # --- horizontal lines ---
            same_h = True
            flipper_h = xy

            # FIX: Added xy[1] - 1 >= 0 to prevent negative indexing wraparound
            if xy[1] + line_len <= 7 and xy[1] - 1 >= 0:
                for token_num in range(1, line_len):
                    if oboard[xy[0], xy[1] + token_num] != op:
                        same_h = False
                    else:
                        flipper_h = np.vstack((flipper_h, np.array([xy[0], xy[1] + token_num])))
            else:
                same_h = False
                
            if same_h:
                end1 = oboard[xy[0], xy[1] - 1]
                end2 = oboard[xy[0], xy[1] + line_len]
                # FIX: Replaced summation (end1 + end2 == ap) with explicit boolean check
                if (end1 == ap and end2 == 0) or (end1 == 0 and end2 == ap):
                    flip_coord.append(np.array(flipper_h))
                    if end1 == 0:
                        legal_coord = np.append(legal_coord, np.array([[xy[0], xy[1] - 1]]), axis = 0)
                    elif end2 == 0:
                        legal_coord = np.append(legal_coord, np.array([[xy[0], xy[1] + line_len]]), axis = 0)

            # --- vertical lines ---
            same_v = True
            flipper_v = xy
            
            # FIX: Added xy[0] - 1 >= 0
            if xy[0] + line_len <= 7 and xy[0] - 1 >= 0:
                for token_num in range(1, line_len):
                    if oboard[xy[0] + token_num, xy[1]] != op:
                        same_v = False
                    else:
                        flipper_v = np.vstack((flipper_v, [xy[0] + token_num, xy[1]]))
            else:
                same_v = False
                
            if same_v:
                end1 = oboard[xy[0] - 1, xy[1]]
                end2 = oboard[xy[0] + line_len, xy[1]]
                if (end1 == ap and end2 == 0) or (end1 == 0 and end2 == ap):
                    flip_coord.append(np.array(flipper_v))
                    if end1 == 0:
                        legal_coord = np.append(legal_coord, np.array([[xy[0] - 1, xy[1]]]), axis = 0)
                    elif end2 == 0:
                        legal_coord = np.append(legal_coord, np.array([[xy[0] + line_len, xy[1]]]), axis = 0)

            # --- diagonal lines (Down-Right) ---
            same_d = True
            flipper_d = xy
            
            # FIX: Added xy[0] - 1 >= 0 and xy[1] - 1 >= 0
            if (xy[0] + line_len <= 7 and xy[1] + line_len <= 7) and (xy[0] - 1 >= 0 and xy[1] - 1 >= 0):
                for token_num in range(1, line_len):
                    if oboard[xy[0] + token_num, xy[1] + token_num] != op:
                        same_d = False
                    else:
                        flipper_d = np.vstack((flipper_d, [xy[0] + token_num, xy[1] + token_num]))
            else:
                same_d = False
                
            if same_d:
                end1 = oboard[xy[0] - 1, xy[1] - 1]
                end2 = oboard[xy[0] + line_len, xy[1] + line_len]
                if (end1 == ap and end2 == 0) or (end1 == 0 and end2 == ap):
                    flip_coord.append(np.array(flipper_d))
                    if end1 == 0:
                        legal_coord = np.append(legal_coord, np.array([[xy[0] - 1, xy[1] - 1]]), axis = 0)
                    elif end2 == 0:
                        legal_coord = np.append(legal_coord, np.array([[xy[0] + line_len, xy[1] + line_len]]), axis = 0)

            # --- diagonal lines 2 (Down-Left) ---
            same_d2 = True
            flipper_d2 = xy
            
            # FIX: Corrected boundaries for checking down-left & up-right
            if (xy[0] + line_len <= 7 and xy[1] - line_len >= 0) and (xy[0] - 1 >= 0 and xy[1] + 1 <= 7):
                for token_num in range(1, line_len):
                    if oboard[xy[0] + token_num, xy[1] - token_num] != op:
                        same_d2 = False
                    else:
                        # FIX: Changed flipper_d to flipper_d2
                        flipper_d2 = np.vstack((flipper_d2, [xy[0] + token_num, xy[1] - token_num]))
            else:
                same_d2 = False
                
            if same_d2:
                end1 = oboard[xy[0] - 1, xy[1] + 1]
                end2 = oboard[xy[0] + line_len, xy[1] - line_len]
                if (end1 == ap and end2 == 0) or (end1 == 0 and end2 == ap):
                    flip_coord.append(np.array(flipper_d2))
                    if end1 == 0:
                        legal_coord = np.append(legal_coord, np.array([[xy[0] - 1, xy[1] + 1]]), axis = 0)
                    elif end2 == 0:
                        legal_coord = np.append(legal_coord, np.array([[xy[0] + line_len, xy[1] - line_len]]), axis = 0)

    return legal_coord, flip_coord

#return True if the move is legal (a part of legal_moves)
def legal_move_check(move, legal_moves):
    return np.any(np.all(move == legal_moves, axis = 1))

#receives current state of the board, the active player, and the move selected,
#and outputs the new state of the board
def update_board(oboard, ap, move, legal_moves, flip_list):
    index_arr= np.where((legal_moves == move).all(axis = 1))
    flip_all = move
    for line in np.array(index_arr).T:
        flip_all = np.vstack((flip_all, flip_list[int(line)]))
    for token in flip_all:
        oboard[token[0], token[1]] = ap
    return oboard

def get_LUT_board(board, legal_moves=None):
    physical_leds = [0] * 64
    state_map = {0: 0, -1: 1, 1: 2} 
    
    # 1. Map the established tokens
    for logical_idx, state in enumerate(board.flatten()):
        physical_leds[LUT[logical_idx]] = state_map[state]
        
    # 2. Overlay the legal moves as state '3'
    if legal_moves is not None and len(legal_moves) > 0:
        for move in legal_moves:
            # move[0] is row, move[1] is col based on your previous code
            logical_idx = int(move[0] * 8 + move[1])
            physical_leds[LUT[logical_idx]] = 3 
            
    return physical_leds

def blink_legal_moves(legal_moves):
    """
    Takes a (2, x) numpy array of legal moves and sends commands 
    to the specific physical LEDs to make them blink/highlight.
    """
    # Assuming the array is shape (2, x) where row 0 is X (or rows) and row 1 is Y (or cols)
    # If your previous function outputted (x, 2), just transpose it before passing: legal_moves.T
    
    num_moves = legal_moves.shape[1]
    
    for i in range(num_moves):
        # Extract row and column (assuming 8x8 board)
        r = legal_moves[0, i]
        c = legal_moves[1, i]
        
        # 1. Convert 2D coordinate to 1D logical index (0 to 63)
        logical_idx = r * 8 + c
        
        # 2. Map logical index to physical LED index
        physical_idx = LUT[logical_idx]
        
        # 3. Define your byte state for "Blinking" (e.g., 3 = blink/legal move color)
        blink_state = 3 
        
        # 4. Construct the command (Index + State)
        # Example: sending 2 bytes per LED over PySerial
        return bytearray([physical_idx, blink_state])

import cv2
import numpy as np

def calibrate_camera():
    """Runs once at the start of the game to lock onto the 4 starting pieces."""
    print("Calibrating camera... Please ensure ONLY the 4 starting tokens are on the board.")
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    if not cap.isOpened():
        raise RuntimeError("Could not open USB camera.")

    while True:
        ret, img = cap.read()
        if not ret:
            continue

        h, w = img.shape[:2]
        corners = np.float32([[265, 55], [576, 57], [628, 359], [188, 357]])
        corners *= np.array([w / 640, h / 480], dtype=np.float32)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)

        x1, x2 = int(0.35 * w), int(0.90 * w)
        y1, y2 = int(0.15 * h), int(0.65 * h)
        roi = binary[y1:y2, x1:x2]

        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        token_candidates = []
        sx, sy = w / 640, h / 480
        area_scale = sx * sy

        for contour in contours:
            area = cv2.contourArea(contour)
            bx, by, bw, bh = cv2.boundingRect(contour)
            perimeter = cv2.arcLength(contour, True)

            if perimeter == 0: continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)

            if not (400 * area_scale <= area <= 2500 * area_scale and 
                    25 * sx <= bw <= 60 * sx and 20 * sy <= bh <= 50 * sy and circularity > 0.5):
                continue

            moments = cv2.moments(contour)
            if moments["m00"] == 0: continue

            cx = moments["m10"] / moments["m00"] + x1
            cy = moments["m01"] / moments["m00"] + y1
            token_candidates.append((area, cx, cy))

        if len(token_candidates) < 4:
            continue # Keep looping until it sees exactly 4 tokens

        token_candidates.sort(key=lambda p: p[0], reverse=True)
        token_candidates = token_candidates[:4]
        token_centers = np.array([[cx, cy] for _, cx, cy in token_candidates], dtype=np.float32)
        token_centers = token_centers[np.argsort(token_centers[:, 1])]

        vertical_gaps = np.diff(token_centers[:, 1])
        split = int(np.argmax(vertical_gaps)) + 1
        upper_row, lower_row = token_centers[:split], token_centers[split:]

        if len(upper_row) != 2 or len(lower_row) != 2:
            continue

        upper_row = upper_row[np.argsort(upper_row[:, 0])]
        lower_row = lower_row[np.argsort(lower_row[:, 0])]

        reference_image_points = np.float32([upper_row[0], upper_row[1], lower_row[0], lower_row[1]])
        reference_grid_points = np.float32([[3, 3], [4, 3], [3, 4], [4, 4]])
        board_grid_corners = np.float32([[-0.5, -0.5], [ 7.5, -0.5], [ 7.5,  7.5], [-0.5,  7.5]])

        weighted_grid_points = np.vstack([board_grid_corners, np.repeat(reference_grid_points, 4, axis=0)])
        weighted_image_points = np.vstack([corners, np.repeat(reference_image_points, 4, axis=0)])

        grid_to_image, _ = cv2.findHomography(weighted_grid_points, weighted_image_points, method=0)

        if grid_to_image is not None:
            SIZE = 800
            CELL_SIZE = SIZE // 8
            pixel_to_grid = np.array([[1 / CELL_SIZE, 0, -0.5], [0, 1 / CELL_SIZE, -0.5], [0, 0, 1]], dtype=np.float64)
            rectified_to_image = grid_to_image @ pixel_to_grid
            
            cap.release()
            print("Camera successfully calibrated!")
            return np.linalg.inv(rectified_to_image)


# Change the definition to accept 'cap'
def find_move(board, image_to_rectified, cap):
    """Runs during the game. Takes a burst of pictures to catch the LEDs blinking OFF."""
    
    # --- NEW: Flush the 5 stale frames out of the Windows webcam buffer ---
    for _ in range(5):
        cap.read()
    # ----------------------------------------------------------------------

    SIZE = 800
    CELL_SIZE = SIZE // 8
    RADIUS, TOKEN_THRESHOLD = 8, 45
    yy, xx = np.ogrid[-RADIUS:RADIUS + 1, -RADIUS:RADIUS + 1]
    mask = xx**2 + yy**2 <= RADIUS**2
    
    # prev_board is in standard Othello coordinates
    prev_board = (np.array(board) != 0).astype(int)

    # Scan up to 15 frames in a row
    for frame_num in range(15):
        ret, img = cap.read()
        if not ret: 
            continue

        warped = cv2.warpPerspective(img, image_to_rectified, (SIZE, SIZE))
        gray_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        board_state = np.zeros((8, 8), dtype=np.uint8)
        preview = warped.copy()

        for cam_row in range(8):
            for cam_col in range(8):
                cx = cam_col * CELL_SIZE + CELL_SIZE // 2
                cy = cam_row * CELL_SIZE + CELL_SIZE // 2
                patch = gray_warped[cy - RADIUS:cy + RADIUS + 1, cx - RADIUS:cx + RADIUS + 1]
                
                if np.median(patch[mask]) < TOKEN_THRESHOLD:
                    # Apply 90-degree CCW Rotation
                    real_row = cam_col
                    real_col = 7 - cam_row
                    board_state[real_row, real_col] = 1
                    cv2.circle(preview, (cx, cy), 11, (0, 0, 255), 2)
                    
                cv2.circle(preview, (cx, cy), 5, (0, 255, 0), -1)

        cv2.imshow("Live Board Check", preview)
        cv2.waitKey(1)

        curr_board = np.array(board_state, dtype=int)
        diff = curr_board - prev_board
        new_moves = np.argwhere(diff == 1)
        
        if len(new_moves) == 1:
            final_row = int(new_moves[0][0])
            final_col = int(new_moves[0][1])
            print(f"SUCCESS: Valid move detected at Real Board ({final_row},{final_col})")
            return final_row, final_col
            
        # --- NEW: If it fails on the final frame, tell us exactly what it saw ---
        if frame_num == 14:
            print(f"DEBUG: Burst failed. Camera saw {len(new_moves)} new piece(s) at: {new_moves.tolist()}")

    return None

def move_robot_and_place(nano, slot, row, col):
    cmd = f"ROBOT,{slot},{row},{col}\n"
    nano.write(cmd.encode('utf-8'))
    print(f"Sent motor command: ROBOT,{slot},{row},{col}")
    
    # Wait for completion
    while True:
        if nano.in_waiting > 0:
            # Read and clean the incoming string
            msg = nano.readline().decode('utf-8', errors='ignore').strip()
            
            # Print whatever the Arduino says so we aren't flying blind!
            if msg:
                print(f"Nano says: {msg}") 
            
            # Use 'in' instead of '==' to catch the string even if garbage characters are attached
            if "ROBOT_DONE" in msg:
                print("Robot movement complete!")
                break