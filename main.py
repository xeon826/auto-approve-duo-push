import subprocess
import time
import cv2
import numpy as np
from PIL import ImageGrab, Image

# Define the target sequence to detect in dbus-monitor output
target_sequence = [
    "kdeconnect",
    "Duo Mobile",
    "1",
    "Tap To View Actions",
]



def check_sequence(lst, sequence):
    seq_len = len(sequence)
    # Slide over the list with a window the size of the sequence
    for i in range(len(lst) - seq_len + 1):
        if lst[i : i + seq_len] == sequence:
            return True
    return False


def get_mouse_position():
    """Get the current mouse position using xdotool."""
    output = subprocess.run(
        ["xdotool", "getmouselocation", "--shell"], capture_output=True, text=True
    )
    lines = output.stdout.splitlines()
    x = int(lines[0].split("=")[1])
    y = int(lines[1].split("=")[1])
    return x, y


def run_dbus_monitor():
    buffer = []
    # The shell command to run
    command = """
    dbus-monitor "interface='org.freedesktop.Notifications'" \
    | grep --line-buffered "string" \
    | grep --line-buffered -e method -e ":" -e '""' -e urgency -e notify -v \
    | grep --line-buffered -oPi '.*(?=string)|(?<=string).*' \
    | grep --line-buffered -v '^\\s*$'
    """
    # Start the command as a subprocess
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    try:
        for line in process.stdout:
            # Strip newline characters and add line to the buffer
            line = line.strip()
            if line:
                # Add line to the buffer and trim buffer to the length of the target sequence
                line = line.replace('"', "")
                buffer.append(line)
                print(buffer)

                # Check if the buffer matches the target sequence
                if check_sequence(buffer, target_sequence):
                    print("Target sequence detected!")

                    time.sleep(0.2)
                    # Get the current mouse position
                    original_x, original_y = get_mouse_position()
                    click_image_on_screen("tap-to-view-actions.png")
                    time.sleep(0.8)
                    click_image_on_screen("approve.png")

                    subprocess.run(["xdotool", "mousemove", str(original_x), str(original_y)])
                    print(f"Mouse returned to original position: ({original_x}, {original_y})")
                    # Execute an action here, e.g., run a command or print a message
                    # Reset the buffer if needed
                    buffer.clear()

    except KeyboardInterrupt:
        # Handle keyboard interrupt (Ctrl+C) to terminate the monitoring
        print("Monitoring stopped.")

    finally:
        # Terminate the process if it's still running
        process.terminate()


def click_image_on_screen(target_image_path, confidence=0.8):
    # Capture the screen using Pillow (replacing pyautogui.screenshot)
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

    # Load the target image and convert it to grayscale
    target_image = cv2.imread(target_image_path, cv2.IMREAD_GRAYSCALE)
    w, h = target_image.shape[::-1]

    # Perform template matching
    res = cv2.matchTemplate(screenshot_gray, target_image, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= confidence)  # Find locations where match exceeds confidence

    # If we have at least one match
    if len(loc[0]) > 0:
        # Get the first match (top-left corner)
        y, x = loc[0][0], loc[1][0]
        # Calculate the center of the matched area
        center_x, center_y = x + w // 2, y + h // 2

        # Move the mouse to the matched location using xdotool
        subprocess.run(["xdotool", "mousemove", str(center_x), str(center_y)])
        subprocess.run(["xdotool", "click", "1"])
        print(f"Found image at: ({center_x}, {center_y})")
        return (center_x, center_y)
    else:
        print("Target image not found on the screen.")
        return None


# Run the monitoring function
run_dbus_monitor()
