import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
from config import Config

class ParkingDatabase:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create parking sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS parking_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spot_id INTEGER NOT NULL,
                    car_identifier TEXT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_minutes REAL,
                    image_path TEXT,
                    confidence_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create car identifiers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS car_identifiers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifier TEXT UNIQUE NOT NULL,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_sessions INTEGER DEFAULT 0,
                    total_duration_hours REAL DEFAULT 0.0,
                    face_encoding TEXT,
                    license_plate TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create parking spots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS parking_spots (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    coords_x INTEGER NOT NULL,
                    coords_y INTEGER NOT NULL,
                    coords_width INTEGER NOT NULL,
                    coords_height INTEGER NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    image_path TEXT,
                    sent_to_slack BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES parking_sessions (id)
                )
            ''')
            
            # Insert default parking spots
            for spot in Config.PARKING_SPOTS:
                cursor.execute('''
                    INSERT OR IGNORE INTO parking_spots 
                    (id, name, coords_x, coords_y, coords_width, coords_height)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    spot['id'], 
                    spot['name'], 
                    spot['coords'][0], 
                    spot['coords'][1], 
                    spot['coords'][2], 
                    spot['coords'][3]
                ))
            
            conn.commit()
    
    def start_parking_session(self, spot_id: int, car_identifier: str = None, 
                            confidence_score: float = 0.0, image_path: str = None) -> int:
        """Start a new parking session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO parking_sessions 
                (spot_id, car_identifier, start_time, confidence_score, image_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (spot_id, car_identifier, datetime.now(), confidence_score, image_path))
            
            session_id = cursor.lastrowid
            
            # Update car identifier stats
            if car_identifier:
                cursor.execute('''
                    INSERT OR REPLACE INTO car_identifiers 
                    (identifier, last_seen, total_sessions)
                    VALUES (
                        ?, 
                        CURRENT_TIMESTAMP,
                        COALESCE((SELECT total_sessions FROM car_identifiers WHERE identifier = ?), 0) + 1
                    )
                ''', (car_identifier, car_identifier))
            
            conn.commit()
            return session_id
    
    def end_parking_session(self, session_id: int) -> bool:
        """End a parking session and calculate duration"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get session start time
            cursor.execute('SELECT start_time FROM parking_sessions WHERE id = ?', (session_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            start_time = datetime.fromisoformat(result[0])
            end_time = datetime.now()
            duration_minutes = (end_time - start_time).total_seconds() / 60
            
            cursor.execute('''
                UPDATE parking_sessions 
                SET end_time = ?, duration_minutes = ?
                WHERE id = ?
            ''', (end_time, duration_minutes, session_id))
            
            conn.commit()
            return True
    
    def get_active_sessions(self) -> List[Dict]:
        """Get all currently active parking sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ps.id, ps.spot_id, ps.car_identifier, ps.start_time, 
                       ps.confidence_score, ps.image_path, p.name as spot_name
                FROM parking_sessions ps
                JOIN parking_spots p ON ps.spot_id = p.id
                WHERE ps.end_time IS NULL
                ORDER BY ps.start_time
            ''')
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_session_by_spot(self, spot_id: int) -> Optional[Dict]:
        """Get the active session for a specific spot"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ps.id, ps.spot_id, ps.car_identifier, ps.start_time, 
                       ps.confidence_score, ps.image_path, p.name as spot_name
                FROM parking_sessions ps
                JOIN parking_spots p ON ps.spot_id = p.id
                WHERE ps.spot_id = ? AND ps.end_time IS NULL
            ''', (spot_id,))
            
            result = cursor.fetchone()
            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
            return None
    
    def get_car_history(self, car_identifier: str) -> List[Dict]:
        """Get parking history for a specific car"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ps.id, ps.spot_id, ps.start_time, ps.end_time, 
                       ps.duration_minutes, p.name as spot_name
                FROM parking_sessions ps
                JOIN parking_spots p ON ps.spot_id = p.id
                WHERE ps.car_identifier = ?
                ORDER BY ps.start_time DESC
            ''', (car_identifier,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_long_parking_sessions(self, hours_threshold: int = 5) -> List[Dict]:
        """Get sessions that have been active for more than the threshold"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ps.id, ps.spot_id, ps.car_identifier, ps.start_time, 
                       ps.confidence_score, ps.image_path, p.name as spot_name,
                       (julianday('now') - julianday(ps.start_time)) * 24 as hours_parked
                FROM parking_sessions ps
                JOIN parking_spots p ON ps.spot_id = p.id
                WHERE ps.end_time IS NULL 
                AND (julianday('now') - julianday(ps.start_time)) * 24 > ?
                ORDER BY ps.start_time
            ''', (hours_threshold,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def create_alert(self, session_id: int, alert_type: str, message: str, 
                    image_path: str = None) -> int:
        """Create a new alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (session_id, alert_type, message, image_path)
                VALUES (?, ?, ?, ?)
            ''', (session_id, alert_type, message, image_path))
            
            alert_id = cursor.lastrowid
            conn.commit()
            return alert_id
    
    def mark_alert_sent(self, alert_id: int):
        """Mark an alert as sent to Slack"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alerts SET sent_to_slack = 1 WHERE id = ?
            ''', (alert_id,))
            conn.commit()
    
    def get_parking_stats(self, days: int = 7) -> Dict:
        """Get parking statistics for the last N days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total sessions
            cursor.execute('''
                SELECT COUNT(*) FROM parking_sessions 
                WHERE start_time >= datetime('now', '-{} days')
            '''.format(days))
            total_sessions = cursor.fetchone()[0]
            
            # Average duration
            cursor.execute('''
                SELECT AVG(duration_minutes) FROM parking_sessions 
                WHERE end_time IS NOT NULL 
                AND start_time >= datetime('now', '-{} days')
            '''.format(days))
            avg_duration = cursor.fetchone()[0] or 0
            
            # Currently occupied spots
            cursor.execute('''
                SELECT COUNT(*) FROM parking_sessions WHERE end_time IS NULL
            ''')
            occupied_spots = cursor.fetchone()[0]
            
            # Total spots
            cursor.execute('SELECT COUNT(*) FROM parking_spots WHERE is_active = 1')
            total_spots = cursor.fetchone()[0]
            
            return {
                'total_sessions': total_sessions,
                'avg_duration_minutes': round(avg_duration, 2),
                'occupied_spots': occupied_spots,
                'total_spots': total_spots,
                'occupancy_rate': round((occupied_spots / total_spots) * 100, 2) if total_spots > 0 else 0
            } 