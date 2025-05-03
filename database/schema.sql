CREATE DATABASE codehub;
USE codehub;
CREATE TABLE `users` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE `branches` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `branch_name` VARCHAR(100) NOT NULL,
  `head_commit_id` INT,
  `user_id` INT,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
);
CREATE TABLE `files` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `filename` VARCHAR(255) NOT NULL,
  `content` TEXT NOT NULL,
  `user_id` INT,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
);
CREATE TABLE `commits` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `commit_hash` CHAR(40) NOT NULL,
  `message` TEXT,
  `file_id` INT DEFAULT NULL,
  `branch_id` INT DEFAULT NULL,
  `parent_commit_id` INT DEFAULT NULL,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `merge_from_commit_id` INT DEFAULT NULL,
  `merge_status` VARCHAR(50) DEFAULT NULL,
  FOREIGN KEY (`file_id`) REFERENCES `files`(`id`),
  FOREIGN KEY (`branch_id`) REFERENCES `branches`(`id`),
  FOREIGN KEY (`parent_commit_id`) REFERENCES `commits`(`id`),
  FOREIGN KEY (`merge_from_commit_id`) REFERENCES `commits`(`id`)
);
-- Add foreign key for `head_commit_id` in the `branches` table
ALTER TABLE `branches`
  ADD FOREIGN KEY (`head_commit_id`) REFERENCES `commits`(`id`);
-- Insert sample user
INSERT INTO `users` (name, email) VALUES ('John Doe', 'john.doe@example.com');

-- Insert a branch for this user (assuming user_id = 1)
INSERT INTO `branches` (branch_name, user_id) VALUES ('main', 1);

-- Insert a file for this user (assuming user_id = 1)
INSERT INTO `files` (filename, content, user_id) VALUES ('README.md', 'This is a sample project', 1);

-- Insert a commit for the user (assuming file_id = 1, branch_id = 1, and no parent_commit_id)
INSERT INTO `commits` (commit_hash, message, file_id, branch_id, parent_commit_id) 
VALUES ('abc123hash', 'Initial commit', 1, 1, NULL);
