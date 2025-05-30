"""
Code Generator UI component for Java Peer Review Training System.

This module provides a professional UI for configuring and generating Java code snippets
with intentional errors for review practice.
"""

import streamlit as st
import logging
from typing import List, Dict, Any
from utils.language_utils import t

# Configure logging
logger = logging.getLogger(__name__)

class CodeGeneratorUI:
    """
    Professional UI component for Java code generation with clean layout and intuitive workflow.
    """
    
    def __init__(self, workflow, code_display_ui):
        """
        Initialize the CodeGeneratorUI.
        
        Args:
            workflow: JavaCodeReviewGraph workflow instance
            code_display_ui: CodeDisplayUI instance for displaying generated code
        """
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

    def _render_header(self):
        """Render the professional header with branding and description."""
        st.markdown("""
        <div class="generate-header">
            <h2>🔧 Code Generation Workshop</h2>
            <p>Configure and generate Java code snippets with intentional errors for review practice</p>
        </div>
        """, unsafe_allow_html=True)
    
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
        
        # Error selection based on mode
        self._render_error_selection_interface()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
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
                # Clear previous selections when switching modes
                st.session_state.selected_categories = []
                st.session_state.selected_specific_errors = []
        
        with col2:
            if st.button("🎯 Advanced Mode", key="advanced_mode", use_container_width=True):
                st.session_state.error_selection_mode = "advanced"
                # Clear previous selections when switching modes
                st.session_state.selected_categories = []
                st.session_state.selected_specific_errors = []
        
        # Initialize mode if not set
        if "error_selection_mode" not in st.session_state:
            st.session_state.error_selection_mode = "random"
        
        # Display current mode
        mode = st.session_state.error_selection_mode
        if mode == "random":
            st.info("🎲 **Random Mode**: Select specific errors from the available list")
        else:
            st.info("🎯 **Advanced Mode**: Choose error categories and specific errors within each category")

    def _render_error_selection_interface(self):
        """Render the error selection interface based on current mode."""
        mode = st.session_state.get("error_selection_mode", "random")
        
        if mode == "random":
            self._render_random_error_selection()
        else:
            self._render_advanced_error_selection()

    def _render_random_error_selection(self):
        """Render error selection for random mode - show all available errors in a simple list."""
        st.markdown("""
        <div class="error-selection-section">
            <div class="selection-header">
                <h4>🎯 Select Errors to Practice</h4>
                <p>Choose specific errors you want to practice identifying</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Load all available errors
        try:
            all_errors = self._load_all_errors()
            
            if not all_errors:
                st.warning("No errors available. Please check your database connection.")
                return
            
            # Initialize selected errors
            if "selected_specific_errors" not in st.session_state:
                st.session_state.selected_specific_errors = []
            
            # Create columns for better layout
            cols = st.columns(2)
            
            for idx, error in enumerate(all_errors):
                col = cols[idx % 2]
                
                with col:
                    category = error.get('category', 'Unknown')
                    error_name = error.get('error_name', 'Unknown Error')
                    description = error.get('description', '')
                    
                    # Create a unique key for this error
                    error_key = f"{category}_{error_name}"
                    
                    # Check if this error is selected
                    is_selected = error in st.session_state.selected_specific_errors
                    
                    # Create a checkbox for this error
                    if st.checkbox(
                        f"**{error_name}**",
                        value=is_selected,
                        key=f"error_select_{error_key}",
                        help=f"Category: {category}\nDescription: {description}"
                    ):
                        # Add to selected if not already there
                        if error not in st.session_state.selected_specific_errors:
                            st.session_state.selected_specific_errors.append(error)
                    else:
                        # Remove from selected if unchecked
                        if error in st.session_state.selected_specific_errors:
                            st.session_state.selected_specific_errors.remove(error)
            
            # Display selection summary
            selected_count = len(st.session_state.selected_specific_errors)
            if selected_count > 0:
                st.success(f"✅ {selected_count} error(s) selected")
            else:
                st.info("Please select at least one error to generate code")
                
        except Exception as e:
            st.error(f"Error loading errors: {str(e)}")

    def _render_advanced_error_selection(self):
        """Render error selection for advanced mode - show categories first, then errors within each."""
        st.markdown("""
        <div class="error-selection-section">
            <div class="selection-header">
                <h4>🎯 Advanced Error Selection</h4>
                <p>First select categories, then choose specific errors within each category</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Step 1: Category Selection
        self._render_category_selection()
        
        # Step 2: Error Selection within selected categories
        selected_categories = st.session_state.get("selected_categories", [])
        if selected_categories:
            self._render_errors_in_categories(selected_categories)

    def _render_category_selection(self):
        """Render the category selection interface with professional styling."""
        st.markdown("""
        <div class="category-selection-enhanced">
            <div class="selection-header">
                <h4>📂 Step 1: Select Error Categories</h4>
                <p>Choose the types of errors you want to practice identifying</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Load error categories
        categories = self._load_error_categories()
        print(f"Loaded {len(categories)} categories from database")
        # Initialize selected categories
        if "selected_categories" not in st.session_state:
            st.session_state.selected_categories = []
        
        # Category grid
        self._render_category_grid(categories)

    def _render_errors_in_categories(self, selected_categories):
        """Render specific error selection within the selected categories."""
        st.markdown("""
        <div class="specific-error-selection">
            <div class="selection-header">
                <h4>🔍 Step 2: Select Specific Errors</h4>
                <p>Choose specific errors from your selected categories</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize selected specific errors
        if "selected_specific_errors" not in st.session_state:
            st.session_state.selected_specific_errors = []
        
        # Load errors for selected categories
        try:
            for category in selected_categories:
                st.markdown(f"### {self._get_category_icon(category)} {category}")
                
                category_errors = self._load_errors_by_category(category)
                
                if not category_errors:
                    st.info(f"No errors found in category: {category}")
                    continue
                
                # Create columns for better layout
                cols = st.columns(2)
                
                for idx, error in enumerate(category_errors):
                    col = cols[idx % 2]
                    
                    with col:
                        error_name = error.get('error_name', 'Unknown Error')
                        description = error.get('description', '')
                        
                        # Create a unique key for this error
                        error_key = f"{category}_{error_name}_{idx}"
                        
                        # Check if this error is selected
                        is_selected = error in st.session_state.selected_specific_errors
                        
                        # Create a checkbox for this error
                        if st.checkbox(
                            f"**{error_name}**",
                            value=is_selected,
                            key=f"specific_error_{error_key}",
                            help=description
                        ):
                            # Add to selected if not already there
                            if error not in st.session_state.selected_specific_errors:
                                st.session_state.selected_specific_errors.append(error)
                        else:
                            # Remove from selected if unchecked
                            if error in st.session_state.selected_specific_errors:
                                st.session_state.selected_specific_errors.remove(error)
                
                st.markdown("---")
            
            # Display selection summary
            selected_count = len(st.session_state.selected_specific_errors)
            if selected_count > 0:
                st.success(f"✅ {selected_count} specific error(s) selected from {len(selected_categories)} categories")
            else:
                st.info("Please select specific errors from the categories above")
                
        except Exception as e:
            st.error(f"Error loading category errors: {str(e)}")

    def _load_all_errors(self) -> List[Dict]:
        """Load all available errors from the database."""
        try:
            from db.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            return db_manager.get_all_errors()
        except Exception as e:
            logger.error(f"Error loading all errors: {str(e)}")
            return []

    def _load_errors_by_category(self, category_name: str) -> List[Dict]:
        """Load errors for a specific category."""
        try:
            from db.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            return db_manager.get_errors_by_category(category_name)
        except Exception as e:
            logger.error(f"Error loading errors for category {category_name}: {str(e)}")
            return []

    def _render_category_grid(self, categories: List[Dict]):
        """Render categories in a professional grid layout."""
        if not categories:
            st.warning("No error categories available")
            return
        
        # Create grid layout
        cols_per_row = 3
        rows = [categories[i:i + cols_per_row] for i in range(0, len(categories), cols_per_row)]
        
        for row in rows:
            cols = st.columns(len(row))
            for idx, category in enumerate(row):
                with cols[idx]:
                    category_name = category.get('category_name', 'Unknown')
                    category_icon = self._get_category_icon(category_name)
                    
                    # Check if category is selected
                    is_selected = category_name in st.session_state.selected_categories
                    
                    # Category card styling
                    card_class = "category-card-selected" if is_selected else "category-card"
                    
                    if st.button(
                        f"{category_icon} {category_name}",
                        key=f"cat_{category_name}",
                        use_container_width=True
                    ):
                        self._toggle_category(category_name)

    def _can_generate(self) -> bool:
        """Check if we can generate code."""
        mode = st.session_state.get("error_selection_mode", "random")
        selected_errors = st.session_state.get("selected_specific_errors", [])
        
        # For both modes, we need at least one specific error selected
        return len(selected_errors) > 0

    def _handle_code_generation(self):
        """Handle the code generation process."""
        with st.spinner("🔧 Generating your Java code challenge..."):
            try:
                # Get selected errors
                selected_errors = st.session_state.get("selected_specific_errors", [])
                
                if not selected_errors:
                    st.error("Please select at least one error before generating code.")
                    return
                
                # Prepare generation parameters
                mode = st.session_state.get("error_selection_mode", "random")
                
                # Trigger workflow with selected specific errors
                result = self.workflow.invoke({
                    "selected_specific_errors": selected_errors,
                    "generation_mode": mode,
                    "code_length": "medium",  # Can be made configurable
                    "difficulty_level": "medium"  # Can be made configurable
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
    
    def _load_error_categories(self) -> List[Dict]:
        """Load error categories from the database."""
        try:
            from db.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            return db_manager.get_error_categories()
        except Exception as e:
            logger.error(f"Error loading categories: {str(e)}")
            return []
    
    def _get_category_icon(self, category_name: str) -> str:
        """Get icon for category."""
        icons = {
            "Logical Errors": "🧠",
            "Syntax Errors": "❌", 
            "Standard Violations": "📏",
            "Java-Specific Errors": "☕",
            "Security Issues": "🔒",
            "Performance Issues": "⚡"
        }
        return icons.get(category_name, "🐛")
    
    def _toggle_category(self, category_name: str):
        """Toggle category selection."""
        if "selected_categories" not in st.session_state:
            st.session_state.selected_categories = []
        
        if category_name in st.session_state.selected_categories:
            st.session_state.selected_categories.remove(category_name)
        else:
            st.session_state.selected_categories.append(category_name)
    
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