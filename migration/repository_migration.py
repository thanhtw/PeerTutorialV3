# migration/repository_migration.py
"""
Migration script to update the system from JSON-based to database-based error repository.

This script handles:
1. Running database migration
2. Updating import statements
3. Testing the new repository
4. Providing rollback options
"""

import os
import sys
import logging
import shutil
from datetime import datetime
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from db.enhanced_schema_update import run_full_migration
from data.database_error_repository import DatabaseErrorRepository
from data.json_error_repository import JsonErrorRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RepositoryMigration:
    """Handle the migration from JSON to database repository."""
    
    def __init__(self):
        self.project_root = project_root
        self.backup_dir = self.project_root / "backup" / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.files_to_update = []
        
    def run_migration(self):
        """Run the complete migration process."""
        try:
            logger.info("Starting repository migration process...")
            
            # Step 1: Create backup
            self.create_backup()
            
            # Step 2: Run database migration
            if not self.migrate_database():
                logger.error("Database migration failed")
                return False
            
            # Step 3: Test new repository
            if not self.test_new_repository():
                logger.error("New repository testing failed")
                return False
            
            # Step 4: Update code files
            self.update_import_statements()
            
            # Step 5: Create adapter for backward compatibility
            self.create_compatibility_adapter()
            
            # Step 6: Final validation
            if not self.validate_migration():
                logger.error("Migration validation failed")
                return False
            
            logger.info("Repository migration completed successfully!")
            logger.info(f"Backup created at: {self.backup_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return False
    
    def create_backup(self):
        """Create backup of important files before migration."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Files to backup
            backup_files = [
                "data/json_error_repository.py",
                "data/__init__.py",
                "db/schema_update.py"
            ]
            
            for file_path in backup_files:
                source = self.project_root / file_path
                if source.exists():
                    dest = self.backup_dir / file_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
                    logger.info(f"Backed up: {file_path}")
            
            logger.info(f"Backup completed in: {self.backup_dir}")
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            raise
    
    def migrate_database(self):
        """Run the database migration."""
        try:
            logger.info("Running database migration...")
            return run_full_migration()
            
        except Exception as e:
            logger.error(f"Database migration error: {str(e)}")
            return False
    
    def test_new_repository(self):
        """Test the new database repository."""
        try:
            logger.info("Testing new database repository...")
            
            # Create repository instance
            db_repo = DatabaseErrorRepository()
            
            # Test basic functionality
            categories = db_repo.get_all_categories()
            if not categories or not categories.get("java_errors"):
                logger.error("No categories found in database repository")
                return False
            
            # Test getting errors for a category
            first_category = categories["java_errors"][0]
            errors = db_repo.get_category_errors(first_category)
            
            if not errors:
                logger.warning(f"No errors found for category: {first_category}")
            
            # Test random error selection
            random_errors = db_repo.get_random_errors_by_categories({"java_errors": [first_category]}, count=2)
            
            logger.info(f"Database repository test passed:")
            logger.info(f"- Categories: {len(categories['java_errors'])}")
            logger.info(f"- Errors in '{first_category}': {len(errors)}")
            logger.info(f"- Random errors selected: {len(random_errors)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Repository testing failed: {str(e)}")
            return False
    
    def update_import_statements(self):
        """Update import statements in code files."""
        try:
            logger.info("Updating import statements...")
            
            # Find files that import JsonErrorRepository
            import_files = self.find_files_with_imports()
            
            for file_path in import_files:
                self.update_file_imports(file_path)
            
            logger.info(f"Updated imports in {len(import_files)} files")
            
        except Exception as e:
            logger.error(f"Import update failed: {str(e)}")
    
    def find_files_with_imports(self):
        """Find Python files that import JsonErrorRepository."""
        import_files = []
        
        # Search in common directories
        search_dirs = [".", "auth", "data", "utils", "web"]
        
        for search_dir in search_dirs:
            dir_path = self.project_root / search_dir
            if not dir_path.exists():
                continue
                
            for file_path in dir_path.rglob("*.py"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if "JsonErrorRepository" in content:
                        import_files.append(file_path)
                        logger.debug(f"Found import in: {file_path}")
                        
                except Exception as e:
                    logger.warning(f"Error reading {file_path}: {str(e)}")
                    continue
        
        return import_files
    
    def update_file_imports(self, file_path):
        """Update imports in a specific file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create updated content
            updated_content = content
            
            # Replace import statements
            replacements = [
                ("from data.json_error_repository import JsonErrorRepository", 
                 "from data.database_error_repository import DatabaseErrorRepository"),
                ("JsonErrorRepository()", "DatabaseErrorRepository()"),
                ("JsonErrorRepository", "DatabaseErrorRepository")
            ]
            
            for old, new in replacements:
                if old in updated_content:
                    updated_content = updated_content.replace(old, new)
                    logger.debug(f"Replaced '{old}' with '{new}' in {file_path}")
            
            # Write updated content
            if updated_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                logger.info(f"Updated imports in: {file_path}")
                
        except Exception as e:
            logger.error(f"Error updating {file_path}: {str(e)}")
    
    def create_compatibility_adapter(self):
        """Create an adapter to maintain backward compatibility."""
        try:
            adapter_content = '''# data/error_repository_adapter.py
"""
Compatibility adapter for the error repository migration.

This adapter allows existing code to continue working while 
transitioning from JSON to database-based repository.
"""

import logging
from data.database_error_repository import DatabaseErrorRepository

logger = logging.getLogger(__name__)

class JsonErrorRepository:
    """
    Compatibility adapter that wraps DatabaseErrorRepository
    to maintain backward compatibility with JsonErrorRepository interface.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with DatabaseErrorRepository."""
        logger.info("Using compatibility adapter - JsonErrorRepository -> DatabaseErrorRepository")
        self._repo = DatabaseErrorRepository()
        
        # Maintain compatibility with old constructor parameters
        if args or kwargs:
            logger.warning("JsonErrorRepository constructor parameters are ignored in database mode")
    
    def __getattr__(self, name):
        """Delegate all method calls to DatabaseErrorRepository."""
        return getattr(self._repo, name)
    
    # Explicitly define key methods for better IDE support
    def get_all_categories(self):
        return self._repo.get_all_categories()
    
    def get_category_errors(self, category_name):
        return self._repo.get_category_errors(category_name)
    
    def get_errors_by_categories(self, selected_categories):
        return self._repo.get_errors_by_categories(selected_categories)
    
    def get_error_details(self, error_type, error_name):
        return self._repo.get_error_details(error_type, error_name)
    
    def get_random_errors_by_categories(self, selected_categories, count=4):
        return self._repo.get_random_errors_by_categories(selected_categories, count)
    
    def get_errors_for_llm(self, selected_categories=None, specific_errors=None, count=4, difficulty="medium"):
        return self._repo.get_errors_for_llm(selected_categories, specific_errors, count, difficulty)
    
    def get_error_by_name(self, error_type, error_name):
        return self._repo.get_error_by_name(error_type, error_name)
'''
            
            adapter_path = self.project_root / "data" / "error_repository_adapter.py"
            with open(adapter_path, 'w', encoding='utf-8') as f:
                f.write(adapter_content)
            
            logger.info("Created compatibility adapter")
            
        except Exception as e:
            logger.error(f"Error creating adapter: {str(e)}")
    
    def validate_migration(self):
        """Validate that the migration was successful."""
        try:
            logger.info("Validating migration...")
            
            # Test both old and new interfaces
            from data.database_error_repository import DatabaseErrorRepository
            
            # Test direct database repository
            db_repo = DatabaseErrorRepository()
            categories = db_repo.get_all_categories()
            
            if not categories or not categories.get("java_errors"):
                logger.error("Database repository validation failed")
                return False
            
            # Test that we can still import from the updated locations
            try:
                # This should work after import updates
                from data.database_error_repository import DatabaseErrorRepository as UpdatedRepo
                updated_repo = UpdatedRepo()
                updated_categories = updated_repo.get_all_categories()
                
                if categories != updated_categories:
                    logger.error("Repository results inconsistent")
                    return False
                    
            except ImportError as e:
                logger.error(f"Import validation failed: {str(e)}")
                return False
            
            logger.info("Migration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return False
    
    def rollback_migration(self):
        """Rollback the migration if needed."""
        try:
            logger.info("Rolling back migration...")
            
            if not self.backup_dir.exists():
                logger.error("No backup found for rollback")
                return False
            
            # Restore backed up files
            for backup_file in self.backup_dir.rglob("*.py"):
                relative_path = backup_file.relative_to(self.backup_dir)
                target_path = self.project_root / relative_path
                
                # Create directories if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Restore file
                shutil.copy2(backup_file, target_path)
                logger.info(f"Restored: {relative_path}")
            
            logger.info("Rollback completed")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False

def run_migration():
    """Run the complete migration process."""
    migration = RepositoryMigration()
    
    try:
        success = migration.run_migration()
        
        if success:
            print("✅ Migration completed successfully!")
            print("\nNext steps:")
            print("1. Test your application thoroughly")
            print("2. Update any remaining manual references to JsonErrorRepository")
            print("3. Consider removing JSON files after confirming everything works")
            print(f"4. Backup is available at: {migration.backup_dir}")
        else:
            print("❌ Migration failed!")
            rollback = input("Would you like to rollback? (y/n): ")
            if rollback.lower() == 'y':
                migration.rollback_migration()
                print("Rollback completed")
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️ Migration interrupted by user")
        rollback = input("Would you like to rollback? (y/n): ")
        if rollback.lower() == 'y':
            migration.rollback_migration()
        return False
    except Exception as e:
        print(f"❌ Migration failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔄 Starting Repository Migration...")
    print("This will migrate from JSON-based to database-based error repository")
    print()
    
    confirm = input("Do you want to continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Migration cancelled")
        sys.exit(0)
    
    success = run_migration()
    sys.exit(0 if success else 1)