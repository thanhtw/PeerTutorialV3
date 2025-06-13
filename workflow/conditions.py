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
        """FIXED: Enhanced Review Input Decision with better state validation."""
        try:
            pending_review = getattr(state, "pending_review", None)
            current_iteration = getattr(state, "current_iteration", 1)
            max_iterations = getattr(state, "max_iterations", 3)
            review_sufficient = getattr(state, "review_sufficient", False)
            review_history = getattr(state, "review_history", [])
            
            logger.info(f"PHASE 2A Decision - Pending: {'Yes' if pending_review else 'No'}, "
                        f"Iteration: {current_iteration}/{max_iterations}, "
                        f"Sufficient: {review_sufficient}, "
                        f"History: {len(review_history)} entries")
            
            # PRIORITY 1: If there's a valid pending review, ALWAYS analyze it
            if pending_review and pending_review.strip():
                review_text = pending_review.strip()
                
                # Basic validation only - don't be too restrictive
                if len(review_text) >= 5:  # Reduced from 10
                    logger.debug("PHASE 2A: Valid pending review found. Proceeding to analysis.")
                    return "analyze_review"
                else:
                    logger.warning("PHASE 2A: Pending review too short")
                    
            # PRIORITY 2: Check completion conditions ONLY if no pending review
            if current_iteration > max_iterations:
                logger.debug("PHASE 2A: Max iterations exceeded")
                return "wait_for_review"
                
            if review_sufficient:
                logger.debug("PHASE 2A: Review marked as sufficient")
                return "wait_for_review"
                
            # Check if all errors found
            if review_history and len(review_history) > 0:
                latest_review = review_history[-1]
                if hasattr(latest_review, 'analysis') and latest_review.analysis:
                    analysis = latest_review.analysis
                    identified_count = analysis.get('identified_count', 0)
                    total_problems = analysis.get('total_problems', 0)
                    
                    if identified_count >= total_problems and total_problems > 0:
                        logger.debug("PHASE 2A: All errors found in latest review")
                        return "wait_for_review"
            
            # Default: wait for student input
            logger.debug("PHASE 2A: No pending review. Waiting for student input.")
            return "wait_for_review"
            
        except Exception as e:
            logger.error(f"Error in should_analyze_or_wait: {str(e)}")
            return "wait_for_review"
    
    @staticmethod
    def should_regenerate_or_review(state: WorkflowState) -> str:
        """
        PHASE 1: ENHANCED Code Generation Decision with safeguards.
        """
        try:
            evaluation_result = getattr(state, "evaluation_result", None)
            evaluation_attempts = getattr(state, "evaluation_attempts", 0)
            max_evaluation_attempts = getattr(state, "max_evaluation_attempts", 3)
            code_snippet = getattr(state, "code_snippet", None)
            
            # ADDED: Check if we already have valid code and shouldn't regenerate
            if code_snippet and hasattr(code_snippet, 'code') and code_snippet.code:
                # ENHANCED: Check if code was recently generated (prevent unnecessary regeneration)
                code_generation_timestamp = getattr(state, "code_generation_timestamp", None)
                if code_generation_timestamp:
                    import time
                    current_time = time.time()
                    # If code was generated within last 30 seconds, don't regenerate unless explicitly needed
                    if current_time - code_generation_timestamp < 30:
                        logger.debug("CODE GENERATION: Recent code exists, checking if regeneration is truly needed")
                        
                        # Only regenerate if there are specific missing errors and we haven't hit max attempts
                        if evaluation_result:
                            missing_errors = evaluation_result.get(t("missing_errors"), [])
                            if len(missing_errors) == 0:
                                logger.debug("CODE GENERATION: No missing errors, proceeding to review")
                                return "review_code"
                            elif evaluation_attempts >= max_evaluation_attempts:
                                logger.debug("CODE GENERATION: Max attempts reached, proceeding to review despite missing errors")
                                return "review_code"
            
            logger.debug(f"CODE GENERATION DECISION: "
                        f"valid={evaluation_result.get(t('valid'), False) if evaluation_result else False}, "
                        f"attempts={evaluation_attempts}/{max_evaluation_attempts}")
            
            # ENHANCED: Check max attempts FIRST with better logging
            if evaluation_attempts >= max_evaluation_attempts:
                logger.debug(f"CODE GENERATION: Max attempts ({max_evaluation_attempts}) reached. "
                           f"Proceeding to review phase regardless of evaluation result.")
                # ADDED: Mark generation as completed to prevent re-entry
                state.code_generation_completed = True
                return "review_code"
            
            # ENHANCED: Validation check with better error handling
            if evaluation_result:
                is_valid = evaluation_result.get(t("valid"), False)
                missing_errors = evaluation_result.get(t("missing_errors"), [])
                found_errors = evaluation_result.get(t("found_errors"), [])
                
                logger.debug(f"CODE GENERATION: Found {len(found_errors)} errors, missing {len(missing_errors)}")
                
                if is_valid or len(missing_errors) == 0:
                    logger.debug("CODE GENERATION: Evaluation passed. Starting review phase.")
                    # ADDED: Set timestamp to track when we moved to review
                    import time
                    state.review_phase_started = time.time()
                    return "review_code"
                
                # Check if we should regenerate
                if len(missing_errors) > 0 and evaluation_attempts < max_evaluation_attempts:
                    logger.debug(f"CODE GENERATION: Missing {len(missing_errors)} errors. "
                               f"Regenerating (attempt {evaluation_attempts + 1}/{max_evaluation_attempts})")
                    return "regenerate_code"
            
            # ENHANCED: Better fallback logic
            logger.debug("CODE GENERATION: No clear evaluation result, defaulting to review phase")
            return "review_code"
            
        except Exception as e:
            logger.error(f"Error in should_regenerate_or_review: {str(e)}")
            # Safe fallback to prevent infinite loops
            return "review_code"

    @staticmethod
    def should_continue_review(state: WorkflowState) -> str:
        """
        PHASE 2: ENHANCED Student Review Decision with completion safeguards.
        """
        try:
            current_iteration = getattr(state, "current_iteration", 1)
            max_iterations = getattr(state, "max_iterations", 3)
            review_sufficient = getattr(state, "review_sufficient", False)
            review_history = getattr(state, "review_history", [])
            workflow_completed = getattr(state, "workflow_completed", False)
            
            logger.debug(f"STUDENT REVIEW DECISION: "
                         f"iteration={current_iteration}/{max_iterations}, "
                         f"sufficient={review_sufficient}, "
                         f"review_count={len(review_history)}, "
                         f"completed={workflow_completed}")
         
            # ADDED: Check if workflow is already marked as completed
            if workflow_completed:
                logger.debug("STUDENT REVIEW: Workflow already completed.")
                return "generate_comparison_report"
         
            # ENHANCED: Check max iterations with better validation
            if current_iteration > max_iterations:
                logger.debug(f"STUDENT REVIEW: Max iterations ({max_iterations}) reached.")
                state.workflow_completed = True
                return "generate_comparison_report"
         
            # ENHANCED: Check if review is marked as sufficient
            if review_sufficient:
                logger.debug("STUDENT REVIEW: Review marked as sufficient.")
                state.workflow_completed = True
                return "generate_comparison_report"
            
            # ENHANCED: Check for completion based on review analysis
            if review_history and len(review_history) > 0:
                latest_review = review_history[-1]

                if hasattr(latest_review, "analysis") and latest_review.analysis:
                    analysis = latest_review.analysis
                    identified_count = analysis.get(t("identified_count"), 0)
                    total_problems = analysis.get(t("total_problems"), 0)
                    
                    # ENHANCED: More robust completion check
                    if identified_count >= total_problems and total_problems > 0:              
                        state.review_sufficient = True
                        state.workflow_completed = True
                        logger.debug(f"STUDENT REVIEW: All {total_problems} issues identified. Generating report.")
                        return "generate_comparison_report"
                    else:
                        logger.debug(f"STUDENT REVIEW: Progress - {identified_count}/{total_problems} identified")
            
            # ENHANCED: Continuation logic with safeguards
            if current_iteration <= max_iterations and not review_sufficient:
                # ADDED: Additional check to prevent infinite loops
                review_phase_started = getattr(state, "review_phase_started", None)
                if review_phase_started:
                    import time
                    current_time = time.time()
                    # If we've been in review phase for more than 10 minutes, force completion
                    if current_time - review_phase_started > 600:  # 10 minutes
                        logger.warning("STUDENT REVIEW: Review phase timeout. Forcing completion.")
                        state.workflow_completed = True
                        return "generate_comparison_report"
                
                logger.debug(f"STUDENT REVIEW: Continuing review phase (iteration {current_iteration}/{max_iterations})")
                return "continue_review"
            else:
                logger.debug("STUDENT REVIEW: Conditions met for completion. Generating report.")
                state.workflow_completed = True
                return "generate_comparison_report"
                
        except Exception as e:
            logger.error(f"Error in should_continue_review: {str(e)}")
            # Safe fallback to prevent infinite loops
            return "generate_comparison_report"
    
    @staticmethod 
    def validate_state_for_review(state: WorkflowState) -> bool:
        """
        ENHANCED: Validate state with additional consistency checks.
        """
        try:
            validation_errors = []
            
            # Check for required code snippet
            if not hasattr(state, 'code_snippet') or not state.code_snippet:
                validation_errors.append("No code snippet")
            elif not hasattr(state.code_snippet, 'code') or not state.code_snippet.code:
                validation_errors.append("Code snippet has no code content")
            
            # Check for required error information
            original_error_count = getattr(state, 'original_error_count', 0)
            if original_error_count <= 0:
                validation_errors.append("No valid original error count")
            
            # ADDED: Check for evaluation result consistency
            evaluation_result = getattr(state, 'evaluation_result', None)
            if evaluation_result:
                found_errors = evaluation_result.get(t('found_errors'), [])
                missing_errors = evaluation_result.get(t('missing_errors'), [])
                total_evaluation_errors = len(found_errors) + len(missing_errors)
                
                # Warn if there's a mismatch (but don't fail validation)
                if total_evaluation_errors != original_error_count:
                    logger.warning(f"Evaluation error count ({total_evaluation_errors}) "
                                 f"doesn't match original ({original_error_count})")
            
            # Check iteration settings with auto-correction
            max_iterations = getattr(state, 'max_iterations', 0)
            if max_iterations <= 0:
                logger.warning("Invalid max_iterations, setting to default (3)")
                state.max_iterations = 3
            
            current_iteration = getattr(state, 'current_iteration', 0)
            if current_iteration <= 0:
                logger.warning("Invalid current_iteration, setting to default (1)")
                state.current_iteration = 1
            
            # ADDED: Validate review history consistency
            review_history = getattr(state, 'review_history', [])
            if review_history:
                for i, review in enumerate(review_history):
                    if not hasattr(review, 'student_review') or not review.student_review:
                        validation_errors.append(f"Review {i+1} has no content")
                    if not hasattr(review, 'iteration_number') or review.iteration_number <= 0:
                        validation_errors.append(f"Review {i+1} has invalid iteration number")
            
            # Log validation results
            if validation_errors:
                logger.error(f"State validation failed: {'; '.join(validation_errors)}")
                return False
            else:
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