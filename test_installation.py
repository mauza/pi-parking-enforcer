#!/usr/bin/env python3
"""
Test script for Pi Parking Enforcer installation
"""

import sys
import os
import importlib
import sqlite3
from pathlib import Path
import subprocess

def test_import(module_name, description):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {e}")
        return False

def test_uv_installation():
    """Test if uv is installed and working"""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ uv installed: {version}")
            return True
        else:
            print("❌ uv not working properly")
            return False
    except FileNotFoundError:
        print("❌ uv not found - please install uv first")
        return False

def test_database():
    """Test database functionality"""
    try:
        from database import ParkingDatabase
        db = ParkingDatabase()
        print("✅ Database module")
        return True
    except Exception as e:
        print(f"❌ Database module: {e}")
        return False

def test_config():
    """Test configuration loading"""
    try:
        from config import Config
        print(f"✅ Configuration loaded (Camera: {Config.CAMERA_INDEX}, Port: {Config.WEB_PORT})")
        return True
    except Exception as e:
        print(f"❌ Configuration: {e}")
        return False

def test_car_detector():
    """Test car detector initialization"""
    try:
        from car_detector import CarDetector
        detector = CarDetector()
        print("✅ Car detector initialized")
        return True
    except Exception as e:
        print(f"❌ Car detector: {e}")
        return False

def test_slack_integration():
    """Test Slack integration"""
    try:
        from slack_integration import SlackIntegration
        slack = SlackIntegration()
        print("✅ Slack integration initialized")
        return True
    except Exception as e:
        print(f"❌ Slack integration: {e}")
        return False

def test_web_interface():
    """Test web interface components"""
    try:
        from web_interface import app
        print("✅ Web interface initialized")
        return True
    except Exception as e:
        print(f"❌ Web interface: {e}")
        return False

def test_parking_monitor():
    """Test parking monitor"""
    try:
        from parking_monitor import ParkingMonitor
        monitor = ParkingMonitor()
        print("✅ Parking monitor initialized")
        return True
    except Exception as e:
        print(f"❌ Parking monitor: {e}")
        return False

def test_directories():
    """Test if required directories exist"""
    directories = ["logs", "captured_images", "templates", "static"]
    all_exist = True
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"✅ Directory: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
            all_exist = False
    
    return all_exist

def test_files():
    """Test if required files exist"""
    files = [
        "main.py",
        "config.py", 
        "database.py",
        "car_detector.py",
        "parking_monitor.py",
        "slack_integration.py",
        "web_interface.py",
        "pyproject.toml",
        "env.example",
        "templates/dashboard.html",
        "static/css/dashboard.css",
        "static/js/dashboard.js"
    ]
    
    all_exist = True
    for file in files:
        if os.path.exists(file):
            print(f"✅ File: {file}")
        else:
            print(f"❌ File missing: {file}")
            all_exist = False
    
    return all_exist

def test_virtual_environment():
    """Test if virtual environment exists"""
    if os.path.exists(".venv"):
        print("✅ Virtual environment (.venv) exists")
        return True
    else:
        print("❌ Virtual environment (.venv) not found")
        return False

def test_camera():
    """Test camera access"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                print("✅ Camera access successful")
                return True
            else:
                print("⚠️ Camera detected but no frame captured")
                return False
        else:
            print("⚠️ Camera not accessible (this is normal if no camera is connected)")
            return True
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Pi Parking Enforcer - Installation Test (uv)")
    print("=" * 60)
    
    tests = [
        ("System Tools", [
            ("uv", test_uv_installation),
            ("Virtual Environment", test_virtual_environment),
        ]),
        ("Python Dependencies", [
            ("opencv-python", "OpenCV"),
            ("numpy", "NumPy"),
            ("flask", "Flask"),
            ("flask-socketio", "Flask-SocketIO"),
            ("ultralytics", "Ultralytics (YOLO)"),
            ("slack-sdk", "Slack SDK"),
            ("python-dotenv", "Python-dotenv"),
            ("matplotlib", "Matplotlib"),
            ("pillow", "Pillow")
        ]),
        ("System Components", [
            ("Database", test_database),
            ("Configuration", test_config),
            ("Car Detector", test_car_detector),
            ("Slack Integration", test_slack_integration),
            ("Web Interface", test_web_interface),
            ("Parking Monitor", test_parking_monitor)
        ]),
        ("Files and Directories", [
            ("Required Files", test_files),
            ("Required Directories", test_directories)
        ]),
        ("Hardware", [
            ("Camera Access", test_camera)
        ])
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for category, test_list in tests:
        print(f"\n📋 {category}:")
        print("-" * 40)
        
        for test in test_list:
            total_tests += 1
            if isinstance(test, tuple):
                # Import test
                module_name, description = test
                if test_import(module_name, description):
                    passed_tests += 1
            else:
                # Function test
                if test():
                    passed_tests += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your installation is ready.")
        print("\n📋 To start the system:")
        print("1. Activate virtual environment: source .venv/bin/activate")
        print("2. Run: python main.py")
        print("3. Or use uv: uv run python main.py")
        print("4. Open web interface: http://your-pi-ip:5000")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        print("\n💡 Common solutions:")
        print("- Run: python setup.py")
        print("- Check your .env configuration")
        print("- Ensure uv is installed: curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("- Sync dependencies: uv sync")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 