"""
Simplified LangGraph Workflow for Java Peer Review Training System.

This module implements the code review workflow as a LangGraph graph
by leveraging the modular components from the workflow package.
FIXED: Submit button now properly uses LangGraph workflow execution.
"""

__all__ = ['JavaCodeReviewGraph']

import streamlit as st
import logging
from typing import Dict, List, Any, Optional

from state_schema import WorkflowState, ReviewAttempt

# Import workflow components
from workflow.manager import WorkflowManager
from workflow.conditions import WorkflowConditions
from utils.language_utils import t


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class JavaCodeReviewGraph:
    """
    Simplified LangGraph implementation of the Java Code Review workflow.
    
    This class provides a clean interface to the LangGraph workflow
    with straightforward execution methods.
    FIXED: Now properly uses LangGraph workflow execution for review processing.
    """
    
    def __init__(self, llm_manager=None):
        """
        Initialize the graph with domain components.
        
        Args:
            llm_manager: Optional LLMManager for managing language models
        """
        # Initialize the workflow manager with LLM manager
        self.llm_manager = llm_manager
        self.workflow_manager = WorkflowManager(llm_manager)
        
        # Get references to workflow components
        self.error_repository = self.workflow_manager.error_repository
        self.workflow_nodes = self.workflow_manager.workflow_nodes
        self.conditions = WorkflowConditions()
        
        # Get the compiled workflow
        self._compiled_workflow = self.workflow_manager.get_compiled_workflow()
        
        logger.debug("JavaCodeReviewGraph initialized successfully")
    
    def execute_code_generation(self, state: WorkflowState) -> WorkflowState:
        """
        Execute code generation workflow.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state after code generation and evaluation
        """
        try:
            logger.debug("Executing code generation")
            
            # Validate the workflow state before proceeding
            is_valid, error_message = self.workflow_manager.validate_workflow_state(state)
            if not is_valid:
                logger.error(f"Invalid workflow state: {error_message}")
                state.error = error_message
                return state
            
            # Set initial step
            state.current_step = "generate"
            
            # Execute using the workflow manager
            result = self.workflow_manager.execute_code_generation_workflow(state)
            
            # Log the workflow status
            if not result.error:
                logger.debug("Code generation completed successfully")
            else:
                logger.error(f"Code generation failed: {result.error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in code generation: {str(e)}")
            state.error = f"Code generation failed: {str(e)}"
            return state
    
    def submit_review(self, state: WorkflowState, student_review: str) -> WorkflowState:
        """
        Submit a student review and update the state using proper LangGraph workflow execution.
        FIXED: Now uses workflow manager instead of directly calling nodes.
        
        Args:
            state: Current workflow state
            student_review: The student's review text
            
        Returns:
            Updated workflow state with analysis
        """
        try:
            logger.debug(f"Submitting review for iteration {state.current_iteration}")
            logger.debug(f"Review text length: {len(student_review)} characters")
            
            # Validate input
            if not student_review or not student_review.strip():
                logger.error("Student review cannot be empty")
                state.error = "Student review cannot be empty"
                return state
            
            review_text = student_review.strip()
            if len(review_text) < 10:
                logger.error("Student review too short")
                state.error = "Student review too short (minimum 10 characters)"
                return state
            
            # FIXED: Use workflow manager to execute review workflow instead of direct node call
            logger.debug("Executing review workflow through WorkflowManager")
            updated_state = self.workflow_manager.execute_review_workflow(state, review_text)
            
            # Check if this is the last iteration or review is sufficient
            if (updated_state.current_iteration > updated_state.max_iterations or 
                updated_state.review_sufficient):
                # Generate comparison report for feedback tab
                self._generate_review_feedback(updated_state)
            
            logger.debug("Review submission completed successfully")
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in submit_review: {str(e)}", exc_info=True)
            state.error = f"Review submission failed: {str(e)}"
            return state
    
    def _generate_review_feedback(self, state: WorkflowState) -> None:
        """
        Generate feedback for review completion with proper language support.
        Now also updates category statistics.
        
        Args:
            state: Current workflow state
        """
        # Check if we have review history
        if not state.review_history:
            logger.warning(t("no_review_history_found"))
            return
                
        # Get latest review
        latest_review = state.review_history[-1]       
        # Generate comparison report if not already generated
        if not state.comparison_report and state.evaluation_result:
            try:
                logger.debug(t("generating_comparison_report"))
                # Extract error information from evaluation results
                found_errors = state.evaluation_result.get(t('found_errors'), [])                
                # Get original error count for consistent metrics
                original_error_count = state.original_error_count                
                # Update the analysis with the original error count if needed
                if original_error_count > 0 and "original_error_count" not in latest_review.analysis:
                    latest_review.analysis["original_error_count"] = original_error_count
                    
                    # Recalculate percentages based on original count
                    identified_count = latest_review.analysis[t('identified_count')]
                    latest_review.analysis[t("identified_percentage")] = (identified_count / original_error_count) * 100
                    latest_review.analysis[t("accuracy_percentage")] = (identified_count / original_error_count) * 100
                        
                # Convert review history to format expected by generate_comparison_report
                converted_history = []
                for review in state.review_history:
                    converted_history.append({
                        "iteration_number": review.iteration_number,
                        "student_comment": review.student_review,
                        "review_analysis": review.analysis,
                        "targeted_guidance": review.targeted_guidance
                    })
                        
                if hasattr(self, "evaluator") and self.evaluator:
                    state.comparison_report = self.evaluator.generate_comparison_report(
                        found_errors,
                        latest_review.analysis,
                        converted_history
                    )
                    logger.debug(t("generated_comparison_report"))
                
                if "auth" in st.session_state and st.session_state.auth.get("is_authenticated", False):
                    user_id = st.session_state.auth.get("user_id")
                    if user_id:
                        # Check if badge manager is available
                        try:
                            from auth.badge_manager import BadgeManager
                            badge_manager = BadgeManager()
                            
                            # Get error categories from found_errors
                            if state.evaluation_result and t('found_errors') in state.evaluation_result:
                                found_errors = state.evaluation_result[t('found_errors')]
                                
                                # Group by category
                                category_stats = {}
                                for error in found_errors:
                                    error_str = str(error)
                                    # Extract category from error string (e.g., "LOGICAL - Off-by-one error")
                                    parts = error_str.split(" - ", 1)
                                    if len(parts) > 0:
                                        category = parts[0]
                                        if category not in category_stats:
                                            category_stats[category] = {"encountered": 0, "identified": 0}
                                        category_stats[category]["encountered"] += 1
                                
                                # Update identified counts from review analysis
                                if latest_review and latest_review.analysis:
                                    identified = latest_review.analysis.get(t('identified_problems'), [])
                                    for problem in identified:
                                        problem_str = str(problem)
                                        parts = problem_str.split(" - ", 1)
                                        if len(parts) > 0:
                                            category = parts[0]
                                            if category in category_stats:
                                                category_stats[category]["identified"] += 1
                                
                                # Update stats for each category
                                for category, stats in category_stats.items():
                                    badge_manager.update_category_stats(
                                        user_id,
                                        category,
                                        stats["encountered"],
                                        stats["identified"]
                                    )
                        except ImportError:
                            logger.warning("Badge manager not available")
                        except Exception as e:
                            logger.error(f"Error updating category stats: {str(e)}")
                
                    
            except Exception as e:
                logger.error(f"{t('error')} {t('generating_comparison_report')}: {str(e)}")
                state.comparison_report = (
                    f"# {t('review_feedback')}\n\n"
                    f"{t('error_generating_report')} "
                    f"{t('check_review_history')}."
                )

    def execute_full_workflow(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the complete workflow from start to finish.
        
        Args:
            state: Initial workflow state
            
        Returns:
            Final workflow state after complete execution
        """
        try:
            logger.debug("Executing full workflow")
            
            # Use the workflow manager execution method
            result = self.workflow_manager.execute_full_workflow(state)
            
            logger.debug("Full workflow execution completed")
            return result
            
        except Exception as e:
            logger.error(f"Error executing full workflow: {str(e)}")
            state.error = f"Full workflow execution failed: {str(e)}"
            return state
    
    def get_all_error_categories(self) -> Dict[str, List[str]]:
        """Get all available error categories."""
        return self.workflow_manager.get_all_error_categories()
    
    def validate_state(self, state: WorkflowState) -> tuple[bool, str]:
        """Validate the workflow state."""
        return self.workflow_manager.validate_workflow_state(state)
    
    def get_workflow_status(self, state: WorkflowState) -> Dict[str, Any]:
        """Get the current status of the workflow."""
        return self.workflow_manager.get_workflow_status(state)
    
    def get_compiled_workflow(self):
        """Get the compiled LangGraph workflow."""
        return self._compiled_workflow
    
    def reset_workflow_state(self, state: WorkflowState) -> WorkflowState:
        """Reset the workflow state for a fresh start."""
        try:
            # Reset execution state while preserving configuration
            state.current_step = "generate"
            state.evaluation_attempts = 0
            state.evaluation_result = None
            state.code_generation_feedback = None
            state.code_snippet = None
            state.review_history = []
            state.current_iteration = 1
            state.review_sufficient = False
            state.comparison_report = None
            state.pending_review = None
            state.error = None
            state.final_summary = None
            
            logger.debug("Workflow state reset successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error resetting workflow state: {str(e)}")
            state.error = f"Failed to reset workflow state: {str(e)}"
            return state