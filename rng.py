import numpy as np
from pynput import mouse, keyboard
import os
import time
import pyautogui
import csv
import threading
from datetime import datetime
import time as tm
import clr
clr.AddReference(r'<PATH>/OpenHardwareMonitorLib') 
from OpenHardwareMonitor.Hardware import Computer, SensorType

BIT_SIZE = 256
IMG_SIZE, N = 64, 64
BLOCK_SIZE = 4
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
CHAOTIC_MAP = []
RAND_NUMBER = 0
MASK = 2**BIT_SIZE - 1
K = 5000
EVENTS = []
VALUE = 0
KEY_TO_VALUE = {}
ACTIVE_MOUSE, ACTIVE_KEYBOARD = False, False
PATH = os.getcwd() + "\data"
CSV_FILE = PATH + "\interactions.csv"

# Thread-safe entropy storage
IMAGE_MOUSE = [[' ' for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]
IMAGE_KEYBOARD = [[' ' for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]
IMAGE_SYSTEM_HW = [[' ' for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]

# Return milliseconds since epoch
def get_milliseconds():
    return int(tm.time() * 1000)


# Write random number to TXT file
def write_rn(number, peripheral):
    with open(f"{PATH}\{peripheral}_rns.txt", "a", newline="", encoding="utf-8") as file:
        file.write(f"{number}")


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


# Function mapping values to coordinates in 64x64 grid
def map_value_to_image(value, image):
    value %= IMG_SIZE**2
    y = value // IMG_SIZE
    x = value % IMG_SIZE
    image[y][x] = "*"


# Compute the XOR of two images
def xor_images(image1, image2):
    xor_image = [[" " for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]

    for i in range(IMG_SIZE):
        for j in range(IMG_SIZE):
            if (image1[i][j] == "*" and not image2[i][j] == "*") or (not image1[i][j] == "*" and image2[i][j] == "*"):

                xor_image[i][j] = "*"

    return xor_image


# Mapping the IMAGE to a 256 bit RAND_NUMBER
def map_image_to_256(image, peripheral):
    rand_number = ""
    indices = 0

    # Apply precomputed chaotic map to the image
    image = map_chaotic(image)

    for i in range(0, IMG_SIZE, 4):
        for j in range(0, IMG_SIZE, 4):

            count = 0
            for x in range(4):
                for y in range(4):
                    if image[i + x][j + y] == "*":
                        count += 1
                        indices += i+x + j+y

            if (count % 2) == 1:
                rand_number = "1" + rand_number
            else:
                rand_number = "0" + rand_number
    rand_number = "0b" + rand_number

    write_rn(rand_number, peripheral)


# Precompute chaotic map
def compute_chaotic_map():
    global CHAOTIC_MAP
    CHAOTIC_MAP = [[(x,y) for x in range(IMG_SIZE)] for y in range(IMG_SIZE)]
    
    # Compute chaotic map for 50 iterations
    for _ in range(50):
        for x in range(IMG_SIZE):
            for y in range(IMG_SIZE):
                x_map = CHAOTIC_MAP[x][y][0]
                y_map = CHAOTIC_MAP[x][y][1]
                x_new = int((x_map + y_map) % N)
                y_new = int((y_map + K * np.sin(N / 2 * np.pi)) % N)
                CHAOTIC_MAP[x][y] = (x_new, y_new)


# Chaotic map of IMAGE (WORK IN PROGRESS)
def map_chaotic(image):
    image_chaotic = [[' ' for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]

    for x in range(IMG_SIZE):
        for y in range(IMG_SIZE):
            x_map = CHAOTIC_MAP[x][y][0]
            y_map = CHAOTIC_MAP[x][y][1]
            image_chaotic[x_map][y_map] = image[x][y]

    return image_chaotic


# Print all the tracked mouse coordinates
def print_trackpad(image):
    for i in range(IMG_SIZE):
        for j in range(IMG_SIZE):
            print(image[i][j], end=" ")
        print()


# Action on move of mouse
def on_move(x, y, injected):
    global ACTIVE_MOUSE

    log_event("mouse", "move", f"{x}, {y}")
    ACTIVE_MOUSE = True

    x, y = map_mouse_to_image(x, y)
    IMAGE_MOUSE[y][x] = "*"


# Action on click of mouse
def on_click(x, y, button, pressed, injected):
    details = "pressed" if pressed else "released"
    log_event("mouse", "click", f"{button} {details} at {x}, {y}")


# Action on scroll of mouse
def on_scroll(x, y, dx, dy, injected):
    log_event("mouse", "scroll", f"{dx}, {dy} at {x}, {y}")


# Action on press of keyboard key
def on_press(key):
    global ACTIVE_KEYBOARD, VALUE

    log_event("keyboard", "press", str(key))
    ACTIVE_KEYBOARD = True

    # Map key to number if mapping does not exist
    if key not in KEY_TO_VALUE:
        VALUE += 1
        KEY_TO_VALUE[key] = VALUE
    
    # Map key press to coordinates in the grid
    value_key = KEY_TO_VALUE[key] * get_milliseconds()
    map_value_to_image(value_key, IMAGE_KEYBOARD)


# Action on release of keyboard key
def on_release(key):
    log_event("keyboard", "release", str(key))


# Retrieve system hardware peripheral information
def system_hardware_peripherals(stop_event):

    # Create computer instance to obtain hardware sensor information
    pc = Computer()
    pc.MainboardEnabled = True
    pc.CPUEnabled = True
    pc.GPUEnabled = True
    pc.Open()

    # Loop until SIGINT detected in main thread
    while not stop_event.is_set():
        sum = 0
        for hw in pc.Hardware:
            hw.Update()

            # Loop over all hardware sensors
            for sensor in hw.Sensors:
                if (sensor.SensorType == SensorType.Temperature or sensor.SensorType == SensorType.Load or
                    sensor.SensorType == SensorType.Clock or sensor.SensorType == SensorType.Power):
                    if sensor.Value:
                        sum += int(sensor.Value)

            # Loop over all subhardware sensors
            for sub in hw.SubHardware:
                sub.Update()
                for sensor in sub.Sensors:
                    if (sensor.SensorType == SensorType.Temperature or sensor.SensorType == SensorType.Load or
                        sensor.SensorType == SensorType.Clock or sensor.SensorType == SensorType.Power):
                        if sensor.Value:
                            sum += int(sensor.Value)

        # Map sum of hardware sensor values to coordinates in grid
        map_value_to_image(sum, IMAGE_SYSTEM_HW)


def main():

    global IMAGE_MOUSE, IMAGE_KEYBOARD, IMAGE_SYSTEM_HW
    global ACTIVE_MOUSE, ACTIVE_KEYBOARD
    
    print(f"Screen size: {SCREEN_WIDTH}x{SCREEN_HEIGHT} pixels")

    # Empty the files
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "peripheral", "event", "details"])

    for peripheral in ["mouse", "keyboard", "combination", "idle"]:
        with open(f"{PATH}\{peripheral}_rns.txt", "w", newline="", encoding="utf-8") as file:
            file.write("")

    # Compute the chaotic map
    compute_chaotic_map()

    stop_event = threading.Event()
    system_hardware_thread = threading.Thread(target=system_hardware_peripherals, name="System hardware peripherals", args=(stop_event,))

    # Mouse listener
    mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)

    # Keyboard listener
    keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)

    # Start recording and listening
    system_hardware_thread.start()
    mouse_listener.start()
    keyboard_listener.start()

    nr_m = nr_k = nr_c = nr_hw = 0

    # Keep program alive until keyboard interrupt
    try:
        while True:
            time.sleep(3)

            # Generate random numbers based on the registerd user activity
            if ACTIVE_MOUSE:
                nr_m += 1
                print("MOUSE", nr_m)
                map_image_to_256(IMAGE_MOUSE, "mouse")
            if ACTIVE_KEYBOARD:
                nr_k += 1
                print("KEYBOARD", nr_k)
                map_image_to_256(IMAGE_KEYBOARD, "keyboard")
            if ACTIVE_MOUSE and ACTIVE_KEYBOARD:
                nr_c += 1
                print("COMBINATION", nr_c)
                map_image_to_256(xor_images(IMAGE_MOUSE, IMAGE_KEYBOARD), "combination")            
            if not ACTIVE_MOUSE and not ACTIVE_KEYBOARD:
                nr_hw += 1
                print("IDLE", nr_hw)
                map_image_to_256(IMAGE_SYSTEM_HW, "idle")
            
            ACTIVE_MOUSE, ACTIVE_KEYBOARD = False, False
            IMAGE_MOUSE = [[' ' for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]
            IMAGE_KEYBOARD = [[' ' for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]
            IMAGE_SYSTEM_HW = [[' ' for _ in range(IMG_SIZE)] for _ in range(IMG_SIZE)]

    # SIGINT thrown by user
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Exiting...")
        stop_event.set()
        system_hardware_thread.join()
        mouse_listener.stop()
        keyboard_listener.stop()


if __name__ == "__main__":
    main()