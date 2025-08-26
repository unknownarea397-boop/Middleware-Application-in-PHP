import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'attendance_system')
    
    # ZKTeco Device Configuration
    ZKTECO_IP = os.getenv('ZKTECO_IP', '192.168.1.100')
    ZKTECO_PORT = int(os.getenv('ZKTECO_PORT', 4370))
    ZKTECO_TIMEOUT = int(os.getenv('ZKTECO_TIMEOUT', 60))
    
    # Application Settings
    SYNC_INTERVAL_MINUTES = int(os.getenv('SYNC_INTERVAL_MINUTES', 5))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def get_db_config(cls):
        """Return database configuration as dictionary"""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME,
            'autocommit': True
        }
    
    @classmethod
    def get_zkteco_config(cls):
        """Return ZKTeco device configuration as dictionary"""
        return {
            'ip': cls.ZKTECO_IP,
            'port': cls.ZKTECO_PORT,
            'timeout': cls.ZKTECO_TIMEOUT
        }
