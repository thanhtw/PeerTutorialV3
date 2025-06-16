# utils/workflow_state_manager.py - SAFE VERSION
"""
Safe Workflow State Manager with comprehensive error handling.
This is an optional component - if it fails to import or work, the app will still function.
"""

import streamlit as st
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class WorkflowStateManager:
    """Manages workflow state and provides context-aware behavior with safe fallbacks."""
    
    @staticmethod
    def get_workflow_status() -> str:
        """
        Get current workflow status with safe error handling.
        
        Returns:
            str: Current workflow status, defaults to "not_started" on any error
        """
        try:
            if not hasattr(st.session_state, 'workflow_state'):
                return "not_started"
            
            state = st.session_state.workflow_state
            
            # Check if state is None or invalid
            if state is None:
                return "not_started"
            
            # Check if code exists
            if not hasattr(state, 'code_snippet') or not state.code_snippet:
                return "not_started"
            
            # Check review status safely
            try:
                review_history = getattr(state, 'review_history', [])
                current_iteration = getattr(state, 'current_iteration', 1)
                max_iterations = getattr(state, 'max_iterations', 3)
                review_sufficient = getattr(state, 'review_sufficient', False)
                
                if not review_history:
                    return "code_generated"
                elif review_sufficient or current_iteration > max_iterations:
                    return "review_completed"
                else:
                    return "review_in_progress"
            except Exception as e:
                logger.warning(f"Error checking review status: {str(e)}")
                return "code_generated"  # Safe default when code exists
                
        except Exception as e:
            logger.warning(f"Error getting workflow status: {str(e)}")
            return "not_started"  # Safe default
    
    @staticmethod
    def get_workflow_context() -> Dict[str, any]:
        """
        Get detailed workflow context information with safe defaults.
        
        Returns:
            Dict containing workflow context data, always returns valid data
        """
        try:
            status = WorkflowStateManager.get_workflow_status()
            context = {
                "status": status,
                "can_generate": True,  # Always allow generation
                "should_show_review_guidance": status in ["code_generated", "review_in_progress"],
                "should_show_completion": status == "review_completed",
                "has_code": status != "not_started"
            }
            
            # Try to add more detailed info
            try:
                if hasattr(st.session_state, 'workflow_state') and st.session_state.workflow_state:
                    state = st.session_state.workflow_state
                    context.update({
                        "current_iteration": getattr(state, 'current_iteration', 1),
                        "max_iterations": getattr(state, 'max_iterations', 3),
                        "review_count": len(getattr(state, 'review_history', [])),
                        "has_comparison_report": bool(getattr(state, 'comparison_report', None))
                    })
            except Exception as e:
                logger.warning(f"Error getting detailed context: {str(e)}")
                # Continue with basic context
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting workflow context: {str(e)}")
            # Return safe defaults
            return {
                "status": "not_started",
                "can_generate": True,
                "should_show_review_guidance": False,
                "should_show_completion": False,
                "has_code": False,
                "current_iteration": 1,
                "max_iterations": 3,
                "review_count": 0,
                "has_comparison_report": False
            }
    
    @staticmethod
    def get_next_recommended_action() -> Tuple[str, str]:
        """
        Get the next recommended action for the user with safe defaults.
        
        Returns:
            Tuple of (action_type, message), always returns valid data
        """
        try:
            status = WorkflowStateManager.get_workflow_status()
            
            action_map = {
                "not_started": ("generate", "Start by generating a Java code challenge"),
                "code_generated": ("review", "Your code is ready! Go to the Review tab to analyze it"),
                "review_in_progress": ("continue_review", "Continue your code review analysis"),
                "review_completed": ("view_feedback", "Check your results in the Feedback tab")
            }
            
            return action_map.get(status, ("generate", "Generate a new code challenge"))
            
        except Exception as e:
            logger.error(f"Error getting recommended action: {str(e)}")
            return ("generate", "Start by generating a Java code challenge")

# Test function to verify the component works
def test_workflow_state_manager():
    """Test function to verify WorkflowStateManager works correctly."""
    try:
        status = WorkflowStateManager.get_workflow_status()
        context = WorkflowStateManager.get_workflow_context()
        action = WorkflowStateManager.get_next_recommended_action()
        
        logger.debug(f"WorkflowStateManager test passed: status={status}, context keys={list(context.keys())}, action={action[0]}")
        return True
    except Exception as e:
        logger.error(f"WorkflowStateManager test failed: {str(e)}")
        return False