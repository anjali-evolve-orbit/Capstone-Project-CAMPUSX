-- ============================================================
-- CAMPUSX — Discover People Behind the Work System
-- Normalized MySQL Relational Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS `campusx_db`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE `campusx_db`;

-- 1. CAMPUSES TABLE
CREATE TABLE IF NOT EXISTS `campuses` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL UNIQUE,
    `location` VARCHAR(255) DEFAULT NULL,
    `description` TEXT DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. INSTITUTIONS / COLLEGES TABLE
CREATE TABLE IF NOT EXISTS `institutions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `campus_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `code` VARCHAR(50) DEFAULT NULL,
    `is_custom` BOOLEAN DEFAULT FALSE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`campus_id`) REFERENCES `campuses`(`id`) ON DELETE CASCADE,
    INDEX `idx_institution_campus` (`campus_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. DEPARTMENTS / PROGRAMS TABLE
CREATE TABLE IF NOT EXISTS `departments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `institution_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `code` VARCHAR(50) DEFAULT NULL,
    `is_custom` BOOLEAN DEFAULT FALSE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE CASCADE,
    INDEX `idx_department_institution` (`institution_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. USERS TABLE
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(150) NOT NULL,
    `email` VARCHAR(191) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('Student', 'Researcher', 'Faculty', 'Other') NOT NULL DEFAULT 'Student',
    `campus_id` INT DEFAULT NULL,
    `institution_id` INT DEFAULT NULL,
    `department_id` INT DEFAULT NULL,
    `custom_institution` VARCHAR(255) DEFAULT NULL,
    `custom_department` VARCHAR(255) DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`campus_id`) REFERENCES `campuses`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`) ON DELETE SET NULL,
    INDEX `idx_user_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. RESEARCHERS TABLE
CREATE TABLE IF NOT EXISTS `researchers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT DEFAULT NULL UNIQUE,
    `name` VARCHAR(150) NOT NULL,
    `designation` VARCHAR(150) NOT NULL,
    `institution_id` INT DEFAULT NULL,
    `department_id` INT DEFAULT NULL,
    `bio` TEXT DEFAULT NULL,
    `avatar_color` VARCHAR(20) DEFAULT '#1E4E8C',
    `citation_count` INT DEFAULT 0,
    `h_index` INT DEFAULT 0,
    `email` VARCHAR(191) DEFAULT NULL,
    `website` VARCHAR(255) DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`) ON DELETE SET NULL,
    INDEX `idx_researcher_dept` (`department_id`),
    INDEX `idx_researcher_inst` (`institution_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. RESEARCH AREAS TABLE
CREATE TABLE IF NOT EXISTS `research_areas` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(150) NOT NULL UNIQUE,
    `description` TEXT DEFAULT NULL,
    `icon_name` VARCHAR(50) DEFAULT 'Brain',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. RESEARCHER_AREAS LINK TABLE
CREATE TABLE IF NOT EXISTS `researcher_areas` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `researcher_id` INT NOT NULL,
    `research_area_id` INT NOT NULL,
    FOREIGN KEY (`researcher_id`) REFERENCES `researchers`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`research_area_id`) REFERENCES `research_areas`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `unique_researcher_area` (`researcher_id`, `research_area_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 14. SKILLS TABLE
CREATE TABLE IF NOT EXISTS `skills` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(150) NOT NULL UNIQUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 15. RESEARCHER_SKILLS LINK TABLE
CREATE TABLE IF NOT EXISTS `researcher_skills` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `researcher_id` INT NOT NULL,
    `skill_id` INT NOT NULL,
    FOREIGN KEY (`researcher_id`) REFERENCES `researchers`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`skill_id`) REFERENCES `skills`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `unique_researcher_skill` (`researcher_id`, `skill_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. PAPERS TABLE
CREATE TABLE IF NOT EXISTS `papers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(300) NOT NULL,
    `abstract` TEXT DEFAULT NULL,
    `publication_year` INT NOT NULL,
    `venue` VARCHAR(255) DEFAULT NULL,
    `citation_count` INT DEFAULT 0,
    `doi` VARCHAR(100) DEFAULT NULL,
    `pdf_url` VARCHAR(255) DEFAULT NULL,
    `primary_area_id` INT DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`primary_area_id`) REFERENCES `research_areas`(`id`) ON DELETE SET NULL,
    INDEX `idx_paper_year` (`publication_year`),
    INDEX `idx_paper_area` (`primary_area_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. PAPER_AUTHORS LINK TABLE
CREATE TABLE IF NOT EXISTS `paper_authors` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `paper_id` INT NOT NULL,
    `researcher_id` INT NOT NULL,
    `author_order` INT DEFAULT 1,
    FOREIGN KEY (`paper_id`) REFERENCES `papers`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`researcher_id`) REFERENCES `researchers`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `unique_paper_author` (`paper_id`, `researcher_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. PAPER_AREAS LINK TABLE
CREATE TABLE IF NOT EXISTS `paper_areas` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `paper_id` INT NOT NULL,
    `research_area_id` INT NOT NULL,
    FOREIGN KEY (`paper_id`) REFERENCES `papers`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`research_area_id`) REFERENCES `research_areas`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `unique_paper_area` (`paper_id`, `research_area_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. COMMUNITIES TABLE
CREATE TABLE IF NOT EXISTS `communities` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(200) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `institution_id` INT DEFAULT NULL,
    `category` VARCHAR(100) DEFAULT 'Research Group',
    `member_count` INT DEFAULT 1,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. COMMUNITY_MEMBERS LINK TABLE
CREATE TABLE IF NOT EXISTS `community_members` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `community_id` INT NOT NULL,
    `researcher_id` INT NOT NULL,
    `role` VARCHAR(100) DEFAULT 'Member',
    FOREIGN KEY (`community_id`) REFERENCES `communities`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`researcher_id`) REFERENCES `researchers`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `unique_community_member` (`community_id`, `researcher_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 13. COLLABORATIONS TABLE (FOR GRAPH/BFS/DFS)
CREATE TABLE IF NOT EXISTS `collaborations` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `researcher1_id` INT NOT NULL,
    `researcher2_id` INT NOT NULL,
    `paper_count` INT DEFAULT 1,
    `joint_papers_desc` TEXT DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`researcher1_id`) REFERENCES `researchers`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`researcher2_id`) REFERENCES `researchers`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `unique_collaboration_pair` (`researcher1_id`, `researcher2_id`),
    INDEX `idx_collab_r1` (`researcher1_id`),
    INDEX `idx_collab_r2` (`researcher2_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
