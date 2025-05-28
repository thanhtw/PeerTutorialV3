# data/database_error_repository.py
"""
Database Error Repository module for Java Peer Review Training System.

This module provides access to error data from the database,
replacing the JSON file-based approach for better performance and maintainability.
"""

import logging
import random
from typing import Dict, List, Any, Optional, Set, Union, Tuple
from db.mysql_connection import MySQLConnection
from utils.language_utils import get_current_language, t

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseErrorRepository:
    """
    Repository for accessing Java error data from the database.
    
    This class handles loading, categorizing, and providing access to
    error data stored in the database tables.
    """
    
    def __init__(self):
        """Initialize the Database Error Repository."""
        self.db = MySQLConnection()
        self.current_language = get_current_language()
        
        # Cache for frequently accessed data
        self._categories_cache = None
        self._cache_timestamp = None
        
        # Verify database connection and tables
        self._verify_database_setup()
    
    def _verify_database_setup(self):
        """Verify that the required database tables exist."""
        try:
            # Check if error_categories table exists
            check_query = """
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'error_categories'
            """
            result = self.db.execute_query(check_query, fetch_one=True)
            
            if not result or result.get('count', 0) == 0:
                logger.error("Error categories table not found. Please run migration first.")
                raise Exception("Database tables not initialized. Run enhanced_schema_update.py first.")
            
            # Check if java_errors table exists
            check_query = """
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'java_errors'
            """
            result = self.db.execute_query(check_query, fetch_one=True)
            
            if not result or result.get('count', 0) == 0:
                logger.error("Java errors table not found. Please run migration first.")
                raise Exception("Database tables not initialized. Run enhanced_schema_update.py first.")
                
            logger.debug("Database tables verified successfully")
            
        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            raise
    
    def _get_language_fields(self, base_field: str) -> str:
        """Get the appropriate language field name."""
        if self.current_language == 'zh':
            return f"{base_field}_zh"
        else:
            return f"{base_field}_en"
    
    def _invalidate_cache(self):
        """Invalidate the categories cache."""
        self._categories_cache = None
        self._cache_timestamp = None
    
    def get_all_categories(self) -> Dict[str, List[str]]:
        """
        Get all error categories.
        
        Returns:
            Dictionary with 'java_errors' categories
        """
        try:
            self.current_language = get_current_language()
            name_field = self._get_language_fields('name')
            
            query = f"""
            SELECT category_code, {name_field} as name
            FROM error_categories 
            WHERE is_active = TRUE
            ORDER BY sort_order
            """
            
            categories = self.db.execute_query(query)
            
            if categories:
                category_names = [cat['name'] for cat in categories]
                return {"java_errors": category_names}
            else:
                logger.warning("No categories found in database")
                return {"java_errors": []}
                
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return {"java_errors": []}
    
    def get_category_errors(self, category_name: str) -> List[Dict[str, str]]:
        """
        Get errors for a specific category.
        
        Args:
            category_name: Name of the category
            
        Returns:
            List of error dictionaries for the category
        """
        try:
            self.current_language = get_current_language()
            
            # Get field names based on language
            name_field = self._get_language_fields('error_name')
            desc_field = self._get_language_fields('description')
            guide_field = self._get_language_fields('implementation_guide')
            
            # First, find the category by name in current language
            cat_name_field = self._get_language_fields('name')
            category_query = f"""
            SELECT id, category_code 
            FROM error_categories 
            WHERE {cat_name_field} = %s AND is_active = TRUE
            """
            
            category = self.db.execute_query(category_query, (category_name,), fetch_one=True)
            
            if not category:
                logger.warning(f"Category not found: {category_name}")
                return []
            
            # Get errors for this category
            errors_query = f"""
            SELECT 
                {name_field} as error_name,
                {desc_field} as description,
                {guide_field} as implementation_guide,
                difficulty_level,
                error_code
            FROM java_errors 
            WHERE category_id = %s AND is_active = TRUE
            ORDER BY error_name_en
            """
            
            errors = self.db.execute_query(errors_query, (category['id'],))
            
            # Format the results to match the expected JSON structure
            formatted_errors = []
            for error in errors or []:
                formatted_errors.append({
                    t("error_name"): error['error_name'],
                    t("description"): error['description'],
                    t("implementation_guide"): error.get('implementation_guide', ''),
                    "difficulty_level": error.get('difficulty_level', 'medium'),
                    "error_code": error.get('error_code', '')
                })
            
            return formatted_errors
            
        except Exception as e:
            logger.error(f"Error getting category errors for {category_name}: {str(e)}")
            return []
    
    def get_errors_by_categories(self, selected_categories: Dict[str, List[str]]) -> Dict[str, List[Dict[str, str]]]:
        """
        Get errors for selected categories.
        
        Args:
            selected_categories: Dictionary with 'java_errors' key
                              containing a list of selected categories
            
        Returns:
            Dictionary with selected errors by category type
        """
        selected_errors = {"java_errors": []}
        
        if "java_errors" in selected_categories:
            for category in selected_categories["java_errors"]:
                category_errors = self.get_category_errors(category)
                selected_errors["java_errors"].extend(category_errors)
        
        return selected_errors
    
    def get_error_details(self, error_type: str, error_name: str) -> Optional[Dict[str, str]]:
        """
        Get details for a specific error.
        
        Args:
            error_type: Type of error ('java_error')
            error_name: Name of the error
            
        Returns:
            Error details dictionary or None if not found
        """
        if error_type != "java_error":
            return None
        
        try:
            self.current_language = get_current_language()
            
            name_field = self._get_language_fields('error_name')
            desc_field = self._get_language_fields('description')
            guide_field = self._get_language_fields('implementation_guide')
            
            query = f"""
            SELECT 
                {name_field} as error_name,
                {desc_field} as description,
                {guide_field} as implementation_guide,
                difficulty_level,
                error_code
            FROM java_errors 
            WHERE {name_field} = %s AND is_active = TRUE
            """
            
            error = self.db.execute_query(query, (error_name,), fetch_one=True)
            
            if error:
                return {
                    t("error_name"): error['error_name'],
                    t("description"): error['description'],
                    t("implementation_guide"): error.get('implementation_guide', ''),
                    "difficulty_level": error.get('difficulty_level', 'medium'),
                    "error_code": error.get('error_code', '')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting error details for {error_name}: {str(e)}")
            return None
    
    def get_random_errors_by_categories(self, selected_categories: Dict[str, List[str]], 
                                      count: int = 4) -> List[Dict[str, Any]]:
        """
        Get random errors from selected categories.
        
        Args:
            selected_categories: Dictionary with 'java_errors' key
                            containing a list of selected categories
            count: Number of errors to select
            
        Returns:
            List of selected errors with type and category information
        """
        try:
            self.current_language = get_current_language()
            
            java_error_categories = selected_categories.get("java_errors", [])
            if not java_error_categories:
                return []
            
            # Get field names based on language
            name_field = self._get_language_fields('error_name')
            desc_field = self._get_language_fields('description')
            guide_field = self._get_language_fields('implementation_guide')
            cat_name_field = self._get_language_fields('name')
            
            # Build query to get random errors from selected categories
            placeholders = ','.join(['%s'] * len(java_error_categories))
            
            query = f"""
            SELECT 
                je.{name_field} as error_name,
                je.{desc_field} as description,
                je.{guide_field} as implementation_guide,
                je.difficulty_level,
                je.error_code,
                ec.{cat_name_field} as category_name
            FROM java_errors je
            JOIN error_categories ec ON je.category_id = ec.id
            WHERE ec.{cat_name_field} IN ({placeholders}) 
            AND je.is_active = TRUE AND ec.is_active = TRUE
            ORDER BY RAND()
            LIMIT %s
            """
            
            params = tuple(java_error_categories) + (count,)
            errors = self.db.execute_query(query, params)
            
            # Format results
            formatted_errors = []
            for error in errors or []:
                formatted_errors.append({
                    "type": "java_error",
                    "category": error['category_name'],
                    "name": error['error_name'],
                    "description": error['description'],
                    "implementation_guide": error.get('implementation_guide', ''),
                    "difficulty_level": error.get('difficulty_level', 'medium'),
                    "error_code": error.get('error_code', '')
                })
            
            return formatted_errors
            
        except Exception as e:
            logger.error(f"Error getting random errors: {str(e)}")
            return []
    
    def get_errors_for_llm(self, 
                          selected_categories: Dict[str, List[str]] = None, 
                          specific_errors: List[Dict[str, Any]] = None,
                          count: int = 4, 
                          difficulty: str = "medium") -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Get errors suitable for sending to the LLM for code generation.
        Can use either category-based selection or specific errors.
        
        Args:
            selected_categories: Dictionary with selected error categories
            specific_errors: List of specific errors to include
            count: Number of errors to select if using categories
            difficulty: Difficulty level to adjust error count
            
        Returns:
            Tuple of (list of error objects, list of problem descriptions)
        """
        # Adjust count based on difficulty
        error_counts = {
            t("easy"): max(2, count - 2),
            t("medium"): count,
            t("hard"): count + 2
        }
        
        adjusted_count = error_counts.get(difficulty.lower(), count)
        
        # If specific errors are provided, use those
        if specific_errors and len(specific_errors) > 0:
            problem_descriptions = []
            selected_errors = []
            
            for error in specific_errors:
                processed_error = error.copy()
                name = processed_error.get(t("error_name_variable"), processed_error.get("name", "Unknown"))
                description = processed_error.get(t("description"), "")
                category = processed_error.get(t("category"), "")
                
                # Add implementation guide if available
                implementation_guide = self._get_implementation_guide(name, category)
                if implementation_guide:
                    processed_error[t("implementation_guide")] = implementation_guide
                
                # Create problem description
                problem_descriptions.append(f"{category}: {name} - {description}")
                selected_errors.append(processed_error)
            
            return selected_errors, problem_descriptions
        
        # Otherwise use category-based selection
        elif selected_categories:
            try:
                self.current_language = get_current_language()
                
                java_error_categories = selected_categories.get("java_errors", [])
                if not java_error_categories:
                    logger.warning("No categories specified, using defaults")
                    selected_categories = {"java_errors": ["Logical", "Syntax", "Code Quality"]}
                    java_error_categories = selected_categories["java_errors"]
                
                # Get field names
                name_field = self._get_language_fields('error_name')
                desc_field = self._get_language_fields('description')
                guide_field = self._get_language_fields('implementation_guide')
                cat_name_field = self._get_language_fields('name')
                
                # Determine selection range based on difficulty
                error_selection_ranges = {
                    t("easy"): (1, 2),
                    t("medium"): (1, 3),
                    t("hard"): (1, 4)
                }
                
                min_errors, max_errors = error_selection_ranges.get(difficulty.lower(), (1, 2))
                
                all_errors = []
                
                # Get errors from each category
                for category in java_error_categories:
                    category_query = f"""
                    SELECT 
                        je.{name_field} as error_name,
                        je.{desc_field} as description,
                        je.{guide_field} as implementation_guide,
                        ec.{cat_name_field} as category_name
                    FROM java_errors je
                    JOIN error_categories ec ON je.category_id = ec.id
                    WHERE ec.{cat_name_field} = %s 
                    AND je.is_active = TRUE AND ec.is_active = TRUE
                    ORDER BY RAND()
                    LIMIT %s
                    """
                    
                    num_to_select = random.randint(min_errors, max_errors)
                    category_errors = self.db.execute_query(category_query, (category, num_to_select))
                    
                    for error in category_errors or []:
                        all_errors.append({
                            t("category"): error['category_name'],
                            t("error_name_variable"): error['error_name'],
                            t("description"): error['description'],
                            t("implementation_guide"): error.get('implementation_guide', '')
                        })
                
                # Select final errors
                if len(all_errors) > adjusted_count:
                    selected_errors = random.sample(all_errors, adjusted_count)
                else:
                    selected_errors = all_errors
                
                # Format problem descriptions
                problem_descriptions = []
                for error in selected_errors:
                    category = error.get(t("category"), "")
                    name = error.get(t("error_name_variable"), "Unknown")
                    description = error.get(t("description"), "")
                    problem_descriptions.append(f"{category} - {name}: {description}")
                
                return selected_errors, problem_descriptions
                
            except Exception as e:
                logger.error(f"Error getting errors for LLM: {str(e)}")
                return [], []
        
        # If no selection method was provided, return empty lists
        logger.warning("No selection method provided, returning empty error list")
        return [], []
    
    def _get_implementation_guide(self, error_name: str, category: str) -> Optional[str]:
        """
        Get implementation guide for a specific error.
        
        Args:
            error_name: Name of the error
            category: Category of the error
            
        Returns:
            Implementation guide string or None if not found
        """
        try:
            self.current_language = get_current_language()
            
            name_field = self._get_language_fields('error_name')
            guide_field = self._get_language_fields('implementation_guide')
            cat_name_field = self._get_language_fields('name')
            
            query = f"""
            SELECT je.{guide_field} as implementation_guide
            FROM java_errors je
            JOIN error_categories ec ON je.category_id = ec.id
            WHERE je.{name_field} = %s AND ec.{cat_name_field} = %s
            AND je.is_active = TRUE AND ec.is_active = TRUE
            """
            
            result = self.db.execute_query(query, (error_name, category), fetch_one=True)
            
            if result:
                return result.get('implementation_guide')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting implementation guide: {str(e)}")
            return None
    
    def get_error_by_name(self, error_type: str, error_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific error by name.
        
        Args:
            error_type: Type of error ('java_error')
            error_name: Name of the error
            
        Returns:
            Error dictionary with added type and category, or None if not found
        """
        if error_type != "java_error":
            return None
        
        try:
            self.current_language = get_current_language()
            
            name_field = self._get_language_fields('error_name')
            desc_field = self._get_language_fields('description')
            cat_name_field = self._get_language_fields('name')
            
            query = f"""
            SELECT 
                je.{name_field} as error_name,
                je.{desc_field} as description,
                ec.{cat_name_field} as category_name
            FROM java_errors je
            JOIN error_categories ec ON je.category_id = ec.id
            WHERE je.{name_field} = %s 
            AND je.is_active = TRUE AND ec.is_active = TRUE
            """
            
            result = self.db.execute_query(query, (error_name,), fetch_one=True)
            
            if result:
                return {
                    t("category"): result['category_name'],
                    t("error_name_variable"): result['error_name'],
                    t("description"): result['description']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting error by name {error_name}: {str(e)}")
            return None
    
    def update_error_usage(self, error_code: str, user_id: str = None, 
                          action_type: str = 'viewed', context: Dict = None):
        """
        Track error usage for analytics.
        
        Args:
            error_code: The error code
            user_id: User ID (optional)
            action_type: Type of action ('viewed', 'practiced', 'mastered', 'failed')
            context: Additional context data
        """
        try:
            # Get error ID
            error_query = "SELECT id FROM java_errors WHERE error_code = %s"
            error_result = self.db.execute_query(error_query, (error_code,), fetch_one=True)
            
            if not error_result:
                return
            
            error_id = error_result['id']
            
            # Insert usage record
            usage_query = """
            INSERT INTO error_usage_stats (error_id, user_id, action_type, context_data)
            VALUES (%s, %s, %s, %s)
            """
            
            import json
            context_json = json.dumps(context) if context else None
            
            self.db.execute_query(usage_query, (error_id, user_id, action_type, context_json))
            
            # Update usage count
            update_query = "UPDATE java_errors SET usage_count = usage_count + 1 WHERE id = %s"
            self.db.execute_query(update_query, (error_id,))
            
        except Exception as e:
            logger.error(f"Error updating usage stats: {str(e)}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get statistics about the error database."""
        try:
            stats = {}
            
            # Total categories
            cat_query = "SELECT COUNT(*) as count FROM error_categories WHERE is_active = TRUE"
            cat_result = self.db.execute_query(cat_query, fetch_one=True)
            stats['total_categories'] = cat_result['count'] if cat_result else 0
            
            # Total errors
            err_query = "SELECT COUNT(*) as count FROM java_errors WHERE is_active = TRUE"
            err_result = self.db.execute_query(err_query, fetch_one=True)
            stats['total_errors'] = err_result['count'] if err_result else 0
            
            # Errors by category
            breakdown_query = """
            SELECT ec.name_en, COUNT(je.id) as error_count
            FROM error_categories ec
            LEFT JOIN java_errors je ON ec.id = je.category_id AND je.is_active = TRUE
            WHERE ec.is_active = TRUE
            GROUP BY ec.id, ec.name_en
            ORDER BY ec.sort_order
            """
            breakdown = self.db.execute_query(breakdown_query)
            stats['errors_by_category'] = {row['name_en']: row['error_count'] for row in breakdown or []}
            
            # Most used errors
            popular_query = """
            SELECT error_name_en, usage_count
            FROM java_errors 
            WHERE is_active = TRUE 
            ORDER BY usage_count DESC 
            LIMIT 5
            """
            popular = self.db.execute_query(popular_query)
            stats['most_used_errors'] = [
                {'name': row['error_name_en'], 'usage_count': row['usage_count']} 
                for row in popular or []
            ]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {}

# Compatibility function to maintain backward compatibility
def create_database_repository() -> DatabaseErrorRepository:
    """Create and return a DatabaseErrorRepository instance."""
    return DatabaseErrorRepository()