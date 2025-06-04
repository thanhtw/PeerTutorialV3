"""
Code Generator UI component for Java Peer Review Training System.

This module provides a professional UI for configuring and generating Java code snippets
with intentional errors for review practice. Revised to properly integrate with workflow manager.
FIXED: Proper handling of LangGraph state objects (AddableValuesDict).
"""

import streamlit as st
import logging
from typing import Dict, List, Any, Optional
from data.database_error_repository import DatabaseErrorRepository
from utils.language_utils import get_current_language, t
from state_schema import WorkflowState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeGeneratorUI:
    """
    Professional UI component for Java code generation with clean layout and intuitive workflow.
    Now properly integrated with the workflow manager system.
    FIXED: Proper handling of LangGraph state objects.
    """
    
    def __init__(self, workflow, code_display_ui):
        """Initialize the CodeGeneratorUI with database repository and workflow."""
        self.db_repository = DatabaseErrorRepository()
        self.current_language = get_current_language()
        self.workflow = workflow  # This is JavaCodeReviewGraph
        self.code_display_ui = code_display_ui
        
        # Get reference to the workflow manager for proper workflow execution
        self.workflow_manager = getattr(workflow, 'workflow_manager', None)
        
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
        """Render the tabbed interface for random and advanced modes with correct state sync."""
        # Use localized tab names
        tab_names = [
            f"🎲 {t('random_mode')}",
            f"🎯 {t('advanced_mode')}"
        ]
        # Track the last active tab in session state
        if "codegen_active_tab" not in st.session_state:
            st.session_state.codegen_active_tab = 0
        # Use radio with localized tab names
        tab_index = st.radio(
            label="Code Generation Mode",  # Non-empty label for accessibility
            options=[0, 1],
            index=st.session_state.codegen_active_tab,
            key="codegen_tab_radio",
            label_visibility="collapsed",
            horizontal=True,
            format_func=lambda x: tab_names[x]
        )
        if tab_index != st.session_state.codegen_active_tab:
            st.session_state.codegen_active_tab = tab_index
            st.session_state.error_selection_mode = "random" if tab_index == 0 else "advanced"

        # Render the correct tab content
        if st.session_state.codegen_active_tab == 0:
            # Random Mode Tab
            st.session_state.error_selection_mode = "random"
            st.markdown(f"""
            <div class="mode-description">
                <p>🎲 {t('random_mode_description')}</p>
            </div>
            """, unsafe_allow_html=True)
            self._render_category_selection()
            selected_categories = st.session_state.get("selected_categories", [])
            if selected_categories:
                st.markdown(
                    f"<div class='selected-categories'>"
                    + "".join(
                        f"<span class='selected-category-item'>{self._get_category_icon(cat)} {cat}</span>"
                        for cat in selected_categories
                    )
                    + "</div>",
                    unsafe_allow_html=True
                )
            st.markdown('<div class="generate-button-section">', unsafe_allow_html=True)
            st.button(
                f"🔧 {t('generate_code_problem')}",
                key="generate_code_main_random",
                type="primary",
                use_container_width=True,
                disabled=not self._can_generate(),
                on_click=self._handle_code_generation if self._can_generate() else None
            )
            st.markdown('</div>', unsafe_allow_html=True)
            if not selected_categories:
                st.warning(f"⚠️ {t('please_select_at_least_one_error_category')}")
        else:
            # Advanced Mode Tab
            st.session_state.error_selection_mode = "advanced"
            st.markdown(f"""
            <div class="mode-description">
                <p>🎯 {t('advanced_mode_help')}</p>
            </div>
            """, unsafe_allow_html=True)
            self._render_advanced_error_selection()
            st.markdown('<div class="generate-button-section">', unsafe_allow_html=True)
            st.button(
                f"🔧 {t('generate_code_problem')}",
                key="generate_code_main_advanced",
                type="primary",
                use_container_width=True,
                disabled=not self._can_generate(),
                on_click=self._handle_code_generation if self._can_generate() else None
            )
            st.markdown('</div>', unsafe_allow_html=True)
            if not st.session_state.get("selected_specific_errors", []):
                st.warning(f"⚠️ {t('please_select_at_least_one_specific_error')}")

    def _render_advanced_error_selection(self):
        from data.database_error_repository import DatabaseErrorRepository  # Add import
        repository = DatabaseErrorRepository()  # Use database repository
                
        # Initialize selected specific errors
        if "selected_specific_errors" not in st.session_state:
            st.session_state.selected_specific_errors = []
        
        # Load all categories from database using repository
        categories_dict = repository.get_all_categories()
        all_categories = categories_dict.get("java_errors", [])
        
        if not all_categories:
            st.warning("No categories available in the database")
            return
        
        # Track current selected errors
        current_selected = []
        
        # Difficulty order for sorting
        difficulty_order = {"easy": 1, "medium": 2, "hard": 3}

        # Display all categories and their errors
        for category in all_categories:
            icon = self._get_category_icon(category)
            with st.expander(f"{icon} {category}", expanded=False):
                errors = repository.get_category_errors(category)  # Use repository method
                
                if not errors:
                    st.warning(f"No errors found for category: {category}")
                    continue

                # Sort errors by difficulty_level (easy, medium, hard)
                errors_sorted = sorted(
                    errors,
                    key=lambda x: (
                        difficulty_order.get(x.get('difficulty_level', 'medium'), 2),
                        x.get(t("error_name"), x.get("name", ""))
                    )
                )
                
                # Create columns for error selection
                for i, error in enumerate(errors_sorted):
                    error_name = error.get(t("error_name"), error.get("name", "Unknown"))
                    description = error.get(t("description"), "")
                    difficulty = error.get("difficulty_level", "medium")
                    
                    # Map internal difficulty to localized label
                    difficulty_label = {
                        "easy": t("easy"),
                        "medium": t("medium"),
                        "hard": t("hard")
                    }.get(difficulty, difficulty)
                    
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
                            key=f"advanced_error_check_{error_key}",
                            help=description[:200] + "..." if len(description) > 200 else description
                        )
                        
                        if is_selected:
                            # Add complete error information
                            error_with_metadata = error.copy()
                            error_with_metadata["category"] = category
                            error_with_metadata[t("category")] = category
                            current_selected.append(error_with_metadata)
                    
                    with col2:
                        # Show difficulty badge with localized label
                        difficulty_colors = {
                            "easy": "🟢", t("easy"): "🟢",
                            "medium": "🟡", t("medium"): "🟡",
                            "hard": "🔴", t("hard"): "🔴"
                        }
                        st.write(f"{difficulty_colors.get(difficulty_label, '⚪')} {difficulty_label}")
        
        # Update session state with currently selected errors
        st.session_state.selected_specific_errors = current_selected
        
        # Show selected count and quick actions
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if current_selected:
                st.success(f"✅ {len(current_selected)} {t('errors_selected')}")
            else:
                st.warning(f"⚠️ {t('no_specific_errors_selected')}")
        
        with col2:
            if st.button(
                f"🎯 {t('select')} {t('all')}",
                key=f"{t('select_all_advanced_errors')}",
                help=f"{t('select_all_available_errors')}",
                use_container_width=True
            ):
                # Select all errors from all categories
                all_selected = []
                for category in all_categories:
                    errors = repository.get_category_errors(category)
                    # Sort errors by difficulty_level for consistency
                    errors_sorted = sorted(
                        errors,
                        key=lambda x: (
                            difficulty_order.get(x.get('difficulty_level', 'medium'), 2),
                            x.get(t("error_name"), x.get("name", ""))
                        )
                    )
                    for error in errors_sorted:
                        error_with_metadata = error.copy()
                        error_with_metadata["category"] = category
                        error_with_metadata[t("category")] = category
                        all_selected.append(error_with_metadata)
                
                st.session_state.selected_specific_errors = all_selected
                st.rerun()
        
        with col3:
            if st.button(
                f"🗑️ {t('clear_all')}",
                key=f"{t('clear_all_advanced_errors')}",
                help=f"{t('clear_all_selected_errors')}",
                use_container_width=True,
                disabled=len(current_selected) == 0
            ):
                st.session_state.selected_specific_errors = []
                st.rerun()

    def _render_parameters_display(self, user_level: str):
        """Render the parameters display with visual cards, supporting both English and Chinese."""
        # Always use the canonical user_level key for lookup (internal: 'basic', 'medium', 'senior')
        # Accept both English and localized user_level
        internal_levels = ["basic", "medium", "senior"]
        localized_levels = [t("basic"), t("medium"), t("senior")]
        # Map user_level to internal if possible
        user_level_key = user_level.lower()
        
        if user_level_key in internal_levels:
            internal_level = user_level_key
        elif user_level_key in localized_levels:
            internal_level = internal_levels[localized_levels.index(user_level_key)]
        else:
            internal_level = "medium"

        params = self._get_level_parameters(user_level)
        
        # Localize code_length and difficulty values
        code_length_localized = {
            "short": t("short"),
            "medium": t("medium"),
            "long": t("long")
        }.get(params['code_length'], params['code_length'])

        difficulty_localized = {
            "easy": t("easy"),
            "medium": t("medium"),
            "hard": t("hard")
        }.get(params['difficulty'], params['difficulty'])

        # Display parameters in a grid
        cols = st.columns(4)
        with cols[0]:
            st.markdown(f"""
            <div class="parameter-card">
                <span class="parameter-icon">📏</span>
                <div class="parameter-label">{t('code_length')}</div>
                <div class="parameter-value">{code_length_localized}</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"""
            <div class="parameter-card">
                <span class="parameter-icon">⭐</span>
                <div class="parameter-label">{t('difficulty')}</div>
                <div class="parameter-value">{difficulty_localized}</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"""
            <div class="parameter-card">
                <span class="parameter-icon">🐛</span>
                <div class="parameter-label">{t('error_count')}</div>
                <div class="parameter-value">{params['error_count_start']} - {params['error_count_end']}</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f"""
            <div class="parameter-card">
                <span class="parameter-icon">👤</span>
                <div class="parameter-label">{t('your_level')}</div>
                <div class="parameter-value">{t(user_level_key) if user_level_key in localized_levels else t(internal_level)}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="parameters-note">
            💡 {t('these_parameters_optimized')}
        </div>
        """, unsafe_allow_html=True)

    def _render_category_selection(self):
        """Render the category selection interface with professional styling."""
        
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
        # This method is now replaced by _render_advanced_error_selection
        # Keep for backward compatibility but redirect
        self._render_advanced_error_selection()

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
        st.rerun()

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
                <div class="parameter-card category-card {selected_class}">
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
                    f"🎯 {t('select')} {t('all')}",
                    key=f"select_all_categories_{st.session_state.error_selection_mode}",
                    help=f"{t('select_all_available_categories')}",
                    use_container_width=True,
                    disabled=len(selected) == len(categories)
                ):
                    st.session_state.selected_categories = categories.copy()
                    st.rerun()
            
            with col2:
                if st.button(
                    f"🗑️ {t('clear_all')}",
                    key=f"clear_all_categories_{st.session_state.error_selection_mode}", 
                    help=f"{t('remove_all_selected_categories')}",
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
            f"{t('basic').lower()}": {
                "code_length": "short",
                "difficulty": "easy",
                "error_count_start": "1",
                "error_count_end": "2"
            },
            f"{t('medium').lower()}": {
                "code_length": "medium", 
                "difficulty": "medium",
                "error_count_start": "2",
                "error_count_end": "3"
            },
            f"{t('senior').lower()}": {
                "code_length": "long",
                "difficulty": "hard", 
                "error_count_start": "3",
                "error_count_end": "5"
            }
        }
        return level_configs.get(user_level.lower(), level_configs[f"{t('medium').lower()}"])

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
            logger.debug(f"Loaded {len(errors)} errors for category {category_name}")
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
        """
        Handle the code generation process with proper workflow integration.
        Now uses the workflow manager for proper workflow execution.
        """
        with st.spinner("🔧 Generating your Java code challenge..."):
            try:
                logger.debug("Starting code generation through workflow manager")
                
                # Prepare workflow state
                workflow_state = self._prepare_workflow_state()
                if not workflow_state:
                    return
                
                # Execute code generation through the workflow system
                updated_state = self._execute_code_generation_workflow(workflow_state)
                
                # Handle the result
                self._handle_generation_result(updated_state)
                    
            except Exception as e:
                logger.error(f"Code generation error: {str(e)}", exc_info=True)
                st.error(f"❌ Generation failed: {str(e)}")

    def _prepare_workflow_state(self) -> Optional[WorkflowState]:
        """
        Prepare the workflow state for code generation.
        
        Returns:
            WorkflowState if preparation is successful, None otherwise
        """
        try:
            # Prepare generation parameters based on mode
            mode = st.session_state.get("error_selection_mode", "random")
            
            # Initialize or get workflow state
            if not hasattr(st.session_state, 'workflow_state') or st.session_state.workflow_state is None:
                st.session_state.workflow_state = WorkflowState()
            
            # Get user level from session state or use default
            user_level = st.session_state.get("user_level", "medium")
            params = self._get_level_parameters(user_level)
            
            # Update workflow state with parameters
            workflow_state = st.session_state.workflow_state
            workflow_state.code_length = params["code_length"]
            workflow_state.difficulty_level = params["difficulty"]
            workflow_state.error_count_start = params["error_count_start"]
            workflow_state.error_count_end = params["error_count_end"]  
            
            if mode == "random":
                # Random mode: use selected categories
                selected_categories = st.session_state.get("selected_categories", [])
                if not selected_categories:
                    st.error("❌ Please select at least one category in Random mode")
                    return None
                
                # Format for workflow
                categories_dict = {"java_errors": selected_categories}
                workflow_state.selected_error_categories = categories_dict
                workflow_state.selected_specific_errors = []
                
                logger.debug(f"Random mode: Selected categories: {selected_categories}")
            else:
                # Advanced mode: use specific errors
                selected_specific_errors = st.session_state.get("selected_specific_errors", [])
                if not selected_specific_errors:
                    st.error("❌ Please select at least one specific error in Advanced mode")
                    return None
                
                # Update error usage tracking
                for error in selected_specific_errors:
                    error_code = error.get("error_code", "")
                    if error_code:
                        self._update_error_usage(error_code, action_type='practiced')
                
                workflow_state.selected_error_categories = {"java_errors": []}
                workflow_state.selected_specific_errors = selected_specific_errors
                
                logger.debug(f"Advanced mode: Selected {len(selected_specific_errors)} specific errors")
            
            # Reset workflow state for fresh generation
            workflow_state.current_step = "generate"
            workflow_state.evaluation_attempts = 0
            workflow_state.evaluation_result = None
            workflow_state.error = None
            
            return workflow_state
            
        except Exception as e:
            logger.error(f"Error preparing workflow state: {str(e)}")
            st.error(f"❌ Failed to prepare generation parameters: {str(e)}")
            return None

    def _execute_code_generation_workflow(self, workflow_state: WorkflowState) -> WorkflowState:
        """
        Execute the code generation through the LangGraph workflow system.
        
        Args:
            workflow_state: Prepared workflow state
            
        Returns:
            Updated workflow state after execution
        """
        try:
            logger.debug("Executing code generation through compiled LangGraph workflow")
            
            # Use the workflow manager to execute code generation
            updated_state = self.workflow_manager.execute_code_generation_workflow(workflow_state)
            return updated_state
                
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            workflow_state.error = f"Workflow execution failed: {str(e)}"
            return workflow_state

    def _safe_get_state_value(self, state, key: str, default=None):
        """
        Safely get a value from a state object, handling both dict-like and attribute access.
        
        Args:
            state: State object (could be WorkflowState, dict, or AddableValuesDict)
            key: Key to access
            default: Default value if key not found
            
        Returns:
            Value from state or default
        """
        try:
            # Try attribute access first (for WorkflowState objects)
            if hasattr(state, key):
                return getattr(state, key)
            
            # Try dictionary access (for dict-like objects)
            if hasattr(state, '__getitem__'):
                try:
                    return state[key]
                except (KeyError, TypeError):
                    pass
            
            # Try get method (for dict-like objects)
            if hasattr(state, 'get'):
                return state.get(key, default)
            
            return default
            
        except Exception as e:
            logger.warning(f"Error accessing key '{key}' from state: {str(e)}")
            return default

    def _convert_state_to_workflow_state(self, state) -> WorkflowState:
        """
        Convert a state object (potentially AddableValuesDict) to a WorkflowState object.
        
        Args:
            state: State object from LangGraph workflow
            
        Returns:
            WorkflowState object
        """
        try:
            # If it's already a WorkflowState, return as-is
            if isinstance(state, WorkflowState):
                return state
            
            # If it's dict-like, extract all the fields
            state_dict = {}
            
            # Define all possible WorkflowState fields
            workflow_state_fields = [
                'current_step', 'workflow_phase', 'code_length', 'difficulty_level', 'domain',
                'error_count_start', 'error_count_end', 'selected_error_categories',
                'selected_specific_errors', 'code_snippet', 'original_error_count',
                'evaluation_attempts', 'max_evaluation_attempts', 'evaluation_result',
                'code_generation_feedback', 'pending_review', 'current_iteration',
                'max_iterations', 'review_sufficient', 'review_history',
                'comparison_report', 'error', 'final_summary'
            ]
            
            # Extract each field
            for field in workflow_state_fields:
                value = self._safe_get_state_value(state, field)
                if value is not None:
                    state_dict[field] = value
            
            # Create and return new WorkflowState
            return WorkflowState(**state_dict)
            
        except Exception as e:
            logger.error(f"Error converting state to WorkflowState: {str(e)}")
            # Return a minimal WorkflowState with error
            return WorkflowState(error=f"State conversion failed: {str(e)}")

    def _handle_generation_result(self, updated_state):
        """
        Handle the result of code generation.
        FIXED: Proper handling of LangGraph state objects using safe access methods.
        
        Args:
            updated_state: The updated workflow state after generation
        """
        try:
            # Convert the state to a proper WorkflowState object for session storage
            workflow_state = self._convert_state_to_workflow_state(updated_state)
            
            # Update session state with result first (important for preserving data)
            st.session_state.workflow_state = workflow_state

            # Use safe access methods to check for code snippet and error
            code_snippet = self._safe_get_state_value(updated_state, 'code_snippet')
            error = self._safe_get_state_value(updated_state, 'error')
            
            has_code_snippet = code_snippet is not None
            has_error = error is not None and error != ""
           
            if has_code_snippet:
                logger.debug("Code generation completed successfully")               
                if has_error:                    
                    st.warning(f"⚠️ Code generated with warnings: {error}")
                    st.info("✅ Code generation completed. You can proceed to review the code.")
                else:
                    st.success("✅ Code generated successfully!") 
                st.session_state.active_tab = 1
                st.rerun()                
            elif has_error:               
                st.error(f"❌ Generation failed: {error}")
                logger.error(f"Code generation failed with error: {error}")
                
            else:               
                st.error("❌ Failed to generate code. Please try again.")
                logger.warning("Code generation completed but no code snippet was created and no error message")                    
        except Exception as e:
            logger.error(f"Error handling generation result: {str(e)}")
            st.error(f"❌ Error processing generation result: {str(e)}")

    def _build_workflow_state(self, **kwargs):
        """Helper to build a WorkflowState object for code generation."""
        # Use current session state as base if it exists, otherwise create new
        if hasattr(st.session_state, 'workflow_state') and st.session_state.workflow_state:
            state_dict = dict(st.session_state.workflow_state.dict())
        else:
            state_dict = {}
        
        # Update with provided kwargs
        state_dict.update(kwargs)
        
        # Create new WorkflowState with updated values
        return WorkflowState(**state_dict)