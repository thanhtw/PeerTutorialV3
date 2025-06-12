"""
Student Behavior Tracking Service for Java Peer Review Training System.

This service provides comprehensive tracking of student interactions, learning patterns,
and behavior analytics for educational research and system improvement.
"""

import uuid
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import streamlit as st
from data.mysql_connection import MySQLConnection
from utils.language_utils import get_current_language

logger = logging.getLogger(__name__)

class BehaviorTracker:
    """
    Comprehensive behavior tracking service for educational analytics.
    """
    
    def __init__(self):
        """Initialize the behavior tracker with database connection."""
        self.db = MySQLConnection()
        self.current_language = get_current_language()
        
        # Initialize session tracking
        self._init_session_tracking()
    
    def _init_session_tracking(self):
        """Initialize session tracking for the current user."""
        try:
            # Generate session ID if not exists
            if "session_id" not in st.session_state:
                st.session_state.session_id = str(uuid.uuid4())
            
            # Initialize session start time
            if "session_start_time" not in st.session_state:
                st.session_state.session_start_time = time.time()
            
            # Initialize interaction counters
            if "interaction_count" not in st.session_state:
                st.session_state.interaction_count = 0
            
            # Initialize tab tracking
            if "tab_visit_times" not in st.session_state:
                st.session_state.tab_visit_times = {}
                
            if "current_tab_start_time" not in st.session_state:
                st.session_state.current_tab_start_time = time.time()
                
            # Initialize tabs visited list
            if "tabs_visited" not in st.session_state:
                st.session_state.tabs_visited = []
                
        except Exception as e:
            logger.error(f"Error initializing session tracking: {str(e)}")
    
    def start_user_session(self, user_id: str) -> str:
        """
        Start tracking a new user session.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Session ID
        """
        try:
            session_id = st.session_state.get("session_id", str(uuid.uuid4()))
            
            # Create session record
            query = """
            INSERT INTO user_sessions 
            (session_id, user_id, language_preference, tabs_visited)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            total_interactions = total_interactions + 1
            """
            
            self.db.execute_query(query, (
                session_id,
                user_id,                
                self.current_language,
                json.dumps([])
            ))
            
            logger.info(f"Started session tracking for user {user_id}, session {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting user session: {str(e)}")
            return session_id
    
    def end_user_session(self, user_id: str) -> None:
        """
        End the current user session and update duration.
        
        Args:
            user_id: The user's ID
        """
        try:
            session_id = st.session_state.get("session_id")
            if not session_id:
                return
            
            # Calculate session duration
            session_start = st.session_state.get("session_start_time", time.time())
            duration_minutes = (time.time() - session_start) / 60
            
            # Get tabs visited
            tabs_visited = st.session_state.get("tabs_visited", [])
            total_interactions = st.session_state.get("interaction_count", 0)
            
            # Update session record
            query = """
            UPDATE user_sessions 
            SET session_end = CURRENT_TIMESTAMP,
                session_duration_minutes = %s,
                total_interactions = %s,
                tabs_visited = %s
            WHERE session_id = %s AND user_id = %s
            """
            
            self.db.execute_query(query, (
                int(duration_minutes),
                total_interactions,
                json.dumps(tabs_visited),
                session_id,
                user_id
            ))
            
            logger.info(f"Ended session {session_id} for user {user_id}, duration: {duration_minutes:.1f} minutes")
            
        except Exception as e:
            logger.error(f"Error ending user session: {str(e)}")
    
    def log_interaction(self, 
                       user_id: str,
                       interaction_type: str,
                       interaction_category: str,
                       component: str,
                       action: str,
                       details: Dict[str, Any] = None,
                       time_spent_seconds: int = 0,
                       success: bool = True,
                       error_message: str = None,
                       context_data: Dict[str, Any] = None) -> None:
        """
        Log a detailed user interaction.
        
        Args:
            user_id: The user's ID
            interaction_type: Type of interaction (e.g., 'click', 'submit', 'navigation')
            interaction_category: Category (e.g., 'code_generation', 'review', 'practice')
            component: UI component name
            action: Specific action taken
            details: Additional details about the interaction
            time_spent_seconds: Time spent on this interaction
            success: Whether the interaction was successful
            error_message: Error message if any
            context_data: Additional context information
        """
        try:
            session_id = st.session_state.get("session_id")
            if not session_id:
                return
            
            # Increment interaction counter
            st.session_state.interaction_count = st.session_state.get("interaction_count", 0) + 1
            
            # Prepare data
            details_json = json.dumps(details) if details else None
            context_json = json.dumps(context_data) if context_data else None
            
            # Insert interaction record
            query = """
            INSERT INTO user_interactions 
            (session_id, user_id, interaction_type, interaction_category, component, 
             action, details, time_spent_seconds, success, error_message, context_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            self.db.execute_query(query, (
                session_id,
                user_id,
                interaction_type,
                interaction_category,
                component,
                action,
                details_json,
                time_spent_seconds,
                success,
                error_message,
                context_json
            ))
            
            logger.debug(f"Logged interaction: {interaction_category}.{component}.{action} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")
    
    
behavior_tracker = BehaviorTracker()