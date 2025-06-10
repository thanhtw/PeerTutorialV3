
-- Enhanced Database Schema for Java Peer Review Training System
-- Version: 2.0 with Comprehensive Logging and Badge System
-- New Datatable
SET FOREIGN_KEY_CHECKS = 0;
DROP VIEW IF EXISTS user_performance_summary;
DROP VIEW IF EXISTS daily_activity_summary;
DROP VIEW IF EXISTS badge_progress_summary; 
DROP TABLE IF EXISTS system_performance_logs;
DROP TABLE IF EXISTS badge_progress_logs;
DROP TABLE IF EXISTS learning_achievements;
DROP TABLE IF EXISTS user_engagement_metrics;
DROP TABLE IF EXISTS system_alerts;
DROP TABLE IF EXISTS system_metrics;



DROP TABLE IF EXISTS user_badges;
DROP TABLE IF EXISTS activity_log;
DROP TABLE IF EXISTS error_usage_stats;
DROP TABLE IF EXISTS java_errors;
DROP TABLE IF EXISTS error_categories;
DROP TABLE IF EXISTS badges;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS user_interactions;
DROP TABLE IF EXISTS practice_sessions;
DROP TABLE IF EXISTS workflow_tracking;
DROP TABLE IF EXISTS tab_navigation;
DROP TABLE IF EXISTS error_identification_analysis;
DROP TABLE IF EXISTS learning_path_progress;
DROP TABLE IF EXISTS error_category_stats;
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
    device_info JSON,
    language_preference VARCHAR(10) DEFAULT 'en',
    ip_address VARCHAR(45),
    user_agent TEXT,
    tabs_visited JSON,
    performance_metrics JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    INDEX idx_user_session (user_id, session_start DESC),
    INDEX idx_session_duration (session_duration_minutes DESC),
    INDEX idx_session_date (session_start)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- New Datatables
CREATE TABLE system_performance_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    component VARCHAR(50) NOT NULL, 
    operation VARCHAR(100) NOT NULL, 
    execution_time_ms INT,
    memory_used_mb DECIMAL(8,2),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    user_id VARCHAR(36),
    session_id VARCHAR(36), 
    performance_data JSON,
    
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE SET NULL,
    INDEX idx_component_time (component, timestamp DESC),
    INDEX idx_operation_performance (operation, execution_time_ms),
    INDEX idx_errors (success, timestamp DESC),
    INDEX idx_user_performance (user_id, timestamp DESC)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE badge_progress_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    badge_id VARCHAR(50) NOT NULL,
    progress_type ENUM('criteria_met', 'progress_update', 'badge_awarded') NOT NULL,
    criteria_key VARCHAR(100), 
    old_value DECIMAL(10,2),
    new_value DECIMAL(10,2),
    progress_percentage DECIMAL(5,2),
    is_completed BOOLEAN DEFAULT FALSE,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context_data JSON,
    
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badges(badge_id) ON DELETE CASCADE,
    INDEX idx_user_badge_progress (user_id, badge_id, logged_at DESC),
    INDEX idx_progress_type (progress_type, logged_at DESC),
    INDEX idx_badge_completion (badge_id, is_completed, logged_at DESC)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Learning Achievements (Milestone Tracking)
CREATE TABLE learning_achievements (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    achievement_type ENUM('milestone', 'streak', 'mastery', 'speed', 'accuracy', 'exploration') NOT NULL,
    achievement_name VARCHAR(100) NOT NULL,
    description TEXT,
    value DECIMAL(10,2), 
    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context_data JSON,
    
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    INDEX idx_user_achievements (user_id, achieved_at DESC),
    INDEX idx_achievement_type (achievement_type, achieved_at DESC),
    INDEX idx_achievement_value (achievement_type, value DESC)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- System Metrics for Performance Monitoring
CREATE TABLE system_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active_sessions INT DEFAULT 0,
    error_rate DECIMAL(5,4) DEFAULT 0.0000,
    avg_response_time DECIMAL(6,3) DEFAULT 0.000,
    completion_rate DECIMAL(5,4) DEFAULT 0.0000,
    total_interactions INT DEFAULT 0,
    memory_usage_mb INT DEFAULT 0,
    cpu_usage_percent DECIMAL(5,2) DEFAULT 0.00,
    database_connections INT DEFAULT 0,
    metrics_data JSON,
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_performance (error_rate, avg_response_time),
    INDEX idx_system_health (active_sessions, completion_rate)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- System Alerts
CREATE TABLE system_alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alert_type VARCHAR(50) NOT NULL,
    severity ENUM('info', 'warning', 'error', 'critical') DEFAULT 'info',
    message TEXT NOT NULL,
    alert_value DECIMAL(10,4),
    threshold_value DECIMAL(10,4),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP NULL,
    resolved_by VARCHAR(100),
    alert_data JSON,
    
    INDEX idx_severity_time (severity, timestamp DESC),
    INDEX idx_alert_type (alert_type, resolved),
    INDEX idx_unresolved (resolved, timestamp DESC)
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

--User Interactions - Detailed interaction logging
CREATE TABLE IF NOT EXISTS user_interactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    interaction_type ENUM('click', 'submit', 'navigation', 'view', 'edit', 'download', 'upload', 'search', 'filter', 'error', 'success', 'warning') NOT NULL,
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

--Practice Sessions - Specific to Error Explorer
CREATE TABLE IF NOT EXISTS practice_sessions (
    practice_session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36),
    error_code VARCHAR(50),
    error_name VARCHAR(200),
    error_category VARCHAR(100),
    difficulty_level ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    status ENUM('setup', 'code_ready', 'review_complete', 'abandoned') DEFAULT 'setup',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    total_duration_minutes INT DEFAULT 0,
    practice_data JSON,
    performance_metrics JSON,
    
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE SET NULL,
    FOREIGN KEY (error_code) REFERENCES java_errors(error_code) ON DELETE SET NULL,
    INDEX idx_user_practice (user_id, started_at DESC),
    INDEX idx_error_practice (error_code, started_at DESC),
    INDEX idx_status_time (status, total_duration_minutes)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Workflow Tracking - Main workflow progress
CREATE TABLE IF NOT EXISTS workflow_tracking (
    workflow_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36),
    workflow_type VARCHAR(50) DEFAULT 'main_workflow',
    current_step VARCHAR(50),
    total_steps_completed INT DEFAULT 0,
    selected_categories JSON,
    selected_errors JSON,
    code_length VARCHAR(20),
    difficulty_level VARCHAR(20),
    status ENUM('in_progress', 'completed', 'abandoned') DEFAULT 'in_progress',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    final_results JSON,
    performance_data JSON,
    
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE SET NULL,
    INDEX idx_user_workflow (user_id, started_at DESC),
    INDEX idx_workflow_status (status, started_at DESC),
    INDEX idx_workflow_type (workflow_type, status)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Tab Navigation Tracking
CREATE TABLE IF NOT EXISTS tab_navigation (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    from_tab VARCHAR(50),
    to_tab VARCHAR(50) NOT NULL,
    tab_index INT,
    time_spent_on_previous_tab_seconds INT DEFAULT 0,
    navigation_trigger VARCHAR(50) DEFAULT 'click',
    context_data JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    INDEX idx_user_navigation (user_id, timestamp DESC),
    INDEX idx_tab_usage (to_tab, timestamp DESC),
    INDEX idx_session_navigation (session_id, timestamp)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Learning Path Progress
CREATE TABLE IF NOT EXISTS learning_path_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    error_category VARCHAR(100) NOT NULL,
    total_encounters INT DEFAULT 0,
    successful_identifications INT DEFAULT 0,
    average_time_to_identify_seconds INT DEFAULT 0,
    mastery_level DECIMAL(3,2) DEFAULT 0.00, 
    progress_data JSON,
    last_practice_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    UNIQUE KEY unique_user_category (user_id, error_category),
    INDEX idx_mastery (mastery_level DESC),
    INDEX idx_last_practice (last_practice_date DESC)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Error Category Statistics - User-specific category performance tracking
CREATE TABLE IF NOT EXISTS error_category_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    category VARCHAR(100) NOT NULL,
    encountered INT DEFAULT 0,
    identified INT DEFAULT 0,
    mastery_level DECIMAL(3,2) DEFAULT 0.00,
    streak_count INT DEFAULT 0,
    best_streak INT DEFAULT 0,
    last_encounter_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    UNIQUE KEY unique_user_category_stats (user_id, category),
    INDEX idx_mastery_level (mastery_level DESC),
    INDEX idx_streak (streak_count DESC)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Error usage statistics table - Enhanced version for better analytics
CREATE TABLE IF NOT EXISTS error_usage_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    error_id INT NOT NULL,
    user_id VARCHAR(36),
    session_id VARCHAR(36),
    practice_session_id VARCHAR(36) NULL,
    workflow_id VARCHAR(36) NULL,
    action_type ENUM('viewed', 'practiced', 'mastered', 'failed', 'skipped', 'reviewed') NOT NULL,
    action_result ENUM('success', 'failure', 'partial', 'timeout') DEFAULT 'success',
    time_spent_seconds INT DEFAULT 0,
    attempts_count INT DEFAULT 1,
    accuracy_score FLOAT DEFAULT 0.0,
    difficulty_perceived ENUM('easy', 'medium', 'hard') NULL,
    context_data JSON,
    device_type VARCHAR(50),
    interaction_source VARCHAR(100),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (error_id) REFERENCES java_errors(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE SET NULL,
    FOREIGN KEY (practice_session_id) REFERENCES practice_sessions(practice_session_id) ON DELETE SET NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflow_tracking(workflow_id) ON DELETE SET NULL,
    INDEX idx_error_user_enhanced (error_id, user_id, action_type),
    INDEX idx_session_enhanced (session_id, created_at),
    INDEX idx_action_type_enhanced (action_type, action_result),
    INDEX idx_performance (accuracy_score, time_spent_seconds),
    INDEX idx_timestamps (started_at, completed_at)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Error Identification Analysis
CREATE TABLE IF NOT EXISTS error_identification_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36),
    practice_session_id VARCHAR(36),
    workflow_id VARCHAR(36),
    error_code VARCHAR(50),
    review_iteration INT DEFAULT 1,
    review_text TEXT,
    identified_correctly BOOLEAN DEFAULT FALSE,
    time_to_identify_seconds INT DEFAULT 0,
    confidence_score DECIMAL(3,2), 
    hint_requests INT DEFAULT 0,
    llm_analysis_data JSON,
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE SET NULL,
    FOREIGN KEY (practice_session_id) REFERENCES practice_sessions(practice_session_id) ON DELETE SET NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflow_tracking(workflow_id) ON DELETE SET NULL,
    FOREIGN KEY (error_code) REFERENCES java_errors(error_code) ON DELETE SET NULL,
    INDEX idx_user_analysis (user_id, analysis_timestamp DESC),
    INDEX idx_error_analysis (error_code, identified_correctly),
    INDEX idx_performance (identified_correctly, time_to_identify_seconds)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;


-- =====================================================
-- Create Views for Analytics
-- =====================================================


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
    COUNT(DISTINCT ps.practice_session_id) as practice_sessions,
    AVG(ecs.mastery_level) as avg_mastery,
    (SELECT COUNT(*) FROM user_sessions WHERE user_id = u.uid) as total_sessions,
    COALESCE(SUM(us.session_duration_minutes), 0) as total_time_minutes
FROM users u
LEFT JOIN user_badges ub ON u.uid = ub.user_id
LEFT JOIN practice_sessions ps ON u.uid = ps.user_id
LEFT JOIN error_category_stats ecs ON u.uid = ecs.user_id
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
AND table_name IN ('users', 'error_categories', 'java_errors', 'badges', 'user_badges', 'activity_log', 'error_usage_stats', 
                   'user_sessions', 'user_interactions', 'practice_sessions', 'workflow_tracking', 
                   'tab_navigation', 'error_identification_analysis', 'learning_path_progress', 'system_performance_logs','badge_progress_logs', 'error_category_stats', 'learning_achievements', 'user_engagement_metrics', 'system_metrics', 'system_alerts');   

