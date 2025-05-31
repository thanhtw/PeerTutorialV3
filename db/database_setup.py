# db/database_setup.py
"""
Database setup and configuration script for Java Peer Review Training System.
This script handles the complete database initialization process.
"""

import mysql.connector
import logging
import os
import sys
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    """Handle database setup and configuration."""
    
    def __init__(self):
        """Initialize database setup with configuration."""
        # Get database configuration from environment variables with defaults
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_user = os.getenv("DB_USER", "root")  # Default to root for setup
        self.db_password = os.getenv("DB_PASSWORD", "")
        self.db_name = os.getenv("DB_NAME", "java_review_db")
        self.db_port = int(os.getenv("DB_PORT", "3306"))
        
        # Application user credentials
        self.app_user = os.getenv("APP_DB_USER", "java_review_user")
        self.app_password = os.getenv("APP_DB_PASSWORD", "Thomas123!")
        
        logger.debug(f"Database setup initialized:")
        logger.debug(f"  Host: {self.db_host}:{self.db_port}")
        logger.debug(f"  Database: {self.db_name}")
        logger.debug(f"  App User: {self.app_user}")
    
    def test_connection(self):
        """Test database connection without specifying database."""
        try:
            logger.debug("Testing database connection...")
            
            connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            
            if connection.is_connected():
                db_info = connection.get_server_info()
                logger.debug(f"Successfully connected to MySQL Server version {db_info}")
                cursor = connection.cursor()
                cursor.execute("SELECT DATABASE();")
                current_db = cursor.fetchone()
                logger.debug(f"Current database: {current_db}")
                cursor.close()
                connection.close()
                return True
            else:
                logger.error("Failed to connect to database")
                return False
                
        except mysql.connector.Error as e:
            logger.error(f"Database connection error: {str(e)}")
            logger.error(f"Error code: {e.errno}")
            logger.error(f"SQL state: {e.sqlstate}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def create_database(self):
        """Create the database if it doesn't exist."""
        try:
            logger.debug(f"Creating database '{self.db_name}' if it doesn't exist...")
            
            connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            
            cursor = connection.cursor()
            
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.debug(f"Database '{self.db_name}' created or already exists")
            
            # Switch to the database
            cursor.execute(f"USE `{self.db_name}`")
            logger.debug(f"Switched to database '{self.db_name}'")
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"Error creating database: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating database: {str(e)}")
            return False
    
    def create_application_user(self):
        """Create application user with proper permissions."""
        try:
            logger.debug(f"Creating application user '{self.app_user}'...")
            
            connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port,
                database=self.db_name,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            
            cursor = connection.cursor()
            
            # Create user if not exists
            try:
                cursor.execute(f"CREATE USER IF NOT EXISTS '{self.app_user}'@'%' IDENTIFIED BY '{self.app_password}'")
                logger.debug(f"User '{self.app_user}' created or already exists")
            except mysql.connector.Error as e:
                if e.errno == 1396:  # User already exists
                    logger.debug(f"User '{self.app_user}' already exists")
                else:
                    raise e
            
            # Grant permissions
            cursor.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER ON `{self.db_name}`.* TO '{self.app_user}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
            
            logger.debug(f"Permissions granted to user '{self.app_user}'")
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"Error creating application user: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating user: {str(e)}")
            return False
    
    def create_core_tables(self):
        """Create the core tables needed for the application."""
        try:
            logger.debug("Creating core tables...")
            
            connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port,
                database=self.db_name,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            
            cursor = connection.cursor()
            
            # Create users table
            users_table = """
            CREATE TABLE IF NOT EXISTS users (
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
                total_points INT DEFAULT 0
            ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """
            
            cursor.execute(users_table)
            logger.debug("Users table created")
            
            # Create error_categories table with enhanced structure
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_category_code (category_code),
                INDEX idx_active (is_active),
                INDEX idx_sort_order (sort_order)
            ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """
            
            cursor.execute(error_categories_table)
            logger.debug("Error categories table created")
            
            # Create java_errors table with enhanced structure
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
                INDEX idx_active (is_active),
                INDEX idx_error_name_en (error_name_en),
                INDEX idx_error_name_zh (error_name_zh)
            ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """
            
            cursor.execute(java_errors_table)
            logger.debug("Java errors table created")
            
            # Create other essential tables
            essential_tables = [
                # Activity log
                """
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
                """,
                
                # Error category stats
                """
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
                """,
                
                # Badges
                """
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
                """,
                
                # User badges
                """
                CREATE TABLE IF NOT EXISTS user_badges (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    badge_id VARCHAR(36) NOT NULL,
                    awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(uid),
                    FOREIGN KEY (badge_id) REFERENCES badges(badge_id),
                    UNIQUE KEY (user_id, badge_id)
                ) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """,
                
                # Error usage stats
                """
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
            ]
            
            for table_sql in essential_tables:
                cursor.execute(table_sql)
            
            logger.debug("All essential tables created")
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"Error creating tables: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating tables: {str(e)}")
            return False

    def migrate_json_data(self):
        """Simple data validation - data is now inserted via SQL file."""
        try:
            logger.debug("Validating inserted data...")
            
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Check if data was inserted
            cursor.execute("SELECT COUNT(*) FROM error_categories")
            categories_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM java_errors") 
            errors_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM badges")
            badges_count = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            logger.debug(f"Data validation results:")
            logger.debug(f"  Error categories: {categories_count}")
            logger.debug(f"  Java errors: {errors_count}")
            logger.debug(f"  Badges: {badges_count}")
            
            if categories_count > 0 and errors_count > 0:
                logger.debug("✅ Data insertion validation successful")
                return True
            else:
                logger.error("❌ Data validation failed - no data found")
                return False
                
        except Exception as e:
            logger.error(f"Error during data validation: {str(e)}")
            return False

    def get_connection(self):
        """Get database connection for validation."""
        return mysql.connector.connect(
            host=self.db_host,
            user=self.app_user,
            password=self.app_password,
            port=self.db_port,
            database=self.db_name,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )

    def run_complete_setup(self):
        """Run the complete database setup process."""
        logger.debug("Starting complete database setup...")
        
        try:
            # Step 1: Test basic connection
            if not self.test_connection():
                logger.error("❌ Basic database connection failed")
                return False
            
            # Step 2: Create database
            if not self.create_database():
                logger.error("❌ Database creation failed")
                return False
            
            # Step 3: Create application user
            if not self.create_application_user():
                logger.error("❌ Application user creation failed")
                return False
            
            # Step 4: Create core tables
            if not self.create_core_tables():
                logger.error("❌ Table creation failed")
                return False
            
            # Step 5: Migrate JSON data
            if not self.migrate_json_data():
                logger.error("❌ Data migration failed")
                return False
            
            # Step 6: Test application connection
            if not self.test_application_connection():
                logger.error("❌ Application user connection test failed")
                return False
            
            logger.debug("✅ Complete database setup with data migration successful!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def create_env_file(self):
        """Create or update .env file with correct database settings."""
        try:
            env_content = f"""# Database Configuration
DB_HOST={self.db_host}
DB_USER={self.app_user}
DB_PASSWORD={self.app_password}
DB_NAME={self.db_name}
DB_PORT={self.db_port}

# Admin Database Configuration (for setup only)
ADMIN_DB_USER={self.db_user}
ADMIN_DB_PASSWORD={self.db_password}

# Application Database User
APP_DB_USER={self.app_user}
APP_DB_PASSWORD={self.app_password}
"""
            
            with open('.env', 'w') as f:
                f.write(env_content)
            
            logger.debug("✅ .env file updated with database configuration")
            return True
            
        except Exception as e:
            logger.error(f"Error creating .env file: {str(e)}")
            return False

    def test_application_connection(self):
        """Test connection using application user credentials."""
        try:
            logger.debug("Testing application user connection...")
            
            connection = mysql.connector.connect(
                host=self.db_host,
                user=self.app_user,
                password=self.app_password,
                port=self.db_port,
                database=self.db_name,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            
            if connection.is_connected():
                cursor = connection.cursor()
                cursor.execute("SELECT DATABASE(), USER(), VERSION()")
                result = cursor.fetchone()
                logger.debug(f"Application connection successful: Database={result[0]}, User={result[1]}")
                cursor.close()
                connection.close()
                return True
            else:
                logger.error("Failed to connect with application user")
                return False
                
        except mysql.connector.Error as e:
            logger.error(f"Application user connection error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing application connection: {str(e)}")
            return False

def main():
    """Main setup function."""
    print("🔧 Java Peer Review Training System - Database Setup")
    print("=" * 70)
    
    # Check if MySQL is accessible
    setup = DatabaseSetup()
    
    print("\n📋 Configuration:")
    print(f"   Host: {setup.db_host}:{setup.db_port}")
    print(f"   Database: {setup.db_name}")
    print(f"   Admin User: {setup.db_user}")
    print(f"   App User: {setup.app_user}")
    
    # Ask for confirmation
    print("\n⚠️  This will create/modify:")
    print(f"   • Database: {setup.db_name}")
    print(f"   • User: {setup.app_user}")
    print("   • Core tables for the application")
    print("   • Note: Run the SQL file separately to insert data")
    
    confirm = input("\nContinue? (y/n): ")
    if confirm.lower() != 'y':
        print("Setup cancelled")
        return False
    
    # Run setup
    success = setup.run_complete_setup()
    
    if success:
        print("\n🎉 Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Run the SQL file to insert all data")
        print("2. Test: python examples/database_repository_usage.py")
        
        # Create/update .env file
        setup.create_env_file()
        
    else:
        print("\n❌ Setup failed!")
        print("Please check the logs above for error details.")
    
    return success

def verify_tables_exist():
    """Verify that all required tables exist."""
    try:
        # Use MySQLConnection instead of direct mysql.connector
        from db.mysql_connection import MySQLConnection
        db = MySQLConnection()
        
        # Test connection first
        if not db.test_connection_only():
            logger.error("Cannot connect to database for verification")
            return False
        
        required_tables = [
            'users', 'error_categories', 'java_errors', 'activity_log',
            'error_usage_stats', 'badges', 'user_badges'
        ]
        
        existing_tables = []
        missing_tables = []
        
        for table in required_tables:
            check_query = """
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = %s
            """
            result = db.execute_query(check_query, (table,), fetch_one=True)
            if result and result.get('count', 0) > 0:
                existing_tables.append(table)
            else:
                missing_tables.append(table)
        
        print(f"\n📊 Tables Status: {len(existing_tables)}/{len(required_tables)} created")
        
        if existing_tables:
            print("✅ Existing tables:")
            for table in existing_tables:
                print(f"   - {table}")
        
        if missing_tables:
            print("❌ Missing tables:")
            for table in missing_tables:
                print(f"   - {table}")
            logger.error(f"Missing tables: {', '.join(missing_tables)}")
            return False
        
        # Verify core tables have proper structure
        if 'error_categories' in existing_tables and 'java_errors' in existing_tables:
            # Check if tables have the expected columns
            cat_columns_query = """
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE table_schema = DATABASE() 
            AND table_name = 'error_categories'
            """
            cat_columns = db.execute_query(cat_columns_query)
            expected_cat_columns = ['id', 'category_code', 'name_en', 'name_zh', 'is_active']
            
            if cat_columns:
                existing_cat_cols = [col['COLUMN_NAME'] for col in cat_columns]
                missing_cols = [col for col in expected_cat_columns if col not in existing_cat_cols]
                if missing_cols:
                    logger.error(f"error_categories table missing columns: {missing_cols}")
                    return False
            
            print("✅ Table structure verification passed")
        
        logger.debug("All required tables exist and have proper structure")
        return True
            
    except Exception as e:
        logger.error(f"Error verifying tables: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)