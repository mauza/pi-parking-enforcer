import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Camera settings
    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))
    CAMERA_WIDTH = int(os.getenv('CAMERA_WIDTH', 640))
    CAMERA_HEIGHT = int(os.getenv('CAMERA_HEIGHT', 480))
    FRAME_RATE = int(os.getenv('FRAME_RATE', 30))
    
    # Parking spot configuration
    # Define parking spots as (x, y, width, height) rectangles
    PARKING_SPOTS = [
        # Example spots - adjust these based on your camera view
        {"id": 1, "coords": (50, 100, 150, 200), "name": "Spot A1"},
        {"id": 2, "coords": (220, 100, 150, 200), "name": "Spot A2"},
        {"id": 3, "coords": (390, 100, 150, 200), "name": "Spot A3"},
        {"id": 4, "coords": (50, 320, 150, 200), "name": "Spot B1"},
        {"id": 5, "coords": (220, 320, 150, 200), "name": "Spot B2"},
        {"id": 6, "coords": (390, 320, 150, 200), "name": "Spot B3"},
    ]
    
    # Detection settings
    DETECTION_INTERVAL = float(os.getenv('DETECTION_INTERVAL', 5.0))  # seconds
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.5))
    CAR_DETECTION_MODEL = os.getenv('CAR_DETECTION_MODEL', 'yolov8n.pt')
    
    # Database settings
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'parking_data.db')
    
    # Web interface settings
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('WEB_PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Slack settings
    SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
    SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', '#parking-alerts')
    SLACK_ALERT_THRESHOLD = int(os.getenv('SLACK_ALERT_THRESHOLD', 5))  # hours
    
    # Car tracking settings
    CAR_TRACKING_ENABLED = os.getenv('CAR_TRACKING_ENABLED', 'True').lower() == 'true'
    FACE_RECOGNITION_ENABLED = os.getenv('FACE_RECOGNITION_ENABLED', 'False').lower() == 'true'
    LICENSE_PLATE_RECOGNITION_ENABLED = os.getenv('LICENSE_PLATE_RECOGNITION_ENABLED', 'False').lower() == 'true'
    
    # Image storage
    IMAGE_STORAGE_PATH = os.getenv('IMAGE_STORAGE_PATH', 'captured_images')
    MAX_STORED_IMAGES = int(os.getenv('MAX_STORED_IMAGES', 1000)) 
    
    # Patrol region as quadrilateral points (x, y) - set to None to use full frame
    # Points in order: top-left, top-right, bottom-right, bottom-left
    PATROL_REGION = [(600, 400), (1300, 350), (1350, 425), (650, 450)]  # Askew quadrilateral 