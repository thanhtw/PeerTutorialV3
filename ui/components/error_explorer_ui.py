import streamlit as st
import os
import logging
import time
from typing import Dict, List, Any, Optional
from data.database_error_repository import DatabaseErrorRepository
from utils.language_utils import t, get_current_language
from static.css_utils import load_css
from utils.code_utils import _get_category_icon, _get_difficulty_icon

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
        """Load CSS styles for the Error Explorer UI with safe encoding handling."""
        try:
            # Get the current directory and construct path to CSS files
            current_dir = os.path.dirname(os.path.abspath(__file__))
            css_dir = os.path.join(current_dir, "..", "..", "static", "css", "error_explorer")
            from static.css_utils import load_css_safe
            result = load_css_safe(css_directory=css_dir)
        except Exception as e:
            logger.error(f"Error loading Error Explorer CSS: {str(e)}")
            # Continue without CSS - the app should still work
            st.warning("Some styling may not be available due to CSS loading issues.")

    def render(self):
        """Render the complete error explorer interface."""
        # Professional header
        self._render_header()
        
        # Search and filter section
        self._render_search_filters()
        
        # Main content area
        self._render_error_content()
    
    def _render_header(self):
        """Render an enhanced professional header with branding and statistics."""
        try:
            stats = self.repository.get_error_statistics()
            total_errors = stats.get('total_errors', 0)
            total_categories = stats.get('total_categories', 0)            
        except Exception as e:
            logger.debug(f"Could not get database statistics: {str(e)}")
            total_errors = 0
            total_categories = 0           
        
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
    
    def _render_search_filters(self):
        """Render enhanced search and filter controls with professional styling."""
        st.markdown('<div class="search-filter-container">', unsafe_allow_html=True)
        
        # Search section header
        st.markdown("""
        <div class="section-header">           
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
        
        # Render professional error cards
        self._render_error_cards(filtered_errors)
    
    def _render_error_cards(self, filtered_errors: List[Dict[str, Any]]):
        """Render errors in professional card format with consecutive container styling."""
        errors_by_category = self._group_errors_by_category(filtered_errors)
        
        for category_name, errors in errors_by_category.items():
            # Sort errors by difficulty within each category
            sorted_errors = self._sort_errors_by_difficulty(errors)
            
            # Category section with professional styling
            st.markdown(f"""
            <div class="category-section">
                <h3 class="category-title">
                    <span class="category-icon">{_get_category_icon(category_name.lower())}</span>
                    {category_name}
                    <span class="error-count">{len(sorted_errors)}</span>
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            for error in sorted_errors:
                self._render_consecutive_error_card(error)

    def _sort_errors_by_difficulty(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort errors by difficulty level (easy -> medium -> hard)."""
        difficulty_order = {'easy': 1, 'medium': 2, 'hard': 3}
        
        def get_difficulty_sort_key(error):
            difficulty = error.get('difficulty_level', 'medium').lower()
            return difficulty_order.get(difficulty, 2)  # Default to medium if unknown
        
        return sorted(errors, key=get_difficulty_sort_key)

    def _render_consecutive_error_card(self, error: Dict[str, Any]):
        """Render error card using a clean expander format with integrated title."""
        error_name = error.get(t("error_name"), "Unknown Error")
        description = error.get(t("description"), "")
        implementation_guide = error.get(t("implementation_guide"), "")
        difficulty = error.get('difficulty_level', 'medium')
        error_code = error.get('error_code', f"error_{hash(error_name) % 10000}")
        difficulty_text = difficulty.title()        
        examples = self.repository.get_error_examples(error_name)        
        expander_title = f" {_get_difficulty_icon(difficulty_text)} **{error_name}**"
        
        # Single professional expander with all content
        with st.expander(expander_title, expanded=False):
            # Description section with enhanced styling
            if description or implementation_guide:
              
                if description:
                    st.markdown("""
                    <div class="section-header-inline">
                        <h4 class="section-title">📋 Error Description</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f'<div class="description-content">{description}</div>', unsafe_allow_html=True)
                
                if implementation_guide:
                    st.markdown("""
                    <div class="section-header-inline">
                        <h4 class="section-title">💡 How to Fix</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f'<div class="solution-content">{implementation_guide}</div>', unsafe_allow_html=True)
                
            # Code examples section with improved layout
            if examples.get("wrong_examples") or examples.get("correct_examples"):
               
                st.markdown("""
                    <div class="section-header-inline">
                        <h4 class="section-title">💻 Code Example</h4>
                    </div>
                    """, unsafe_allow_html=True)
                # Create columns for side-by-side comparison when both exist
                if examples.get("wrong_examples") and examples.get("correct_examples"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("""
                        <div class="code-section-header error-header">
                            <h4 class="code-section-title">❌ Problematic Code</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, example in enumerate(examples["wrong_examples"][:2], 1):
                            if len(examples["wrong_examples"]) > 1:
                                st.markdown(f'<div class="example-label">Example {i}:</div>', unsafe_allow_html=True)
                            st.code(example, language="java")
                    
                    with col2:
                        st.markdown("""
                        <div class="code-section-header solution-header">
                            <h4 class="code-section-title">✅ Corrected Code</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, example in enumerate(examples["correct_examples"][:2], 1):
                            if len(examples["correct_examples"]) > 1:
                                st.markdown(f'<div class="example-label">Example {i}:</div>', unsafe_allow_html=True)
                            st.code(example, language="java")
                
                else:
                    # Single column layout when only one type exists
                    if examples.get("wrong_examples"):
                        st.markdown("""
                        <div class="code-section-header error-header">
                            <h4 class="code-section-title">❌ Problematic Code Examples</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, example in enumerate(examples["wrong_examples"][:3], 1):
                            if len(examples["wrong_examples"]) > 1:
                                st.markdown(f'<div class="example-label">Example {i}:</div>', unsafe_allow_html=True)
                            st.code(example, language="java")
                            if i < len(examples["wrong_examples"][:3]):
                                st.markdown('<hr class="example-divider">', unsafe_allow_html=True)
                    
                    if examples.get("correct_examples"):
                        st.markdown("""
                        <div class="code-section-header solution-header">
                            <h4 class="code-section-title">✅ Corrected Code Examples</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, example in enumerate(examples["correct_examples"][:3], 1):
                            if len(examples["correct_examples"]) > 1:
                                st.markdown(f'<div class="example-label">Example {i}:</div>', unsafe_allow_html=True)
                            st.code(example, language="java")
                            if i < len(examples["correct_examples"][:3]):
                                st.markdown('<hr class="example-divider">', unsafe_allow_html=True)
                
            
            col1, col2, col3 = st.columns([1, 5, 1])
            with col2:
                if st.button(
                    "🚀 Start Practice Session", 
                    key=f"practice_{error_code}", 
                    use_container_width=True,
                    type="primary",
                    help="Generate practice code with this error type"
                ):
                    self._handle_practice_error(error)
            
            # Close wrapper
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Add professional styling
            st.markdown("""
            <style>
            .error-card-content-wrapper {
                padding: 1rem;
                background: #fafafa;
                border-radius: 8px;
                margin: 0.5rem 0;
            }
            
            .error-metadata-section {
                background: white;
                padding: 1rem;
                border-radius: 6px;
                margin-bottom: 1.5rem;
                border-left: 4px solid #2196f3;
            }
            
            .metadata-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
            }
            
            .metadata-item {
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .metadata-label {
                font-weight: 600;
                color: #555;
                font-size: 0.9rem;
            }
            
            .metadata-value {
                font-weight: 500;
                color: #333;
                padding: 0.25rem 0.5rem;
                background: #f0f0f0;
                border-radius: 4px;
                font-size: 0.85rem;
            }
            
            .metadata-value.difficulty-easy { background: #e8f5e8; color: #2e7d32; }
            .metadata-value.difficulty-medium { background: #fff3e0; color: #f57c00; }
            .metadata-value.difficulty-hard { background: #ffebee; color: #d32f2f; }
            
            .error-overview-section {
                background: white;
                padding: 1.5rem;
                border-radius: 6px;
                margin-bottom: 1.5rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .section-header-inline {
                margin-bottom: 1rem;
                border-bottom: 2px solid #f0f0f0;
                padding-bottom: 0.5rem;
            }
            
            .section-title {
                margin: 0;
                color: #333;
                font-size: 1.1rem;
                font-weight: 600;
            }
            
            .description-content, .solution-content {
                padding: 1rem;
                border-radius: 4px;
                line-height: 1.6;
                margin-bottom: 1rem;
            }
            
            .description-content {
                background: #e3f2fd;
                border-left: 4px solid #2196f3;
                color: #1565c0;
            }
            
            .solution-content {
                background: #e8f5e8;
                border-left: 4px solid #4caf50;
                color: #2e7d32;
            }
            
            .code-examples-section {
                background: white;
                padding: 1.5rem;
                border-radius: 6px;
                margin-bottom: 1.5rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .code-section-header {
                margin-bottom: 1rem;
                padding: 0.75rem;
                border-radius: 4px;
            }
            
            .code-section-header.error-header {
                background: #ffebee;
                border-left: 4px solid #f44336;
            }
            
            .code-section-header.solution-header {
                background: #e8f5e8;
                border-left: 4px solid #4caf50;
            }
            
            .code-section-title {
                margin: 0;
                font-size: 1rem;
                font-weight: 600;
            }
            
            .example-label {
                font-weight: 600;
                color: #666;
                margin: 0.75rem 0 0.25rem 0;
                font-size: 0.9rem;
            }
            
            .example-divider {
                margin: 1.5rem 0;
                border: none;
                border-top: 1px solid #e0e0e0;
            }
            
            .key-points-section {
                background: white;
                padding: 1.5rem;
                border-radius: 6px;
                margin-bottom: 1.5rem;
                border-left: 4px solid #ff9800;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .key-points-content {
                background: #fff8e1;
                padding: 1rem;
                border-radius: 4px;
                margin-top: 0.5rem;
            }
            
            .explanation-text {
                line-height: 1.6;
                color: #555;
                font-style: italic;
            }
            
            .practice-section {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 6px;
                text-align: center;
                margin-bottom: 1rem;
            }
            
            .practice-header h4 {
                margin: 0 0 0.5rem 0;
                color: white;
            }
            
            .practice-description {
                margin: 0;
                opacity: 0.9;
                font-size: 0.9rem;
            }
            </style>
            """, unsafe_allow_html=True)

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