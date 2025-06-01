"""
Workflow Nodes for Java Peer Review Training System.

This module contains the node implementations for the LangGraph workflow,
separating node logic from graph construction for better maintainability.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional

from state_schema import WorkflowState, CodeSnippet
from utils.code_utils import extract_both_code_versions, create_regeneration_prompt, get_error_count_from_state
from utils.language_utils import t
import random
import logging

# Configure logging
logger = logging.getLogger(__name__)

class WorkflowNodes:
    """
    Node implementations for the Java Code Review workflow.
    
    This class contains all node handlers that process state transitions
    in the LangGraph workflow, extracted for better separation of concerns.
    """
    
    def __init__(self, code_generator, code_evaluation, error_repository, llm_logger):
        """
        Initialize workflow nodes with required components.
        
        Args:
            code_generator: Component for generating Java code with errors
            code_evaluation: Component for evaluating generated code quality
            error_repository: Repository for accessing Java error data
            llm_logger: Logger for tracking LLM interactions
        """
        self.code_generator = code_generator
        self.code_evaluation = code_evaluation
        self.error_repository = error_repository
        self.llm_logger = llm_logger
    
    def review_code_node(self, state: WorkflowState) -> WorkflowState:
        """
        Review code node - waits for student review submission and processes it.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        # Check if there's a pending review to process
        if hasattr(state, 'pending_review') and state.pending_review:
            # Process the pending review
            student_review = state.pending_review
            
            # Create a new review attempt
            from state_schema import ReviewAttempt
            review_attempt = ReviewAttempt(
                student_review=student_review,
                iteration_number=state.current_iteration,
                analysis={},
                targeted_guidance=None
            )
            
            # Add to review history
            state.review_history.append(review_attempt)
            
            # Clear the pending review
            state.pending_review = None
            
            # Set step to analyze
            state.current_step = "analyze"
            
            logger.debug(f"Processed student review for iteration {state.current_iteration}")
        else:
            # Set state to waiting for review
            state.current_step = "review"
            logger.debug("Waiting for student review submission")
        
        return state
    
    def comparison_report_node(self, state: WorkflowState) -> WorkflowState:
        """
        Generate comparison report node - NEW NODE.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state with comparison report
        """
        try:
            logger.debug("Generating comparison report")
            
            # Check if we have review history
            if not state.review_history:
                logger.warning(t("no_review_history_found"))
                state.current_step = "complete"
                return state
                    
            # Get latest review
            latest_review = state.review_history[-1]
            
            # Generate comparison report if not already generated
            if not state.comparison_report and state.evaluation_result:
                # Extract error information from evaluation results
                found_errors = state.evaluation_result.get(t('found_errors'), [])
                
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
                else:
                    # Fallback comparison report
                    state.comparison_report = self._generate_fallback_comparison_report(state, latest_review)
            
            # Update state - FIXED: Use correct step name
            state.current_step = "generate_comparison_report"
            
            return state
            
        except Exception as e:
            logger.error(f"Error generating comparison report: {str(e)}", exc_info=True)
            state.error = f"Error generating comparison report: {str(e)}"
            return state
    
    def _generate_fallback_comparison_report(self, state: WorkflowState, latest_review) -> str:
        """Generate a basic comparison report as fallback."""
        try:
            analysis = latest_review.analysis
            identified_count = analysis.get(t('identified_count'), 0)
            total_problems = analysis.get(t('total_problems'), 0)
            accuracy = analysis.get(t('identified_percentage'), 0)
            
            report = f"""# {t('review_feedback')}

## {t('performance_summary')}
- {t('issues_identified')}: {identified_count}/{total_problems}
- {t('accuracy')}: {accuracy:.1f}%
- {t('review_attempts')}: {len(state.review_history)}

## {t('completion_status')}
{"✅ " + t('all_issues_found') if identified_count == total_problems else "⚠️ " + t('some_issues_missed')}

{t('review_completed_successfully')}
"""
            return report
        except Exception as e:
            logger.error(f"Error generating fallback report: {str(e)}")
            return f"# {t('review_feedback')}\n\n{t('error_generating_report')}"

    # ... (include all other existing node methods here)
    
    def generate_code_node(self, state: WorkflowState) -> WorkflowState:
        """Generate Java code with errors based on selected parameters."""
        try:
            # Get parameters from state
            code_length = getattr(state, "code_length", "medium")
            difficulty_level = getattr(state, "difficulty_level", "medium")
            selected_error_categories = getattr(state, "selected_error_categories", {})
            selected_specific_errors = getattr(state, "selected_specific_errors", [])
            
            # Reset state for a fresh generation
            state.evaluation_attempts = 0
            state.evaluation_result = None
            state.code_generation_feedback = None

            # Set domain if not already set
            if not hasattr(state, "domain") or not state.domain:
                domains = [
                    "user_management", "file_processing", "data_validation", 
                    "calculation", "inventory_system", "notification_service",
                    "logging", "banking", "e-commerce", "student_management"
                ]
                state.domain = random.choice(domains)
                logger.debug(f"Selected domain: {state.domain}")
            
            # Determine error selection mode
            using_specific_errors = len(selected_specific_errors) > 0
            
            if using_specific_errors:
                if not selected_specific_errors:
                    state.error = t("no_specific_errors_selected")
                    return state
                       
                logger.debug(f"Using specific errors mode with {len(selected_specific_errors)} errors")
                selected_errors = selected_specific_errors
                original_error_count = len(selected_errors)
            else:
                if not selected_error_categories or not selected_error_categories.get("java_errors", []):
                    state.error = t("no_categories")
                    return state
                
                # Get errors based on difficulty
                error_count_start = int(getattr(state, "error_count_start", 1))
                error_count_end = int(getattr(state, "error_count_end", 2))
                required_error_count = random.randint(error_count_start, error_count_end)
            
                selected_errors, _ = self.error_repository.get_errors_for_llm(
                    selected_categories=selected_error_categories,
                    count=required_error_count,
                    difficulty=difficulty_level
                )

                original_error_count = len(selected_errors)
           
            logger.debug(f"Final error count for generation: {len(selected_errors)}")
            
            # Generate code with selected errors
            response = self.code_generator._generate_with_llm(
                code_length=code_length,
                difficulty_level=difficulty_level,
                selected_errors=selected_errors,
                domain=getattr(state, "domain", "")
            )

            # Extract both annotated and clean versions
            annotated_code, clean_code = extract_both_code_versions(response)

            # Create code snippet object
            from state_schema import CodeSnippet
            code_snippet = CodeSnippet(
                code=annotated_code,
                clean_code=clean_code,
                raw_errors={
                    "java_errors": selected_errors
                },
                expected_error_count=original_error_count
            )                   
            
            # Update state
            state.original_error_count = original_error_count
            state.code_snippet = code_snippet
            state.current_step = "evaluate"
            
            return state
                    
        except Exception as e:           
            logger.error(f"Error generating code: {str(e)}", exc_info=True)
            state.error = f"Error generating Java code: {str(e)}"
            return state

    def regenerate_code_node(self, state: WorkflowState) -> WorkflowState:
        """Regenerate code based on evaluation feedback."""
        try:
            logger.debug(f"Starting code regeneration (Attempt {getattr(state, 'evaluation_attempts', 0)})")
            
            # Use the code generation feedback to generate improved code
            feedback_prompt = getattr(state, "code_generation_feedback", None)
            
            if hasattr(self.code_generator, 'llm') and self.code_generator.llm:
                # Generate the code
                response = self.code_generator.llm.invoke(feedback_prompt)
                
                # Log the regeneration
                metadata = {
                    "attempt": getattr(state, "evaluation_attempts", 0),
                    "max_attempts": getattr(state, "max_evaluation_attempts", 3)
                }
                self.llm_logger.log_code_regeneration(feedback_prompt, response, metadata)
                
                # Process the response
                annotated_code, clean_code = extract_both_code_versions(response)                
                
                # Get requested errors from state
                requested_errors = self._extract_requested_errors(state)
                
                # Create updated code snippet
                from state_schema import CodeSnippet
                state.code_snippet = CodeSnippet(
                    code=annotated_code,
                    clean_code=clean_code,
                    raw_errors={
                        "java_errors": requested_errors
                    }
                )
                
                # Move to evaluation step again
                state.current_step = "evaluate"
                logger.debug(f"Code regenerated successfully")
                
                return state
            else:
                # Fallback to standard generation
                logger.warning("No LLM available for regeneration. Falling back to standard generation.")
                return self.generate_code_node(state)
            
        except Exception as e:                 
            logger.error(f"Error regenerating code: {str(e)}", exc_info=True)
            state.error = f"Error regenerating code: {str(e)}"
            return state
        
    def evaluate_code_node(self, state: WorkflowState) -> WorkflowState:
        """Evaluate generated code to ensure it contains requested errors - FIXED with proper termination."""
        try:
            logger.debug("Starting code evaluation node")
            
            # Validate code snippet
            if not hasattr(state, 'code_snippet') or state.code_snippet is None:
                state.error = t("no_code_snippet_evaluation")
                return state
                    
            # Get the code with annotations
            code = state.code_snippet.code
            
            # Get requested errors from state
            requested_errors = self._extract_requested_errors(state)
            
            # Get original error count
            original_error_count = getattr(state, "original_error_count", len(requested_errors))
            if original_error_count == 0:
                original_error_count = len(requested_errors)
                state.original_error_count = original_error_count
                
            logger.debug(f"Evaluating code for {original_error_count} expected errors")
            
            # Evaluate the code
            raw_evaluation_result = self.code_evaluation.evaluate_code(code, requested_errors)
            
            # Process evaluation result
            if not isinstance(raw_evaluation_result, dict):
                logger.error(f"Expected dict for evaluation_result, got {type(raw_evaluation_result)}")
                evaluation_result = {
                    "found_errors": [],
                    "missing_errors": [f"{error.get('type', '').upper()} - {error.get('name', '')}" 
                                    for error in requested_errors],
                    "valid": False,
                    "feedback": f"Error in evaluation. Please ensure code contains all {original_error_count} requested errors.",
                    "original_error_count": original_error_count
                }
            else:
                evaluation_result = raw_evaluation_result
                evaluation_result["original_error_count"] = original_error_count

                # Set validity based on missing errors
                missing_errors = evaluation_result.get('missing_errors', [])
                evaluation_result['valid'] = len(missing_errors) == 0
                
                logger.debug(f"Code validation: valid={evaluation_result.get('valid', False)}, " +
                        f"missing={len(missing_errors)}")
                
            # Update state with evaluation results
            state.evaluation_result = evaluation_result
            state.evaluation_attempts += 1
            
            # Generate feedback for potential regeneration
            missing_count = len(evaluation_result.get('missing_errors', []))
            
            # FIXED: Improved decision logic with proper termination
            max_attempts = getattr(state, "max_evaluation_attempts", 3)
            
            if missing_count > 0:
                logger.warning(f"Missing {missing_count} out of {original_error_count} requested errors")
                
                if hasattr(self.code_evaluation, 'generate_improved_prompt'):
                    feedback = self.code_evaluation.generate_improved_prompt(
                        code, requested_errors, evaluation_result
                    )
                else:
                    feedback = create_regeneration_prompt(
                        code=code,
                        domain=getattr(state, "domain", ""),
                        missing_errors=evaluation_result.get('missing_errors', []),
                        found_errors=evaluation_result.get('found_errors', []), 
                        requested_errors=requested_errors
                    )
                state.code_generation_feedback = feedback
            else:
                logger.debug(f"All {original_error_count} requested errors implemented correctly")
                state.code_generation_feedback = None
        
            # FIXED: Improved decision logic - always check max attempts first
            if state.evaluation_attempts >= max_attempts:
                # Force move to review if max attempts reached
                state.current_step = "review"
                logger.warning(f"Reached maximum evaluation attempts ({max_attempts}). Proceeding to review.")
            elif evaluation_result.get("valid", False):
                # Code is valid, proceed to review
                state.current_step = "review"
                logger.debug("All errors successfully implemented, proceeding to review")
            elif missing_count > 0:
                # Need to regenerate
                state.current_step = "regenerate"
                logger.debug(f"Found {missing_count} missing errors, proceeding to regeneration")
            else:
                # No missing errors but not marked as valid - proceed to review anyway
                state.current_step = "review"
                logger.debug("No missing errors found, proceeding to review")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in evaluation: {str(e)}", exc_info=True)
            state.error = f"Error evaluating code: {str(e)}"
            return state

    def regenerate_code_node(self, state: WorkflowState) -> WorkflowState:
        """Regenerate code based on evaluation feedback - FIXED with proper termination."""
        try:
            logger.debug(f"Starting code regeneration (Attempt {getattr(state, 'evaluation_attempts', 0)})")
            
            # FIXED: Check if we've reached max attempts before regenerating
            max_attempts = getattr(state, "max_evaluation_attempts", 3)
            if state.evaluation_attempts >= max_attempts:
                logger.warning(f"Max attempts ({max_attempts}) reached. Skipping regeneration and moving to review.")
                state.current_step = "review"
                return state
            
            # Use the code generation feedback to generate improved code
            feedback_prompt = getattr(state, "code_generation_feedback", None)
            
            if not feedback_prompt:
                logger.warning("No feedback prompt available for regeneration. Moving to review.")
                state.current_step = "review"
                return state
            
            if hasattr(self.code_generator, 'llm') and self.code_generator.llm:
                # Generate the code
                response = self.code_generator.llm.invoke(feedback_prompt)
                
                # Log the regeneration
                metadata = {
                    "attempt": getattr(state, "evaluation_attempts", 0),
                    "max_attempts": max_attempts
                }
                self.llm_logger.log_code_regeneration(feedback_prompt, response, metadata)
                
                # Process the response
                annotated_code, clean_code = extract_both_code_versions(response)                
                
                # Get requested errors from state
                requested_errors = self._extract_requested_errors(state)
                
                # Create updated code snippet
                from state_schema import CodeSnippet
                state.code_snippet = CodeSnippet(
                    code=annotated_code,
                    clean_code=clean_code,
                    raw_errors={
                        "java_errors": requested_errors
                    }
                )
                
                # FIXED: Always move to evaluation step after regeneration
                state.current_step = "evaluate"
                logger.debug(f"Code regenerated successfully, moving to evaluation")
                
                return state
            else:
                # No LLM available - move to review
                logger.warning("No LLM available for regeneration. Moving to review.")
                state.current_step = "review"
                return state
            
        except Exception as e:                 
            logger.error(f"Error regenerating code: {str(e)}", exc_info=True)
            state.error = f"Error regenerating code: {str(e)}"
            return state

    def analyze_review_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze student review and provide feedback - FIXED with proper iteration handling."""
        try:
            # Validate review history
            if not state.review_history:
                state.error = t("no_review_submitted")
                return state
                    
            latest_review = state.review_history[-1]
            student_review = latest_review.student_review
            
            # Validate code snippet
            if not state.code_snippet:
                state.error = t("no_code_snippet_available")
                return state
                    
            code_snippet = state.code_snippet.code
            raw_errors = state.code_snippet.raw_errors
            
            
            known_problems = []
            original_error_count = getattr(state, "original_error_count", 0)

            if isinstance(raw_errors, dict):
                for error_type, errors in raw_errors.items():
                    for error in errors:
                        if isinstance(error, dict):
                            error_name = error.get('error_name', error.get('name', ''))
                            category = error.get('category', error.get('type', ''))
                            description = error.get('description', '')
                            known_problems.append(f"{category} - {error_name}: {description}")
            
            # Get the student response evaluator
            evaluator = getattr(self, "evaluator", None)
            if not evaluator:
                state.error = t("student_evaluator_not_initialized")
                return state
            
            # Evaluate the review
            analysis = evaluator.evaluate_review(
                code_snippet=code_snippet,
                known_problems=known_problems,
                student_review=student_review
            )

            # Update analysis with original error count
            if original_error_count > 0:
                identified_count = analysis.get('identified_count', 0)
                
                analysis["total_problems"] = original_error_count
                analysis["original_error_count"] = original_error_count
                
                # Calculate percentage
                percentage = (identified_count / original_error_count) * 100
                analysis["identified_percentage"] = percentage
                analysis["accuracy_percentage"] = percentage
                
                logger.debug(f"Updated review analysis: {identified_count}/{original_error_count} ({percentage:.1f}%)")
                
                # Mark review as sufficient if all errors are found
                if identified_count == original_error_count:
                    analysis["review_sufficient"] = True
                    state.review_sufficient = True
                    logger.debug("All errors found! Marking review as sufficient.")

            # Update the review with analysis
            latest_review.analysis = analysis
            
            # FIXED: Proper iteration handling
            max_iterations = getattr(state, "max_iterations", 3)
            
            # Generate targeted guidance if needed
            if not state.review_sufficient and state.current_iteration < max_iterations:
                targeted_guidance = evaluator.generate_targeted_guidance(
                    code_snippet=code_snippet,
                    known_problems=known_problems,
                    student_review=student_review,
                    review_analysis=analysis,
                    iteration_count=state.current_iteration,
                    max_iterations=max_iterations
                )               
                latest_review.targeted_guidance = targeted_guidance              
            
            # FIXED: Increment iteration count AFTER processing
            state.current_iteration += 1
            
            # FIXED: Set current step to analyze
            state.current_step = "analyze"
            
            return state
        
        except Exception as e:
            logger.error(f"Error analyzing review: {str(e)}", exc_info=True)
            state.error = f"Error analyzing review: {str(e)}"
            return state

    def generate_summary_node(self, state: WorkflowState) -> WorkflowState:
        """Generate final summary node - marks the completion of the workflow."""
        try:
            logger.debug("Generating final summary for workflow completion")
            
            # Mark the workflow as completed
            state.current_step = "complete"
            
            # Generate final summary if needed
            if not hasattr(state, 'final_summary') or not state.final_summary:
                if state.review_history:
                    latest_review = state.review_history[-1]
                    analysis = latest_review.analysis
                    
                    identified_count = analysis.get('identified_count', 0)
                    original_error_count = getattr(state, 'original_error_count', 0)
                    
                    if original_error_count > 0:
                        percentage = (identified_count / original_error_count) * 100
                        state.final_summary = f"Review completed: {identified_count}/{original_error_count} errors identified ({percentage:.1f}%)"
                    else:
                        state.final_summary = f"Review completed: {identified_count} errors identified"
                else:
                    state.final_summary = "Review workflow completed"
            
            logger.debug("Summary generation completed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}", exc_info=True)
            state.error = f"Error generating summary: {str(e)}"
            return state

    def _extract_requested_errors(self, state: WorkflowState) -> List[Dict[str, Any]]:
        """Extract requested errors from the state."""
        requested_errors = []
        
        if not hasattr(state, 'code_snippet') or state.code_snippet is None:
            logger.warning("No code snippet in state for extracting requested errors")
            return requested_errors
        
        if hasattr(state, 'code_snippet') and hasattr(state.code_snippet, "raw_errors"):
            raw_errors = state.code_snippet.raw_errors           
            
            if not isinstance(raw_errors, dict):
                logger.warning(f"Expected dict for raw_errors, got {type(raw_errors)}")
                return requested_errors
            
            if "java_errors" in raw_errors:
                errors = raw_errors.get("java_errors", [])
                if not isinstance(errors, list):
                    logger.warning(f"Expected list for java_errors, got {type(errors)}")
                    return requested_errors
                
                for error in errors:
                    if not isinstance(error, dict):
                        logger.warning(f"Expected dict for error, got {type(error)}")
                        continue
                    requested_errors.append(error)
        
        elif hasattr(state, 'selected_specific_errors') and state.selected_specific_errors:
            if isinstance(state.selected_specific_errors, list):
                for error in state.selected_specific_errors:
                    if isinstance(error, dict):
                        requested_errors.append(error)
        
        logger.debug(f"Extracted {len(requested_errors)} requested errors")
        return requested_errors