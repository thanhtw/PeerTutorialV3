"""
Database Error Repository module for Java Peer Review Training System.

This module provides access to error data from the database,
replacing the JSON file-based approach for better performance and maintainability.
"""

import logging
import random
from typing import Dict, List, Any, Optional, Set, Union, Tuple
from utils.language_utils import get_current_language, t

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JsonErrorRepository:
    """
    Repository for accessing Java error data from the database.
    
    This class maintains compatibility with the JSON-based interface
    while using database backend for better performance and maintainability.
    """
    
    def __init__(self, java_errors_path: str = None):
        """
        Initialize the Database Error Repository.
        
        Args:
            java_errors_path: Deprecated - kept for compatibility
        """
        # Import here to avoid circular imports
        from db.mysql_connection import MySQLConnection
        
        self.db = MySQLConnection()
        self.current_language = get_current_language()
        
        # Cache for frequently accessed data
        self.java_errors = {}
        self.java_error_categories = []
        
        # Load error data from database
        self.load_error_data()
    
    def _get_language_fields(self, base_field: str) -> str:
        """Get the appropriate language field name."""
        if self.current_language == 'zh':
            return f"{base_field}_zh"
        else:
            return f"{base_field}_en"
    
    def load_error_data(self) -> bool:
        """
        Load error data from database.
        
        Returns:
            True if data is loaded successfully, False otherwise
        """
        try:
            # Test database connection
            if not self.db.test_connection_only():
                logger.warning("Database connection not available, using fallback")
                self._setup_fallback_data()
                return False
            
            # Load categories
            self._load_categories()
            
            # Load errors by category
            self._load_errors_by_category()
            
            logger.info(f"Loaded {len(self.java_error_categories)} categories with errors from database")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data from database: {str(e)}")
            self._setup_fallback_data()
            return False
    
    def _load_categories(self):
        """Load categories from database."""
        try:
            name_field = self._get_language_fields('name')
            
            query = f"""
            SELECT category_code, {name_field} as name
            FROM error_categories 
            WHERE is_active = TRUE
            ORDER BY sort_order
            """
            
            categories = self.db.execute_query(query)
            
            if categories:
                self.java_error_categories = [cat['name'] for cat in categories]
            else:
                self.java_error_categories = []
                
        except Exception as e:
            logger.error(f"Error loading categories: {str(e)}")
            self.java_error_categories = []
    
    def _load_errors_by_category(self):
        """Load errors organized by category."""
        try:
            self.java_errors = {}
            
            for category_name in self.java_error_categories:
                category_errors = self.get_category_errors(category_name)
                self.java_errors[category_name] = category_errors
                
        except Exception as e:
            logger.error(f"Error loading errors by category: {str(e)}")
            self.java_errors = {}
    
    def _setup_fallback_data(self):
        """Setup fallback data when database is not available."""
        logger.warning("Using fallback error categories")
        self.java_errors = {
            "Logical Errors": [],
            "Syntax Errors": [],
            "Code Quality": [],
            "Standard Violation": [],
            "Java Specific": []
        }
        self.java_error_categories = list(self.java_errors.keys())
    
    def get_all_categories(self) -> Dict[str, List[str]]:
        """
        Get all error categories.
        
        Returns:
            Dictionary with 'java_errors' categories
        """
        return {"java_errors": self.java_error_categories}
    
    def get_category_errors(self, category_name: str) -> List[Dict[str, str]]:
        """
        Get errors for a specific category.
        
        Args:
            category_name: Name of the category
            
        Returns:
            List of error dictionaries for the category
        """
        try:
            if not self.db.test_connection_only():
                return self.java_errors.get(category_name, [])
            
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
            if not self.db.test_connection_only():
                # Fallback to loaded data
                for category in self.java_errors:
                    for error in self.java_errors[category]:
                        if error.get(t("error_name")) == error_name:
                            return error
                return None
            
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
            java_error_categories = selected_categories.get("java_errors", [])
            if not java_error_categories:
                return []
            
            if not self.db.test_connection_only():
                # Use fallback logic
                all_errors = []
                for category in java_error_categories:
                    if category in self.java_errors:
                        for error in self.java_errors[category]:
                            all_errors.append({
                                "type": "java_error",
                                "category": category,
                                "name": error.get(t("error_name")),
                                "description": error.get(t("description")),
                                "implementation_guide": error.get(t("implementation_guide"), "")
                            })
                
                if all_errors:
                    if len(all_errors) <= count:
                        return all_errors
                    return random.sample(all_errors, count)
                return []
            
            # Database logic
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
        # Use database repository implementation
        try:
            from data.database_error_repository import DatabaseErrorRepository
            db_repo = DatabaseErrorRepository()
            return db_repo.get_errors_for_llm(selected_categories, specific_errors, count, difficulty)
        except Exception as e:
            logger.error(f"Error using database repository: {str(e)}")
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
            if not self.db.test_connection_only():
                # Fallback logic
                if category in self.java_errors:
                    for error in self.java_errors[category]:
                        if error.get(t("error_name")) == error_name:
                            return error.get(t("implementation_guide"))
                return None
            
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
            if not self.db.test_connection_only():
                # Fallback logic
                for category, errors in self.java_errors.items():
                    for error in errors:
                        if error.get(t("error_name_variable")) == error_name:
                            return {
                                t("category"): category,
                                t("error_name_variable"): error.get(t("error_name_variable")),
                                t("description"): error.get(t("description"))
                            }
                return None
            
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