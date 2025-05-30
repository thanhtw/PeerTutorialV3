import streamlit as st
import logging
from typing import Dict, List, Any, Optional
from data.database_error_repository import DatabaseErrorRepository
from utils.language_utils import get_current_language, t

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeGeneratorUI:
    """
    Professional UI component for Java code generation with clean layout and intuitive workflow.
    """
    
    def __init__(self):
        """Initialize the CodeGeneratorUI with database repository."""
        self.db_repository = DatabaseErrorRepository()
        self.current_language = get_current_language()
        
    def _load_all_errors(self) -> List[Dict]:
        """Load all available errors from the database."""
        try:
            # Get all categories first
            categories = self.db_repository.get_all_categories()
            all_errors = []
            
            # Get errors from all categories
            for category_list in categories.values():
                for category in category_list:
                    category_errors = self.db_repository.get_category_errors(category)
                    for error in category_errors:
                        error['category'] = category
                        all_errors.append(error)
            
            logger.info(f"Loaded {len(all_errors)} total errors from database")
            return all_errors
            
        except Exception as e:
            logger.error(f"Error loading all errors: {str(e)}")
            return []

    def _load_errors_by_category(self, category_name: str) -> List[Dict]:
        """Load errors for a specific category."""
        try:
            errors = self.db_repository.get_category_errors(category_name)
            logger.info(f"Loaded {len(errors)} errors for category {category_name}")
            return errors
        except Exception as e:
            logger.error(f"Error loading errors for category {category_name}: {str(e)}")
            return []
    
    def _get_error_categories(self) -> Dict[str, List[str]]:
        """Get all available error categories."""
        try:
            return self.db_repository.get_all_categories()
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return {"java_errors": []}
    
    def _get_error_details(self, error_name: str) -> Optional[Dict[str, str]]:
        """Get detailed information for a specific error."""
        try:
            return self.db_repository.get_error_details("java_error", error_name)
        except Exception as e:
            logger.error(f"Error getting details for {error_name}: {str(e)}")
            return None
    
    def _get_errors_for_llm(self, selected_categories: Dict[str, List[str]], 
                           count: int = 4, difficulty: str = "medium") -> tuple:
        """Get errors formatted for LLM processing."""
        try:
            return self.db_repository.get_errors_for_llm(
                selected_categories=selected_categories,
                count=count,
                difficulty=difficulty
            )
        except Exception as e:
            logger.error(f"Error getting errors for LLM: {str(e)}")
            return [], []
    
    def _get_random_errors(self, selected_categories: Dict[str, List[str]], 
                          count: int = 4) -> List[Dict[str, Any]]:
        """Get random errors from selected categories."""
        try:
            return self.db_repository.get_random_errors_by_categories(
                selected_categories, count
            )
        except Exception as e:
            logger.error(f"Error getting random errors: {str(e)}")
            return []
    
    def _update_error_usage(self, error_code: str, user_id: str = None, 
                           action_type: str = 'viewed'):
        """Track error usage for analytics."""
        try:
            self.db_repository.update_error_usage(
                error_code=error_code,
                user_id=user_id,
                action_type=action_type
            )
        except Exception as e:
            logger.error(f"Error updating usage stats: {str(e)}")
    
    def _get_database_statistics(self) -> Dict[str, Any]:
        """Get database statistics for display."""
        try:
            return self.db_repository.get_error_statistics()
        except Exception as e:
            logger.error(f"Error getting database statistics: {str(e)}")
            return {}
    
    def render_category_selection(self) -> Dict[str, List[str]]:
        """Render the category selection interface."""
        st.subheader(t("select_error_categories"))
        
        # Get available categories
        categories = self._get_error_categories()
        selected_categories = {"java_errors": []}
        
        if "java_errors" in categories:
            java_categories = categories["java_errors"]
            
            # Create columns for better layout
            cols = st.columns(3)
            
            for i, category in enumerate(java_categories):
                with cols[i % 3]:
                    if st.checkbox(category, key=f"cat_{category}"):
                        selected_categories["java_errors"].append(category)
        
        return selected_categories
    
    def render_error_selection(self, selected_categories: Dict[str, List[str]]) -> List[Dict]:
        """Render error selection interface for specific errors."""
        selected_errors = []
        
        if not selected_categories.get("java_errors"):
            st.warning(t("please_select_categories_first"))
            return selected_errors
        
        st.subheader(t("select_specific_errors"))
        
        for category in selected_categories["java_errors"]:
            with st.expander(f"{t('category')}: {category}"):
                errors = self._load_errors_by_category(category)
                
                for error in errors:
                    error_name = error.get(t("error_name"), error.get("name", "Unknown"))
                    description = error.get(t("description"), "")
                    
                    if st.checkbox(
                        f"{error_name}",
                        key=f"error_{category}_{error_name}",
                        help=description[:100] + "..." if len(description) > 100 else description
                    ):
                        error_with_category = error.copy()
                        error_with_category["category"] = category
                        selected_errors.append(error_with_category)
                        
                        # Track error usage
                        error_code = error.get("error_code", "")
                        if error_code:
                            self._update_error_usage(error_code, action_type='viewed')
        
        return selected_errors
    
    def render_difficulty_selection(self) -> str:
        """Render difficulty selection interface."""
        difficulty_options = [
            ("easy", t("easy")),
            ("medium", t("medium")),
            ("hard", t("hard"))
        ]
        
        selected_difficulty = st.selectbox(
            t("select_difficulty"),
            options=[opt[0] for opt in difficulty_options],
            format_func=lambda x: dict(difficulty_options)[x],
            index=1  # Default to medium
        )
        
        return selected_difficulty
    
    def render_error_count_selection(self) -> int:
        """Render error count selection interface."""
        return st.slider(
            t("number_of_errors"),
            min_value=1,
            max_value=10,
            value=4,
            help=t("select_number_of_errors_help")
        )
    
    def render_database_info(self):
        """Render database information and statistics."""
        with st.expander(t("database_information")):
            stats = self._get_database_statistics()
            
            if stats:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(t("total_categories"), stats.get('total_categories', 0))
                    st.metric(t("total_errors"), stats.get('total_errors', 0))
                
                with col2:
                    if 'errors_by_category' in stats:
                        st.write(t("errors_by_category"))
                        for category, count in stats['errors_by_category'].items():
                            st.write(f"• {category}: {count}")
                
                if 'most_used_errors' in stats and stats['most_used_errors']:
                    st.write(t("most_used_errors"))
                    for error in stats['most_used_errors'][:5]:
                        st.write(f"• {error['name']}: {error['usage_count']} uses")
            else:
                st.warning(t("database_statistics_unavailable"))
    
    def render_error_preview(self, errors: List[Dict]):
        """Render preview of selected errors."""
        if not errors:
            return
        
        st.subheader(t("selected_errors_preview"))
        
        for i, error in enumerate(errors, 1):
            with st.expander(f"{i}. {error.get(t('error_name'), error.get('name', 'Unknown'))}"):
                st.write(f"**{t('category')}:** {error.get('category', 'Unknown')}")
                st.write(f"**{t('description')}:** {error.get(t('description'), '')}")
                
                # Show implementation guide if available
                impl_guide = error.get(t('implementation_guide'), '')
                if impl_guide:
                    st.write(f"**{t('implementation_guide')}:** {impl_guide}")
                
                # Show difficulty level
                difficulty = error.get('difficulty_level', 'medium')
                st.write(f"**{t('difficulty')}:** {difficulty}")
    
    def get_errors_for_generation(self, selected_categories: Dict[str, List[str]], 
                                 specific_errors: List[Dict] = None,
                                 count: int = 4, 
                                 difficulty: str = "medium") -> tuple:
        """Get errors prepared for code generation."""
        if specific_errors:
            # Use specific errors if provided
            problem_descriptions = []
            for error in specific_errors:
                name = error.get(t("error_name"), error.get("name", "Unknown"))
                description = error.get(t("description"), "")
                category = error.get("category", "")
                problem_descriptions.append(f"{category}: {name} - {description}")
            
            return specific_errors, problem_descriptions
        else:
            # Use category-based selection
            return self._get_errors_for_llm(selected_categories, count, difficulty)
    
    def render_main_interface(self):
        """Render the main code generator interface."""
        st.title(t("java_code_generator"))
        
        # Database information
        self.render_database_info()
        
        # Selection method
        selection_method = st.radio(
            t("selection_method"),
            [t("by_categories"), t("specific_errors")],
            horizontal=True
        )
        
        selected_categories = {}
        specific_errors = []
        
        if selection_method == t("by_categories"):
            # Category-based selection
            selected_categories = self.render_category_selection()
            
            if selected_categories.get("java_errors"):
                # Additional options
                col1, col2 = st.columns(2)
                
                with col1:
                    difficulty = self.render_difficulty_selection()
                
                with col2:
                    error_count = self.render_error_count_selection()
                
                # Preview random errors from selected categories
                if st.button(t("preview_random_errors")):
                    preview_errors = self._get_random_errors(selected_categories, error_count)
                    self.render_error_preview(preview_errors)
        
        else:
            # Specific error selection
            selected_categories = self.render_category_selection()
            if selected_categories.get("java_errors"):
                specific_errors = self.render_error_selection(selected_categories)
                self.render_error_preview(specific_errors)
                difficulty = "medium"  # Default for specific errors
                error_count = len(specific_errors)
        
        # Return the configuration for code generation
        return {
            "selected_categories": selected_categories,
            "specific_errors": specific_errors,
            "difficulty": difficulty if 'difficulty' in locals() else "medium",
            "error_count": error_count if 'error_count' in locals() else 4
        }

# ...existing code...