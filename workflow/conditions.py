"""
Schema-compliant Workflow Conditions for Java Peer Review Training System.

This module contains the conditional logic for determining
which paths to take in the LangGraph workflow using original condition names.
FIXED: Uses original condition names to maintain schema compatibility.
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
    between code generation/evaluation and student review phases, using
    the original condition names for schema compatibility.
    """
    
    @staticmethod
    def should_analyze_or_wait(state: WorkflowState) -> str:
        """
        PHASE 2A: Review Input Decision
        Determine if there's a pending review to analyze or if we should wait for student input.
        
        This prevents the infinite loop by ending the workflow when no review is pending.
        The workflow will be re-invoked when the student submits a review.
        
        Args:
            state: Current workflow state
            
        Returns:
            "analyze_review" if there's a pending review to analyze
            "wait_for_review" if still waiting for student input (END workflow)
        """
        pending_review = getattr(state, "pending_review", None)
        
        if pending_review and pending_review.strip():
            logger.debug("PHASE 2A: Pending review found. Proceeding to analysis.")
            return "analyze_review"
        else:
            logger.debug("PHASE 2A: No pending review. Ending workflow to wait for student input.")
            return "wait_for_review"  # This will END the workflow
    
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
    
    @staticmethod
    def should_continue_review(state: WorkflowState) -> str:
        """
        PHASE 2: Student Review Decision
        Determine if we should continue with another review iteration or generate comparison report.
        
        This condition ONLY considers student review submissions and analysis,
        NOT code generation or evaluation results.
        
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
        
        # Get the latest review analysis to check if all issues are identified
        latest_review = review_history[-1] if review_history else None

        if latest_review and hasattr(latest_review, "analysis"):
            analysis = latest_review.analysis
            identified_count = analysis.get(t("identified_count"), 0)
            total_problems = analysis.get(t("total_problems"), 0)
            
            # Check if all issues have been identified
            if identified_count >= total_problems and total_problems > 0:              
                state.review_sufficient = True
                logger.debug(f"All {total_problems} issues identified by student. Generating final report.")
                return "generate_comparison_report"
        
        # Continue review if we haven't reached max iterations and review isn't sufficient
        if current_iteration <= max_iterations:
            logger.debug(f"Continuing review phase (iteration {current_iteration}/{max_iterations})")
            return "continue_review"
        else:
            # Fallback to final report
            logger.debug("Fallback: Generating final report")
            return "generate_comparison_report"