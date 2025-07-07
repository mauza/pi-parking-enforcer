#!/usr/bin/env python3
"""
Simple camera test to fix frame reading issues
"""

import cv2
import time
import subprocess
import os

def check_camera_processes():
    """Check if any processes are using the camera"""
    try:
        result = subprocess.run(['lsof', '/dev/video0'], capture_output=True, text=True)
        if result.stdout:
            print("Processes using camera:")
            print(result.stdout)
            return True
        else:
            print("No processes using camera")
            return False
    except FileNotFoundError:
        print("lsof not available, skipping process check")
        return False

def test_camera_basic():
    """Test camera with minimal settings"""
    print("Testing camera with minimal settings...")
    
    # Check for processes first
    check_camera_processes()
    
    # Try to release any existing camera handles
    try:
        temp_camera = cv2.VideoCapture(0)
        temp_camera.release()
        time.sleep(1)
    except:
        pass
    
    # Initialize camera
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        print("FAILED: Could not open camera")
        return False
    
    print("SUCCESS: Camera opened")
    
    # Don't set any properties initially
    print("Testing frame reading without setting properties...")
    
    success_count = 0
    for i in range(5):
        ret, frame = camera.read()
        if ret and frame is not None:
            success_count += 1
            print(f"  Frame {i+1}: SUCCESS - Shape: {frame.shape}")
        else:
            print(f"  Frame {i+1}: FAILED")
        time.sleep(0.5)
    
    camera.release()
    
    if success_count > 0:
        print(f"Basic camera test: {success_count}/5 frames successful")
        return True
    else:
        print("Basic camera test failed")
        return False

def test_camera_with_properties():
    """Test camera with properties set"""
    print("\nTesting camera with properties set...")
    
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        print("FAILED: Could not open camera")
        return False
    
    # Set basic properties
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)
    
    # Allow time for properties to take effect
    time.sleep(1)
    
    success_count = 0
    for i in range(5):
        ret, frame = camera.read()
        if ret and frame is not None:
            success_count += 1
            print(f"  Frame {i+1}: SUCCESS - Shape: {frame.shape}")
        else:
            print(f"  Frame {i+1}: FAILED")
        time.sleep(0.5)
    
    camera.release()
    
    if success_count > 0:
        print(f"Camera with properties: {success_count}/5 frames successful")
        return True
    else:
        print("Camera with properties failed")
        return False

def test_camera_with_timeout():
    """Test camera with timeout handling"""
    print("\nTesting camera with timeout handling...")
    
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        print("FAILED: Could not open camera")
        return False
    
    # Set a timeout for frame reading
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    success_count = 0
    for i in range(5):
        # Try to read with a timeout
        start_time = time.time()
        ret = False
        frame = None
        
        while time.time() - start_time < 2.0:  # 2 second timeout
            ret, frame = camera.read()
            if ret and frame is not None:
                break
            time.sleep(0.1)
        
        if ret and frame is not None:
            success_count += 1
            print(f"  Frame {i+1}: SUCCESS - Shape: {frame.shape}")
        else:
            print(f"  Frame {i+1}: FAILED (timeout)")
        time.sleep(0.5)
    
    camera.release()
    
    if success_count > 0:
        print(f"Camera with timeout: {success_count}/5 frames successful")
        return True
    else:
        print("Camera with timeout failed")
        return False

if __name__ == "__main__":
    print("=== Camera Diagnostic Test ===")
    
    # Test 1: Basic camera test
    if test_camera_basic():
        print("\n✅ Basic camera test passed!")
    else:
        print("\n❌ Basic camera test failed")
    
    # Test 2: Camera with properties
    if test_camera_with_properties():
        print("\n✅ Camera with properties test passed!")
    else:
        print("\n❌ Camera with properties test failed")
    
    # Test 3: Camera with timeout
    if test_camera_with_timeout():
        print("\n✅ Camera with timeout test passed!")
    else:
        print("\n❌ Camera with timeout test failed")
    
    print("\n=== Test Complete ===") 