#!/usr/bin/env python3
"""
Simple camera test to diagnose frame reading issues
"""

import cv2
import time
from config import Config

def test_camera_frames():
    """Test camera frame reading"""
    print("Testing camera frame reading...")
    print(f"Camera index: {Config.CAMERA_INDEX}")
    print(f"Resolution: {Config.CAMERA_WIDTH}x{Config.CAMERA_HEIGHT}")
    print(f"Frame rate: {Config.FRAME_RATE}")
    
    # Initialize camera
    camera = cv2.VideoCapture(Config.CAMERA_INDEX)
    
    # Set camera properties
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, Config.FRAME_RATE)
    
    # Try different camera backends
    backends = [
        cv2.CAP_V4L2,  # Video4Linux2
        cv2.CAP_ANY,   # Auto-detect
    ]
    
    for backend in backends:
        print(f"\nTrying backend: {backend}")
        camera = cv2.VideoCapture(Config.CAMERA_INDEX, backend)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
        camera.set(cv2.CAP_PROP_FPS, Config.FRAME_RATE)
        
        if not camera.isOpened():
            print(f"  FAILED: Could not open camera with backend {backend}")
            camera.release()
            continue
        
        print(f"  SUCCESS: Camera opened with backend {backend}")
        
        # Test reading frames
        success_count = 0
        for i in range(10):
            ret, frame = camera.read()
            if ret:
                success_count += 1
                print(f"    Frame {i+1}: SUCCESS - Shape: {frame.shape}")
            else:
                print(f"    Frame {i+1}: FAILED")
            time.sleep(0.1)
        
        print(f"  Summary: {success_count}/10 frames successful")
        
        if success_count > 0:
            print(f"  Camera working with backend {backend}")
            camera.release()
            return True
        
        camera.release()
    
    print("\nAll backends failed")
    return False

if __name__ == "__main__":
    test_camera_frames() 