"""
Simplified Workflow Nodes for Java Peer Review Training System.

This module contains the node implementations for the LangGraph workflow,
with separated review nodes for clearer flow.
FIXED: Enhanced review processing and better state management for submit button processing.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional

from state_schema import WorkflowState, CodeSnippet, ReviewAttempt
from utils.code_utils import extract_both_code_versions, create_regeneration_prompt, get_error_count_from_state
from utils.language_utils import t
import random

# Configure logging
logger = logging.getLogger(__name__)

class WorkflowNodes:
    """
    Node implementations for the Java Code Review workflow.
    
    This class contains all node handlers with separated review nodes
    for clearer phase separation and enhanced submit processing.
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
    
    # =================================================================
    # PHASE 1: CODE GENERATION AND EVALUATION NODES
    # =================================================================
    
    def generate_code_node(self, state: WorkflowState) -> WorkflowState:
        """Generate Java code with errors based on selected parameters."""
        try:
            logger.debug("PHASE 1: Starting code generation")
            
            # Get parameters from state
            code_length = getattr(state, "code_length", "medium")
            difficulty_level = getattr(state, "difficulty_level", "medium")
            selected_error_categories = getattr(state, "selected_error_categories", {})
            selected_specific_errors = getattr(state, "selected_specific_errors", [])
            
            # Reset generation state for fresh start
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
            
            # Determine error selection mode and get errors
            if selected_specific_errors:
                logger.debug(f"Using specific errors mode with {len(selected_specific_errors)} errors")
                selected_errors = selected_specific_errors
                original_error_count = len(selected_errors)
            else:
                if not selected_error_categories or not selected_error_categories.get("java_errors", []):
                    state.error = t("no_categories_selected")
                    return state
                
                # Get errors based on difficulty and count range
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
           
            # Validate code extraction
            if not annotated_code.strip() or not clean_code.strip():
                logger.error("Code generation failed: No code extracted from LLM response")
                state.error = "Failed to generate code. Please try again."
                return state

            # Create code snippet object
            code_snippet = CodeSnippet(
                code=annotated_code,
                clean_code=clean_code,
                raw_errors={"java_errors": selected_errors},
                expected_error_count=original_error_count
            )                  
            
            # Update state and proceed to evaluation
            state.original_error_count = original_error_count
            state.code_snippet = code_snippet
            state.current_step = "evaluate"
            
            logger.debug("PHASE 1: Code generation completed successfully")
            return state
                    
        except Exception as e:           
            logger.error(f"Error generating code: {str(e)}", exc_info=True)
            state.error = f"Error generating Java code: {str(e)}"
            return state

    def evaluate_code_node(self, state: WorkflowState) -> WorkflowState:
        """
        Evaluate generated code to check if it contains the required errors.
        """
        try:
            logger.debug("PHASE 1: Starting code evaluation")
            
            # Validate code snippet exists
            if not hasattr(state, 'code_snippet') or state.code_snippet is None:
                state.error = "No code snippet available for evaluation"
                return state
                    
            # Get the code with annotations
            code = state.code_snippet.code
            
            # Get requested errors from state
            requested_errors = self._extract_requested_errors(state)
            
            # Ensure we have errors to evaluate against
            if not requested_errors:
                logger.warning("No requested errors found, marking evaluation as valid")
                state.evaluation_result = {
                    t("found_errors"): [],
                    t("missing_errors"): [],
                    t("valid"): True,
                    t("feedback"): "No errors to evaluate against"
                }
                return state
            
            # Set up evaluation tracking
            original_error_count = getattr(state, "original_error_count", len(requested_errors))
            if original_error_count == 0:
                original_error_count = len(requested_errors)
                state.original_error_count = original_error_count
            
            # Ensure max_evaluation_attempts is set
            if not hasattr(state, 'max_evaluation_attempts'):
                state.max_evaluation_attempts = 3
                
            logger.debug(f"Evaluating code for {original_error_count} expected errors")
            
            # Initialize and increment attempts
            if not hasattr(state, 'evaluation_attempts'):
                state.evaluation_attempts = 0
            state.evaluation_attempts += 1
            
            logger.debug(f"Evaluation attempt {state.evaluation_attempts}/{state.max_evaluation_attempts}")
            
            # Perform the evaluation
            try:
                raw_evaluation_result = self.code_evaluation.evaluate_code(code, requested_errors)
            except Exception as eval_error:
                logger.error(f"Code evaluation failed: {str(eval_error)}")
                raw_evaluation_result = {
                    t("found_errors"): [],
                    t("missing_errors"): [f"EVALUATION_ERROR - {str(eval_error)}"],
                    t("valid"): False,
                    t("feedback"): f"Evaluation failed: {str(eval_error)}"
                }
            
            # Process and validate evaluation result
            evaluation_result = self._process_evaluation_result(
                raw_evaluation_result, requested_errors, original_error_count
            )
            
            # Update state with evaluation results
            state.evaluation_result = evaluation_result
            
            # Generate feedback for potential regeneration if needed
            missing_count = len(evaluation_result.get(t('missing_errors'), []))
            
            if missing_count > 0 and state.evaluation_attempts < state.max_evaluation_attempts:
                logger.debug(f"Missing {missing_count} out of {original_error_count} requested errors")
                
                try:
                    if hasattr(self.code_evaluation, 'generate_improved_prompt'):
                        feedback = self.code_evaluation.generate_improved_prompt(
                            code, requested_errors, evaluation_result
                        )
                    else:
                        feedback = create_regeneration_prompt(
                            code=code,
                            domain=getattr(state, "domain", ""),
                            missing_errors=evaluation_result.get(t('missing_errors'), []),
                            found_errors=evaluation_result.get(t('found_errors'), []), 
                            requested_errors=requested_errors
                        )
                    state.code_generation_feedback = feedback
                except Exception as feedback_error:
                    logger.error(f"Failed to generate feedback: {str(feedback_error)}")
                    state.code_generation_feedback = None
            else:
                if missing_count > 0:
                    logger.warning(f"Still missing {missing_count} errors but reached max attempts")
                else:
                    logger.debug(f"All {original_error_count} requested errors implemented correctly")
                state.code_generation_feedback = None

            logger.debug(f"PHASE 1: Evaluation complete. Valid: {evaluation_result.get(t('valid'), False)}")
            return state
            
        except Exception as e:
            logger.error(f"Error in evaluation: {str(e)}", exc_info=True)
            state.error = f"Error evaluating code: {str(e)}"
            return state

    def regenerate_code_node(self, state: WorkflowState) -> WorkflowState:
        """Regenerate code based on evaluation feedback."""
        try:
            current_attempt = getattr(state, 'evaluation_attempts', 0)
            max_attempts = getattr(state, "max_evaluation_attempts", 3)
            
            logger.debug(f"PHASE 1: Starting code regeneration (attempt {current_attempt}/{max_attempts})")
            
            # Check max attempts (should not happen due to conditions, but safety check)
            if current_attempt >= max_attempts:
                logger.warning(f"Max attempts ({max_attempts}) reached. Skipping regeneration.")
                return state
            
            # Use the code generation feedback to generate improved code
            feedback_prompt = getattr(state, "code_generation_feedback", None)
            
            if not feedback_prompt:
                logger.warning("No feedback prompt available for regeneration.")
                return state
            
            if hasattr(self.code_generator, 'llm') and self.code_generator.llm:
                try:
                    # Generate improved code
                    response = self.code_generator.llm.invoke(feedback_prompt)
                    
                    # Log the regeneration
                    metadata = {
                        "attempt_after_evaluation": current_attempt,
                        "max_attempts": max_attempts
                    }
                    self.llm_logger.log_code_regeneration(feedback_prompt, response, metadata)
                    
                    # Process the response
                    annotated_code, clean_code = extract_both_code_versions(response)                
                    
                    # Get requested errors from state
                    requested_errors = self._extract_requested_errors(state)
                    
                    # Create updated code snippet
                    state.code_snippet = CodeSnippet(
                        code=annotated_code,
                        clean_code=clean_code,
                        raw_errors={"java_errors": requested_errors}
                    )
                    
                    logger.debug(f"PHASE 1: Code regenerated successfully for attempt {current_attempt + 1}")
                    
                except Exception as regen_error:
                    logger.error(f"Failed to regenerate code: {str(regen_error)}")
                    
                return state
            else:
                logger.warning("No LLM available for regeneration.")
                return state
            
        except Exception as e:                 
            logger.error(f"Error regenerating code: {str(e)}", exc_info=True)
            logger.warning("Regeneration failed, continuing with existing code")
            return state

    # =================================================================
    # PHASE 2: REVIEW PHASE NODE (ENHANCED FOR SUBMIT PROCESSING)
    # =================================================================
    
    def review_code_node(self, state: WorkflowState) -> WorkflowState:
        """
        PHASE 2: Enhanced review node that handles both initial setup and review continuation.
        FIXED: Better state management and submit processing integration.
        """
        try:
            logger.debug("PHASE 2: Review code node - Enhanced processing")
            
            # Get current state information
            current_iteration = getattr(state, "current_iteration", 1)
            review_history = getattr(state, "review_history", [])
            pending_review = getattr(state, "pending_review", None)
            
            logger.debug(f"PHASE 2: Current iteration: {current_iteration}, "
                        f"Review history count: {len(review_history)}, "
                        f"Pending review: {'Yes' if pending_review else 'No'}")
            
            # SCENARIO 1: Initial review setup (no review history yet)
            if not review_history:
                logger.debug("PHASE 2: Setting up initial review phase")
                
                # Validate code snippet exists
                if not hasattr(state, 'code_snippet') or state.code_snippet is None:
                    state.error = "No code snippet available for review"
                    return state
                
                # Initialize review state with proper defaults
                if not hasattr(state, 'max_iterations') or state.max_iterations <= 0:
                    state.max_iterations = 3
                if not hasattr(state, 'review_sufficient'):
                    state.review_sufficient = False
                if not hasattr(state, 'review_history'):
                    state.review_history = []
                if not hasattr(state, 'current_iteration') or state.current_iteration <= 0:
                    state.current_iteration = 1
                
                # Clear any pending review from previous sessions
                state.pending_review = None
                state.current_step = "review"
                
                logger.debug(f"PHASE 2: Ready for review iteration {state.current_iteration}/{state.max_iterations}")
                return state
            
            # SCENARIO 2: Processing submitted review (pending review exists)
            elif pending_review and pending_review.strip():
                logger.debug(f"PHASE 2: Processing submitted review for iteration {current_iteration}")
                
                # Validate the pending review
                review_text = pending_review.strip()
                if len(review_text) < 10:
                    logger.warning("Submitted review is too short")
                    state.error = "Review is too short. Please provide a more detailed review."
                    return state
                
                # FIXED: Create review attempt with proper initialization
                try:
                    review_attempt = ReviewAttempt(
                        student_review=review_text,
                        iteration_number=current_iteration,
                        analysis={},  # Will be filled by analyze_review_node
                        targeted_guidance=None  # Will be filled by analyze_review_node
                    )
                    
                    # Add to history
                    state.review_history.append(review_attempt)
                    
                    logger.debug(f"PHASE 2: Review attempt created and added to history (iteration {current_iteration})")
                    logger.debug(f"PHASE 2: Review history now has {len(state.review_history)} entries")
                    
                    # IMPORTANT: Keep pending_review set so the conditional edge can detect it
                    # It will be cleared in the analyze_review_node
                    
                except Exception as review_error:
                    logger.error(f"Error creating review attempt: {str(review_error)}")
                    state.error = f"Failed to process review: {str(review_error)}"
                    return state
                
                return state
            
            # SCENARIO 3: Continuation after analysis (no pending review, but has history)
            else:
                logger.debug("PHASE 2: Review continuation or waiting state")
                
                # Check if we should continue or if we're done
                if hasattr(state, 'review_sufficient') and state.review_sufficient:
                    logger.debug("PHASE 2: Review marked as sufficient")
                    return state
                
                # Check if we've reached max iterations
                if current_iteration > getattr(state, 'max_iterations', 3):
                    logger.debug("PHASE 2: Max iterations reached")
                    return state
                
                # Waiting for next review submission
                state.current_step = "review"
                logger.debug("PHASE 2: Waiting for next student review submission...")
                return state
            
        except Exception as e:
            logger.error(f"Error in review_code_node: {str(e)}", exc_info=True)
            state.error = f"Error in review phase: {str(e)}"
            return state
    
    def analyze_review_node(self, state: WorkflowState) -> WorkflowState:
        """
        PHASE 2: Enhanced analyze student review using the evaluator.
        FIXED: Better error handling and state management for submit processing.
        """
        try:
            logger.debug("PHASE 2: Starting enhanced review analysis")
            
            # FIXED: Clear the pending review FIRST to prevent infinite loops
            if hasattr(state, 'pending_review'):
                logger.debug("PHASE 2: Clearing pending review")
                state.pending_review = None
            
            # Validate review history
            if not hasattr(state, 'review_history') or not state.review_history:
                state.error = "No review submitted for analysis"
                logger.error("PHASE 2: No review history found for analysis")
                return state
                    
            latest_review = state.review_history[-1]
            student_review = latest_review.student_review
            current_iteration = getattr(state, 'current_iteration', 1)
            
            logger.debug(f"PHASE 2: Analyzing review for iteration {current_iteration}")
            logger.debug(f"PHASE 2: Review text length: {len(student_review)} characters")
            
            # Validate code snippet
            if not hasattr(state, 'code_snippet') or not state.code_snippet:
                state.error = "No code snippet available for review analysis"
                logger.error("PHASE 2: No code snippet found for analysis")
                return state
                    
            code_snippet = state.code_snippet.code
            raw_errors = state.code_snippet.raw_errors
            
            # Extract known problems from raw errors
            known_problems = []
            original_error_count = getattr(state, "original_error_count", 0)

            try:
                if isinstance(raw_errors, dict):
                    for error_type, errors in raw_errors.items():
                        for error in errors:
                            if isinstance(error, dict):
                                error_name = error.get('error_name', error.get('name', ''))
                                category = error.get('category', error.get('type', ''))
                                description = error.get('description', '')
                                known_problems.append(f"{category} - {error_name}: {description}")
                                
                logger.debug(f"PHASE 2: Extracted {len(known_problems)} known problems")
                                
            except Exception as extraction_error:
                logger.error(f"Error extracting known problems: {str(extraction_error)}")
                # Continue with empty known_problems - better than failing completely
            
            # Get the student response evaluator
            evaluator = getattr(self, "evaluator", None)
            if not evaluator:
                state.error = "Student evaluator not initialized"
                logger.error("PHASE 2: Student evaluator not available")
                return state
            
            # Evaluate the review
            try:
                logger.debug("PHASE 2: Evaluating student review with evaluator")
                analysis = evaluator.evaluate_review(
                    code_snippet=code_snippet,
                    known_problems=known_problems,
                    student_review=student_review
                )
                
                if not analysis:
                    raise ValueError("Evaluator returned empty analysis")
                    
                logger.debug(f"PHASE 2: Review analysis completed: {analysis}")
                
            except Exception as eval_error:
                logger.error(f"Review evaluation failed: {str(eval_error)}", exc_info=True)
                # Create fallback analysis
                analysis = {
                    t("identified_count"): 0,
                    t("total_problems"): original_error_count,
                    t("identified_percentage"): 0,
                    t("review_sufficient"): False,
                    t("identified_problems"): [],
                    t("missed_problems"): known_problems,
                    "error": f"Evaluation failed: {str(eval_error)}"
                }

            # FIXED: Enhanced analysis processing with better error handling
            try:
                if original_error_count > 0:
                    identified_count = analysis.get(t('identified_count'), 0)
                    
                    # Ensure identified_count is not greater than total problems
                    if identified_count > original_error_count:
                        logger.warning(f"Identified count ({identified_count}) exceeds total problems ({original_error_count}), capping")
                        identified_count = original_error_count
                        analysis[t("identified_count")] = identified_count
                    
                    analysis[t("total_problems")] = original_error_count
                    analysis[t("original_error_count")] = original_error_count
                    
                    # Calculate percentage
                    percentage = (identified_count / original_error_count) * 100 if original_error_count > 0 else 0
                    analysis[t("identified_percentage")] = percentage
                    analysis[t("accuracy_percentage")] = percentage
                    
                    logger.debug(f"PHASE 2: Updated analysis metrics: {identified_count}/{original_error_count} ({percentage:.1f}%)")
                    
                    # Mark review as sufficient if all errors are found
                    if identified_count >= original_error_count:
                        analysis[t("review_sufficient")] = True
                        state.review_sufficient = True
                        logger.debug("PHASE 2: All errors found! Marking review as sufficient.")
                else:
                    logger.warning("PHASE 2: Original error count is 0, cannot calculate meaningful metrics")
                    
            except Exception as processing_error:
                logger.error(f"Error processing analysis: {str(processing_error)}")
                # Continue with basic analysis
            
            # Update the review with analysis
            latest_review.analysis = analysis
            
            # FIXED: Enhanced iteration management
            try:
                # Only increment iteration if we're going to continue reviewing
                max_iterations = getattr(state, "max_iterations", 3)
                review_sufficient = getattr(state, 'review_sufficient', False)
                
                if not review_sufficient and current_iteration < max_iterations:
                    state.current_iteration = current_iteration + 1
                    logger.debug(f"PHASE 2: Incremented iteration to {state.current_iteration}")
                else:
                    logger.debug(f"PHASE 2: Not incrementing iteration (sufficient: {review_sufficient}, iteration: {current_iteration}/{max_iterations})")
                
            except Exception as iteration_error:
                logger.error(f"Error managing iteration: {str(iteration_error)}")
            
            # Generate targeted guidance if needed
            try:
                if not state.review_sufficient and state.current_iteration <= max_iterations:
                    logger.debug("PHASE 2: Generating targeted guidance")
                    
                    targeted_guidance = evaluator.generate_targeted_guidance(
                        code_snippet=code_snippet,
                        known_problems=known_problems,
                        student_review=student_review,
                        review_analysis=analysis,
                        iteration_count=current_iteration,  # Use current iteration for guidance context
                        max_iterations=max_iterations
                    )
                    
                    if targeted_guidance:
                        latest_review.targeted_guidance = targeted_guidance
                        logger.debug("PHASE 2: Targeted guidance generated successfully")
                    else:
                        logger.warning("PHASE 2: No targeted guidance generated")
                else:
                    logger.debug("PHASE 2: Skipping guidance generation (review sufficient or max iterations reached)")
                    
            except Exception as guidance_error:
                logger.error(f"Failed to generate guidance: {str(guidance_error)}")
                latest_review.targeted_guidance = None
            
            logger.debug(f"PHASE 2: Review analysis completed successfully for iteration {current_iteration}")
            return state
        
        except Exception as e:
            logger.error(f"Error analyzing review: {str(e)}", exc_info=True)
            state.error = f"Error analyzing review: {str(e)}"
            return state

    # =================================================================
    # PHASE 3: FINAL REPORT GENERATION
    # =================================================================

    def generate_comparison_report_node(self, state: WorkflowState) -> WorkflowState:
        """
        PHASE 3: Generate comparison report node.
        """
        try:
            logger.debug("PHASE 3: Generating comparison report")
            
            # Check if we have review history
            if not hasattr(state, 'review_history') or not state.review_history:
                logger.warning("No review history found")
                state.comparison_report = self._generate_fallback_comparison_report(state, None)
                state.current_step = "complete"
                return state
                    
            # Get latest review
            latest_review = state.review_history[-1]
            
            # Generate comparison report if not already generated
            if not hasattr(state, 'comparison_report') or not state.comparison_report:
                if hasattr(state, 'evaluation_result') and state.evaluation_result:
                    # Extract error information from evaluation results
                    found_errors = state.evaluation_result.get(t('found_errors'), [])
                    
                    # Convert review history to format expected by generate_comparison_report
                    converted_history = []
                    for review in state.review_history:
                        converted_history.append({
                            "iteration_number": review.iteration_number,
                            "student_comment": review.student_review,
                            "review_analysis": review.analysis,
                            "targeted_guidance": getattr(review, 'targeted_guidance', None)
                        })
                            
                    if hasattr(self, "evaluator") and self.evaluator:
                        try:
                            state.comparison_report = self.evaluator.generate_comparison_report(
                                found_errors,
                                latest_review.analysis,
                                converted_history
                            )
                            logger.debug("PHASE 3: Generated comparison report successfully")
                        except Exception as report_error:
                            logger.error(f"Failed to generate comparison report: {str(report_error)}")
                            state.comparison_report = self._generate_fallback_comparison_report(state, latest_review)
                    else:
                        # Fallback comparison report
                        state.comparison_report = self._generate_fallback_comparison_report(state, latest_review)
                else:
                    # No evaluation result available
                    state.comparison_report = self._generate_fallback_comparison_report(state, latest_review)
            
            # Update state to complete
            state.current_step = "complete"
            
            # Generate final summary
            if not hasattr(state, 'final_summary') or not state.final_summary:
                if hasattr(state, 'review_history') and state.review_history:
                    latest_review = state.review_history[-1]
                    if hasattr(latest_review, 'analysis') and latest_review.analysis:
                        analysis = latest_review.analysis
                        identified_count = analysis.get(t('identified_count'), 0)
                        original_error_count = getattr(state, 'original_error_count', 0)
                        
                        if original_error_count > 0:
                            percentage = (identified_count / original_error_count) * 100
                            state.final_summary = f"Review completed: {identified_count}/{original_error_count} errors identified ({percentage:.1f}%)"
                        else:
                            state.final_summary = f"Review completed: {identified_count} errors identified"
                    else:
                        state.final_summary = "Review workflow completed"
                else:
                    state.final_summary = "Workflow completed successfully"
            
            logger.debug("PHASE 3: Comparison report generation completed")
            return state
            
        except Exception as e:
            logger.error(f"Error generating comparison report: {str(e)}", exc_info=True)
            state.error = f"Error generating comparison report: {str(e)}"
            return state

    # =================================================================
    # HELPER METHODS
    # =================================================================

    def _generate_fallback_comparison_report(self, state: WorkflowState, latest_review) -> str:
        """Generate a basic comparison report as fallback."""
        try:
            if latest_review and hasattr(latest_review, 'analysis') and latest_review.analysis:
                analysis = latest_review.analysis
                identified_count = analysis.get(t('identified_count'), 0)
                total_problems = analysis.get(t('total_problems'), 0)
                accuracy = analysis.get(t('identified_percentage'), 0)
                
                report = f"""# {t('review_feedback')}

## {t('performance_summary')}
- {t('issues_identified')}: {identified_count}/{total_problems}
- {t('accuracy')}: {accuracy:.1f}%
- {t('review_attempts')}: {len(state.review_history) if hasattr(state, 'review_history') and state.review_history else 0}

## {t('completion_status')}
{"✅ " + t('all_issues_found') if identified_count == total_problems else "⚠️ " + t('some_issues_missed')}

{t('review_completed_successfully')}
"""
            else:
                report = f"""# {t('review_feedback')}

## {t('completion_status')}
{t('review_completed_successfully')}
"""
            
            return report
        except Exception as e:
            logger.error(f"Error generating fallback report: {str(e)}")
            return f"# {t('review_feedback')}\n\n{t('error_generating_report')}"

    def _process_evaluation_result(self, raw_result, requested_errors, original_error_count):
        """
        Process and validate evaluation result to ensure it's in the correct format.
        """
        try:
            if not isinstance(raw_result, dict):
                logger.error(f"Expected dict for evaluation_result, got {type(raw_result)}")
                evaluation_result = {
                    t("found_errors"): [],
                    t("missing_errors"): [f"{error.get('type', '').upper()} - {error.get('name', '')}" 
                                    for error in requested_errors],
                    t("valid"): False,
                    t("feedback"): f"Invalid evaluation result type: {type(raw_result)}",
                    t("original_error_count"): original_error_count
                }
            else:
                evaluation_result = raw_result.copy()
                evaluation_result[t("original_error_count")] = original_error_count

                # Ensure required fields exist
                if t("found_errors") not in evaluation_result:
                    evaluation_result[t("found_errors")] = []
                if t("missing_errors") not in evaluation_result:
                    evaluation_result[t("missing_errors")] = []
                
                # Ensure fields are lists
                if not isinstance(evaluation_result.get(t("found_errors")), list):
                    evaluation_result[t("found_errors")] = []
                if not isinstance(evaluation_result.get(t("missing_errors")), list):
                    evaluation_result[t("missing_errors")] = []
                
                # Set validity based on missing errors
                missing_errors = evaluation_result.get(t('missing_errors'), [])
                evaluation_result[t('valid')] = len(missing_errors) == 0
                
                logger.debug(f"Processed evaluation: found={len(evaluation_result.get(t('found_errors'), []))}, "
                            f"missing={len(missing_errors)}, valid={evaluation_result[t('valid')]}")
                
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error processing evaluation result: {str(e)}")
            # Return a safe fallback
            return {
                t("found_errors"): [],
                t("missing_errors"): [f"PROCESSING_ERROR - {str(e)}"],
                t("valid"): False,
                t("feedback"): f"Error processing evaluation: {str(e)}",
                t("original_error_count"): original_error_count
            }

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