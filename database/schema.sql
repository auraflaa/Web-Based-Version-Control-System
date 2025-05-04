CREATE DATABASE codehub;
USE codehub;

CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL
);

CREATE TABLE branches (
  id INT PRIMARY KEY AUTO_INCREMENT,
  branch_name VARCHAR(100) NOT NULL,
  head_commit_id INT,
  user_id INT,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE files (
  id INT PRIMARY KEY AUTO_INCREMENT,
  filename VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE commits (
  id INT PRIMARY KEY AUTO_INCREMENT,
  commit_hash CHAR(40) NOT NULL,
  message TEXT,
  branch_id INT,
  user_id INT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  merge_status VARCHAR(50) DEFAULT NULL,
  FOREIGN KEY (branch_id) REFERENCES branches(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE commit_files (
  commit_id INT,
  file_id INT,
  content TEXT NOT NULL,
  PRIMARY KEY (commit_id, file_id),
  FOREIGN KEY (commit_id) REFERENCES commits(id),
  FOREIGN KEY (file_id) REFERENCES files(id)
);

CREATE TABLE commit_parents (
  commit_id INT,
  parent_commit_id INT,
  PRIMARY KEY (commit_id, parent_commit_id),
  FOREIGN KEY (commit_id) REFERENCES commits(id),
  FOREIGN KEY (parent_commit_id) REFERENCES commits(id)
);

ALTER TABLE branches
  ADD FOREIGN KEY (head_commit_id) REFERENCES commits(id);

CREATE TABLE repositories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Table for working tree (tracks modified/untracked files per user/repo)
CREATE TABLE working_tree (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    repo_id INT,
    file_path VARCHAR(512) NOT NULL,
    status VARCHAR(32) NOT NULL, -- e.g., 'modified', 'deleted', 'untracked'
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);

-- Table for staging area (tracks staged files per user/repo)
CREATE TABLE staging_area (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    repo_id INT,
    file_path VARCHAR(512) NOT NULL,
    staged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);

-- Update already inputted values with demo passwords (plain text for demo, use hashes in production)
UPDATE users SET password = 'alice123' WHERE email = 'alice@example.com';
UPDATE users SET password = 'bob123' WHERE email = 'bob@example.com';