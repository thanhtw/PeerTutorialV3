"""
Simplified Workflow Conditions for Java Peer Review Training System.

This module contains the conditional logic for determining
which paths to take in the LangGraph workflow.
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
    
    This class contains all the conditional functions used to determine
    the next step in the workflow based on the current state.
    """
    
    @staticmethod
    def should_regenerate_or_review(state: WorkflowState) -> str:
        """
        Determine if we should regenerate code or move to review.
        
        Args:
            state: Current workflow state
            
        Returns:
            "regenerate_code" if we need to regenerate code based on evaluation feedback
            "review_code" if the code is valid or we've reached max attempts
        """
        evaluation_result = getattr(state, "evaluation_result", None)
        evaluation_attempts = getattr(state, "evaluation_attempts", 0)
        max_evaluation_attempts = getattr(state, "max_evaluation_attempts", 3)
        
        logger.debug(f"Deciding workflow path: "
                    f"valid={evaluation_result.get(t('valid'), False) if evaluation_result else False}, "
                    f"attempts={evaluation_attempts}/{max_evaluation_attempts}")
        
        # Check max attempts FIRST to prevent infinite loops
        if evaluation_attempts >= max_evaluation_attempts:
            logger.debug(f"Max evaluation attempts ({max_evaluation_attempts}) reached. Moving to review.")
            return "review_code"
        
        # Check if evaluation result is valid (no missing errors)
        if evaluation_result and evaluation_result.get(t("valid"), False):
            logger.debug("Evaluation passed. Moving to review.")
            return "review_code"

        # Check if we have missing errors and are under max attempts
        if evaluation_result:
            missing_errors = evaluation_result.get(t("missing_errors"), [])
            if len(missing_errors) > 0 and evaluation_attempts < max_evaluation_attempts:
                logger.debug(f"Found {len(missing_errors)} missing errors. "
                        f"Regenerating (attempt {evaluation_attempts + 1}/{max_evaluation_attempts})")
                return "regenerate_code"
        
        # Default to review
        logger.debug("Defaulting to review")
        return "review_code"
    
    @staticmethod
    def should_continue_review(state: WorkflowState) -> str:
        """
        Determine if we should continue with another review iteration or generate comparison report.
        
        Args:
            state: Current workflow state
            
        Returns:
            "continue_review" if more review iterations are needed
            "generate_comparison_report" if the review is sufficient or max iterations reached
        """
        current_iteration = getattr(state, "current_iteration", 1)
        max_iterations = getattr(state, "max_iterations", 3)
        review_sufficient = getattr(state, "review_sufficient", False)
        review_history = getattr(state, "review_history", [])
        
        logger.debug(f"Deciding review path: "
                     f"iteration={current_iteration}/{max_iterations}, sufficient={review_sufficient}")
     
        # Check max iterations FIRST to prevent infinite loops
        if current_iteration > max_iterations:
            logger.debug(f"Max review iterations ({max_iterations}) reached. Moving to comparison report.")
            return "generate_comparison_report"
     
        # Check if review is marked as sufficient
        if review_sufficient:
            logger.debug("Review marked as sufficient. Moving to comparison report.")
            return "generate_comparison_report"
        
        # Get the latest review analysis to check if all issues are identified
        latest_review = review_history[-1] if review_history else None

        if latest_review and hasattr(latest_review, "analysis"):
            analysis = latest_review.analysis
            identified_count = analysis.get(t("identified_count"), 0)
            total_problems = analysis.get(t("total_problems"), 0)
            
            # Check if all issues have been identified
            if identified_count >= total_problems and total_problems > 0:              
                state.review_sufficient = True
                logger.debug(f"All {total_problems} issues identified. Moving to comparison report.")
                return "generate_comparison_report"
        
        # Continue review if we haven't reached max iterations
        if current_iteration <= max_iterations:
            logger.debug(f"Continuing review (iteration {current_iteration}/{max_iterations})")
            return "continue_review"
        else:
            # Fallback to comparison report
            logger.debug("Fallback to comparison report")
            return "generate_comparison_report"