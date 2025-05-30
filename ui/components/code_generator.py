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
        st.markdown("""
        <div class="section-header">
            <span class="section-icon">⚙️</span>
            <div>
                <h3 class="section-title">Configuration</h3>
                <p class="section-subtitle">Set up your code generation parameters</p>
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
        st.markdown("""
        <div class="generate-button-section">
            <h4>🚀 Ready to Generate</h4>
            <p>Click below to generate a Java code snippet with your selected configuration</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Check if we can generate
        can_generate = self._can_generate()
        
        if can_generate:
            if st.button(
                "🔧 Generate Code Problem",
                key="generate_code_main",
                type="primary",
                use_container_width=True
            ):
                self._handle_code_generation()
        else:
            st.error("⚠️ Please select at least one error category in Advanced Mode")
            st.button(
                "🔧 Generate Code Problem",
                key="generate_code_disabled",
                disabled=True,
                use_container_width=True
            )

    def _render_mode_selection(self):
        """Render the error selection mode with professional styling."""
        st.markdown("""
        <div class="mode-selector-container">
            <div class="mode-selector-header">
                <h4>Error Selection Mode</h4>
                <p>Choose how you want to select errors for the generated code</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mode selection with custom styling
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎲 Random Mode", key="random_mode", use_container_width=True):
                st.session_state.error_selection_mode = "random"
        
        with col2:
            if st.button("🎯 Advanced Mode", key="advanced_mode", use_container_width=True):
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
        st.markdown("""
        <div class="parameters-display">
            <div class="parameters-header">
                <h4>📊 Generation Parameters</h4>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Parameter mapping based on user level
        params = self._get_level_parameters(user_level)
        
        # Display parameters in a grid
        cols = st.columns(4)
        
        with cols[0]:
            st.markdown(f"""
            <div class="parameter-card">
                <span class="parameter-icon">📏</span>
                <div class="parameter-label">Code Length</div>
                <div class="parameter-value">{params['code_length'].title()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown(f"""
            <div class="parameter-card">
                <span class="parameter-icon">⭐</span>
                <div class="parameter-label">Difficulty</div>
                <div class="parameter-value">{params['difficulty'].title()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown(f"""
            <div class="parameter-card">
                <span class="parameter-icon">🐛</span>
                <div class="parameter-label">Error Count</div>
                <div class="parameter-value">{params['error_count']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[3]:
            st.markdown(f"""
            <div class="parameter-card">
                <span class="parameter-icon">👤</span>
                <div class="parameter-label">Your Level</div>
                <div class="parameter-value">{user_level.title()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="parameters-note">
            💡 These parameters are automatically optimized based on your experience level
        </div>
        """, unsafe_allow_html=True)

    def _render_selection_interface(self):
        """Render the category/error selection interface."""
        mode = st.session_state.get("error_selection_mode", "random")
        
        if mode == "random":
            self._render_category_selection()

    def _render_category_selection(self):
        """Render the category selection interface with professional styling."""
        st.markdown("""
        <div class="category-selection-enhanced">
            <div class="selection-header">
                <h4>🎯 Select Error Categories</h4>
                <p>Choose the types of errors you want to practice identifying</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Help section
        st.markdown("""
        <div class="selection-help">
            <span class="selection-help-icon">💡</span>
            <strong>Tip:</strong> Select multiple categories to create more challenging review scenarios
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
            st.warning("No categories available")
        
        # Selected categories display
        self._render_selected_categories()


    def _get_category_icon(self, category_name: str) -> str:
        """Get icon for category based on name."""
        icon_mapping = {
            "syntax_errors": "🔤",
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
        return icon_mapping.get(category_name.lower(), "🐛")

    def _toggle_category(self, category_name: str):
        """Toggle category selection."""
        if "selected_categories" not in st.session_state:
            st.session_state.selected_categories = []
        
        if category_name in st.session_state.selected_categories:
            st.session_state.selected_categories.remove(category_name)
        else:
            st.session_state.selected_categories.append(category_name)
            
    def _render_selected_categories(self):
        """Render the selected categories display."""
        selected = st.session_state.get("selected_categories", [])
        
        if selected:
            st.markdown("""
            <div class="selected-categories-enhanced">
                <div class="selected-categories-header">
                    <h4>Selected Categories</h4>
                    <span class="selected-categories-count">{}</span>
                </div>
            </div>
            """.format(len(selected)), unsafe_allow_html=True)
            
            # Display selected categories as tags
            cols = st.columns(min(len(selected), 4))
            for i, category in enumerate(selected):
                col_idx = i % len(cols)
                with cols[col_idx]:
                    icon = self._get_category_icon(category)
                    st.markdown(f"""
                    <div class="selected-category-tag">
                        <span class="category-tag-icon">{icon}</span>
                        {category}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="no-selection-message">
                🎯 Select at least one error category to generate code
            </div>
            """, unsafe_allow_html=True)

    def _render_category_grid(self, categories: List[str]):
        """Render categories in a professional grid layout."""
        st.markdown('<div class="problem-area-grid-enhanced">', unsafe_allow_html=True)
        
        for category_name in categories:
            # category is now a string, not a dictionary
            description = f"Practice with {category_name} related errors"
            icon = self._get_category_icon(category_name)
            
            is_selected = category_name in st.session_state.get("selected_categories", [])
            selected_class = "selected" if is_selected else ""
            
            if st.button(
                f"{icon} {category_name}",
                key=f"category_{category_name}",
                help=description,
                use_container_width=True
            ):
                self._toggle_category(category_name)
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

    def _can_generate(self) -> bool:
        """Check if we can generate code."""
        mode = st.session_state.get("error_selection_mode", "random")
        if mode == "random":
            return True
        else:
            return len(st.session_state.get("selected_categories", [])) > 0

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

    def _render_header(self):
        """Render the professional header with branding and description."""
        st.markdown("""
        <div class="generate-header">
            <h2>🔧 Code Generation Workshop</h2>
            <p>Configure and generate Java code snippets with intentional errors for review practice</p>
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