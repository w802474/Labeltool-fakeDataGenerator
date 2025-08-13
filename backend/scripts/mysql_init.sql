-- MySQL initialization script for LabelTool
-- This script sets up the database with proper character encoding and timezone

-- Set default character encoding
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Set timezone to UTC for consistency
SET time_zone = '+00:00';

-- Enable strict mode for better data integrity
SET sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';

-- Create database if it doesn't exist (usually already created by Docker)
-- CREATE DATABASE IF NOT EXISTS labeltool_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Switch to the database
USE labeltool_db;

-- Grant necessary privileges to the application user
-- (User is already created by Docker environment variables)

-- Enable JSON data type validation
-- MySQL 8.0 natively supports JSON, no additional setup needed

-- Log initialization completion
SELECT 'MySQL database initialized successfully for LabelTool' as Status;