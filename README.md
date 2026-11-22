# Webcam TRNG — Linux

## Start

1. Install Python 3 and a working OpenCV desktop environment.
2. Run `python -m pip install -r requirements.txt` (prefer an isolated environment on distribution-managed Python installations).
3. Put the files you want to encrypt into `input/`.
4. From this project's directory, run `python main.py`.

- Camera: Logitech C170 via `/dev/video2` with V4L2. The device path is unchanged.
- A key is only generated when you choose **3. New key**. It is saved to `key/key_DDMMYYYY`.
- Encryption saves `input/original.ext.enc`; decryption saves `output/original.ext`.
- Exit with **4. Exit** to see session statistics; counters reset on each launch.
- Capture durations include stabilization: key 5s + 10s; nonce 3s + 3s.

**Important:** Generating a new key replaces the active key, so older encrypted files require a retained copy of their original key. A date is a label, not a unique key ID (a second key on the same date reuses the name). This experimental webcam entropy source has not been validated for production cryptographic security.
