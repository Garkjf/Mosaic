# Advanced Gesture Mosaic 

A real-time computer vision application that allows you to draw, pin, and control mosaic filters (like pixelation and blur) over your webcam feed using only hand gestures. Built with Python, OpenCV, and Google's MediaPipe.

## Features
* **Real-Time Hand Tracking:** Accurately tracks your fingers to create dynamic bounding boxes.
* **Draw & Pin:** Use two hands to draw a custom-sized censor box and pin it to the screen.
* **Multiple Styles:** Cycle between Pixelated, Gaussian Blur, Color Invert, Neon Edges, and Sepia filters.
* **Gesture Controls:** Use one-handed swipes to change styles and colors, or hover to delete mistakes.
* **Visual UI Feedback:** Features glowing pointer trails, loading bars, and on-screen text flashes so you know exactly what the app is tracking.

##  Installation

**1. Install Python**
Ensure you have Python installed on your computer. 

**2. Install Dependencies**
Open your terminal or command prompt and install the required libraries:
`pip install opencv-python mediapipe numpy`

**3. Run the App**
`python main.py`
*(Note: Change `main.py` to whatever you named your Python file).*

## How to Use (Controls)

The app uses a **1-Hand vs. 2-Hand rule** to understand what you want to do.

### Drawing Mode (2 Hands Visible)
* **Draw a Box:** Hold up both hands. The box will stretch from your furthest left finger to your furthest right finger. 
* **Pin a Box:** Once you like the size and location of your box, hold your hands perfectly still. A green loading line will scan across the box. Once it finishes, the box is permanently pinned to the screen and you can drop your hands.

### Control Mode (1 Hand Visible)
* **Change Style:** Swipe your hand aggressively from Left to Right (or Right to Left).
* **Change Color:** Swipe your hand aggressively Up or Down to cycle through color tints (Clear, Red, Green, Blue).
* **Delete a Box:** Move your finger pointer over a pinned box. It will pulse red. Hold it there for 2 seconds to delete it.

### Keyboard Controls
* Press **`q`** while the window is selected to close the camera and quit the app.
