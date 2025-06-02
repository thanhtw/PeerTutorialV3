"""
Schema-compliant Workflow Conditions for Java Peer Review Training System.

This module contains the conditional logic for determining
which paths to take in the LangGraph workflow using original condition names.
FIXED: Enhanced submit processing and better conditional logic for review workflow.
"""

import logging
from typing import Dict, Any, List, Optional
from state_schema import WorkflowState
from utils.language_utils import t

# Configure logging
logger = logging.getLogger(__name__)

class WorkflowConditions:
    """
    Conditional logic for the Java Code Review workflow.
    
    This class contains all the conditional functions with clear separation
    between code generation/evaluation and student review phases, with
    enhanced submit processing support.
    """
    
    @staticmethod
    def should_analyze_or_wait(state: WorkflowState) -> str:
        """
        PHASE 2A: Review Input Decision
        Determine if there's a pending review to analyze or if we should wait for student input.
        
        FIXED: Enhanced logic for better submit button processing support.
        
        Args:
            state: Current workflow state
            
        Returns:
            "analyze_review" if there's a pending review to analyze
            "wait_for_review" if still waiting for student input (END workflow)
        """
        try:
            pending_review = getattr(state, "pending_review", None)
            current_iteration = getattr(state, "current_iteration", 1)
            max_iterations = getattr(state, "max_iterations", 3)
            review_sufficient = getattr(state, "review_sufficient", False)
            review_history = getattr(state, "review_history", [])
            
            logger.debug(f"PHASE 2A Decision - Pending: {'Yes' if pending_review else 'No'}, "
                        f"Iteration: {current_iteration}/{max_iterations}, "
                        f"Sufficient: {review_sufficient}, "
                        f"History: {len(review_history)} entries")
            
            # FIXED: Enhanced pending review detection
            if pending_review and pending_review.strip():
                # Additional validation for meaningful review content
                review_text = pending_review.strip()
                if len(review_text) >= 10:  # Minimum meaningful review length
                    logger.debug("PHASE 2A: Valid pending review found. Proceeding to analysis.")
                    return "analyze_review"
                else:
                    logger.warning("PHASE 2A: Pending review too short, treating as no review")
            
            # Check if we've exceeded max iterations
            if current_iteration > max_iterations:
                logger.debug(f"PHASE 2A: Max iterations ({max_iterations}) exceeded. Ending workflow.")
                return "wait_for_review"
            
            # Check if review is sufficient
            if review_sufficient:
                logger.debug("PHASE 2A: Review marked as sufficient. Ending workflow.")
                return "wait_for_review"
            
            # Check if all errors found by looking at latest review analysis
            if review_history and len(review_history) > 0:
                latest_review = review_history[-1]
                if hasattr(latest_review, 'analysis') and latest_review.analysis:
                    analysis = latest_review.analysis
                    identified_count = analysis.get(t('identified_count'), 0)
                    total_problems = analysis.get(t('total_problems'), 0)
                    
                    if identified_count >= total_problems and total_problems > 0:
                        logger.debug(f"PHASE 2A: All {total_problems} errors found. Ending workflow.")
                        return "wait_for_review"
            
            # Default: wait for student input
            logger.debug("PHASE 2A: No pending review. Ending workflow to wait for student input.")
            return "wait_for_review"  # This will END the workflow
            
        except Exception as e:
            logger.error(f"Error in should_analyze_or_wait: {str(e)}")
            # Safe fallback
            return "wait_for_review"
    
    @staticmethod
    def should_regenerate_or_review(state: WorkflowState) -> str:
        """
        PHASE 1: Code Generation/Evaluation Decision (original name)
        Determine if we should regenerate code or start the review phase.
        
        This condition ONLY considers code generation and evaluation results,
        NOT student review submissions.
        
        Args:
            state: Current workflow state
            
        Returns:
            "regenerate_code" if we need to regenerate code based on evaluation feedback
            "review_code" if the code is valid or we've reached max generation attempts
        """
        try:
            evaluation_result = getattr(state, "evaluation_result", None)
            evaluation_attempts = getattr(state, "evaluation_attempts", 0)
            max_evaluation_attempts = getattr(state, "max_evaluation_attempts", 3)
           
            logger.debug(f"CODE GENERATION DECISION: "
                        f"valid={evaluation_result.get(t('valid'), False) if evaluation_result else False}, "
                        f"attempts={evaluation_attempts}/{max_evaluation_attempts}")
            
            # Check max attempts FIRST to prevent infinite loops in code generation
            if evaluation_attempts >= max_evaluation_attempts:
                logger.debug(f"Max code generation attempts ({max_evaluation_attempts}) reached. Starting review phase.")
                return "review_code"
            
            # If evaluation result is valid, we can start the review phase
            if evaluation_result and evaluation_result.get(t("valid"), False):
                logger.debug("Code evaluation passed. Starting review phase.")
                return "review_code"

            # Check if we have missing errors and are under max attempts
            if evaluation_result:
                missing_errors = evaluation_result.get(t("missing_errors"), [])
                if len(missing_errors) > 0 and evaluation_attempts < max_evaluation_attempts:
                    logger.debug(f"Found {len(missing_errors)} missing errors in code. "
                            f"Regenerating code (attempt {evaluation_attempts + 1}/{max_evaluation_attempts})")
                    return "regenerate_code"
            
            # Default to starting review if we can't determine what to do
            logger.debug("Defaulting to review phase")
            return "review_code"
            
        except Exception as e:
            logger.error(f"Error in should_regenerate_or_review: {str(e)}")
            # Safe fallback
            return "review_code"
    
    @staticmethod
    def should_continue_review(state: WorkflowState) -> str:
        """
        PHASE 2: Student Review Decision
        Determine if we should continue with another review iteration or generate comparison report.
        
        FIXED: Enhanced logic for better submit processing support.
        
        Args:
            state: Current workflow state
            
        Returns:
            "continue_review" if more review iterations are needed
            "generate_comparison_report" if the review is sufficient or max iterations reached
        """
        try:
            current_iteration = getattr(state, "current_iteration", 1)
            max_iterations = getattr(state, "max_iterations", 3)
            review_sufficient = getattr(state, "review_sufficient", False)
            review_history = getattr(state, "review_history", [])
            
            logger.debug(f"STUDENT REVIEW DECISION: "
                         f"iteration={current_iteration}/{max_iterations}, "
                         f"sufficient={review_sufficient}, "
                         f"review_count={len(review_history)}")
         
            # Check max iterations FIRST to prevent infinite loops in review phase
            if current_iteration > max_iterations:
                logger.debug(f"Max review iterations ({max_iterations}) reached. Generating final report.")
                return "generate_comparison_report"
         
            # Check if review is marked as sufficient
            if review_sufficient:
                logger.debug("Review marked as sufficient. Generating final report.")
                return "generate_comparison_report"
            
            # FIXED: Enhanced check for all issues identified
            if review_history and len(review_history) > 0:
                latest_review = review_history[-1]

                if hasattr(latest_review, "analysis") and latest_review.analysis:
                    analysis = latest_review.analysis
                    identified_count = analysis.get(t("identified_count"), 0)
                    total_problems = analysis.get(t("total_problems"), 0)
                    
                    # Check if all issues have been identified
                    if identified_count >= total_problems and total_problems > 0:              
                        state.review_sufficient = True
                        logger.debug(f"All {total_problems} issues identified by student. Generating final report.")
                        return "generate_comparison_report"
                    else:
                        logger.debug(f"Still missing issues: {identified_count}/{total_problems} identified")
            
            # FIXED: Enhanced continuation logic
            # Continue review if we haven't reached max iterations and review isn't sufficient
            if current_iteration <= max_iterations:
                logger.debug(f"Continuing review phase (iteration {current_iteration}/{max_iterations})")
                return "continue_review"
            else:
                # This should not happen due to the max_iterations check above, but safety fallback
                logger.warning("Unexpected state: iteration exceeds max but not caught earlier. Generating report.")
                return "generate_comparison_report"
                
        except Exception as e:
            logger.error(f"Error in should_continue_review: {str(e)}")
            # Safe fallback - generate report rather than continue to prevent infinite loops
            return "generate_comparison_report"
    
    @staticmethod 
    def validate_state_for_review(state: WorkflowState) -> bool:
        """
        HELPER: Validate that the state is ready for review processing.
        
        Args:
            state: Current workflow state
            
        Returns:
            True if state is valid for review processing
        """
        try:
            # Check for required code snippet
            if not hasattr(state, 'code_snippet') or not state.code_snippet:
                logger.error("State validation failed: No code snippet")
                return False
            
            # Check for required error information
            if not hasattr(state, 'original_error_count') or state.original_error_count <= 0:
                logger.error("State validation failed: No valid original error count")
                return False
            
            # Check for evaluation result
            if not hasattr(state, 'evaluation_result') or not state.evaluation_result:
                logger.warning("State validation warning: No evaluation result")
                # Not a failure, but worth noting
            
            # Check iteration settings
            if not hasattr(state, 'max_iterations') or state.max_iterations <= 0:
                logger.warning("State validation warning: Invalid max_iterations, using default")
                state.max_iterations = 3
            
            if not hasattr(state, 'current_iteration') or state.current_iteration <= 0:
                logger.warning("State validation warning: Invalid current_iteration, using default")
                state.current_iteration = 1
            
            logger.debug("State validation passed for review processing")
            return True
            
        except Exception as e:
            logger.error(f"Error validating state for review: {str(e)}")
            return False
    
    @staticmethod
    def get_review_progress_info(state: WorkflowState) -> Dict[str, Any]:
        """
        HELPER: Get current review progress information.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with progress information
        """
        try:
            current_iteration = getattr(state, "current_iteration", 1)
            max_iterations = getattr(state, "max_iterations", 3)
            review_history = getattr(state, "review_history", [])
            review_sufficient = getattr(state, "review_sufficient", False)
            pending_review = getattr(state, "pending_review", None)
            
            # Calculate progress
            progress_percentage = ((current_iteration - 1) / max_iterations) * 100
            
            # Get latest analysis if available
            latest_analysis = None
            if review_history and len(review_history) > 0:
                latest_review = review_history[-1]
                if hasattr(latest_review, 'analysis'):
                    latest_analysis = latest_review.analysis
            
            progress_info = {
                "current_iteration": current_iteration,
                "max_iterations": max_iterations,
                "review_count": len(review_history),
                "review_sufficient": review_sufficient,
                "has_pending_review": bool(pending_review and pending_review.strip()),
                "progress_percentage": progress_percentage,
                "latest_analysis": latest_analysis,
                "can_continue": current_iteration <= max_iterations and not review_sufficient
            }
            
            if latest_analysis:
                progress_info.update({
                    "identified_count": latest_analysis.get(t("identified_count"), 0),
                    "total_problems": latest_analysis.get(t("total_problems"), 0),
                    "accuracy_percentage": latest_analysis.get(t("identified_percentage"), 0)
                })
            
            return progress_info
            
        except Exception as e:
            logger.error(f"Error getting review progress info: {str(e)}")
            return {
                "current_iteration": 1,
                "max_iterations": 3,
                "review_count": 0,
                "review_sufficient": False,
                "has_pending_review": False,
                "progress_percentage": 0,
                "latest_analysis": None,
                "can_continue": True,
                "error": str(e)
            }