import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import os
from datetime import datetime
from config import Config
import uuid

class CarDetector:
    def __init__(self):
        self.model = YOLO(Config.CAR_DETECTION_MODEL)
        self.confidence_threshold = Config.CONFIDENCE_THRESHOLD
        
        # Create image storage directory
        os.makedirs(Config.IMAGE_STORAGE_PATH, exist_ok=True)
        
        # Car class IDs in COCO dataset (car=2, truck=7, bus=5)
        self.car_classes = [2, 7, 5]
    
    def detect_cars_in_frame(self, frame: np.ndarray) -> List[Dict]:
        """Detect cars in the entire frame"""
        results = self.model(frame, verbose=False)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Check if detection is a car/truck/bus
                    if int(box.cls[0]) in self.car_classes:
                        confidence = float(box.conf[0])
                        if confidence >= self.confidence_threshold:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            detections.append({
                                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                'confidence': confidence,
                                'class_id': int(box.cls[0])
                            })
        
        return detections
    
    def detect_cars_in_spot(self, frame: np.ndarray, spot_coords: Tuple[int, int, int, int]) -> List[Dict]:
        """Detect cars in a specific parking spot"""
        x, y, w, h = spot_coords
        spot_roi = frame[y:y+h, x:x+w]
        
        if spot_roi.size == 0:
            return []
        
        # Detect cars in the spot ROI
        detections = self.detect_cars_in_frame(spot_roi)
        
        # Adjust bounding box coordinates to full frame
        for detection in detections:
            bbox = detection['bbox']
            detection['bbox'] = (bbox[0] + x, bbox[1] + y, bbox[2] + x, bbox[3] + y)
        
        return detections
    
    def is_spot_occupied(self, frame: np.ndarray, spot_coords: Tuple[int, int, int, int]) -> Tuple[bool, float, Optional[str]]:
        """Check if a parking spot is occupied by a car"""
        detections = self.detect_cars_in_spot(frame, spot_coords)
        
        if not detections:
            return False, 0.0, None
        
        # Get the detection with highest confidence
        best_detection = max(detections, key=lambda x: x['confidence'])
        
        # Save image if car detected
        image_path = None
        if best_detection['confidence'] > self.confidence_threshold:
            image_path = self.save_spot_image(frame, spot_coords, best_detection)
        
        return True, best_detection['confidence'], image_path
    
    def save_spot_image(self, frame: np.ndarray, spot_coords: Tuple[int, int, int, int], 
                       detection: Dict) -> str:
        """Save an image of the detected car in the parking spot"""
        x, y, w, h = spot_coords
        spot_roi = frame[y:y+h, x:x+w].copy()
        
        # Add detection box to the image
        bbox = detection['bbox']
        bbox_relative = (bbox[0] - x, bbox[1] - y, bbox[2] - x, bbox[3] - y)
        cv2.rectangle(spot_roi, (bbox_relative[0], bbox_relative[1]), 
                     (bbox_relative[2], bbox_relative[3]), (0, 255, 0), 2)
        
        # Add confidence text
        confidence_text = f"Car: {detection['confidence']:.2f}"
        cv2.putText(spot_roi, confidence_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"spot_{timestamp}_{unique_id}.jpg"
        filepath = os.path.join(Config.IMAGE_STORAGE_PATH, filename)
        
        # Save image
        cv2.imwrite(filepath, spot_roi)
        return filepath
    
    def generate_car_identifier(self, frame: np.ndarray, detection: Dict) -> str:
        """Generate a unique identifier for a car based on its appearance"""
        # For now, use a simple hash of the detection area
        # In a more advanced implementation, you could use:
        # - Face recognition for drivers
        # - License plate recognition
        # - Car color and model classification
        
        bbox = detection['bbox']
        car_roi = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        
        if car_roi.size == 0:
            return f"car_{uuid.uuid4().hex[:8]}"
        
        # Create a simple hash based on the car's appearance
        # Resize to consistent size for hashing
        car_roi_resized = cv2.resize(car_roi, (64, 64))
        car_roi_gray = cv2.cvtColor(car_roi_resized, cv2.COLOR_BGR2GRAY)
        
        # Simple hash based on average pixel values in different regions
        h, w = car_roi_gray.shape
        regions = [
            car_roi_gray[0:h//2, 0:w//2].mean(),  # Top-left
            car_roi_gray[0:h//2, w//2:w].mean(),  # Top-right
            car_roi_gray[h//2:h, 0:w//2].mean(),  # Bottom-left
            car_roi_gray[h//2:h, w//2:w].mean(),  # Bottom-right
        ]
        
        # Create hash from region averages
        hash_value = sum(int(region) * (i + 1) for i, region in enumerate(regions))
        return f"car_{hash_value % 1000000:06d}"
    
    def draw_detections_on_frame(self, frame: np.ndarray, detections: List[Dict], 
                               spot_coords: Tuple[int, int, int, int] = None) -> np.ndarray:
        """Draw detection boxes and labels on the frame"""
        frame_copy = frame.copy()
        
        # Draw spot boundary if provided
        if spot_coords:
            x, y, w, h = spot_coords
            cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        # Draw detections
        for detection in detections:
            bbox = detection['bbox']
            confidence = detection['confidence']
            
            # Draw bounding box
            cv2.rectangle(frame_copy, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            
            # Draw confidence label
            label = f"Car: {confidence:.2f}"
            cv2.putText(frame_copy, label, (bbox[0], bbox[1] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame_copy
    
    def cleanup_old_images(self):
        """Remove old images to prevent disk space issues"""
        if not os.path.exists(Config.IMAGE_STORAGE_PATH):
            return
        
        files = os.listdir(Config.IMAGE_STORAGE_PATH)
        if len(files) <= Config.MAX_STORED_IMAGES:
            return
        
        # Sort files by modification time (oldest first)
        files_with_time = []
        for file in files:
            filepath = os.path.join(Config.IMAGE_STORAGE_PATH, file)
            mtime = os.path.getmtime(filepath)
            files_with_time.append((filepath, mtime))
        
        files_with_time.sort(key=lambda x: x[1])
        
        # Remove oldest files
        files_to_remove = len(files) - Config.MAX_STORED_IMAGES
        for i in range(files_to_remove):
            try:
                os.remove(files_with_time[i][0])
            except OSError:
                pass 