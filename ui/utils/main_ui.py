"""
Main UI utilities for Java Peer Review Training System.

This module provides core UI utility functions for the Streamlit interface,
including session state management, tab rendering, and LLM logs.
"""

import streamlit as st
import os
import logging
import re
import json
import time
from typing import Dict, List, Any, Optional

from utils.llm_logger import LLMInteractionLogger
from state_schema import WorkflowState
from utils.language_utils import t, get_current_language

# Configure logging
logger = logging.getLogger(__name__)

def init_session_state():
    """Initialize session state with default values."""
    # Initialize workflow state
    if 'workflow_state' not in st.session_state:
        st.session_state.workflow_state = WorkflowState()
    
    # Initialize UI state
    ui_defaults = {
        'active_tab': 0,
        'error': None,
        'workflow_steps': [],
        'sidebar_tab': "Status",
        'user_level': None
    }
    
    for key, default_value in ui_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Initialize workflow state attributes
    _init_workflow_state_attributes()
    
    # Initialize LLM logger
    if 'llm_logger' not in st.session_state:
        st.session_state.llm_logger = LLMInteractionLogger()
    
    # Clean up legacy session state
    _cleanup_legacy_session_state()


def _init_workflow_state_attributes():
    """Initialize workflow state attributes if missing."""
    workflow_state = st.session_state.workflow_state
    
    attributes = {
        'current_step': 'generate',
        'evaluation_attempts': 0,
        'max_evaluation_attempts': 3
    }
    
    for attr, default_value in attributes.items():
        if not hasattr(workflow_state, attr):
            setattr(workflow_state, attr, default_value)


def _cleanup_legacy_session_state():
    """Remove legacy session state entries that are no longer used."""
    # Remove direct code_snippet references (should be in workflow_state)
    if 'code_snippet' in st.session_state:
        # Transfer to workflow_state if needed
        if hasattr(st.session_state.workflow_state, 'code_snippet') and not st.session_state.workflow_state.code_snippet:
            st.session_state.workflow_state.code_snippet = st.session_state.code_snippet
        del st.session_state.code_snippet


def create_enhanced_tabs(labels: List[str]):
    """
    Create enhanced UI tabs with proper state management.
    
    Args:
        labels: List of tab labels
        
    Returns:
        List of tab objects
    """
    # Create tabs
    tabs = st.tabs(labels)
    
    # Handle forced tab reset
    if st.session_state.get("force_tab_zero", False):
        st.session_state.active_tab = 0
        st.session_state["force_tab_zero"] = False
    
    # Get current active tab
    current_tab = st.session_state.active_tab
    
    # Check review completion for feedback tab access
    if current_tab == 2:  # Feedback tab
        if not _is_review_completed():
            st.warning(t("complete_review_first"))
            st.session_state.active_tab = 1
            current_tab = 1
    
    # Update active tab
    if current_tab != 0:
        st.session_state.active_tab = current_tab
    
    return tabs


def _is_review_completed() -> bool:
    """Check if review process is completed."""
    if not hasattr(st.session_state, 'workflow_state'):
        return False
    
    state = st.session_state.workflow_state
    
    # Check max iterations or sufficient review
    if hasattr(state, 'current_iteration') and hasattr(state, 'max_iterations'):
        if state.current_iteration > state.max_iterations:
            return True
        if hasattr(state, 'review_sufficient') and state.review_sufficient:
            return True
    
    # Check if all errors identified
    if hasattr(state, 'review_history') and state.review_history:
        latest_review = state.review_history[-1]
        if hasattr(latest_review, 'analysis'):
            analysis = latest_review.analysis
            identified = analysis.get(t('identified_count'), 0)
            total = analysis.get(t('total_problems'), 0)
            if identified == total and total > 0:
                return True
    
    return False


def render_sidebar(llm_manager):
    """
    Render the sidebar with application info and model status.
    
    Args:
        llm_manager: LLMManager instance
    """
    with st.sidebar:
        # LLM Provider info
        st.subheader(f"LLM {t('provider')}")
        
        provider = llm_manager.provider.capitalize()
        
        if provider == "Groq":
            connection_status, message = llm_manager.check_groq_connection()
            status_text = f"✅ Connected" if connection_status else "❌ Disconnected"
            
            st.markdown(f"**{t('provider')}:** {provider}")
            st.markdown(f"**Status:** {status_text}")
            
            if not connection_status:
                st.error(f"Error: {message}")


def render_llm_logs_tab():
    """
    Render the LLM interaction logs tab with enhanced functionality.
    """
    try:
        from utils.llm_logger import LLMInteractionLogger
        from utils.language_utils import t
        
        if 'llm_logger' not in st.session_state:
            st.warning(t("llm_logger_not_initialized"))
            return
        
        logger_instance = st.session_state.llm_logger
        
        st.subheader(t("llm_logs_title"))
        
        # Control panel
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            logs_to_show = st.selectbox(
                t("logs_to_display"),
                options=[10, 25, 50, 100],
                index=1,
                key="logs_display_count"
            )
        
        with col2:
            log_type_filter = st.selectbox(
                t("filter_by_type"),
                options=["all", "code_generation", "code_evaluation", "review_analysis"],
                index=0,
                key="log_type_filter"
            )
        
        with col3:
            if st.button(t("refresh_logs"), key="refresh_logs_btn"):
                st.rerun()
        
        # Get and display logs
        logs = logger_instance.get_recent_logs(limit=logs_to_show, log_type=log_type_filter if log_type_filter != "all" else None)
        
        if not logs:
            st.info(t("no_logs_found"))
            return
        
        st.info(t("displaying_logs").format(count=len(logs)))
        
        # Display logs in expandable sections
        for i, log_entry in enumerate(logs):
            timestamp = log_entry.get("timestamp", t("unknown_time"))
            interaction_type = log_entry.get("type", t("unknown_type"))
            
            with st.expander(f"{timestamp} - {interaction_type}", expanded=False):
                tab1, tab2, tab3 = st.tabs([t("prompt_tab"), t("response_tab"), t("metadata_tab")])
                
                with tab1:
                    st.markdown(f"**{t('prompt_sent')}**")
                    prompt = log_entry.get("prompt", t("no_response"))
                    st.code(prompt, language="text")
                
                with tab2:
                    st.markdown(f"**{t('response_label')}**")
                    response = log_entry.get("response", t("no_response"))
                    st.markdown(response)
                
                with tab3:
                    metadata = log_entry.get("metadata", {})
                    if metadata:
                        st.json(metadata)
                    else:
                        st.info(t("no_metadata"))
        
        # Clear logs section
        st.markdown("---")
        with st.expander(t("troubleshooting"), expanded=False):
            st.markdown(t("log_info_markdown"))
            
            if st.button(t("clear_logs"), key="clear_logs_btn"):
                st.warning(t("clear_logs_warning"))
                if st.button(t("confirm_clear_logs"), key="confirm_clear_btn"):
                    logger_instance.clear_logs()
                    st.success(t("logs_cleared"))
                    st.rerun()
    
    except Exception as e:
        from utils.language_utils import t
        logger.error(f"Error rendering LLM logs tab: {str(e)}")
        st.error(f"Error loading logs: {str(e)}")


def render_professional_sidebar(llm_manager):
    """
    Render an enhanced professional sidebar with better styling.
    
    Args:
        llm_manager: LLMManager instance
    """
    from utils.language_utils import t
    
    with st.sidebar:
        # Enhanced LLM Provider info with better styling
        st.markdown(f"""
        <div class="sidebar-section">
            <h3 class="sidebar-title">🤖 {t('llm_provider_setup')}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        provider = llm_manager.provider.capitalize()
        
        if provider == "Groq":
            connection_status, message = llm_manager.check_groq_connection()
            
            # Enhanced status display
            status_color = "#28a745" if connection_status else "#dc3545"
            status_icon = "✅" if connection_status else "❌"
            status_text = t("connected") if connection_status else t("disconnected")
            
            st.markdown(f"""
            <div class="provider-status">
                <div class="provider-info">
                    <strong>{t('provider')}:</strong> {provider}
                </div>
                <div class="status-indicator" style="color: {status_color};">
                    {status_icon} <strong>{status_text}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if not connection_status:
                st.error(f"⚠️ {t('error')}: {message}")
                st.info(t("groq_api_message"))
        
        # Add system status section
        st.markdown("---")
        st.markdown(f"""
        <div class="sidebar-section">
            <h4 class="sidebar-subtitle">📊 {t('system_status')}</h4>
        </div>
        """, unsafe_allow_html=True)