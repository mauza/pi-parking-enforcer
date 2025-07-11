from flask import Flask, render_template, jsonify, Response, request
from flask_socketio import SocketIO, emit
from picamera2 import Picamera2
import cv2
import numpy as np
import json
import threading
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from .config import Config
from .parking_monitor import ParkingMonitor
from .database import ParkingDatabase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'parking-enforcer-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global parking monitor instance - will be set by main.py
parking_monitor = None
camera_frame = None
frame_lock = threading.Lock()

def set_parking_monitor(monitor_instance):
    """Set the parking monitor instance from main.py"""
    global parking_monitor
    parking_monitor = monitor_instance

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get current system status"""
    if parking_monitor:
        return jsonify(parking_monitor.get_current_status())
    return jsonify({'error': 'Parking monitor not initialized'})

@app.route('/api/active-sessions')
def get_active_sessions():
    """Get all active parking sessions"""
    if parking_monitor:
        return jsonify(parking_monitor.get_active_sessions_data())
    return jsonify([])

@app.route('/api/start-monitoring', methods=['POST'])
def start_monitoring():
    """Start the parking monitoring system"""
    global parking_monitor
    
    if not parking_monitor:
        return jsonify({'success': False, 'message': 'Parking monitor not initialized'})
    
    if parking_monitor.start_monitoring():
        return jsonify({'success': True, 'message': 'Monitoring started'})
    else:
        return jsonify({'success': False, 'message': 'Failed to start monitoring'})

@app.route('/api/stop-monitoring', methods=['POST'])
def stop_monitoring():
    """Stop the parking monitoring system"""
    global parking_monitor
    
    if parking_monitor:
        parking_monitor.stop_monitoring()
        return jsonify({'success': True, 'message': 'Monitoring stopped'})
    
    return jsonify({'success': False, 'message': 'No monitoring to stop'})

@app.route('/api/parking-stats')
def get_parking_stats():
    """Get parking statistics"""
    db = ParkingDatabase()
    days = request.args.get('days', 7, type=int)
    stats = db.get_parking_stats(days)
    return jsonify(stats)

@app.route('/api/occupancy-chart')
def get_occupancy_chart():
    """Generate and return occupancy chart as base64 image"""
    db = ParkingDatabase()
    
    # Get data for the last 24 hours (hourly data)
    hours = 24
    data = []
    
    for i in range(hours):
        time_point = datetime.now() - timedelta(hours=i)
        # This is a simplified version - in a real implementation, you'd query hourly data
        # For now, we'll use current stats
        stats = db.get_parking_stats(1)
        data.append({
            'time': time_point,
            'occupancy': stats['occupancy_rate']
        })
    
    # Create chart
    plt.figure(figsize=(10, 6))
    times = [d['time'] for d in reversed(data)]
    occupancy = [d['occupancy'] for d in reversed(data)]
    
    plt.plot(times, occupancy, marker='o', linewidth=2, markersize=6)
    plt.title('Parking Occupancy - Last 24 Hours', fontsize=14, fontweight='bold')
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('Occupancy Rate (%)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 100)
    
    # Format x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=4))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # Convert to base64
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()
    
    return jsonify({'chart_data': img_base64})

@app.route('/api/parking-spots')
def get_parking_spots():
    """Get parking spot configuration"""
    return jsonify(Config.PARKING_SPOTS)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    def generate_frames():
        global camera_frame
        
        while True:
            with frame_lock:
                if camera_frame is not None:
                    # Convert numpy array to PIL Image and encode
                    # Handle RGBA frames by converting to RGB
                    if camera_frame.shape[2] == 4:  # RGBA
                        # Convert RGBA to RGB by dropping alpha channel
                        rgb_frame = camera_frame[:, :, :3]
                        pil_image = Image.fromarray(rgb_frame)
                    else:
                        pil_image = Image.fromarray(camera_frame)
                    
                    img_buffer = io.BytesIO()
                    pil_image.save(img_buffer, format='JPEG', quality=85)
                    frame_data = img_buffer.getvalue()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
                else:
                    # Create a fallback image when no camera frame is available
                    fallback_image = create_fallback_image()
                    img_buffer = io.BytesIO()
                    fallback_image.save(img_buffer, format='JPEG', quality=85)
                    frame_data = img_buffer.getvalue()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            
            time.sleep(0.1)  # 10 FPS
    
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

def create_fallback_image():
    """Create a fallback image when camera is not available"""
    # Create a 640x480 image with a message
    width, height = 640, 480
    image = Image.new('RGB', (width, height), color='#2c3e50')
    
    # Add text to the image
    draw = ImageDraw.Draw(image)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Center the text
    text = "Camera Not Available"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2 - 20
    
    # Draw the main text
    draw.text((x, y), text, fill='white', font=font)
    
    # Add subtitle
    subtitle = "Check camera connection"
    bbox = draw.textbbox((0, 0), subtitle, font=font)
    sub_width = bbox[2] - bbox[0]
    sub_x = (width - sub_width) // 2
    draw.text((sub_x, y + 40), subtitle, fill='#bdc3c7', font=font)
    
    # Add camera icon or symbol
    camera_symbol = "📷"
    # For now, just add text representation
    draw.text((width // 2 - 20, y + 80), camera_symbol, fill='#3498db', font=font)
    
    return image

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    emit('status', {'message': 'Connected to parking monitor'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

@socketio.on('request_status')
def handle_status_request():
    """Handle status request from client"""
    if parking_monitor:
        status = parking_monitor.get_current_status()
        emit('status_update', status)

def update_camera_frame(frame):
    """Update the global camera frame for web streaming"""
    global camera_frame
    with frame_lock:
        camera_frame = frame.copy()

def start_web_server():
    """Start the Flask web server"""
    socketio.run(app, 
                host=Config.WEB_HOST, 
                port=Config.WEB_PORT, 
                debug=Config.DEBUG,
                allow_unsafe_werkzeug=True,
                use_reloader=False)  # Disable reloader to avoid signal issues

if __name__ == '__main__':
    start_web_server() 