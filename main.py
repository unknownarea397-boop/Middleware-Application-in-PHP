#!/usr/bin/env python3
"""
ZKTeco MySQL Attendance Import System

This application connects to ZKTeco biometric devices and imports attendance data
into a MySQL database. It supports both manual sync and scheduled automatic sync.

Usage:
    python main.py [command]

Commands:
    sync        - Perform one-time attendance sync
    sync-users  - Sync user data from device
    test        - Test connections to device and database
    schedule    - Run scheduled sync (default every 5 minutes)
    summary     - Show attendance summary for last 7 days
    help        - Show this help message
"""

import sys
import time
import schedule
from datetime import datetime
from attendance_sync import AttendanceSync

def print_help():
    """Print help message"""
    print(__doc__)

def run_sync():
    """Run attendance synchronization"""
    print(f"\n{'='*60}")
    print(f"Starting attendance sync at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    sync = AttendanceSync()
    success, message = sync.sync_attendance_data()
    
    if success:
        print(f"✅ SYNC SUCCESS: {message}")
    else:
        print(f"❌ SYNC FAILED: {message}")
    
    print(f"{'='*60}\n")
    return success

def run_user_sync():
    """Run user synchronization"""
    print(f"\n{'='*60}")
    print(f"Starting user sync at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    sync = AttendanceSync()
    success, message = sync.sync_users()
    
    if success:
        print(f"✅ USER SYNC SUCCESS: {message}")
    else:
        print(f"❌ USER SYNC FAILED: {message}")
    
    print(f"{'='*60}\n")
    return success

def test_connections():
    """Test all connections"""
    print(f"\n{'='*60}")
    print(f"Testing connections at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    sync = AttendanceSync()
    results = sync.test_connections()
    
    # Database test results
    db_result = results['database']
    if db_result['connected']:
        print("✅ Database Connection: SUCCESS")
    else:
        print(f"❌ Database Connection: FAILED - {db_result.get('error', 'Unknown error')}")
    
    # ZKTeco device test results
    zk_result = results['zkteco']
    if zk_result['connected']:
        print("✅ ZKTeco Device Connection: SUCCESS")
        device_info = zk_result.get('device_info', {})
        if device_info:
            print(f"   Device: {device_info.get('device_name', 'Unknown')}")
            print(f"   Serial: {device_info.get('serial_number', 'Unknown')}")
            print(f"   Firmware: {device_info.get('firmware_version', 'Unknown')}")
            print(f"   Users: {zk_result.get('user_count', 0)}")
            print(f"   Attendance Records: {zk_result.get('attendance_count', 0)}")
    else:
        print(f"❌ ZKTeco Device Connection: FAILED - {zk_result.get('error', 'Unknown error')}")
    
    print(f"{'='*60}\n")
    
    return db_result['connected'] and zk_result['connected']

def show_summary():
    """Show attendance summary"""
    print(f"\n{'='*60}")
    print(f"Attendance Summary (Last 7 Days)")
    print(f"{'='*60}")
    
    sync = AttendanceSync()
    summary = sync.get_attendance_summary(7)
    
    if not summary:
        print("No attendance data found for the last 7 days.")
        return
    
    print(f"{'Employee ID':<12} {'Name':<20} {'Date':<12} {'Punches':<8} {'First':<8} {'Last':<8}")
    print("-" * 80)
    
    for record in summary:
        first_time = record['first_punch'].strftime('%H:%M') if record['first_punch'] else '--:--'
        last_time = record['last_punch'].strftime('%H:%M') if record['last_punch'] else '--:--'
        
        print(f"{record['employee_id']:<12} "
              f"{record['employee_name'][:20]:<20} "
              f"{record['attendance_date']:<12} "
              f"{record['punch_count']:<8} "
              f"{first_time:<8} "
              f"{last_time:<8}")
    
    print(f"\nTotal records: {len(summary)}")
    print(f"{'='*60}\n")

def run_scheduled_sync():
    """Run scheduled synchronization"""
    from config import Config
    
    print(f"\n{'='*60}")
    print(f"Starting scheduled sync service")
    print(f"Sync interval: {Config.SYNC_INTERVAL_MINUTES} minutes")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Schedule the sync job
    schedule.every(Config.SYNC_INTERVAL_MINUTES).minutes.do(run_sync)
    
    # Run initial sync
    run_sync()
    
    print(f"Scheduled sync is running. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        print(f"\n\nStopping scheduled sync at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Goodbye!")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        command = "help"
    else:
        command = sys.argv[1].lower()
    
    commands = {
        'sync': run_sync,
        'sync-users': run_user_sync,
        'test': test_connections,
        'schedule': run_scheduled_sync,
        'summary': show_summary,
        'help': print_help
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print_help()

if __name__ == "__main__":
    main()
