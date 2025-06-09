-- Drop existing tables if they exist (in correct order to handle foreign keys)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS user_badges;
DROP TABLE IF EXISTS activity_log;
DROP TABLE IF EXISTS error_usage_stats;
DROP TABLE IF EXISTS java_errors;
DROP TABLE IF EXISTS error_categories;
DROP TABLE IF EXISTS badges;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- Create users table
CREATE TABLE users (
    uid VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,       
    display_name_en VARCHAR(255),
    display_name_zh VARCHAR(255),
    password VARCHAR(255) NOT NULL,       
    level_name_en VARCHAR(50) DEFAULT 'Basic',
    level_name_zh VARCHAR(50) DEFAULT '基礎',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviews_completed INT DEFAULT 0,
    score INT DEFAULT 0,
    last_activity DATE DEFAULT NULL,
    consecutive_days INT DEFAULT 0,
    total_points INT DEFAULT 0,
    INDEX idx_email (email),
    INDEX idx_last_activity (last_activity)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Error categories table
CREATE TABLE error_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_code VARCHAR(50) NOT NULL UNIQUE,
    name_en VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100) NOT NULL,
    description_en TEXT,
    description_zh TEXT,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category_code (category_code),
    INDEX idx_sort_order (sort_order),
    INDEX idx_active (is_active)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Java errors table
CREATE TABLE java_errors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    error_code VARCHAR(100) NOT NULL UNIQUE,
    category_id INT NOT NULL,
    
    -- English fields
    error_name_en VARCHAR(200) NOT NULL,
    description_en TEXT NOT NULL,
    implementation_guide_en TEXT,
    
    -- Chinese fields  
    error_name_zh VARCHAR(200) NOT NULL,
    description_zh TEXT NOT NULL,
    implementation_guide_zh TEXT,
    
    -- Additional metadata
    difficulty_level ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    frequency_weight INT DEFAULT 1,
    tags JSON,
    examples JSON,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES error_categories(id) ON DELETE CASCADE,
    INDEX idx_category_id (category_id),
    INDEX idx_error_code (error_code),
    INDEX idx_difficulty (difficulty_level),
    INDEX idx_active (is_active),
    INDEX idx_usage_count (usage_count)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Badges table
CREATE TABLE badges (
    badge_id VARCHAR(50) PRIMARY KEY,
    name_en VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100) NOT NULL,
    description_en TEXT NOT NULL,
    description_zh TEXT NOT NULL,
    icon VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    points INT DEFAULT 10,
    achievement_category VARCHAR(50) DEFAULT 'learning_journey',
    unlock_criteria JSON,
    rarity VARCHAR(20) DEFAULT 'common',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_difficulty (difficulty)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- User badges table
CREATE TABLE user_badges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    badge_id VARCHAR(50) NOT NULL,
    awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badges(badge_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_badge (user_id, badge_id),
    INDEX idx_user_id (user_id),
    INDEX idx_badge_id (badge_id)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Activity log table
CREATE TABLE activity_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    points INT NOT NULL,
    details_en TEXT,
    details_zh TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_activity_type (activity_type),
    INDEX idx_created_at (created_at)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Error usage statistics table
CREATE TABLE error_usage_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    error_id INT NOT NULL,
    user_id VARCHAR(36),
    session_id VARCHAR(36),
    action_type ENUM('viewed', 'practiced', 'mastered', 'failed') NOT NULL,
    context_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (error_id) REFERENCES java_errors(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE SET NULL,
    INDEX idx_error_user (error_id, user_id),
    INDEX idx_session (session_id),
    INDEX idx_action_type (action_type),
    INDEX idx_created_at (created_at)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 1. User Sessions - Track overall user sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP NULL,
    session_duration_minutes INT DEFAULT 0,
    total_interactions INT DEFAULT 0,
    tabs_visited JSON,
    device_info JSON,
    user_agent TEXT,
    ip_address VARCHAR(45),
    language_preference VARCHAR(10) DEFAULT 'en',
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    INDEX idx_user_sessions_user_id (user_id),
    INDEX idx_user_sessions_start (session_start)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. User Interactions - Detailed interaction logging
CREATE TABLE IF NOT EXISTS user_interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    interaction_category VARCHAR(50) NOT NULL,
    component VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_spent_seconds INT DEFAULT 0,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT NULL,
    context_data JSON,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    INDEX idx_interactions_session (session_id),
    INDEX idx_interactions_user (user_id),
    INDEX idx_interactions_type (interaction_type),
    INDEX idx_interactions_timestamp (timestamp)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 3. Practice Sessions - Specific to Error Explorer
CREATE TABLE IF NOT EXISTS practice_sessions (
    practice_session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    error_code VARCHAR(100) NOT NULL,
    error_name VARCHAR(200) NOT NULL,
    error_category VARCHAR(100) NOT NULL,
    difficulty_level VARCHAR(20) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    status ENUM('setup', 'code_ready', 'review_complete', 'abandoned') DEFAULT 'setup',
    total_duration_minutes INT DEFAULT 0,
    code_generation_attempts INT DEFAULT 0,
    review_iterations INT DEFAULT 0,
    final_accuracy_percentage FLOAT DEFAULT 0.0,
    errors_identified INT DEFAULT 0,
    total_errors INT DEFAULT 0,
    practice_data JSON,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_practice_user (user_id),
    INDEX idx_practice_error (error_code),
    INDEX idx_practice_status (status),
    INDEX idx_practice_started (started_at)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 4. Workflow Tracking - Main workflow progress
CREATE TABLE IF NOT EXISTS workflow_tracking (
    workflow_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    workflow_type VARCHAR(50) DEFAULT 'main_workflow',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    current_step VARCHAR(50) NOT NULL,
    total_steps_completed INT DEFAULT 0,
    code_generation_time_seconds INT DEFAULT 0,
    review_time_seconds INT DEFAULT 0,
    feedback_time_seconds INT DEFAULT 0,
    selected_categories JSON,
    selected_errors JSON,
    code_length VARCHAR(20),
    difficulty_level VARCHAR(20),
    final_results JSON,
    status ENUM('in_progress', 'completed', 'abandoned') DEFAULT 'in_progress',
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_workflow_user (user_id),
    INDEX idx_workflow_session (session_id),
    INDEX idx_workflow_type (workflow_type),
    INDEX idx_workflow_status (status)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 5. Tab Navigation Tracking
CREATE TABLE IF NOT EXISTS tab_navigation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    from_tab VARCHAR(50),
    to_tab VARCHAR(50) NOT NULL,
    tab_index INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_spent_on_previous_tab_seconds INT DEFAULT 0,
    navigation_trigger VARCHAR(50),
    context_data JSON,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    INDEX idx_tab_nav_session (session_id),
    INDEX idx_tab_nav_user (user_id),
    INDEX idx_tab_nav_timestamp (timestamp)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 6. Error Identification Analysis
CREATE TABLE IF NOT EXISTS error_identification_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    practice_session_id VARCHAR(36) NULL,
    workflow_id VARCHAR(36) NULL,
    error_code VARCHAR(100) NOT NULL,
    review_iteration INT NOT NULL,
    review_text TEXT NOT NULL,
    identified_correctly BOOLEAN DEFAULT FALSE,
    time_to_identify_seconds INT DEFAULT 0,
    confidence_level VARCHAR(20),
    review_quality_score FLOAT DEFAULT 0.0,
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    llm_analysis_data JSON,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (practice_session_id) REFERENCES practice_sessions(practice_session_id) ON DELETE SET NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflow_tracking(workflow_id) ON DELETE SET NULL,
    INDEX idx_error_analysis_user (user_id),
    INDEX idx_error_analysis_error (error_code),
    INDEX idx_error_analysis_timestamp (analysis_timestamp)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 7. Learning Path Progress
CREATE TABLE IF NOT EXISTS learning_path_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    error_category VARCHAR(100) NOT NULL,
    total_encounters INT DEFAULT 0,
    successful_identifications INT DEFAULT 0,
    practice_sessions_count INT DEFAULT 0,
    main_workflow_encounters INT DEFAULT 0,
    average_time_to_identify_seconds FLOAT DEFAULT 0.0,
    improvement_trend FLOAT DEFAULT 0.0,
    mastery_level FLOAT DEFAULT 0.0, 
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    progress_data JSON,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    UNIQUE KEY unique_user_category (user_id, error_category),
    INDEX idx_learning_progress_user (user_id),
    INDEX idx_learning_progress_category (error_category),
    INDEX idx_learning_progress_mastery (mastery_level)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;


-- Verification and status
SELECT 'Database tables created successfully!' as Status;
SELECT COUNT(table_name) as Tables_Created 
FROM information_schema.tables 
WHERE table_schema = DATABASE() 
AND table_name IN ('users', 'error_categories', 'java_errors', 'badges', 'user_badges', 'activity_log', 'error_usage_stats', 
                   'user_sessions', 'user_interactions', 'practice_sessions', 'workflow_tracking', 
                   'tab_navigation', 'error_identification_analysis', 'learning_path_progress');