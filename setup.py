#!/usr/bin/env python3
"""
Setup script for Pi Parking Enforcer
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_uv():
    """Install uv if not already installed"""
    try:
        # Check if uv is already installed
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ uv is already installed")
            return True
    except FileNotFoundError:
        pass
    
    print("🔄 Installing uv...")
    try:
        # Install uv using the official installer
        install_script = subprocess.run([
            "curl", "-LsSf", "https://astral.sh/uv/install.sh"
        ], capture_output=True, text=True)
        
        if install_script.returncode == 0:
            # Run the install script
            install_result = subprocess.run([
                "sh", "-c", install_script.stdout
            ], check=True)
            print("✅ uv installed successfully")
            return True
        else:
            print("❌ Failed to download uv installer")
            return False
    except Exception as e:
        print(f"❌ Failed to install uv: {e}")
        return False

def install_system_dependencies():
    """Install system dependencies"""
    commands = [
        ("sudo apt update", "Updating package list"),
        ("sudo apt install -y python3-pip python3-venv libopencv-dev curl", "Installing system packages")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    return True

def create_virtual_environment():
    """Create Python virtual environment using uv"""
    if os.path.exists(".venv"):
        print("🔄 Virtual environment already exists, skipping creation")
        return True
    
    return run_command("uv venv", "Creating virtual environment with uv")

def install_python_dependencies():
    """Install Python dependencies using uv"""
    return run_command("uv pip install -e .", "Installing Python dependencies with uv")

def install_dev_dependencies():
    """Install development dependencies using uv"""
    return run_command("uv pip install -e '.[dev]'", "Installing development dependencies with uv")

def setup_environment_file():
    """Create .env file from template"""
    if os.path.exists(".env"):
        print("🔄 .env file already exists, skipping creation")
        return True
    
    if os.path.exists("env.example"):
        shutil.copy("env.example", ".env")
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your configuration")
        return True
    else:
        print("❌ env.example file not found")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "captured_images"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def download_yolo_model():
    """Download YOLO model if not present"""
    try:
        # Activate the virtual environment and import ultralytics
        if os.name == 'nt':  # Windows
            python_path = ".venv\\Scripts\\python"
        else:  # Unix/Linux
            python_path = ".venv/bin/python"
        
        # Run the download in a subprocess
        result = subprocess.run([
            python_path, "-c", 
            "from ultralytics import YOLO; YOLO('yolov8n.pt')"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ YOLO model downloaded successfully")
            return True
        else:
            print(f"⚠️ YOLO model download failed: {result.stderr}")
            print("⚠️ Model will be downloaded on first run")
            return True
    except Exception as e:
        print(f"⚠️ Failed to download YOLO model: {e}")
        print("⚠️ Model will be downloaded on first run")
        return True

def main():
    """Main setup function"""
    print("=" * 60)
    print("Pi Parking Enforcer - Setup Script (uv)")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install system dependencies
    print("\n📦 Installing system dependencies...")
    if not install_system_dependencies():
        print("❌ Failed to install system dependencies")
        sys.exit(1)
    
    # Install uv
    print("\n🚀 Installing uv...")
    if not install_uv():
        print("❌ Failed to install uv")
        sys.exit(1)
    
    # Create virtual environment
    print("\n🐍 Setting up Python environment...")
    if not create_virtual_environment():
        print("❌ Failed to create virtual environment")
        sys.exit(1)
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Install development dependencies (optional)
    print("\n🔧 Installing development dependencies...")
    install_dev_dependencies()
    
    # Setup environment file
    print("\n⚙️ Setting up configuration...")
    if not setup_environment_file():
        print("❌ Failed to setup environment file")
        sys.exit(1)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Download YOLO model
    print("\n🤖 Setting up AI model...")
    download_yolo_model()
    
    print("\n" + "=" * 60)
    print("✅ Setup completed successfully!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("1. Edit .env file with your configuration")
    print("2. Activate virtual environment: source .venv/bin/activate")
    print("3. Run the application: python main.py")
    print("4. Open web interface: http://your-pi-ip:5000")
    print("\n🚀 uv commands:")
    print("- uv run python main.py          # Run with uv")
    print("- uv add <package>               # Add new dependency")
    print("- uv remove <package>            # Remove dependency")
    print("- uv sync                        # Sync dependencies")
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main() 