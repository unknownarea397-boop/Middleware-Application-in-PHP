from zk import ZK
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import Config

class ZKTecoConnector:
    def __init__(self):
        self.config = Config.get_zkteco_config()
        self.zk = ZK(
            ip=self.config['ip'], 
            port=self.config['port'], 
            timeout=self.config['timeout']
        )
        self.conn = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """Connect to ZKTeco device"""
        try:
            self.conn = self.zk.connect()
            if self.conn:
                self.logger.info(f"Successfully connected to ZKTeco device at {self.config['ip']}:{self.config['port']}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to connect to ZKTeco device: {e}")
            return False
        return False
    
    def disconnect(self):
        """Disconnect from ZKTeco device"""
        if self.conn:
            self.conn.disconnect()
            self.logger.info("Disconnected from ZKTeco device")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def get_device_info(self) -> Dict:
        """Get device information"""
        if not self.conn:
            return {}
        
        try:
            firmware_version = self.conn.get_firmware_version()
            serialnumber = self.conn.get_serialnumber()
            platform = self.conn.get_platform()
            device_name = self.conn.get_device_name()
            
            return {
                'firmware_version': firmware_version,
                'serial_number': serialnumber,
                'platform': platform,
                'device_name': device_name,
                'ip': self.config['ip'],
                'port': self.config['port']
            }
        except Exception as e:
            self.logger.error(f"Error getting device info: {e}")
            return {}
    
    def get_users(self) -> List[Dict]:
        """Get all users from the device"""
        if not self.conn:
            return []
        
        try:
            users = self.conn.get_users()
            user_list = []
            
            for user in users:
                user_data = {
                    'employee_id': str(user.uid) if user.uid else str(user.user_id),
                    'employee_name': user.name if user.name else f"User {user.user_id}",
                    'privilege': user.privilege,
                    'password': user.password,
                    'group_id': user.group_id,
                    'user_id': user.user_id
                }
                user_list.append(user_data)
            
            self.logger.info(f"Retrieved {len(user_list)} users from device")
            return user_list
            
        except Exception as e:
            self.logger.error(f"Error retrieving users: {e}")
            return []
    
    def get_attendance_records(self, start_datetime: Optional[datetime] = None) -> List[Dict]:
        """Get attendance records from the device"""
        if not self.conn:
            return []
        
        try:
            attendances = self.conn.get_attendance()
            attendance_list = []
            
            for attendance in attendances:
                # Convert timestamp to datetime
                attendance_datetime = attendance.timestamp
                
                # Filter by start datetime if provided
                if start_datetime and attendance_datetime <= start_datetime:
                    continue
                
                # Get user info for this attendance record
                user_info = self._get_user_info(attendance.user_id)
                
                attendance_data = {
                    'employee_id': str(attendance.user_id),
                    'employee_name': user_info.get('name', f"User {attendance.user_id}"),
                    'attendance_datetime': attendance_datetime,
                    'punch_type': self._determine_punch_type(attendance.punch),
                    'verify_code': attendance.verify_code if hasattr(attendance, 'verify_code') else 0,
                    'work_code': attendance.work_code if hasattr(attendance, 'work_code') else 0,
                    'device_id': f"{self.config['ip']}:{self.config['port']}"
                }
                attendance_list.append(attendance_data)
            
            # Sort by datetime
            attendance_list.sort(key=lambda x: x['attendance_datetime'])
            
            self.logger.info(f"Retrieved {len(attendance_list)} attendance records from device")
            return attendance_list
            
        except Exception as e:
            self.logger.error(f"Error retrieving attendance records: {e}")
            return []
    
    def _get_user_info(self, user_id: int) -> Dict:
        """Get user information by user ID"""
        try:
            users = self.conn.get_users()
            for user in users:
                if user.user_id == user_id:
                    return {
                        'name': user.name if user.name else f"User {user_id}",
                        'privilege': user.privilege,
                        'group_id': user.group_id
                    }
        except Exception as e:
            self.logger.error(f"Error getting user info for ID {user_id}: {e}")
        
        return {'name': f"User {user_id}"}
    
    def _determine_punch_type(self, punch_code: int) -> str:
        """Determine punch type based on punch code"""
        punch_types = {
            0: 'IN',
            1: 'OUT',
            2: 'BREAK_OUT',
            3: 'BREAK_IN',
            4: 'OVERTIME_IN',
            5: 'OVERTIME_OUT'
        }
        return punch_types.get(punch_code, 'IN')
    
    def get_new_attendance_records(self, last_sync_datetime: Optional[datetime] = None) -> List[Dict]:
        """Get attendance records newer than the last sync datetime"""
        if not last_sync_datetime:
            # If no last sync datetime, get records from last 24 hours
            last_sync_datetime = datetime.now() - timedelta(days=1)
        
        return self.get_attendance_records(start_datetime=last_sync_datetime)
    
    def clear_attendance_records(self) -> bool:
        """Clear all attendance records from device (use with caution)"""
        if not self.conn:
            return False
        
        try:
            self.conn.clear_attendance()
            self.logger.info("Cleared all attendance records from device")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing attendance records: {e}")
            return False
    
    def test_connection(self) -> Dict:
        """Test connection and return device status"""
        result = {
            'connected': False,
            'device_info': {},
            'user_count': 0,
            'attendance_count': 0,
            'error': None
        }
        
        try:
            if self.connect():
                result['connected'] = True
                result['device_info'] = self.get_device_info()
                
                # Get counts
                users = self.get_users()
                attendances = self.get_attendance_records()
                
                result['user_count'] = len(users)
                result['attendance_count'] = len(attendances)
                
                self.disconnect()
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Connection test failed: {e}")
        
        return result
