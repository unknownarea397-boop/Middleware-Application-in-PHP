# Quick Start Guide

## ZKTeco MySQL Attendance Import System

### 🚀 Quick Setup (5 minutes)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup database:**
   ```bash
   mysql -u root -p < database_schema.sql
   ```

3. **Configure application:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Test connections:**
   ```bash
   python main.py test
   ```

### 📋 Configuration Checklist

Edit `.env` file with your settings:

- [ ] **DB_HOST** - Your MySQL server (usually `localhost`)
- [ ] **DB_USER** - MySQL username  
- [ ] **DB_PASSWORD** - MySQL password
- [ ] **DB_NAME** - Database name (`attendance_system`)
- [ ] **ZKTECO_IP** - Your ZKTeco device IP address
- [ ] **ZKTECO_PORT** - Device port (usually `4370`)

### ✅ Quick Commands

| Command | Description |
|---------|-------------|
| `python main.py test` | Test all connections |
| `python main.py sync-users` | Sync employees from device |
| `python main.py sync` | Sync attendance data |
| `python main.py schedule` | Run automatic sync |
| `python main.py summary` | Show attendance report |
| `python web_interface.py` | Start web dashboard |

### 🔧 Troubleshooting

**Can't connect to device?**
- Check device IP address: `ping YOUR_DEVICE_IP`
- Verify device port (usually 4370)
- Ensure device allows TCP connections

**Database connection failed?**
- Check MySQL service: `sudo systemctl status mysql`
- Verify credentials in `.env` file
- Create database: `mysql -u root -p -e "CREATE DATABASE attendance_system;"`

**No attendance data?**
- Check if device has records
- Verify employee enrollment on device
- Try: `python demo.py full-demo` for testing

### 📊 Web Dashboard

Start the web interface to monitor your system:

```bash
python web_interface.py
```

Then visit: http://localhost:5000

### 🧪 Demo Mode

Try the system with sample data:

```bash
python demo.py full-demo
```

This creates sample employees and attendance records for testing.

### 📈 Production Deployment

For production use:

1. **Scheduled Sync** (every 5 minutes):
   ```bash
   # Add to crontab
   */5 * * * * cd /path/to/project && python main.py sync
   ```

2. **Web Dashboard Service**:
   ```bash
   # Run as background service
   python web_interface.py &
   ```

3. **Monitoring**:
   - Check logs: `tail -f attendance_sync.log`
   - View sync status in web dashboard
   - Set up alerts for failed syncs

### 📞 Support

- Check `README.md` for detailed documentation
- Run `python main.py help` for command help
- Check logs in `attendance_sync.log`
- Test individual components with `python demo.py`

---

**Need help?** 
- Make sure your ZKTeco device supports TCP/IP
- Most devices work out of the box
- Default credentials are usually not required
- Check device manual for network settings
