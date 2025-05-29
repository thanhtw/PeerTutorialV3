import logging
from db.mysql_connection import MySQLConnection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database_schema():
    """Apply comprehensive schema updates to support multilingual fields, learning features, and enhanced badge system."""
    db = MySQLConnection()

    try:
        # Create core tables
        create_core_tables(db)
        
        # Create learning feature tables
        create_learning_tables(db)
        
        # Create error library tables
        create_error_library_tables(db)
        
        # Create achievement and badge tables
        create_achievement_tables(db)
        
        # Create peer learning tables
        create_peer_learning_tables(db)
        
        # Create daily challenge tables
        create_daily_challenge_tables(db)
        
        # Create code examples and preferences tables
        create_additional_tables(db)
        
        # Create indexes for performance
        create_indexes(db)
        
        # Insert default data
        insert_default_data(db)
        
        logger.info("Database schema updated successfully with all learning features")
        return True
        
    except Exception as e:
        logger.error(f"Error updating database schema: {str(e)}")
        return False

def create_core_tables(db):
    """Create core user and basic tracking tables."""
    
    # Create users table with multilingual support
    users_table = """
    CREATE TABLE IF NOT EXISTS users (
        uid VARCHAR(36) PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,       
        display_name_en VARCHAR(255),
        display_name_zh VARCHAR(255),
        password VARCHAR(255) NOT NULL,       
        level_name_en VARCHAR(50),
        level_name_zh VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviews_completed INT DEFAULT 0,
        score INT DEFAULT 0,
        last_activity DATE DEFAULT NULL,
        consecutive_days INT DEFAULT 0,
        total_points INT DEFAULT 0
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    # Create error_category_stats table
    error_category_stats_table = """
    CREATE TABLE IF NOT EXISTS error_category_stats (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        category VARCHAR(50) NOT NULL,
        encountered INT DEFAULT 0,
        identified INT DEFAULT 0,
        mastery_level FLOAT DEFAULT 0.0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(uid),
        UNIQUE KEY (user_id, category)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    # Create activity_log table for detailed point history
    activity_log_table = """
    CREATE TABLE IF NOT EXISTS activity_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        activity_type VARCHAR(50) NOT NULL,
        points INT NOT NULL,
        details_en TEXT,
        details_zh TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(uid)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    db.execute_query(users_table)
    db.execute_query(error_category_stats_table)
    db.execute_query(activity_log_table)
    logger.info("Core tables created successfully")

def create_learning_tables(db):
    """Create learning progress and tutorial tracking tables."""
    
    # Learning Progress Tracking
    learning_progress_table = """
    CREATE TABLE IF NOT EXISTS learning_progress (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        skill_category VARCHAR(50) NOT NULL,
        current_level INT DEFAULT 1,
        experience_points INT DEFAULT 0,
        mastery_percentage FLOAT DEFAULT 0.0,
        last_practiced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        practice_streak INT DEFAULT 0,
        total_practice_time INT DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(uid),
        UNIQUE KEY (user_id, skill_category)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    # Tutorial Progress
    tutorial_progress_table = """
    CREATE TABLE IF NOT EXISTS tutorial_progress (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        tutorial_step INT DEFAULT 0,
        completed_steps JSON,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP NULL,
        current_focus_error VARCHAR(100),
        attempts_count INT DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(uid),
        UNIQUE KEY (user_id)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    # Learning Hints System
    hint_usage_table = """
    CREATE TABLE IF NOT EXISTS hint_usage (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        session_id VARCHAR(36) NOT NULL,
        error_type VARCHAR(50) NOT NULL,
        hint_level INT NOT NULL,
        used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        helpful BOOLEAN NULL,
        FOREIGN KEY (user_id) REFERENCES users(uid)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    # Pattern Recognition Progress
    pattern_recognition_stats_table = """
    CREATE TABLE IF NOT EXISTS pattern_recognition_stats (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        error_pattern VARCHAR(50) NOT NULL,
        correct_identifications INT DEFAULT 0,
        total_attempts INT DEFAULT 0,
        average_time_seconds FLOAT DEFAULT 0.0,
        current_streak INT DEFAULT 0,
        best_streak INT DEFAULT 0,
        difficulty_level VARCHAR(20) DEFAULT 'beginner',
        last_practiced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(uid),
        UNIQUE KEY (user_id, error_pattern)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    # Learning Sessions
    learning_sessions_table = """
    CREATE TABLE IF NOT EXISTS learning_sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        session_type VARCHAR(50) NOT NULL,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ended_at TIMESTAMP NULL,
        duration_minutes INT DEFAULT 0,
        activities_completed INT DEFAULT 0,
        errors_encountered JSON,
        performance_score FLOAT DEFAULT 0.0,
        session_data JSON,
        FOREIGN KEY (user_id) REFERENCES users(uid)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    # AI Tutor Interactions
    ai_tutor_interactions_table = """
    CREATE TABLE IF NOT EXISTS ai_tutor_interactions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        question_text TEXT NOT NULL,
        response_text TEXT NOT NULL,
        interaction_type VARCHAR(50) NOT NULL,
        context_data JSON,
        helpful_rating INT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(uid)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    # Learning Paths
    learning_paths_table = """
    CREATE TABLE IF NOT EXISTS learning_paths (
        id INT AUTO_INCREMENT PRIMARY KEY,
        path_name VARCHAR(100) NOT NULL,
        description_en TEXT,
        description_zh TEXT,
        difficulty_level VARCHAR(20) NOT NULL, /* e.g., 'Beginner', 'Intermediate', 'Advanced' */
        estimated_hours INT DEFAULT 0,
        prerequisites JSON, /* e.g., {"completed_paths": [1, 2], "min_level": "intermediate"} */
        skills_learned JSON, /* e.g., ["NULL_POINTER", "ARRAY_INDEX_OUT_OF_BOUNDS"] */
        path_order INT DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """

    learning_path_steps_table = """
    CREATE TABLE IF NOT EXISTS learning_path_steps (
        id INT AUTO_INCREMENT PRIMARY KEY,
        path_id INT NOT NULL,
        step_order INT NOT NULL,
        title VARCHAR(255) NOT NULL,
        description_md TEXT, /* General instructions or introductory text for the step */
        step_type VARCHAR(50) NOT NULL, 
            /* Examples: 'ERROR_DETAIL_STUDY', 'PATTERN_GAME', 'GUIDED_PRACTICE', 'QUIZ', 'VIDEO', 'EXTERNAL_LINK' */
        content_reference VARCHAR(255) NULL, 
            /* Links to specific content: error_code for ERROR_DETAIL_STUDY, 
               error_type for PATTERN_GAME, exercise_id for GUIDED_PRACTICE, etc. */
        estimated_time_minutes INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (path_id) REFERENCES learning_paths(id) ON DELETE CASCADE
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    user_learning_paths_table = """
    CREATE TABLE IF NOT EXISTS user_learning_paths (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        path_id INT NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'not_started', /* e.g., 'not_started', 'in_progress', 'completed' */
        current_step_id INT NULL, /* FK to learning_path_steps.id */
        total_steps INT DEFAULT 0, /* Should be set upon enrollment based on path definition */
        progress_percentage FLOAT DEFAULT 0.0,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
        FOREIGN KEY (path_id) REFERENCES learning_paths(id) ON DELETE CASCADE,
        FOREIGN KEY (current_step_id) REFERENCES learning_path_steps(id) ON DELETE SET NULL, /* If a step is deleted, nullify here */
        UNIQUE KEY (user_id, path_id)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    # User preferences for personalized learning
    user_learning_preferences_table = """
    CREATE TABLE IF NOT EXISTS user_learning_preferences (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        learning_style VARCHAR(50),
        preferred_difficulty VARCHAR(20) DEFAULT 'adaptive',
        hint_frequency VARCHAR(20) DEFAULT 'moderate',
        practice_reminders BOOLEAN DEFAULT TRUE,
        daily_goal_minutes INT DEFAULT 30,
        preferred_categories JSON,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(uid),
        UNIQUE KEY (user_id)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    db.execute_query(learning_progress_table)
    db.execute_query(tutorial_progress_table)
    db.execute_query(hint_usage_table)
    db.execute_query(pattern_recognition_stats_table)
    db.execute_query(learning_sessions_table)
    db.execute_query(ai_tutor_interactions_table)
    db.execute_query(learning_paths_table)
    db.execute_query(learning_path_steps_table) # New call
    db.execute_query(user_learning_paths_table)
    db.execute_query(user_learning_preferences_table)
    logger.info("Learning tables created successfully")

def create_achievement_tables(db):
    """Create badge and achievement system tables."""
    
    # Achievement Categories
    achievement_categories_table = """
    CREATE TABLE IF NOT EXISTS achievement_categories (
        id INT AUTO_INCREMENT PRIMARY KEY,
        category_name VARCHAR(50) NOT NULL UNIQUE,
        description_en TEXT,
        description_zh TEXT,
        icon VARCHAR(20),
        sort_order INT DEFAULT 0
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    # Create badges table with multilingual fields and enhanced features
    badges_table = """
    CREATE TABLE IF NOT EXISTS badges (
        badge_id VARCHAR(36) PRIMARY KEY,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    # Create user_badges table
    user_badges_table = """
    CREATE TABLE IF NOT EXISTS user_badges (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        badge_id VARCHAR(36) NOT NULL,
        awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(uid),
        FOREIGN KEY (badge_id) REFERENCES badges(badge_id),
        UNIQUE KEY (user_id, badge_id)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    db.execute_query(achievement_categories_table)
    db.execute_query(badges_table)
    db.execute_query(user_badges_table)
    logger.info("Achievement tables created successfully")

def create_peer_learning_tables(db):
    """Create peer learning and review system tables."""
    
    # Peer Learning System
    peer_review_sessions_table = """
    CREATE TABLE IF NOT EXISTS peer_review_sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        session_code VARCHAR(10) NOT NULL UNIQUE,
        creator_id VARCHAR(36) NOT NULL,
        code_snippet TEXT NOT NULL,
        known_errors JSON NOT NULL,
        max_participants INT DEFAULT 4,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        FOREIGN KEY (creator_id) REFERENCES users(uid)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    peer_review_participants_table = """
    CREATE TABLE IF NOT EXISTS peer_review_participants (
        id INT AUTO_INCREMENT PRIMARY KEY,
        session_id INT NOT NULL,
        user_id VARCHAR(36) NOT NULL,
        review_text TEXT,
        submitted_at TIMESTAMP NULL,
        peer_score FLOAT DEFAULT 0.0,
        FOREIGN KEY (session_id) REFERENCES peer_review_sessions(id),
        FOREIGN KEY (user_id) REFERENCES users(uid),
        UNIQUE KEY (session_id, user_id)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    db.execute_query(peer_review_sessions_table)
    db.execute_query(peer_review_participants_table)
    logger.info("Peer learning tables created successfully")

def create_daily_challenge_tables(db):
    """Create daily challenge system tables."""
    
    # Daily Challenges
    daily_challenges_table = """
    CREATE TABLE IF NOT EXISTS daily_challenges (
        id INT AUTO_INCREMENT PRIMARY KEY,
        challenge_date DATE NOT NULL UNIQUE,
        challenge_type VARCHAR(50) NOT NULL,
        difficulty_level VARCHAR(20) NOT NULL,
        error_types JSON NOT NULL,
        description_en TEXT,
        description_zh TEXT,
        reward_points INT DEFAULT 50,
        bonus_badge VARCHAR(50) NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    user_daily_challenges_table = """
    CREATE TABLE IF NOT EXISTS user_daily_challenges (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        challenge_id INT NOT NULL,
        completed_at TIMESTAMP NULL,
        score FLOAT DEFAULT 0.0,
        attempts INT DEFAULT 0,
        bonus_earned BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (user_id) REFERENCES users(uid),
        FOREIGN KEY (challenge_id) REFERENCES daily_challenges(id),
        UNIQUE KEY (user_id, challenge_id)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    db.execute_query(daily_challenges_table)
    db.execute_query(user_daily_challenges_table)
    logger.info("Daily challenge tables created successfully")

def create_additional_tables(db):
    """Create code examples library and other additional tables."""
    
    # Code Examples Library
    code_examples_table = """
    CREATE TABLE IF NOT EXISTS code_examples (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        description_en TEXT,
        description_zh TEXT,
        code_content TEXT NOT NULL,
        error_types JSON NOT NULL,
        difficulty_level VARCHAR(20) NOT NULL,
        category VARCHAR(50) NOT NULL,
        source VARCHAR(100),
        created_by VARCHAR(36),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        usage_count INT DEFAULT 0,
        rating FLOAT DEFAULT 0.0,
        FOREIGN KEY (created_by) REFERENCES users(uid)
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    
    db.execute_query(code_examples_table)
    logger.info("Additional tables created successfully")

def create_error_library_tables(db):
    """Create tables for the error library, including detailed error information."""
    error_details_table = """
    CREATE TABLE IF NOT EXISTS error_details (
        id INT AUTO_INCREMENT PRIMARY KEY,
        error_code VARCHAR(50) NOT NULL UNIQUE,
        language VARCHAR(20) NOT NULL DEFAULT 'Java', -- Represents programming_language
        title VARCHAR(255) NOT NULL,
        detailed_description_md TEXT,
        category VARCHAR(255) NOT NULL,
        content_language VARCHAR(10) NOT NULL,
        implementation_guide_md TEXT NULL,
        suggestion_fix_md TEXT NULL,
        example_good_code_md TEXT,
        example_bad_code_md TEXT,
        before_after_comparison_md TEXT,
        common_misconceptions_md TEXT,
        importance_explanation_md TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    db.execute_query(error_details_table)
    logger.info("Error library tables created successfully")

def create_indexes(db):
    """Create indexes for performance optimization."""
    
    # Define indexes as (table_name, index_name, columns)
    indexes = [
        ("learning_progress", "idx_learning_progress_user", "user_id"),
        ("learning_progress", "idx_learning_progress_category", "skill_category"),
        ("hint_usage", "idx_hint_usage_user_session", "user_id, session_id"),
        ("pattern_recognition_stats", "idx_pattern_stats_user", "user_id"),
        ("learning_sessions", "idx_learning_sessions_user", "user_id"),
        ("ai_tutor_interactions", "idx_ai_interactions_user", "user_id"),
        ("daily_challenges", "idx_daily_challenges_date", "challenge_date"),
        ("code_examples", "idx_code_examples_category", "category, difficulty_level")
    ]
    
    for table_name, index_name, columns in indexes:
        try:
            # Check if index already exists
            check_query = """
            SELECT COUNT(*) as index_count 
            FROM information_schema.statistics 
            WHERE table_schema = DATABASE() 
            AND table_name = %s 
            AND index_name = %s
            """
            result = db.execute_query(check_query, (table_name, index_name), fetch_one=True)
            index_exists = result.get('index_count', 0) > 0 if result else False
            
            if not index_exists:
                # Create the index
                create_index_query = f"CREATE INDEX {index_name} ON {table_name}({columns})"
                db.execute_query(create_index_query)
                logger.debug(f"Created index {index_name} on {table_name}")
            else:
                logger.debug(f"Index {index_name} already exists on {table_name}")
                
        except Exception as e:
            logger.warning(f"Error creating index {index_name}: {str(e)}")
            continue
    
    logger.info("Indexes processed successfully")

def insert_default_data(db):
    """Insert default achievement categories and badges."""
    try:
        # Insert achievement categories
        categories_data = [
            ('learning_journey', 'Learning Journey', '學習旅程', 'Milestones in learning progress', '學習進度里程碑', 1),
            ('expertise', 'Expertise', '專業技能', 'Skill-based achievements', '基於技能的成就', 2),
            ('consistency', 'Consistency', '持續性', 'Regular practice achievements', '定期練習成就', 3),
            ('achievement', 'Achievement', '成就', 'Special accomplishments', '特殊成就', 4),
            ('mastery', 'Mastery', '精通', 'Subject mastery badges', '學科精通徽章', 5),
            ('volume', 'Volume', '數量', 'Volume-based achievements', '基於數量的成就', 6)
        ]
        
        for category_data in categories_data:
            check_query = "SELECT COUNT(*) as count FROM achievement_categories WHERE category_name = %s"
            result = db.execute_query(check_query, (category_data[0],), fetch_one=True)
            
            if not result or result.get('count', 0) == 0:
                insert_query = """
                INSERT INTO achievement_categories 
                (category_name, description_en, description_zh, icon, sort_order)
                VALUES (%s, %s, %s, %s, %s)
                """
                db.execute_query(insert_query, (
                    category_data[0], category_data[3], category_data[4], 
                    '🏆', category_data[5]
                ))
        
        # Insert default badges
        badges_data = [
            ('badge_first_review', 'First Review', '第一次審查', 
             'Complete your first code review successfully', '成功完成你的第一次代碼審查',
             '🎯', 'milestone', 'easy', 10, '{"reviews_completed": 1}'),
            ('badge_syntax_master', 'Syntax Master', '語法大師',
             'Identify 10 syntax errors correctly', '正確識別10個語法錯誤',
             '📝', 'expertise', 'medium', 25, '{"syntax_errors_found": 10}'),
            ('badge_logic_detective', 'Logic Detective', '邏輯偵探',
             'Successfully find 5 logical errors in code', '成功在代碼中找到5個邏輯錯誤',
             '🔍', 'expertise', 'medium', 30, '{"logical_errors_found": 5}')
        ]
        
        for badge_data in badges_data:
            check_query = "SELECT COUNT(*) as count FROM badges WHERE badge_id = %s"
            result = db.execute_query(check_query, (badge_data[0],), fetch_one=True)
            
            if not result or result.get('count', 0) == 0:
                insert_query = """
                INSERT INTO badges 
                (badge_id, name_en, name_zh, description_en, description_zh, 
                 icon, category, difficulty, points, unlock_criteria)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                db.execute_query(insert_query, badge_data)
        
        logger.info("Default data inserted successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error inserting default data: {str(e)}")
        return False

if __name__ == "__main__":
    success = update_database_schema()
    if success:
        print("✅ Database schema updated successfully!")
    else:
        print("❌ Schema update failed. Check logs for details.")