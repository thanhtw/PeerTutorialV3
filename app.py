"""
Java Peer Code Review Training System - LangGraph Version

This module provides a Streamlit web interface for the Java code review training system
using LangGraph for workflow management with a modular UI structure.
"""

import streamlit as st
import os
import logging
from state_schema import WorkflowState

# Import CSS utilities
from static.css_utils import load_css

# Import language utilities with i18n support
from utils.language_utils import init_language, render_language_selector, t

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
    render_llm_logs_tab,
    create_enhanced_tabs
)

# Import UI components
from ui.components.code_generator import CodeGeneratorUI
from ui.components.code_display import CodeDisplayUI, render_review_tab  
from ui.components.feedback_system import render_feedback_tab, render_enhanced_feedback_tab
from ui.components.auth_ui import AuthUI
from ui.components.enhanced_tutorial import EnhancedTutorialUI
from ui.components.learning_dashboard import LearningDashboardUI
from ui.components.error_explorer_ui import ErrorExplorerUI


# Set page config
st.set_page_config(
    page_title="Java Code Review Trainer",
    page_icon="☕",  # Java coffee cup icon
    layout="wide",
    initial_sidebar_state="expanded"
)

css_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "css")

try:
    load_css(css_directory=css_dir)
except Exception as e:
    logger.warning(f"CSS loading failed: {str(e)}")

def main():
    """Enhanced main application function with provider selection."""

    # Initialize language selection and i18n system
    init_language()

    try:
        from db.schema_update import update_database_schema
        update_database_schema()
    except Exception as e:
        logger.error(f"Database schema update failed: {str(e)}")

    # Initialize the authentication UI
    auth_ui = AuthUI()

    # Check if the user is authenticated
    if not auth_ui.is_authenticated():
        # Render the authentication page
        render_language_selector()
        is_authenticated = auth_ui.render_auth_page()
        if not is_authenticated:
            return

    # Get user level and store in session state
    user_level = auth_ui.get_user_level()   
    st.session_state.user_level = user_level
    
    if st.session_state.get("full_reset", False):
        del st.session_state["full_reset"]
        preserved = {
            key: st.session_state.get(key) 
            for key in ["auth", "provider_selection", "user_level", "language"]
            if key in st.session_state
        }        
        # Clear workflow-related state
        workflow_keys = [k for k in st.session_state.keys() 
                        if k not in preserved.keys()]
        for key in workflow_keys:
            del st.session_state[key]
        
        # Restore preserved values
        st.session_state.update(preserved)
        st.session_state.workflow_state = WorkflowState()
        st.session_state.active_tab = 0
        st.rerun()

    # Initialize session state
    init_session_state()
    
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

    # Configure provider without testing connection (will be tested on first use)
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

    # Initialize UI components
    code_display_ui = CodeDisplayUI()
    code_generator_ui = CodeGeneratorUI(workflow, code_display_ui)
    enhanced_tutorial_ui = EnhancedTutorialUI(llm_manager)
    learning_dashboard_ui = LearningDashboardUI()
    error_explorer_ui = ErrorExplorerUI()
    
    # Header with improved styling
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: rgb(178 185 213); margin-bottom: 5px;">{t('app_title')}</h1>
        <p style="font-size: 1.1rem; color: #666;">{t('app_subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display error message if there's an error
    if st.session_state.error:
        st.error(f"Error: {st.session_state.error}")
        if st.button("Clear Error"):
            st.session_state.error = None
            st.rerun()
    
    # Create enhanced tabs for different steps of the workflow
    tab_labels = [
        t("tab_generate"),
        t("tab_review"),
        t("tab_feedback"),
        t("tab_tutorial"),  # New
        t("tab_dashboard"), # New
        t("tab_error_explorer") # New
        #t("tab_logs")
    ]
    
    # Use the enhanced tabs function
    tabs = create_enhanced_tabs(tab_labels)
    
    # Get user level from auth_ui
    user_level = auth_ui.get_user_level()

    # Tab content
    with tabs[0]:
        if st.session_state.get("practice_session_active", False):
            error_name = st.session_state.get("practice_error_name", "")
            st.info(f"🎯 **Practice Session Active** - Practicing with error: **{error_name}**")
            st.info("💡 A code snippet has been generated for this error. Go to the **Review** tab to start analyzing!")
        
        code_generator_ui.render(user_level)
    
    with tabs[1]:
        render_enhanced_review_tab(workflow, code_display_ui, auth_ui)
    
    with tabs[2]:
        render_enhanced_feedback_tab(workflow, auth_ui)  # Use the enhanced v
        
    with tabs[3]: # Tutorial Tab
        user_id = st.session_state.auth.get("user_id")
        if user_id:
            enhanced_tutorial_ui.render(user_id=user_id, on_complete=lambda: st.session_state.update({"active_tab": 0}))
        else:
            st.info(t("tutorial_available_after_login"))

    with tabs[4]: # Dashboard Tab
        user_id = st.session_state.auth.get("user_id")
        if user_id:
            learning_dashboard_ui.render(user_id=user_id)
        else:
            st.warning(t("user_not_authenticated_dashboard")) # Message for user not found
        
    with tabs[5]: # Error Explorer Tab
        error_explorer_ui.render(workflow)
        
    # with tabs[3]:  # This should be tabs[6] if logs are re-enabled
    #     render_llm_logs_tab()

def render_enhanced_review_tab(workflow, code_display_ui, auth_ui=None):
    """
    Enhanced review tab that supports both regular and practice sessions.
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
                if "practice_session_active" in st.session_state:
                    del st.session_state["practice_session_active"]
                if "practice_error_name" in st.session_state:
                    del st.session_state["practice_error_name"]
                
                # Reset workflow state
                st.session_state.workflow_state = WorkflowState()
                st.session_state.active_tab = 0
                st.rerun()
    
    # Use the original render_review_tab function
    from ui.components.code_display import render_review_tab
    render_review_tab(workflow, code_display_ui, auth_ui)

if __name__ == "__main__":
    main()