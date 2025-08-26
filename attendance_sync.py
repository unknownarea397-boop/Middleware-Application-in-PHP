import logging
import sys
from datetime import datetime
from typing import Tuple
from database import DatabaseManager
from zkteco_connector import ZKTecoConnector
from config import Config

class AttendanceSync:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('attendance_sync.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def sync_attendance_data(self) -> Tuple[bool, str]:
        """Synchronize attendance data from ZKTeco device to MySQL database"""
        sync_start_time = datetime.now()
        records_processed = 0
        records_inserted = 0
        records_updated = 0
        error_message = None
        
        try:
            # Get last sync datetime from database
            with DatabaseManager() as db:
                if not db.connection:
                    error_message = "Failed to connect to database"
                    self.logger.error(error_message)
                    return False, error_message
                
                last_sync_datetime = db.get_last_attendance_datetime()
                self.logger.info(f"Last sync datetime: {last_sync_datetime}")
            
            # Connect to ZKTeco device and get new records
            with ZKTecoConnector() as zk:
                if not zk.conn:
                    error_message = "Failed to connect to ZKTeco device"
                    self.logger.error(error_message)
                    return False, error_message
                
                # Get device info
                device_info = zk.get_device_info()
                self.logger.info(f"Connected to device: {device_info.get('device_name', 'Unknown')} "
                               f"(SN: {device_info.get('serial_number', 'Unknown')})")
                
                # Get new attendance records
                attendance_records = zk.get_new_attendance_records(last_sync_datetime)
                records_processed = len(attendance_records)
                
                self.logger.info(f"Found {records_processed} new attendance records")
                
                if records_processed == 0:
                    self.logger.info("No new records to sync")
                    return True, "No new records to sync"
            
            # Insert records into database
            with DatabaseManager() as db:
                if not db.connection:
                    error_message = "Failed to connect to database for insertion"
                    self.logger.error(error_message)
                    return False, error_message
                
                records_inserted, records_updated = db.bulk_insert_attendance(attendance_records)
                
                # Log sync operation
                status = 'SUCCESS' if records_processed == (records_inserted + records_updated) else 'PARTIAL'
                db.log_sync_operation(
                    records_processed=records_processed,
                    records_inserted=records_inserted,
                    records_updated=records_updated,
                    status=status,
                    error_message=error_message
                )
            
            sync_duration = (datetime.now() - sync_start_time).total_seconds()
            success_message = (f"Sync completed successfully in {sync_duration:.2f}s. "
                             f"Processed: {records_processed}, "
                             f"Inserted: {records_inserted}, "
                             f"Updated: {records_updated}")
            
            self.logger.info(success_message)
            return True, success_message
            
        except Exception as e:
            error_message = f"Sync failed: {str(e)}"
            self.logger.error(error_message, exc_info=True)
            
            # Try to log the failed operation
            try:
                with DatabaseManager() as db:
                    if db.connection:
                        db.log_sync_operation(
                            records_processed=records_processed,
                            records_inserted=records_inserted,
                            records_updated=records_updated,
                            status='FAILED',
                            error_message=error_message
                        )
            except:
                pass  # Don't fail if we can't log the error
            
            return False, error_message
    
    def sync_users(self) -> Tuple[bool, str]:
        """Synchronize user data from ZKTeco device to MySQL database"""
        try:
            self.logger.info("Starting user synchronization...")
            
            # Connect to ZKTeco device and get users
            with ZKTecoConnector() as zk:
                if not zk.conn:
                    error_message = "Failed to connect to ZKTeco device"
                    self.logger.error(error_message)
                    return False, error_message
                
                users = zk.get_users()
                self.logger.info(f"Found {len(users)} users on device")
            
            # Insert users into database
            with DatabaseManager() as db:
                if not db.connection:
                    error_message = "Failed to connect to database"
                    self.logger.error(error_message)
                    return False, error_message
                
                users_processed = 0
                for user in users:
                    if db.insert_employee(user['employee_id'], user['employee_name']):
                        users_processed += 1
                
                success_message = f"User sync completed. Processed {users_processed} out of {len(users)} users"
                self.logger.info(success_message)
                return True, success_message
                
        except Exception as e:
            error_message = f"User sync failed: {str(e)}"
            self.logger.error(error_message, exc_info=True)
            return False, error_message
    
    def test_connections(self) -> dict:
        """Test connections to both ZKTeco device and database"""
        result = {
            'database': {'connected': False, 'error': None},
            'zkteco': {'connected': False, 'error': None, 'device_info': {}}
        }
        
        # Test database connection
        try:
            with DatabaseManager() as db:
                if db.connection and db.connection.is_connected():
                    result['database']['connected'] = True
                    self.logger.info("Database connection test: SUCCESS")
                else:
                    result['database']['error'] = "Failed to connect to database"
        except Exception as e:
            result['database']['error'] = str(e)
            self.logger.error(f"Database connection test failed: {e}")
        
        # Test ZKTeco device connection
        try:
            zk = ZKTecoConnector()
            zk_test_result = zk.test_connection()
            result['zkteco'] = zk_test_result
            
            if zk_test_result['connected']:
                self.logger.info("ZKTeco device connection test: SUCCESS")
            else:
                self.logger.error(f"ZKTeco device connection test failed: {zk_test_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            result['zkteco']['error'] = str(e)
            self.logger.error(f"ZKTeco connection test failed: {e}")
        
        return result
    
    def get_attendance_summary(self, days: int = 7) -> list:
        """Get attendance summary for the last N days"""
        try:
            with DatabaseManager() as db:
                if not db.connection:
                    self.logger.error("Failed to connect to database")
                    return []
                
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                summary = db.get_attendance_summary(start_date, end_date)
                self.logger.info(f"Retrieved attendance summary for {len(summary)} records")
                return summary
                
        except Exception as e:
            self.logger.error(f"Error getting attendance summary: {e}")
            return []
