# %%

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

import cv2

SAVE_DIR = Path("snapshots_rtsp")
DEFAULT_DURATION = 10  # seconds
DEFAULT_FILEFORMAT = "jpg"
SUPPORTED_FORMATS = ["jpg", "mp4"]


def create_output_directory(path):
    os.makedirs(path, exist_ok=True)


def safe_filename(filename):
    return "".join(
        [c for c in filename if c.isalpha() or c.isdigit() or c in ("_", ".")]
    )


def save_snapshot(name: str, url: str, output_path: Path):
    """
    Save a snapshot from an RTSP stream to a file.

    Args:
        name (str): Name of the camera.
        url (str): RTSP URL of the camera.
        output_path (str): Output file path.
    """
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print(f"Error: Could not open video stream for URL: {url}")
        exit()

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # Wait a bit for keyframe
    t0 = time.time()
    frame = None
    while time.time() - t0 < 5:
        ok, frm = cap.read()
        if ok and frm is not None:
            frame = frm
            break
        time.sleep(0.05)

    success = cv2.imwrite(str(output_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    if not success:
        print(f"[{name}] Error: Could not write image to {output_path}")
    else:
        print(f"[{name}] Saved snapshot: {output_path} ({frame.shape[1]}x{frame.shape[0]})")
    cap.release()


def save_video(name: str, url: str, duration_sec: int, output_path: Path, fps: int = 25):
    """
    Save a video stream to a file.

    Args:
        name (str): Name of the camera.
        url (str): RTSP URL of the camera.
        duration_sec (int): Duration to record (in seconds).
        output_path (str): Output file path.
        fps (int, optional): Frames per second for the output video. Defaults to 25.
    """
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        print(f"[{name}] Could not open {url}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"[{name}] Saving video to {output_path} for {duration_sec} seconds...")
    start_time = time.time()
    while time.time() - start_time < duration_sec:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    cap.release()
    out.release()
    print(f"[{name}] Saved video: {output_path}  ({width}x{height})")


def record_rtsp_stream(
    name: str, url: str, output_path: Path, fileformat: str, duration_sec: int
):
    """Record RTSP stream to a file.

    Args:
        name (str): Name of the camera.
        url (str): RTSP URL of the camera.
        out_path (str): Output file path.
        fileformat (str): File format (jpg or mp4).
        duration (int): Duration to record (in seconds).

    Raises:
        ValueError: If the file format is unsupported.
    """
    if fileformat == "jpg":
        save_snapshot(name, url, output_path)
    elif fileformat == "mp4":
        save_video(name, url, duration_sec, output_path)
    else:
        raise ValueError(f"Unsupported format: {fileformat}")


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Record RTSP camera stream to a file")
    parser.add_argument(
        "--config-file", required=True, help="Path to the JSON config file"
    )
    args = parser.parse_args()

    if not os.path.exists(args.config_file):
        raise FileNotFoundError(f"Config file not found: {args.config_file}")

    # Open config file
    with open(args.config_file, "r") as f:
        try:
            devices = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")

    if not devices:
        print("No devices found in config file. Nothing to do.")
        return

    # Iterate devices defined in config file
    for device in devices:
        camera_name = device.get("camera_name")
        camera_url = device.get("camera_url")
        directory = safe_filename(device.get("directory", ""))
        filename = device.get("filename", "video.mp4")
        fileformat = device.get("fileformat", "mp4")
        duration = int(device.get("duration", DEFAULT_DURATION))

        if not camera_url or not camera_name:
            print("[WARNING] Skipping device with missing camera_name or camera_url...")
            continue

        if fileformat not in SUPPORTED_FORMATS:
            print(
                f"Unsupported file format '{fileformat}', using default format: '{DEFAULT_FILEFORMAT}'"
            )
            fileformat = DEFAULT_FILEFORMAT

        if directory:
            os.makedirs(SAVE_DIR / directory, exist_ok=True)
            output_path = SAVE_DIR / directory
        else:
            output_path = SAVE_DIR

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Record the RTSP stream for each device
        record_rtsp_stream(
            camera_name,
            camera_url,
            output_path / f"{timestamp}_{filename}.{fileformat}",
            fileformat,
            duration,
        )


if __name__ == "__main__":
    create_output_directory(SAVE_DIR)
    main()
