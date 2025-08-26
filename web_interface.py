#!/usr/bin/env python3
"""
Simple web interface for ZKTeco Attendance System
Provides a basic web dashboard to view attendance data and sync status
"""

from flask import Flask, render_template, jsonify, request
import json
from datetime import datetime, timedelta
from database import DatabaseManager
from attendance_sync import AttendanceSync
import logging

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/sync/status')
def sync_status():
    """Get sync status and device info"""
    try:
        sync = AttendanceSync()
        connections = sync.test_connections()
        
        # Get last sync info
        with DatabaseManager() as db:
            last_sync_query = """
                SELECT * FROM sync_log 
                ORDER BY sync_datetime DESC 
                LIMIT 1
            """
            last_sync = db.fetch_query(last_sync_query)
            last_sync_info = last_sync[0] if last_sync else None
        
        return jsonify({
            'success': True,
            'connections': connections,
            'last_sync': {
                'datetime': last_sync_info['sync_datetime'].isoformat() if last_sync_info else None,
                'status': last_sync_info['status'] if last_sync_info else None,
                'records_processed': last_sync_info['records_processed'] if last_sync_info else 0,
                'records_inserted': last_sync_info['records_inserted'] if last_sync_info else 0,
                'records_updated': last_sync_info['records_updated'] if last_sync_info else 0,
                'error_message': last_sync_info['error_message'] if last_sync_info else None
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sync/run', methods=['POST'])
def run_sync():
    """Manually trigger sync"""
    try:
        sync = AttendanceSync()
        success, message = sync.sync_attendance_data()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/attendance/summary')
def attendance_summary():
    """Get attendance summary"""
    try:
        days = int(request.args.get('days', 7))
        sync = AttendanceSync()
        summary = sync.get_attendance_summary(days)
        
        # Convert datetime objects to ISO format
        for record in summary:
            if record.get('attendance_date'):
                record['attendance_date'] = record['attendance_date'].isoformat()
            if record.get('first_punch'):
                record['first_punch'] = record['first_punch'].isoformat()
            if record.get('last_punch'):
                record['last_punch'] = record['last_punch'].isoformat()
        
        return jsonify({'success': True, 'data': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/attendance/recent')
def recent_attendance():
    """Get recent attendance records"""
    try:
        limit = int(request.args.get('limit', 50))
        
        with DatabaseManager() as db:
            query = """
                SELECT employee_id, employee_name, attendance_datetime, 
                       punch_type, device_id
                FROM attendance 
                ORDER BY attendance_datetime DESC 
                LIMIT %s
            """
            records = db.fetch_query(query, (limit,))
            
            # Convert datetime objects
            for record in records:
                if record.get('attendance_datetime'):
                    record['attendance_datetime'] = record['attendance_datetime'].isoformat()
        
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/employees')
def get_employees():
    """Get all employees"""
    try:
        with DatabaseManager() as db:
            query = """
                SELECT e.employee_id, e.employee_name, e.created_at,
                       COUNT(a.id) as total_punches,
                       MAX(a.attendance_datetime) as last_attendance
                FROM employees e
                LEFT JOIN attendance a ON e.employee_id = a.employee_id
                GROUP BY e.employee_id, e.employee_name, e.created_at
                ORDER BY e.employee_name
            """
            employees = db.fetch_query(query)
            
            # Convert datetime objects
            for employee in employees:
                if employee.get('created_at'):
                    employee['created_at'] = employee['created_at'].isoformat()
                if employee.get('last_attendance'):
                    employee['last_attendance'] = employee['last_attendance'].isoformat()
        
        return jsonify({'success': True, 'data': employees})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    try:
        with DatabaseManager() as db:
            stats = {}
            
            # Total employees
            result = db.fetch_query("SELECT COUNT(*) as count FROM employees")
            stats['total_employees'] = result[0]['count'] if result else 0
            
            # Total attendance records
            result = db.fetch_query("SELECT COUNT(*) as count FROM attendance")
            stats['total_attendance'] = result[0]['count'] if result else 0
            
            # Today's attendance
            today = datetime.now().date()
            result = db.fetch_query(
                "SELECT COUNT(*) as count FROM attendance WHERE DATE(attendance_datetime) = %s",
                (today,)
            )
            stats['today_attendance'] = result[0]['count'] if result else 0
            
            # This week's attendance
            week_ago = datetime.now() - timedelta(days=7)
            result = db.fetch_query(
                "SELECT COUNT(*) as count FROM attendance WHERE attendance_datetime >= %s",
                (week_ago,)
            )
            stats['week_attendance'] = result[0]['count'] if result else 0
            
            # Sync statistics
            result = db.fetch_query("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
                       MAX(sync_datetime) as last_sync
                FROM sync_log
            """)
            
            if result and result[0]['total']:
                stats['total_syncs'] = result[0]['total']
                stats['successful_syncs'] = result[0]['successful']
                stats['last_sync'] = result[0]['last_sync'].isoformat() if result[0]['last_sync'] else None
            else:
                stats['total_syncs'] = 0
                stats['successful_syncs'] = 0
                stats['last_sync'] = None
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Create templates directory and basic template
import os

def create_template():
    """Create basic HTML template"""
    template_dir = 'templates'
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZKTeco Attendance System</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #3498db; }
        .status { padding: 20px; background: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #2980b9; }
        .success { color: #27ae60; }
        .error { color: #e74c3c; }
        .warning { color: #f39c12; }
        .table { width: 100%; border-collapse: collapse; background: white; border-radius: 5px; overflow: hidden; }
        .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .table th { background: #34495e; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ZKTeco Attendance System Dashboard</h1>
        </div>
        
        <div class="stats" id="stats">
            <!-- Stats will be loaded here -->
        </div>
        
        <div class="status" id="status">
            <h3>System Status</h3>
            <div id="connection-status"></div>
            <div id="sync-status"></div>
            <button class="btn" onclick="runSync()">Manual Sync</button>
        </div>
        
        <div style="background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h3>Recent Attendance Records</h3>
            <table class="table" id="attendance-table">
                <thead>
                    <tr>
                        <th>Employee ID</th>
                        <th>Name</th>
                        <th>Date/Time</th>
                        <th>Type</th>
                        <th>Device</th>
                    </tr>
                </thead>
                <tbody id="attendance-body">
                    <!-- Data will be loaded here -->
                </tbody>
            </table>
        </div>
    </div>

    <script>
        function loadStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const stats = data.data;
                        document.getElementById('stats').innerHTML = `
                            <div class="stat-card">
                                <div class="stat-number">${stats.total_employees}</div>
                                <div>Total Employees</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.total_attendance}</div>
                                <div>Total Records</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.today_attendance}</div>
                                <div>Today's Records</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.week_attendance}</div>
                                <div>This Week</div>
                            </div>
                        `;
                    }
                });
        }

        function loadStatus() {
            fetch('/api/sync/status')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const db = data.connections.database;
                        const zk = data.connections.zkteco;
                        const lastSync = data.last_sync;
                        
                        const dbStatus = db.connected ? '<span class="success">✓ Connected</span>' : '<span class="error">✗ Disconnected</span>';
                        const zkStatus = zk.connected ? '<span class="success">✓ Connected</span>' : '<span class="error">✗ Disconnected</span>';
                        
                        document.getElementById('connection-status').innerHTML = `
                            <p><strong>Database:</strong> ${dbStatus}</p>
                            <p><strong>ZKTeco Device:</strong> ${zkStatus}</p>
                        `;
                        
                        if (lastSync.datetime) {
                            const syncTime = new Date(lastSync.datetime).toLocaleString();
                            const syncStatus = lastSync.status === 'SUCCESS' ? 'success' : 'error';
                            document.getElementById('sync-status').innerHTML = `
                                <p><strong>Last Sync:</strong> ${syncTime}</p>
                                <p><strong>Status:</strong> <span class="${syncStatus}">${lastSync.status}</span></p>
                                <p><strong>Records:</strong> ${lastSync.records_inserted} inserted, ${lastSync.records_updated} updated</p>
                            `;
                        }
                    }
                });
        }

        function loadAttendance() {
            fetch('/api/attendance/recent?limit=20')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const tbody = document.getElementById('attendance-body');
                        tbody.innerHTML = data.data.map(record => `
                            <tr>
                                <td>${record.employee_id}</td>
                                <td>${record.employee_name}</td>
                                <td>${new Date(record.attendance_datetime).toLocaleString()}</td>
                                <td>${record.punch_type}</td>
                                <td>${record.device_id || '-'}</td>
                            </tr>
                        `).join('');
                    }
                });
        }

        function runSync() {
            const btn = document.querySelector('button');
            btn.disabled = true;
            btn.textContent = 'Syncing...';
            
            fetch('/api/sync/run', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    btn.disabled = false;
                    btn.textContent = 'Manual Sync';
                    
                    if (data.success) {
                        alert('Sync completed successfully: ' + data.message);
                        loadStats();
                        loadStatus();
                        loadAttendance();
                    } else {
                        alert('Sync failed: ' + data.error);
                    }
                });
        }

        // Load data on page load
        loadStats();
        loadStatus();
        loadAttendance();

        // Refresh data every 30 seconds
        setInterval(() => {
            loadStats();
            loadStatus();
            loadAttendance();
        }, 30000);
    </script>
</body>
</html>'''

    with open(os.path.join(template_dir, 'dashboard.html'), 'w') as f:
        f.write(template_content)

def main():
    """Run the web interface"""
    create_template()
    print("Starting web interface on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    # Add Flask to requirements if not present
    requirements_path = 'requirements.txt'
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    if 'flask' not in content.lower():
        with open(requirements_path, 'a') as f:
            f.write('\nflask==2.3.3\n')
    
    main()
