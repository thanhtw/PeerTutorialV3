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

from utils.code_utils import add_line_numbers, _log_user_interaction_code_display
from utils.language_utils import t, get_current_language


# Configure logging
logger = logging.getLogger(__name__)

class CodeDisplayUI:
    """
    Enhanced UI Component for displaying Java code snippets with professional styling.
    FIXED: Resolved setIn error issues with proper state management.
    """
    
    def __init__(self):
        """Initialize the CodeDisplayUI component."""
        self.current_language = get_current_language()
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
        FIXED: Enhanced review input with comprehensive validation.
        """
        # Validate input parameters
        iteration_count = max(1, int(iteration_count)) if iteration_count else 1
        max_iterations = max(1, int(max_iterations)) if max_iterations else 3
        student_review = str(student_review) if student_review else ""
        
        # Enhanced review container
        st.markdown('<div class="enhanced-review-container">', unsafe_allow_html=True)
        
        # Enhanced review header
        self._render_enhanced_review_header(iteration_count, max_iterations)
        
        # Guidance and history layout with enhanced styling
        if targeted_guidance:
            self._render_enhanced_guidance_section(targeted_guidance, review_analysis, student_review, iteration_count)
        
        # Enhanced review guidelines
        self._render_enhanced_review_guidelines()
        
        # FIXED: Enhanced review input and submission with validation
        self._render_review_form_fixed(iteration_count, on_submit_callback)
        
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
    
    def _render_review_form_fixed(self, iteration_count: int, on_submit_callback: Callable) -> bool:
        """
        FIXED: Simplified review form for fixed workflow.
        """
        # Basic validation
        if not callable(on_submit_callback):
            st.error("❌ Invalid submission handler. Please refresh the page.")
            return False
        
        # Simple form keys
        text_area_key = f"review_input_iter_{iteration_count}"
        submit_button_key = f"submit_review_iter_{iteration_count}"
        
        # Form header
        st.markdown(f"""
        <div class="enhanced-input-section-header">
            <h4>✍️ {t('your_review')} (Attempt {iteration_count})</h4>
            <p>{t('write_comprehensive_review')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Review input
        student_review_input = st.text_area(
            t("enter_your_review"),
            value="", 
            height=350,
            key=text_area_key,
            placeholder=f"Example:\nLine 5: Missing semicolon\nLine 12: Null pointer risk...",
            label_visibility="collapsed"
        )
        
        
        submit_button = st.button(
                f"🚀 {t('submit_review_button')} (Attempt {iteration_count})", 
                type="primary", 
                use_container_width=True,
                key=submit_button_key
            )
        
        # Handle submission
        if submit_button:
            if not student_review_input or len(student_review_input.strip()) < 10:
                st.error("❌ Please provide a more detailed review")
                return False
            
            # FIXED: Simple processing with fixed workflow
            with st.spinner("🔄 Processing your review..."):
                user_id = st.session_state.auth.get("user_id")
                if user_id:
                    try:
                        _log_user_interaction_code_display(
                            user_id=user_id,
                            interaction_category="practice", 
                            interaction_type="submit_review",               
                            details={
                                "review_length": len(student_review_input),
                                "iteration": iteration_count,
                                "has_content": bool(student_review_input.strip())
                            }
                        )
                    except Exception as log_error:
                        logger.warning(f"Could not log interaction: {str(log_error)}")

                result = on_submit_callback(student_review_input.strip())
                
                if result:
                    st.success("✅ Review submitted successfully!")
                    time.sleep(0.5)
                    st.rerun()
                    return True
                else:
                    st.error("❌ Review processing failed")
                    return False
        
        return False

    def _safe_clear_processing_flag(self, processing_flag: str) -> None:
        """FIXED: Safely clear processing flag with error handling."""
        try:
            if processing_flag and processing_flag in st.session_state:
                del st.session_state[processing_flag]
        except Exception as e:
            logger.warning(f"Could not clear processing flag {processing_flag}: {str(e)}")

    def _process_review_submission(self, review_text: str, iteration_count: int, 
                                        on_submit_callback: Callable, success_flag: str,
                                        processing_flag: str) -> bool:
        """
        FIXED: Process review submission with comprehensive validation and error handling.
        """
        try:
            logger.debug(f"Processing review submission for iteration {iteration_count}")
            
            # FIXED: Comprehensive input validation
            if not isinstance(review_text, str):
                review_text = str(review_text) if review_text else ""
            
            if not review_text or not review_text.strip():
                st.error(f"❌ {t('please_enter_review')}")
                self._safe_clear_processing_flag(processing_flag)
                return False
            
            cleaned_review = review_text.strip()
            
            # FIXED: Enhanced validation
            if len(cleaned_review) < 20:
                st.warning(t("review_too_short_warning"))
                self._safe_clear_processing_flag(processing_flag)
                return False
            
            # Additional validation
            if len(cleaned_review.split()) < 5:
                st.warning("Please provide a more detailed review with at least 5 words.")
                self._safe_clear_processing_flag(processing_flag)
                return False
            
            # FIXED: Validate callback before calling
            if not callable(on_submit_callback):
                st.error("❌ Invalid submission handler. Please refresh the page.")
                self._safe_clear_processing_flag(processing_flag)
                return False
            
            # Show processing indicator
            with st.spinner(f"🔄 {t('processing_review')}..."):
                logger.debug(f"Calling submit callback with review: '{cleaned_review[:100]}...'")
                
                try:
                    logger.debug("Executing callback function...")
                    result = on_submit_callback(cleaned_review)
                    logger.debug(f"Callback returned: {result} (type: {type(result)})")
                    
                    # Clear processing flag
                    self._safe_clear_processing_flag(processing_flag)
                    
                    # FIXED: Enhanced success check with validation
                    if result is True or result is None:
                        # Set success flag
                        try:
                            st.session_state[success_flag] = True
                        except Exception as flag_error:
                            logger.warning(f"Could not set success flag: {str(flag_error)}")
                        
                        # Clear the draft
                        try:
                            draft_key = f"review_draft_iter_{iteration_count}"
                            if draft_key in st.session_state:
                                del st.session_state[draft_key]
                        except Exception as draft_error:
                            logger.warning(f"Could not clear draft: {str(draft_error)}")
                        
                        logger.debug(f"Review successfully submitted for iteration {iteration_count}")
                        
                        # FIXED: Safe rerun with error handling
                        try:
                            time.sleep(0.5)  # Small delay to ensure state persistence
                            st.rerun()
                        except Exception as rerun_error:
                            logger.error(f"Error during rerun: {str(rerun_error)}")
                            st.success("✅ Review submitted successfully! Please refresh if the page doesn't update.")
                        
                        return True
                    else:
                        logger.warning(f"Submit callback returned: {result} for iteration {iteration_count}")
                        st.error(f"❌ {t('error')} {t('processing_review')}. Callback returned: {result}")
                        return False
                        
                except Exception as callback_error:
                    self._safe_clear_processing_flag(processing_flag)
                    logger.error(f"Exception in submit callback: {str(callback_error)}", exc_info=True)
                    st.error(f"❌ {t('error')} {t('processing_review')}: {str(callback_error)}")
                    return False
                    
        except Exception as e:
            self._safe_clear_processing_flag(processing_flag)
            logger.error(f"Exception in review submission processing: {str(e)}", exc_info=True)
            st.error(f"❌ {t('error')} {t('processing_review')}: {str(e)}")
            return False

def render_review_tab(workflow, code_display_ui, auth_ui=None):
    """
    FIXED: Simplified review tab using fixed workflow.
    """
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <h2 style="color: #495057; margin-bottom: 0.5rem; font-size: 2rem; font-weight: 700;">
            📋 {t('review_java_code')}
        </h2>
        <p style="color: #6c757d; margin: 0; font-size: 1.1rem;">
            {t('carefully_examine_code')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Simple state check
    if not hasattr(st.session_state, 'workflow_state') or not st.session_state.workflow_state:
        st.info("📝 Please generate code first before reviewing.")
        return
        
    if not hasattr(st.session_state.workflow_state, 'code_snippet') or not st.session_state.workflow_state.code_snippet:
        st.info("⚙️ Please complete code generation before review.")
        return
    
    # Display code
    code_display_ui.render_code_display(st.session_state.workflow_state.code_snippet)
    
    # Handle review submission with fixed workflow
    _handle_review_submission_fixed(workflow, code_display_ui, auth_ui)

def _handle_review_submission_fixed(workflow, code_display_ui, auth_ui=None):
    """
    FIXED: Simplified review submission handling.
    """
    state = st.session_state.workflow_state
    current_iteration = getattr(state, 'current_iteration', 1)
    max_iterations = getattr(state, 'max_iterations', 3)
    review_sufficient = getattr(state, 'review_sufficient', False)
    
    if current_iteration <= max_iterations and not review_sufficient:
        # Get review data for display
        review_history = getattr(state, 'review_history', [])
        latest_review = review_history[-1] if review_history else None
        
        targeted_guidance = getattr(latest_review, "targeted_guidance", None) if latest_review else None
        review_analysis = getattr(latest_review, "analysis", None) if latest_review else None
        
        # Simple callback for fixed workflow
        def on_submit_fixed(review_text):
            updated_state = workflow.submit_review(state, review_text)
            if hasattr(updated_state, 'error') and updated_state.error:
                st.error(f"❌ {updated_state.error}")
                return False
            st.session_state.workflow_state = updated_state
            return True
        
        # Render review input
        code_display_ui.render_review_input(
            on_submit_callback=on_submit_fixed,
            iteration_count=current_iteration,
            max_iterations=max_iterations,
            targeted_guidance=targeted_guidance,
            review_analysis=review_analysis
        )
    else:
        # Show completion
        if review_sufficient:
            st.success("🎉 Excellent work! Review completed successfully.")
        else:
            st.info("⏰ Review session completed. Check the Feedback tab for results.")
 
def _process_student_review(workflow, student_review: str) -> bool:
    """
    FIXED: Simplified review processing using fixed workflow.
    """
    try:
        logger.debug("Processing review submission with fixed workflow")
        
        # Basic validation
        if not workflow:
            st.error("❌ No workflow available for review processing")
            return False
        
        if not hasattr(st.session_state, 'workflow_state') or not st.session_state.workflow_state:
            st.error("❌ No workflow state available. Please generate code first.")
            return False
        
        # CRITICAL: Use the fixed workflow that won't regenerate code
        logger.debug("Calling fixed workflow.submit_review (NO CODE REGENERATION)")
        state = st.session_state.workflow_state
        current_iteration = getattr(state, 'current_iteration', 1)
        max_iterations = getattr(state, 'max_iterations', 3)
        user_id = st.session_state.auth.get("user_id") if hasattr(st.session_state, 'auth') else None
        if user_id:
            try:
                # FIXED: Safe review analysis
                review_analysis = {
                    "review_length": len(student_review),
                    "word_count": len(student_review.split()),
                    "line_count": len(student_review.split('\n')),
                    "has_line_references": bool(re.search(r'line\s*\d+', student_review.lower())),
                    "iteration": current_iteration,
                    "max_iterations": max_iterations
                }
                
                _log_user_interaction_code_display(
                    user_id=user_id,
                    interaction_category="practice",
                    interaction_type="review_analysis_start",                   
                    details={
                        "analysis_step": "processing",
                        "review_iteration": current_iteration,
                        **review_analysis
                    }
                )
            except Exception as log_error:
                logger.warning(f"Could not log review start: {str(log_error)}")

        updated_state = workflow.submit_review(st.session_state.workflow_state, student_review)
        
        # Simple error check
        if hasattr(updated_state, 'error') and updated_state.error:
            logger.error(f"Workflow returned error: {updated_state.error}")
            st.error(f"❌ {updated_state.error}")
            return False
        
        # Update session state
        st.session_state.workflow_state = updated_state
        
        if user_id:
            try:
                _log_user_interaction_code_display(
                    user_id=user_id,
                    interaction_category="practice",
                    interaction_type="review_analysis_complete",                    
                    details={
                        "analysis_step": "completed"
                    }
                )
            except Exception as log_error:
                        logger.warning(f"Could not log completion: {str(log_error)}")
        
        logger.debug("Review processing completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in review processing: {str(e)}", exc_info=True)
        st.error(f"❌ Review processing failed: {str(e)}")
        return False


