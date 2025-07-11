import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import os
from datetime import datetime
from .config import Config
import uuid

class CarDetector:
    def __init__(self):
        self.model = YOLO(Config.CAR_DETECTION_MODEL)
        self.confidence_threshold = Config.CONFIDENCE_THRESHOLD
        
        # Create image storage directory
        os.makedirs(Config.IMAGE_STORAGE_PATH, exist_ok=True)
        
        # Car class IDs in COCO dataset (car=2, truck=7, bus=5)
        self.car_classes = [2, 7, 5]
    
    def _is_quadrilateral_region(self, patrol_region) -> bool:
        """Check if patrol region is a quadrilateral (list of 4 points)"""
        return isinstance(patrol_region, list) and len(patrol_region) == 4 and all(len(point) == 2 for point in patrol_region)
    
    def _is_rectangle_region(self, patrol_region) -> bool:
        """Check if patrol region is a rectangle (x, y, w, h)"""
        return isinstance(patrol_region, tuple) and len(patrol_region) == 4
    
    def _crop_to_quadrilateral(self, frame: np.ndarray, points: List[Tuple[int, int]]) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Crop frame to quadrilateral region and return cropped frame with offset"""
        # Convert points to numpy array
        pts = np.array(points, np.int32)
        
        # Get bounding rectangle of the quadrilateral
        x, y, w, h = cv2.boundingRect(pts)
        
        # Ensure coordinates are within frame bounds
        x = max(0, x)
        y = max(0, y)
        w = min(w, frame.shape[1] - x)
        h = min(h, frame.shape[0] - y)
        
        # Check if the region is valid
        if w <= 0 or h <= 0:
            # Return empty frame if region is invalid
            return np.zeros((1, 1, frame.shape[2] if len(frame.shape) == 3 else 1), dtype=frame.dtype), (0, 0)
        
        # Crop to bounding rectangle
        cropped = frame[y:y+h, x:x+w]
        
        # Check if cropped frame is valid
        if cropped.size == 0:
            return np.zeros((1, 1, frame.shape[2] if len(frame.shape) == 3 else 1), dtype=frame.dtype), (0, 0)
        
        # Create mask for the quadrilateral
        mask = np.zeros((h, w), dtype=np.uint8)
        # Adjust points relative to bounding rectangle
        adjusted_pts = pts - np.array([x, y])
        cv2.fillPoly(mask, [adjusted_pts], 255)
        
        # Apply mask to cropped frame
        if len(cropped.shape) == 3:
            # Ensure mask has the same number of channels as the frame
            if cropped.shape[2] == 4:  # RGBA
                mask_4d = np.stack([mask] * 4, axis=2)
                masked_frame = cv2.bitwise_and(cropped, mask_4d)
            else:  # RGB
                mask_3d = np.stack([mask] * 3, axis=2)
                masked_frame = cv2.bitwise_and(cropped, mask_3d)
        else:
            masked_frame = cv2.bitwise_and(cropped, mask)
        
        return masked_frame, (x, y)
    
    def _draw_quadrilateral(self, frame: np.ndarray, points: List[Tuple[int, int]], color: Tuple[int, int, int] = (255, 0, 0), thickness: int = 2):
        """Draw quadrilateral outline on frame"""
        pts = np.array(points, np.int32)
        cv2.polylines(frame, [pts], True, color, thickness)
    
    def detect_cars_in_frame(self, frame: np.ndarray) -> List[Dict]:
        """Detect cars in the entire frame or patrol region if specified"""
        # Use patrol region if specified
        patrol_region = getattr(Config, 'PATROL_REGION', None)
        if patrol_region:
            if self._is_quadrilateral_region(patrol_region):
                # Handle quadrilateral region
                frame, region_offset = self._crop_to_quadrilateral(frame, patrol_region)
            elif self._is_rectangle_region(patrol_region):
                # Handle rectangle region (backward compatibility)
                x, y, w, h = patrol_region
                frame = frame[y:y+h, x:x+w]
                region_offset = (x, y)
            else:
                # Invalid patrol region format
                region_offset = (0, 0)
        else:
            region_offset = (0, 0)
        # Convert RGBA to RGB if needed for YOLO model
        if frame.shape[2] == 4:  # RGBA
            frame_rgb = frame[:, :, :3]  # Drop alpha channel
        else:
            frame_rgb = frame
        results = self.model(frame_rgb, verbose=False)
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
                            # Adjust for patrol region offset
                            x1, y1, x2, y2 = int(x1 + region_offset[0]), int(y1 + region_offset[1]), int(x2 + region_offset[0]), int(y2 + region_offset[1])
                            detections.append({
                                'bbox': (x1, y1, x2, y2),
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
        
        # Convert RGBA to RGB if needed for saving
        if spot_roi.shape[2] == 4:  # RGBA
            spot_roi = spot_roi[:, :, :3]  # Drop alpha channel
        
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
        
        # Convert RGBA to RGB if needed
        if car_roi.shape[2] == 4:  # RGBA
            car_roi = car_roi[:, :, :3]  # Drop alpha channel
        
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
        """Draw square boxes and labels on the frame, and draw patrol region if set"""
        # Convert RGBA to RGB if needed for drawing
        if frame.shape[2] == 4:  # RGBA
            frame_copy = frame[:, :, :3].copy()  # Drop alpha channel
        else:
            frame_copy = frame.copy()
        # Draw patrol region if set
        patrol_region = getattr(Config, 'PATROL_REGION', None)
        if patrol_region:
            if self._is_quadrilateral_region(patrol_region):
                # Draw quadrilateral region
                self._draw_quadrilateral(frame_copy, patrol_region, (255, 0, 0), 2)
            elif self._is_rectangle_region(patrol_region):
                # Draw rectangle region (backward compatibility)
                x, y, w, h = patrol_region
                cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (255, 0, 0), 2)
        # Draw spot boundary if provided
        if spot_coords:
            x, y, w, h = spot_coords
            cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (255, 0, 0), 2)
        # Draw detections as squares
        for detection in detections:
            bbox = detection['bbox']
            confidence = detection['confidence']
            # Calculate square
            x1, y1, x2, y2 = bbox
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            side = max(x2 - x1, y2 - y1)
            half_side = side // 2
            sq_x1 = cx - half_side
            sq_y1 = cy - half_side
            sq_x2 = cx + half_side
            sq_y2 = cy + half_side
            # Draw square
            cv2.rectangle(frame_copy, (sq_x1, sq_y1), (sq_x2, sq_y2), (0, 255, 0), 2)
            # Draw confidence label
            label = f"Car: {confidence:.2f}"
            cv2.putText(frame_copy, label, (sq_x1, sq_y1 - 10), 
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