"""
Enhanced UI package for Java Peer Review Training System.

This package contains professional UI components for the Streamlit interface
with improved styling, better i18n support, and enhanced user experience.
"""

# Core UI components
from ui.components.code_generator import CodeGeneratorUI
from ui.components.code_display import CodeDisplayUI
from ui.components.feedback_system import FeedbackSystem
from ui.components.auth_ui import AuthUI

# UI utilities
from ui.utils.main_ui import (
    init_session_state,
    render_llm_logs_tab,    
    render_sidebar,
    render_professional_sidebar
)

# Animation and interactive components
from ui.components.animation import level_up_animation
from ui.components.profile_leaderboard import ProfileLeaderboardSidebar


__all__ = [
    # Core components
    'CodeGeneratorUI',
    'CodeDisplayUI', 
    'FeedbackSystem',
    'AuthUI'
        
    # UI utilities - compact and professional
    'init_session_state',
    'render_llm_logs_tab',    
    'render_sidebar',
    'render_professional_sidebar',
    
    # Interactive components - optimized sizing
    'level_up_animation',
    'ProfileLeaderboardSidebar'
]