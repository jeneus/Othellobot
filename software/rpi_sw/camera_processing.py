import cv2
import numpy as np

# ==========================================
# 1. Start Live USB Camera
# ==========================================
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

if not cap.isOpened():
    cap.release()
    raise RuntimeError("Could not open USB camera.")

print("Live Calibration Tool Running.")
print("Adjust your board, camera, and lighting.")
print("Press 'q' on your keyboard to quit.")

while True:
    ret, img = cap.read()
    if not ret:
        print("Failed to capture image.")
        break

    h, w = img.shape[:2]

    # ==========================================
    # 2. Define approximate board corners
    # ==========================================
    corners = np.float32([
        [265, 55],     # Top-left (Adjusted inward)
        [576, 57],     # Top-right
        [628, 359],    # Bottom-right
        [188, 357]     # Bottom-left
    ])
    corners *= np.array([w / 640, h / 480], dtype=np.float32)

    # ==========================================
    # 3. Detect the FOUR central black tokens
    # ==========================================
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, binary = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)

    x1, x2 = int(0.35 * w), int(0.90 * w)
    y1, y2 = int(0.15 * h), int(0.65 * h)
    roi = binary[y1:y2, x1:x2]

    debug_img = img.copy()
    # Draw the blue search box
    cv2.rectangle(debug_img, (x1, y1), (x2, y2), (255, 0, 0), 2) 

    contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    token_candidates = []
    sx, sy = w / 640, h / 480
    area_scale = sx * sy

    for contour in contours:
        offset_contour = contour + np.array([[[x1, y1]]])
        area = cv2.contourArea(contour)
        bx, by, bw, bh = cv2.boundingRect(contour)
        perimeter = cv2.arcLength(contour, True)

        if perimeter == 0:
            continue

        circularity = 4 * np.pi * area / (perimeter * perimeter)

        if not (
            400 * area_scale <= area <= 2500 * area_scale
            and 25 * sx <= bw <= 60 * sx
            and 20 * sy <= bh <= 50 * sy
            and circularity > 0.5 
        ):
            # Draw rejected shapes in RED
            cv2.drawContours(debug_img, [offset_contour], -1, (0, 0, 255), 1)
            continue

        moments = cv2.moments(contour)
        if moments["m00"] == 0:
            continue

        cx = moments["m10"] / moments["m00"] + x1
        cy = moments["m01"] / moments["m00"] + y1

        token_candidates.append((area, cx, cy))
        
        # Draw accepted tokens in GREEN
        cv2.drawContours(debug_img, [offset_contour], -1, (0, 255, 0), 2)
        cv2.circle(debug_img, (int(cx), int(cy)), 3, (0, 255, 255), -1)

    # If it fails to find exactly 4, show the debug screen and restart the loop
    if len(token_candidates) < 4:
        cv2.putText(debug_img, f"Missing Tokens! Found: {len(token_candidates)}/4", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Live Calibration", debug_img)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue # Skip the rest of the loop until 4 are found

    # ==========================================
    # 4. Identify tokens and map the board
    # ==========================================
    token_candidates.sort(key=lambda p: p[0], reverse=True)
    token_candidates = token_candidates[:4]  # Keep the 4 largest valid tokens

    token_centers = np.array([[cx, cy] for _, cx, cy in token_candidates], dtype=np.float32)
    token_centers = token_centers[np.argsort(token_centers[:, 1])]

    vertical_gaps = np.diff(token_centers[:, 1])
    split = int(np.argmax(vertical_gaps)) + 1

    upper_row = token_centers[:split]
    lower_row = token_centers[split:]

    if len(upper_row) != 2 or len(lower_row) != 2:
        cv2.putText(debug_img, "Tokens found, but shape is wrong (Not 2 on top, 2 on bottom)", 
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        cv2.imshow("Live Calibration", debug_img)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        continue

    upper_row = upper_row[np.argsort(upper_row[:, 0])]
    lower_row = lower_row[np.argsort(lower_row[:, 0])]

    reference_image_points = np.array([upper_row[0], upper_row[1], lower_row[0], lower_row[1]], dtype=np.float32)
    
    # Standard Othello starting positions: (col 3, row 3), (col 4, row 3), (col 3, row 4), (col 4, row 4)
    reference_grid_points = np.float32([[3, 3], [4, 3], [3, 4], [4, 4]])
    board_grid_corners = np.float32([[-0.5, -0.5], [ 7.5, -0.5], [ 7.5,  7.5], [-0.5,  7.5]])

    weighted_grid_points = np.vstack([board_grid_corners, np.repeat(reference_grid_points, 4, axis=0)])
    weighted_image_points = np.vstack([corners, np.repeat(reference_image_points, 4, axis=0)])

    grid_to_image, _ = cv2.findHomography(weighted_grid_points, weighted_image_points, method=0)

    if grid_to_image is None:
        continue

    # ==========================================
    # 5. Show the aligned grid (Green Dots)
    # ==========================================
    SIZE = 800
    CELL_SIZE = SIZE // 8

    pixel_to_grid = np.array([[1 / CELL_SIZE, 0, -0.5], [0, 1 / CELL_SIZE, -0.5], [0, 0, 1]], dtype=np.float64)
    rectified_to_image = grid_to_image @ pixel_to_grid
    image_to_rectified = np.linalg.inv(rectified_to_image)

    warped = cv2.warpPerspective(img, image_to_rectified, (SIZE, SIZE))
    gray_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    
    RADIUS = 8
    TOKEN_THRESHOLD = 45
    yy, xx = np.ogrid[-RADIUS:RADIUS + 1, -RADIUS:RADIUS + 1]
    mask = xx**2 + yy**2 <= RADIUS**2

    preview = warped.copy()
    
    # Draw Green dots!
    for row in range(8):
        for col in range(8):
            cx = col * CELL_SIZE + CELL_SIZE // 2
            cy = row * CELL_SIZE + CELL_SIZE // 2
            
            patch = gray_warped[cy - RADIUS:cy + RADIUS + 1, cx - RADIUS:cx + RADIUS + 1]
            brightness = np.median(patch[mask])

            # Green dot at center
            cv2.circle(preview, (cx, cy), 5, (0, 255, 0), -1)

            # Red ring if piece is detected
            if brightness < TOKEN_THRESHOLD:
                cv2.circle(preview, (cx, cy), 11, (0, 0, 255), 2)

    cv2.putText(preview, "Perfect! Grid Aligned.", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Live Calibration", preview)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()