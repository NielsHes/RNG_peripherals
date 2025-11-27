import numpy as np
from pynput import mouse, keyboard
import sys
import time
import atexit
import pyautogui
import csv
from datetime import datetime
import time as tm

# Maybe use fan rotation speed peripheral if possible? nope
HEADS, TAILS = 0, 0

BIT_SIZE = 256
IMG_SIZE, N = 64, 64
BLOCK_SIZE = 4
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
RAND_NUMBER = 0
MASK = 2**BIT_SIZE - 1
K = 5000
EVENTS = []
CSV_FILE = ""
VALUE = 0
KEY_TO_VALUE = {}  # EMPTY AFTER EACH ROUND?

# Thread-safe entropy storage
IMAGE_MOUSE = [[" " for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]
IMAGE_KEYBOARD = [[" " for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]


# Return milliseconds since epoch
def get_milliseconds():
    return int(tm.time() * 1000)


# Write random number to TXT file
def write_rn(peripheral, active_idle, number):
    with open(
        f"{peripheral}_{active_idle}_rns.txt", "a", newline="", encoding="utf-8"
    ) as file:
        file.write(f"{number}\n")


# Write to CSV file
def log_event(peripheral, event, details):
    timestamp = datetime.now().isoformat(timespec="milliseconds")
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, peripheral, event, details])


# Map mouse coordinates on screen to 64x64 grid
def map_mouse_to_image(x, y):
    x_small = int(x / SCREEN_WIDTH * IMG_SIZE)
    y_small = int(y / SCREEN_HEIGHT * IMG_SIZE)

    # Clamp values just in case
    x_small = min(max(x_small, 0), IMG_SIZE - 1)
    y_small = min(max(y_small, 0), IMG_SIZE - 1)

    return x_small, y_small


# Compute the XOR of two images
def xor_images(image1, image2):
    xor_image = [[" " for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]

    for i in range(IMG_SIZE):
        for j in range(IMG_SIZE):
            if (image1[i][j] == "*" and not image2[i][j] == "*") or (
                not image1[i][j] == "*" and image2[i][j] == "*"
            ):

                xor_image[i][j] = "*"

    return xor_image


# Mapping the IMAGE to a 256 bit RAND_NUMBER
def map_image_to_256(image, peripheral, active_idle):
    global HEADS, TAILS
    rand_number = 0

    for i in range(0, IMG_SIZE, 4):
        for j in range(0, IMG_SIZE, 4):

            count = 0
            for x in range(4):
                for y in range(4):
                    if image[i + x][j + y] == "*":
                        count += 1

            if (count % 2) == 1:
                # print(i/4, j/4, count)
                rand_number |= 1 << int(i / 4) * BLOCK_SIZE**2 + int(j / 4)

    rand_number &= MASK
    if rand_number % 100 >= 50:
        print("HEADS")
        HEADS += 1
    else:
        print("TAILS")
        TAILS += 1

    write_rn(peripheral, active_idle, rand_number)


# Chaotic map of IMAGE (WORK IN PROGRESS)
def chaotic_map():
    global IMAGE_MOUSE
    mapping = [[(-1, -1) for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]

    for x in range(IMG_SIZE):
        for y in range(IMG_SIZE):
            x_mapped = (x + y) % N
            y_mapped = (
                y + K * np.sin(N / 2 * np.pi)
            ) % N  # Apparently the formula in the paper doesn't make sense
            mapping[x][y] = (x_mapped, y_mapped)

    for _ in range(50):
        image_copy = IMAGE_MOUSE.copy()
        for x in range(IMG_SIZE):
            for y in range(IMG_SIZE):
                x_new = mapping[x][y][0]
                y_new = mapping[x][y][1]
                image_copy[x_new][y_new] = IMAGE_MOUSE[x][y]
        IMAGE_MOUSE = image_copy


# Print all the tracked mouse coordinates
def print_trackpad(image):
    for i in range(IMG_SIZE):
        for j in range(IMG_SIZE):
            print(image[i][j], end=" ")
        print()


# Action on move of mouse
def on_move(x, y, injected):
    log_event("mouse", "move", f"{x}, {y}")

    x, y = map_mouse_to_image(x, y)
    IMAGE_MOUSE[y][x] = "*"

    # print('Pointer moved to {}; it was {}'.format(
    #     (x, y), 'faked' if injected else 'not faked'))


# Action on click of mouse
def on_click(x, y, button, pressed, injected):
    details = "pressed" if pressed else "released"
    log_event("mouse", "click", f"{button} {details} at {x}, {y}")

    # print('{} at {}; it was {}'.format(
    #     'Pressed' if pressed else 'Released',
    #     (x, y), 'faked' if injected else 'not faked'))


# Action on scroll of mouse
def on_scroll(x, y, dx, dy, injected):
    log_event("mouse", "scroll", f"{dx}, {dy} at {x}, {y}")

    # print('Scrolled {} and {} at {}; it was {}'.format(
    #     'down' if dy < 0 else 'up', 'left' if dx < 0 else 'right',
    #     (x, y), 'faked' if injected else 'not faked'))


# Action on press of keyboard key
def on_press(key):
    global VALUE

    log_event("keyboard", "press", str(key))

    if key not in KEY_TO_VALUE:
        VALUE += 1
        KEY_TO_VALUE[key] = VALUE

    unique_value_image = KEY_TO_VALUE[key] * get_milliseconds() % IMG_SIZE**2
    y = unique_value_image // IMG_SIZE
    x = unique_value_image % IMG_SIZE
    IMAGE_KEYBOARD[y][x] = "*"

    # print(f'Key {key} pressed')  # Print pressed key


# Action on release of keyboard key
def on_release(key):
    log_event("keyboard", "release", str(key))

    # print(f'Key {key} released')  # Print released key
    if str(key) == "Key.esc":  # Stop listener on ESC
        return False


def main():

    global CSV_FILE
    global IMAGE_MOUSE, IMAGE_KEYBOARD

    print(f"Screen size: {SCREEN_WIDTH}x{SCREEN_HEIGHT} pixels")

    active_idle = "active"

    if len(sys.argv) > 1:
        if sys.argv[2] == "idle":
            active_idle = "idle"
        elif sys.argv[2] != "active":
            exit()

    CSV_FILE = f"{active_idle}_interactions.csv"

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "peripheral", "event", "details"])

    for peripheral in ["mouse", "keyboard", "combination"]:
        with open(
            f"{peripheral}_{active_idle}_rns.txt", "w", newline="", encoding="utf-8"
        ) as file:
            file.write("")

    # Mouse listener
    mouse_listener = mouse.Listener(
        on_move=on_move, on_click=on_click, on_scroll=on_scroll
    )

    # Keyboard listener
    keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)

    # Start listening
    mouse_listener.start()
    keyboard_listener.start()

    # Actions on program exit
    def on_exit():
        print("\nProgram exiting. Stopping listeners...")
        mouse_listener.stop()
        keyboard_listener.stop()
        print_trackpad(IMAGE_MOUSE)
        print()
        print_trackpad(IMAGE_KEYBOARD)
        print(HEADS, TAILS)

    atexit.register(on_exit)

    try:
        while True:
            time.sleep(5)
            map_image_to_256(IMAGE_MOUSE, "mouse", active_idle)
            map_image_to_256(IMAGE_KEYBOARD, "keyboard", active_idle)
            map_image_to_256(
                xor_images(IMAGE_MOUSE, IMAGE_KEYBOARD), "combination", active_idle
            )
            IMAGE_MOUSE = [[" " for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]
            IMAGE_KEYBOARD = [[" " for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Exiting...")


if __name__ == "__main__":
    main()
