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
    
    def log_interaction(self, 
                       user_id: str,
                       interaction_type: str,
                       interaction_category: str,                       
                       action: str,
                       details: Dict[str, Any] = None,
                       time_spent_seconds: int = 0,
                       success: bool = True) -> None:
        """
        Log a detailed user interaction.
        
        Args:
            user_id: The user's ID
            interaction_type: Type of interaction (e.g., 'click', 'submit', 'navigation')
            interaction_category: Category (e.g., 'code_generation', 'review', 'practice')           
            action: Specific action taken
            details: Additional details about the interaction
            time_spent_seconds: Time spent on this interaction
            success: Whether the interaction was successful
            error_message: Error message if any           
        """
        try:
            session_id = st.session_state.get("session_id")
            if not session_id:
                return
            
            # Increment interaction counter
            st.session_state.interaction_count = st.session_state.get("interaction_count", 0) + 1
            
            # Prepare data
            details_json = json.dumps(details) if details else None
            
            
            # Insert interaction record
            query = """
            INSERT INTO user_interactions 
            (user_id, interaction_type, interaction_category, 
             action, details, time_spent_seconds, success)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            self.db.execute_query(query, (               
                user_id,
                interaction_type,
                interaction_category,                
                action,
                details_json,
                time_spent_seconds,
                success              
            ))
            
            logger.debug(f"Logged interaction: {interaction_category}.{action} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")
    
    
behavior_tracker = BehaviorTracker()