# ui/components/error_explorer_ui.py - Enhanced version

import streamlit as st
import os
import logging
import time
from typing import Dict, List, Any, Optional
from data.database_error_repository import DatabaseErrorRepository
from utils.language_utils import t, get_current_language
from static.css_utils import load_css
from utils.code_utils import _get_category_icon, _get_difficulty_icon
from state_schema import WorkflowState

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
    
    def _render_practice_mode(self):
        """Render the streamlined practice mode."""
        practice_error = st.session_state.get("practice_error_data", {})
        error_name = practice_error.get("error_name", t("unknown_error"))
        
        # Practice mode header
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #4CAF50, #45a049); color: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0; color: white;">🎯 {t('practice_mode')}: {error_name}</h2>
                    <p style="margin: 0.5rem 0 0 0; color: white;">{t('focused_practice_session_error_type')}</p>
                </div>
                <div>
                    <button onclick="window.location.reload()" style="background: rgba(255,255,255,0.2); border: 1px solid white; color: white; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer;">
                        {t('exit_practice_mode')}
                    </button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Practice workflow status
        workflow_status = st.session_state.get("practice_workflow_status", "setup")
        
        if workflow_status == "setup":
            self._render_practice_setup(practice_error)
        elif workflow_status == "code_ready":
            self._render_practice_review_interface()
        elif workflow_status == "review_complete":
            self._render_practice_feedback()
        
        # Exit practice mode button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(f"🏠 {t('exit_practice_mode')}", key="exit_practice", use_container_width=True):
                self._exit_practice_mode()
    
    def _render_practice_setup(self, practice_error):
        """Render the practice setup phase."""
        st.subheader(f"🔧 {t('generating_practice_code')}")
        
        # Show error details
        with st.expander(f"📋 {t('error_details')}", expanded=True):
            st.markdown(f"**{t('error')}:** {practice_error.get('error_name', t('unknown_error'))}")
            st.markdown(f"**{t('description')}:** {practice_error.get('description', t('no_description_available'))}")
            if practice_error.get('implementation_guide'):
                st.markdown(f"**{t('how_to_identify')}:** {practice_error.get('implementation_guide')}")
        
        # Debug info for workflow
        if not self.workflow:
            st.error(f"❌ {t('no_workflow_available_practice')}")
            st.info(t('debug_workflow_not_initialized'))
            
            # Show diagnostic info
            with st.expander(f"🔧 {t('diagnostic_information')}", expanded=False):
                st.code(f"""
{t('workflow_status')}: {self.workflow}
{t('session_state_keys')}: {list(st.session_state.keys())}
{t('practice_mode_active')}: {st.session_state.get('practice_mode_active', False)}
                """)
            return
        
        # Auto-generate code (this runs once when practice mode starts)
        if "practice_code_generated" not in st.session_state:
            self._generate_practice_code(practice_error)
    
    def _generate_practice_code(self, practice_error):
        """Generate practice code in the background."""
        if not self.workflow:
            logger.error("No workflow available for practice mode")
            st.error(f"❌ {t('practice_mode_requires_workflow_refresh')}")
            st.info(t('debug_info_workflow_none'))
            return
        
        try:
            with st.spinner(f"🔧 {t('generating_your_practice_code')}"):
                # Prepare workflow state
                workflow_state = self._prepare_practice_workflow_state(practice_error)
                
                if not workflow_state:
                    st.error(f"❌ {t('failed_prepare_practice_session')}")
                    return
                
                # Execute code generation
                logger.info(f"Executing code generation with workflow: {type(self.workflow)}")
                updated_state = self.workflow.execute_code_generation(workflow_state)
                
                # Validate result
                if hasattr(updated_state, 'error') and updated_state.error:
                    st.error(f"❌ {t('failed_to_generate_practice_code')}: {updated_state.error}")
                    return
                
                if not hasattr(updated_state, 'code_snippet') or not updated_state.code_snippet:
                    st.error(f"❌ {t('failed_to_generate_practice_code')}: No code generated")
                    return
                
                # Store results
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
                            context={'source': 'practice_mode', 'method': 'streamlined'}
                        )
                except Exception as e:
                    logger.debug(f"Could not track error usage: {str(e)}")
                
                st.success(f"✅ {t('practice_code_generated_successfully_rerun')}")
                time.sleep(1)
                st.rerun()
                
        except Exception as e:
            logger.error(f"Error generating practice code: {str(e)}", exc_info=True)
            st.error(f"❌ {t('error_setting_up_practice_session')}: {str(e)}")
            st.info(t('please_refresh_start_again'))
    
    def _render_practice_review_interface(self):
        """Render the integrated review interface for practice mode."""
        workflow_state = st.session_state.get("practice_workflow_state")
        
        if not workflow_state or not hasattr(workflow_state, 'code_snippet'):
            st.error(t('no_practice_session_data'))
            return
        
        # Display the code
        st.subheader(f"☕ {t('review_this_java_code')}")
        st.info(f"🎯 {t('look_for_specific_error_practicing')}")
        
        # Code display
        code_to_display = workflow_state.code_snippet.clean_code
        st.code(code_to_display, language="java")
        
        # Review input section
        st.subheader(f"📝 {t('your_review')}")
        
        # Get current iteration info
        current_iteration = getattr(workflow_state, 'current_iteration', 1)
        max_iterations = getattr(workflow_state, 'max_iterations', 3)
        
        # Show previous review if exists
        review_history = getattr(workflow_state, 'review_history', [])
        if review_history:
            latest_review = review_history[-1]
            if hasattr(latest_review, 'targeted_guidance') and latest_review.targeted_guidance:
                st.markdown(f"""
                <div style="background: #e3f2fd; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <h4>💡 {t('guidance_for_improvement')}</h4>
                    <p>{latest_review.targeted_guidance}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Review input
        review_key = f"practice_review_{current_iteration}"
        student_review = st.text_area(
            t('enter_your_review_attempt').format(current_iteration=current_iteration, max_iterations=max_iterations),
            height=200,
            key=review_key,
            placeholder=t('example_review_format_line')
        )
        
        # Submit review
        col1, col2 = st.columns([3, 1])
        with col1:
            submit_disabled = not student_review or len(student_review.strip()) < 10
            if st.button(
                f"🚀 {t('submit_review_attempt').format(current_iteration=current_iteration)}", 
                disabled=submit_disabled,
                key=f"submit_practice_review_{current_iteration}",
                use_container_width=True
            ):
                self._process_practice_review(student_review.strip())
        
        with col2:
            if st.button(f"🔄 {t('generate_new_code')}", key="regenerate_practice"):
                self._regenerate_practice_code()
    
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
    
    def _render_practice_feedback(self):
        """Render the practice session feedback."""
        workflow_state = st.session_state.get("practice_workflow_state")
        
        if not workflow_state:
            st.error(t('no_practice_session_data'))
            return
        
        st.subheader(f"🎉 {t('practice_session_complete')}")
        
        # Get analysis results
        review_history = getattr(workflow_state, 'review_history', [])
        if review_history:
            latest_review = review_history[-1]
            if hasattr(latest_review, 'analysis') and latest_review.analysis:
                analysis = latest_review.analysis
                
                # Performance metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    identified = analysis.get(t('identified_count'), 0)
                    total = analysis.get(t('total_problems'), 1)
                    st.metric(t('issues_found'), f"{identified}/{total}")
                
                with col2:
                    accuracy = analysis.get(t('identified_percentage'), 0)
                    st.metric(t('accuracy'), f"{accuracy:.1f}%")
                
                with col3:
                    attempts = len(review_history)
                    st.metric(t('attempts_used'), attempts)
                
                # Show comparison report if available
                comparison_report = getattr(workflow_state, 'comparison_report', None)
                if comparison_report:
                    st.subheader(f"📊 {t('detailed_feedback')}")
                    st.markdown(comparison_report)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"🔄 {t('practice_this_error_again')}", use_container_width=True):
                self._restart_practice_session()
        
        with col2:
            if st.button(f"🎯 {t('practice_different_error')}", use_container_width=True):
                self._exit_practice_mode()
        
        with col3:
            if st.button(f"📈 {t('view_progress_dashboard')}", use_container_width=True):
                self._exit_practice_mode()
                st.session_state.active_tab = 4  # Dashboard tab
    
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
                
            
            col1, col2, col3 = st.columns([1, 5, 1])
            with col2:
                # Fixed: Use unique key to avoid setIn error
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