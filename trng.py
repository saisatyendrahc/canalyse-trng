"""Webcam sampling, random-number extraction, and AES key derivation."""

import hashlib
import time

import cv2


CAMERA_DEVICE = 0  # Windows webcam index for Logitech Webcam C170 (adjust if needed).
WINDOW_NAME = "Logitech C170 - TRNG Analysis"


def canalyse(stabilize_seconds, collect_seconds):
    """Yield all grayscale pixel bytes captured after webcam stabilization."""
    camera = cv2.VideoCapture(CAMERA_DEVICE, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera.release()
        raise RuntimeError(f"Could not open webcam: {CAMERA_DEVICE}")

    try:
        print(f"Webcam: Logitech C170 (Windows camera index {CAMERA_DEVICE})")
        print(f"Stabilizing for {stabilize_seconds} seconds...")
        end = time.monotonic() + stabilize_seconds
        while time.monotonic() < end:
            success, frame = camera.read()
            if not success:
                raise RuntimeError("Could not read a webcam frame.")
            cv2.imshow(WINDOW_NAME, frame)
            cv2.waitKey(1)

        print(f"Collecting pixels for {collect_seconds} seconds...")
        end = time.monotonic() + collect_seconds
        while time.monotonic() < end:
            success, frame = camera.read()
            if not success:
                raise RuntimeError("Could not read a webcam frame.")
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cv2.imshow(WINDOW_NAME, gray)
            cv2.waitKey(1)
            yield gray.tobytes()
    finally:
        camera.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)  # Flush the GUI event queue so the window closes.


def trng(pixel_frames):
    """Stream captured pixel bytes through SHA-256 and return a 256-bit integer."""
    hasher = hashlib.sha256()
    count = 0
    for pixels in pixel_frames:
        hasher.update(pixels)
        count += 1

    if count == 0:
        raise RuntimeError("No grayscale frames were captured.")

    print(f"Processed {count} grayscale frames.")
    return int.from_bytes(hasher.digest(), "big")


def keygen(random_number):
    """Represent the 256-bit webcam-derived number as a 32-byte AES key."""
    return random_number.to_bytes(32, "big")
