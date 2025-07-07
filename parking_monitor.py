import cv2
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from config import Config
from database import ParkingDatabase
from car_detector import CarDetector
from slack_integration import SlackIntegration

class ParkingMonitor:
    def __init__(self):
        self.database = ParkingDatabase()
        self.car_detector = CarDetector()
        self.slack = SlackIntegration()
        
        # Camera setup
        self.camera = None
        self.is_running = False
        self.monitor_thread = None
        
        # Track active sessions
        self.active_sessions = {}  # spot_id -> session_data
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Load existing active sessions
        self._load_active_sessions()
    
    def _load_active_sessions(self):
        """Load existing active sessions from database"""
        active_sessions = self.database.get_active_sessions()
        for session in active_sessions:
            self.active_sessions[session['spot_id']] = session
        self.logger.info(f"Loaded {len(active_sessions)} active sessions")
    
    def start_camera(self):
        """Initialize and start the camera"""
        try:
            self.camera = cv2.VideoCapture(Config.CAMERA_INDEX)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, Config.FRAME_RATE)
            
            if not self.camera.isOpened():
                raise Exception("Failed to open camera")
            
            self.logger.info("Camera initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def stop_camera(self):
        """Stop and release the camera"""
        if self.camera:
            self.camera.release()
            self.camera = None
        self.logger.info("Camera stopped")
    
    def start_monitoring(self):
        """Start the parking monitoring process"""
        if self.is_running:
            self.logger.warning("Monitoring is already running")
            return False
        
        if not self.start_camera():
            return False
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("Parking monitoring started")
        
        # Send startup notification
        if self.slack.is_connected():
            self.slack.send_system_status("System Online", "Parking monitor started successfully")
        
        return True
    
    def stop_monitoring(self):
        """Stop the parking monitoring process"""
        self.is_running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.stop_camera()
        
        # End all active sessions
        for spot_id in list(self.active_sessions.keys()):
            self._end_session(spot_id)
        
        self.logger.info("Parking monitoring stopped")
        
        # Send shutdown notification
        if self.slack.is_connected():
            self.slack.send_system_status("System Offline", "Parking monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        last_detection_time = 0
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Check if it's time for detection
                if current_time - last_detection_time >= Config.DETECTION_INTERVAL:
                    self._check_all_spots()
                    last_detection_time = current_time
                
                # Check for long-parking alerts
                self._check_long_parking_alerts()
                
                # Cleanup old images periodically
                if int(current_time) % 3600 == 0:  # Every hour
                    self.car_detector.cleanup_old_images()
                
                time.sleep(1)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _check_all_spots(self):
        """Check all parking spots for cars"""
        if not self.camera or not self.camera.isOpened():
            self.logger.error("Camera not available")
            return
        
        ret, frame = self.camera.read()
        if not ret:
            self.logger.error("Failed to read frame from camera")
            return
        
        for spot in Config.PARKING_SPOTS:
            spot_id = spot['id']
            spot_coords = spot['coords']
            
            # Check if spot is occupied
            is_occupied, confidence, image_path = self.car_detector.is_spot_occupied(frame, spot_coords)
            
            if is_occupied:
                self._handle_car_detected(spot_id, spot_coords, confidence, image_path, frame)
            else:
                self._handle_car_left(spot_id)
    
    def _handle_car_detected(self, spot_id: int, spot_coords: tuple, confidence: float, 
                           image_path: str, frame):
        """Handle when a car is detected in a parking spot"""
        # Check if there's already an active session for this spot
        if spot_id in self.active_sessions:
            # Update existing session
            session = self.active_sessions[spot_id]
            self.logger.debug(f"Car still in spot {spot_id} (session {session['id']})")
            return
        
        # Start new session
        car_identifier = None
        if Config.CAR_TRACKING_ENABLED:
            # Generate car identifier
            detections = self.car_detector.detect_cars_in_spot(frame, spot_coords)
            if detections:
                car_identifier = self.car_detector.generate_car_identifier(frame, detections[0])
        
        session_id = self.database.start_parking_session(
            spot_id=spot_id,
            car_identifier=car_identifier,
            confidence_score=confidence,
            image_path=image_path
        )
        
        # Store session data
        session_data = {
            'id': session_id,
            'spot_id': spot_id,
            'car_identifier': car_identifier,
            'start_time': datetime.now().isoformat(),
            'confidence_score': confidence,
            'image_path': image_path,
            'spot_name': next((s['name'] for s in Config.PARKING_SPOTS if s['id'] == spot_id), f"Spot {spot_id}")
        }
        
        self.active_sessions[spot_id] = session_data
        
        self.logger.info(f"New car detected in spot {spot_id} (session {session_id})")
    
    def _handle_car_left(self, spot_id: int):
        """Handle when a car leaves a parking spot"""
        if spot_id in self.active_sessions:
            self._end_session(spot_id)
    
    def _end_session(self, spot_id: int):
        """End a parking session"""
        session_data = self.active_sessions[spot_id]
        session_id = session_data['id']
        
        if self.database.end_parking_session(session_id):
            duration_minutes = session_data.get('duration_minutes', 0)
            self.logger.info(f"Car left spot {spot_id} (session {session_id}) - Duration: {duration_minutes:.1f} minutes")
        
        del self.active_sessions[spot_id]
    
    def _check_long_parking_alerts(self):
        """Check for cars that have been parked too long and send Slack alerts"""
        long_sessions = self.database.get_long_parking_sessions(Config.SLACK_ALERT_THRESHOLD)
        
        for session in long_sessions:
            # Check if we've already sent an alert for this session
            if not self._has_alert_been_sent(session['id']):
                self._send_long_parking_alert(session)
    
    def _has_alert_been_sent(self, session_id: int) -> bool:
        """Check if an alert has already been sent for this session"""
        # This is a simplified check - in a real implementation, you'd query the alerts table
        # For now, we'll assume no alerts have been sent
        return False
    
    def _send_long_parking_alert(self, session_data: Dict):
        """Send a Slack alert for a car parked too long"""
        if not self.slack.is_connected():
            return
        
        image_path = session_data.get('image_path')
        if self.slack.send_parking_alert(session_data, image_path):
            # Mark alert as sent in database
            alert_id = self.database.create_alert(
                session_id=session_data['id'],
                alert_type='long_parking',
                message=f"Car parked for over {Config.SLACK_ALERT_THRESHOLD} hours",
                image_path=image_path
            )
            self.database.mark_alert_sent(alert_id)
            self.logger.info(f"Sent long-parking alert for session {session_data['id']}")
    
    def get_current_status(self) -> Dict:
        """Get current system status"""
        stats = self.database.get_parking_stats()
        
        return {
            'is_running': self.is_running,
            'camera_connected': self.camera is not None and self.camera.isOpened(),
            'slack_connected': self.slack.is_connected(),
            'active_sessions': len(self.active_sessions),
            'total_spots': len(Config.PARKING_SPOTS),
            'stats': stats
        }
    
    def get_active_sessions_data(self) -> List[Dict]:
        """Get data for all active sessions"""
        sessions = []
        for spot_id, session_data in self.active_sessions.items():
            # Calculate current duration
            start_time = datetime.fromisoformat(session_data['start_time'])
            duration_hours = (datetime.now() - start_time).total_seconds() / 3600
            
            session_info = {
                'spot_id': spot_id,
                'spot_name': session_data['spot_name'],
                'car_identifier': session_data['car_identifier'],
                'start_time': session_data['start_time'],
                'duration_hours': round(duration_hours, 2),
                'confidence_score': session_data['confidence_score'],
                'image_path': session_data['image_path']
            }
            sessions.append(session_info)
        
        return sessions 