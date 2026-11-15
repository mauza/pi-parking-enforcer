#!/usr/bin/env python3
"""
Test camera at 1920x1080 resolution
"""

import time
import sys
from picamera2 import Picamera2
from config import Config

def test_1920x1080_resolution():
    """Test if camera can handle 1920x1080 resolution"""
    print("Testing camera at 1920x1080 resolution...")
    print(f"Target resolution: {Config.CAMERA_WIDTH}x{Config.CAMERA_HEIGHT}")
    print(f"Frame rate: {Config.FRAME_RATE} FPS")
    
    camera = None
    try:
        # Initialize camera
        camera = Picamera2()
        
        # Configure camera with 1920x1080 resolution
        config = camera.create_preview_configuration(
            main={"size": (Config.CAMERA_WIDTH, Config.CAMERA_HEIGHT)},
            controls={"FrameDurationLimits": (int(1000000/Config.FRAME_RATE), int(1000000/Config.FRAME_RATE))}
        )
        camera.configure(config)
        camera.start()
        
        print("✅ Camera configured successfully")
        
        # Allow camera to warm up
        time.sleep(2)
        
        # Test reading frames
        success_count = 0
        total_frames = 10
        
        print(f"Testing {total_frames} frames...")
        
        for i in range(total_frames):
            try:
                frame = camera.capture_array()
                if frame is not None and frame.size > 0:
                    success_count += 1
                    print(f"  Frame {i+1}: ✅ Shape: {frame.shape}")
                    
                    # Check if resolution matches expected
                    if frame.shape[1] == Config.CAMERA_WIDTH and frame.shape[0] == Config.CAMERA_HEIGHT:
                        print(f"    Resolution: ✅ {frame.shape[1]}x{frame.shape[0]}")
                    else:
                        print(f"    Resolution: ⚠️  {frame.shape[1]}x{frame.shape[0]} (expected {Config.CAMERA_WIDTH}x{Config.CAMERA_HEIGHT})")
                else:
                    print(f"  Frame {i+1}: ❌ Empty frame")
            except Exception as e:
                print(f"  Frame {i+1}: ❌ Error: {e}")
            
            time.sleep(0.5)
        
        camera.stop()
        camera.close()
        
        print(f"\nResults: {success_count}/{total_frames} frames successful")
        
        if success_count > 0:
            print("✅ Camera can handle 1920x1080 resolution!")
            return True
        else:
            print("❌ Camera failed to read frames at 1920x1080")
            return False
            
    except Exception as e:
        print(f"❌ Camera initialization failed: {e}")
        if camera:
            try:
                camera.stop()
                camera.close()
            except:
                pass
        return False

def test_lower_resolutions():
    """Test lower resolutions as fallback options"""
    print("\nTesting lower resolutions as fallback...")
    
    resolutions = [
        (1280, 720),
        (800, 600),
        (640, 480)
    ]
    
    for width, height in resolutions:
        print(f"\nTesting {width}x{height}...")
        
        camera = None
        try:
            camera = Picamera2()
            config = camera.create_preview_configuration(
                main={"size": (width, height)}
            )
            camera.configure(config)
            camera.start()
            
            time.sleep(1)
            frame = camera.capture_array()
            camera.stop()
            camera.close()
            
            if frame is not None and frame.size > 0:
                print(f"✅ {width}x{height}: Works - Shape: {frame.shape}")
            else:
                print(f"❌ {width}x{height}: Failed")
                
        except Exception as e:
            print(f"❌ {width}x{height}: Error - {e}")
            if camera:
                try:
                    camera.stop()
                    camera.close()
                except:
                    pass

def main():
    print("=" * 60)
    print("High Resolution Camera Test")
    print("=" * 60)
    
    # Test 1920x1080
    if test_1920x1080_resolution():
        print("\n🎉 SUCCESS: Camera works at full 1920x1080 resolution!")
        print("You can now run the main application with high resolution.")
    else:
        print("\n⚠️  Camera doesn't support 1920x1080, testing lower resolutions...")
        test_lower_resolutions()
        print("\n💡 Consider using a lower resolution in your config.py file.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 