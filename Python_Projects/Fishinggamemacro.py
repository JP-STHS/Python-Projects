import tkinter as tk
import threading
import time
from pynput.mouse import Controller, Button

# Mouse controller
mouse = Controller()

# Global flag for stopping
running = False

# Macro logic
def macro_task(hold_time=2, wait_time=60):
    global running
    while running:
        # Click and hold
        mouse.press(Button.left)
        print("Mouse held down")

        time.sleep(hold_time)

        # Release
        mouse.release(Button.left)
        print("Mouse released")

        # Wait before repeating
        for i in range(wait_time):
            if not running:  # early stop
                break
            time.sleep(1)

# Start macro
def start_macro():
    global running
    if not running:
        running = True
        threading.Thread(target=macro_task, daemon=True).start()

# Stop macro
def stop_macro():
    global running
    running = False
    print("Stopped")

# UI
root = tk.Tk()
root.title("Mouse Macro")

start_button = tk.Button(root, text="▶ Play", command=start_macro, width=15, height=2, bg="green", fg="white")
start_button.pack(pady=10)

stop_button = tk.Button(root, text="■ Stop", command=stop_macro, width=15, height=2, bg="red", fg="white")
stop_button.pack(pady=10)

root.mainloop()
