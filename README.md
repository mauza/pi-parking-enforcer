# Pi Parking Enforcer

A comprehensive parking monitoring system designed for Raspberry Pi with computer vision, real-time tracking, and Slack integration.

## Features

- **Computer Vision Detection**: Uses YOLOv8 to detect cars in configurable parking spots
- **Real-time Tracking**: Monitors how long each car stays in parking spots
- **Car Identification**: Generates unique identifiers for cars to track them over time
- **Web Dashboard**: Beautiful, responsive web interface with live video feed and statistics
- **Slack Integration**: Automatic alerts for cars parked over 5 hours with cropped images
- **SQLite Database**: Persistent storage of parking sessions and car history
- **Configurable Parking Spots**: Easy setup of parking spot boundaries
- **Real-time Charts**: Visual representation of occupancy rates and parking patterns

## System Requirements

- Raspberry Pi (3 or 4 recommended)
- USB camera or Raspberry Pi Camera Module
- Python 3.8+
- Internet connection (for Slack integration and YOLO model download)

## Installation

### Quick Start (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/pi-parking-enforcer.git
   cd pi-parking-enforcer
   ```

2. **Run the automated setup**:
   ```bash
   python setup.py
   ```

3. **Configure the system**:
   ```bash
   nano .env  # Edit with your settings
   ```

4. **Test the installation**:
   ```bash
   python test_installation.py
   ```

### Manual Installation

1. **Install uv** (modern Python package manager):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/pi-parking-enforcer.git
   cd pi-parking-enforcer
   ```

3. **Create virtual environment and install dependencies**:
   ```bash
   uv venv
   uv pip install -e .
   ```

4. **Configure the system**:
   ```bash
   cp env.example .env
   nano .env  # Edit with your settings
   ```

## Configuration

### Basic Settings

Edit the `.env` file to configure your system:

```bash
# Camera Settings
CAMERA_INDEX=0          # Camera device index (usually 0 for USB camera)
CAMERA_WIDTH=640        # Video width
CAMERA_HEIGHT=480       # Video height
FRAME_RATE=30          # Frames per second

# Detection Settings
DETECTION_INTERVAL=5.0  # How often to check for cars (seconds)
CONFIDENCE_THRESHOLD=0.5 # Minimum confidence for car detection

# Web Interface
WEB_HOST=0.0.0.0       # Listen on all interfaces
WEB_PORT=5000          # Web interface port
```

### Parking Spot Configuration

Edit `config.py` to define your parking spots:

```python
PARKING_SPOTS = [
    {"id": 1, "coords": (50, 100, 150, 200), "name": "Spot A1"},
    {"id": 2, "coords": (220, 100, 150, 200), "name": "Spot A2"},
    # Add more spots as needed
]
```

The `coords` are (x, y, width, height) in pixels.

### Slack Integration (Optional)

1. Create a Slack app at https://api.slack.com/apps
2. Add bot token scopes: `chat:write`, `files:write`
3. Install the app to your workspace
4. Add the bot token to your `.env` file:

```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_CHANNEL=#parking-alerts
SLACK_ALERT_THRESHOLD=5  # Hours before alert
```

## Usage

### Starting the System

**Option 1: Using uv (Recommended)**
```bash
uv run python main.py
```

**Option 2: Traditional virtual environment**
```bash
source .venv/bin/activate
python main.py
```

**Option 3: Direct execution**
```bash
python main.py
```

### Access the Web Interface

Open your browser and go to `http://your-pi-ip:5000`

### Web Dashboard

The web interface provides:

- **Live Video Feed**: Real-time camera view with parking spot overlays
- **System Controls**: Start/stop monitoring, refresh data
- **Statistics Cards**: Total spots, occupied spots, occupancy rate, average duration
- **Active Sessions**: List of currently parked cars with duration
- **Occupancy Chart**: Visual representation of parking patterns
- **Settings**: Configure system parameters

### API Endpoints

- `GET /api/status` - Get system status
- `GET /api/active-sessions` - Get current parking sessions
- `POST /api/start-monitoring` - Start monitoring
- `POST /api/stop-monitoring` - Stop monitoring
- `GET /api/parking-stats` - Get parking statistics
- `GET /api/occupancy-chart` - Get occupancy chart image

## Development

### Using uv for Development

```bash
# Install development dependencies
uv pip install -e '.[dev]'

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run flake8 .

# Type checking
uv run mypy .
```

### Adding Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Sync dependencies
uv sync
```

## File Structure

```
pi-parking-enforcer/
├── main.py                 # Main application entry point
├── config.py              # Configuration settings
├── database.py            # SQLite database operations
├── car_detector.py        # YOLO-based car detection
├── parking_monitor.py     # Main monitoring logic
├── slack_integration.py   # Slack alert system
├── web_interface.py       # Flask web server
├── pyproject.toml         # Project configuration and dependencies
├── setup.py              # Automated setup script
├── test_installation.py  # Installation verification
├── templates/             # HTML templates
│   └── dashboard.html     # Main dashboard page
├── static/                # Static web assets
│   ├── css/
│   │   └── dashboard.css  # Dashboard styles
│   └── js/
│       └── dashboard.js   # Dashboard JavaScript
├── env.example           # Environment variables template
└── README.md             # This file
```

## Troubleshooting

### Installation Issues

- **uv not found**: Install uv with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Dependencies not installing**: Run `uv sync` to sync dependencies
- **Virtual environment issues**: Delete `.venv` and run `uv venv` again

### Camera Issues

- **Camera not detected**: Check `CAMERA_INDEX` in `.env`
- **Poor detection**: Adjust `CONFIDENCE_THRESHOLD` or lighting
- **High CPU usage**: Increase `DETECTION_INTERVAL`

### Web Interface Issues

- **Can't access dashboard**: Check firewall settings and `WEB_HOST`/`WEB_PORT`
- **Video not loading**: Ensure camera is working and accessible

### Slack Integration Issues

- **Alerts not sending**: Verify bot token and channel permissions
- **Image upload fails**: Check bot has `files:write` scope

### Performance Optimization

- **Slow detection**: Use smaller YOLO model (e.g., `yolov8n.pt`)
- **High memory usage**: Reduce `MAX_STORED_IMAGES`
- **Database size**: Regular cleanup of old sessions

## Advanced Features

### Custom Car Detection

The system uses YOLOv8 for car detection. You can:

- Train custom models for specific car types
- Adjust detection parameters in `car_detector.py`
- Add license plate recognition (requires additional setup)

### Database Management

The SQLite database stores:

- Parking sessions with start/end times
- Car identifiers and history
- Alert records
- Parking spot configurations

### Extending the System

- Add face recognition for driver identification
- Implement license plate recognition
- Add payment integration
- Create mobile app for notifications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs in `logs/parking_enforcer.log`
3. Run `python test_installation.py` to verify your setup
4. Open an issue on GitHub

## Acknowledgments

- YOLOv8 by Ultralytics for object detection
- OpenCV for computer vision capabilities
- Flask for the web framework
- Bootstrap for the UI components
- uv by Astral for fast Python package management