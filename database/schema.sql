-- Regenerated schema.sql for codehub database (as of 2025-05-09)

CREATE DATABASE IF NOT EXISTS codehub;
USE codehub;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(200) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Repositories table
CREATE TABLE IF NOT EXISTS repositories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    user_id INT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Commits table
CREATE TABLE IF NOT EXISTS commits (
    id INT PRIMARY KEY AUTO_INCREMENT,
    commit_hash VARCHAR(40) NOT NULL UNIQUE,
    message TEXT NOT NULL,
    user_id INT NOT NULL,
    repository_id INT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    parent_hash VARCHAR(40),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (repository_id) REFERENCES repositories(id)
);

-- Files table
CREATE TABLE IF NOT EXISTS files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    repo_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);

-- CommitFiles table
CREATE TABLE IF NOT EXISTS commit_files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    commit_id INT NOT NULL,
    file_id INT NOT NULL,
    content TEXT,
    status VARCHAR(20),
    FOREIGN KEY (commit_id) REFERENCES commits(id),
    FOREIGN KEY (file_id) REFERENCES files(id)
);

-- Branches table
CREATE TABLE IF NOT EXISTS branches (
    id INT PRIMARY KEY AUTO_INCREMENT,
    branch_name VARCHAR(100) NOT NULL,
    repository_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_commit_hash VARCHAR(40),
    FOREIGN KEY (repository_id) REFERENCES repositories(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Working tree table
CREATE TABLE IF NOT EXISTS working_tree (
    id INT PRIMARY KEY AUTO_INCREMENT,
    repo_id INT NOT NULL,
    file_id INT NOT NULL,
    content TEXT,
    status VARCHAR(20),
    timestamp DATETIME,
    FOREIGN KEY (repo_id) REFERENCES repositories(id),
    FOREIGN KEY (file_id) REFERENCES files(id)
);

-- Staging area table
CREATE TABLE IF NOT EXISTS staging_area (
    id INT PRIMARY KEY AUTO_INCREMENT,
    repo_id INT NOT NULL,
    file_id INT NOT NULL,
    content TEXT,
    status VARCHAR(20),
    timestamp DATETIME,
    FOREIGN KEY (repo_id) REFERENCES repositories(id),
    FOREIGN KEY (file_id) REFERENCES files(id)
);

