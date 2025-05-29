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
        
        # Category/Error selection based on mode
        self._render_selection_interface()
        
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
        
        if mode == "advanced":
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
        categories = self._load_error_categories()
        
        # Initialize selected categories
        if "selected_categories" not in st.session_state:
            st.session_state.selected_categories = []
        
        # Category grid
        self._render_category_grid(categories)
        
        # Selected categories display
        self._render_selected_categories()
    
    def _render_category_grid(self, categories: List[Dict]):
        """Render categories in a professional grid layout."""
        st.markdown('<div class="problem-area-grid-enhanced">', unsafe_allow_html=True)
        
        for category in categories:
            category_name = category.get("category_name", "Unknown")
            description = category.get("description", "No description available")
            icon = self._get_category_icon(category_name)
            
            is_selected = category_name in st.session_state.selected_categories
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
    
    def _can_generate(self) -> bool:
        """Check if we can generate code."""
        mode = st.session_state.get("error_selection_mode", "random")
        if mode == "random":
            return True
        else:
            return len(st.session_state.get("selected_categories", [])) > 0
    
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