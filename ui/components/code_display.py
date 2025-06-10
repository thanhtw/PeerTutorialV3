# ui/components/code_display.py - FIXED version

"""
Enhanced Code Display UI component for Java Peer Review Training System.

proper session state management.
"""

import streamlit as st
import time
import logging
import datetime
import re
from typing import List, Dict, Any, Optional, Callable

from utils.code_utils import add_line_numbers
from utils.language_utils import t
from analytics.behavior_tracker import behavior_tracker

# Configure logging
logger = logging.getLogger(__name__)

class CodeDisplayUI:
    """
    Enhanced UI Component for displaying Java code snippets with professional styling.
    FIXED: Resolved setIn error issues with proper state management.
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
            # Use clean_code first if available (since it's specifically for display)
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
        
        lines = code.split('\n')
        line_count = len(lines)
        char_count = len(code)
        
        # Enhanced code header
        self._render_code_header(line_count, char_count, known_problems, instructor_mode)
        
        # Code container with professional styling
        self._render_code_container(code, lines, known_problems)
         
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
        
        # Code is already clean from CodeSnippet.clean_code, just ensure proper format
        display_code = self._ensure_proper_line_breaks(code)
        
        # Use Streamlit's native code display
        st.code(add_line_numbers(display_code), language="java")
    
    def _ensure_proper_line_breaks(self, code: str) -> str:
        """Ensure proper line breaks in code without heavy cleaning."""
        if not code:
            return ""
            
        # Convert to string if it's not already
        code_str = str(code)
        
        # Handle different types of line break representations (minimal processing)
        # Replace literal \n with actual newlines if needed
        if '\\n' in code_str and '\n' not in code_str:
            code_str = code_str.replace('\\n', '\n')
        
        # Handle \r\n (Windows) and \r (Mac) line endings
        code_str = code_str.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive empty lines (more than 2 consecutive)
        import re
        code_str = re.sub(r'\n{3,}', '\n\n', code_str)
        
        return code_str.strip()
    
    def render_review_input(self, 
                          student_review: str = "", 
                          on_submit_callback: Callable[[str], None] = None,
                          iteration_count: int = 1,
                          max_iterations: int = 3,
                          targeted_guidance: str = None,
                          review_analysis: Dict[str, Any] = None) -> None:
        """       
        Uses better state management and avoids multiple st.rerun() calls.
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
        
        # FIXED: Enhanced review input and submission
        self._render_fixed_review_form(iteration_count, on_submit_callback)
        
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
    
    def _render_fixed_review_form(self, iteration_count: int, on_submit_callback: Callable) -> bool:
        """       
        Uses session state flags instead of immediate st.rerun() calls.
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
        
        # FIXED: Use timestamp-based keys to avoid conflicts
        text_area_key = f"review_input"
        submit_button_key = f"submit_review"
        clear_button_key = f"clear_review"
        
        # FIXED: Check for success flag and clear input accordingly
        success_flag = f"review_submitted_success_{iteration_count}"
        if st.session_state.get(success_flag, False):
            # Clear the success flag
            del st.session_state[success_flag]
            # Don't set initial value if review was just submitted
            initial_value = ""
        else:
            initial_value = st.session_state.get(f"review_draft_{iteration_count}", "")
        
        # Enhanced review input
        student_review_input = st.text_area(
            t("enter_your_review"),
            value=initial_value, 
            height=350,
            key=text_area_key,
            placeholder=t("review_placeholder"),
            label_visibility="collapsed",
            help=t("review_help_text")
        )
        
        # Save draft to session state (for persistence)
        if student_review_input:
            st.session_state[f"review_draft_{iteration_count}"] = student_review_input
        
        # Enhanced buttons with better layout
        st.markdown('<div class="enhanced-button-container">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([8, 2])
        
        with col1:
            submit_text = t("submit_review_button") if iteration_count == 1 else f"{t('submit_review_button')} ({t('attempt')} {iteration_count})"
            submit_button = st.button(
                f"🚀 {submit_text}", 
                type="primary", 
                use_container_width=True,
                help=t("submit_review_help"),
                key=submit_button_key
            )
            
        with col2:
            clear_button = st.button(
                f"🗑️ {t('clear')}", 
                use_container_width=True,
                help=t("clear_review_help"),
                key=clear_button_key
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # FIXED: Handle clear button with session state flag - NO RERUN
        if clear_button:
            # Clear the draft
            if f"review_draft_{iteration_count}" in st.session_state:
                del st.session_state[f"review_draft_{iteration_count}"]
            st.info("Review cleared. Please refresh if the text area is not empty.")
            return False
        
        # FIXED: Handle submit button with better error handling - NO IMMEDIATE RERUN
        if submit_button:
            return self._process_review_submission(
                student_review_input, 
                iteration_count, 
                on_submit_callback,
                success_flag
            )
        
        return False
    
    def _process_review_submission(self, review_text: str, iteration_count: int, 
                                 on_submit_callback: Callable, success_flag: str) -> bool:
        """
        FIXED: Process review submission without causing setIn errors and only rerun when complete.
        """
        try:
            logger.info(f"Processing review submission for iteration {iteration_count}")
            logger.info(f"Review text length: {len(review_text)} characters")
            
            # Validate input
            if not review_text or not review_text.strip():
                st.error(f"❌ {t('please_enter_review')}")
                return False
            
            cleaned_review = review_text.strip()
            
            if len(cleaned_review) < 20:
                st.warning(t("review_too_short_warning"))
                return False
            
            # Additional validation - check for meaningful content
            if len(cleaned_review.split()) < 5:
                st.warning("Please provide a more detailed review with at least 5 words.")
                return False
            
            # Show processing indicator
            with st.spinner(f"🔄 {t('processing_review')}..."):
                logger.info(f"Calling submit callback with review: '{cleaned_review[:100]}...'")
                
                # Call the submit callback
                if on_submit_callback:
                    try:
                        logger.info("Executing callback function...")
                        result = on_submit_callback(cleaned_review)
                        logger.info(f"Callback returned: {result} (type: {type(result)})")
                        
                        # FIXED: More lenient success check
                        if result is True or result is None:  # Accept True or None as success
                          
                            st.session_state[success_flag] = True
                            
                            # Clear the draft
                            draft_key = f"review_draft_{iteration_count}"
                            if draft_key in st.session_state:
                                del st.session_state[draft_key]
                            
                            logger.info(f"Review successfully submitted for iteration {iteration_count}")
                            
                            # Show success message without immediate rerun
                            st.success("✅ Review submitted successfully!")       
                            
                            # FIXED: Only rerun after a delay to ensure processing is complete
                            time.sleep(1)
                            st.rerun()
                            return True
                        else:
                            logger.warning(f"Submit callback returned: {result} for iteration {iteration_count}")
                            st.error(f"❌ {t('error')} {t('processing_review')}. Callback returned: {result}")
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
            logger.error(f"Exception in review submission processing: {str(e)}", exc_info=True)
            st.error(f"❌ {t('error')} {t('processing_review')}: {str(e)}")
            return False


def render_review_tab(workflow, code_display_ui, auth_ui=None):
    """
    Render the review tab UI with enhanced debugging and state management.
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
    
    # ADDED: Debug information (can be enabled for troubleshooting)
    if st.session_state.get("debug_mode", False):
        with st.expander("🔧 Debug Information", expanded=False):
            st.code(f"""
Debug Info:
- Workflow: {type(workflow) if workflow else 'None'}
- Has workflow_state: {hasattr(st.session_state, 'workflow_state')}
- Workflow state type: {type(st.session_state.workflow_state) if hasattr(st.session_state, 'workflow_state') else 'None'}
- Has code_snippet: {hasattr(st.session_state.workflow_state, 'code_snippet') if hasattr(st.session_state, 'workflow_state') else False}
- Current iteration: {getattr(st.session_state.workflow_state, 'current_iteration', 'N/A') if hasattr(st.session_state, 'workflow_state') else 'N/A'}
- Current step: {getattr(st.session_state.workflow_state, 'current_step', 'N/A') if hasattr(st.session_state, 'workflow_state') else 'N/A'}
            """)
            
            if st.button("Toggle Debug Mode Off"):
                st.session_state.debug_mode = False
                st.rerun()
    else:
        # Small debug toggle button
        if st.button("🔧 Debug", help="Show debug information"):
            st.session_state.debug_mode = True
            st.rerun()
    
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
    
    # Validate workflow
    if not workflow:
        st.error("❌ No workflow available for processing reviews. Please refresh the page.")
        return
    
    # Get known problems for instructor view
    known_problems = _extract_known_problems(st.session_state.workflow_state)
    
    # Display the code
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
    Handle review submission with better state management and NO automatic tab switching.
    """
    # Get current review state
    state = st.session_state.workflow_state
    current_iteration = getattr(state, 'current_iteration', 1)
    max_iterations = getattr(state, 'max_iterations', 3)
    
    logger.info(f"Handling review submission - iteration {current_iteration}/{max_iterations}")
    
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
            """FIXED: Submit callback with enhanced error handling and debugging."""
            try:
                logger.info(f"Submit callback triggered for iteration {current_iteration}")
                logger.info(f"Review text: '{review_text[:100]}...' (length: {len(review_text)})")
                
                # Validate workflow and state
                if not workflow:
                    logger.error("No workflow available for review processing")
                    st.error("❌ No workflow available for processing reviews")
                    return False
                
                if not hasattr(st.session_state, 'workflow_state') or not st.session_state.workflow_state:
                    logger.error("No workflow state available")
                    st.error("❌ No workflow state available. Please generate code first.")
                    return False
                
                # Process the student review
                logger.info("Calling _process_student_review...")
                result = _process_student_review_with_comprehensive_tracking(workflow, review_text)
                logger.info(f"_process_student_review returned: {result}")
                
                if result is True:
                    logger.info(f"Review processing completed successfully for iteration {current_iteration}")
                    return True
                elif result is None:
                    logger.info(f"Review processing completed (returned None) for iteration {current_iteration}")
                    return True  # Treat None as success
                else:
                    logger.warning(f"Review processing returned: {result} for iteration {current_iteration}")
                    return False
                
            except Exception as e:
                logger.error(f"Exception in submit callback: {str(e)}", exc_info=True)
                st.error(f"Submit processing failed: {str(e)}")
                return False
        
        # Render the review input with the callback
        logger.info("Rendering review input with callback")
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
            
            # Update user statistics if available
            if auth_ui and review_analysis:
                try:
                    accuracy = review_analysis.get(t("accuracy_percentage"), 
                                                 review_analysis.get(t("identified_percentage"), 0))
                    identified_count = review_analysis.get(t("identified_count"), 0)
                    
                    # Create a unique key to prevent duplicate updates
                    stats_key = f"review_tab_stats_updated_{current_iteration}_{identified_count}"
                    
                    if stats_key not in st.session_state:
                        logger.debug(f"Updating stats: accuracy={accuracy:.1f}%, score={identified_count}")
                        result = auth_ui.update_review_stats(accuracy, identified_count)
                        
                        if result and result.get("success", False):
                            st.session_state[stats_key] = True
                            logger.debug("Stats updated successfully in review tab")
                            
                except Exception as e:
                    logger.error(f"Error updating stats in review tab: {str(e)}")
            
            # FIXED: Remove automatic tab switching - let user decide when to view feedback
            # Only show a button to go to feedback if user wants
            if not st.session_state.get("feedback_tab_offered", False):
                st.session_state.feedback_tab_offered = True
                st.balloons()
                
                
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
            
            # FIXED: Offer feedback button instead of automatic switching
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("📊 View Results", key="go_to_results", type="primary", use_container_width=True):
                    st.session_state.active_tab = 3
                    st.rerun()
 
def _process_student_review_with_comprehensive_tracking(workflow, student_review: str) -> bool:
    """Enhanced review processing with detailed behavior tracking."""
    try:
        user_id = st.session_state.auth.get("user_id") if "auth" in st.session_state else None
        review_start_time = time.time()
        
        logger.debug("Starting student review processing")
        logger.debug(f"Processing review: '{student_review[:100]}...' (length: {len(student_review)})")
        
        # Track review submission
        if user_id:
            current_iteration = getattr(st.session_state.workflow_state, 'current_iteration', 1)
            max_iterations = getattr(st.session_state.workflow_state, 'max_iterations', 3)
            
            # Analyze review content for tracking
            review_analysis = {
                "review_length": len(student_review),
                "word_count": len(student_review.split()),
                "line_count": len(student_review.split('\n')),
                "has_line_references": bool(re.search(r'line\s*\d+', student_review.lower())),
                "iteration": current_iteration,
                "max_iterations": max_iterations
            }
            
            # Update workflow step
            behavior_tracker.update_workflow_step(
                user_id=user_id,
                new_step="review_analysis",
                step_data={
                    "review_submitted": True,
                    "review_iteration": current_iteration,
                    "review_analysis": review_analysis
                }
            )
        
        # Enhanced status tracking with detailed steps
        with st.status(t("processing_review"), expanded=True) as status:
            
            # Validation steps with tracking
            status.update(label="🔍 Validating workflow...", state="running")
            
            if not workflow:
                error_msg = "No workflow provided"
                logger.error(error_msg)
                
                if user_id:
                    behavior_tracker.log_interaction(
                        user_id=user_id,
                        interaction_type="error",
                        interaction_category="main_workflow",
                        component="workflow_validator",
                        action="workflow_validation_failed",
                        success=False,
                        error_message=error_msg
                    )
                
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {error_msg}")
                return False
            
            # Step 2: Validate workflow state
            status.update(label="🔍 Validating workflow state...", state="running")
            
            if not hasattr(st.session_state, 'workflow_state'):
                error_msg = "Workflow state not found"
                logger.error(error_msg)
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {error_msg}. {t('please_generate_problem_first')}")
                return False
                
            state = st.session_state.workflow_state
            logger.debug(f"Current workflow state: step={getattr(state, 'current_step', 'unknown')}, iteration={getattr(state, 'current_iteration', 'unknown')}")
            
            # Step 3: Validate code snippet
            status.update(label="🔍 Validating code snippet...", state="running")
            
            if not hasattr(state, "code_snippet") or state.code_snippet is None:
                error_msg = "No code snippet available"
                logger.error(error_msg)
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {error_msg}. {t('please_generate_problem_first')}")
                return False
            
            # Step 4: Validate review content
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
            
            # Step 5: Submit to workflow
            status.update(label="🚀 Analyzing review with AI...", state="running")
            
            try:
                analysis_start_time = time.time()
                raw_updated_state = workflow.submit_review(st.session_state.workflow_state, student_review)
                analysis_duration = time.time() - analysis_start_time
                
                logger.debug(f"Workflow analysis completed in {analysis_duration:.2f}s")
                
                if not raw_updated_state:
                    error_msg = "Workflow returned empty state"
                    
                    if user_id:
                        behavior_tracker.log_interaction(
                            user_id=user_id,
                            interaction_type="error",
                            interaction_category="main_workflow",
                            component="workflow_execution",
                            action="workflow_empty_response",
                            success=False,
                            error_message=error_msg,
                            time_spent_seconds=int(analysis_duration)
                        )
                    
                    status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                    st.error(f"❌ {error_msg}")
                    return False
                
            except Exception as workflow_error:
                analysis_duration = time.time() - analysis_start_time
                error_msg = f"Workflow execution failed: {str(workflow_error)}"
                logger.error(error_msg, exc_info=True)
                
                if user_id:
                    behavior_tracker.log_interaction(
                        user_id=user_id,
                        interaction_type="error",
                        interaction_category="main_workflow",
                        component="workflow_execution",
                        action="workflow_execution_exception",
                        success=False,
                        error_message=str(workflow_error),
                        time_spent_seconds=int(analysis_duration)
                    )
                
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {error_msg}")
                return False
            
            # Process results with tracking
            status.update(label="📊 Processing analysis results...", state="running")
            
            error = getattr(raw_updated_state, 'error', None)
            if error:
                logger.error(f"Workflow returned error: {error}")
                
                if user_id:
                    behavior_tracker.log_interaction(
                        user_id=user_id,
                        interaction_type="error",
                        interaction_category="main_workflow",
                        component="workflow_result",
                        action="workflow_result_error",
                        success=False,
                        error_message=error,
                        time_spent_seconds=int(time.time() - review_start_time)
                    )
                
                status.update(label=f"❌ {t('error')}: {error}", state="error")
                st.error(f"❌ {error}")
                return False
            
            # Update session state
            status.update(label="💾 Updating session state...", state="running")
            
            st.session_state.workflow_state = raw_updated_state
            st.session_state.review_processing_success = True
            st.session_state.last_review_timestamp = time.time()
            
            # Extract results for tracking
            review_history = getattr(raw_updated_state, 'review_history', None)
            current_iteration = getattr(raw_updated_state, 'current_iteration', 1)
            review_sufficient = getattr(raw_updated_state, 'review_sufficient', False)
            
            total_processing_time = time.time() - review_start_time
            
            if review_history and len(review_history) > 0:
                logger.debug(f"Review processing completed successfully. History length: {len(review_history)}")
                
                # Track successful review processing
                if user_id:
                    latest_review = review_history[-1]
                    analysis_results = getattr(latest_review, 'analysis', {}) if hasattr(latest_review, 'analysis') else {}
                    
                    processing_details = {
                        "processing_duration": total_processing_time,
                        "analysis_duration": analysis_duration,
                        "review_iteration": current_iteration,
                        "review_sufficient": review_sufficient,
                        "analysis_results": {
                            "identified_count": analysis_results.get(t('identified_count'), 0),
                            "total_problems": analysis_results.get(t('total_problems'), 0),
                            "accuracy_percentage": analysis_results.get(t('identified_percentage'), 0)
                        }
                    }
                    
                    behavior_tracker.log_interaction(
                        user_id=user_id,
                        interaction_type="success",
                        interaction_category="main_workflow",
                        component="review_processor",
                        action="review_processing_success",
                        time_spent_seconds=int(total_processing_time),
                        details=processing_details
                    )
                    
                    # Check for workflow completion
                    if review_sufficient or current_iteration > getattr(raw_updated_state, 'max_iterations', 3):
                        behavior_tracker.complete_workflow(
                            user_id=user_id,
                            final_results={
                                "identified_count": analysis_results.get(t('identified_count'), 0),
                                "total_problems": analysis_results.get(t('total_problems'), 0),
                                "accuracy": analysis_results.get(t('identified_percentage'), 0),
                                "iterations_used": current_iteration - 1,
                                "review_sufficient": review_sufficient,
                                "total_processing_time": total_processing_time
                            }
                        )
                
                status.update(label=f"✅ {t('analysis_complete_processed')}", state="complete")
                return True
            else:
                logger.warning("Review processing may not have completed properly - no review history found")
                
                if user_id:
                    behavior_tracker.log_interaction(
                        user_id=user_id,
                        interaction_type="warning",
                        interaction_category="main_workflow",
                        component="review_processor",
                        action="review_processing_incomplete",
                        time_spent_seconds=int(total_processing_time),
                        details={"warning": "No review history found"}
                    )
                
                status.update(label="⚠️ Processing completed with warnings", state="complete")
                return True
            
    except Exception as e:
        total_time = time.time() - review_start_time
        error_msg = f"Exception in review processing: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Track processing exception
        if user_id:
            behavior_tracker.log_interaction(
                user_id=user_id,
                interaction_type="error",
                interaction_category="main_workflow",
                component="review_processor",
                action="review_processing_exception",
                success=False,
                error_message=str(e),
                time_spent_seconds=int(total_time)
            )
        
        st.error(f"❌ {error_msg}")
        return False



