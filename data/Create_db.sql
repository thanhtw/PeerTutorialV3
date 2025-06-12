
-- Enhanced Database Schema for Java Peer Review Training System
-- Version: 2.0 with Comprehensive Logging and Badge System
-- New Datatable
SET FOREIGN_KEY_CHECKS = 0;
DROP VIEW IF EXISTS user_performance_summary;
DROP VIEW IF EXISTS daily_activity_summary;
DROP VIEW IF EXISTS badge_progress_summary; 

DROP TABLE IF EXISTS user_badges;
DROP TABLE IF EXISTS activity_log;
DROP TABLE IF EXISTS java_errors;
DROP TABLE IF EXISTS error_categories;
DROP TABLE IF EXISTS badges;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS user_interactions;
SET FOREIGN_KEY_CHECKS = 1;


-- Create users table
CREATE TABLE IF NOT EXISTS users (
    uid VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL, 
    password VARCHAR(255) NOT NULL,      
    display_name_en VARCHAR(255),
    display_name_zh VARCHAR(255),
    level_name_en VARCHAR(50) DEFAULT 'Basic',
    level_name_zh VARCHAR(50) DEFAULT '基礎',   
    reviews_completed INT DEFAULT 0,
    score INT DEFAULT 0,
    total_points INT DEFAULT 0,
    consecutive_days INT DEFAULT 0,
    last_activity DATE DEFAULT NULL,
    total_session_time INT DEFAULT 0,
    preferred_language ENUM('en', 'zh') DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_email (email),
    INDEX idx_level (level_name_en),
    INDEX idx_points (total_points DESC),
    INDEX idx_activity (last_activity DESC),
    INDEX idx_performance (reviews_completed, score)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Badges table
CREATE TABLE IF NOT EXISTS badges (
    badge_id VARCHAR(50) PRIMARY KEY,
    name_en VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100) NOT NULL,
    description_en TEXT NOT NULL,
    description_zh TEXT NOT NULL,
    icon VARCHAR(50) DEFAULT '🏅',
    category ENUM('achievement', 'progress', 'skill', 'consistency', 'special') DEFAULT 'achievement',
    difficulty ENUM('easy', 'medium', 'hard', 'legendary') DEFAULT 'medium',
    points INT DEFAULT 10,
    rarity ENUM('common', 'uncommon', 'rare', 'epic', 'legendary') DEFAULT 'common',
    prerequisite_badges JSON, 
    criteria JSON NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_category (category),
    INDEX idx_difficulty (difficulty),
    INDEX idx_rarity (rarity),
    INDEX idx_active (is_active)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- User Sessions - Track overall user sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP NULL,
    session_duration_minutes INT DEFAULT 0,
    total_interactions INT DEFAULT 0,   
    language_preference VARCHAR(10) DEFAULT 'en',     
    tabs_visited JSON NULL,   
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    INDEX idx_user_session (user_id, session_start DESC),
    INDEX idx_session_duration (session_duration_minutes DESC),
    INDEX idx_session_date (session_start)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;


-- Error categories table
CREATE TABLE error_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,    
    name_en VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100) NOT NULL,
    description_en TEXT,
    description_zh TEXT,
    icon VARCHAR(50) DEFAULT '📂',
    sort_order INT DEFAULT 0,    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name_en (name_en),
    INDEX idx_sort_order (sort_order)    
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Java errors table
CREATE TABLE java_errors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    error_code VARCHAR(100) NOT NULL UNIQUE,
    category_id INT NOT NULL,
    error_name_en VARCHAR(200) NOT NULL,
    error_name_zh VARCHAR(200) NOT NULL,
    description_en TEXT NOT NULL,
    description_zh TEXT NOT NULL,
    implementation_guide_en TEXT, 
    implementation_guide_zh TEXT,
    difficulty_level ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    frequency_weight INT DEFAULT 1,
    tags JSON,
    examples JSON,    
    usage_count INT DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.00,
    avg_identification_time INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES error_categories(id) ON DELETE CASCADE,
    INDEX idx_error_code (error_code),
    INDEX idx_category_difficulty (category_id, difficulty_level),
    INDEX idx_usage_stats (usage_count, success_rate)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- User badges table
CREATE TABLE user_badges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    badge_id VARCHAR(50) NOT NULL,
    awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    progress_data JSON,
    notification_sent BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badges(badge_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_badge (user_id, badge_id),
    INDEX idx_user_awarded (user_id, awarded_at DESC),
    INDEX idx_badge_awarded (badge_id, awarded_at DESC)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Activity log table
CREATE TABLE activity_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    points INT NOT NULL,
    details_en TEXT,
    details_zh TEXT,
    metadata JSON,
    related_entity_type VARCHAR(50),
    related_entity_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    INDEX idx_user_activity (user_id, created_at DESC),
    INDEX idx_activity_type (activity_type, created_at DESC),
    INDEX idx_points (points DESC),
    INDEX idx_related_entity (related_entity_type, related_entity_id)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

--User Interactions - Detailed interaction logging
CREATE TABLE IF NOT EXISTS user_interactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    interaction_type ENUM('review_analysis_complete','view_feedback_tab','view_code_generator','analysis_complete','review_analysis_start','start_review','code_ready_for_review','generate_completed','start_generate','view_progress_dashboard','view_badge_showcase','deselect_category','select_category','submit_review','view_code_display','tutorial_identification_attempt','start_practice_session','complete_tutorial_abandoned','complete_tutorial_incomplete','complete_tutorial_completed','tutorial_step_code_generate_complete','tutorial_step_code_generation_no_output','tutorial_step_code_generation_failed','tutorial_step_code_generation_started','tutorial_step_submit_again','tutorial_step_review_analysis_complete','tutorial_step_review_submitted','tutorial_step_ready_for_review','code_generation_exception','start_tutorial_error','start_tutorial_code_generation','filter_by_difficulty','filter_by_category','search_errors','regenerate_tutorial_code','restart_tutorial_session','review_processing_error','error_identification_attempt','start_tutorial_session_error','start_tutorial_session','access_tutorial_ui','action','error_identification','complete_workflow','start_workflow','status_change','start_session','step_change','access','click', 'submit', 'navigation', 'view', 'edit', 'download', 'upload', 'search', 'filter', 'error', 'success', 'warning','mode_change') NOT NULL,
    interaction_category VARCHAR(50) NOT NULL,
    component VARCHAR(100) NOT NULL, 
    action VARCHAR(100) NOT NULL, 
    details JSON,
    time_spent_seconds INT DEFAULT 0,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    context_data JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    INDEX idx_user_timestamp (user_id, timestamp DESC),
    INDEX idx_interaction_type (interaction_type, timestamp DESC),
    INDEX idx_category_action (interaction_category, action),
    INDEX idx_success_errors (success, error_message(100))
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- User Performance Summary View
CREATE VIEW user_performance_summary AS
SELECT 
    u.uid,
    u.display_name_en,
    u.display_name_zh,
    u.reviews_completed,
    u.total_points,
    u.consecutive_days,
    COUNT(DISTINCT ub.badge_id) as total_badges,    
    AVG(ecs.mastery_level) as avg_mastery,
    (SELECT COUNT(*) FROM user_sessions WHERE user_id = u.uid) as total_sessions,
    COALESCE(SUM(us.session_duration_minutes), 0) as total_time_minutes
FROM users u
LEFT JOIN user_badges ub ON u.uid = ub.user_id
LEFT JOIN user_sessions us ON u.uid = us.user_id
GROUP BY u.uid;

-- Daily Activity Summary View
CREATE VIEW daily_activity_summary AS
SELECT 
    DATE(timestamp) as activity_date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) as total_interactions,
    AVG(time_spent_seconds) as avg_interaction_time,
    COUNT(CASE WHEN success = FALSE THEN 1 END) as error_count,
    COUNT(CASE WHEN interaction_type = 'submit' THEN 1 END) as submissions
FROM user_interactions
WHERE timestamp >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
GROUP BY DATE(timestamp)
ORDER BY activity_date DESC;

-- Badge Progress Summary View
CREATE VIEW badge_progress_summary AS
SELECT 
    b.badge_id,
    b.name_en,
    b.category,
    b.difficulty,
    COUNT(ub.user_id) as users_earned,
    AVG(DATEDIFF(ub.awarded_at, (
        SELECT MIN(created_at) FROM activity_log WHERE user_id = ub.user_id
    ))) as avg_days_to_earn
FROM badges b
LEFT JOIN user_badges ub ON b.badge_id = ub.badge_id
GROUP BY b.badge_id
ORDER BY users_earned DESC;

-- Verification and status
SELECT 'Database tables created successfully!' as Status;
SELECT COUNT(table_name) as Tables_Created 
FROM information_schema.tables 
WHERE table_schema = DATABASE() 
AND table_name IN ('users', 'error_categories', 'java_errors', 'badges', 'user_badges', 'activity_log', 'user_sessions', 'user_interactions');   

