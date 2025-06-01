"""
Enhanced Code Display UI component for Java Peer Review Training System.

This module provides professional code display components with enhanced formatting,
syntax highlighting, and interactive features.
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
    """
    
    def __init__(self):
        """Initialize the CodeDisplayUI component."""
        pass
    
    def _get_unique_key(self, base_key: str) -> str:
        """Generate a unique key for Streamlit elements to avoid conflicts."""
        if 'code_display_counter' not in st.session_state:
            st.session_state.code_display_counter = 0
        
        st.session_state.code_display_counter += 1
        return f"{base_key}_{st.session_state.code_display_counter}"
    
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
        <div style="
            text-align: center; 
            padding: 3rem 2rem; 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            border: 2px dashed #dee2e6;
            margin: 2rem 0;
        ">
            <div style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.6;">⚙️</div>
            <h3 style="color: #6c757d; margin-bottom: 0.5rem;">{t('no_code_generated_yet')}</h3>
            <p style="color: #6c757d; margin: 0;">
                {t('generate_code_snippet_instruction')}
            </p>
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
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 12px 12px 0 0;
            margin-bottom: 0;
            border-bottom: 3px solid rgba(255,255,255,0.2);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <h3 style="margin: 0 0 0.5rem 0; font-size: 1.5rem; font-weight: 600;">
                        ☕ {t('java_code_review_challenge')}
                    </h3>
                    <p style="margin: 0; opacity: 0.9; font-size: 1rem;">
                        {t('review_code_below_instruction')}
                    </p>
                </div>
                <div style="display: flex; gap: 1rem; align-items: center;">
                    <div style="text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: bold;">{line_count}</div>
                        <div style="font-size: 0.8rem; opacity: 0.8;">{t('lines')}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: bold;">{char_count}</div>
                        <div style="font-size: 0.8rem; opacity: 0.8;">{t('characters')}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_code_container(self, code: str, lines: List[str], known_problems: List[str] = None):
        """Render the main code container with enhanced styling."""
        
        # Add custom CSS for code styling
        st.markdown("""
        <style>
        .code-container {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 0 0 12px 12px;
            margin-top: 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .code-header {
            background: #ffffff;
            border-bottom: 1px solid #e9ecef;
            padding: 0.5rem 1rem;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.8rem;
            color: #6c757d;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .stCode {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
            font-size: 14px !important;
            line-height: 1.5 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Main code container with header
        st.markdown("""
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
    
    def _calculate_basic_complexity(self, code: str) -> int:
        """Calculate a basic complexity score for the code."""
        complexity = 0
        lines = code.split('\n')
        
        for line in lines:
            line = line.strip()
            # Count control structures
            if re.search(r'\b(if|for|while|switch|try)\b', line):
                complexity += 1
            # Count nested structures (rough estimate)
            if line.startswith('    ') and re.search(r'\b(if|for|while)\b', line):
                complexity += 1
        
        return complexity
    
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
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #ffffff 0%, #f8fafe 100%);
            border-radius: 12px;
            padding: 0;
            margin: 2rem 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            border: 1px solid #e1e8f0;
        ">
        """, unsafe_allow_html=True)
        
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
        header_html = f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px 12px 0 0;
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                height: 4px;
                width: {progress_percentage}%;
                background: rgba(255, 255, 255, 0.3);
                transition: width 0.5s ease;
            "></div>
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <h3 style="margin: 0 0 0.5rem 0; font-size: 1.8rem; font-weight: 700;">
                        📝 {t("submit_review")}
                    </h3>
                    <p style="margin: 0; opacity: 0.9; font-size: 1.1rem;">
                        {t('provide_detailed_review')}
                    </p>
                </div>
                <div style="text-align: center;">
                    <div style="
                        background: rgba(255, 255, 255, 0.2);
                        border-radius: 50%;
                        width: 80px;
                        height: 80px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        backdrop-filter: blur(10px);
                    ">
                        <div style="font-size: 1.5rem; font-weight: bold;">{iteration_count}</div>
                        <div style="font-size: 0.8rem; opacity: 0.8;">{t('of')} {max_iterations}</div>
                    </div>
                </div>
            </div>
        </div>
        """
        
        st.markdown(header_html, unsafe_allow_html=True)
    
    def _render_enhanced_guidance_section(self, targeted_guidance: str, review_analysis: Dict[str, Any], student_review: str, iteration_count: int) -> None:
        """Render enhanced guidance and history section."""
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if targeted_guidance and iteration_count > 1:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #e7f3ff 0%, #f1f8ff 100%);
                    border-left: 4px solid #0066cc;
                    border-radius: 8px;
                    padding: 1.5rem;
                    margin: 1.5rem;
                ">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">🎯</span>
                        <h4 style="margin: 0; color: #0066cc; font-weight: 600;">
                            {t("review_guidance")}
                        </h4>
                    </div>
                    <div style="color: #495057; line-height: 1.6;">
                        {targeted_guidance}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if review_analysis:
                    identified_count = review_analysis.get(t("identified_count"), 0)
                    total_problems = review_analysis.get(t("total_problems"), 0)
                    percentage = review_analysis.get(t("identified_percentage"), 0)
                    
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #fff3cd 0%, #fef8e1 100%);
                        border-left: 4px solid #ffc107;
                        border-radius: 8px;
                        padding: 1.5rem;
                        margin: 1.5rem;
                    ">
                        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                            <span style="font-size: 1.5rem; margin-right: 0.5rem;">📊</span>
                            <h4 style="margin: 0; color: #856404; font-weight: 600;">
                                {t("previous_results")}
                            </h4>
                        </div>
                        <div style="color: #856404;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span>{t("issues_found")}:</span>
                                <strong>{identified_count} / {total_problems}</strong>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span>{t("accuracy")}:</span>
                                <strong>{percentage:.1f}%</strong>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col2:
            if student_review and iteration_count > 1:
                st.markdown(f"""
                <div style="margin: 1.5rem;">
                    <h4 style="
                        color: #495057; 
                        margin-bottom: 1rem;
                        display: flex;
                        align-items: center;
                    ">
                        <span style="margin-right: 0.5rem;">📝</span>
                        {t("previous_review")}
                    </h4>
                    <div style="
                        background: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 8px;
                        padding: 1rem;
                        max-height: 200px;
                        overflow-y: auto;
                        font-family: 'Monaco', 'Menlo', monospace;
                        font-size: 0.85rem;
                        line-height: 1.4;
                        color: #495057;
                    ">
                        {student_review.replace(chr(10), '<br>')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    def _render_enhanced_review_guidelines(self) -> None:
        """Render enhanced review guidelines with better presentation."""
        
        with st.expander(f"📋 {t('review_guidelines')}", expanded=False):
            st.markdown(f"""
            <div style="padding: 1rem 0;">
                <div style="
                    background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
                    border-radius: 8px;
                    padding: 1.5rem;
                    margin-bottom: 2rem;
                ">
                    <h4 style="margin: 0 0 1rem 0; color: #2e7d32;">
                        ✨ {t('how_to_write')}
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
                        <div>
                            <strong style="color: #2e7d32;">🎯 {t('be_specific')}</strong>
                            <p style="margin: 0.5rem 0 0 0; color: #4a5568; font-size: 0.9rem;">
                                Point out exact lines and explain the issue clearly
                            </p>
                        </div>
                        <div>
                            <strong style="color: #2e7d32;">🔍 {t('be_comprehensive')}</strong>
                            <p style="margin: 0.5rem 0 0 0; color: #4a5568; font-size: 0.9rem;">
                                Check all aspects: syntax, logic, style, security
                            </p>
                        </div>
                        <div>
                            <strong style="color: #2e7d32;">💡 {t('be_constructive')}</strong>
                            <p style="margin: 0.5rem 0 0 0; color: #4a5568; font-size: 0.9rem;">
                                Suggest improvements and explain why
                            </p>
                        </div>
                    </div>
                </div>
                
                <div style="margin-bottom: 2rem;">
                    <h4 style="color: #495057; margin-bottom: 1rem;">🔍 {t('check_for')}</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                        <div style="background: #f8f9fa; padding: 1rem; border-radius: 6px; border-left: 3px solid #0066cc;">
                            <strong>🔤 Syntax & Compilation</strong>
                            <ul style="margin: 0.5rem 0 0 0; padding-left: 1rem; color: #6c757d; font-size: 0.9rem;">
                                <li>Missing semicolons</li>
                                <li>Bracket mismatches</li>
                                <li>Type errors</li>
                            </ul>
                        </div>
                        <div style="background: #f8f9fa; padding: 1rem; border-radius: 6px; border-left: 3px solid #dc3545;">
                            <strong>🐛 Logic & Bugs</strong>
                            <ul style="margin: 0.5rem 0 0 0; padding-left: 1rem; color: #6c757d; font-size: 0.9rem;">
                                <li>Array bounds</li>
                                <li>Null pointers</li>
                                <li>Loop conditions</li>
                            </ul>
                        </div>
                        <div style="background: #f8f9fa; padding: 1rem; border-radius: 6px; border-left: 3px solid #28a745;">
                            <strong>⭐ Code Quality</strong>
                            <ul style="margin: 0.5rem 0 0 0; padding-left: 1rem; color: #6c757d; font-size: 0.9rem;">
                                <li>Naming conventions</li>
                                <li>Code formatting</li>
                                <li>Documentation</li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div style="
                    background: #e7f3ff;
                    border: 1px solid #b3d9ff;
                    border-radius: 8px;
                    padding: 1.5rem;
                ">
                    <h4 style="margin: 0 0 1rem 0; color: #0066cc;">📝 {t('format_your_review')}</h4>
                    <pre style="
                        background: white;
                        border: 1px solid #d1ecf1;
                        border-radius: 4px;
                        padding: 1rem;
                        margin: 0;
                        color: #495057;
                        font-size: 0.85rem;
                        overflow-x: auto;
                    ">{t('review_format_example')}</pre>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_enhanced_review_form(self, iteration_count: int, on_submit_callback: Callable) -> bool:
        """Render enhanced review form with better UX."""
        st.markdown('<div style="padding: 2rem;">', unsafe_allow_html=True)
        
        # Enhanced form header
        st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <h4 style="
                color: #495057;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
            ">
                <span style="margin-right: 0.5rem;">✍️</span>
                {t('your_review')}
            </h4>
            <p style="color: #6c757d; margin: 0; font-size: 0.9rem;">
                {t('write_comprehensive_review')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create unique key for text area
        text_area_key = self._get_unique_key(f"student_review_input_{iteration_count}")
        
        # Get initial value
        initial_value = ""
        if iteration_count > 1 and text_area_key in st.session_state:
            initial_value = st.session_state[text_area_key]
        
        # Enhanced review input with better styling
        student_review_input = st.text_area(
            t("enter_review"),
            value=initial_value, 
            height=350,
            key=text_area_key,
            placeholder=t("review_placeholder"),
            label_visibility="collapsed",
            help=t("review_help_text")
        )
        
        # Enhanced buttons with better layout
        st.markdown('<div style="margin-top: 1.5rem;">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([6, 2, 2])
        
        with col1:
            submit_text = t("submit_review_button") if iteration_count == 1 else f"{t('submit_review_button')} ({t('attempt')} {iteration_count})"
            submit_button = st.button(
                f"🚀 {submit_text}", 
                type="primary", 
                use_container_width=True,
                help=t("submit_review_help"),
                key=self._get_unique_key(f"submit_review_{iteration_count}")
            )
        with col2:
            clear_button = st.button(
                f"🗑️ {t('clear')}", 
                use_container_width=True,
                help=t("clear_review_help"),
                key=self._get_unique_key(f"clear_review_{iteration_count}")
            )
        with col3:
            char_count = len(student_review_input)
            st.metric(t("characters"), char_count, help=t("character_count_help"))
        
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        # Handle buttons
        if clear_button:
            st.session_state[text_area_key] = ""
            st.rerun()
        
        if submit_button:
            if not student_review_input.strip():
                st.error(f"❌ {t('please_enter_review')}")
                return False
            elif len(student_review_input.strip()) < 20:
                st.warning(t("review_too_short_warning"))
                return False
            elif on_submit_callback:
                with st.spinner(f"🔄 {t('processing_review')}..."):
                    on_submit_callback(student_review_input)
                    if f"submitted_review_{iteration_count}" not in st.session_state:
                        st.session_state[f"submitted_review_{iteration_count}"] = student_review_input
                return True
        
        return False


def render_review_tab(workflow, code_display_ui, auth_ui=None):
    """
    Render the review tab UI with enhanced styling and better user experience.
    Now accepts auth_ui parameter for immediate stats updates.
    
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
        st.markdown("""
        <div style="
            text-align: center; 
            padding: 3rem; 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            border: 2px dashed #dee2e6;
            margin: 2rem 0;
        ">
            <div style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.6;">⚙️</div>
            <h3 style="color: #6c757d; margin-bottom: 1rem;">{t('no_code_available')}</h3>
            <p style="color: #6c757d; margin-bottom: 1.5rem;">
                {t('generate_code_snippet_first')}
            </p>
            <div style="
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: 25px;
                font-weight: 600;
            ">
                👈 {t('go_to_generate_tab')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
        
    # Check code snippet
    if not hasattr(st.session_state.workflow_state, 'code_snippet') or not st.session_state.workflow_state.code_snippet:
        st.markdown("""
        <div style="
            text-align: center; 
            padding: 3rem; 
            background: linear-gradient(135deg, #fff3cd 0%, #fef8e1 100%);
            border-radius: 12px;
            border: 2px solid #ffc107;
            margin: 2rem 0;
        ">
            <div style="font-size: 4rem; margin-bottom: 1rem;">⚠️</div>
            <h3 style="color: #856404; margin-bottom: 1rem;">{t('code_generation_incomplete')}</h3>
            <p style="color: #856404; margin: 0;">
                {t('complete_code_generation_before_review')}
            </p>
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
    """Handle the review submission logic with enhanced UX and immediate stats update."""
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
            logger.debug(f"Submitting review (iteration {current_iteration})")
            _process_student_review(workflow, review_text)
        
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
            <div style="
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                border: 2px solid #28a745;
                border-radius: 12px;
                padding: 2rem;
                text-align: center;
                margin: 2rem 0;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🎉</div>
                <h3 style="color: #155724; margin-bottom: 1rem; font-weight: 700;">
                    {t('excellent_work')}
                </h3>
                <p style="color: #155724; margin: 0; font-size: 1.1rem;">
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
            <div style="
                background: linear-gradient(135deg, #fff3cd 0%, #fef8e1 100%);
                border: 2px solid #ffc107;
                border-radius: 12px;
                padding: 2rem;
                text-align: center;
                margin: 2rem 0;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⏰</div>
                <h3 style="color: #856404; margin-bottom: 1rem; font-weight: 700;">
                    {t('review_session_complete')}
                </h3>
                <p style="color: #856404; margin: 0; font-size: 1.1rem;">
                    {t('completed_review_attempts', max_iterations=max_iterations)}
                    <br>
                    {t('check_feedback_tab_results')}
                </p>
            </div>
            """, unsafe_allow_html=True)


def _process_student_review(workflow, student_review: str) -> bool:
    """Process a student review using the compiled LangGraph workflow with enhanced feedback."""
    with st.status(t("processing_review"), expanded=True) as status:
        try:
            # Validate workflow state
            if not hasattr(st.session_state, 'workflow_state'):
                status.update(label=f"❌ {t('error')}: {t('workflow_not_initialized')}", state="error")
                st.session_state.error = t("please_generate_problem_first")
                return False
                
            state = st.session_state.workflow_state
            
            # Validate code snippet
            if not hasattr(state, "code_snippet") or state.code_snippet is None:
                status.update(label=f"❌ {t('error')}: {t('no_code_snippet_available')}", state="error")
                st.session_state.error = t("please_generate_problem_first")
                return False
            
            # Validate review content
            if not student_review.strip():
                status.update(label=f"❌ {t('error')}: {t('review_cannot_be_empty')}", state="error")
                st.session_state.error = t("please_enter_review")
                return False
            
            # Enhanced validation
            if len(student_review.strip()) < 10:
                status.update(label="❌ Error: Review too short", state="error")
                st.session_state.error = "Please provide a more detailed review (at least 10 characters)"
                return False
            
            # Validate review format
            evaluator = workflow.workflow_nodes.evaluator
            if evaluator:
                is_valid, reason = evaluator.validate_review_format(student_review)
                if not is_valid:
                    status.update(label=f"❌ {t('error')}: {reason}", state="error")
                    st.session_state.error = reason
                    return False
            
            # Update status with progress
            status.update(label="🔄 Analyzing your review...", state="running")
            
            # Submit review using the compiled workflow
            updated_state = workflow.submit_review(state, student_review)
            
            # Check for errors
            if updated_state.error:
                status.update(label=f"❌ {t('error')}: {updated_state.error}", state="error")
                st.session_state.error = updated_state.error
                return False
            
            # Update session state
            st.session_state.workflow_state = updated_state
            
            # Enhanced completion message
            status.update(label="✅ Analysis complete! Review processed successfully.", state="complete")
            
            # Add brief delay for user feedback
            time.sleep(1)
            st.rerun()
            
            return True
            
        except Exception as e:
            error_msg = f"❌ {t('error')} {t('processing_student_review')}: {str(e)}"
            logger.error(error_msg)
            status.update(label=error_msg, state="error")
            st.session_state.error = error_msg
            return False