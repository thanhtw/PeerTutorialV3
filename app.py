# app.py - Updated with comprehensive fixes for rerun issues

"""
Java Peer Code Review Training System - LangGraph Version

UPDATED: Enhanced with comprehensive fixes for rerun issues:
1. Fixed review form state management during reruns
2. Prevented unnecessary code regeneration on reruns  
3. Added robust session state management
4. Enhanced workflow conditions with safeguards
"""

import streamlit as st
import os
import logging
from state_schema import WorkflowState

# Import CSS utilities
from static.css_utils import load_css

# Import language utilities with i18n support
from utils.language_utils import init_language, render_language_selector, t

# ADDED: Import enhanced session state manager
from utils.session_state_manager import session_state_manager

# Configure logging
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import LLM Manager
from llm_manager import LLMManager

# Import LangGraph components
from langgraph_workflow import JavaCodeReviewGraph

# Import modularized UI functions
from ui.utils.main_ui import (
    init_session_state,    
    create_enhanced_tabs
)

# Import UI components
from ui.components.code_generator import CodeGeneratorUI
from ui.components.code_display import CodeDisplayUI, render_review_tab  
from ui.components.feedback_system import render_feedback_tab
from ui.components.auth_ui import AuthUI
from ui.components.tutorial import TutorialUI

from analytics.behavior_tracker import behavior_tracker
import atexit

# Set page config
st.set_page_config(
    page_title="Java Code Review Trainer",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

css_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "css")

try:
    load_css(css_directory=css_dir)    
except Exception as e:
    logger.warning(f"CSS loading failed: {str(e)}")

def main():
    """Enhanced main application function with comprehensive rerun fixes."""

    # ADDED: Clean up expired locks at start of each run
    session_state_manager.cleanup_expired_locks()

    # Initialize language selection and i18n system
    init_language()

    # Initialize the authentication UI
    auth_ui = AuthUI()
    
    # Check if the user is authenticated
    if not auth_ui.is_authenticated():
        render_language_selector()
        is_authenticated = auth_ui.render_auth_page()
        if not is_authenticated:
            return

    # Get user level and store in session state
    user_level = auth_ui.get_user_level()   
    st.session_state.user_level = user_level
    
    # ENHANCED: Handle full reset with better state management
    if st.session_state.get("full_reset", False):
        del st.session_state["full_reset"]
        preserved = {
            key: st.session_state.get(key) 
            for key in ["auth", "provider_selection", "user_level", "language", "session_id"]
            if key in st.session_state
        }        
        
        # Clear workflow-related state but preserve practice mode if active
        workflow_keys = [k for k in st.session_state.keys() 
                        if k not in preserved.keys() and not k.startswith("practice_")]
        for key in workflow_keys:
            del st.session_state[key]
        
        # Restore preserved values
        st.session_state.update(preserved)
        
        # Only reset workflow state if not in practice mode
        if not st.session_state.get("practice_mode_active", False):
            st.session_state.workflow_state = WorkflowState()
            st.session_state.active_tab = 0
        
        st.rerun()

    # Initialize session state with enhanced management
    init_session_state_enhanced()
    
    # Initialize LLM manager
    llm_manager = LLMManager()
    
    if "provider_selection" not in st.session_state:
        st.session_state.provider_selection = "groq"    
    
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        st.error("⚠️ No Groq API key found in environment variables. Please set GROQ_API_KEY in your .env file.")
        st.info("To get a Groq API key:")
        st.info("1. Visit https://console.groq.com/")
        st.info("2. Sign up and get your API key")
        st.info("3. Add GROQ_API_KEY=your_key_here to your .env file")
        st.stop()

    # Configure provider
    try:
        success = llm_manager.set_provider("groq", api_key)
        if not success:
            st.error("❌ Failed to configure Groq provider. Please check your configuration.")
            st.stop()
        else:
            logger.debug("✅ Groq provider configured successfully")
    except Exception as e:
        st.error(f"❌ Error configuring LLM provider: {str(e)}")
        st.stop()

    # Add language selector to sidebar
    render_language_selector()
    
    # Render user profile
    auth_ui.render_combined_profile_leaderboard()

    # Initialize workflow after provider is setup
    workflow = JavaCodeReviewGraph(llm_manager)

    # Initialize UI components with enhanced state management
    code_display_ui = CodeDisplayUI()
    code_generator_ui = CodeGeneratorUIEnhanced(workflow, code_display_ui)       
    error_explorer_ui = TutorialUI(workflow)
    
    # Check if we're in practice mode
    if st.session_state.get("practice_mode_active", False):
        render_practice_mode_interface(error_explorer_ui, workflow)
    else:
        render_normal_interface_enhanced(
            code_generator_ui, 
            workflow, 
            code_display_ui, 
            auth_ui,          
            error_explorer_ui,
            user_level
        )

def init_session_state_enhanced():
    """Enhanced session state initialization with conflict prevention."""
    
    # Use the session state manager for safe initialization
    if 'workflow_state' not in st.session_state:
        st.session_state.workflow_state = WorkflowState()
    
    # Initialize UI state with enhanced management
    ui_defaults = {
        'active_tab': 0,
        'error': None,
        'workflow_steps': [],
        'sidebar_tab': "Status",
        'user_level': None,
        # ADDED: State management flags
        'generation_in_progress': False,
        'review_submission_in_progress': False,
        'last_rerun_timestamp': 0
    }
    
    for key, default_value in ui_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Update last rerun timestamp
    import time
    st.session_state.last_rerun_timestamp = time.time()
    
    # Initialize LLM logger
    if 'llm_logger' not in st.session_state:
        from utils.llm_logger import LLMInteractionLogger
        st.session_state.llm_logger = LLMInteractionLogger()

class CodeGeneratorUIEnhanced:
    """Enhanced Code Generator UI with rerun protection."""
    
    def __init__(self, workflow, code_display_ui):
        from ui.components.code_generator import CodeGeneratorUI
        self.original_ui = CodeGeneratorUI(workflow, code_display_ui)
        self.workflow = workflow
        self.code_display_ui = code_display_ui
    
    def render(self, user_level: str = "medium"):
        """Enhanced render with rerun protection."""
        
        # ADDED: Check if code generation should be prevented
        if session_state_manager.prevent_code_regeneration_on_rerun():
            logger.debug("Code regeneration prevented due to recent activity")
            # Just show the existing code
            self._render_existing_code_safely()
            return
        
        # Check if generation is already in progress
        if session_state_manager.is_operation_in_progress("code_generation"):
            st.info("🔄 Code generation in progress... Please wait.")
            return
        
        # Delegate to original UI
        self.original_ui.render(user_level)
    
    def _render_existing_code_safely(self):
        """Safely render existing code without regeneration."""
        workflow_state = session_state_manager.get_workflow_state_safely()
        
        if hasattr(workflow_state, 'code_snippet') and workflow_state.code_snippet:
            st.info("✅ Code already generated. You can proceed to review it.")
            self.code_display_ui.render_code_display(workflow_state.code_snippet)
            
            # Show regenerate option if needed
            st.markdown("---")
            if st.button("🔄 Generate New Problem", key="safe_regenerate"):
                # Clear the prevention flag and allow regeneration
                if "last_code_generation" in st.session_state:
                    del st.session_state["last_code_generation"]
                st.rerun()
        else:
            st.info("No code generated yet. Please configure and generate code.")

def render_practice_mode_interface(error_explorer_ui, workflow):
    """Render the streamlined practice mode interface."""
    
    # Header with practice mode indicator
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px; background: linear-gradient(90deg, #4CAF50, #45a049); color: white; padding: 1rem; border-radius: 8px;">
        <h1 style="color: white; margin-bottom: 5px;">🎯 {t('practice_mode')} - {t('app_title')}</h1>
        <p style="font-size: 1.1rem; color: white; margin: 0;">Focused practice session with specific error types</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Render the error explorer in practice mode with workflow
    error_explorer_ui.render(workflow)

def render_normal_interface_enhanced(code_generator_ui, workflow, code_display_ui, auth_ui, 
                                   error_explorer_ui, user_level):
    """Enhanced normal interface with rerun protection."""
    
    # Header with improved styling
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: rgb(178 185 213); margin-bottom: 5px;">{t('app_title')}</h1>
        <p style="font-size: 1.1rem; color: #666;">{t('app_subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ADDED: Show debug info if requested
    if st.session_state.get("show_debug_info", False):
        with st.expander("🔧 Debug Information", expanded=False):
            debug_info = session_state_manager.debug_session_state()
            st.json(debug_info)
            
            if st.button("Hide Debug Info"):
                st.session_state.show_debug_info = False
                st.rerun()
    else:
        if st.button("🔧 Show Debug Info", help="Show session state debug information"):
            st.session_state.show_debug_info = True
            st.rerun()
    
    # Display error message if there's an error
    if st.session_state.error:
        st.error(f"Error: {st.session_state.error}")
        if st.button("Clear Error"):
            st.session_state.error = None
            st.rerun()
    
    # Create enhanced tabs for different steps of the workflow
    tab_labels = [
        t("tab_tutorial"),
        t("tab_generate"),
        t("tab_review"),
        t("tab_feedback")      
    ]
    
    # Use the enhanced tabs function
    tabs = create_enhanced_tabs(tab_labels)

    # Tab content with enhanced error handling
    with tabs[0]: # Tutorial Tab
        try:
            error_explorer_ui.render(workflow) 
        except Exception as e:
            logger.error(f"Error in tutorial tab: {str(e)}")
            st.error("Error loading tutorial. Please refresh the page.")

    with tabs[1]: # Generate Tab
        try:
            # Check for special practice session completion flow
            if st.session_state.get("practice_session_active", False):
                error_name = st.session_state.get("practice_error_name", "")
                st.info(f"🎯 **Practice Session Active** - Practicing with error: **{error_name}**")
                st.info("💡 A code snippet has been generated for this error. Go to the **Review** tab to start analyzing!")
            
            code_generator_ui.render(user_level)
        except Exception as e:
            logger.error(f"Error in generate tab: {str(e)}")
            st.error("Error in code generation. Please refresh the page.")
    
    with tabs[2]: # Review Tab
        try:
            render_enhanced_review_tab_protected(workflow, code_display_ui, auth_ui)
        except Exception as e:
            logger.error(f"Error in review tab: {str(e)}")
            st.error("Error in review section. Please refresh the page.")
    
    with tabs[3]: # Feedback Tab
        try:
            render_feedback_tab(workflow, auth_ui)
        except Exception as e:
            logger.error(f"Error in feedback tab: {str(e)}")
            st.error("Error loading feedback. Please refresh the page.")

def render_enhanced_review_tab_protected(workflow, code_display_ui, auth_ui=None):
    """
    Enhanced review tab with comprehensive rerun protection.
    """
    # Check if this is a practice session
    practice_session = st.session_state.get("practice_session_active", False)
    practice_error_name = st.session_state.get("practice_error_name", "")
    
    if practice_session:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #4CAF50, #45a049); color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <h3 style="margin: 0; color: white;">🎯 Practice Session: {practice_error_name}</h3>
            <p style="margin: 0.5rem 0 0 0; color: white;">Review the generated code below and identify the specific error you're practicing with.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add option to end practice session
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 End Practice Session", help="Return to normal workflow"):
                # Clear practice session flags
                practice_keys = [key for key in st.session_state.keys() if key.startswith("practice_")]
                for key in practice_keys:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Reset workflow state
                st.session_state.workflow_state = WorkflowState()
                st.session_state.active_tab = 0
                st.rerun()
    
    # ENHANCED: Use the enhanced review tab rendering
    render_review_tab_with_state_protection(workflow, code_display_ui, auth_ui)

def render_review_tab_with_state_protection(workflow, code_display_ui, auth_ui=None):
    """
    Render review tab with enhanced state protection.
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
    
    # Get workflow state safely
    workflow_state = session_state_manager.get_workflow_state_safely()
    
    # Validate workflow state
    if not workflow_state:
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
    if not hasattr(workflow_state, 'code_snippet') or not workflow_state.code_snippet:
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
    
    # Extract known problems for instructor view
    known_problems = []
    try:
        evaluation_result = getattr(workflow_state, 'evaluation_result', None)
        if evaluation_result and t('found_errors') in evaluation_result:
            known_problems = evaluation_result[t('found_errors')]
        
        # Fallback to selected errors
        if not known_problems:
            selected_specific_errors = getattr(workflow_state, 'selected_specific_errors', None)
            if selected_specific_errors:
                known_problems = [
                    f"{error.get(t('type'), '').upper()} - {error.get(t('name'), '')}" 
                    for error in selected_specific_errors
                ]
    except Exception as e:
        logger.error(f"Error extracting known problems: {str(e)}")
        known_problems = []
    
    # Display the code
    code_display_ui.render_code_display(
        getattr(workflow_state, 'code_snippet', None),
        known_problems=known_problems
    )
    
    # Handle review submission logic with protection
    handle_review_submission_protected(workflow, code_display_ui, auth_ui)

def handle_review_submission_protected(workflow, code_display_ui, auth_ui=None):
    """Handle review submission with comprehensive protection against reruns."""
    
    # Get current review state safely
    workflow_state = session_state_manager.get_workflow_state_safely()
    current_iteration = getattr(workflow_state, 'current_iteration', 1)
    max_iterations = getattr(workflow_state, 'max_iterations', 3)
    
    logger.debug(f"Handling review submission - iteration {current_iteration}/{max_iterations}")
    
    # Get review data
    review_history = getattr(workflow_state, 'review_history', None)
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
    review_sufficient = getattr(workflow_state, 'review_sufficient', False)
    
    if current_iteration <= max_iterations and not review_sufficient and not all_errors_found:
        def on_submit_review_protected(review_text):
            """ENHANCED: Protected submit callback with duplicate prevention."""
            
            # Use session state manager for safe submission
            success, result = session_state_manager.safe_review_submission(
                review_text, 
                current_iteration,
                lambda text: process_student_review_enhanced(workflow, text)
            )
            
            if success:
                logger.debug(f"Review processed successfully for iteration {current_iteration}")
                return result
            else:
                logger.warning(f"Review processing failed: {result}")
                st.error(f"❌ {result}")
                return False
        
        # Render the review input with the protected callback
        logger.debug("Rendering review input with protected callback")
        code_display_ui.render_review_input(
            student_review=student_review,
            on_submit_callback=on_submit_review_protected,
            iteration_count=current_iteration,
            max_iterations=max_iterations,
            targeted_guidance=targeted_guidance,
            review_analysis=review_analysis
        )
    else:
        # Show completion messages
        if review_sufficient or all_errors_found:
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
                    stats_key = f"review_tab_stats_updated_{current_iteration}"
                    
                    if stats_key not in st.session_state:
                        logger.debug(f"Updating stats: accuracy={accuracy:.1f}%, score={identified_count}")
                        result = auth_ui.update_review_stats(accuracy, identified_count)
                        
                        if result and result.get("success", False):
                            st.session_state[stats_key] = True
                            logger.debug("Stats updated successfully in review tab")
                            
                except Exception as e:
                    logger.error(f"Error updating stats in review tab: {str(e)}")
            
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
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("📊 View Results", key="go_to_results", type="primary", use_container_width=True):
                    st.session_state.active_tab = 3
                    st.rerun()

def process_student_review_enhanced(workflow, student_review: str) -> bool:
    """Enhanced review processing with comprehensive tracking and error handling."""
    try:
        # Use the existing processing function but with enhanced error handling
        from ui.components.code_display import _process_student_review_with_comprehensive_tracking
        return _process_student_review_with_comprehensive_tracking(workflow, student_review)
        
    except Exception as e:
        logger.error(f"Error in enhanced review processing: {str(e)}")
        return False

if __name__ == "__main__":
    main()