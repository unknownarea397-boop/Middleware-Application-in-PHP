# ZKTeco MySQL Attendance Import System

A Python application that connects to ZKTeco biometric devices to retrieve employee attendance data and store it in a MySQL database.

## Features

- **Real-time Sync**: Connect to ZKTeco biometric devices and sync attendance data
- **Employee Management**: Automatically sync employee information from device
- **Database Storage**: Store attendance records in MySQL with proper indexing
- **Scheduled Sync**: Run automatic synchronization at configurable intervals
- **Logging**: Comprehensive logging with sync history tracking
- **Error Handling**: Robust error handling and recovery mechanisms
- **Connection Testing**: Test connectivity to both device and database
- **Attendance Reports**: Generate attendance summaries and reports

## Prerequisites

- Python 3.7+
- MySQL 5.7+ or MariaDB 10.3+
- ZKTeco biometric device with network connectivity
- Required Python packages (see requirements.txt)

## Installation

1. **Clone or download this repository**

2. **Install required Python packages:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup MySQL Database:**
   ```bash
   mysql -u root -p < database_schema.sql
   ```

4. **Configure the application:**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

## Configuration

Edit the `.env` file with your specific settings:

### Database Configuration
```bash
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=attendance_system
```

### ZKTeco Device Configuration
```bash
ZKTECO_IP=192.168.1.100    # IP address of your ZKTeco device
ZKTECO_PORT=4370           # Default ZKTeco port
ZKTECO_TIMEOUT=60          # Connection timeout in seconds
```

### Application Settings
```bash
SYNC_INTERVAL_MINUTES=5    # How often to sync (for scheduled mode)
LOG_LEVEL=INFO            # Logging level (DEBUG, INFO, WARNING, ERROR)
```

## Usage

The application provides several commands for different operations:

### One-time Attendance Sync
```bash
python main.py sync
```

### Sync Users from Device
```bash
python main.py sync-users
```

### Test Connections
```bash
python main.py test
```

### Run Scheduled Sync
```bash
python main.py schedule
```

### Show Attendance Summary
```bash
python main.py summary
```

### Help
```bash
python main.py help
```

## Database Schema

The application creates the following tables:

### `employees`
- `id`: Primary key
- `employee_id`: Unique employee identifier from device
- `employee_name`: Employee name
- `created_at`, `updated_at`: Timestamps

### `attendance`
- `id`: Primary key
- `employee_id`: Foreign key to employees
- `employee_name`: Employee name (denormalized for reporting)
- `attendance_datetime`: Date and time of attendance
- `punch_type`: Type of punch (IN, OUT, BREAK_OUT, etc.)
- `device_id`: Device identifier
- `verify_code`, `work_code`: Device-specific codes
- `created_at`: Record creation timestamp

### `sync_log`
- `id`: Primary key
- `sync_datetime`: When sync was performed
- `records_processed`: Number of records processed
- `records_inserted`: Number of new records inserted
- `records_updated`: Number of records updated
- `status`: Sync status (SUCCESS, PARTIAL, FAILED)
- `error_message`: Error details if sync failed

## ZKTeco Device Setup

1. **Network Configuration**: Ensure your ZKTeco device is connected to the network
2. **IP Address**: Note the device's IP address (usually shown on device display)
3. **Port**: Default port is 4370 (can be changed in device settings)
4. **Access Control**: Ensure the device allows network connections

## Common ZKTeco Device Models Supported

This application works with most ZKTeco devices that support TCP/IP communication, including:
- ZKTeco K40
- ZKTeco F18/F19
- ZKTeco MA300/MA500
- ZKTeco U160/U260/U300
- ZKTeco IN01/IN02/IN05
- And many other models

## Troubleshooting

### Connection Issues

1. **Device not responding:**
   - Check IP address and port in .env file
   - Verify device is powered on and connected to network
   - Test ping to device: `ping <device_ip>`
   - Check firewall settings

2. **Database connection failed:**
   - Verify MySQL service is running
   - Check database credentials in .env file
   - Ensure database exists: `mysql -u root -p -e "SHOW DATABASES;"`

### Data Issues

1. **No attendance records:**
   - Check if device has attendance data
   - Verify date/time on device is correct
   - Check if users are properly enrolled on device

2. **Duplicate records:**
   - The system uses unique constraints to prevent duplicates
   - Duplicate prevention is based on employee_id + attendance_datetime

### Performance

- The application processes records in batches for better performance
- Large datasets (>10,000 records) may take several minutes to sync
- Consider running scheduled sync more frequently for real-time data

## Scheduled Deployment

For production deployment, you can:

### Using Cron (Linux/macOS)
```bash
# Add to crontab to run every 5 minutes
*/5 * * * * /usr/bin/python3 /path/to/project/main.py sync >> /var/log/attendance-sync.log 2>&1
```

### Using Task Scheduler (Windows)
Create a scheduled task that runs `python main.py sync` at your desired interval.

### Using systemd (Linux)
Create a service file for continuous scheduled sync:

```ini
[Unit]
Description=ZKTeco Attendance Sync Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 main.py schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

## Logging

The application creates detailed logs in `attendance_sync.log`:
- Connection status
- Sync operations
- Error details
- Performance metrics

Log levels can be configured in the .env file (DEBUG, INFO, WARNING, ERROR).

## Support

For issues or questions:
1. Check the logs in `attendance_sync.log`
2. Run `python main.py test` to verify connections
3. Ensure all configuration settings are correct
4. Verify ZKTeco device is accessible and functioning

## License

This project is provided as-is for educational and commercial use.
