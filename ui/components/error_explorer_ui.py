import streamlit as st
import os
import logging
from typing import Dict, List, Any, Optional
from data.database_error_repository import DatabaseErrorRepository
from utils.language_utils import t, get_current_language
from static.css_utils import load_css

logger = logging.getLogger(__name__)

class ErrorExplorerUI:
    """UI component for exploring Java errors with examples and solutions."""
    
    def __init__(self):
        """Initialize the Error Explorer UI."""
        self.repository = DatabaseErrorRepository()
        self.error_data = self._load_error_database()
        
        # Initialize session state
        if "selected_error_code" not in st.session_state:
            st.session_state.selected_error_code = None
        if "error_explorer_view" not in st.session_state:
            st.session_state.error_explorer_view = "list"
        if "user_progress" not in st.session_state:
            st.session_state.user_progress = {}
        self._load_styles()
    def _load_styles(self):
        """Load CSS styles for the Error Explorer UI."""
        try:
            # Get the current directory and construct path to CSS files
            current_dir = os.path.dirname(os.path.abspath(__file__))
            css_dir = os.path.join(current_dir, "..", "..", "static", "css", "error_explorer")
            
            if os.path.exists(css_dir):
                loaded_files = load_css(css_directory=css_dir)
                if loaded_files:
                    logger.debug(f"Loaded Error Explorer CSS files: {loaded_files}")
            else:
                logger.warning(f"CSS directory not found: {css_dir}")
        except Exception as e:
            logger.error(f"Error loading Error Explorer CSS: {str(e)}")

    def render(self):
        """Render the complete error explorer interface."""
       
        # Professional header
        self._render_header()
        # Search and filter section
        self._render_search_filters()
        
        # Main content area
        self._render_error_content()
    
    def _render_search_filters(self):
        """Render search and filter controls."""
        with st.container():
            st.markdown('<div class="search-filter-container">', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                search_term = st.text_input(
                    t("search_errors"),
                    placeholder=t("search_placeholder"),
                    key="error_search"
                )
            
            with col2:
                categories = self._get_categories()
                selected_category = st.selectbox(
                    t("filter_by_category"),
                    options=["All"] + categories,
                    key="category_filter"
                )
            
            with col3:
                difficulty_levels = ["All", t("easy"), t("medium"), t("hard")]
                selected_difficulty = st.selectbox(
                    t("filter_by_difficulty"),
                    options=difficulty_levels,
                    key="difficulty_filter"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Store filters in session state
        st.session_state.search_term = search_term
        st.session_state.selected_category = selected_category
        st.session_state.selected_difficulty = selected_difficulty
    
    def _render_error_content(self):
        """Render the main error content based on filters."""
        # Get filtered errors
        filtered_errors = self._get_filtered_errors()
        
        if not filtered_errors:
            self._render_no_results()
            return
        
        # Results count
        st.markdown(f'<div class="results-count">{len(filtered_errors)} {t("errors_found")}</div>', 
                   unsafe_allow_html=True)
        
        # Render errors by category
        errors_by_category = self._group_errors_by_category(filtered_errors)
        
        for category_name, errors in errors_by_category.items():
            self._render_category_section(category_name, errors)
    
    def _get_categories(self) -> List[str]:
        """Get all available categories."""
        try:
            categories_data = self.repository.get_all_categories()
            return categories_data.get("java_errors", [])
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []
    
    def _get_filtered_errors(self) -> List[Dict[str, Any]]:
        """Get errors based on current filters."""
        try:
            # Get all categories if no specific filter
            if st.session_state.get('selected_category', 'All') == 'All':
                categories = self._get_categories()
            else:
                categories = [st.session_state.selected_category]
            
            all_errors = []
            for category in categories:
                category_errors = self.repository.get_category_errors(category)
                for error in category_errors:
                    error['category'] = category
                    all_errors.append(error)
            
            # Apply filters
            filtered_errors = self._apply_filters(all_errors)
            return filtered_errors
            
        except Exception as e:
            logger.error(f"Error getting filtered errors: {str(e)}")
            return []
    
    def _apply_filters(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply search and difficulty filters to errors."""
        filtered = errors
        
        # Search filter
        search_term = st.session_state.get('search_term', '').lower()
        if search_term:
            filtered = [
                error for error in filtered
                if search_term in error.get(t("error_name"), "").lower() or
                   search_term in error.get(t("description"), "").lower()
            ]
        
        # Difficulty filter
        selected_difficulty = st.session_state.get('selected_difficulty', 'All')
        if selected_difficulty != 'All':
            # Map localized difficulty to database values
            difficulty_map = {
                t("easy"): "easy",
                t("medium"): "medium", 
                t("hard"): "hard"
            }
            db_difficulty = difficulty_map.get(selected_difficulty, "medium")
            
            filtered = [
                error for error in filtered
                if error.get('difficulty_level') == db_difficulty
            ]
        
        return filtered
    
    def _group_errors_by_category(self, errors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group errors by category."""
        grouped = {}
        for error in errors:
            category = error.get('category', 'Unknown')
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(error)
        return grouped
    
    def _render_category_section(self, category_name: str, errors: List[Dict[str, Any]]):
        """Render a category section with its errors."""
        st.markdown(f'<div class="category-section">', unsafe_allow_html=True)
        st.markdown(f'<h3 class="category-title">{category_name} <span class="error-count">({len(errors)})</span></h3>', 
                   unsafe_allow_html=True)
        
        # Render errors in this category
        for error in errors:
            self._render_error_card(error)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_error_card(self, error: Dict[str, Any]):
        """Render an individual error card with simplified display."""
        error_name = error.get(t("error_name"), "Unknown Error")
        
        with st.expander(f"🔧 {error_name}", expanded=False):
            # Error description
            st.markdown(f"**{t('description')}:**")
            st.write(error.get(t("description"), "No description available"))
            
            # Show difficulty and metadata in a compact row
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                difficulty = error.get('difficulty_level', 'medium')
                st.info(f"**{t('difficulty')}:** {difficulty.title()}")
            with col2:
                if error.get('error_code'):
                    st.info(f"**{t('error_code')}:** {error['error_code']}")
            with col3:
                if st.button(f"🎯 {t('practice_this_error')}", key=f"practice_{error_name}", use_container_width=True):
                    self._handle_practice_error(error)
            
            # Get examples from database
            examples = self.repository.get_error_examples(error_name)
            
            # Show wrong examples if available
            if examples.get("wrong_examples"):
                st.markdown(f"**❌ {t('problematic_code')}:**")
                for i, example in enumerate(examples["wrong_examples"][:2]):  # Show max 2 examples
                    st.markdown('<div class="code-example error-code">', unsafe_allow_html=True)
                    st.code(example, language="java")
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Show correct examples if available
            if examples.get("correct_examples"):
                st.markdown(f"**✅ {t('corrected_code')}:**")
                for i, example in enumerate(examples["correct_examples"][:2]):  # Show max 2 examples
                    st.markdown('<div class="code-example correct-code">', unsafe_allow_html=True)
                    st.code(example, language="java")
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Show explanation if available
            explanation = examples.get("explanation", "")
            if explanation:
                st.markdown(f"**💡 {t('explanation')}:**")
                st.info(explanation)
            elif error.get(t("implementation_guide")):
                st.markdown(f"**💡 {t('how_to_fix')}:**")
                st.info(error.get(t("implementation_guide")))

    def _handle_practice_error(self, error: Dict[str, Any]):
        """Handle practice error button click."""
        error_name = error.get(t("error_name"), "Unknown Error")
        st.success(f"🎯 {t('practice_started')}: {error_name}")
        st.info(f"💡 {t('practice_feature_info')}")
        # TODO: Integrate with practice system when available

    def _render_no_results(self):
        """Render no results message."""
        st.markdown("""
        <div class="no-results">
            <div class="no-results-icon">🔍</div>
            <h3>No errors found</h3>
            <p>Try adjusting your search criteria or filters.</p>
        </div>
        """, unsafe_allow_html=True)

    def _render_header(self):
        """Render the professional header with branding and statistics."""
        # Get error statistics from database
        try:
            stats = self.repository.get_error_statistics()
            total_errors = stats.get('total_errors', 0)
            total_categories = stats.get('total_categories', 0)
        except Exception as e:
            logger.debug(f"Could not get database statistics: {str(e)}")
            # Fallback to counting loaded data
            total_errors = sum(len(errors) for errors in self.error_data.values())
            total_categories = len(self.error_data)
        
        st.markdown(f"""
        <div class="error-explorer-header">
            <div class="header-content">
                <div class="title-section">
                    <h1>🔍 {t('error_explorer')}</h1>
                    <p class="subtitle">{t('explore_comprehensive_error_library')}</p>
                </div>
                <div class="stats-section">
                    <div class="stat-card">
                        <div class="stat-number">{total_errors}</div>
                        <div class="stat-label">{t('total_errors_available')}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{total_categories}</div>
                        <div class="stat-label">{t('error_categories')}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _render_main_content(self):
        """Render the main content area with enhanced layout."""
        # Search and filter controls
        self._render_search_and_filters()
       
        # Main content based on view mode
        self._render_list_view()

    def _load_error_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load the error database with enhanced mock data."""
        return {
            t("logical"): [
                {
                    "name": t("null_pointer_access"),
                    "description": t("null_pointer_description"),
                    "difficulty": t("medium"),
                    "frequency": t("high_frequency"),
                    "example": "String str = null; int len = str.length();",
                    "fix": t("null_pointer_fix")
                },
                {
                    "name": t("off_by_one_error"), 
                    "description": t("off_by_one_description"),
                    "difficulty": t("easy"),
                    "frequency": t("medium_frequency"),
                    "example": "for(int i = 0; i <= array.length; i++)",
                    "fix": t("off_by_one_fix")
                },
                {
                    "name": t("infinite_loop"),
                    "description": t("infinite_loop_description"),
                    "difficulty": t("medium"),
                    "frequency": t("medium_frequency"),
                    "example": "while(true) { /* missing break condition */ }",
                    "fix": t("infinite_loop_fix")
                }
            ],
            t("syntax"): [
                {
                    "name": t("missing_semicolon"),
                    "description": t("missing_semicolon_description"),
                    "difficulty": t("easy"),
                    "frequency": t("high_frequency"), 
                    "example": "int x = 5",
                    "fix": t("missing_semicolon_fix")
                },
                {
                    "name": t("mismatched_braces"),
                    "description": t("mismatched_braces_description"),
                    "difficulty": t("easy"),
                    "frequency": t("medium_frequency"),
                    "example": "if (condition) { ... ",
                    "fix": t("mismatched_braces_fix")
                },
                {
                    "name": t("wrong_variable_type"),
                    "description": t("wrong_variable_type_description"),
                    "difficulty": t("medium"),
                    "frequency": t("medium_frequency"),
                    "example": "int result = \"Hello World\";",
                    "fix": t("wrong_variable_type_fix")
                }
            ],
            t("code_quality"): [
                {
                    "name": t("poor_variable_naming"),
                    "description": t("poor_variable_naming_description"),
                    "difficulty": t("medium"),
                    "frequency": t("high_frequency"),
                    "example": "int x = calculateTotal();",
                    "fix": t("poor_variable_naming_fix")
                },
                {
                    "name": t("magic_numbers"),
                    "description": t("magic_numbers_description"),
                    "difficulty": t("easy"),
                    "frequency": t("medium_frequency"),
                    "example": "if (score > 85) { grade = 'A'; }",
                    "fix": t("magic_numbers_fix")
                }
            ],
            t("standard_violation"): [
                {
                    "name": t("naming_convention_violation"),
                    "description": t("naming_convention_description"),
                    "difficulty": t("easy"),
                    "frequency": t("medium_frequency"),
                    "example": "class myClass { ... }",
                    "fix": t("naming_convention_fix")
                },
                {
                    "name": t("improper_indentation"),
                    "description": t("improper_indentation_description"),
                    "difficulty": t("easy"),
                    "frequency": t("low_frequency"),
                    "example": "if(condition){\nreturn true;\n}",
                    "fix": t("improper_indentation_fix")
                }
            ],
            t("java_specific"): [
                {
                    "name": t("resource_leak"),
                    "description": t("resource_leak_description"),
                    "difficulty": t("hard"),
                    "frequency": t("medium_frequency"),
                    "example": "FileInputStream fis = new FileInputStream(file);",
                    "fix": t("resource_leak_fix")
                },
                {
                    "name": t("string_comparison_equals"),
                    "description": t("string_comparison_description"),
                    "difficulty": t("medium"),
                    "frequency": t("high_frequency"),
                    "example": "if (str1 == str2) { ... }",
                    "fix": t("string_comparison_fix")
                }
            ]
        }


def render_error_explorer():
    """Main function to render the error explorer."""
    explorer = ErrorExplorerUI()
    explorer.render()
