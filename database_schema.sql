-- Create database
CREATE DATABASE IF NOT EXISTS attendance_system;
USE attendance_system;

-- Create employees table
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    employee_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create attendance table
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    employee_name VARCHAR(255) NOT NULL,
    attendance_datetime DATETIME NOT NULL,
    punch_type ENUM('IN', 'OUT', 'BREAK_OUT', 'BREAK_IN', 'OVERTIME_IN', 'OVERTIME_OUT') DEFAULT 'IN',
    device_id VARCHAR(50),
    verify_code INT DEFAULT 0,
    work_code INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (employee_id, attendance_datetime),
    INDEX idx_employee_date (employee_id, attendance_datetime),
    INDEX idx_attendance_date (attendance_datetime)
);

-- Create sync_log table to track synchronization
CREATE TABLE IF NOT EXISTS sync_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sync_datetime DATETIME NOT NULL,
    records_processed INT DEFAULT 0,
    records_inserted INT DEFAULT 0,
    records_updated INT DEFAULT 0,
    status ENUM('SUCCESS', 'PARTIAL', 'FAILED') NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert some sample employees (optional)
INSERT IGNORE INTO employees (employee_id, employee_name) VALUES 
('EMP001', 'John Doe'),
('EMP002', 'Jane Smith'),
('EMP003', 'Bob Johnson');
