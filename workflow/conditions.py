"""
Workflow Conditions for Java Peer Review Training System.

This module contains the conditional logic for determining
which paths to take in the LangGraph workflow with proper termination conditions.
FIXED: Improved conditional logic with workflow phase awareness and robust termination.
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
    FIXED: Improved conditional logic with workflow phase awareness and robust termination.
    """
    
    @staticmethod
    def should_regenerate_or_review(state: WorkflowState) -> str:
        """
        Determine if we should regenerate code or move to review.
        FIXED: Enhanced logic with workflow phase awareness and robust termination conditions.
        
        Args:
            state: Current workflow state
            
        Returns:
            "regenerate_code" if we need to regenerate code based on evaluation feedback
            "review_code" if the code is valid or we've reached max attempts or in generation-only phase
        """
        # Extract state attributes for clearer code
        evaluation_result = getattr(state, "evaluation_result", None)
        evaluation_attempts = getattr(state, "evaluation_attempts", 0)
        max_evaluation_attempts = getattr(state, "max_evaluation_attempts", 3)
        workflow_phase = getattr(state, "workflow_phase", "full")
        
        logger.debug(f"Deciding workflow path: phase={workflow_phase}, "
                     f"valid={evaluation_result.get(t('valid'), False) if evaluation_result else False}, "
                     f"attempts={evaluation_attempts}/{max_evaluation_attempts}")
        
        # CRITICAL: Always check max attempts FIRST to prevent infinite loops
        if evaluation_attempts >= max_evaluation_attempts:
            logger.debug(f"Max evaluation attempts ({max_evaluation_attempts}) reached. FORCING move to review.")
            return "review_code"
        
        # Check if evaluation result is valid (no missing errors)
        if evaluation_result and evaluation_result.get(t("valid"), False):
            logger.debug("Evaluation passed. Moving to review.")
            return "review_code"

        # If we're in generation-only phase and have any evaluation result, move to review
        # This prevents the workflow from getting stuck in generation phase
        if workflow_phase == "generation" and evaluation_result is not None:
            logger.debug("Generation-only phase complete, moving to review regardless of validation.")
            return "review_code"

        # Check if we have missing errors and are under max attempts
        if evaluation_result:
            missing_errors = evaluation_result.get(t("missing_errors"), [])
            if len(missing_errors) > 0 and evaluation_attempts < max_evaluation_attempts:
                logger.debug(f"Found {len(missing_errors)} missing errors. "
                           f"Regenerating (attempt {evaluation_attempts + 1}/{max_evaluation_attempts})")
                return "regenerate_code"
        
        # Safety fallback - always go to review if conditions aren't met
        logger.debug("Defaulting to review (safety fallback)")
        return "review_code"
    
    @staticmethod
    def should_continue_review(state: WorkflowState) -> str:
        """
        Determine if we should continue with another review iteration or generate comparison report.
        FIXED: Enhanced logic with workflow phase awareness and robust termination conditions.
        
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
        workflow_phase = getattr(state, "workflow_phase", "full")
        
        logger.debug(f"Deciding review path: phase={workflow_phase}, "
                     f"iteration={current_iteration}/{max_iterations}, sufficient={review_sufficient}")
     
        # CRITICAL: Always check max iterations FIRST to prevent infinite loops
        if current_iteration > max_iterations:
            logger.debug(f"Max review iterations ({max_iterations}) reached. FORCING move to comparison report.")
            return "generate_comparison_report"
     
        # Check if review is marked as sufficient
        if review_sufficient:
            logger.debug("Review marked as sufficient. Moving to comparison report.")
            return "generate_comparison_report"
        
        # If we're in generation-only phase, skip review iterations
        if workflow_phase == "generation":
            logger.debug("Generation-only phase, skipping review iterations.")
            return "generate_comparison_report"
        
        # Get the latest review analysis
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
        
        # Only continue if we haven't reached max iterations and we're in a review phase
        if current_iteration <= max_iterations and workflow_phase in ["review", "full"]:
            logger.debug(f"Continuing review (iteration {current_iteration}/{max_iterations})")
            return "continue_review"
        else:
            # Safety fallback to comparison report
            logger.debug("Fallback to comparison report (safety)")
            return "generate_comparison_report"
    
    @staticmethod
    def should_skip_review_in_generation_phase(state: WorkflowState) -> bool:
        """
        Helper method to determine if review should be skipped in generation-only phase.
        
        Args:
            state: Current workflow state
            
        Returns:
            True if review should be skipped, False otherwise
        """
        workflow_phase = getattr(state, "workflow_phase", "full")
        return workflow_phase == "generation"