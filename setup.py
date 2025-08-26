#!/usr/bin/env python3
"""
Setup script for ZKTeco MySQL Attendance Import System
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.7+"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required. Current version:", sys.version)
        return False
    print("✅ Python version:", sys.version.split()[0])
    return True

def install_requirements():
    """Install required Python packages"""
    try:
        print("📦 Installing Python packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def setup_env_file():
    """Setup .env file from template"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("⚠️  .env file already exists, skipping creation")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your configuration before running the application")
        return True
    else:
        print("❌ .env.example file not found")
        return False

def check_mysql():
    """Check if MySQL client is available"""
    try:
        result = subprocess.run(["mysql", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MySQL client found:", result.stdout.strip())
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  MySQL client not found. Please install MySQL client to setup database")
    return False

def setup_database():
    """Setup database schema"""
    if not check_mysql():
        print("⚠️  Skipping database setup. Run database_schema.sql manually when MySQL is available")
        return True
    
    print("\n📊 Database Setup")
    print("To setup the database, run the following command:")
    print("mysql -u root -p < database_schema.sql")
    print("(You'll need to enter your MySQL root password)")
    
    setup_now = input("\nWould you like to setup the database now? (y/N): ").lower().strip()
    
    if setup_now == 'y':
        try:
            username = input("MySQL username (default: root): ").strip() or "root"
            subprocess.check_call(["mysql", "-u", username, "-p", "-e", "source database_schema.sql"])
            print("✅ Database setup completed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Database setup failed: {e}")
            print("Please run the following command manually:")
            print("mysql -u root -p < database_schema.sql")
            return False
    else:
        print("⚠️  Database not setup. Run 'mysql -u root -p < database_schema.sql' when ready")
        return True

def make_executable():
    """Make main.py executable"""
    try:
        os.chmod("main.py", 0o755)
        print("✅ Made main.py executable")
        return True
    except Exception as e:
        print(f"⚠️  Could not make main.py executable: {e}")
        return True  # Not critical

def print_next_steps():
    """Print next steps for user"""
    print("\n" + "="*60)
    print("🎉 Setup completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Edit .env file with your configuration:")
    print("   - Set your MySQL database credentials")
    print("   - Set your ZKTeco device IP address")
    print("")
    print("2. Test the connections:")
    print("   python main.py test")
    print("")
    print("3. Sync users from device:")
    print("   python main.py sync-users")
    print("")
    print("4. Sync attendance data:")
    print("   python main.py sync")
    print("")
    print("5. For scheduled sync:")
    print("   python main.py schedule")
    print("")
    print("6. View attendance summary:")
    print("   python main.py summary")
    print("")
    print("For more information, see README.md")
    print("="*60)

def main():
    """Main setup function"""
    print("🚀 ZKTeco MySQL Attendance Import System Setup")
    print("="*60)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install requirements
    if success and not install_requirements():
        success = False
    
    # Setup .env file
    if success and not setup_env_file():
        success = False
    
    # Setup database
    if success and not setup_database():
        success = False
    
    # Make main.py executable
    if success:
        make_executable()
    
    if success:
        print_next_steps()
    else:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
