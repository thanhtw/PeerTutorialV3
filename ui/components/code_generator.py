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
        
        # Initialize session state properly
        self._initialize_session_state()
        
        # Main content in clean sections
        self._render_configuration_section(user_level)
        
        # Generation section
        self._render_generation_section()
        
        # Generated code display section
        self._render_code_display_section()

    def _initialize_session_state(self):
        """Initialize session state variables with correct data types."""
        if "selected_categories" not in st.session_state:
            st.session_state.selected_categories = []
        
        if "selected_specific_errors" not in st.session_state:
            st.session_state.selected_specific_errors = []
        
        if "error_selection_mode" not in st.session_state:
            st.session_state.error_selection_mode = "random"
        
        # Ensure selected_categories is always a list
        if not isinstance(st.session_state.selected_categories, list):
            st.session_state.selected_categories = []

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
        """Render the configuration section with tabbed mode selection and parameters."""
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
        
        # Parameters display
        self._render_parameters_display(user_level)
        
        # Tabbed mode selection and interface
        self._render_tabbed_mode_interface()
        
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_tabbed_mode_interface(self):
        """Render the tabbed interface for random and advanced modes."""
        # Create tabs for the two modes
        mode_tabs = st.tabs([
            f"🎲 {t('random_mode')}",
            f"🎯 {t('advanced_mode')}"
        ])
        
        with mode_tabs[0]:  # Random Mode Tab
            st.session_state.error_selection_mode = "random"
            
            st.markdown("""
            <div class="mode-description">
                <p>🎲 <strong>Random Mode</strong>: System will automatically select appropriate errors based on your level and chosen categories.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Category selection for random mode
            self._render_category_selection()
        
        with mode_tabs[1]:  # Advanced Mode Tab
            st.session_state.error_selection_mode = "advanced"
            
            st.markdown("""
            <div class="mode-description">
                <p>🎯 <strong>Advanced Mode</strong>: Choose specific error categories and individual errors to include in the generated code.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Category selection for advanced mode
            self._render_category_selection()
            
            # Specific error selection (only in advanced mode)
            selected_categories = st.session_state.get("selected_categories", [])
            if selected_categories:
                self._render_specific_error_selection()

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

    def _render_specific_error_selection(self):
        """Render specific error selection for advanced mode."""
        selected_categories = st.session_state.get("selected_categories", [])
        
        if not selected_categories:
            return
        
        st.markdown(f"""
        <div class="error-selection-section">
            <h4>🎯 {t('select_specific_errors')}</h4>
            <p>Choose which specific errors to include in the generated code</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize selected specific errors
        if "selected_specific_errors" not in st.session_state:
            st.session_state.selected_specific_errors = []
        
        # Track current selected errors
        current_selected = []
        
        for category in selected_categories:
            with st.expander(f"📁 {category}", expanded=True):
                errors = self._load_errors_by_category(category)
                
                if not errors:
                    st.warning(f"No errors found for category: {category}")
                    continue
                
                # Create columns for error selection
                for i, error in enumerate(errors):
                    error_name = error.get(t("error_name"), error.get("name", "Unknown"))
                    description = error.get(t("description"), "")
                    difficulty = error.get("difficulty_level", "medium")
                    
                    # Create unique key for this error
                    error_key = f"{category}_{error_name}"
                    
                    # Check if this error was previously selected
                    was_selected = any(
                        e.get("category") == category and e.get(t("error_name")) == error_name 
                        for e in st.session_state.selected_specific_errors
                    )
                    
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        is_selected = st.checkbox(
                            f"**{error_name}**",
                            value=was_selected,
                            key=f"error_check_{error_key}",
                            help=description[:200] + "..." if len(description) > 200 else description
                        )
                        
                        if is_selected:
                            # Add complete error information
                            error_with_metadata = error.copy()
                            error_with_metadata["category"] = category
                            error_with_metadata[t("category")] = category
                            current_selected.append(error_with_metadata)
                    
                    with col2:
                        # Show difficulty badge
                        difficulty_colors = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
                        st.write(f"{difficulty_colors.get(difficulty, '⚪')} {difficulty}")
        
        # Update session state with currently selected errors
        st.session_state.selected_specific_errors = current_selected
        
        # Show selected count
        if current_selected:
            st.success(f"✅ {len(current_selected)} errors selected")
        else:
            st.warning("⚠️ No specific errors selected")
        
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
            "java_specific": "☕"
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
        # Ensure selected_categories is initialized as a list
        if "selected_categories" not in st.session_state:
            st.session_state.selected_categories = []
        
        # Ensure it's always a list
        if not isinstance(st.session_state.selected_categories, list):
            st.session_state.selected_categories = []
        
        if category_name in st.session_state.selected_categories:
            st.session_state.selected_categories.remove(category_name)
            # Clear specific errors for this category if in advanced mode
            if "selected_specific_errors" in st.session_state:
                st.session_state.selected_specific_errors = [
                    e for e in st.session_state.selected_specific_errors 
                    if e.get("category") != category_name
                ]
        else:
            st.session_state.selected_categories.append(category_name)

    def _render_category_grid(self, categories: List[str]):
        """Render categories in a compact three-column layout with parameter card styling."""
        # Ensure selected_categories is a list
        selected = st.session_state.get("selected_categories", [])
        if not isinstance(selected, list):
            selected = []
            st.session_state.selected_categories = []
        
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
                </div>
                """, unsafe_allow_html=True)
                
                # Hidden button for interaction (maintains functionality)
                if st.button(
                    selection_indicator,
                    key=f"category_card_{category_name}_{st.session_state.error_selection_mode}",
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
                    key=f"select_all_categories_{st.session_state.error_selection_mode}",
                    help="Select all available categories",
                    use_container_width=True,
                    disabled=len(selected) == len(categories)
                ):
                    st.session_state.selected_categories = categories.copy()
                    st.rerun()
            
            with col2:
                if st.button(
                    f"🗑️ Clear All",
                    key=f"clear_all_categories_{st.session_state.error_selection_mode}", 
                    help="Remove all selected categories",
                    use_container_width=True,
                    disabled=len(selected) == 0
                ):
                    st.session_state.selected_categories = []
                    if "selected_specific_errors" in st.session_state:
                        st.session_state.selected_specific_errors = []
                    st.rerun()

    def _can_generate(self) -> bool:
        """Check if we can generate code based on selected categories or specific errors."""
        mode = st.session_state.get("error_selection_mode", "random")
        selected_categories = st.session_state.get("selected_categories", [])
        
        # In random mode, we need at least one category selected
        if mode == "random":
            return len(selected_categories) > 0
        
        # In advanced mode, we need at least one specific error selected
        if mode == "advanced":
            selected_specific_errors = st.session_state.get("selected_specific_errors", [])
            return len(selected_specific_errors) > 0
        
        return False

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
    
    def _handle_code_generation(self):
        """Handle the code generation process."""
        with st.spinner("🔧 Generating your Java code challenge..."):
            try:
                # Prepare generation parameters based on mode
                mode = st.session_state.get("error_selection_mode", "random")
                
                if mode == "random":
                    # Random mode: use selected categories
                    selected_categories = st.session_state.get("selected_categories", [])
                    
                    # Ensure it's a list
                    if not isinstance(selected_categories, list):
                        selected_categories = []
                    
                    # Format for workflow
                    categories_dict = {"java_errors": selected_categories} if selected_categories else None
                    
                    result = self.workflow.invoke({
                        "selected_categories": categories_dict,
                        "generation_mode": "random"
                    })
                else:
                    # Advanced mode: use specific errors
                    selected_specific_errors = st.session_state.get("selected_specific_errors", [])
                    
                    if not selected_specific_errors:
                        st.error("❌ Please select at least one specific error in Advanced mode")
                        return
                    
                    # Update error usage tracking
                    for error in selected_specific_errors:
                        error_code = error.get("error_code", "")
                        if error_code:
                            self._update_error_usage(error_code, action_type='practiced')
                    
                    result = self.workflow.invoke({
                        "selected_specific_errors": selected_specific_errors,
                        "generation_mode": "advanced"
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