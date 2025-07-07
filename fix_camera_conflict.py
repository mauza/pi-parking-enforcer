#!/usr/bin/env python3
"""
Fix camera conflicts with PipeWire and other processes
"""

import subprocess
import time
import sys

def check_camera_processes():
    """Check what processes are using the camera"""
    try:
        result = subprocess.run(['lsof', '/dev/video0'], capture_output=True, text=True)
        if result.stdout:
            print("Processes currently using camera:")
            print(result.stdout)
            return True
        else:
            print("No processes using camera")
            return False
    except FileNotFoundError:
        print("lsof not available")
        return False

def stop_pipewire():
    """Stop PipeWire to free up camera"""
    print("\nAttempting to stop PipeWire...")
    try:
        # Stop PipeWire
        subprocess.run(['systemctl', '--user', 'stop', 'pipewire'], check=False)
        subprocess.run(['systemctl', '--user', 'stop', 'pipewire-pulse'], check=False)
        subprocess.run(['systemctl', '--user', 'stop', 'wireplumber'], check=False)
        
        # Wait a moment
        time.sleep(2)
        
        print("PipeWire stopped")
        return True
    except Exception as e:
        print(f"Failed to stop PipeWire: {e}")
        return False

def start_pipewire():
    """Start PipeWire again"""
    print("\nStarting PipeWire again...")
    try:
        subprocess.run(['systemctl', '--user', 'start', 'pipewire'], check=False)
        subprocess.run(['systemctl', '--user', 'start', 'pipewire-pulse'], check=False)
        subprocess.run(['systemctl', '--user', 'start', 'wireplumber'], check=False)
        print("PipeWire restarted")
        return True
    except Exception as e:
        print(f"Failed to start PipeWire: {e}")
        return False

def test_camera_after_fix():
    """Test if camera works after stopping PipeWire"""
    print("\nTesting camera after stopping PipeWire...")
    
    try:
        from picamera2 import Picamera2
        
        camera = Picamera2()
        config = camera.create_preview_configuration()
        camera.configure(config)
        camera.start()
        
        # Try to read a frame
        frame = camera.capture_array()
        camera.stop()
        camera.close()
        
        if frame is not None and frame.size > 0:
            print(f"✅ Camera working! Frame shape: {frame.shape}")
            return True
        else:
            print("❌ Camera still not reading frames")
            return False
            
    except ImportError:
        print("PiCamera2 not available")
        return False
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def main():
    print("=== Camera Conflict Resolution ===")
    
    # Check current processes
    has_conflicts = check_camera_processes()
    
    if not has_conflicts:
        print("No camera conflicts detected")
        return
    
    print("\nThe camera is being used by PipeWire (audio/video system).")
    print("This prevents OpenCV from accessing the camera.")
    print("\nOptions:")
    print("1. Stop PipeWire temporarily (will disable audio)")
    print("2. Use a different camera")
    print("3. Configure PipeWire to not use the camera")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\nStopping PipeWire...")
        if stop_pipewire():
            print("\nTesting camera...")
            if test_camera_after_fix():
                print("\n✅ SUCCESS! Camera is now working.")
                print("Note: Audio is disabled. Run this script again to restart PipeWire.")
                
                restart = input("\nRestart PipeWire now? (y/n): ").strip().lower()
                if restart == 'y':
                    start_pipewire()
            else:
                print("\n❌ Camera still not working after stopping PipeWire")
                start_pipewire()  # Restart PipeWire
        else:
            print("\n❌ Failed to stop PipeWire")
    
    elif choice == "2":
        print("\nTo use a different camera:")
        print("1. Connect a different USB camera")
        print("2. Update CAMERA_INDEX in your .env file")
        print("3. Run the application again")
    
    elif choice == "3":
        print("\nTo configure PipeWire to not use the camera:")
        print("1. Edit ~/.config/pipewire/pipewire.conf")
        print("2. Add camera device to blacklist")
        print("3. Restart PipeWire")
        print("\nThis is more complex and may require system configuration.")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main() 