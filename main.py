import numpy as np
from pynput import mouse, keyboard
import threading
import time
import hashlib
import atexit
from pynput.mouse import Button, Controller
import pyautogui

# Maybe use fan rotation speed peripheral if possible?

img_size = 64
block_size = 4
screen_width, screen_height = pyautogui.size()
rand_number = 0

# Thread-safe entropy storage
image = [[' ' for _ in range(img_size)] for _ in range(img_size)]

# Map mouse coordinates on screen to 64x64 grid
def map_mouse_to_image(x, y):
    x_small = int(x / screen_width * img_size)
    y_small = int(y / screen_height * img_size)
    
    # Clamp values just in case
    x_small = min(max(x_small, 0), img_size - 1)
    y_small = min(max(y_small, 0), img_size - 1)
    
    return x_small, y_small

def map_image_to_256():
    for i in range(img_size):
        for j in range(img_size):
            if image[i][j] == '*':
                rand_number >> i * (block_size*block_size) + j | 1
    print(rand_number)


# Print all the tracked mouse coordinates
def print_trackpad():
    for i in range(img_size):
        for j in range(img_size):
            print(image[j][i], end=' ')
        print()

print_trackpad()
print(f"Screen size: {screen_width}x{screen_height} pixels")

# Action on move of mouse
def on_move(x, y, injected):
    x, y = map_mouse_to_image(x,y)
    image[y][x] = '*'
    print('Pointer moved to {}; it was {}'.format(
        (x, y), 'faked' if injected else 'not faked'))

# Action on click of mouse
def on_click(x, y, button, pressed, injected):
    print('{} at {}; it was {}'.format(
        'Pressed' if pressed else 'Released',
        (x, y), 'faked' if injected else 'not faked'))

# Action on scroll of mouse
def on_scroll(x, y, dx, dy, injected):
    print('Scrolled {} and {} at {}; it was {}'.format(
        'down' if dy < 0 else 'up', 'left' if dx < 0 else 'right',
        (x, y), 'faked' if injected else 'not faked'))

# Action on press of keyboard key
def on_press(key):
    print(f'Key {key} pressed')  # Print pressed key

# Action on release of keyboard key
def on_release(key):
    print(f'Key {key} released')  # Print released key
    if str(key) == 'Key.esc':     # Stop listener on ESC
        return False

# Mouse listener
mouse_listener = mouse.Listener(
    on_move=on_move,
    on_click=on_click,
    on_scroll=on_scroll)

# Keyboard listener
keyboard_listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)

# Start listening
mouse_listener.start()
keyboard_listener.start()

# Actions on program exit
def on_exit():
    print("\nProgram exiting. Stopping listeners...")
    mouse_listener.stop()
    keyboard_listener.stop()
    if image:
        # Optional: final random bytes from remaining entropy
        print_trackpad()
        map_image_to_256()

atexit.register(on_exit)

# ---------- Keep main program alive ----------
# Main loop to keep program alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Keyboard interrupt received. Exiting...")

# ---------- Mouse event handlers ----------
# def on_move(x, y):
#     t = time.time_ns()
#     entropy_data.append(f"MOVE-{x}-{y}-{t}")

# def on_click(x, y, button, pressed):
#     t = time.time_ns()
#     entropy_data.append(f"CLICK-{button}-{pressed}-{t}")

# def on_scroll(x, y, dx, dy):
#     t = time.time_ns()
#     entropy_data.append(f"SCROLL-{dx}-{dy}-{t}")

# # ---------- Keyboard event handlers ----------
# def on_press(key):
#     t = time.time_ns()
#     entropy_data.append(f"PRESS-{key}-{t}")

# def on_release(key):
#     t = time.time_ns()
#     entropy_data.append(f"RELEASE-{key}-{t}")

# ---------- Start listeners ----------
# mouse_listener = mouse.Listener(
#     on_move=on_move,
#     on_click=on_click,
#     on_scroll=on_scroll
# )
# keyboard_listener = keyboard.Listener(
#     on_press=on_press,
#     on_release=on_release
# )

# mouse_listener.start()
# keyboard_listener.start()

# ---------- Generate random bytes ----------
# def generate_random_bytes():
#     while True:
#         if entropy_data:
#             # Take a snapshot of current entropy
#             snapshot = ''.join(entropy_data).encode()
#             # Hash it to generate random bytes
#             random_bytes = hashlib.sha256(snapshot).digest()
#             print(f"Random bytes: {random_bytes.hex()}")
#             # Clear entropy_data to avoid reusing same events
#             entropy_data.clear()
#         time.sleep(2)  # Adjust frequency of random generation

# ---------- Run random generator in a separate thread ----------
# generator_thread = threading.Thread(target=generate_random_bytes, daemon=True)
# generator_thread.start()
