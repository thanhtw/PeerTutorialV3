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
            st.warning(t("css_loading_warning"))

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
                        <div class="stat-label-compact">{t('errors')}</div>
                    </div>
                    <div class="stat-card-compact">
                        <div class="stat-number-compact">{total_categories}</div>
                        <div class="stat-label-compact">{t('categories')}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_search_filters(self):
        """Render enhanced search and filter controls with professional styling."""
        st.markdown('<div class="search-filter-container">', unsafe_allow_html=True)
        
        # Search section header
        st.markdown(f"""
        <div class="section-header">           
            <div>
                <div class="section-title">{t('search_and_filter_errors')}</div>
                <div class="section-subtitle">{t('find_specific_errors_or_browse')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Main search and filter controls
        col1, col2, col3 = st.columns([4, 2, 2])
        
        with col1:
            search_term = st.text_input(
                "",
                placeholder=f"🔍 {t('search_errors_placeholder')}",
                key="error_search",
                help=t('search_help_text')
            )
        
        with col2:
            categories = self._get_categories()
            selected_category = st.selectbox(
                f"📂 {t('category')}",
                options=[t('all_categories')] + categories,
                key="category_filter",
                help=t('category_filter_help')
            )
        
        with col3:
            difficulty_levels = [t('all_levels'), t('easy'), t('medium'), t('hard')]
            selected_difficulty = st.selectbox(
                f"⚡ {t('difficulty')}",
                options=difficulty_levels,
                key="difficulty_filter",
                help=t('difficulty_filter_help')
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
            difficulty = error.get('difficulty_level', 'medium')
            return difficulty_order.get(difficulty, 2)  # Default to medium if unknown
        
        return sorted(errors, key=get_difficulty_sort_key)

    def _render_consecutive_error_card(self, error: Dict[str, Any]):
        """Render error card using a clean expander format with integrated title."""
        error_name = error.get(t("error_name"), t("unknown_error"))
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
                    st.markdown(f"""
                    <div class="section-header-inline">
                        <h4 class="section-title">📋 {t('error_description')}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f'<div class="description-content">{description}</div>', unsafe_allow_html=True)
                
                if implementation_guide:
                    st.markdown(f"""
                    <div class="section-header-inline">
                        <h4 class="section-title">💡 {t('how_to_fix')}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f'<div class="solution-content">{implementation_guide}</div>', unsafe_allow_html=True)
                
            # Code examples section with improved layout
            if examples.get("wrong_examples") or examples.get("correct_examples"):
               
                st.markdown(f"""
                    <div class="section-header-inline">
                        <h4 class="section-title">💻 {t('code_example')}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                # Create columns for side-by-side comparison when both exist
                if examples.get("wrong_examples") and examples.get("correct_examples"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="code-section-header error-header">
                            <h4 class="code-section-title">❌ {t('problematic_code')}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, example in enumerate(examples["wrong_examples"][:2], 1):
                            if len(examples["wrong_examples"]) > 1:
                                st.markdown(f'<div class="example-label">Example {i}:</div>', unsafe_allow_html=True)
                            st.code(example, language="java")
                    
                    with col2:
                        st.markdown(f"""
                        <div class="code-section-header solution-header">
                            <h4 class="code-section-title">✅ {t('corrected_code')}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, example in enumerate(examples["correct_examples"][:2], 1):
                            if len(examples["correct_examples"]) > 1:
                                st.markdown(f'<div class="example-label">Example {i}:</div>', unsafe_allow_html=True)
                            st.code(example, language="java")
                
                else:
                    # Single column layout when only one type exists
                    if examples.get("wrong_examples"):
                        st.markdown(f"""
                        <div class="code-section-header error-header">
                            <h4 class="code-section-title">❌ {t('problematic_code')} {t('examples')}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, example in enumerate(examples["wrong_examples"][:3], 1):
                            if len(examples["wrong_examples"]) > 1:
                                st.markdown(f'<div class="example-label">{t("example")} {i}:</div>', unsafe_allow_html=True)
                            st.code(example, language="java")
                            if i < len(examples["wrong_examples"][:3]):
                                st.markdown('<hr class="example-divider">', unsafe_allow_html=True)
                    
                    if examples.get("correct_examples"):
                        st.markdown(f"""
                        <div class="code-section-header solution-header">
                            <h4 class="code-section-title">✅ {t('corrected_code')} {t('examples')}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, example in enumerate(examples["correct_examples"][:3], 1):
                            if len(examples["correct_examples"]) > 1:
                                st.markdown(f'<div class="example-label">{t("example")} {i}:</div>', unsafe_allow_html=True)
                            st.code(example, language="java")
                            if i < len(examples["correct_examples"][:3]):
                                st.markdown('<hr class="example-divider">', unsafe_allow_html=True)
                
            
            col1, col2, col3 = st.columns([1, 5, 1])
            with col2:
                if st.button(
                    f"🚀 {t('start_practice_session')}", 
                    key=f"practice_{error_code}", 
                    use_container_width=True,
                    type="primary",
                    help=t('generate_practice_code_with_error_type')
                ):
                    self._handle_practice_error(error)
            
            # Close wrapper
            st.markdown('</div>', unsafe_allow_html=True)

    def _handle_practice_error(self, error: Dict[str, Any]):
        """Handle practice error by generating code with LangGraph and starting review workflow."""
        if not self.workflow:
            st.error(t("practice_mode_requires_workflow"))
            return
        
        error_name = error.get(t("error_name"), t("unknown_error"))
        error_code = error.get('error_code', '')
        
        try:
            # Show immediate feedback
            st.success(f"🎯 {t('generating_practice_code_with')} {error_name}...")
            
            # Create a progress bar for user feedback
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Reset workflow state for new practice session
            progress_bar.progress(20)
            status_text.text(t("preparing_practice_session"))
            
            # Reset workflow state
            from state_schema import WorkflowState
            st.session_state.workflow_state = WorkflowState()
            
            # Step 2: Set up error-specific generation
            progress_bar.progress(40)
            status_text.text(t("configuring_error_parameters"))
            
            # Configure the workflow for this specific error
            state = st.session_state.workflow_state
            
            # Set up the error selection for targeted generation
            state.selected_categories = {"java_errors": [error.get('category', 'Other')]}
            state.specific_errors = [error]  # Focus on this specific error
            state.difficulty_level = error.get('difficulty_level', 'medium')
            state.current_step = 'generate'
            
            # Step 3: Generate code with the specific error
            progress_bar.progress(60)
            status_text.text(t("generating_code_with_error"))
            
            # Use the workflow to generate code
            result = self.workflow.generate_code_with_errors(
                selected_categories=state.selected_categories,
                specific_errors=state.specific_errors,
                difficulty=state.difficulty_level
            )
            
            if result.get('success', False):
                # Step 4: Set up the generated code in workflow state
                progress_bar.progress(80)
                status_text.text(t("setting_up_practice_environment"))
                
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
                status_text.text(t("practice_session_ready"))
                
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
                st.success(f"✅ {t('practice_code_generated_successfully')}")
                st.info(f"💡 {t('navigate_to_review_tab_to_start_analyzing')} {error_name}")
                
                # Set the active tab to review (index 1)
                st.session_state.active_tab = 1
                st.session_state["force_tab_switch"] = True
                
                # Brief pause for user to read the message
                time.sleep(2)
                st.rerun()
                
            else:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ {t('failed_to_generate_practice_code')}: {result.get('error', t('unknown_error'))}")
                
        except Exception as e:
            logger.error(f"Error in practice mode: {str(e)}")
            st.error(f"❌ {t('error_setting_up_practice_session')}: {str(e)}")
            st.info(t("please_try_again_or_contact_support"))
    
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
            selected_category = st.session_state.get('selected_category', t('all_categories'))
            
            if selected_category == t('all_categories'):                
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
        selected_difficulty = st.session_state.get('selected_difficulty', t('all_levels'))
        
        if selected_difficulty != t('all_levels'):
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
    
    def _render_no_results(self):
        """Render enhanced no results message."""
        st.markdown(f"""
        <div class="no-results">
            <div class="no-results-icon">🔍</div>
            <h3>{t('no_errors_found')}</h3>
            <p>{t('no_errors_found_message')}</p>
            <div class="no-results-suggestions">
                <h4>{t('try_these_suggestions')}:</h4>
                <ul>
                    <li>{t('check_spelling_try_different_keywords')}</li>
                    <li>{t('broaden_search_select_all_categories')}</li>
                    <li>{t('try_searching_common_terms')}</li>
                    <li>{t('clear_search_box_browse_all')}</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_error_explorer(workflow=None):
    """Main function to render the error explorer with workflow integration."""
    explorer = ErrorExplorerUI(workflow=workflow)
    explorer.render()