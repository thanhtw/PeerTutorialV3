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
        total_points INT DEFAULT 0,
        tutorial_completed BOOLEAN DEFAULT FALSE        
    )
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
    )
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
    )
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
    )
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
    )
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
    )
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
    )
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
    )
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
    )
    """
    
    # Learning Paths
    learning_paths_table = """
    CREATE TABLE IF NOT EXISTS learning_paths (
        id INT AUTO_INCREMENT PRIMARY KEY,
        path_name VARCHAR(100) NOT NULL,
        description_en TEXT,
        description_zh TEXT,
        difficulty_level VARCHAR(20) NOT NULL,
        estimated_hours INT DEFAULT 0,
        prerequisites JSON,
        skills_learned JSON,
        path_order INT DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE
    )
    """
    
    user_learning_paths_table = """
    CREATE TABLE IF NOT EXISTS user_learning_paths (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        path_id INT NOT NULL,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP NULL,
        current_step INT DEFAULT 0,
        total_steps INT DEFAULT 0,
        progress_percentage FLOAT DEFAULT 0.0,
        FOREIGN KEY (user_id) REFERENCES users(uid),
        FOREIGN KEY (path_id) REFERENCES learning_paths(id),
        UNIQUE KEY (user_id, path_id)
    )
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
    )
    """
    
    db.execute_query(learning_progress_table)
    db.execute_query(tutorial_progress_table)
    db.execute_query(hint_usage_table)
    db.execute_query(pattern_recognition_stats_table)
    db.execute_query(learning_sessions_table)
    db.execute_query(ai_tutor_interactions_table)
    db.execute_query(learning_paths_table)
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
    )
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
    )
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
    )
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
    )
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
    )
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
    )
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
    )
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
    )
    """
    
    db.execute_query(code_examples_table)
    logger.info("Additional tables created successfully")

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
    
    # Insert achievement categories
    insert_achievement_categories(db)
    
    # Insert default badges
    insert_default_badges(db)

def insert_achievement_categories(db):
    """Insert default achievement categories."""
    
    # Check if categories already exist
    count_query = "SELECT COUNT(*) as category_count FROM achievement_categories"
    result = db.execute_query(count_query, fetch_one=True)
    category_count = result.get('category_count', 0) if result else 0
    
    if category_count > 0:
        logger.debug(f"Achievement categories already exist ({category_count} found). Skipping insertion.")
        return
    
    categories = [
        ('learning_journey', 'Progress through learning stages', '通過學習階段的進展', '🎓', 1),
        ('skill_mastery', 'Master specific error types', '掌握特定錯誤類型', '🎯', 2),
        ('social', 'Community engagement and helping others', '社區參與和幫助他人', '🤝', 3),
        ('special', 'Unique achievements and milestones', '獨特成就和里程碑', '⭐', 4)
    ]
    
    for category_name, desc_en, desc_zh, icon, sort_order in categories:
        try:
            insert_query = """
            INSERT INTO achievement_categories (category_name, description_en, description_zh, icon, sort_order)
            VALUES (%s, %s, %s, %s, %s)
            """
            db.execute_query(insert_query, (category_name, desc_en, desc_zh, icon, sort_order))
        except Exception as e:
            logger.warning(f"Error inserting achievement category {category_name}: {str(e)}")
    
    logger.info("Achievement categories inserted successfully")

def insert_default_badges(db):
    """Insert default badges into the badges table with multilingual support."""
    
    # Check if badges already exist
    count_query = "SELECT COUNT(*) as badge_count FROM badges"
    result = db.execute_query(count_query, fetch_one=True)
    badge_count = result.get('badge_count', 0) if result else 0
    
    if badge_count > 0:
        logger.debug(f"Badges already exist in the database ({badge_count} found). Skipping insertion.")
        return
    
    # Define default badges with English and Chinese translations
    default_badges = [
        # Achievement badges
        ("bug-hunter", "Bug Hunter", "錯誤獵人", "Found all errors in at least 5 reviews", "在至少 5 次審查中找到所有錯誤", "🐞", "achievement", "medium", 50, "skill_mastery", "common"),
        ("perfectionist", "Perfectionist", "完美主義者", "Achieved 100% accuracy in 3 consecutive reviews", "連續 3 次審查達到 100% 準確度", "✨", "achievement", "hard", 100, "skill_mastery", "rare"),
        ("quick-eye", "Quick Eye", "敏銳之眼", "Found a Hard difficulty error in under 2 minutes", "2 分鐘內發現困難等級錯誤", "👁️", "achievement", "medium", 30, "skill_mastery", "common"),
        ("consistency-champ", "Consistency Champion", "持續冠軍", "Completed reviews on 5 consecutive days", "連續 5 天完成審查", "🏆", "achievement", "medium", 50, "learning_journey", "common"),
        ("reviewer-novice", "Reviewer Novice", "審查新手", "Completed 5 code reviews", "完成 5 次代碼審查", "🔰", "progression", "easy", 10, "learning_journey", "common"),
        ("reviewer-adept", "Reviewer Adept", "審查熟手", "Completed 25 code reviews", "完成 25 次代碼審查", "🥈", "progression", "medium", 30, "learning_journey", "common"),
        ("reviewer-master", "Reviewer Master", "審查大師", "Completed 50 code reviews", "完成 50 次代碼審查", "🥇", "progression", "hard", 100, "learning_journey", "rare"),
        
        # Error category badges
        ("syntax-specialist", "Syntax Specialist", "語法專家", "Mastered Syntax error identification", "掌握語法錯誤識別", "📝", "category", "medium", 40, "skill_mastery", "common"),
        ("logic-guru", "Logic Guru", "邏輯大師", "Mastered Logical error identification", "掌握邏輯錯誤識別", "🧠", "category", "medium", 40, "skill_mastery", "common"),
        ("quality-inspector", "Quality Inspector", "品質檢查員", "Mastered Code Quality error identification", "掌握程式碼品質錯誤識別", "🔍", "category", "medium", 40, "skill_mastery", "common"),
        ("standards-expert", "Standards Expert", "標準專家", "Mastered Standard Violation identification", "掌握標準違規識別", "📏", "category", "medium", 40, "skill_mastery", "common"),
        ("java-maven", "Java Maven", "Java 專家", "Mastered Java Specific error identification", "掌握 Java 特定錯誤識別", "☕", "category", "medium", 40, "skill_mastery", "common"),
        
        # Special badges
        ("full-spectrum", "Full Spectrum", "全方位", "Identified at least one error in each category", "在每個類別中至少識別一個錯誤", "🌈", "special", "hard", 75, "special", "rare"),
        ("rising-star", "Rising Star", "冉冉新星", "Earned 500 points in your first week", "在第一週內獲得 500 點", "⭐", "special", "hard", 100, "special", "epic"),
        ("tutorial-master", "Tutorial Master", "教學大師", "Completed the interactive tutorial", "完成互動教學", "🎓", "tutorial", "easy", 25, "learning_journey", "common")
    ]
    
    # Insert each badge with error handling
    successfully_inserted = 0
    for badge_id, name_en, name_zh, desc_en, desc_zh, icon, category, difficulty, points, achievement_category, rarity in default_badges:
        try:
            # Check if this specific badge already exists
            check_query = "SELECT COUNT(*) as exists_count FROM badges WHERE badge_id = %s"
            result = db.execute_query(check_query, (badge_id,), fetch_one=True)
            badge_exists = result.get('exists_count', 0) > 0 if result else False
            
            if badge_exists:
                logger.debug(f"Badge {badge_id} already exists, skipping insertion")
                continue
                
            # Insert the badge with multilingual fields and enhanced features
            insert_query = """
            INSERT INTO badges (badge_id, name_en, name_zh, description_en, description_zh, icon, category, difficulty, points, achievement_category, rarity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            db.execute_query(insert_query, (badge_id, name_en, name_zh, desc_en, desc_zh, icon, category, difficulty, points, achievement_category, rarity))
            successfully_inserted += 1
            
        except Exception as e:
            logger.warning(f"Error inserting badge {badge_id}: {str(e)}")
            continue
    
    logger.info(f"Inserted {successfully_inserted} enhanced multilingual badges")

if __name__ == "__main__":
    success = update_database_schema()
    if success:
        print("Database schema updated successfully!")
    else:
        print("Failed to update database schema. Check logs for details.")