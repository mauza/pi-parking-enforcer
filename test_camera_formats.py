#!/usr/bin/env python3
"""
Test different camera formats for Raspberry Pi
"""

import cv2
import time
from config import Config

def test_camera_formats():
    """Test different camera formats and settings"""
    print("Testing different camera formats...")
    
    # Try different resolutions and formats
    test_configs = [
        {"width": 640, "height": 480, "fps": 30},
        {"width": 640, "height": 480, "fps": 15},
        {"width": 320, "height": 240, "fps": 30},
        {"width": 1280, "height": 720, "fps": 30},
    ]
    
    for config in test_configs:
        print(f"\nTrying config: {config['width']}x{config['height']} @ {config['fps']}fps")
        
        camera = cv2.VideoCapture(Config.CAMERA_INDEX)
        
        # Set properties
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, config['width'])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config['height'])
        camera.set(cv2.CAP_PROP_FPS, config['fps'])
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not camera.isOpened():
            print(f"  FAILED: Could not open camera")
            camera.release()
            continue
        
        print(f"  SUCCESS: Camera opened")
        
        # Test reading frames
        success_count = 0
        for i in range(5):
            ret, frame = camera.read()
            if ret:
                success_count += 1
                print(f"    Frame {i+1}: SUCCESS - Shape: {frame.shape}")
            else:
                print(f"    Frame {i+1}: FAILED")
            time.sleep(0.2)  # Longer delay
        
        print(f"  Summary: {success_count}/5 frames successful")
        
        if success_count > 0:
            print(f"  WORKING CONFIG FOUND!")
            camera.release()
            return config
        
        camera.release()
    
    print("\nAll configs failed")
    return None

def test_with_picamera():
    """Test using picamera2 library if available"""
    try:
        print("\nTrying picamera2...")
        from picamera2 import Picamera2
        print("picamera2 imported successfully")
        
        picam2 = Picamera2()
        print("Picamera2 instance created")
        
        config = picam2.create_preview_configuration()
        print("Preview configuration created")
        
        picam2.configure(config)
        print("Camera configured")
        
        picam2.start()
        print("Camera started")
        
        # Test reading frames
        success_count = 0
        for i in range(5):
            try:
                frame = picam2.capture_array()
                if frame is not None and frame.size > 0:
                    success_count += 1
                    print(f"    Frame {i+1}: SUCCESS - Shape: {frame.shape}")
                else:
                    print(f"    Frame {i+1}: FAILED - Frame is None or empty")
            except Exception as e:
                print(f"    Frame {i+1}: FAILED - Error: {e}")
            time.sleep(0.2)
        
        print(f"  Summary: {success_count}/5 frames successful")
        picam2.stop()
        
        if success_count > 0:
            print("  picamera2 works!")
            return True
            
    except ImportError as e:
        print(f"picamera2 import failed: {e}")
    except Exception as e:
        print(f"picamera2 failed: {e}")
        import traceback
        traceback.print_exc()
    
    return False

if __name__ == "__main__":
    # Test OpenCV with different formats
    working_config = test_camera_formats()
    
    # Test picamera2 as alternative
    test_with_picamera()
    
    if working_config:
        print(f"\nRecommended config: {working_config}")
    else:
        print("\nNo working configuration found") 