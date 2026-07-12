import cv2
import mediapipe as mp
import numpy as np
from collections import deque


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
cap = cv2.VideoCapture(0)

styles = ['pixel', 'blur', 'invert', 'edges', 'sepia']
current_style_idx = 0

colors = [(0,0,0), (0,0,255), (0,255,0), (255,0,0)] 
current_color_idx = 0

pinned_mosaics = []

pin_timer = 0
delete_timer = 0
target_delete_idx = -1
prev_box = None

hand_path = deque(maxlen=20) 
swipe_cooldown = 0
ui_flash_text = ""
ui_flash_timer = 0

def apply_effect(img, x1, y1, x2, y2, style, color):
    """Applies the chosen mosaic, filter, and color to an area."""
    roi = img[y1:y2, x1:x2]
    if roi.size == 0: return img
    
    # Apply Style
    if style == 'pixel':
        small = cv2.resize(roi, (15, 15), interpolation=cv2.INTER_LINEAR)
        res = cv2.resize(small, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST)
    elif style == 'blur':
        res = cv2.GaussianBlur(roi, (75, 75), 0)
    elif style == 'invert':
        res = cv2.bitwise_not(roi)
    elif style == 'edges':
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 75, 150)
        res = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    elif style == 'sepia':
        kernel = np.array([[0.272, 0.534, 0.131],
                           [0.349, 0.686, 0.168],
                           [0.393, 0.769, 0.189]])
        res = cv2.transform(roi, kernel)
        res = np.clip(res, 0, 255).astype(np.uint8)
        
    if color != (0,0,0) and style not in ['sepia', 'edges']:
        tint = np.full(res.shape, color, dtype=np.uint8)
        res = cv2.addWeighted(res, 0.7, tint, 0.3, 0)
        
    img[y1:y2, x1:x2] = res
    return img

print("Camera active. 2 Hands: Draw. 1 Hand: Swipe/Delete. Press 'q' to quit.")

while True:
    success, frame = cap.read()
    if not success: break
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    for i, p in enumerate(pinned_mosaics):
        px1, py1, px2, py2 = p['box']
        frame = apply_effect(frame, px1, py1, px2, py2, p['style'], p['color'])
        
        if i == target_delete_idx:
            thickness = int(4 + 4 * np.sin(delete_timer * 0.2))
            cv2.rectangle(frame, (px1, py1), (px2, py2), (0, 0, 255), thickness)

    if swipe_cooldown > 0: swipe_cooldown -= 1
    if ui_flash_timer > 0: ui_flash_timer -= 1

    if results.multi_hand_landmarks:
        num_hands = len(results.multi_hand_landmarks)

        if num_hands == 1:
            hand = results.multi_hand_landmarks[0]
            pointer_x = int(hand.landmark[9].x * w)
            pointer_y = int(hand.landmark[9].y * h)
            
            # A. Check for Deletion
            is_hovering = False
            for i, p in enumerate(pinned_mosaics):
                px1, py1, px2, py2 = p['box']
                if px1 < pointer_x < px2 and py1 < pointer_y < py2:
                    is_hovering = True
                    target_delete_idx = i
                    delete_timer += 1
                    if delete_timer > 60:
                        pinned_mosaics.pop(i)
                        delete_timer = 0
                        target_delete_idx = -1
                        ui_flash_text = "DELETED!"
                        ui_flash_timer = 20
                    break
            
            if not is_hovering:
                delete_timer = 0
                target_delete_idx = -1

                hand_path.append((pointer_x, pointer_y))

                for i in range(1, len(hand_path)):
                    cv2.line(frame, hand_path[i-1], hand_path[i], (0, 255, 255), 3)

                if len(hand_path) >= 15 and swipe_cooldown == 0:
                    dx = hand_path[-1][0] - hand_path[0][0]
                    dy = hand_path[-1][1] - hand_path[0][1]

                    if abs(dx) > 200 and abs(dx) > abs(dy) * 2:
                        current_style_idx = (current_style_idx + 1) % len(styles)
                        swipe_cooldown = 30
                        hand_path.clear()
                        ui_flash_text = f"STYLE: {styles[current_style_idx].upper()}"
                        ui_flash_timer = 30
                    
                    elif abs(dy) > 200 and abs(dy) > abs(dx) * 2:
                        current_color_idx = (current_color_idx + 1) % len(colors)
                        swipe_cooldown = 30
                        hand_path.clear()
                        ui_flash_text = "COLOR CHANGED"
                        ui_flash_timer = 30

        elif num_hands == 2:
            hand_path.clear()
            x_coords, y_coords = [], []
            for hand_landmarks in results.multi_hand_landmarks:
                x_coords.extend([int(hand_landmarks.landmark[4].x * w), int(hand_landmarks.landmark[8].x * w)])
                y_coords.extend([int(hand_landmarks.landmark[4].y * h), int(hand_landmarks.landmark[8].y * h)])

            x1, x2 = min(x_coords), max(x_coords)
            y1, y2 = min(y_coords), max(y_coords)

            if x1 >= 0 and y1 >= 0 and x2 <= w and y2 <= h and (x2 - x1) > 20 and (y2 - y1) > 20:
                current_style = styles[current_style_idx]
                current_color = colors[current_color_idx]
                frame = apply_effect(frame, x1, y1, x2, y2, current_style, current_color)
                
                if prev_box is not None:
                    diff = abs(x1 - prev_box[0]) + abs(y1 - prev_box[1]) + abs(x2 - prev_box[2]) + abs(y2 - prev_box[3])
                    if diff < 60: 
                        pin_timer += 1
                        scan_y = y1 + int((y2 - y1) * (pin_timer / 40))
                        cv2.line(frame, (x1, scan_y), (x2, scan_y), (0, 255, 0), 4)
                        
                        if pin_timer > 40: 
                            pinned_mosaics.append({
                                'box': (x1, y1, x2, y2),
                                'style': current_style,
                                'color': current_color
                            })
                            pin_timer = 0
                            ui_flash_text = "PINNED!"
                            ui_flash_timer = 30
                    else:
                        pin_timer = 0 
                prev_box = (x1, y1, x2, y2)
                
    else:
        hand_path.clear()
        prev_box = None
        pin_timer = 0
        delete_timer = 0
        target_delete_idx = -1

    cv2.putText(frame, f"Style: {styles[current_style_idx]}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Pinned: {len(pinned_mosaics)}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)


    if ui_flash_timer > 0:
        text_size = cv2.getTextSize(ui_flash_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 4)[0]
        text_x = (w - text_size[0]) // 2
        text_y = (h + text_size[1]) // 2
        cv2.putText(frame, ui_flash_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 4)

    cv2.imshow("Advanced Gesture Mosaic Pro", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()