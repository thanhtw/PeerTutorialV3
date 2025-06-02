"""
Enhanced Code Display UI component for Java Peer Review Training System.

This module provides professional code display components with enhanced formatting,
syntax highlighting, and interactive features.
FIXED: Submit button key generation issue that prevented button clicks from being detected.
"""

import streamlit as st
import time
import logging
import datetime
import re
from typing import List, Dict, Any, Optional, Callable

from utils.code_utils import add_line_numbers
from utils.language_utils import t

# Configure logging
logger = logging.getLogger(__name__)

class CodeDisplayUI:
    """
    Enhanced UI Component for displaying Java code snippets with professional styling.
    
    This class handles displaying Java code snippets with enhanced syntax highlighting,
    professional layout, interactive features, and proper formatting.
    FIXED: Stable key generation to ensure button clicks are properly detected.
    """
    
    def __init__(self):
        """Initialize the CodeDisplayUI component."""
        pass

    def render_code_display(self, code_snippet, known_problems: List[str] = None, instructor_mode: bool = False) -> None:
        """
        Render a code snippet with enhanced professional styling and features.

        Args:
            code_snippet: Code snippet object or string
            known_problems: List of known problems for instructor view
            instructor_mode: Whether to show instructor view
        """
        if not code_snippet:
            self._render_no_code_message()
            return

        # Extract and validate code content
        display_code = self._extract_code_content(code_snippet)
        if not display_code:
            st.warning(t("code_exists_but_empty"))
            return
        
        # Render professional code display
        self._render_professional_code_display(
            display_code, 
            known_problems, 
            instructor_mode
        )
    
    def _extract_code_content(self, code_snippet) -> str:
        """Extract code content from snippet object or string."""
        if isinstance(code_snippet, str):
            return code_snippet
        else:
            # Try multiple possible attributes
            if hasattr(code_snippet, 'clean_code') and code_snippet.clean_code:
                return code_snippet.clean_code
            elif hasattr(code_snippet, 'code') and code_snippet.code:
                return code_snippet.code
            elif hasattr(code_snippet, 'content') and code_snippet.content:
                return code_snippet.content
            elif hasattr(code_snippet, 'text') and code_snippet.text:
                return code_snippet.text
            else:
                # Try to convert to string
                return str(code_snippet)
    
    def _render_no_code_message(self):
        """Render a professional no-code message."""
        st.markdown(f"""
        <div class="no-code-message">
            <div class="icon">⚙️</div>
            <h3>{t('no_code_generated_yet')}</h3>
            <p>{t('generate_code_snippet_instruction')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_professional_code_display(self, code: str, known_problems: List[str] = None, instructor_mode: bool = False):
        """Render code with professional styling and enhanced features."""
        
        # Clean the code first to ensure proper formatting
        clean_code = self._clean_code_for_display(code)
        lines = clean_code.split('\n')
        line_count = len(lines)
        char_count = len(clean_code)
        
        # Enhanced code header
        self._render_code_header(line_count, char_count, known_problems, instructor_mode)
        
        # Code container with professional styling - pass the cleaned code
        self._render_code_container(clean_code, lines, known_problems)
         
    def _render_code_header(self, line_count: int, char_count: int, known_problems: List[str], instructor_mode: bool):
        """Render professional code header with metadata and controls."""
        st.markdown(f"""
        <div class="professional-code-header">
            <div class="header-content">
                <div>
                    <h3>☕ {t('java_code_review_challenge')}</h3>
                    <p>{t('review_code_below_instruction')}</p>
                </div>
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-value">{line_count}</div>
                        <div class="stat-label">{t('lines')}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{char_count}</div>
                        <div class="stat-label">{t('characters')}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_code_container(self, code: str, lines: List[str], known_problems: List[str] = None):
        """Render the main code container with enhanced styling."""
        
        # Main code container with header
        st.markdown(f"""
        <div class="code-container">
            <div class="code-header">
                <span>📄 Main.java</span>
                <span>☕ Java</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Clean the code and ensure proper line breaks
        clean_code = self._clean_code_for_display(code)
        
        # Use Streamlit's native code display
        st.code(add_line_numbers(clean_code), language="java")
    
    def _clean_code_for_display(self, code: str) -> str:
        """Clean and format code for proper display."""
        if not code:
            return ""
            
        # Convert to string if it's not already
        code_str = str(code)
        
        # Handle different types of line break representations
        # Replace literal \n with actual newlines
        code_str = code_str.replace('\\n', '\n')
        
        # Handle \r\n (Windows) and \r (Mac) line endings
        code_str = code_str.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split into lines and clean each line
        lines = code_str.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Strip trailing whitespace but preserve leading indentation
            cleaned_line = line.rstrip()
            cleaned_lines.append(cleaned_line)
        
        # Join lines back together
        result = '\n'.join(cleaned_lines)
        
        # Remove excessive empty lines (more than 2 consecutive)
        import re
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result
    
    def render_review_input(self, 
                          student_review: str = "", 
                          on_submit_callback: Callable[[str], None] = None,
                          iteration_count: int = 1,
                          max_iterations: int = 3,
                          targeted_guidance: str = None,
                          review_analysis: Dict[str, Any] = None) -> None:
        """
        Render a professional text area for student review input with enhanced guidance.
        
        Args:
            student_review: Initial value for the text area
            on_submit_callback: Callback function when review is submitted
            iteration_count: Current iteration number
            max_iterations: Maximum number of iterations
            targeted_guidance: Optional guidance for the student
            review_analysis: Optional analysis of previous review attempt
        """
        # Enhanced review container
        st.markdown('<div class="enhanced-review-container">', unsafe_allow_html=True)
        
        # Enhanced review header
        self._render_enhanced_review_header(iteration_count, max_iterations)
        
        # Guidance and history layout with enhanced styling
        if targeted_guidance:
            self._render_enhanced_guidance_section(targeted_guidance, review_analysis, student_review, iteration_count)
        
        # Enhanced review guidelines
        self._render_enhanced_review_guidelines()
        
        # Enhanced review input and submission
        submitted = self._render_enhanced_review_form(iteration_count, on_submit_callback)
        
        # Close review container
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_enhanced_review_header(self, iteration_count: int, max_iterations: int) -> None:
        """Render enhanced review header with better styling."""
        progress_percentage = ((iteration_count - 1) / max_iterations) * 100
        
        st.markdown(f"""
        <div class="enhanced-review-header">
            <div class="progress-bar" style="width: {progress_percentage}%;"></div>
            <div class="header-content">
                <div>
                    <h3>📝 {t("submit_review_section")}</h3>
                    <p>{t('provide_detailed_review')}</p>
                </div>
                <div class="iteration-indicator">
                    <div class="iteration-number">{iteration_count}</div>
                    <div class="iteration-text">{t('of')} {max_iterations}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_enhanced_guidance_section(self, targeted_guidance: str, review_analysis: Dict[str, Any], student_review: str, iteration_count: int) -> None:
        """Render enhanced guidance and history section."""
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if targeted_guidance and iteration_count > 1:
                st.markdown(f"""
                <div class="enhanced-guidance-section">
                    <div class="guidance-header">
                        <span class="guidance-icon">🎯</span>
                        <h4>{t("review_guidance")}</h4>
                    </div>
                    <div class="guidance-content">
                        {targeted_guidance}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if review_analysis:
                    identified_count = review_analysis.get(t("identified_count"), 0)
                    total_problems = review_analysis.get(t("total_problems"), 0)
                    percentage = review_analysis.get(t("identified_percentage"), 0)
                    
                    st.markdown(f"""
                    <div class="analysis-section">
                        <div class="analysis-header">
                            <span class="analysis-icon">📊</span>
                            <h4>{t("previous_results")}</h4>
                        </div>
                        <div class="analysis-stats">
                            <div class="stat-row">
                                <span>{t("issues_found")}:</span>
                                <strong>{identified_count} / {total_problems}</strong>
                            </div>
                            <div class="stat-row">
                                <span>{t("accuracy")}:</span>
                                <strong>{percentage:.1f}%</strong>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col2:
            if student_review and iteration_count > 1:
                st.markdown(f"""
                <div class="previous-review-section">
                    <h4>
                        <span class="review-icon">📝</span>
                        {t("previous_review")}
                    </h4>
                    <div class="previous-review-content">
                        {student_review.replace(chr(10), '<br>')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    def _render_enhanced_review_guidelines(self) -> None:
        """Render enhanced review guidelines with better presentation."""
        
        with st.expander(f"📋 {t('review_guidelines')}", expanded=False):
            # Use individual st.markdown calls instead of one large HTML block
            st.markdown(f"""
            <div class="guidelines-section">
                <h4>✨ {t('how_to_write_good_review')}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Use columns for better layout
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                **🎯 {t('be_specific')}**
                
                {t('point_out_exact_lines')}
                """)
                
            with col2:
                st.markdown(f"""
                **🔍 {t('be_comprehensive')}**
                
                {t('check_all_aspects')}
                """)
                
            with col3:
                st.markdown(f"""
                **💡 {t('be_constructive')}**
                
                {t('suggest_improvements')}
                """)
            
            st.markdown(f"### 🔍 {t('what_to_check_for')}")
            
            # Use columns for check items
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                **🔤 {t('syntax_compilation')}**
                - {t('missing_semicolons')}
                - {t('bracket_mismatches')}
                - {t('type_errors')}
                """)
                
            with col2:
                st.markdown(f"""
                **🐛 {t('logic_bugs')}**
                - {t('array_bounds_issues')}
                - {t('null_pointers')}
                - {t('loop_conditions')}
                """)
                
            with col3:
                st.markdown(f"""
                **⭐ {t('code_quality')}**
                - {t('naming_conventions')}
                - {t('code_formatting')}
                - {t('documentation')}
                """)
            
            # Example format
            st.markdown(f"### 📝 {t('example_review_format')}")
            st.code(t('review_format_example'), language="text")
    
    def _render_enhanced_review_form(self, iteration_count: int, on_submit_callback: Callable) -> bool:
        """
        Render enhanced review form with better UX and FIXED submit processing.
        FIXED: Use stable keys to ensure button clicks are properly detected.
        
        Args:
            iteration_count: Current iteration number
            on_submit_callback: Callback function for submit
            
        Returns:
            True if form was submitted successfully, False otherwise
        """
        
        # Enhanced form header
        st.markdown(f"""
        <div class="enhanced-input-section-header">
            <h4>
                <span class="input-icon">✍️</span>
                {t('your_review')}
            </h4>
            <p>{t('write_comprehensive_review')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # FIXED: Create stable keys that don't change across renders
        text_area_key = f"student_review_input_key"
        submit_button_key = f"submit_review_iter_key"
        clear_button_key = f"clear_review_iter_key"
        
        # Get initial value
        initial_value = ""
        if iteration_count > 1 and text_area_key in st.session_state:
            initial_value = st.session_state[text_area_key]
        
        # Enhanced review input with better styling
        student_review_input = st.text_area(
            t("enter_your_review"),
            value=initial_value, 
            height=350,
            key=text_area_key,
            placeholder=t("review_placeholder"),
            label_visibility="collapsed",
            help=t("review_help_text")
        )
        
        # Enhanced buttons with better layout
        st.markdown('<div class="enhanced-button-container">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([8, 2])
        
        with col1:
            submit_text = t("submit_review_button") if iteration_count == 1 else f"{t('submit_review_button')} ({t('attempt')} {iteration_count})"
            # FIXED: Use stable key that doesn't change across renders
            submit_button = st.button(
                f"🚀 {submit_text}", 
                type="primary", 
                use_container_width=True,
                help=t("submit_review_help"),
                key=submit_button_key  # Stable key
            )
            
        with col2:
            # FIXED: Use stable key that doesn't change across renders
            clear_button = st.button(
                f"🗑️ {t('clear')}", 
                use_container_width=True,
                help=t("clear_review_help"),
                key=clear_button_key  # Stable key
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Handle buttons
        if clear_button:
            st.session_state[text_area_key] = ""
            st.rerun()
        
        if submit_button:
            # FIXED: Enhanced submit button processing with better validation and error handling
            try:
                logger.info(f"Submit button clicked for iteration {iteration_count}")
                logger.info(f"Student review input: '{student_review_input[:100]}...' (length: {len(student_review_input)})")
                
                # Validate input
                if not student_review_input or not student_review_input.strip():
                    st.error(f"❌ {t('please_enter_review')}")
                    return False
                
                review_text = student_review_input.strip()
                
                if len(review_text) < 20:
                    st.warning(t("review_too_short_warning"))
                    return False
                
                # Additional validation - check for meaningful content
                if len(review_text.split()) < 5:
                    st.warning("Please provide a more detailed review with at least 5 words.")
                    return False
                
                # Show processing indicator
                with st.spinner(f"🔄 {t('processing_review')}..."):
                    logger.debug(f"Processing review submission for iteration {iteration_count}")
                    logger.debug(f"Review text length: {len(review_text)} characters")
                    
                    # Call the submit callback
                    if on_submit_callback:
                        try:
                            # FIXED: Better error handling and state management
                            result = on_submit_callback(review_text)
                            
                            if result is not False:
                                # Mark as submitted
                                submit_key = f"submitted_review_{iteration_count}"
                                if submit_key not in st.session_state:
                                    st.session_state[submit_key] = review_text
                                    
                                logger.debug(f"Review successfully submitted for iteration {iteration_count}")
                                
                                # Show success message briefly
                                success_placeholder = st.empty()
                                success_placeholder.success(f"✅ {t('review_submitted_successfully')}")
                                time.sleep(1)
                                success_placeholder.empty()
                                
                                return True
                            else:
                                logger.warning(f"Submit callback returned False for iteration {iteration_count}")
                                st.error(f"❌ {t('error')} {t('processing_review')}. Please try again.")
                                return False
                                
                        except Exception as callback_error:
                            logger.error(f"Exception in submit callback: {str(callback_error)}", exc_info=True)
                            st.error(f"❌ {t('error')} {t('processing_review')}: {str(callback_error)}")
                            return False
                    else:
                        logger.error("No submit callback provided")
                        st.error(f"❌ {t('error')}: No submission handler available")
                        return False
                        
            except Exception as e:
                logger.error(f"Exception in submit button processing: {str(e)}", exc_info=True)
                st.error(f"❌ {t('error')} {t('processing_review')}: {str(e)}")
                return False
        
        return False

def render_review_tab(workflow, code_display_ui, auth_ui=None):
    """
    Render the review tab UI with enhanced styling and better user experience.
    
    Args:
        workflow: JavaCodeReviewGraph workflow
        code_display_ui: CodeDisplayUI instance for displaying code
        auth_ui: Optional AuthUI instance for updating stats
    """
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <h2 style="
            color: #495057; 
            margin-bottom: 0.5rem;
            font-size: 2rem;
            font-weight: 700;
        ">
            📋 {t('review_java_code')}
        </h2>
        <p style="color: #6c757d; margin: 0; font-size: 1.1rem;">
            {t('carefully_examine_code')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check workflow state
    if not hasattr(st.session_state, 'workflow_state') or not st.session_state.workflow_state:
        st.markdown(f"""
        <div class="unavailable-state">
            <div class="state-icon">⚙️</div>
            <h3>{t('no_code_available')}</h3>
            <p>{t('generate_code_snippet_first')}</p>
            <div class="action-hint">👈 {t('go_to_generate_tab')}</div>
        </div>
        """, unsafe_allow_html=True)
        return
        
    # Check code snippet
    if not hasattr(st.session_state.workflow_state, 'code_snippet') or not st.session_state.workflow_state.code_snippet:
        st.markdown(f"""
        <div class="incomplete-state">
            <div class="state-icon">⚠️</div>
            <h3>{t('code_generation_incomplete')}</h3>
            <p>{t('complete_code_generation_before_review')}</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Get known problems for instructor view
    known_problems = _extract_known_problems(st.session_state.workflow_state)
    
    # Display code with enhanced styling
    code_display_ui.render_code_display(
        getattr(st.session_state.workflow_state, 'code_snippet', None),
        known_problems=known_problems
    )
    
    # Handle review submission logic
    _handle_review_submission(workflow, code_display_ui, auth_ui)

def _extract_known_problems(state) -> List[str]:
    """Extract known problems from workflow state."""
    known_problems = []
    
    # Extract from evaluation result
    evaluation_result = getattr(state, 'evaluation_result', None)
    if evaluation_result and t('found_errors') in evaluation_result:
        known_problems = evaluation_result[t('found_errors')]
    
    # Fallback to selected errors
    if not known_problems:
        selected_specific_errors = getattr(state, 'selected_specific_errors', None)
        if selected_specific_errors:
            known_problems = [
                f"{error.get(t('type'), '').upper()} - {error.get(t('name'), '')}" 
                for error in selected_specific_errors
            ]
    
    return known_problems

def _handle_review_submission(workflow, code_display_ui, auth_ui=None):
    """
    Handle the review submission logic with enhanced UX and immediate stats update.
    FIXED: Improved submit processing and better error handling.
    """
    # Get current review state
    state = st.session_state.workflow_state
    current_iteration = getattr(state, 'current_iteration', 1)
    max_iterations = getattr(state, 'max_iterations', 3)
    
    # Get review data
    review_history = getattr(state, 'review_history', None)
    latest_review = review_history[-1] if review_history and len(review_history) > 0 else None
    
    # Extract review information
    targeted_guidance = None
    review_analysis = None
    student_review = ""
    
    if latest_review:
        targeted_guidance = getattr(latest_review, "targeted_guidance", None)
        review_analysis = getattr(latest_review, "analysis", None)
        student_review = getattr(latest_review, 'student_review', "")
    
    # Check if all errors found
    all_errors_found = False
    if review_analysis:
        identified_count = review_analysis.get(t('identified_count'), 0)
        total_problems = review_analysis.get(t('total_problems'), 0)
        if identified_count == total_problems and total_problems > 0:
            all_errors_found = True
    
    # Handle submission logic
    review_sufficient = getattr(state, 'review_sufficient', False)
    
    if current_iteration <= max_iterations and not review_sufficient and not all_errors_found:
        def on_submit_review(review_text):
            """FIXED: Enhanced submit callback with better error handling and logging."""
            try:
                logger.debug(f"Submit callback triggered for iteration {current_iteration}")
                logger.debug(f"Review text: {review_text[:100]}...")  # Log first 100 chars
                
                # Process the student review
                result = _process_student_review(workflow, review_text)
                
                if result:
                    logger.debug(f"Review processing completed successfully for iteration {current_iteration}")
                else:
                    logger.warning(f"Review processing returned False for iteration {current_iteration}")
                
                return result
                
            except Exception as e:
                logger.error(f"Exception in submit callback: {str(e)}", exc_info=True)
                st.error(f"Submit processing failed: {str(e)}")
                return False
        
        code_display_ui.render_review_input(
            student_review=student_review,
            on_submit_callback=on_submit_review,
            iteration_count=current_iteration,
            max_iterations=max_iterations,
            targeted_guidance=targeted_guidance,
            review_analysis=review_analysis
        )
    else:
        if review_sufficient or all_errors_found:
            # Enhanced success message
            st.markdown(f"""
            <div class="success-message">
                <div class="success-icon">🎉</div>
                <h3>{t('excellent_work')}</h3>
                <p>
                    {t('successfully_identified_issues')}
                    <br>
                    {t('check_feedback_tab')}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if auth_ui and review_analysis:
                try:
                    # Update user statistics
                    accuracy = review_analysis.get(t("accuracy_percentage"), 
                                                 review_analysis.get(t("identified_percentage"), 0))
                    identified_count = review_analysis.get(t("identified_count"), 0)
                    
                    # Create a unique key to prevent duplicate updates
                    stats_key = f"review_tab_stats_updated_{current_iteration}_{identified_count}"
                    
                    if stats_key not in st.session_state:
                        logger.debug(f"Updating stats immediately: accuracy={accuracy:.1f}%, score={identified_count}")
                        result = auth_ui.update_review_stats(accuracy, identified_count)
                        
                        if result and result.get("success", False):
                            logger.debug("Stats updated successfully in review tab")
                            st.session_state[stats_key] = True
                            
                            # Update session state with new values
                            if "auth" in st.session_state and "user_info" in st.session_state.auth:
                                user_info = st.session_state.auth["user_info"]
                                if "reviews_completed" in result:
                                    user_info["reviews_completed"] = result["reviews_completed"]
                                if "score" in result:
                                    user_info["score"] = result["score"]
                                    
                                logger.debug(f"Updated session state: reviews={user_info.get('reviews_completed')}, score={user_info.get('score')}")
                        else:
                            logger.error(f"Failed to update stats in review tab: {result}")
                            
                except Exception as e:
                    logger.error(f"Error updating stats in review tab: {str(e)}")
            
            # Auto-switch to feedback tab with enhanced transition
            if not st.session_state.get("feedback_tab_switch_attempted", False):
                st.session_state.feedback_tab_switch_attempted = True
                st.session_state.active_tab = 2
                
                # Add celebration effect
                st.balloons()
                time.sleep(2)
                st.rerun()
        else:
            # Enhanced iterations completed message
            st.markdown(f"""
            <div class="warning-message">
                <div class="warning-icon">⏰</div>
                <h3>{t('review_session_complete')}</h3>
                <p>
                    {t('completed_review_attempts', max_iterations=max_iterations)}
                    <br>
                    {t('check_feedback_tab_results')}
                </p>
            </div>
            """, unsafe_allow_html=True)

def _process_student_review(workflow, student_review: str) -> bool:
    """
    Process a student review using the compiled LangGraph workflow with enhanced feedback.
    FIXED: Improved error handling, state validation, and processing logic.
    """
    try:
        logger.debug("Starting student review processing")
        
        # Enhanced status tracking
        with st.status(t("processing_review"), expanded=True) as status:
            
            # Step 1: Validate workflow state
            status.update(label="🔍 Validating workflow state...", state="running")
            
            if not hasattr(st.session_state, 'workflow_state'):
                error_msg = "Workflow state not found"
                logger.error(error_msg)
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {error_msg}. {t('please_generate_problem_first')}")
                return False
                
            state = st.session_state.workflow_state
            
            # Step 2: Validate code snippet
            status.update(label="🔍 Validating code snippet...", state="running")
            
            if not hasattr(state, "code_snippet") or state.code_snippet is None:
                error_msg = "No code snippet available"
                logger.error(error_msg)
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {error_msg}. {t('please_generate_problem_first')}")
                return False
            
            # Step 3: Validate review content
            status.update(label="🔍 Validating review content...", state="running")
            
            if not student_review or not student_review.strip():
                error_msg = "Review cannot be empty"
                logger.error(error_msg)
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {t('please_enter_review')}")
                return False
            
            review_text = student_review.strip()
            
            if len(review_text) < 10:
                error_msg = "Review too short"
                logger.error(error_msg)
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {t('provide_detailed_review_minimum')}")
                return False
            
            # Step 4: Validate review format (if evaluator available)
            if hasattr(workflow, 'workflow_nodes') and hasattr(workflow.workflow_nodes, 'evaluator'):
                evaluator = workflow.workflow_nodes.evaluator
                if evaluator and hasattr(evaluator, 'validate_review_format'):
                    is_valid, reason = evaluator.validate_review_format(review_text)
                    if not is_valid:
                        logger.error(f"Review format validation failed: {reason}")
                        status.update(label=f"❌ {t('error')}: {reason}", state="error")
                        st.error(f"❌ {reason}")
                        return False
            
            # Step 5: Submit to workflow
            status.update(label="🚀 Submitting to workflow...", state="running")
            
            logger.info("Submitting review through LangGraph workflow")
            logger.info(f"Current state step: {getattr(state, 'current_step', 'unknown')}")
            logger.info(f"Current iteration: {getattr(state, 'current_iteration', 'unknown')}")
            
            try:
                # FIXED: Enhanced workflow submission with better error handling
                raw_updated_state = workflow.submit_review(state, review_text)
                
                if not raw_updated_state:
                    error_msg = "Workflow returned empty state"
                    logger.error(error_msg)
                    status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                    st.error(f"❌ {error_msg}")
                    return False
                
            except Exception as workflow_error:
                error_msg = f"Workflow execution failed: {str(workflow_error)}"
                logger.error(error_msg, exc_info=True)
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {error_msg}")
                return False
            
            # Step 6: Process workflow result
            status.update(label="⚙️ Processing workflow result...", state="running")
            
            # Helper function to safely access state values
            def _safe_get_state_value(state, key: str, default=None):
                """Safely get a value from a state object."""
                try:
                    if hasattr(state, key):
                        return getattr(state, key)
                    if hasattr(state, '__getitem__'):
                        try:
                            return state[key]
                        except (KeyError, TypeError):
                            pass
                    if hasattr(state, 'get'):
                        return state.get(key, default)
                    return default
                except Exception:
                    return default
            
            # Check for errors using safe access
            error = _safe_get_state_value(raw_updated_state, 'error')
            if error:
                logger.error(f"Workflow returned error: {error}")
                status.update(label=f"❌ {t('error')}: {error}", state="error")
                st.error(f"❌ {error}")
                return False
            
            # Step 7: Convert state if needed
            status.update(label="🔄 Converting state...", state="running")
            
            # Import WorkflowState if needed
            from state_schema import WorkflowState
            
            # Convert to WorkflowState if needed (handle AddableValuesDict)
            if not isinstance(raw_updated_state, WorkflowState):
                try:
                    # Extract all fields safely
                    state_dict = {}
                    workflow_state_fields = [
                        'current_step', 'code_length', 'difficulty_level', 'domain',
                        'error_count_start', 'error_count_end', 'selected_error_categories',
                        'selected_specific_errors', 'code_snippet', 'original_error_count',
                        'evaluation_attempts', 'max_evaluation_attempts', 'evaluation_result',
                        'code_generation_feedback', 'pending_review', 'current_iteration',
                        'max_iterations', 'review_sufficient', 'review_history',
                        'comparison_report', 'error', 'final_summary'
                    ]
                    
                    for field in workflow_state_fields:
                        value = _safe_get_state_value(raw_updated_state, field)
                        if value is not None:
                            state_dict[field] = value
                    
                    updated_state = WorkflowState(**state_dict)
                    logger.debug("Successfully converted state to WorkflowState")
                    
                except Exception as conversion_error:
                    logger.error(f"Error converting state: {str(conversion_error)}")
                    # Fallback: store the raw state and continue
                    updated_state = raw_updated_state
            else:
                updated_state = raw_updated_state
            
            # Step 8: Update session state
            status.update(label="💾 Updating session state...", state="running")
            
            st.session_state.workflow_state = updated_state
            
            # Step 9: Verify processing success
            status.update(label="✅ Verifying processing...", state="running")
            
            # Check if workflow completed successfully using safe access
            review_history = _safe_get_state_value(updated_state, 'review_history')
            current_iteration = _safe_get_state_value(updated_state, 'current_iteration', 1)
            
            if review_history and len(review_history) > 0:
                logger.debug(f"Review processing completed successfully. History length: {len(review_history)}")
                status.update(label=f"✅ {t('analysis_complete_processed')}", state="complete")
                
                # Brief success display
                time.sleep(1)
                st.rerun()
                return True
            else:
                logger.warning("Review processing may not have completed properly - no review history found")
                status.update(label="⚠️ Processing completed with warnings", state="complete")
                
                # Still rerun to update UI
                time.sleep(1)
                st.rerun()
                return True
            
    except Exception as e:
        error_msg = f"Exception in review processing: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(f"❌ {error_msg}")
        return False