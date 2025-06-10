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
            VALUES (%s, %s, %s, %s, %s)
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
    
    def start_practice_session(self, 
                              user_id: str,
                              error_code: str,
                              error_name: str,
                              error_category: str,
                              difficulty_level: str) -> str:
        """
        Start tracking a practice session in Error Explorer.
        
        Args:
            user_id: The user's ID
            error_code: Code of the error being practiced
            error_name: Name of the error
            error_category: Category of the error
            difficulty_level: Difficulty level
            
        Returns:
            Practice session ID
        """
        try:
            practice_session_id = str(uuid.uuid4())
            session_id = st.session_state.get("session_id")
            
            # Store in session state for tracking
            st.session_state.practice_session_id = practice_session_id
            st.session_state.practice_start_time = time.time()
            
            # Insert practice session record
            query = """
            INSERT INTO practice_sessions 
            (practice_session_id, user_id, session_id, error_code, error_name, 
             error_category, difficulty_level, status, practice_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            practice_data = {
                "start_time": datetime.now().isoformat(),
                "language": self.current_language,
                "source": "error_explorer"
            }
            
            self.db.execute_query(query, (
                practice_session_id,
                user_id,
                session_id,
                error_code,
                error_name,
                error_category,
                difficulty_level,
                "setup",
                json.dumps(practice_data)
            ))
            
            # Log the interaction
            self.log_interaction(
                user_id=user_id,
                interaction_type="start_session",
                interaction_category="practice",
                component="error_explorer",
                action="start_practice",
                details={
                    "error_code": error_code,
                    "error_name": error_name,
                    "error_category": error_category,
                    "difficulty_level": difficulty_level
                }
            )
            
            logger.info(f"Started practice session {practice_session_id} for error {error_code}")
            return practice_session_id
            
        except Exception as e:
            logger.error(f"Error starting practice session: {str(e)}")
            return str(uuid.uuid4())  # Return a fallback ID
    
    def update_practice_session(self,
                               user_id: str,
                               status: str,
                               additional_data: Dict[str, Any] = None) -> None:
        """
        Update the current practice session status and data.
        
        Args:
            user_id: The user's ID
            status: New status ('setup', 'code_ready', 'review_complete', 'abandoned')
            additional_data: Additional data to store
        """
        try:
            practice_session_id = st.session_state.get("practice_session_id")
            if not practice_session_id:
                return
            
            # Calculate duration if completing
            if status in ["review_complete", "abandoned"]:
                start_time = st.session_state.get("practice_start_time", time.time())
                duration_minutes = (time.time() - start_time) / 60
                
                query = """
                UPDATE practice_sessions 
                SET status = %s, completed_at = CURRENT_TIMESTAMP, 
                    total_duration_minutes = %s, practice_data = JSON_MERGE_PATCH(practice_data, %s)
                WHERE practice_session_id = %s AND user_id = %s
                """
                
                update_data = additional_data or {}
                update_data["completion_time"] = datetime.now().isoformat()
                
                self.db.execute_query(query, (
                    status,
                    int(duration_minutes),
                    json.dumps(update_data),
                    practice_session_id,
                    user_id
                ))
            else:
                query = """
                UPDATE practice_sessions 
                SET status = %s, practice_data = JSON_MERGE_PATCH(practice_data, %s)
                WHERE practice_session_id = %s AND user_id = %s
                """
                
                self.db.execute_query(query, (
                    status,
                    json.dumps(additional_data or {}),
                    practice_session_id,
                    user_id
                ))
            
            # Log the status change
            self.log_interaction(
                user_id=user_id,
                interaction_type="status_change",
                interaction_category="practice",
                component="practice_session",
                action=f"status_changed_to_{status}",
                details=additional_data
            )
            
            logger.debug(f"Updated practice session {practice_session_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Error updating practice session: {str(e)}")
    
    def start_workflow_tracking(self,
                               user_id: str,
                               workflow_type: str = "main_workflow",
                               initial_step: str = "generate",
                               configuration: Dict[str, Any] = None) -> str:
        """
        Start tracking a main workflow session.
        
        Args:
            user_id: The user's ID
            workflow_type: Type of workflow
            initial_step: Starting step
            configuration: Initial configuration data
            
        Returns:
            Workflow ID
        """
        try:
            workflow_id = str(uuid.uuid4())
            session_id = st.session_state.get("session_id")
            
            # Store in session state
            st.session_state.workflow_id = workflow_id
            st.session_state.workflow_start_time = time.time()
            st.session_state.workflow_step_times = {}
            
            # Extract configuration data
            config = configuration or {}
            selected_categories = config.get("selected_categories", [])
            selected_errors = config.get("selected_errors", [])
            code_length = config.get("code_length", "medium")
            difficulty_level = config.get("difficulty_level", "medium")
            
            # Insert workflow tracking record
            query = """
            INSERT INTO workflow_tracking 
            (workflow_id, user_id, session_id, workflow_type, current_step,
             selected_categories, selected_errors, code_length, difficulty_level, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            self.db.execute_query(query, (
                workflow_id,
                user_id,
                session_id,
                workflow_type,
                initial_step,
                json.dumps(selected_categories),
                json.dumps(selected_errors),
                code_length,
                difficulty_level,
                "in_progress"
            ))
            
            # Log the interaction
            self.log_interaction(
                user_id=user_id,
                interaction_type="start_workflow",
                interaction_category="main_workflow",
                component="workflow_manager",
                action="start_workflow",
                details=configuration
            )
            
            logger.info(f"Started workflow tracking {workflow_id} for user {user_id}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Error starting workflow tracking: {str(e)}")
            return str(uuid.uuid4())
    
    def update_workflow_step(self,
                            user_id: str,
                            new_step: str,
                            step_data: Dict[str, Any] = None) -> None:
        """
        Update the current workflow step and track time spent.
        
        Args:
            user_id: The user's ID
            new_step: The new workflow step
            step_data: Additional step data
        """
        try:
            workflow_id = st.session_state.get("workflow_id")
            if not workflow_id:
                return
            
            # Track time spent on previous step
            step_times = st.session_state.get("workflow_step_times", {})
            current_time = time.time()
            
            # Update step timing
            if new_step not in step_times:
                step_times[new_step] = {"start_time": current_time, "total_time": 0}
            
            st.session_state.workflow_step_times = step_times
            
            # Update database
            query = """
            UPDATE workflow_tracking 
            SET current_step = %s, total_steps_completed = total_steps_completed + 1
            WHERE workflow_id = %s AND user_id = %s
            """
            
            self.db.execute_query(query, (new_step, workflow_id, user_id))
            
            # Log the step change
            self.log_interaction(
                user_id=user_id,
                interaction_type="step_change",
                interaction_category="main_workflow",
                component="workflow_step",
                action=f"moved_to_{new_step}",
                details=step_data
            )
            
            logger.debug(f"Updated workflow {workflow_id} to step {new_step}")
            
        except Exception as e:
            logger.error(f"Error updating workflow step: {str(e)}")
    
    def complete_workflow(self,
                         user_id: str,
                         final_results: Dict[str, Any] = None) -> None:
        """
        Complete the current workflow tracking.
        
        Args:
            user_id: The user's ID
            final_results: Final workflow results
        """
        try:
            workflow_id = st.session_state.get("workflow_id")
            if not workflow_id:
                return
            
            # Calculate total duration
            start_time = st.session_state.get("workflow_start_time", time.time())
            total_duration = time.time() - start_time
            
            # Update workflow completion
            query = """
            UPDATE workflow_tracking 
            SET completed_at = CURRENT_TIMESTAMP, 
                status = 'completed',
                final_results = %s
            WHERE workflow_id = %s AND user_id = %s
            """
            
            self.db.execute_query(query, (
                json.dumps(final_results or {}),
                workflow_id,
                user_id
            ))
            
            # Log completion
            self.log_interaction(
                user_id=user_id,
                interaction_type="complete_workflow",
                interaction_category="main_workflow",
                component="workflow_manager",
                action="workflow_completed",
                details=final_results,
                time_spent_seconds=int(total_duration)
            )
            
            logger.info(f"Completed workflow {workflow_id} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error completing workflow: {str(e)}")
    
    def track_tab_navigation(self,
                            user_id: str,
                            from_tab: str,
                            to_tab: str,
                            tab_index: int,
                            trigger: str = "click") -> None:
        """
        Track tab navigation behavior.
        
        Args:
            user_id: The user's ID
            from_tab: Previous tab name
            to_tab: New tab name
            tab_index: Tab index
            trigger: What triggered the navigation
        """
        try:
            session_id = st.session_state.get("session_id")
            if not session_id:
                return
            
            # Calculate time spent on previous tab
            current_time = time.time()
            previous_tab_time = st.session_state.get("current_tab_start_time", current_time)
            time_spent = int(current_time - previous_tab_time)
            
            # Update tab start time
            st.session_state.current_tab_start_time = current_time
            
            # Add to tabs visited list
            tabs_visited = st.session_state.get("tabs_visited", [])
            if to_tab not in tabs_visited:
                tabs_visited.append(to_tab)
                st.session_state.tabs_visited = tabs_visited
            
            # Insert navigation record
            query = """
            INSERT INTO tab_navigation 
            (session_id, user_id, from_tab, to_tab, tab_index, 
             time_spent_on_previous_tab_seconds, navigation_trigger)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            self.db.execute_query(query, (
                session_id,
                user_id,
                from_tab,
                to_tab,
                tab_index,
                time_spent,
                trigger
            ))
            
            # Log the navigation
            self.log_interaction(
                user_id=user_id,
                interaction_type="navigation",
                interaction_category="tab_navigation",
                component="tab_container",
                action=f"navigate_to_{to_tab}",
                details={
                    "from_tab": from_tab,
                    "to_tab": to_tab,
                    "tab_index": tab_index,
                    "trigger": trigger,
                    "time_spent_seconds": time_spent
                }
            )
            
            logger.debug(f"Tracked tab navigation: {from_tab} -> {to_tab} (spent {time_spent}s)")
            
        except Exception as e:
            logger.error(f"Error tracking tab navigation: {str(e)}")
    
    def track_error_identification(self,
                                  user_id: str,
                                  error_code: str,
                                  review_iteration: int,
                                  review_text: str,
                                  identified_correctly: bool,
                                  time_to_identify: int,
                                  analysis_data: Dict[str, Any] = None) -> None:
        """
        Track error identification attempts and accuracy.
        
        Args:
            user_id: The user's ID
            error_code: Code of the error being identified
            review_iteration: Current review iteration
            review_text: Student's review text
            identified_correctly: Whether the error was correctly identified
            time_to_identify: Time taken to identify the error
            analysis_data: Additional analysis data from LLM
        """
        try:
            session_id = st.session_state.get("session_id")
            practice_session_id = st.session_state.get("practice_session_id")
            workflow_id = st.session_state.get("workflow_id")
            
            # Insert error identification record
            query = """
            INSERT INTO error_identification_analysis 
            (user_id, session_id, practice_session_id, workflow_id, error_code,
             review_iteration, review_text, identified_correctly, time_to_identify_seconds,
             llm_analysis_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            self.db.execute_query(query, (
                user_id,
                session_id,
                practice_session_id,
                workflow_id,
                error_code,
                review_iteration,
                review_text,
                identified_correctly,
                time_to_identify,
                json.dumps(analysis_data or {})
            ))
            
            # Update learning path progress
            self._update_learning_progress(user_id, error_code, identified_correctly, time_to_identify)
            
            # Log the identification attempt
            self.log_interaction(
                user_id=user_id,
                interaction_type="error_identification",
                interaction_category="review_analysis",
                component="review_evaluator",
                action="identify_error",
                details={
                    "error_code": error_code,
                    "identified_correctly": identified_correctly,
                    "review_iteration": review_iteration,
                    "time_to_identify": time_to_identify
                },
                success=identified_correctly
            )
            
            logger.debug(f"Tracked error identification: {error_code}, correct: {identified_correctly}")
            
        except Exception as e:
            logger.error(f"Error tracking error identification: {str(e)}")
    
    def _update_learning_progress(self,
                                 user_id: str,
                                 error_code: str,
                                 identified_correctly: bool,
                                 time_to_identify: int) -> None:
        """
        Update learning path progress for the user.
        
        Args:
            user_id: The user's ID
            error_code: Error code
            identified_correctly: Whether correctly identified
            time_to_identify: Time taken
        """
        try:
            # Get error category from error code
            error_query = """
            SELECT ec.name_en as category_name 
            FROM java_errors je 
            JOIN error_categories ec ON je.category_id = ec.id 
            WHERE je.error_code = %s
            """
            
            result = self.db.execute_query(error_query, (error_code,), fetch_one=True)
            if not result:
                return
            
            error_category = result['category_name']
            
            # Update or insert learning progress
            query = """
            INSERT INTO learning_path_progress 
            (user_id, error_category, total_encounters, successful_identifications,
             average_time_to_identify_seconds, progress_data)
            VALUES (%s, %s, 1, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            total_encounters = total_encounters + 1,
            successful_identifications = successful_identifications + %s,
            average_time_to_identify_seconds = (
                (average_time_to_identify_seconds * (total_encounters - 1) + %s) / total_encounters
            ),
            mastery_level = LEAST(1.0, successful_identifications / GREATEST(1, total_encounters)),
            progress_data = JSON_MERGE_PATCH(progress_data, %s)
            """
            
            success_count = 1 if identified_correctly else 0
            progress_data = {
                "last_encounter": datetime.now().isoformat(),
                "last_time_to_identify": time_to_identify,
                "last_success": identified_correctly
            }
            
            self.db.execute_query(query, (
                user_id,
                error_category,
                success_count,
                time_to_identify,
                json.dumps(progress_data),
                success_count,
                time_to_identify,
                json.dumps(progress_data)
            ))
            
            logger.debug(f"Updated learning progress for {error_category}")
            
        except Exception as e:
            logger.error(f"Error updating learning progress: {str(e)}")
    
    def get_user_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a user.
        
        Args:
            user_id: The user's ID
            days: Number of days to look back
            
        Returns:
            Analytics data dictionary
        """
        try:
            # Time range
            start_date = datetime.now() - timedelta(days=days)
            
            analytics = {}
            
            # Session statistics
            session_query = """
            SELECT COUNT(*) as session_count,
                   AVG(session_duration_minutes) as avg_duration,
                   SUM(total_interactions) as total_interactions
            FROM user_sessions 
            WHERE user_id = %s AND session_start >= %s
            """
            
            session_result = self.db.execute_query(session_query, (user_id, start_date), fetch_one=True)
            analytics['session_stats'] = session_result or {}
            
            # Practice session statistics
            practice_query = """
            SELECT COUNT(*) as practice_count,
                   AVG(total_duration_minutes) as avg_practice_duration,
                   SUM(CASE WHEN status = 'review_complete' THEN 1 ELSE 0 END) as completed_practices
            FROM practice_sessions 
            WHERE user_id = %s AND started_at >= %s
            """
            
            practice_result = self.db.execute_query(practice_query, (user_id, start_date), fetch_one=True)
            analytics['practice_stats'] = practice_result or {}
            
            # Learning progress
            progress_query = """
            SELECT error_category, mastery_level, total_encounters, successful_identifications
            FROM learning_path_progress 
            WHERE user_id = %s
            ORDER BY mastery_level DESC
            """
            
            progress_results = self.db.execute_query(progress_query, (user_id,))
            analytics['learning_progress'] = progress_results or []
            
            # Most practiced errors
            error_query = """
            SELECT error_code, COUNT(*) as practice_count
            FROM error_identification_analysis 
            WHERE user_id = %s AND analysis_timestamp >= %s
            GROUP BY error_code
            ORDER BY practice_count DESC
            LIMIT 10
            """
            
            error_results = self.db.execute_query(error_query, (user_id, start_date))
            analytics['most_practiced_errors'] = error_results or []
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {str(e)}")
            return {}

# Singleton instance
behavior_tracker = BehaviorTracker()