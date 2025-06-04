import streamlit as st
import os
import logging
import time
from typing import Dict, List, Any, Optional
from data.database_error_repository import DatabaseErrorRepository
from utils.language_utils import t, get_current_language
from static.css_utils import load_css

logger = logging.getLogger(__name__)

class ErrorExplorerUI:
    """UI component for exploring Java errors with examples and solutions."""
    
    def __init__(self, workflow=None):
        """Initialize the Error Explorer UI."""
        self.repository = DatabaseErrorRepository()
        self.workflow = workflow  # Add workflow for practice functionality
        
        # Initialize session state
        if "selected_error_code" not in st.session_state:
            st.session_state.selected_error_code = None
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
        self._render_enhanced_header()
        
        # Search and filter section
        self._render_enhanced_search_filters()
        
        # Main content area
        self._render_error_content()
    
    def _render_enhanced_header(self):
        """Render an enhanced professional header with branding and statistics."""
        try:
            stats = self.repository.get_error_statistics()
            total_errors = stats.get('total_errors', 0)
            total_categories = stats.get('total_categories', 0)
            errors_by_category = stats.get('errors_by_category', {})
        except Exception as e:
            logger.debug(f"Could not get database statistics: {str(e)}")
            total_errors = 0
            total_categories = 0
            errors_by_category = {}
        
        st.markdown(f"""
        <div class="error-explorer-header-compact">
            <div class="header-content-compact">
                <div class="title-section-compact">
                    <h1>🔍 {t('error_explorer')}</h1>
                    <p class="subtitle-compact">{t('explore_comprehensive_error_library')}</p>
                </div>
                <div class="stats-section-compact">
                    <div class="stat-card-compact">
                        <div class="stat-number-compact">{total_errors}</div>
                        <div class="stat-label-compact">Errors</div>
                    </div>
                    <div class="stat-card-compact">
                        <div class="stat-number-compact">{total_categories}</div>
                        <div class="stat-label-compact">Categories</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_enhanced_search_filters(self):
        """Render enhanced search and filter controls with professional styling."""
        st.markdown('<div class="search-filter-container">', unsafe_allow_html=True)
        
        # Search section header
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">🔍</div>
            <div>
                <div class="section-title">Search & Filter Errors</div>
                <div class="section-subtitle">Find specific errors or browse by category and difficulty</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Main search and filter controls
        col1, col2, col3 = st.columns([4, 2, 2])
        
        with col1:
            search_term = st.text_input(
                "",
                placeholder="🔍 Search errors by name or description...",
                key="error_search",
                help="Search for specific error patterns, keywords, or descriptions"
            )
        
        with col2:
            categories = self._get_categories()
            selected_category = st.selectbox(
                "📂 Category",
                options=["All Categories"] + categories,
                key="category_filter",
                help="Filter by error category"
            )
        
        with col3:
            difficulty_levels = ["All Levels", "Easy", "Medium", "Hard"]
            selected_difficulty = st.selectbox(
                "⚡ Difficulty",
                options=difficulty_levels,
                key="difficulty_filter",
                help="Filter by difficulty level"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Store filters in session state
        st.session_state.search_term = search_term
        st.session_state.selected_category = selected_category
        st.session_state.selected_difficulty = selected_difficulty

    def _render_error_content(self):
        """Render the main error content with professional cards."""
        # Get filtered errors
        filtered_errors = self._get_filtered_errors()
        
        if not filtered_errors:
            self._render_no_results()
            return
        
        # Results count with smaller, more compact styling
        st.markdown(f"""
        <div style="text-align: center; margin: 10px 0;">
            <span style="font-size: 0.9em; color: #6c757d; background: #f8f9fa; padding: 4px 12px; border-radius: 15px;">
                {len(filtered_errors)} {t("errors_found")}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Render professional error cards
        self._render_professional_error_cards(filtered_errors)
    
    def _render_professional_error_cards(self, filtered_errors: List[Dict[str, Any]]):
        """Render errors in professional card format with integrated content and buttons."""
        errors_by_category = self._group_errors_by_category(filtered_errors)
        
        for category_name, errors in errors_by_category.items():
            st.markdown(f'<h3 class="category-title">{category_name} <span class="error-count">({len(errors)})</span></h3>', 
                       unsafe_allow_html=True)
            
            for error in errors:
                self._render_optimized_error_card(error)
    
    def _render_optimized_error_card(self, error: Dict[str, Any]):
        """Render an optimized error card with expanders for examples."""
        error_name = error.get(t("error_name"), "Unknown Error")
        description = error.get(t("description"), "")
        implementation_guide = error.get(t("implementation_guide"), "")
        difficulty = error.get('difficulty_level', 'medium')
        error_code = error.get('error_code', f"error_{hash(error_name) % 10000}")
        
        # Create the professional card container with CSS class
        card_container = st.container()
        with card_container:
            # Add CSS class to the container
            st.markdown(f"""
            <style>
            .element-container:has(> .stContainer) {{
                background: linear-gradient(135deg, #ffffff 0%, #f8fafe 100%);
                border: 2px solid #e1e8f0;
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }}
            </style>
            """, unsafe_allow_html=True)
            
            # Card header
            st.markdown(f"""
            <div class="card-header" style="margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #f1f3f4;">
                <div class="error-title-section">
                    <h4 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 1.2rem; font-weight: 600; display: flex; align-items: center; line-height: 1.3;">
                        <span style="margin-right: 8px;">🔧</span>
                        {error_name}
                    </h4>
                    <div style="display: flex; gap: 8px; align-items: center; margin-top: 8px; flex-wrap: wrap;">
                        <span style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 74, 188, 0.05)); color: #667eea; padding: 4px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 500; border: 1px solid rgba(102, 126, 234, 0.2); font-family: 'Courier New', monospace;">{error_code}</span>
                        <span class="difficulty-badge {difficulty}" style="color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); border: none; background: {'linear-gradient(135deg, #28a745, #20c997)' if difficulty == 'easy' else 'linear-gradient(135deg, #ffc107, #ffb347)' if difficulty == 'medium' else 'linear-gradient(135deg, #dc3545, #e74c3c)'}; {'color: #212529;' if difficulty == 'medium' else ''}">{difficulty.title()}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Get examples for the expander
            examples = self.repository.get_error_examples(error_name)
            
            # Single expander containing description, fix guide, and examples
            with st.expander("📝 **View Code Examples**", expanded=False):
                # Description
                st.markdown("**📋 Description:**")
                st.info(description)
                
                # Implementation guide if available
                if implementation_guide:
                    st.markdown("**💡 How to Fix This Error:**")
                    st.success(implementation_guide)
                
                # Code examples
                self._render_code_examples(examples)
            
                # Practice button at the bottom of the card
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Show explanation if available
                    explanation = examples.get("explanation", "")
                    if explanation:
                        st.markdown("**💡 Key Points:**")
                        st.caption(explanation)
                
                with col2:
                    if st.button(
                        "🎯 Practice", 
                        key=f"practice_{error_code}", 
                        use_container_width=True,
                        type="primary",
                        help="Generate practice code with this error type"
                    ):
                        self._handle_practice_error(error)
        
        # Add spacing between cards
        st.markdown("<br>", unsafe_allow_html=True)
    
    def _render_code_examples(self, examples: Dict[str, Any]):
        """Render code examples in a structured format."""
        # Wrong examples section
        if examples.get("wrong_examples"):
            st.markdown("#### ❌ **Problematic Code Examples**")
            for i, example in enumerate(examples["wrong_examples"][:3], 1):  # Show up to 3 examples
                if len(examples["wrong_examples"]) > 1:
                    st.markdown(f"**Example {i}:**")
                st.code(example, language="java")
                if i < len(examples["wrong_examples"][:3]):
                    st.markdown("---")
        
        # Correct examples section
        if examples.get("correct_examples"):
            st.markdown("#### ✅ **Corrected Code Examples**")
            for i, example in enumerate(examples["correct_examples"][:3], 1):  # Show up to 3 examples
                if len(examples["correct_examples"]) > 1:
                    st.markdown(f"**Example {i}:**")
                st.code(example, language="java")
                if i < len(examples["correct_examples"][:3]):
                    st.markdown("---")
        
        # Comparison tip
        if examples.get("wrong_examples") and examples.get("correct_examples"):
            st.info("💡 **Tip:** Compare the problematic and corrected examples to understand the differences!")
    

    
    def _handle_practice_error(self, error: Dict[str, Any]):
        """Handle practice error by generating code with LangGraph and starting review workflow."""
        if not self.workflow:
            st.error("Practice mode requires workflow integration. Please contact administrator.")
            return
        
        error_name = error.get(t("error_name"), "Unknown Error")
        error_code = error.get('error_code', '')
        
        try:
            # Show immediate feedback
            st.success(f"🎯 Generating practice code with {error_name}...")
            
            # Create a progress bar for user feedback
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Reset workflow state for new practice session
            progress_bar.progress(20)
            status_text.text("Preparing practice session...")
            
            # Reset workflow state
            from state_schema import WorkflowState
            st.session_state.workflow_state = WorkflowState()
            
            # Step 2: Set up error-specific generation
            progress_bar.progress(40)
            status_text.text("Configuring error parameters...")
            
            # Configure the workflow for this specific error
            state = st.session_state.workflow_state
            
            # Set up the error selection for targeted generation
            state.selected_categories = {"java_errors": [error.get('category', 'Other')]}
            state.specific_errors = [error]  # Focus on this specific error
            state.difficulty_level = error.get('difficulty_level', 'medium')
            state.current_step = 'generate'
            
            # Step 3: Generate code with the specific error
            progress_bar.progress(60)
            status_text.text("Generating code with error...")
            
            # Use the workflow to generate code
            result = self.workflow.generate_code_with_errors(
                selected_categories=state.selected_categories,
                specific_errors=state.specific_errors,
                difficulty=state.difficulty_level
            )
            
            if result.get('success', False):
                # Step 4: Set up the generated code in workflow state
                progress_bar.progress(80)
                status_text.text("Setting up practice environment...")
                
                code_content = result.get('code_content', '')
                known_errors = result.get('known_errors', [])
                
                # Create code snippet object
                from dataclasses import dataclass
                from typing import List as ListType
                
                @dataclass
                class CodeSnippet:
                    content: str
                    known_errors: ListType[Dict[str, Any]]
                    language: str = "java"
                    difficulty: str = "medium"
                
                state.code_snippet = CodeSnippet(
                    content=code_content,
                    known_errors=known_errors,
                    language="java",
                    difficulty=state.difficulty_level
                )
                
                # Step 5: Complete setup
                progress_bar.progress(100)
                status_text.text("Practice session ready!")
                
                # Track usage in database
                try:
                    self.repository.update_error_usage(
                        error_code=error_code,
                        action_type='practiced',
                        context={
                            'source': 'error_explorer', 
                            'method': 'practice_button',
                            'generated_code': True
                        }
                    )
                except Exception as e:
                    logger.debug(f"Could not track error usage: {str(e)}")
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Show success message and navigate
                st.success(f"✅ Practice code generated successfully!")
                st.info(f"💡 Navigate to the **Review** tab to start analyzing the code with {error_name}")
                
                # Set the active tab to review (index 1)
                st.session_state.active_tab = 1
                st.session_state["force_tab_switch"] = True
                
                # Brief pause for user to read the message
                time.sleep(2)
                st.rerun()
                
            else:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Failed to generate practice code: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in practice mode: {str(e)}")
            st.error(f"❌ Error setting up practice session: {str(e)}")
            st.info("Please try again or contact support if the problem persists.")
    
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
            selected_category = st.session_state.get('selected_category', 'All Categories')
            if selected_category == 'All Categories':
                categories = self._get_categories()
            else:
                categories = [selected_category]
            
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
        selected_difficulty = st.session_state.get('selected_difficulty', 'All Levels')
        if selected_difficulty != 'All Levels':
            difficulty_map = {
                "Easy": "easy",
                "Medium": "medium", 
                "Hard": "hard"
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
    
    def _render_no_results(self):
        """Render enhanced no results message."""
        st.markdown("""
        <div class="no-results">
            <div class="no-results-icon">🔍</div>
            <h3>No Errors Found</h3>
            <p>We couldn't find any errors matching your search criteria.</p>
            <div class="no-results-suggestions">
                <h4>Try these suggestions:</h4>
                <ul>
                    <li>Check your spelling and try different keywords</li>
                    <li>Broaden your search by selecting "All Categories"</li>
                    <li>Try searching for common terms like "null", "loop", or "syntax"</li>
                    <li>Clear the search box to browse all errors</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_error_explorer(workflow=None):
    """Main function to render the error explorer with workflow integration."""
    explorer = ErrorExplorerUI(workflow=workflow)
    explorer.render()