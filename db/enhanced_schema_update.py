import logging
import json
import os
import uuid
from db.mysql_connection import MySQLConnection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_error_storage_tables():
    """Create tables specifically for storing Java error data from JSON files."""
    db = MySQLConnection()
    
    try:
        # Create error categories table with multilingual support
        error_categories_table = """
        CREATE TABLE IF NOT EXISTS error_categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category_code VARCHAR(50) NOT NULL UNIQUE,
            name_en VARCHAR(100) NOT NULL,
            name_zh VARCHAR(100) NOT NULL,
            description_en TEXT,
            description_zh TEXT,
            sort_order INT DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
        
        # Create Java errors table with full multilingual support
        java_errors_table = """
        CREATE TABLE IF NOT EXISTS java_errors (
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
            INDEX idx_active (is_active)
        ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
        
        # Create error usage statistics table
        error_usage_stats_table = """
        CREATE TABLE IF NOT EXISTS error_usage_stats (
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
            INDEX idx_action_type (action_type)
        ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
        
        db.execute_query(error_categories_table)
        db.execute_query(java_errors_table)
        db.execute_query(error_usage_stats_table)
        
        logger.debug("Error storage tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating error storage tables: {str(e)}")
        return False

def migrate_json_to_database():
    """Migrate error data from JSON files to database."""
    db = MySQLConnection()
    
    try:
        # First, create the tables
        if not create_error_storage_tables():
            logger.error("Failed to create error storage tables")
            return False
        
        # Load and migrate English data
        en_success = migrate_language_data(db, 'en')
        
        # Load and migrate Chinese data  
        zh_success = migrate_language_data(db, 'zh')
        
        if en_success or zh_success:
            logger.debug("JSON migration completed successfully")
            return True
        else:
            logger.error("Failed to migrate any JSON data")
            return False
            
    except Exception as e:
        logger.error(f"Error during JSON migration: {str(e)}")
        return False

def migrate_language_data(db, language_code):
    """Migrate data for a specific language."""
    try:
        # Determine file path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(current_dir), 'data')
        json_file = os.path.join(data_dir, f'{language_code}_Java_code_review_errors.json')
        
        if not os.path.exists(json_file):
            logger.warning(f"JSON file not found: {json_file}")
            return False
        
        # Load JSON data
        with open(json_file, 'r', encoding='utf-8') as file:
            error_data = json.load(file)
        
        logger.debug(f"Loaded {language_code} error data with {len(error_data)} categories")
        
        # Create category mapping for this language
        category_mapping = create_category_mapping(db, error_data, language_code)
        
        # Migrate errors for this language
        migrate_errors_for_language(db, error_data, category_mapping, language_code)
        
        return True
        
    except Exception as e:
        logger.error(f"Error migrating {language_code} data: {str(e)}")
        return False

def create_category_mapping(db, error_data, language_code):
    """Create or update error categories and return mapping."""
    category_mapping = {}
    
    # Define category mappings between English and Chinese
    category_translations = {
        'Logical': '邏輯錯誤',
        'Syntax': '語法錯誤', 
        'Code Quality': '程式碼品質',
        'Standard Violation': '標準違規',
        'Java Specific': 'Java 特定錯誤'
    }
    
    # Reverse mapping for Chinese to English
    reverse_translations = {v: k for k, v in category_translations.items()}
    
    sort_order = 1
    for category_name in error_data.keys():
        try:
            # Determine English and Chinese names
            if language_code == 'en':
                name_en = category_name
                name_zh = category_translations.get(category_name, category_name)
            else:
                name_zh = category_name  
                name_en = reverse_translations.get(category_name, category_name)
            
            # Create category code (standardized identifier)
            category_code = name_en.lower().replace(' ', '_')
            
            # Check if category exists
            check_query = "SELECT id FROM error_categories WHERE category_code = %s"
            result = db.execute_query(check_query, (category_code,), fetch_one=True)
            
            if result:
                category_id = result['id']
                # Update with new language data if needed
                update_query = """
                UPDATE error_categories 
                SET name_en = %s, name_zh = %s, updated_at = CURRENT_TIMESTAMP
                WHERE category_code = %s
                """
                db.execute_query(update_query, (name_en, name_zh, category_code))
            else:
                # Insert new category
                insert_query = """
                INSERT INTO error_categories (category_code, name_en, name_zh, sort_order)
                VALUES (%s, %s, %s, %s)
                """
                db.execute_query(insert_query, (category_code, name_en, name_zh, sort_order))
                
                # Get the inserted ID
                result = db.execute_query(check_query, (category_code,), fetch_one=True)
                category_id = result['id'] if result else None
            
            if category_id:
                category_mapping[category_name] = category_id
                logger.debug(f"Mapped category '{category_name}' to ID {category_id}")
            
            sort_order += 1
            
        except Exception as e:
            logger.error(f"Error processing category {category_name}: {str(e)}")
            continue
    
    return category_mapping

def migrate_errors_for_language(db, error_data, category_mapping, language_code):
    """Migrate error entries for a specific language."""
    
    # Field name mappings for different languages
    field_mappings = {
        'en': {
            'error_name': 'error_name',
            'description': 'description', 
            'implementation_guide': 'implementation_guide'
        },
        'zh': {
            'error_name': '錯誤名稱',
            'description': '描述',
            'implementation_guide': '實作範例'
        }
    }
    
    fields = field_mappings[language_code]
    errors_processed = 0
    
    for category_name, errors in error_data.items():
        category_id = category_mapping.get(category_name)
        if not category_id:
            logger.warning(f"No category ID found for {category_name}")
            continue
        
        for error in errors:
            try:
                # Extract error information
                error_name = error.get(fields['error_name'], 'Unknown Error')
                description = error.get(fields['description'], '')
                implementation_guide = error.get(fields['implementation_guide'], '')
                
                # Generate error code (unique identifier)
                error_code = generate_error_code(category_name, error_name, language_code)
                
                # Check if error already exists
                check_query = "SELECT id FROM java_errors WHERE error_code = %s"
                result = db.execute_query(check_query, (error_code,), fetch_one=True)
                
                if result:
                    # Update existing error with new language data
                    update_error_language_data(db, result['id'], error_name, description, 
                                             implementation_guide, language_code)
                else:
                    # Insert new error
                    insert_new_error(db, error_code, category_id, error_name, description,
                                    implementation_guide, language_code)
                
                errors_processed += 1
                
            except Exception as e:
                logger.error(f"Error processing error in {category_name}: {str(e)}")
                continue
    
    logger.debug(f"Processed {errors_processed} errors for language {language_code}")

def generate_error_code(category_name, error_name, language_code):
    """Generate a unique error code."""
    # Standardize category name  
    if language_code == 'zh':
        category_mappings = {
            '邏輯錯誤': 'logical',
            '語法錯誤': 'syntax',
            '程式碼品質': 'code_quality', 
            '標準違規': 'standard_violation',
            'Java 特定錯誤': 'java_specific'
        }
        category_code = category_mappings.get(category_name, category_name.lower())
    else:
        category_code = category_name.lower().replace(' ', '_')
    
    # Standardize error name
    error_code = error_name.lower().replace(' ', '_').replace('-', '_')
    error_code = ''.join(c for c in error_code if c.isalnum() or c == '_')
    
    return f"{category_code}_{error_code}"

def update_error_language_data(db, error_id, error_name, description, implementation_guide, language_code):
    """Update existing error with language-specific data."""
    if language_code == 'en':
        update_query = """
        UPDATE java_errors 
        SET error_name_en = %s, description_en = %s, implementation_guide_en = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
    else:  # zh
        update_query = """
        UPDATE java_errors 
        SET error_name_zh = %s, description_zh = %s, implementation_guide_zh = %s,
            updated_at = CURRENT_TIMESTAMP  
        WHERE id = %s
        """
    
    db.execute_query(update_query, (error_name, description, implementation_guide, error_id))

def insert_new_error(db, error_code, category_id, error_name, description, implementation_guide, language_code):
    """Insert a new error with language-specific data."""
    if language_code == 'en':
        insert_query = """
        INSERT INTO java_errors 
        (error_code, category_id, error_name_en, description_en, implementation_guide_en,
         error_name_zh, description_zh, implementation_guide_zh)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (error_code, category_id, error_name, description, implementation_guide,
                 error_name, description, implementation_guide)  # Placeholder for Chinese
    else:  # zh
        insert_query = """
        INSERT INTO java_errors 
        (error_code, category_id, error_name_en, description_en, implementation_guide_en,
         error_name_zh, description_zh, implementation_guide_zh)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (error_code, category_id, error_name, description, implementation_guide,
                 error_name, description, implementation_guide)  # Placeholder for English
    
    db.execute_query(insert_query, params)

def create_sample_data_if_missing():
    """Create sample data if no JSON files are found."""
    db = MySQLConnection()
    
    try:
        # Check if we already have data
        cat_check = db.execute_query("SELECT COUNT(*) as count FROM error_categories", fetch_one=True)
        if cat_check and cat_check['count'] > 0:
            logger.debug("Categories already exist, skipping sample data creation")
            return True
        
        logger.debug("Creating sample data...")
        
        # Insert sample categories
        sample_categories = [
            ('logical', 'Logical Errors', '邏輯錯誤', 1),
            ('syntax', 'Syntax Errors', '語法錯誤', 2),
            ('code_quality', 'Code Quality', '程式碼品質', 3),
            ('java_specific', 'Java Specific', 'Java特定錯誤', 4)
        ]
        
        for code, name_en, name_zh, order in sample_categories:
            insert_cat = """
            INSERT IGNORE INTO error_categories (category_code, name_en, name_zh, sort_order)
            VALUES (%s, %s, %s, %s)
            """
            db.execute_query(insert_cat, (code, name_en, name_zh, order))
        
        # Insert sample errors
        sample_errors = [
            ('logical_null_pointer', 1, 'Null Pointer Dereference', 
             'Accessing methods or fields of an object that might be null',
             'Always check for null before accessing object methods'),
            ('syntax_missing_semicolon', 2, 'Missing Semicolon',
             'Forgetting to terminate statements with semicolons',
             'Add semicolon (;) at the end of every statement'),
            ('code_quality_magic_numbers', 3, 'Magic Numbers',
             'Using literal numbers instead of named constants',
             'Replace magic numbers with named constants'),
            ('java_specific_raw_types', 4, 'Raw Type Usage',
             'Using raw types instead of parameterized generic types',
             'Always specify generic type parameters')
        ]
        
        for code, cat_id, name, desc, guide in sample_errors:
            insert_err = """
            INSERT IGNORE INTO java_errors 
            (error_code, category_id, error_name_en, description_en, implementation_guide_en,
             error_name_zh, description_zh, implementation_guide_zh)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            db.execute_query(insert_err, (code, cat_id, name, desc, guide, name, desc, guide))
        
        logger.debug("Sample data created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating sample data: {str(e)}")
        return False

def verify_migration():
    """Verify the migration was successful."""
    db = MySQLConnection()
    
    try:
        # Check categories
        cat_query = "SELECT COUNT(*) as count FROM error_categories"
        cat_result = db.execute_query(cat_query, fetch_one=True)
        cat_count = cat_result['count'] if cat_result else 0
        
        # Check errors
        err_query = "SELECT COUNT(*) as count FROM java_errors"
        err_result = db.execute_query(err_query, fetch_one=True)
        err_count = err_result['count'] if err_result else 0
        
        # Check errors by category
        cat_breakdown_query = """
        SELECT ec.name_en, COUNT(je.id) as error_count
        FROM error_categories ec
        LEFT JOIN java_errors je ON ec.id = je.category_id
        GROUP BY ec.id, ec.name_en
        ORDER BY ec.sort_order
        """
        breakdown = db.execute_query(cat_breakdown_query)
        
        logger.debug(f"Migration verification:")
        logger.debug(f"- Categories: {cat_count}")
        logger.debug(f"- Total errors: {err_count}")
        logger.debug(f"- Breakdown by category:")
        
        for row in breakdown or []:
            logger.debug(f"  - {row['name_en']}: {row['error_count']} errors")
        
        return cat_count > 0 and err_count > 0
        
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        return False

def run_full_migration():
    """Run the complete migration process."""
    logger.debug("Starting JSON to database migration...")
    
    try:
        # Step 1: Create tables first
        if not create_error_storage_tables():
            logger.error("Failed to create error storage tables")
            return False
        
        # Step 2: Try to migrate JSON data
        json_migrated = migrate_json_to_database()
        
        if not json_migrated:
            logger.warning("JSON migration failed, creating sample data instead")
            if not create_sample_data_if_missing():
                logger.error("Failed to create sample data")
                return False
        
        # Step 3: Populate missing translations
        populate_missing_translations()
        
        # Step 4: Verify migration
        if verify_migration():
            logger.debug("Migration completed successfully!")
            return True
        else:
            logger.error("Migration verification failed")
            return False
            
    except Exception as e:
        logger.error(f"Error during full migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_full_migration()
    if success:
        print("✅ JSON to database migration completed successfully!")
    else:
        print("❌ Migration failed. Check logs for details.")