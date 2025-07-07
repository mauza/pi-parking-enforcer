import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import List, Dict, Optional
from datetime import datetime
from config import Config
import logging

class SlackIntegration:
    def __init__(self):
        self.client = None
        self.channel = Config.SLACK_CHANNEL
        self.alert_threshold = Config.SLACK_ALERT_THRESHOLD
        
        if Config.SLACK_BOT_TOKEN:
            try:
                self.client = WebClient(token=Config.SLACK_BOT_TOKEN)
                # Test the connection
                self.client.auth_test()
                logging.info("Slack integration initialized successfully")
            except SlackApiError as e:
                logging.error(f"Failed to initialize Slack client: {e.response['error']}")
                self.client = None
        else:
            logging.warning("No Slack bot token provided. Slack integration disabled.")
    
    def send_parking_alert(self, session_data: Dict, image_path: Optional[str] = None) -> bool:
        """Send an alert for a car that has been parked too long"""
        if not self.client:
            logging.warning("Slack client not available")
            return False
        
        try:
            # Calculate hours parked
            start_time = datetime.fromisoformat(session_data['start_time'])
            hours_parked = (datetime.now() - start_time).total_seconds() / 3600
            
            # Create message
            message = self._create_alert_message(session_data, hours_parked)
            
            # Send message with or without image
            if image_path and os.path.exists(image_path):
                return self._send_message_with_image(message, image_path)
            else:
                return self._send_text_message(message)
                
        except Exception as e:
            logging.error(f"Failed to send Slack alert: {e}")
            return False
    
    def _create_alert_message(self, session_data: Dict, hours_parked: float) -> str:
        """Create the alert message text"""
        spot_name = session_data.get('spot_name', f"Spot {session_data['spot_id']}")
        car_id = session_data.get('car_identifier', 'Unknown')
        
        message = f"""
🚨 *Parking Alert - Vehicle Exceeding Time Limit*

*Location:* {spot_name}
*Vehicle ID:* {car_id}
*Time Parked:* {hours_parked:.1f} hours
*Start Time:* {session_data['start_time']}
*Confidence:* {session_data.get('confidence_score', 0):.2f}

This vehicle has been parked for over {self.alert_threshold} hours and may require attention.
        """.strip()
        
        return message
    
    def _send_text_message(self, message: str) -> bool:
        """Send a text-only message to Slack"""
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message,
                parse='mrkdwn'
            )
            logging.info(f"Slack message sent successfully: {response['ts']}")
            return True
        except SlackApiError as e:
            logging.error(f"Failed to send Slack message: {e.response['error']}")
            return False
    
    def _send_message_with_image(self, message: str, image_path: str) -> bool:
        """Send a message with an image attachment to Slack"""
        try:
            # Upload the image first
            with open(image_path, 'rb') as file:
                upload_response = self.client.files_upload_v2(
                    channel=self.channel,
                    file=file,
                    title="Parking Violation Image",
                    initial_comment=message
                )
            
            logging.info(f"Slack message with image sent successfully: {upload_response['file']['id']}")
            return True
            
        except SlackApiError as e:
            logging.error(f"Failed to send Slack message with image: {e.response['error']}")
            # Fallback to text-only message
            return self._send_text_message(message)
        except Exception as e:
            logging.error(f"Error uploading image to Slack: {e}")
            # Fallback to text-only message
            return self._send_text_message(message)
    
    def send_daily_report(self, stats: Dict) -> bool:
        """Send a daily parking statistics report"""
        if not self.client:
            return False
        
        try:
            message = f"""
📊 *Daily Parking Report*

*Total Sessions Today:* {stats['total_sessions']}
*Average Duration:* {stats['avg_duration_minutes']:.1f} minutes
*Currently Occupied:* {stats['occupied_spots']}/{stats['total_spots']} spots
*Occupancy Rate:* {stats['occupancy_rate']:.1f}%

*Report generated at:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            return self._send_text_message(message)
            
        except Exception as e:
            logging.error(f"Failed to send daily report: {e}")
            return False
    
    def send_system_status(self, status: str, details: str = "") -> bool:
        """Send system status updates"""
        if not self.client:
            return False
        
        try:
            emoji = "✅" if "online" in status.lower() else "⚠️" if "warning" in status.lower() else "❌"
            
            message = f"""
{emoji} *System Status Update*

*Status:* {status}
*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            if details:
                message += f"\n\n*Details:* {details}"
            
            return self._send_text_message(message)
            
        except Exception as e:
            logging.error(f"Failed to send system status: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if Slack integration is properly connected"""
        return self.client is not None
    
    def test_connection(self) -> bool:
        """Test the Slack connection"""
        if not self.client:
            return False
        
        try:
            response = self.client.auth_test()
            logging.info(f"Slack connection test successful. Connected as: {response['user']}")
            return True
        except SlackApiError as e:
            logging.error(f"Slack connection test failed: {e.response['error']}")
            return False 