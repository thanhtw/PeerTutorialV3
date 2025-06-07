# ui/components/error_explorer_ui.py - Enhanced version

import streamlit as st
import os
import logging
import time
from typing import Dict, List, Any, Optional
from data.database_error_repository import DatabaseErrorRepository
from utils.language_utils import t, get_current_language
from static.css_utils import load_css
from utils.code_utils import _get_category_icon, _get_difficulty_icon, add_line_numbers
from state_schema import WorkflowState
import json
import re

logger = logging.getLogger(__name__)

class ErrorExplorerUI:
    """UI component for exploring Java errors with examples and solutions."""
    
    def __init__(self, workflow=None):
        """Initialize the Error Explorer UI."""
        self.repository = DatabaseErrorRepository()
        self.workflow = workflow  # JavaCodeReviewGraph instance
        
        # Log workflow initialization for debugging
        if workflow:
            logger.info(f"ErrorExplorerUI initialized with workflow: {type(workflow)}")
        else:
            logger.warning("ErrorExplorerUI initialized without workflow - practice mode will not work")
        
        # Initialize session state
        if "selected_error_code" not in st.session_state:
            st.session_state.selected_error_code = None
        if "user_progress" not in st.session_state:
            st.session_state.user_progress = {}
        if "practice_mode_active" not in st.session_state:
            st.session_state.practice_mode_active = False
        
        self._load_styles()
    
    def _load_styles(self):
        """Load CSS styles for the Error Explorer UI with safe encoding handling."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            css_dir = os.path.join(current_dir, "..", "..", "static", "css", "error_explorer")
            from static.css_utils import load_css_safe
            result = load_css_safe(css_directory=css_dir)
        except Exception as e:
            logger.error(f"Error loading Error Explorer CSS: {str(e)}")
            st.warning(t("css_loading_warning"))

    def render(self, workflow=None):
        """Render the complete error explorer interface."""
        # Only update workflow if one is provided, otherwise keep the existing one
        if workflow is not None:
            self.workflow = workflow
        
        # Check if we're in practice mode
        if st.session_state.get("practice_mode_active", False):
            self._render_practice_mode()
        else:
            self._render_exploration_mode()
    
    def _render_exploration_mode(self):
        """Render the normal exploration mode."""
        # Professional header
        self._render_header()
        
        # Search and filter section
        self._render_search_filters()
        
        # Main content area
        self._render_error_content()
    
    def _process_practice_review(self, student_review):
        """Process the submitted practice review."""
        try:
            workflow_state = st.session_state.practice_workflow_state
            
            with st.spinner(f"🔄 {t('analyzing_your_review')}"):
                # Submit review through workflow
                updated_state = self.workflow.submit_review(workflow_state, student_review)
                
                # Update stored state
                st.session_state.practice_workflow_state = updated_state
                
                # Check if review is complete
                review_sufficient = getattr(updated_state, 'review_sufficient', False)
                current_iteration = getattr(updated_state, 'current_iteration', 1)
                max_iterations = getattr(updated_state, 'max_iterations', 3)
                
                if review_sufficient or current_iteration > max_iterations:
                    st.session_state.practice_workflow_status = "review_complete"
                    st.success(f"✅ {t('review_analysis_complete')}")
                else:
                    st.info(f"📝 {t('review_submitted_try_improve')}")
                
                time.sleep(1)
                st.rerun()
                
        except Exception as e:
            logger.error(f"Error processing practice review: {str(e)}")
            st.error(f"❌ {t('error_processing_review')}: {str(e)}")
    
    def _restart_practice_session(self):
        """Restart the practice session with the same error."""
        # Clear practice session state but keep error data
        practice_error = st.session_state.get("practice_error_data", {})
        
        keys_to_clear = [
            "practice_code_generated",
            "practice_workflow_state", 
            "practice_workflow_status"
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state.practice_workflow_status = "setup"
        st.rerun()
    
    def _regenerate_practice_code(self):
        """Regenerate practice code with the same error."""
        practice_error = st.session_state.get("practice_error_data", {})
        
        # Clear code generation state
        if "practice_code_generated" in st.session_state:
            del st.session_state["practice_code_generated"]
        if "practice_workflow_state" in st.session_state:
            del st.session_state["practice_workflow_state"]
        
        st.session_state.practice_workflow_status = "setup"
        st.rerun()
    
    def _exit_practice_mode(self):
        """Exit practice mode and return to exploration."""
        # Clear all practice-related session state
        practice_keys = [key for key in st.session_state.keys() if key.startswith("practice_")]
        for key in practice_keys:
            del st.session_state[key]
        
        st.session_state.practice_mode_active = False
        st.rerun()
    
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
        error_name = error.get(t("error_name_variable"), t("unknown_error"))
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
                
            
            
            practice_key = f"practice_{error_code}_{hash(error_name) % 1000}"
            if st.button(
                    f"🚀 {t('start_practice_session')}", 
                    key=practice_key, 
                    use_container_width=True,
                    type="primary",
                    help=t('generate_practice_code_with_error_type')
            ):
                    # FIXED: Avoid multiple st.rerun() calls that cause setIn error
                self._start_practice_session(error)

    def _start_practice_session(self, error: Dict[str, Any]):
        """
        FIXED: Start practice session without causing setIn error.
        Uses session state flags instead of immediate st.rerun() calls.
        """
        try:
            error_name = error.get(t("error_name_variable"), t("unknown_error"))
            logger.info(f"Starting practice session for error: {error_name}")
            
            # Set session state flags (no st.rerun() yet)
            st.session_state.practice_mode_active = True
            st.session_state.practice_error_data = error
            st.session_state.practice_workflow_status = "setup"
            
            # Clear any existing practice state
            practice_keys = [key for key in st.session_state.keys() 
                           if key.startswith("practice_") and key not in 
                           ["practice_mode_active", "practice_error_data", "practice_workflow_status"]]
            for key in practice_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Show immediate feedback without st.rerun()
            st.success(t('starting_practice_session_with').format(error_name=error_name))
            st.info(f"✨ {t('practice_mode_activated_interface_reload')}")
            
            # Single st.rerun() call at the end
            time.sleep(0.5)  # Brief pause for user to see the message
            st.rerun()
            
        except Exception as e:
            logger.error(f"Error starting practice session: {str(e)}", exc_info=True)
            st.error(f"❌ {t('error_setting_up_practice_session')}: {str(e)}")

    def _prepare_practice_workflow_state(self, error: Dict[str, Any]) -> Optional[WorkflowState]:
        """Prepare a WorkflowState specifically for practice sessions with a single error."""
        try:
            error_name = error.get(t("error_name_variable"), t("unknown_error"))
            difficulty_level = error.get('difficulty_level', 'medium')
            category = error.get('category', 'Other')
            
            logger.debug(f"Preparing practice state for error: {error_name}, difficulty: {difficulty_level}")
            
            # Create a new WorkflowState
            state = WorkflowState()
            
            # Set basic parameters optimized for single error practice
            state.code_length = "medium"  # Good balance for practice
            state.difficulty_level = difficulty_level
            state.error_count_start = 1
            state.error_count_end = 1
            
            # Set domain based on error category if available
            domain_mapping = {
                "logical errors": "calculation",
                "logical_errors": "calculation", 
                "syntax errors": "user_management",
                "syntax_errors": "user_management",
                "code quality": "file_processing",
                "code_quality": "file_processing",
                "standard violation": "data_validation",
                "standard_violation": "data_validation",
                "java specific": "banking",
                "java_specific": "banking"
            }
            state.domain = domain_mapping.get(category.lower(), "student_management")
            
            # Configure for specific error mode
            state.selected_error_categories = {"java_errors": []}  # Empty for specific mode
            state.selected_specific_errors = [error]  # Focus on this single error
            
            # Set workflow control parameters
            state.current_step = "generate"
            state.max_evaluation_attempts = 3
            state.max_iterations = 3
            
            # Reset all other state fields to defaults
            state.evaluation_attempts = 0
            state.current_iteration = 1
            state.review_sufficient = False
            state.review_history = []
            state.evaluation_result = None
            state.code_snippet = None
            state.comparison_report = None
            state.error = None
            
            logger.debug(f"Practice state prepared successfully for {error_name}")
            return state
            
        except Exception as e:
            logger.error(f"Error preparing practice workflow state: {str(e)}")
            return None
    
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
                if search_term in error.get(t("implementation_guide"), "").lower() or
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



    def _render_practice_mode(self):
        """Render the enhanced professional practice mode interface."""
        practice_error = st.session_state.get("practice_error_data", {})
        error_name = practice_error.get("error_name", t("unknown_error"))
        error_code = practice_error.get("error_code", "")
        difficulty = practice_error.get("difficulty_level", "medium")
        category = practice_error.get("category", "")
        
        # Professional practice mode header with enhanced styling
        self._render_professional_practice_header(error_name, difficulty, category)
        
        # Main practice workflow based on status
        workflow_status = st.session_state.get("practice_workflow_status", "setup")
        
        if workflow_status == "setup":
            self._render_professional_practice_setup(practice_error)
        elif workflow_status == "code_ready":
            self._render_professional_practice_review()
        elif workflow_status == "review_complete":
            self._render_professional_practice_feedback()

    def _render_professional_practice_header(self, error_name: str, difficulty: str, category: str):
        """Render enhanced professional practice mode header."""
        # Difficulty colors and icons
        difficulty_config = {
            "easy": {"color": "#28a745", "icon": "🟢", "bg": "#d4edda"},
            "medium": {"color": "#ffc107", "icon": "🟡", "bg": "#fff3cd"},
            "hard": {"color": "#dc3545", "icon": "🔴", "bg": "#f8d7da"}
        }
        
        config = difficulty_config.get(difficulty, difficulty_config["medium"])
        category_icon = _get_category_icon(category.lower()) if category else "📚"
        
        st.markdown(f"""
        <div class="professional-practice-header">
            <div class="practice-header-content">
                <div class="practice-title-section">
                    <div class="practice-mode-badge">
                        <span class="practice-icon">🎯</span>
                        <span class="practice-label">{t('practice_mode')}</span>
                    </div>
                    <h1 class="practice-error-title">{error_name}</h1>
                    <div class="practice-meta-info">
                        <span class="practice-category">
                            <span class="category-icon">{category_icon}</span>
                            {category}
                        </span>
                        <span class="practice-difficulty" style="background: {config['bg']}; color: {config['color']};">
                            <span class="difficulty-icon">{config['icon']}</span>
                            {t(difficulty)}
                        </span>
                    </div>
                </div>
                <div class="practice-actions-section">
                    <div class="practice-progress-indicator">
                        <div class="progress-step active">1</div>
                        <div class="progress-connector"></div>
                        <div class="progress-step">2</div>
                        <div class="progress-connector"></div>
                        <div class="progress-step">3</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _render_professional_practice_setup(self, practice_error):
        """Render the enhanced professional practice setup phase."""
        st.markdown(f"""
        <div class="professional-practice-container">
            <div class="practice-section-header">
                <span class="section-icon">⚙️</span>
                <div>
                    <h3 class="section-title">{t('preparing_practice_session')}</h3>
                    <p class="section-subtitle">{t('generating_custom_code_challenge')}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced error details with professional cards
        self._render_enhanced_error_details(practice_error)
        
        # Workflow validation and generation
        if not self.workflow:
            self._render_workflow_error_message()
            return
        
        # Auto-generate code with enhanced status
        if "practice_code_generated" not in st.session_state:
            self._generate_practice_code_professional(practice_error)

    def _render_enhanced_error_details(self, practice_error):
        """Render enhanced error details with professional styling."""
        description = practice_error.get('description', t('no_description_available'))
        implementation_guide = practice_error.get('implementation_guide', '')
        difficulty = practice_error.get('difficulty_level', 'medium')
        
        st.markdown(f"""
        <div class="enhanced-error-details-container">
            <div class="error-details-header">
                <h4><span class="details-icon">📋</span> {t('error_overview')}</h4>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Create columns for better layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Description card
            st.markdown(f"""
            <div class="detail-card description-card">
                <div class="card-header">
                    <span class="card-icon">📝</span>
                    <h5>{t('what_youll_learn')}</h5>
                </div>
                <div class="card-content">
                    {description}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if implementation_guide:
                # Implementation guide card
                st.markdown(f"""
                <div class="detail-card guide-card">
                    <div class="card-header">
                        <span class="card-icon">💡</span>
                        <h5>{t('identification_tips')}</h5>
                    </div>
                    <div class="card-content">
                        {implementation_guide}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Session info card
            st.markdown(f"""
            <div class="detail-card session-info-card">
                <div class="card-header">
                    <span class="card-icon">⚡</span>
                    <h5>{t('session_details')}</h5>
                </div>
                <div class="card-content">
                    <div class="info-item">
                        <span class="info-label">{t('difficulty')}:</span>
                        <span class="info-value difficulty-{difficulty}">{t(difficulty)}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">{t('focus_area')}:</span>
                        <span class="info-value">{t('single_error_type')}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">{t('attempts')}:</span>
                        <span class="info-value">3 {t('maximum')}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def _render_workflow_error_message(self):
        """Render professional workflow error message."""
        st.markdown(f"""
        <div class="workflow-error-container">
            <div class="error-icon">⚠️</div>
            <h3>{t('practice_session_unavailable')}</h3>
            <p>{t('workflow_system_not_initialized')}</p>
            <div class="error-actions">
                <button onclick="window.location.reload()" class="refresh-button">
                    🔄 {t('refresh_page')}
                </button>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _generate_practice_code_professional(self, practice_error):
        """Generate practice code with enhanced professional status display."""
        if not self.workflow:
            logger.error("No workflow available for practice mode")
            st.error(f"❌ {t('practice_mode_requires_workflow_refresh')}")
            return
        
        try:
            # Enhanced status container
            status_container = st.container()
            
            with status_container:
                st.markdown(f"""
                <div class="generation-status-container">
                    <div class="status-header">
                        <span class="status-icon">🚀</span>
                        <h4>{t('generating_practice_challenge')}</h4>
                    </div>
                    <div class="status-content">
                        <div class="progress-bar-container">
                            <div class="progress-bar animated"></div>
                        </div>
                        <p class="status-message">{t('creating_custom_code_with_error')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Execute the generation
            workflow_state = self._prepare_practice_workflow_state(practice_error)
            
            if not workflow_state:
                st.error(f"❌ {t('failed_prepare_practice_session')}")
                return
            
            logger.info(f"Executing code generation with workflow: {type(self.workflow)}")
            updated_state = self.workflow.execute_code_generation(workflow_state)
            
            # Validate and handle result
            if hasattr(updated_state, 'error') and updated_state.error:
                st.error(f"❌ {t('failed_to_generate_practice_code')}: {updated_state.error}")
                return
            
            if not hasattr(updated_state, 'code_snippet') or not updated_state.code_snippet:
                st.error(f"❌ {t('failed_to_generate_practice_code')}: No code generated")
                return
            
            # Store results and update status
            st.session_state.practice_workflow_state = updated_state
            st.session_state.practice_code_generated = True
            st.session_state.practice_workflow_status = "code_ready"
            
            # Track usage
            try:
                error_code = practice_error.get('error_code', '')
                if error_code:
                    self.repository.update_error_usage(
                        error_code=error_code,
                        action_type='practiced',
                        context={'source': 'practice_mode', 'method': 'professional'}
                    )
            except Exception as e:
                logger.debug(f"Could not track error usage: {str(e)}")
            
            # Success message with enhanced styling
            st.markdown(f"""
            <div class="generation-success-container">
                <div class="success-icon">✨</div>
                <h4>{t('practice_challenge_ready')}</h4>
                <p>{t('code_generated_successfully_review_time')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            logger.error(f"Error generating practice code: {str(e)}", exc_info=True)
            st.error(f"❌ {t('error_setting_up_practice_session')}: {str(e)}")

    def _render_professional_practice_review(self):
        """Render the enhanced professional practice review interface."""
        workflow_state = st.session_state.get("practice_workflow_state")
        
        if not workflow_state or not hasattr(workflow_state, 'code_snippet'):
            st.error(t('no_practice_session_data'))
            return
        
        # Enhanced practice review container
        st.markdown(f"""
        <div class="professional-practice-review-container">
            <div class="review-phase-header">
                <div class="phase-indicator">
                    <span class="phase-icon">👀</span>
                    <div class="phase-info">
                        <h3>{t('code_review_phase')}</h3>
                        <p>{t('analyze_code_find_specific_error')}</p>
                    </div>
                </div>
                <div class="practice-tips">
                    <span class="tip-icon">💡</span>
                    <span>{t('look_for_specific_error_practicing')}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced code display section
        self._render_enhanced_code_display(workflow_state)
        
        # Enhanced review input section
        self._render_enhanced_review_input(workflow_state)

    def _render_enhanced_code_display(self, workflow_state):
        """Render enhanced code display for practice mode."""
        code_to_display = workflow_state.code_snippet.clean_code
        
        # Professional code container
        st.markdown(f"""
        <div class="enhanced-code-container">
            <div class="code-header-professional">
                <div class="code-meta">
                    <span class="file-icon">📄</span>
                    <span class="file-name">PracticeChallenge.java</span>
                </div>
                <div class="code-stats">
                    <span class="stat-item">
                        <span class="stat-icon">📏</span>
                        <span>{len(code_to_display.split())} {t('lines')}</span>
                    </span>
                    <span class="language-badge">☕ Java</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Code display with professional styling
        st.code(add_line_numbers(code_to_display), language="java")

    def _render_enhanced_review_input(self, workflow_state):
        """Render enhanced review input section for practice mode."""
        current_iteration = getattr(workflow_state, 'current_iteration', 1)
        max_iterations = getattr(workflow_state, 'max_iterations', 3)
        
        # Show guidance if available
        review_history = getattr(workflow_state, 'review_history', [])
        if review_history:
            latest_review = review_history[-1]
            if hasattr(latest_review, 'targeted_guidance') and latest_review.targeted_guidance:
                st.markdown(f"""
                <div class="professional-guidance-container">
                    <div class="guidance-header">
                        <span class="guidance-icon">🎯</span>
                        <h4>{t('personalized_guidance')}</h4>
                    </div>
                    <div class="guidance-content">
                        {latest_review.targeted_guidance}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Enhanced review input container
        st.markdown(f"""
        <div class="enhanced-review-input-container">
            <div class="input-section-header">
                <div class="input-meta">
                    <span class="input-icon">✍️</span>
                    <div class="input-info">
                        <h4>{t('submit_your_analysis')}</h4>
                        <p>{t('attempt')} {current_iteration} {t('of')} {max_iterations}</p>
                    </div>
                </div>
                <div class="attempt-progress">
                    <div class="progress-circles">
                        {"".join(f'<div class="circle {"active" if i < current_iteration else ""}"></div>' for i in range(1, max_iterations + 1))}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Review input
        review_key = f"practice_review_{current_iteration}"
        student_review = st.text_area(
            "",
            height=250,
            key=review_key,
            placeholder=f"🔍 {t('example_review_format_line')}",
            label_visibility="collapsed"
        )
        
        # Enhanced action buttons - REMOVED DISABLED FUNCTIONALITY
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # REMOVED: submit_disabled = not student_review or len(student_review.strip()) < 10
            if st.button(
                f"🚀 {t('submit_analysis')}",
                # REMOVED: disabled=submit_disabled,
                key=f"submit_practice_review_{current_iteration}",
                use_container_width=True,
                type="primary"
            ):
                # Add basic validation in the processing function instead
                if student_review and student_review.strip():
                    self._process_practice_review(student_review.strip())
                else:
                    st.warning(f"⚠️ {t('please_enter_review')}")
        
        with col2:
            if st.button(
                f"🔄 {t('generate_new_challenge')}",
                key="regenerate_practice",
                use_container_width=True
            ):
                self._regenerate_practice_code()
        
        with col3:
            if st.button(
                f"🏠 {t('exit')}",
                key="exit_practice_from_review",
                use_container_width=True
            ):
                self._exit_practice_mode()

    def _render_professional_practice_feedback(self):
        """Render the enhanced professional practice feedback interface."""
        workflow_state = st.session_state.get("practice_workflow_state")
        
        if not workflow_state:
            st.error(t('no_practice_session_data'))
            return
        
        # Professional feedback header
        st.markdown(f"""
        <div class="professional-feedback-header">
            <div class="feedback-celebration">
                <div class="celebration-icon">🎉</div>
                <div class="celebration-content">
                    <h2>{t('practice_session_complete')}</h2>
                    <p>{t('excellent_work_analysis_complete')}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced results dashboard
        self._render_enhanced_results_dashboard(workflow_state)
        
        # Extract and render comparison report if available
        comparison_report = getattr(workflow_state, 'comparison_report', None)
        if comparison_report:
            self._render_comparison_report(comparison_report)
        
        # Enhanced action panel
        self._render_enhanced_action_panel()

    def _render_comparison_report(self, comparison_report: str):
        """
        Extract and render the comparison report JSON with professional layout and CSS.
        """
        # Extract JSON object after "=== RESPONSE ==="
        json_text = ""
        if "=== RESPONSE ===" in comparison_report:
            # If the report is a full LLM log, extract after marker
            json_text = comparison_report.split("=== RESPONSE ===", 1)[-1].strip()
        else:
            # Otherwise, try to find the first JSON object in the string
            match = re.search(r'\{[\s\S]+\}', comparison_report)
            if match:
                json_text = match.group(0)
            else:
                st.warning("No valid comparison report found.")
                return

        # Try to parse JSON
        try:
            report_data = json.loads(json_text)
        except Exception as e:
            st.error(f"Failed to parse comparison report: {e}")
            st.code(json_text)
            return

        # Enhanced CSS for professional report layout
        st.markdown("""
        <style>
        .comparison-report-container {
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
            padding: 2.5rem;
            margin: 2rem 0;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            border: 1px solid #e9ecef;
            position: relative;
            overflow: hidden;
        }
        
        .comparison-report-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #4CAF50 0%, #2196F3 50%, #FF9800 100%);
        }
        
        .comparison-section-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1a202c;
            margin: 2rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e2e8f0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .comparison-section-title:first-child {
            margin-top: 0;
        }
        
        .comparison-summary-table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
            background: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        
        .comparison-summary-table th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 1.5rem;
            font-weight: 600;
            text-align: left;
            font-size: 0.95rem;
            letter-spacing: 0.5px;
        }
        
        .comparison-summary-table td {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #f1f5f9;
            color: #374151;
            font-size: 1rem;
            transition: background-color 0.2s ease;
        }
        
        .comparison-summary-table tr:hover td {
            background-color: #f8fafc;
        }
        
        .comparison-summary-table tr:last-child td {
            border-bottom: none;
        }
        
        .comparison-badge {
            display: inline-flex;
            align-items: center;
            background: linear-gradient(135deg, #e0f2fe 0%, #b3e5fc 100%);
            color: #0277bd;
            border-radius: 20px;
            padding: 0.4rem 1rem;
            font-size: 0.9rem;
            font-weight: 600;
            margin-right: 0.75rem;
            margin-bottom: 0.5rem;
            box-shadow: 0 2px 4px rgba(2, 119, 189, 0.1);
            border: 1px solid #81d4fa;
        }
        
        .comparison-issue-list {
            margin: 1rem 0;
            padding: 0;
            list-style: none;
        }
        
        .comparison-issue-list li {
            background: #ffffff;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            border-left: 4px solid #e2e8f0;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .comparison-issue-list li:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }
        
        .comparison-issue-list li.success-item {
            border-left-color: #10b981;
            background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%);
        }
        
        .comparison-issue-list li.error-item {
            border-left-color: #ef4444;
            background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
        }
        
        .comparison-praise {
            color: #059669;
            font-style: italic;
            margin-top: 0.75rem;
            padding: 0.75rem 1rem;
            background: #f0fdf4;
            border-radius: 8px;
            border-left: 3px solid #10b981;
            font-size: 0.95rem;
        }
        
        .comparison-missed {
            color: #dc2626;
            margin-top: 0.75rem;
            padding: 0.75rem 1rem;
            background: #fef2f2;
            border-radius: 8px;
            border-left: 3px solid #ef4444;
            font-size: 0.95rem;
        }
        
        .comparison-tip {
            background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
            border: 1px solid #fbbf24;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin: 1.5rem 0;
            position: relative;
            box-shadow: 0 2px 8px rgba(251, 191, 36, 0.1);
        }
        
        .comparison-tip::before {
            content: '💡';
            position: absolute;
            top: -8px;
            left: 1.5rem;
            background: #fbbf24;
            padding: 0.5rem;
            border-radius: 50%;
            font-size: 1rem;
        }
        
        .comparison-tip strong {
            color: #92400e;
            font-weight: 700;
        }
        
        .comparison-encouragement {
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border: 1px solid #10b981;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin: 1.5rem 0;
            position: relative;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.1);
        }
        
        .comparison-encouragement::before {
            content: '🎯';
            position: absolute;
            top: -8px;
            left: 1.5rem;
            background: #10b981;
            padding: 0.5rem;
            border-radius: 50%;
            font-size: 1rem;
        }
        
        .comparison-encouragement strong {
            color: #047857;
            font-weight: 700;
        }
        
        .comparison-feedback-list {
            margin: 1rem 0;
            padding: 0;
            list-style: none;
        }
        
        .comparison-feedback-list li {
            background: #f8fafc;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            border-left: 3px solid #3b82f6;
            color: #374151;
            font-size: 0.95rem;
            transition: all 0.2s ease;
        }
        
        .comparison-feedback-list li:hover {
            background: #e2e8f0;
            transform: translateX(4px);
        }
        
        .comparison-metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 1.5rem 0;
        }
        
        .comparison-metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
            transition: all 0.3s ease;
        }
        
        .comparison-metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        }
        
        .comparison-metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #1a202c;
            margin-bottom: 0.5rem;
        }
        
        .comparison-metric-label {
            color: #6b7280;
            font-size: 0.9rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .success-highlight {
            color: #10b981 !important;
        }
        
        .warning-highlight {
            color: #f59e0b !important;
        }
        
        .error-highlight {
            color: #ef4444 !important;
        }
        
        .section-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, #e2e8f0 50%, transparent 100%);
            margin: 2rem 0;
        }
        
        @media (max-width: 768px) {
            .comparison-report-container {
                padding: 1.5rem;
                margin: 1rem 0;
            }
            
            .comparison-summary-table th,
            .comparison-summary-table td {
                padding: 0.75rem;
                font-size: 0.9rem;
            }
            
            .comparison-section-title {
                font-size: 1.3rem;
            }
            
            .comparison-metrics-grid {
                grid-template-columns: 1fr;
            }
        }
        """, unsafe_allow_html=True)

        # Render summary with enhanced metrics
        summary = report_data.get("performance_summary", {})
        st.markdown('<div class="comparison-report-container">', unsafe_allow_html=True)
        
        # Performance metrics grid
        total_issues = summary.get('total_issues', 0)
        identified_count = summary.get('identified_count', 0)
        accuracy = summary.get('accuracy_percentage', 0)
        missed_count = summary.get('missed_count', 0)
        
        st.markdown(f'''
        <div class="comparison-section-title">📊 {t("review_performance_summary")}</div>
        <div class="comparison-metrics-grid">
            <div class="comparison-metric-card">
                <div class="comparison-metric-value">{total_issues}</div>
                <div class="comparison-metric-label">{t('total_issues')}</div>
            </div>
            <div class="comparison-metric-card">
                <div class="comparison-metric-value success-highlight">{identified_count}</div>
                <div class="comparison-metric-label">{t('identified_count')}</div>
            </div>
            <div class="comparison-metric-card">
                <div class="comparison-metric-value {'success-highlight' if accuracy >= 80 else 'warning-highlight' if accuracy >= 60 else 'error-highlight'}">{accuracy}%</div>
                <div class="comparison-metric-label">{t('accuracy')}</div>
            </div>
            <div class="comparison-metric-card">
                <div class="comparison-metric-value {'success-highlight' if missed_count == 0 else 'error-highlight'}">{missed_count}</div>
                <div class="comparison-metric-label">{t('missed_count')}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Overall assessment card
        overall_assessment = summary.get('overall_assessment', '')
        completion_status = summary.get('completion_status', '')
        if overall_assessment or completion_status:
            st.markdown(f'''
            <div class="comparison-encouragement">
                <strong>{t('overall_assessment')}:</strong> {overall_assessment}<br>
                <strong>{t('completion_status')}:</strong> {completion_status}
            </div>
            ''', unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # Correctly identified issues
        identified = report_data.get("correctly_identified_issues", [])
        st.markdown(f'<div class="comparison-section-title">✅ {t("correctly_identified_issues")}</div>', unsafe_allow_html=True)
        if identified:
            st.markdown('<ul class="comparison-issue-list">', unsafe_allow_html=True)
            for issue in identified:
                desc = issue.get("issue_description", "")
                praise = issue.get("praise_comment", "")
                st.markdown(f'<li class="success-item"><span class="comparison-badge">✅ {t("found")}</span> {desc}<div class="comparison-praise">🌟 {praise}</div></li>', unsafe_allow_html=True)
            st.markdown('</ul>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="comparison-tip">🔍 {t("no_identified_issues")}</div>', unsafe_allow_html=True)

        # Missed issues
        missed = report_data.get("missed_issues", [])
        st.markdown(f'<div class="comparison-section-title">❌ {t("missed_issues")}</div>', unsafe_allow_html=True)
        if missed:
            st.markdown('<ul class="comparison-issue-list">', unsafe_allow_html=True)
            for issue in missed:
                desc = issue.get("issue_description", "")
                why = issue.get("why_important", "")
                how = issue.get("how_to_find", "")
                st.markdown(f'<li class="error-item"><span class="comparison-badge">❌ {t("missed")}</span> {desc}<div class="comparison-missed">❗ <strong>{t("why_important")}:</strong> {why}<br>🔍 <strong>{t("how_to_find")}:</strong> {how}</div></li>', unsafe_allow_html=True)
            st.markdown('</ul>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="comparison-encouragement">🎉 {t("all_issues_found")}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # Tips for improvement
        tips = report_data.get("tips_for_improvement", [])
        if tips:
            st.markdown(f'<div class="comparison-section-title">💡 {t("tips_for_improvement")}</div>', unsafe_allow_html=True)
            for tip in tips:
                st.markdown(
                    f'<div class="comparison-tip"><strong>{tip.get("category", "")}:</strong> {tip.get("tip", "")}<br><em>💭 {t("example")}: {tip.get("example", "")}</em></div>',
                    unsafe_allow_html=True
                )

        # Java-specific guidance
        java_guidance = report_data.get("java_specific_guidance", [])
        if java_guidance:
            st.markdown(f'<div class="comparison-section-title">☕ {t("java_specific_guidance")}</div>', unsafe_allow_html=True)
            for item in java_guidance:
                st.markdown(
                    f'<div class="comparison-tip"><strong>☕ {item.get("topic", "")}:</strong> {item.get("guidance", "")}</div>',
                    unsafe_allow_html=True
                )

        # Encouragement and next steps
        encouragement = report_data.get("encouragement_and_next_steps", {})
        if encouragement:
            st.markdown(f'<div class="comparison-section-title">🎯 {t("encouragement_and_next_steps")}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="comparison-encouragement">'
                f'<strong>🌟 {t("positive_feedback")}:</strong> {encouragement.get("positive_feedback", "")}<br><br>'
                f'<strong>🎯 {t("next_focus_areas")}:</strong> {encouragement.get("next_focus_areas", "")}<br><br>'
                f'<strong>📚 {t("learning_objectives")}:</strong> {encouragement.get("learning_objectives", "")}'
                f'</div>',
                unsafe_allow_html=True
            )

        # Detailed feedback
        detailed = report_data.get("detailed_feedback", {})
        if detailed:
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="comparison-section-title">📝 {t("detailed_feedback")}</div>', unsafe_allow_html=True)
            
            strengths = detailed.get("strengths_identified", [])
            patterns = detailed.get("improvement_patterns", [])
            approach = detailed.get("review_approach_feedback", "")
            
            if strengths:
                st.markdown(f'<strong>💪 {t("strengths_identified")}:</strong>', unsafe_allow_html=True)
                st.markdown('<ul class="comparison-feedback-list">' + ''.join(f'<li>✨ {s}</li>' for s in strengths) + '</ul>', unsafe_allow_html=True)
            
            if patterns:
                st.markdown(f'<strong>📈 {t("improvement_patterns")}:</strong>', unsafe_allow_html=True)
                st.markdown('<ul class="comparison-feedback-list">' + ''.join(f'<li>📊 {p}</li>' for p in patterns) + '</ul>', unsafe_allow_html=True)
            
            if approach:
                st.markdown(f'<div class="comparison-tip"><strong>🔍 {t("review_approach_feedback")}:</strong> {approach}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_enhanced_results_dashboard(self, workflow_state):
        """Render enhanced results dashboard with detailed metrics."""
        review_history = getattr(workflow_state, 'review_history', [])
        
        if review_history:
            latest_review = review_history[-1]
            analysis = getattr(latest_review, 'analysis', {}) if hasattr(latest_review, 'analysis') else {}
            
            identified = analysis.get(t('identified_count'), 0)
            total = analysis.get(t('total_problems'), 1)
            accuracy = analysis.get(t('identified_percentage'), 0)
            attempts = len(review_history)
            
            # Enhanced metrics dashboard
            st.markdown(f"""
            <div class="enhanced-results-dashboard">
                <div class="dashboard-header">
                    <h3><span class="dashboard-icon">📊</span> {t('performance_summary')}</h3>
                </div>
                <div class="metrics-grid">
                    <div class="metric-card primary">
                        <div class="metric-icon">🎯</div>
                        <div class="metric-content">
                            <div class="metric-value">{identified}/{total}</div>
                            <div class="metric-label">{t('issues_identified')}</div>
                        </div>
                    </div>
                    <div class="metric-card success">
                        <div class="metric-icon">📈</div>
                        <div class="metric-content">
                            <div class="metric-value">{accuracy:.1f}%</div>
                            <div class="metric-label">{t('accuracy_score')}</div>
                        </div>
                    </div>
                    <div class="metric-card info">
                        <div class="metric-icon">🔄</div>
                        <div class="metric-content">
                            <div class="metric-value">{attempts}</div>
                            <div class="metric-label">{t('attempts_used')}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Detailed feedback section
            comparison_report = getattr(workflow_state, 'comparison_report', None)
            

    def _render_enhanced_action_panel(self):
        """Render enhanced action panel with professional styling."""
        st.markdown(f"""
        <div class="enhanced-action-panel">
            <div class="action-header">
                <h4><span class="action-icon">🚀</span> {t('what_would_you_like_to_do_next')}</h4>
            </div>
            <div class="action-grid">
                <div class="action-option">
                    <div class="option-icon">🔄</div>
                    <div class="option-content">
                        <h5>{t('practice_again')}</h5>
                        <p>{t('retry_same_error_type_new_code')}</p>
                    </div>
                </div>
                <div class="action-option">
                    <div class="option-icon">🎯</div>
                    <div class="option-content">
                        <h5>{t('try_different_error')}</h5>
                        <p>{t('explore_other_error_types_library')}</p>
                    </div>
                </div>
                <div class="action-option">
                    <div class="option-icon">📈</div>
                    <div class="option-content">
                        <h5>{t('view_progress')}</h5>
                        <p>{t('check_overall_learning_progress')}</p>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(
                f"🔄 {t('practice_same_error')}",
                use_container_width=True,
                type="primary"
            ):
                self._restart_practice_session()
        
        with col2:
            if st.button(
                f"🎯 {t('explore_more_errors')}",
                use_container_width=True,
                type="secondary"
            ):
                self._exit_practice_mode()
        
        with col3:
            if st.button(
                f"📈 {t('view_dashboard')}",
                use_container_width=True,
                type="secondary"
            ):
                self._exit_practice_mode()
                st.session_state.active_tab = 4