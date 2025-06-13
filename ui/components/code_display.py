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
        self._render_review_form(iteration_count, on_submit_callback)
        
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
    
    def _render_review_form(self, iteration_count: int, on_submit_callback: Callable) -> bool:
        """
        FIXED: Enhanced review form with comprehensive variable validation.
        """
        # FIXED: Validate callback first
        if not callable(on_submit_callback):
            st.error("❌ Invalid submission handler. Please refresh the page.")
            return False
        
        # FIXED: Safe user ID extraction with validation
        user_id = None
        try:
            if hasattr(st.session_state, 'auth') and isinstance(st.session_state.auth, dict):
                user_id = st.session_state.auth.get("user_id")
                if not user_id or not isinstance(user_id, str):
                    user_id = None
        except Exception as e:
            logger.warning(f"Could not extract user_id: {str(e)}")
            user_id = None
        
        # FIXED: Validate iteration count
        try:
            iteration_count = max(1, int(iteration_count))
        except (ValueError, TypeError):
            iteration_count = 1
            logger.warning("Invalid iteration_count, defaulting to 1")
        
        # FIXED: Safe workflow step extraction
        workflow_step = "unknown"
        try:
            if hasattr(st.session_state, 'workflow_state') and st.session_state.workflow_state:
                workflow_step = getattr(st.session_state.workflow_state, 'current_step', 'unknown')
                if not isinstance(workflow_step, str):
                    workflow_step = str(workflow_step) if workflow_step else "unknown"
        except Exception as e:
            logger.warning(f"Could not extract workflow_step: {str(e)}")
        
        # FIXED: Unique keys with validation
        try:
            iteration_key = f"iter_{iteration_count}"
            text_area_key = f"review_input_{iteration_key}"
            submit_button_key = f"submit_review_{iteration_key}"
            clear_button_key = f"clear_review_{iteration_key}"
            review_processing_key = f"review_processing_{iteration_key}"
        except Exception as e:
            logger.error(f"Error creating form keys: {str(e)}")
            st.error("❌ Form initialization error. Please refresh the page.")
            return False
        
        # FIXED: Safe processing flag check
        is_processing = False
        try:
            is_processing = bool(st.session_state.get(review_processing_key, False))
        except Exception as e:
            logger.warning(f"Could not check processing flag: {str(e)}")
        
        if is_processing:
            st.info("⏳ Processing your review... Please wait.")
            return False
        
        # FIXED: Safe success flag management
        success_flag = f"review_submitted_{iteration_key}"
        initial_value = ""
        
        try:
            if st.session_state.get(success_flag, False):
                # Clear success flag and draft
                if success_flag in st.session_state:
                    del st.session_state[success_flag]
                draft_key = f"review_draft_{iteration_key}"
                if draft_key in st.session_state:
                    del st.session_state[draft_key]
                st.success("✅ Review submitted successfully!")
            else:
                # Preserve draft content with iteration-specific key
                draft_key = f"review_draft_{iteration_key}"
                initial_value = str(st.session_state.get(draft_key, ""))
        except Exception as e:
            logger.warning(f"Error managing success flag: {str(e)}")
        
        # Enhanced form header
        st.markdown(f"""
        <div class="enhanced-input-section-header">
            <h4>
                <span class="input-icon">✍️</span>
                {t('your_review')} (Attempt {iteration_count})
            </h4>
            <p>{t('write_comprehensive_review')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced review input with workflow-aware placeholder
        placeholder_text = t("review_placeholder")
        if workflow_step == "review":
            placeholder_text += f"\n\n💡 This is attempt {iteration_count}. Be specific about line numbers and error types."
        
        # FIXED: Safe text area rendering
        try:
            student_review_input = st.text_area(
                t("enter_your_review"),
                value=initial_value, 
                height=350,
                key=text_area_key,
                placeholder=placeholder_text,
                label_visibility="collapsed",
                help=t("review_help_text")
            )
            
            # Ensure we got a string
            if not isinstance(student_review_input, str):
                student_review_input = str(student_review_input) if student_review_input else ""
                
        except Exception as e:
            logger.error(f"Error rendering text area: {str(e)}")
            st.error("❌ Form rendering error. Please refresh the page.")
            return False
        
        # FIXED: Safe draft saving
        try:
            if student_review_input:
                draft_key = f"review_draft_{iteration_key}"
                st.session_state[draft_key] = student_review_input
        except Exception as e:
            logger.warning(f"Could not save draft: {str(e)}")
        
        # Enhanced buttons with better layout
        st.markdown('<div class="enhanced-button-container">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([8, 2])
        
        # FIXED: Safe button rendering
        submit_button = False
        clear_button = False
        
        try:
            with col1:
                submit_text = f"{t('submit_review_button')} (Attempt {iteration_count})"
                submit_button = st.button(
                    f"🚀 {submit_text}", 
                    type="primary", 
                    use_container_width=True,
                    help=t("submit_review_help"),
                    key=submit_button_key,
                    disabled=is_processing
                )
                
            with col2:
                clear_button = st.button(
                    f"🗑️ {t('clear')}", 
                    use_container_width=True,
                    help=t("clear_review_help"),
                    key=clear_button_key,
                    disabled=is_processing
                )
        except Exception as e:
            logger.error(f"Error rendering buttons: {str(e)}")
            st.error("❌ Button rendering error. Please refresh the page.")
            return False
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Handle clear button
        if clear_button:
            try:
                draft_key = f"review_draft_{iteration_key}"
                if draft_key in st.session_state:
                    del st.session_state[draft_key]
                st.info("✅ Review cleared.")
                st.rerun()
                return False
            except Exception as e:
                logger.error(f"Error clearing review: {str(e)}")
                st.error("❌ Could not clear review. Please refresh the page.")
        
        # Handle submit button
        if submit_button:
            # FIXED: Comprehensive validation before processing
            try:
                # Set processing flag to prevent multiple submissions
                st.session_state[review_processing_key] = True
                
                # Log interaction with safe user_id
                if user_id:
                    try:
                        _log_user_interaction_code_display(
                            user_id=user_id,
                            interaction_category="practice", 
                            interaction_type="submit_review",               
                            details={
                                "review_length": len(student_review_input),
                                "iteration": iteration_count,
                                "workflow_step": workflow_step,
                                "has_content": bool(student_review_input.strip())
                            }
                        )
                    except Exception as log_error:
                        logger.warning(f"Could not log interaction: {str(log_error)}")
                
                # Process the submission
                return self._process_review_submission(
                    student_review_input, 
                    iteration_count, 
                    on_submit_callback,
                    success_flag,
                    review_processing_key
                )
                
            except Exception as e:
                # Ensure processing flag is cleared on error
                try:
                    if review_processing_key in st.session_state:
                        del st.session_state[review_processing_key]
                except:
                    pass
                logger.error(f"Error handling submit button: {str(e)}")
                st.error(f"❌ Submit error: {str(e)}")
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
    # Get current review state
    state = st.session_state.workflow_state
    current_iteration = getattr(state, 'current_iteration', 1)
    max_iterations = getattr(state, 'max_iterations', 3)
    
    logger.debug(f"Handling review submission - iteration {current_iteration}/{max_iterations}")
    
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
                logger.debug(f"Submit callback triggered for iteration {current_iteration}")
                logger.debug(f"Review text: '{review_text[:100]}...' (length: {len(review_text)})")
                
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
                logger.debug("Calling _process_student_review...")
                result = _process_student_review_with_comprehensive_tracking(workflow, review_text)
                logger.debug(f"_process_student_review returned: {result}")
                
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
        logger.debug("Rendering review input with callback")
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
                    stats_key = f"review_tab_stats_updated"
                    
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
    """
    FIXED: Enhanced review processing with comprehensive variable validation.
    """
    try:
        # FIXED: Safe user ID extraction
        user_id = None
        try:
            if hasattr(st.session_state, 'auth') and isinstance(st.session_state.auth, dict):
                user_id = st.session_state.auth.get("user_id")
                if not isinstance(user_id, str) or not user_id.strip():
                    user_id = None
        except Exception as e:
            logger.warning(f"Could not extract user_id: {str(e)}")
        
        review_start_time = time.time()
        
        logger.debug("Starting student review processing")
        logger.debug(f"Processing review: '{student_review[:100]}...' (length: {len(student_review)})")
        
        # FIXED: Safe workflow state validation
        if not hasattr(st.session_state, 'workflow_state') or not st.session_state.workflow_state:
            logger.error("No workflow state available")
            st.error("❌ No workflow state available. Please generate code first.")
            return False
        
        state = st.session_state.workflow_state
        
        # FIXED: Safe attribute extraction with validation
        try:
            current_iteration = getattr(state, 'current_iteration', 1)
            if not isinstance(current_iteration, int) or current_iteration <= 0:
                current_iteration = 1
                
            max_iterations = getattr(state, 'max_iterations', 3)
            if not isinstance(max_iterations, int) or max_iterations <= 0:
                max_iterations = 3
        except Exception as e:
            logger.warning(f"Error extracting iteration info: {str(e)}")
            current_iteration = 1
            max_iterations = 3
        
        # Track review submission with safe user_id
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
        
        # Enhanced status tracking with detailed steps
        with st.status(t("processing_review"), expanded=True) as status:
            
            # Step 1: Validate workflow
            status.update(label="🔍 Validating workflow...", state="running")
            
            # FIXED: Comprehensive workflow validation
            if not workflow:
                error_msg = "No workflow provided"
                logger.error(error_msg)                
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {error_msg}")
                return False
            
            # FIXED: Validate workflow has required methods
            if not hasattr(workflow, 'submit_review') or not callable(workflow.submit_review):
                error_msg = "Workflow missing submit_review method"
                logger.error(error_msg)
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {error_msg}")
                return False
            
            # Step 2: Validate code snippet
            status.update(label="🔍 Validating code snippet...", state="running")
            
            if not hasattr(state, "code_snippet") or state.code_snippet is None:
                error_msg = "No code snippet available"
                logger.error(error_msg)
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {error_msg}. {t('please_generate_problem_first')}")
                return False
            
            # FIXED: Validate code snippet has required content
            try:
                code_content = getattr(state.code_snippet, 'code', None)
                if not code_content or not isinstance(code_content, str) or not code_content.strip():
                    error_msg = "Code snippet has no valid content"
                    logger.error(error_msg)
                    status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                    st.error(f"❌ {error_msg}")
                    return False
            except Exception as code_error:
                error_msg = f"Error accessing code content: {str(code_error)}"
                logger.error(error_msg)
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {error_msg}")
                return False
            
            # Step 3: Submit to workflow
            status.update(label="🚀 Analyzing review with AI...", state="running")
            
            try:
                analysis_start_time = time.time()
                
                # FIXED: Safe workflow submission with validation
                raw_updated_state = workflow.submit_review(state, student_review)
                
                analysis_duration = time.time() - analysis_start_time
                
                # FIXED: Validate workflow response
                if not raw_updated_state:
                    error_msg = "Workflow returned empty state"
                    status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                    st.error(f"❌ {error_msg}")
                    return False
                
                # FIXED: Check for workflow errors
                try:
                    error = getattr(raw_updated_state, 'error', None)
                    if error and isinstance(error, str) and error.strip():
                        logger.error(f"Workflow returned error: {error}")
                        status.update(label=f"❌ {t('error')}: {error}", state="error")
                        st.error(f"❌ {error}")
                        return False
                except Exception as error_check:
                    logger.warning(f"Could not check workflow error: {str(error_check)}")
                
                # Log completion if user_id available
                if user_id:
                    try:
                        _log_user_interaction_code_display(
                            user_id=user_id,
                            interaction_category="practice",
                            interaction_type="review_analysis_complete",                    
                            details={
                                "analysis_step": "completed",
                                "analysis_duration": analysis_duration
                            }
                        )
                    except Exception as log_error:
                        logger.warning(f"Could not log completion: {str(log_error)}")
                
                logger.debug(f"Workflow analysis completed in {analysis_duration:.2f}s")
                
            except Exception as workflow_error:
                error_msg = f"Workflow execution failed: {str(workflow_error)}"
                logger.error(error_msg, exc_info=True)
                status.update(label=f"❌ {t('error')}: {error_msg}", state="error")
                st.error(f"❌ {error_msg}")
                return False
            
            # Step 4: Update session state
            status.update(label="💾 Updating session state...", state="running")
            
            try:
                st.session_state.workflow_state = raw_updated_state
                st.session_state.review_processing_success = True
                st.session_state.last_review_timestamp = time.time()
            except Exception as state_error:
                logger.error(f"Error updating session state: {str(state_error)}")
                # Continue - this is not a fatal error
            
            # Step 5: Validate results
            try:
                review_history = getattr(raw_updated_state, 'review_history', None)
                if review_history and len(review_history) > 0:
                    logger.debug(f"Review processing completed successfully. History length: {len(review_history)}")
                    
                    # FIXED: Safe tracking of processing completion
                    if user_id:
                        try:
                            latest_review = review_history[-1]
                            analysis_results = getattr(latest_review, 'analysis', {}) if hasattr(latest_review, 'analysis') else {}
                            
                            total_processing_time = time.time() - review_start_time
                            
                            processing_details = {
                                "processing_duration": total_processing_time,
                                "analysis_duration": analysis_duration,
                                "review_iteration": current_iteration,
                                "review_sufficient": getattr(raw_updated_state, 'review_sufficient', False),
                                "analysis_results": {
                                    "identified_count": analysis_results.get(t('identified_count'), 0),
                                    "total_problems": analysis_results.get(t('total_problems'), 0),
                                    "accuracy_percentage": analysis_results.get(t('identified_percentage'), 0)
                                }
                            }
                            
                            _log_user_interaction_code_display(
                                user_id=user_id,
                                interaction_category="practice",
                                interaction_type="review_processing_complete",
                                details=processing_details
                            )
                        except Exception as final_log_error:
                            logger.warning(f"Could not log final completion: {str(final_log_error)}")
                    
                    status.update(label=f"✅ {t('analysis_complete_processed')}", state="complete")
                    return True
                else:
                    logger.warning("Review processing may not have completed properly - no review history found")
                    status.update(label="⚠️ Processing completed with warnings", state="complete")
                    return True
                    
            except Exception as validation_error:
                logger.warning(f"Error validating results: {str(validation_error)}")
                # Still return True as processing likely succeeded
                status.update(label="✅ Processing completed", state="complete")
                return True
            
    except Exception as e:        
        error_msg = f"Exception in review processing: {str(e)}"
        logger.error(error_msg, exc_info=True)  
        st.error(f"❌ {error_msg}")
        return False



