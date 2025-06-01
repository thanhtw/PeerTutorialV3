"""
Workflow Conditions for Java Peer Review Training System.

This module contains the conditional logic for determining
which paths to take in the LangGraph workflow with proper termination conditions.
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
        Determine if we should regenerate code or move to review - FIXED with proper termination.
        
        Args:
            state: Current workflow state
            
        Returns:
            "regenerate_code" if we need to regenerate code based on evaluation feedback
            "review_code" if the code is valid or we've reached max attempts
        """
        # Extract state attributes for clearer code
        current_step = getattr(state, "current_step", None)
        evaluation_result = getattr(state, "evaluation_result", None)
        evaluation_attempts = getattr(state, "evaluation_attempts", 0)
        max_evaluation_attempts = getattr(state, "max_evaluation_attempts", 3)
        
        logger.debug(f"Deciding workflow path with state: step={current_step}, "
                     f"valid={evaluation_result.get('valid', False) if evaluation_result else False}, "
                     f"attempts={evaluation_attempts}/{max_evaluation_attempts}")
        
        # FIXED: Always check max attempts first to prevent infinite loops
        if evaluation_attempts >= max_evaluation_attempts:
            logger.debug(f"Max evaluation attempts ({max_evaluation_attempts}) reached. Moving to review.")
            return "review_code"
        
        # Check if current step is explicitly set to regenerate
        if current_step == "regenerate":
            logger.debug(f"{t('path_decision')}: regenerate_code ({t('explicit_current_step')})")
            return "regenerate_code"
        
        # Check validity flag
        if evaluation_result and evaluation_result.get("valid", False):
            logger.debug(f"{t('path_decision')}: review_code ({t('evaluation_passed')})")
            return "review_code"

        # Check if we have missing errors and haven't reached max attempts
        has_missing_errors = evaluation_result and len(evaluation_result.get("missing_errors", [])) > 0
        
        # FIXED: Only regenerate if we have missing errors AND haven't reached max attempts
        if has_missing_errors and evaluation_attempts < max_evaluation_attempts:
            logger.debug(f"{t('path_decision')}: regenerate_code (missing errors, attempt {evaluation_attempts + 1}/{max_evaluation_attempts})")
            return "regenerate_code"
        
        # Default to review if no regeneration is needed or max attempts reached
        logger.debug(f"{t('path_decision')}: review_code (no regeneration needed or max attempts reached)")
        return "review_code"
    
    @staticmethod
    def should_continue_review(state: WorkflowState) -> str:
        """
        Determine if we should continue with another review iteration or generate comparison report - FIXED.
        
        This is used for the conditional edge from the analyze_review node.
        
        Args:
            state: Current workflow state
            
        Returns:
            "continue_review" if more review iterations are needed
            "generate_comparison_report" if the review is sufficient or max iterations reached or all issues identified
        """
        # Extract state attributes for clearer code
        current_iteration = getattr(state, "current_iteration", 1)
        max_iterations = getattr(state, "max_iterations", 3)
        review_sufficient = getattr(state, "review_sufficient", False)
        review_history = getattr(state, "review_history", [])
        
        logger.debug(f"Deciding review path with state: iteration={current_iteration}/{max_iterations}, "
                     f"sufficient={review_sufficient}")
     
        # FIXED: Always check max iterations first to prevent infinite loops
        if current_iteration > max_iterations:
            logger.debug(f"Max review iterations ({max_iterations}) reached. Moving to comparison report.")
            return "generate_comparison_report"
     
        # Get the latest review analysis
        latest_review = review_history[-1] if review_history else None

        if latest_review and hasattr(latest_review, "analysis"):
            analysis = latest_review.analysis
            identified_count = analysis.get("identified_count", 0)
            total_problems = analysis.get("total_problems", 0)
            
            # Check if all issues have been identified
            if identified_count == total_problems and total_problems > 0:              
                state.review_sufficient = True
                logger.debug(f"Review path decision: generate_comparison_report (all {total_problems} issues identified)")
                return "generate_comparison_report"
        
        # Check if review is marked as sufficient
        if review_sufficient:
            logger.debug("Review path decision: generate_comparison_report (review marked sufficient)")
            return "generate_comparison_report"
        
        # FIXED: Only continue if we haven't reached max iterations
        if current_iteration <= max_iterations:
            logger.debug(f"Review path decision: continue_review (iteration {current_iteration}/{max_iterations})")
            return "continue_review"
        else:
            # Fallback to comparison report if something goes wrong
            logger.debug("Review path decision: generate_comparison_report (fallback)")
            return "generate_comparison_report"