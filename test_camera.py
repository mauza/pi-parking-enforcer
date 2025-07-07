#!/usr/bin/env python3
"""
Simple camera test to fix frame reading issues using PiCamera2
"""

from picamera2 import Picamera2
import time
import subprocess
import os
import numpy as np

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
        temp_camera = Picamera2()
        temp_camera.close()
        time.sleep(1)
    except:
        pass
    
    # Initialize camera
    camera = Picamera2()
    
    try:
        # Configure camera with minimal settings
        config = camera.create_preview_configuration()
        camera.configure(config)
        camera.start()
        
        print("SUCCESS: Camera opened and started")
        
        # Don't set any properties initially
        print("Testing frame reading without setting properties...")
        
        success_count = 0
        for i in range(5):
            try:
                frame = camera.capture_array()
                if frame is not None and frame.size > 0:
                    success_count += 1
                    print(f"  Frame {i+1}: SUCCESS - Shape: {frame.shape}")
                else:
                    print(f"  Frame {i+1}: FAILED - Empty frame")
            except Exception as e:
                print(f"  Frame {i+1}: FAILED - {e}")
            time.sleep(0.5)
        
        camera.stop()
        camera.close()
        
        if success_count > 0:
            print(f"Basic camera test: {success_count}/5 frames successful")
            return True
        else:
            print("Basic camera test failed")
            return False
            
    except Exception as e:
        print(f"FAILED: Could not open camera - {e}")
        try:
            camera.close()
        except:
            pass
        return False

def test_camera_with_properties():
    """Test camera with properties set"""
    print("\nTesting camera with properties set...")
    
    camera = Picamera2()
    
    try:
        # Configure camera with specific properties
        config = camera.create_preview_configuration(
            main={"size": (640, 480)},
            controls={"FrameDurationLimits": (33333, 33333)}  # 30 FPS
        )
        camera.configure(config)
        camera.start()
        
        print("SUCCESS: Camera opened with properties")
        
        # Allow time for properties to take effect
        time.sleep(1)
        
        success_count = 0
        for i in range(5):
            try:
                frame = camera.capture_array()
                if frame is not None and frame.size > 0:
                    success_count += 1
                    print(f"  Frame {i+1}: SUCCESS - Shape: {frame.shape}")
                else:
                    print(f"  Frame {i+1}: FAILED - Empty frame")
            except Exception as e:
                print(f"  Frame {i+1}: FAILED - {e}")
            time.sleep(0.5)
        
        camera.stop()
        camera.close()
        
        if success_count > 0:
            print(f"Camera with properties: {success_count}/5 frames successful")
            return True
        else:
            print("Camera with properties failed")
            return False
            
    except Exception as e:
        print(f"FAILED: Could not open camera with properties - {e}")
        try:
            camera.close()
        except:
            pass
        return False

def test_camera_with_timeout():
    """Test camera with timeout handling"""
    print("\nTesting camera with timeout handling...")
    
    camera = Picamera2()
    
    try:
        # Configure camera with minimal buffer
        config = camera.create_preview_configuration(
            buffer_count=1
        )
        camera.configure(config)
        camera.start()
        
        print("SUCCESS: Camera opened with timeout handling")
        
        success_count = 0
        for i in range(5):
            # Try to read with a timeout
            start_time = time.time()
            frame = None
            success = False
            
            while time.time() - start_time < 2.0:  # 2 second timeout
                try:
                    frame = camera.capture_array()
                    if frame is not None and frame.size > 0:
                        success = True
                        break
                except Exception as e:
                    pass
                time.sleep(0.1)
            
            if success and frame is not None:
                success_count += 1
                print(f"  Frame {i+1}: SUCCESS - Shape: {frame.shape}")
            else:
                print(f"  Frame {i+1}: FAILED (timeout)")
            time.sleep(0.5)
        
        camera.stop()
        camera.close()
        
        if success_count > 0:
            print(f"Camera with timeout: {success_count}/5 frames successful")
            return True
        else:
            print("Camera with timeout failed")
            return False
            
    except Exception as e:
        print(f"FAILED: Could not open camera with timeout - {e}")
        try:
            camera.close()
        except:
            pass
        return False

def test_camera_formats():
    """Test different camera formats"""
    print("\nTesting different camera formats...")
    
    camera = Picamera2()
    
    try:
        # Test different resolutions
        resolutions = [
            (640, 480),
            (1280, 720),
            (1920, 1080)
        ]
        
        success_count = 0
        for width, height in resolutions:
            try:
                config = camera.create_preview_configuration(
                    main={"size": (width, height)}
                )
                camera.configure(config)
                camera.start()
                
                # Try to capture a frame
                frame = camera.capture_array()
                if frame is not None and frame.size > 0:
                    success_count += 1
                    print(f"  Resolution {width}x{height}: SUCCESS - Shape: {frame.shape}")
                else:
                    print(f"  Resolution {width}x{height}: FAILED - Empty frame")
                
                camera.stop()
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Resolution {width}x{height}: FAILED - {e}")
                try:
                    camera.stop()
                except:
                    pass
        
        camera.close()
        
        if success_count > 0:
            print(f"Camera formats test: {success_count}/{len(resolutions)} resolutions successful")
            return True
        else:
            print("Camera formats test failed")
            return False
            
    except Exception as e:
        print(f"FAILED: Could not test camera formats - {e}")
        try:
            camera.close()
        except:
            pass
        return False

if __name__ == "__main__":
    print("=== PiCamera2 Diagnostic Test ===")
    
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
    
    # Test 4: Camera formats
    if test_camera_formats():
        print("\n✅ Camera formats test passed!")
    else:
        print("\n❌ Camera formats test failed")
    
    print("\n=== Test Complete ===") 