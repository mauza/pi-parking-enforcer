#!/usr/bin/env python3
"""
Pi Parking Enforcer - Main Application
A comprehensive parking monitoring system for Raspberry Pi
"""

import sys
import os
import logging
import threading
import time
from datetime import datetime
from config import Config
from parking_monitor import ParkingMonitor
from web_interface import start_web_server, update_camera_frame, set_parking_monitor
from slack_integration import SlackIntegration

class ParkingEnforcerApp:
    def __init__(self):
        self.parking_monitor = None
        self.web_server_thread = None
        self.is_running = False
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('logs/parking_enforcer.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def start(self):
        """Start the parking enforcement application"""
        self.logger.info("Starting Pi Parking Enforcer...")
        
        try:
            # Initialize parking monitor
            self.parking_monitor = ParkingMonitor()
            
            # Pass parking monitor instance to web interface
            set_parking_monitor(self.parking_monitor)
            
            # Start web server in a separate thread
            self.web_server_thread = threading.Thread(
                target=self.start_web_server_wrapper,
                daemon=True
            )
            self.web_server_thread.start()
            
            # Start parking monitoring
            if self.parking_monitor.start_monitoring():
                self.is_running = True
                self.logger.info("Parking enforcement system started successfully")
                
                # Main application loop
                self.main_loop()
            else:
                self.logger.error("Failed to start parking monitoring")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting application: {e}")
            return False
        
        return True
    
    def start_web_server_wrapper(self):
        """Wrapper to start web server with proper error handling"""
        try:
            start_web_server()
        except Exception as e:
            self.logger.error(f"Web server error: {e}")
    
    def main_loop(self):
        """Main application loop"""
        self.logger.info("Entering main application loop")
        
        while self.is_running:
            try:
                # Update camera frame for web interface
                if self.parking_monitor:
                    ret, frame = self.parking_monitor.read_frame()
                    if ret:
                        update_camera_frame(frame)
                    else:
                        # Log camera read failures less frequently
                        if int(time.time()) % 30 == 0:  # Every 30 seconds
                            self.logger.warning("Camera frame read failed - this may be normal if no camera is connected")
                
                # Check system health
                self.check_system_health()
                
                # Sleep for a short interval
                time.sleep(1)
                
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def check_system_health(self):
        """Check system health and send alerts if needed"""
        # This could include:
        # - Disk space monitoring
        # - Memory usage monitoring
        # - Camera connection status
        # - Database health checks
        
        # For now, just log that we're running
        if int(time.time()) % 300 == 0:  # Every 5 minutes
            self.logger.info("System health check - All systems operational")
    
    def shutdown(self):
        """Gracefully shutdown the application"""
        self.logger.info("Shutting down Pi Parking Enforcer...")
        
        self.is_running = False
        
        # Stop parking monitoring
        if self.parking_monitor:
            self.parking_monitor.stop_monitoring()
        
        # Wait for web server to stop
        if self.web_server_thread and self.web_server_thread.is_alive():
            self.logger.info("Waiting for web server to stop...")
            self.web_server_thread.join(timeout=5)
        
        self.logger.info("Pi Parking Enforcer shutdown complete")
        sys.exit(0)

def main():
    """Main entry point"""
    print("=" * 60)
    print("Pi Parking Enforcer")
    print("A comprehensive parking monitoring system")
    print("=" * 60)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Web interface: http://{Config.WEB_HOST}:{Config.WEB_PORT}")
    print(f"Camera index: {Config.CAMERA_INDEX}")
    print(f"Detection interval: {Config.DETECTION_INTERVAL} seconds")
    print(f"Slack alerts: {'Enabled' if Config.SLACK_BOT_TOKEN else 'Disabled'}")
    print("=" * 60)
    
    # Create and start application
    app = ParkingEnforcerApp()
    
    try:
        if app.start():
            print("Application started successfully!")
            print("Press Ctrl+C to stop")
        else:
            print("Failed to start application")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        app.shutdown()

if __name__ == "__main__":
    main() 