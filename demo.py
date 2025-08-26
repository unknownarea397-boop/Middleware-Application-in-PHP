#!/usr/bin/env python3
"""
Demo script for ZKTeco MySQL Attendance System
This script demonstrates the functionality with sample data if no device is available
"""

import sys
import random
from datetime import datetime, timedelta
from database import DatabaseManager
from config import Config

def create_sample_data():
    """Create sample attendance data for testing"""
    sample_employees = [
        ('EMP001', 'John Doe'),
        ('EMP002', 'Jane Smith'),
        ('EMP003', 'Bob Johnson'),
        ('EMP004', 'Alice Brown'),
        ('EMP005', 'Charlie Wilson')
    ]
    
    print("Creating sample attendance data...")
    
    with DatabaseManager() as db:
        if not db.connection:
            print("❌ Failed to connect to database")
            return False
        
        # Insert sample employees
        for emp_id, emp_name in sample_employees:
            db.insert_employee(emp_id, emp_name)
        
        # Create sample attendance records for the last 7 days
        base_date = datetime.now() - timedelta(days=7)
        attendance_records = []
        
        for day in range(7):
            current_date = base_date + timedelta(days=day)
            
            for emp_id, emp_name in sample_employees:
                # Skip some days randomly to simulate real attendance
                if random.random() < 0.1:  # 10% chance of absence
                    continue
                
                # Morning punch in (8:00 - 9:30)
                punch_in_time = current_date.replace(
                    hour=8, minute=0, second=0, microsecond=0
                ) + timedelta(minutes=random.randint(0, 90))
                
                attendance_records.append({
                    'employee_id': emp_id,
                    'employee_name': emp_name,
                    'attendance_datetime': punch_in_time,
                    'punch_type': 'IN',
                    'device_id': 'DEMO_DEVICE'
                })
                
                # Lunch break out (12:00 - 13:00)
                if random.random() < 0.8:  # 80% take lunch break
                    lunch_out = punch_in_time.replace(hour=12, minute=0) + timedelta(
                        minutes=random.randint(0, 60)
                    )
                    attendance_records.append({
                        'employee_id': emp_id,
                        'employee_name': emp_name,
                        'attendance_datetime': lunch_out,
                        'punch_type': 'BREAK_OUT',
                        'device_id': 'DEMO_DEVICE'
                    })
                    
                    # Lunch break in (13:00 - 14:00)
                    lunch_in = lunch_out + timedelta(minutes=random.randint(30, 60))
                    attendance_records.append({
                        'employee_id': emp_id,
                        'employee_name': emp_name,
                        'attendance_datetime': lunch_in,
                        'punch_type': 'BREAK_IN',
                        'device_id': 'DEMO_DEVICE'
                    })
                
                # Evening punch out (17:00 - 19:00)
                punch_out_time = punch_in_time.replace(hour=17, minute=0) + timedelta(
                    minutes=random.randint(0, 120)
                )
                attendance_records.append({
                    'employee_id': emp_id,
                    'employee_name': emp_name,
                    'attendance_datetime': punch_out_time,
                    'punch_type': 'OUT',
                    'device_id': 'DEMO_DEVICE'
                })
        
        # Insert all attendance records
        inserted, updated = db.bulk_insert_attendance(attendance_records)
        
        # Log the demo sync
        db.log_sync_operation(
            records_processed=len(attendance_records),
            records_inserted=inserted,
            records_updated=updated,
            status='SUCCESS',
            error_message=None
        )
        
        print(f"✅ Sample data created successfully!")
        print(f"   - {len(sample_employees)} employees")
        print(f"   - {len(attendance_records)} attendance records")
        print(f"   - {inserted} new records inserted")
        print(f"   - {updated} records updated")
        
        return True

def show_sample_report():
    """Show a sample attendance report"""
    print("\n" + "="*80)
    print("SAMPLE ATTENDANCE REPORT - Last 7 Days")
    print("="*80)
    
    with DatabaseManager() as db:
        if not db.connection:
            print("❌ Failed to connect to database")
            return
        
        # Get attendance summary
        query = """
            SELECT 
                employee_id,
                employee_name,
                DATE(attendance_datetime) as attendance_date,
                COUNT(*) as punch_count,
                MIN(CASE WHEN punch_type = 'IN' THEN attendance_datetime END) as first_in,
                MAX(CASE WHEN punch_type = 'OUT' THEN attendance_datetime END) as last_out,
                TIMESTAMPDIFF(MINUTE, 
                    MIN(CASE WHEN punch_type = 'IN' THEN attendance_datetime END),
                    MAX(CASE WHEN punch_type = 'OUT' THEN attendance_datetime END)
                ) as work_minutes
            FROM attendance
            WHERE attendance_datetime >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY employee_id, employee_name, DATE(attendance_datetime)
            ORDER BY attendance_date DESC, employee_name
        """
        
        records = db.fetch_query(query)
        
        if not records:
            print("No attendance data found. Run 'python demo.py create-sample' first.")
            return
        
        print(f"{'Employee':<20} {'Date':<12} {'First In':<10} {'Last Out':<10} {'Hours':<8} {'Punches'}")
        print("-" * 80)
        
        total_hours = 0
        for record in records:
            first_in = record['first_in'].strftime('%H:%M') if record['first_in'] else '--:--'
            last_out = record['last_out'].strftime('%H:%M') if record['last_out'] else '--:--'
            hours = f"{record['work_minutes'] / 60:.1f}h" if record['work_minutes'] else '0.0h'
            
            if record['work_minutes']:
                total_hours += record['work_minutes'] / 60
            
            print(f"{record['employee_name'][:20]:<20} "
                  f"{record['attendance_date']:<12} "
                  f"{first_in:<10} "
                  f"{last_out:<10} "
                  f"{hours:<8} "
                  f"{record['punch_count']}")
        
        print("-" * 80)
        print(f"Total work hours: {total_hours:.1f}h")
        print("="*80)

def test_device_simulation():
    """Simulate device connection for testing"""
    print("🔌 Testing device connection simulation...")
    
    # Simulate device info
    device_info = {
        'ip': Config.ZKTECO_IP,
        'port': Config.ZKTECO_PORT,
        'device_name': 'DEMO Device',
        'serial_number': 'DEMO12345',
        'firmware_version': '6.60.00',
        'platform': 'ZEM600_TFT'
    }
    
    print("✅ Simulated device info:")
    for key, value in device_info.items():
        print(f"   {key}: {value}")
    
    return True

def cleanup_sample_data():
    """Clean up sample data"""
    print("🧹 Cleaning up sample data...")
    
    with DatabaseManager() as db:
        if not db.connection:
            print("❌ Failed to connect to database")
            return False
        
        # Delete sample attendance records
        db.execute_query("DELETE FROM attendance WHERE device_id = 'DEMO_DEVICE'")
        
        # Delete sample employees (this will cascade to attendance due to foreign key)
        sample_emp_ids = ['EMP001', 'EMP002', 'EMP003', 'EMP004', 'EMP005']
        for emp_id in sample_emp_ids:
            db.execute_query("DELETE FROM employees WHERE employee_id = %s", (emp_id,))
        
        print("✅ Sample data cleaned up successfully")
        return True

def main():
    """Main demo function"""
    if len(sys.argv) < 2:
        print("Demo script for ZKTeco MySQL Attendance System")
        print("\nUsage:")
        print("  python demo.py create-sample    - Create sample attendance data")
        print("  python demo.py show-report      - Show attendance report")
        print("  python demo.py test-device      - Test device simulation")
        print("  python demo.py cleanup          - Clean up sample data")
        print("  python demo.py full-demo        - Run complete demonstration")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'create-sample':
        create_sample_data()
    elif command == 'show-report':
        show_sample_report()
    elif command == 'test-device':
        test_device_simulation()
    elif command == 'cleanup':
        cleanup_sample_data()
    elif command == 'full-demo':
        print("🚀 Running full demonstration...")
        test_device_simulation()
        create_sample_data()
        show_sample_report()
        print("\n✅ Demo completed! You can now:")
        print("   - Run 'python main.py test' to test real connections")
        print("   - Run 'python web_interface.py' to see the web dashboard")
        print("   - Run 'python demo.py cleanup' to remove sample data")
    else:
        print(f"Unknown command: {command}")
        main()

if __name__ == "__main__":
    main()
