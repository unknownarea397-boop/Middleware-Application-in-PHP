import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import Config

class DatabaseManager:
    def __init__(self):
        self.config = Config.get_db_config()
        self.connection = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                self.logger.info("Successfully connected to MySQL database")
                return True
        except Error as e:
            self.logger.error(f"Error connecting to MySQL: {e}")
            return False
        return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.logger.info("MySQL connection closed")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def execute_query(self, query: str, params: tuple = None) -> bool:
        """Execute a single query"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            self.logger.error(f"Error executing query: {e}")
            self.connection.rollback()
            return False
    
    def fetch_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query and return results"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            self.logger.error(f"Error fetching query results: {e}")
            return []
    
    def insert_employee(self, employee_id: str, employee_name: str) -> bool:
        """Insert or update employee information"""
        query = """
            INSERT INTO employees (employee_id, employee_name) 
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE 
            employee_name = VALUES(employee_name),
            updated_at = CURRENT_TIMESTAMP
        """
        return self.execute_query(query, (employee_id, employee_name))
    
    def insert_attendance_record(self, employee_id: str, employee_name: str, 
                               attendance_datetime: datetime, punch_type: str = 'IN',
                               device_id: str = None, verify_code: int = 0, 
                               work_code: int = 0) -> bool:
        """Insert attendance record"""
        query = """
            INSERT IGNORE INTO attendance 
            (employee_id, employee_name, attendance_datetime, punch_type, 
             device_id, verify_code, work_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (
            employee_id, employee_name, attendance_datetime, punch_type,
            device_id, verify_code, work_code
        ))
    
    def bulk_insert_attendance(self, records: List[Dict]) -> Tuple[int, int]:
        """Bulk insert attendance records"""
        inserted_count = 0
        updated_count = 0
        
        try:
            cursor = self.connection.cursor()
            
            for record in records:
                # First ensure employee exists
                employee_query = """
                    INSERT INTO employees (employee_id, employee_name) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE 
                    employee_name = VALUES(employee_name),
                    updated_at = CURRENT_TIMESTAMP
                """
                cursor.execute(employee_query, (record['employee_id'], record['employee_name']))
                
                # Insert attendance record
                attendance_query = """
                    INSERT INTO attendance 
                    (employee_id, employee_name, attendance_datetime, punch_type, 
                     device_id, verify_code, work_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    employee_name = VALUES(employee_name),
                    punch_type = VALUES(punch_type),
                    device_id = VALUES(device_id),
                    verify_code = VALUES(verify_code),
                    work_code = VALUES(work_code)
                """
                
                cursor.execute(attendance_query, (
                    record['employee_id'],
                    record['employee_name'],
                    record['attendance_datetime'],
                    record.get('punch_type', 'IN'),
                    record.get('device_id'),
                    record.get('verify_code', 0),
                    record.get('work_code', 0)
                ))
                
                if cursor.rowcount > 0:
                    if cursor.lastrowid > 0:
                        inserted_count += 1
                    else:
                        updated_count += 1
            
            self.connection.commit()
            cursor.close()
            
        except Error as e:
            self.logger.error(f"Error in bulk insert: {e}")
            self.connection.rollback()
        
        return inserted_count, updated_count
    
    def log_sync_operation(self, records_processed: int, records_inserted: int,
                          records_updated: int, status: str, error_message: str = None):
        """Log synchronization operation"""
        query = """
            INSERT INTO sync_log 
            (sync_datetime, records_processed, records_inserted, records_updated, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        self.execute_query(query, (
            datetime.now(), records_processed, records_inserted, 
            records_updated, status, error_message
        ))
    
    def get_last_attendance_datetime(self) -> Optional[datetime]:
        """Get the datetime of the most recent attendance record"""
        query = "SELECT MAX(attendance_datetime) as last_datetime FROM attendance"
        results = self.fetch_query(query)
        
        if results and results[0]['last_datetime']:
            return results[0]['last_datetime']
        return None
    
    def get_attendance_summary(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Get attendance summary for a date range"""
        query = """
            SELECT 
                employee_id,
                employee_name,
                DATE(attendance_datetime) as attendance_date,
                COUNT(*) as punch_count,
                MIN(attendance_datetime) as first_punch,
                MAX(attendance_datetime) as last_punch
            FROM attendance
        """
        
        params = []
        if start_date or end_date:
            query += " WHERE "
            conditions = []
            if start_date:
                conditions.append("attendance_datetime >= %s")
                params.append(start_date)
            if end_date:
                conditions.append("attendance_datetime <= %s")
                params.append(end_date)
            query += " AND ".join(conditions)
        
        query += " GROUP BY employee_id, DATE(attendance_datetime) ORDER BY attendance_date DESC"
        
        return self.fetch_query(query, tuple(params) if params else None)
