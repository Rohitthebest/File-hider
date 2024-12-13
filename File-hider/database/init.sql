-- Create database
CREATE DATABASE IF NOT EXISTS file_hider_db;
USE file_hider_db;

-- Users table
CREATE USER 'fileuser'@'%' IDENTIFIED WITH mysql_native_password BY 'filepassword';
GRANT ALL PRIVILEGES ON file_hider_db.* TO 'fileuser'@'%';
FLUSH PRIVILEGES;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hidden files table
CREATE TABLE hidden_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    hidden_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    hidden_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);