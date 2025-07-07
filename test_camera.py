#!/usr/bin/env python3
"""
Improved camera test for USB webcams (Logitech C920)
"""

import cv2
import time
from config import Config

def test_camera_improved():
    """Test camera with improved settings for USB webcams"""
    print("Testing camera with improved USB webcam settings...")
    print(f"Camera index: {Config.CAMERA_INDEX}")
    print(f"Resolution: {Config.CAMERA_WIDTH}x{Config.CAMERA_HEIGHT}")
    print(f"Frame rate: {Config.FRAME_RATE}")
    
    # Initialize camera
    camera = cv2.VideoCapture(Config.CAMERA_INDEX)
    
    if not camera.isOpened():
        print("FAILED: Could not open camera")
        return False
    
    print("SUCCESS: Camera opened")
    
    # Set camera properties for USB webcam
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, Config.FRAME_RATE)
    
    # Set buffer size to 1 to reduce latency
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # Try to set MJPG format for better compatibility
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    
    # Allow camera to warm up
    print("Warming up camera...")
    time.sleep(2)
    
    # Test reading frames
    success_count = 0
    for i in range(10):
        ret, frame = camera.read()
        if ret and frame is not None:
            success_count += 1
            print(f"  Frame {i+1}: SUCCESS - Shape: {frame.shape}")
        else:
            print(f"  Frame {i+1}: FAILED")
        time.sleep(0.2)
    
    print(f"Summary: {success_count}/10 frames successful")
    
    if success_count > 0:
        print("Camera working with improved settings!")
        camera.release()
        return True
    else:
        print("Camera still not working")
        camera.release()
        return False

def test_different_formats():
    """Test different camera formats"""
    print("\nTesting different camera formats...")
    
    formats = [
        ('MJPG', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')),
        ('YUYV', cv2.VideoWriter_fourcc('Y', 'U', 'Y', 'V')),
        ('H264', cv2.VideoWriter_fourcc('H', '2', '6', '4')),
    ]
    
    for format_name, fourcc in formats:
        print(f"\nTrying format: {format_name}")
        camera = cv2.VideoCapture(Config.CAMERA_INDEX)
        
        if not camera.isOpened():
            print(f"  FAILED: Could not open camera")
            camera.release()
            continue
        
        # Set format
        camera.set(cv2.CAP_PROP_FOURCC, fourcc)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
        camera.set(cv2.CAP_PROP_FPS, Config.FRAME_RATE)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Test reading frames
        success_count = 0
        for i in range(5):
            ret, frame = camera.read()
            if ret and frame is not None:
                success_count += 1
                print(f"    Frame {i+1}: SUCCESS - Shape: {frame.shape}")
            else:
                print(f"    Frame {i+1}: FAILED")
            time.sleep(0.2)
        
        print(f"  Summary: {success_count}/5 frames successful")
        
        if success_count > 0:
            print(f"  {format_name} format works!")
            camera.release()
            return format_name
        
        camera.release()
    
    return None

if __name__ == "__main__":
    # Test with improved settings
    if test_camera_improved():
        print("\nCamera is working with improved settings!")
    else:
        print("\nTrying different formats...")
        working_format = test_different_formats()
        if working_format:
            print(f"\nCamera works with {working_format} format")
        else:
            print("\nNo working configuration found") 