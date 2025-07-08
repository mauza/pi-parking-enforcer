#!/usr/bin/env python3
"""
Camera Reset Script for Pi Parking Enforcer
Helps resolve camera conflicts and reset camera state
"""

import subprocess
import time
import sys
import os

def check_camera_processes():
    """Check what processes are using the camera"""
    print("🔍 Checking for processes using camera...")
    try:
        result = subprocess.run(['lsof', '/dev/video0'], capture_output=True, text=True)
        if result.stdout:
            print("Processes using camera:")
            print(result.stdout)
            return True
        else:
            print("✅ No processes using camera")
            return False
    except FileNotFoundError:
        print("⚠️  lsof not available, skipping process check")
        return False

def stop_pipewire():
    """Stop PipeWire services that might be using the camera"""
    print("🛑 Stopping PipeWire services...")
    services = ['pipewire', 'pipewire-pulse', 'pipewire-media-session']
    
    for service in services:
        try:
            result = subprocess.run(['systemctl', 'stop', service], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Stopped {service}")
            else:
                print(f"⚠️  Could not stop {service}: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Error stopping {service}: {e}")
    
    time.sleep(2)

def reset_camera_devices():
    """Reset camera devices by unloading and reloading modules"""
    print("🔄 Resetting camera devices...")
    
    # Try to unload camera modules
    modules = ['bcm2835-v4l2', 'v4l2loopback']
    for module in modules:
        try:
            result = subprocess.run(['modprobe', '-r', module], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Unloaded {module}")
            else:
                print(f"⚠️  Could not unload {module}: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Error unloading {module}: {e}")
    
    time.sleep(1)
    
    # Try to reload camera modules
    for module in modules:
        try:
            result = subprocess.run(['modprobe', module], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Loaded {module}")
            else:
                print(f"⚠️  Could not load {module}: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Error loading {module}: {e}")
    
    time.sleep(2)

def test_camera():
    """Test if camera is working after reset"""
    print("🧪 Testing camera...")
    
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
        print("❌ PiCamera2 not available")
        return False
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def main():
    """Main reset function"""
    print("=" * 60)
    print("Pi Parking Enforcer - Camera Reset Tool")
    print("=" * 60)
    
    # Check if running as root (needed for some operations)
    if os.geteuid() != 0:
        print("⚠️  Some operations may require root privileges")
        print("   Run with 'sudo python3 reset_camera.py' if needed")
        print()
    
    # Step 1: Check current state
    check_camera_processes()
    print()
    
    # Step 2: Stop PipeWire
    stop_pipewire()
    print()
    
    # Step 3: Reset camera devices
    reset_camera_devices()
    print()
    
    # Step 4: Test camera
    if test_camera():
        print("\n🎉 Camera reset successful!")
        print("You can now restart the parking enforcer application.")
    else:
        print("\n❌ Camera reset failed.")
        print("Try the following:")
        print("1. Check camera hardware connection")
        print("2. Reboot the system")
        print("3. Check camera permissions")
        print("4. Run 'sudo python3 reset_camera.py' for full reset")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 