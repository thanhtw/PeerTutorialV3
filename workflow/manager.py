"""
Simplified Workflow Manager for Java Peer Review Training System.

This module provides a central manager class that integrates
all components of the workflow system using LangGraph execution.
FIXED: Enhanced state management and submit button processing support.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from langgraph.graph import StateGraph
from state_schema import WorkflowState, ReviewAttempt

from data.database_error_repository import DatabaseErrorRepository

from core.code_generator import CodeGenerator
from core.student_response_evaluator import StudentResponseEvaluator
from core.code_evaluation import CodeEvaluationAgent

from workflow.node import WorkflowNodes
from workflow.conditions import WorkflowConditions
from workflow.builder import GraphBuilder

from utils.llm_logger import LLMInteractionLogger
from utils.language_utils import t
import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)

class WorkflowManager:
    """
    Enhanced manager class for the Java Code Review workflow system.
    FIXED: Better state management and submit button processing support.
    """
    def __init__(self, llm_manager):
        """
        Initialize the workflow manager with the LLM manager.
        
        Args:
            llm_manager: Manager for LLM models
        """
        self.llm_manager = llm_manager
        self.llm_logger = LLMInteractionLogger()
        
        # Initialize repositories
        self.error_repository = DatabaseErrorRepository()
        
        # Initialize domain objects
        self._initialize_domain_objects()
        
        # Create workflow nodes and conditions
        self.workflow_nodes = self._create_workflow_nodes()
        self.conditions = WorkflowConditions()
        
        # Build and compile the workflow graph
        self.workflow = self._build_workflow_graph()
        self._compiled_workflow = None
        
        logger.debug("WorkflowManager initialized successfully")
    
    def _initialize_domain_objects(self) -> None:
        """Initialize domain objects with appropriate LLMs."""
        logger.debug("Initializing domain objects")
        
        # Initialize models for different functions
        generative_model = self._initialize_model_for_role("GENERATIVE")
        review_model = self._initialize_model_for_role("REVIEW")
        summary_model = self._initialize_model_for_role("SUMMARY")
        
        # Initialize domain objects with models
        self.code_generator = CodeGenerator(generative_model, self.llm_logger)
        self.code_evaluation = CodeEvaluationAgent(review_model, self.llm_logger)
        self.evaluator = StudentResponseEvaluator(review_model, llm_logger=self.llm_logger)
        
        # Store feedback models for generating final feedback
        self.summary_model = summary_model
        
        logger.debug("Domain objects initialization completed")

    def _initialize_model_for_role(self, role: str):
        """Initialize an LLM for a specific role."""
        try:
            logger.debug(f"Attempting to initialize {role} model")
            
            model = self.llm_manager.initialize_model_from_env(f"{role}_MODEL", f"{role}_TEMPERATURE")
            
            if model:
                logger.debug(f"Successfully initialized {role} model")
                return model
            else:
                logger.warning(f"Failed to initialize {role} model")
                return None
                
        except Exception as e:
            logger.error(f"Exception while initializing {role} model: {str(e)}")
            return None
    
    def _create_workflow_nodes(self) -> WorkflowNodes:
        """Create workflow nodes with initialized domain objects."""
        logger.debug("Creating workflow nodes")
        nodes = WorkflowNodes(
            self.code_generator,
            self.code_evaluation,
            self.error_repository,
            self.llm_logger
        )
        
        # Attach evaluator to nodes
        nodes.evaluator = self.evaluator
        
        return nodes
    
    def _build_workflow_graph(self) -> StateGraph:
        """Build the workflow graph using the graph builder."""
        logger.debug("Building workflow graph")
        self.graph_builder = GraphBuilder(self.workflow_nodes)
        return self.graph_builder.build_graph()
    
    def _safe_get_state_value(self, state, key: str, default=None):
        """
        Safely get a value from a state object, handling both dict-like and attribute access.
        FIXED: Enhanced error handling and type checking.
        
        Args:
            state: State object (could be WorkflowState, dict, or AddableValuesDict)
            key: Key to access
            default: Default value if key not found
            
        Returns:
            Value from state or default
        """
        try:
            # Handle None state
            if state is None:
                logger.debug(f"State is None when accessing key '{key}'")
                return default
            
            # Try attribute access first (for WorkflowState objects)
            if hasattr(state, key):
                value = getattr(state, key)
                if value is not None:
                    return value
            
            # Try dictionary access (for dict-like objects)
            if hasattr(state, '__getitem__'):
                try:
                    value = state[key]
                    if value is not None:
                        return value
                except (KeyError, TypeError, AttributeError):
                    pass
            
            # Try get method (for dict-like objects)
            if hasattr(state, 'get'):
                value = state.get(key, default)
                if value is not None:
                    return value
            
            return default
            
        except Exception as e:
            logger.warning(f"Error accessing key '{key}' from state: {str(e)}")
            return default

    def _convert_state_to_workflow_state(self, state) -> WorkflowState:
        """
        Convert a state object (potentially AddableValuesDict) to a WorkflowState object.
        FIXED: Enhanced state conversion with better error handling and validation.
        
        Args:
            state: State object from LangGraph workflow
            
        Returns:
            WorkflowState object
        """
        try:
            # If it's already a WorkflowState, return as-is
            if isinstance(state, WorkflowState):
                logger.debug("State is already a WorkflowState")
                return state
            
            # If it's dict-like, extract all the fields
            state_dict = {}
            
            # Define all possible WorkflowState fields with their defaults
            workflow_state_fields = {
                'current_step': 'generate',
                'code_length': 'medium',
                'difficulty_level': 'medium', 
                'domain': None,
                'error_count_start': 1,
                'error_count_end': 2,
                'selected_error_categories': {},
                'selected_specific_errors': [],
                'code_snippet': None,
                'original_error_count': 0,
                'evaluation_attempts': 0,
                'max_evaluation_attempts': 3,
                'evaluation_result': None,
                'code_generation_feedback': None,
                'pending_review': None,
                'current_iteration': 1,
                'max_iterations': 3,
                'review_sufficient': False,
                'review_history': [],
                'comparison_report': None,
                'error': None,
                'final_summary': None
            }
            
            # Extract each field with proper defaults
            for field, default_value in workflow_state_fields.items():
                value = self._safe_get_state_value(state, field, default_value)
                
                # Special handling for certain fields
                if field == 'review_history':
                    # Ensure review_history is a proper list of ReviewAttempt objects
                    if isinstance(value, list):
                        processed_history = []
                        for item in value:
                            if isinstance(item, ReviewAttempt):
                                processed_history.append(item)
                            elif isinstance(item, dict):
                                # Convert dict to ReviewAttempt
                                try:
                                    review_attempt = ReviewAttempt(
                                        student_review=item.get('student_review', ''),
                                        iteration_number=item.get('iteration_number', 1),
                                        analysis=item.get('analysis', {}),
                                        targeted_guidance=item.get('targeted_guidance', None)
                                    )
                                    processed_history.append(review_attempt)
                                except Exception as review_error:
                                    logger.warning(f"Error converting review history item: {str(review_error)}")
                        state_dict[field] = processed_history
                    else:
                        state_dict[field] = default_value
                elif field == 'selected_error_categories':
                    # Ensure proper dict structure
                    if isinstance(value, dict):
                        state_dict[field] = value
                    else:
                        state_dict[field] = default_value
                elif field == 'selected_specific_errors':
                    # Ensure proper list structure
                    if isinstance(value, list):
                        state_dict[field] = value
                    else:
                        state_dict[field] = default_value
                else:
                    state_dict[field] = value
            
            # Create and return new WorkflowState
            logger.debug("Converting state to WorkflowState with extracted fields")
            return WorkflowState(**state_dict)
            
        except Exception as e:
            logger.error(f"Error converting state to WorkflowState: {str(e)}", exc_info=True)
            # Return a minimal WorkflowState with error
            return WorkflowState(error=f"State conversion failed: {str(e)}")

    def execute_code_generation_workflow(self, workflow_state: WorkflowState) -> WorkflowState:
        """
        Execute code generation workflow using LangGraph execution.
        FIXED: Enhanced error handling and state management.
        
        Args:
            workflow_state: Initial workflow state with parameters
            
        Returns:
            Updated workflow state after generation and evaluation
        """
        try:
            logger.debug("Starting enhanced code generation workflow")
            
            # Set initial step
            workflow_state.current_step = "generate"
            # Ensure max attempts are set to prevent infinite loops
            if not hasattr(workflow_state, 'max_evaluation_attempts') or int(workflow_state.max_evaluation_attempts) <= 0:
                workflow_state.max_evaluation_attempts = 3

            # Validate the state before processing
            if not self.validate_workflow_state(workflow_state)[0]:
                is_valid, error_msg = self.validate_workflow_state(workflow_state)
                workflow_state.error = error_msg
                return workflow_state
            
            # Get the compiled workflow
            compiled_workflow = self.get_compiled_workflow()
            
            # Execute the workflow with appropriate configuration
            config = {"recursion_limit": 50}  # Reasonable limit for code generation
            
            logger.debug("Invoking LangGraph workflow for code generation")
            raw_result = compiled_workflow.invoke(workflow_state, config)
            
            # Convert the result back to a WorkflowState object
            result = self._convert_state_to_workflow_state(raw_result)
            
            # Validate the result
            if hasattr(result, 'error') and result.error:
                logger.error(f"Code generation workflow returned error: {result.error}")
            else:
                logger.debug("Code generation workflow completed successfully")
                
            return result
            
        except Exception as e:
            logger.error(f"Error in code generation workflow: {str(e)}", exc_info=True)
            workflow_state.error = f"Code generation workflow failed: {str(e)}"
            return workflow_state

    def execute_review_workflow(self, workflow_state: WorkflowState, student_review: str) -> WorkflowState:
        """
        Execute review analysis workflow using LangGraph execution.
        FIXED: Enhanced submit processing and state management.
        
        Args:
            workflow_state: Current workflow state
            student_review: Student's review text
            
        Returns:
            Updated workflow state after review analysis
        """
        try:
            logger.debug("Starting enhanced review workflow")
            logger.debug(f"Processing review: {student_review[:100]}...")  # Log first 100 chars
            
            # FIXED: Enhanced review validation
            if not student_review or not student_review.strip():
                error_msg = "Student review cannot be empty"
                logger.error(error_msg)
                workflow_state.error = error_msg
                return workflow_state
            
            review_text = student_review.strip()
            if len(review_text) < 10:
                error_msg = "Student review too short (minimum 10 characters)"
                logger.error(error_msg)
                workflow_state.error = error_msg
                return workflow_state
            
            # Set the pending review and current step
            workflow_state.pending_review = review_text
            workflow_state.current_step = "review"
            
            # Ensure max iterations are set
            if not hasattr(workflow_state, 'max_iterations') or int(workflow_state.max_iterations) <= 0:
                workflow_state.max_iterations = 3
                
            # Validate current state
            current_iteration = getattr(workflow_state, 'current_iteration', 1)
            max_iterations = getattr(workflow_state, 'max_iterations', 3)
            
            if current_iteration > max_iterations:
                error_msg = f"Current iteration ({current_iteration}) exceeds max iterations ({max_iterations})"
                logger.warning(error_msg)
                workflow_state.error = error_msg
                return workflow_state
            
            # Validate workflow state
            if not self.conditions.validate_state_for_review(workflow_state):
                error_msg = "Workflow state not ready for review processing"
                logger.error(error_msg)
                workflow_state.error = error_msg
                return workflow_state
            
            # Get the compiled workflow
            compiled_workflow = self.get_compiled_workflow()
            
            # FIXED: Execute the workflow with proper configuration
            config = {"recursion_limit": 30}  # Reasonable limit for review processing
            
            logger.debug("Invoking LangGraph workflow for review processing")
            raw_result = compiled_workflow.invoke(workflow_state, config)
            
            # Convert the result back to a WorkflowState object
            result = self._convert_state_to_workflow_state(raw_result)
            
            # FIXED: Enhanced result validation
            if hasattr(result, 'error') and result.error:
                logger.error(f"Review workflow returned error: {result.error}")
            else:
                # Verify that the review was actually processed
                review_history = getattr(result, 'review_history', [])
                if review_history and len(review_history) > 0:
                    logger.debug(f"Review workflow completed successfully. History has {len(review_history)} entries.")
                else:
                    logger.warning("Review workflow completed but no review history found")
                    
                # Clear pending review if processing was successful
                if hasattr(result, 'pending_review'):
                    result.pending_review = None
            
            return result
            
        except Exception as e:
            logger.error(f"Error in review workflow: {str(e)}", exc_info=True)
            workflow_state.error = f"Review workflow failed: {str(e)}"
            return workflow_state

    def execute_full_workflow(self, workflow_state: WorkflowState) -> WorkflowState:
        """
        Execute the complete workflow using LangGraph execution.
        FIXED: Enhanced workflow execution with better error handling.
        
        Args:
            workflow_state: Initial workflow state
            
        Returns:
            Final workflow state after complete execution
        """
        try:
            logger.debug("Executing enhanced full workflow")
            
            # Set initial step
            workflow_state.current_step = "generate"
            
            # Ensure all limits are set
            if not hasattr(workflow_state, 'max_evaluation_attempts') or int(workflow_state.max_evaluation_attempts) <= 0:
                workflow_state.max_evaluation_attempts = 3
            if not hasattr(workflow_state, 'max_iterations') or int(workflow_state.max_iterations) <= 0:
                workflow_state.max_iterations = 3
            
            # Validate the initial state
            is_valid, error_msg = self.validate_workflow_state(workflow_state)
            if not is_valid:
                workflow_state.error = error_msg
                return workflow_state
            
            # Get the compiled workflow
            compiled_workflow = self.get_compiled_workflow()
            
            # Execute the workflow with increased recursion limit for full workflow
            config = {"recursion_limit": 100}  # Higher limit for full workflow
            
            logger.debug("Invoking LangGraph workflow for full execution")
            raw_result = compiled_workflow.invoke(workflow_state, config)
            
            # Convert the result back to a WorkflowState object
            result = self._convert_state_to_workflow_state(raw_result)
            
            # Validate completion
            if hasattr(result, 'error') and result.error:
                logger.error(f"Full workflow returned error: {result.error}")
            else:
                logger.debug("Full workflow completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing full workflow: {str(e)}", exc_info=True)
            workflow_state.error = f"Full workflow execution failed: {str(e)}"
            return workflow_state

    def get_compiled_workflow(self):
        """
        Get the compiled workflow with enhanced error handling.
        """
        if self._compiled_workflow is None:
            try:
                logger.debug("Compiling LangGraph workflow")
                self._compiled_workflow = self.workflow.compile()
                logger.debug("LangGraph workflow compiled successfully")
            except Exception as e:
                logger.error(f"Error compiling workflow: {str(e)}")
                raise
        
        return self._compiled_workflow

    def get_all_error_categories(self) -> Dict[str, List[str]]:
        """Get all available error categories."""
        try:
            return self.error_repository.get_all_categories()
        except Exception as e:
            logger.error(f"Error getting error categories: {str(e)}")
            return {}
    
    def validate_workflow_state(self, state: WorkflowState) -> Tuple[bool, str]:
        """
        Validate that the workflow state is ready for execution.
        FIXED: Enhanced validation with better error messages.
        """
        try:
            # Check required parameters
            if not hasattr(state, 'code_length') or not state.code_length:
                return False, "Code length parameter is required"
            
            if not hasattr(state, 'difficulty_level') or not state.difficulty_level:
                return False, "Difficulty level parameter is required"
            
            # Validate code_length values
            valid_lengths = ["short", "medium", "long"]
            if state.code_length not in valid_lengths:
                return False, f"Invalid code length. Must be one of: {valid_lengths}"
            
            # Validate difficulty_level values  
            valid_difficulties = ["easy", "medium", "hard"]
            if state.difficulty_level not in valid_difficulties:
                return False, f"Invalid difficulty level. Must be one of: {valid_difficulties}"
            
            # Check error selection
            has_categories = (hasattr(state, 'selected_error_categories') and 
                            state.selected_error_categories and
                            state.selected_error_categories.get("java_errors", []))
            
            has_specific_errors = (hasattr(state, 'selected_specific_errors') and 
                                 state.selected_specific_errors)
            
            if not has_categories and not has_specific_errors:
                return False, "Either error categories or specific errors must be selected"
            
            # Validate error counts
            if hasattr(state, 'error_count_start') and hasattr(state, 'error_count_end'):
                if int(state.error_count_start) <= 0 or int(state.error_count_end) <= 0:
                    return False, "Error counts must be positive integers"
                if int(state.error_count_start) > int(state.error_count_end):
                    return False, "Error count start cannot be greater than error count end"
            
            # Validate iteration settings
            if hasattr(state, 'max_iterations') and int(state.max_iterations) <= 0:
                return False, "Max iterations must be a positive integer"
                
            if hasattr(state, 'max_evaluation_attempts') and int(state.max_evaluation_attempts)  <= 0:
                return False, "Max evaluation attempts must be a positive integer"
            
            logger.debug("Enhanced workflow state validation passed")
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating workflow state: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def get_workflow_status(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Get the current status of the workflow with enhanced information.
        FIXED: Better status reporting for debugging submit issues.
        """
        try:
            # Basic status information
            status = {
                "current_step": getattr(state, 'current_step', 'unknown'),
                "has_code": hasattr(state, 'code_snippet') and state.code_snippet is not None,
                "evaluation_attempts": getattr(state, 'evaluation_attempts', 0),
                "max_evaluation_attempts": getattr(state, 'max_evaluation_attempts', 3),
                "current_iteration": getattr(state, 'current_iteration', 1),
                "max_iterations": getattr(state, 'max_iterations', 3),
                "review_sufficient": getattr(state, 'review_sufficient', False),
                "has_error": hasattr(state, 'error') and state.error is not None,
                "error_message": getattr(state, 'error', None),
                "has_comparison_report": hasattr(state, 'comparison_report') and state.comparison_report is not None,
                "has_pending_review": hasattr(state, 'pending_review') and bool(getattr(state, 'pending_review', None))
            }
            
            # Add evaluation status if available
            if hasattr(state, 'evaluation_result') and state.evaluation_result:
                eval_result = state.evaluation_result
                status.update({
                    "evaluation_valid": eval_result.get("valid", False),
                    "found_errors_count": len(eval_result.get("found_errors", [])),
                    "missing_errors_count": len(eval_result.get("missing_errors", []))
                })
            
            # Add review status if available
            if hasattr(state, 'review_history') and state.review_history:
                review_history = state.review_history
                status["review_attempts"] = len(review_history)
                
                # Get latest review analysis
                if len(review_history) > 0:
                    latest_review = review_history[-1]
                    if hasattr(latest_review, 'analysis') and latest_review.analysis:
                        analysis = latest_review.analysis
                        status.update({
                            "identified_count": analysis.get(t("identified_count"), 0),
                            "total_problems": analysis.get(t("total_problems"), 0),
                            "identified_percentage": analysis.get(t("identified_percentage"), 0),
                            "latest_review_text": getattr(latest_review, 'student_review', '')[:100] + "..." if len(getattr(latest_review, 'student_review', '')) > 100 else getattr(latest_review, 'student_review', '')
                        })
            
            # Add workflow progress information
            progress_info = self.conditions.get_review_progress_info(state)
            status["progress_info"] = progress_info
            
            # Add validation status
            is_valid, validation_message = self.validate_workflow_state(state)
            status.update({
                "state_valid": is_valid,
                "validation_message": validation_message
            })
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {
                "error": f"Status retrieval failed: {str(e)}",
                "current_step": "unknown",
                "has_code": False,
                "state_valid": False
            }
    
    def debug_state_info(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Get detailed debug information about the current state.
        Useful for troubleshooting submit button issues.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with detailed debug information
        """
        try:
            debug_info = {
                "state_type": type(state).__name__,
                "has_pending_review": hasattr(state, 'pending_review'),
                "pending_review_value": getattr(state, 'pending_review', None),
                "pending_review_length": len(getattr(state, 'pending_review', '') or ''),
                "current_iteration": getattr(state, 'current_iteration', None),
                "max_iterations": getattr(state, 'max_iterations', None),
                "review_history_count": len(getattr(state, 'review_history', [])),
                "review_sufficient": getattr(state, 'review_sufficient', None),
                "current_step": getattr(state, 'current_step', None),
                "has_code_snippet": hasattr(state, 'code_snippet') and state.code_snippet is not None,
                "has_evaluation_result": hasattr(state, 'evaluation_result') and state.evaluation_result is not None,
                "workflow_error": getattr(state, 'error', None)
            }
            
            # Add review history details
            if hasattr(state, 'review_history') and state.review_history:
                review_details = []
                for i, review in enumerate(state.review_history):
                    review_info = {
                        "index": i,
                        "iteration_number": getattr(review, 'iteration_number', None),
                        "has_analysis": hasattr(review, 'analysis') and review.analysis is not None,
                        "review_length": len(getattr(review, 'student_review', '') or ''),
                        "has_guidance": hasattr(review, 'targeted_guidance') and review.targeted_guidance is not None
                    }
                    if hasattr(review, 'analysis') and review.analysis:
                        analysis = review.analysis
                        review_info.update({
                            "identified_count": analysis.get(t("identified_count"), 0),
                            "total_problems": analysis.get(t("total_problems"), 0)
                        })
                    review_details.append(review_info)
                debug_info["review_history_details"] = review_details
            
            return debug_info
            
        except Exception as e:
            logger.error(f"Error getting debug state info: {str(e)}")
            return {"error": f"Debug info failed: {str(e)}"}