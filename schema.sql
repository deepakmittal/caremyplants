-- MySQL Schema for Garden Application

CREATE DATABASE IF NOT EXISTS garden_db;
USE garden_db;

-- User Table
-- Stores user profile information and contact details.
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL UNIQUE,
    user_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Garden Table
-- Stores high-level information about each garden.
CREATE TABLE gardens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- GardenUser Table (Junction Table)
-- Handles the many-to-many relationship between users and gardens.
CREATE TABLE garden_users (
    user_id INT,
    garden_id INT,
    role VARCHAR(50) DEFAULT 'owner', -- Added to distinguish permissions if needed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, garden_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (garden_id) REFERENCES gardens(id) ON DELETE CASCADE
);

-- Plant Table
-- Stores data for individual plants within a specific garden.
CREATE TABLE plants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    garden_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    plant_variety VARCHAR(255),
    `condition` VARCHAR(255), -- Fixed spelling from "conditition"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (garden_id) REFERENCES gardens(id) ON DELETE CASCADE
);

-- Garden_Updates Table
-- Stores periodic updates and recommendations for a garden.
CREATE TABLE garden_updates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    garden_id INT NOT NULL,
    status VARCHAR(255),
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (garden_id) REFERENCES gardens(id) ON DELETE CASCADE
);

-- Garden_Photos Table
-- Stores GCS URLs for photos associated with gardens and updates.
CREATE TABLE garden_photos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    garden_id INT NOT NULL,
    update_id INT DEFAULT NULL,
    photo_url VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (garden_id) REFERENCES gardens(id) ON DELETE CASCADE,
    FOREIGN KEY (update_id) REFERENCES garden_updates(id) ON DELETE SET NULL
);
