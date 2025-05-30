"""
Code Generator UI component for Java Peer Review Training System.

This module provides a professional UI for configuring and generating Java code snippets
with intentional errors for review practice.
"""

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
    
    def __init__(self, workflow, code_display_ui):
        """Initialize the CodeGeneratorUI with database repository."""
        self.db_repository = DatabaseErrorRepository()
        self.current_language = get_current_language()
        self.workflow = workflow
        self.code_display_ui = code_display_ui
        
    def render(self, user_level: str = "medium"):
        """
        Render the professional code generation interface.
        
        Args:
            user_level: User's experience level (basic, medium, senior)
        """
        # Professional header section
        self._render_header()
        
        # Main content in clean sections
        self._render_configuration_section(user_level)
        
        # Generation section
        self._render_generation_section()
        
        # Generated code display section
        self._render_code_display_section()

    def _render_code_display_section(self):
        """Render the generated code display section."""
        if hasattr(st.session_state, 'workflow_state') and st.session_state.workflow_state:
            state = st.session_state.workflow_state
            
            if hasattr(state, 'code_snippet') and state.code_snippet:
                st.markdown("""
                <div class="generated-code-section">
                    <div class="code-preview-header">
                        <span class="section-icon">☕</span>
                        <h3 class="code-preview-title">Generated Java Code</h3>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display the code
                self.code_display_ui.render_code_display(state.code_snippet)
                
                # Regenerate option
                st.markdown("""
                <div class="regenerate-section">
                    <h4>🔄 Not satisfied with the result?</h4>
                    <p>Generate a new code snippet with the same configuration</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔄 Generate New Problem", key="regenerate", use_container_width=True):
                    self._handle_code_generation()

    def _render_configuration_section(self, user_level: str):
        """Render the configuration section with mode selection and parameters."""
        st.markdown('<div class="generate-section">', unsafe_allow_html=True)
        
        # Section header
        st.markdown(f"""
        <div class="section-header">
            <span class="section-icon">⚙️</span>
            <div>
                <h3 class="section-title">{t('configuration')}</h3>
                <p class="section-subtitle">{t('setup_code_generation_parameters')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Error selection mode
        self._render_mode_selection()
        
        # Parameters display
        self._render_parameters_display(user_level)
        
        # Category/Error selection based on mode
        self._render_selection_interface()
        
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_generation_section(self):
        """Render the generation button and controls."""
        
        # Check if we can generate
        can_generate = self._can_generate()
        
        if can_generate:
            if st.button(
                f"🔧 {t('generate_code_problem')}",
                key="generate_code_main",
                type="primary",
                use_container_width=True
            ):
                self._handle_code_generation()
        else:
            st.error(f"⚠️ {t('please_select_at_least_one_error_category')}")
            st.button(
                f"🔧 {t('generate_code_problem')}",
                key="generate_code_disabled",
                disabled=True,
                use_container_width=True
            )

    def _render_mode_selection(self):
        """Render the error selection mode with professional styling."""
        
        
        # Mode selection with custom styling
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(f"🎲 {t('random_mode')}", key="random_mode", use_container_width=True):
                st.session_state.error_selection_mode = "random"
        
        with col2:
            if st.button(f"🎯 {t('advanced_mode')}", key="advanced_mode", use_container_width=True):
                st.session_state.error_selection_mode = "advanced"
        
        # Initialize mode if not set
        if "error_selection_mode" not in st.session_state:
            st.session_state.error_selection_mode = "random"
        
        # Display current mode
        mode = st.session_state.error_selection_mode
        if mode == "random":
            st.info("🎲 **Random Mode**: System will automatically select appropriate errors based on your level")
        else:
            st.info("🎯 **Advanced Mode**: Choose specific error categories to include in the generated code")

    def _render_parameters_display(self, user_level: str):
        """Render the parameters display with visual cards."""
        
        # Parameter mapping based on user level
        params = self._get_level_parameters(user_level)
        
        # Display parameters in a grid
        cols = st.columns(4)
        
        with cols[0]:
            st.markdown(f"""
            <div class="parameter-card">
                <span class="parameter-icon">📏</span>
                <div class="parameter-label">{t('code_length')}</div>
                <div class="parameter-value">{params['code_length'].title()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown(f"""
            <div class="parameter-card">
                <span class="parameter-icon">⭐</span>
                <div class="parameter-label">{t('difficulty')}</div>
                <div class="parameter-value">{params['difficulty'].title()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown(f"""
            <div class="parameter-card">
                <span class="parameter-icon">🐛</span>
                <div class="parameter-label">{t('error_count')}</div>
                <div class="parameter-value">{params['error_count']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[3]:
            st.markdown(f"""
            <div class="parameter-card">
                <span class="parameter-icon">👤</span>
                <div class="parameter-label">{t('your_level')}</div>
                <div class="parameter-value">{user_level.title()}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="parameters-note">
            💡 {t('these_parameters_optimized')}
        </div>
        """, unsafe_allow_html=True)

    def _render_selection_interface(self):
        """Render the category/error selection interface."""
        mode = st.session_state.get("error_selection_mode", "random")
        
        if mode == "random":
            self._render_category_selection()

    def _render_category_selection(self):
        """Render the category selection interface with professional styling."""
        st.markdown(f"""
        <div class="category-selection-enhanced">
            <div class="selection-header">
                <h4>🎯 {t('select_error_categories')}</h4>
                <p>{t('choose_error_types')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Load error categories
        categories_dict = self._get_error_categories()
        
        # Initialize selected categories
        if "selected_categories" not in st.session_state:
            st.session_state.selected_categories = []
        
        # Extract the java_errors list and pass it to the grid
        java_categories = categories_dict.get("java_errors", [])
        if java_categories:
            self._render_category_grid(java_categories)
        else:
            st.warning(t("no_categories_available"))
        
    def _get_category_icon(self, category_name: str) -> str:
        """Get icon for category based on name (language-aware)."""
        # Map both English and Chinese category names to icons
        icon_mapping = {
            # English category names (from database)
            "logical errors": "🧠",
            "syntax errors": "🔤", 
            "code quality": "⭐",
            "standard violation": "📋",
            "java specific": "☕",
            
            # Chinese category names (from database)
            "邏輯錯誤": "🧠",
            "語法錯誤": "🔤",
            "程式碼品質": "⭐", 
            "標準違規": "📋",
            "java 特定錯誤": "☕",
            
            # Category codes (fallback)
            "logical": "🧠",
            "syntax": "🔤",
            "code_quality": "⭐",
            "standard_violation": "📋", 
            "java_specific": "☕",
            
            # Legacy mappings (in case they're still used)
            "logic_errors": "🧠",
            "runtime_errors": "⚡",
            "null_pointer": "🚫",
            "array_errors": "📊",
            "loop_errors": "🔄",
            "condition_errors": "❓",
            "method_errors": "🔧",
            "class_errors": "🏗️",
            "variable_errors": "📝"
        }
        
        # Try exact match first (case-sensitive)
        if category_name in icon_mapping:
            return icon_mapping[category_name]
        
        # Try case-insensitive match
        category_lower = category_name.lower()
        for key, icon in icon_mapping.items():
            if key.lower() == category_lower:
                return icon
        
        # Default fallback icon
        return "🐛"

    def _toggle_category(self, category_name: str):
        """Toggle category selection."""
        if "selected_categories" not in st.session_state:
            st.session_state.selected_categories = []
        
        if category_name in st.session_state.selected_categories:
            st.session_state.selected_categories.remove(category_name)
        else:
            st.session_state.selected_categories.append(category_name)
            
    def _render_category_grid(self, categories: List[str]):
        """Render categories in a compact three-column layout with parameter card styling."""
        selected = st.session_state.get("selected_categories", [])
        
        # Three-column grid for better space utilization
        cols = st.columns(3, gap="medium")
        
        # Distribute categories across three columns
        for i, category_name in enumerate(categories):
            description = f"{t('practice_with')} {category_name} {t('related_errors')}"
            icon = self._get_category_icon(category_name)
            is_selected = category_name in selected
            
            # Current column (cycle through 0, 1, 2)
            current_col = cols[i % 3]
            
            with current_col:
                # Parameter card style with selection state
                selected_class = "selected" if is_selected else ""
                selection_indicator = f"✓ {t('selected')}" if is_selected else f"{t('click_to_select')}"

                st.markdown(f"""
                <div class="parameter-card category-card {selected_class}" style="{
                    'border: 2px solid #28a745; background: rgba(40, 167, 69, 0.1);' if is_selected 
                    else 'border: 1px solid #dee2e6; background: #f8f9fa;'
                }">
                    <span class="parameter-icon">{icon}</span>
                    <div class="parameter-label">{category_name}</div>
                """, unsafe_allow_html=True)
                
                # Hidden button for interaction (maintains functionality)
                if st.button(
                    selection_indicator,  # Empty label for hidden appearance
                    key=f"category_card_{category_name}",
                    help=description,
                    use_container_width=True
                ):
                    self._toggle_category(category_name)
                    st.rerun()
        
        # Compact quick actions optimized for 3-column layout
        if categories and len(categories) > 1:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(
                    f"🎯 {t('select')} All",
                    key="select_all_categories",
                    help="Select all available categories",
                    use_container_width=True,
                    disabled=len(selected) == len(categories)
                ):
                    st.session_state.selected_categories = categories.copy()
                    st.rerun()
            
            with col2:
                if st.button(
                    f"🗑️ Clear All",
                    key="clear_all_categories", 
                    help="Remove all selected categories",
                    use_container_width=True,
                    disabled=len(selected) == 0
                ):
                    st.session_state.selected_categories = []
                    st.rerun()
                   
    def _can_generate(self) -> bool:
        """Check if we can generate code based on selected categories."""
        mode = st.session_state.get("error_selection_mode", "random")
        selected_categories = st.session_state.get("selected_categories", [])
        
        # For both modes, we need at least one category selected
        if not selected_categories or len(selected_categories) == 0:
            return False
            
        # Additional validation: ensure categories contain actual error types
        if not any(category.strip() for category in selected_categories):
            return False
            
        return True

    def _get_level_parameters(self, user_level: str) -> Dict[str, Any]:
        """Get parameters based on user level."""
        level_configs = {
            "basic": {
                "code_length": "short",
                "difficulty": "easy",
                "error_count": "1-2"
            },
            "medium": {
                "code_length": "medium", 
                "difficulty": "medium",
                "error_count": "2-3"
            },
            "senior": {
                "code_length": "long",
                "difficulty": "hard", 
                "error_count": "3-5"
            }
        }
        return level_configs.get(user_level, level_configs["medium"])

    def _render_header(self):
        """Render the professional header with branding and description."""
        st.markdown(f"""
        <div class="generate-header">
            <h2>🔧 {t('code_generation_workshop')}</h2>
            <p>{t('configure_generate_java_code')}</p>
        </div>
        """, unsafe_allow_html=True)
    
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
    
    def _handle_code_generation(self):
        """Handle the code generation process."""
        with st.spinner("🔧 Generating your Java code challenge..."):
            try:
                # Prepare generation parameters
                mode = st.session_state.get("error_selection_mode", "random")
                selected_categories = st.session_state.get("selected_categories", []) if mode == "advanced" else None
                
                # Trigger workflow
                result = self.workflow.invoke({
                    "selected_categories": selected_categories,
                    "generation_mode": mode
                })
                
                if result and hasattr(result, 'code_snippet'):
                    st.success("✅ Code generated successfully! Proceed to the Review tab.")
                    # Switch to review tab
                    st.session_state.active_tab = 1
                    st.rerun()
                else:
                    st.error("❌ Failed to generate code. Please try again.")
                    
            except Exception as e:
                logger.error(f"Code generation error: {str(e)}")
                st.error(f"❌ Generation failed: {str(e)}")

    