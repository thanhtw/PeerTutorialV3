"""
Enhanced Workflow Manager for Java Peer Review Training System.

FIXED: Removed _sanitize_workflow_state method and rely on Pydantic validation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from langgraph.graph import StateGraph
from state_schema import WorkflowState, ReviewAttempt, CodeSnippet

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
    FIXED: Simplified state management by removing manual sanitization.
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
        Safely get a value from AddableValuesDict or other state objects.
        COMPREHENSIVE: Try all possible access methods to avoid data loss.
        """
        try:
            if state is None:
                return default
            
            # Method 1: Dictionary-style access (for AddableValuesDict)
            if hasattr(state, '__getitem__'):
                try:
                    value = state[key]
                    if value is not None:
                        return value
                except (KeyError, TypeError, AttributeError):
                    pass
            
            # Method 2: Attribute access (for objects)
            if hasattr(state, key):
                try:
                    value = getattr(state, key)
                    if value is not None:
                        return value
                except AttributeError:
                    pass
            
            # Method 3: get() method (for dict-like objects)
            if hasattr(state, 'get'):
                try:
                    value = state.get(key)
                    if value is not None:
                        return value
                except (TypeError, AttributeError):
                    pass
            
            # Method 4: Check if it's in __dict__ (for some objects)
            if hasattr(state, '__dict__') and key in state.__dict__:
                try:
                    value = state.__dict__[key]
                    if value is not None:
                        return value
                except (KeyError, AttributeError):
                    pass
            
            return default
            
        except Exception as e:
            logger.warning(f"Error accessing key '{key}' from state {type(state)}: {str(e)}")
            return default

    def _create_clean_code_snippet(self, value) -> Optional[CodeSnippet]:
        """
        Create a clean CodeSnippet instance, preserving all data.
        """
        try:
            if value is None:
                return None
            
            # Extract data based on input type
            if isinstance(value, CodeSnippet):
                return value  # Already clean
            elif isinstance(value, dict):
                code = value.get('code', '')
                clean_code = value.get('clean_code', '')
                raw_errors = value.get('raw_errors', {})
                expected_error_count = value.get('expected_error_count', 0)
            elif hasattr(value, 'code'):
                code = getattr(value, 'code', '')
                clean_code = getattr(value, 'clean_code', '')
                raw_errors = getattr(value, 'raw_errors', {})
                expected_error_count = getattr(value, 'expected_error_count', 0)
            else:
                logger.warning(f"Cannot convert {type(value)} to CodeSnippet")
                return None
            
            # Ensure proper types
            clean_code_val = str(code) if code else ''
            clean_clean_code_val = str(clean_code) if clean_code else clean_code_val
            clean_expected_count = int(expected_error_count) if isinstance(expected_error_count, (int, float, str)) and str(expected_error_count).replace('.', '').isdigit() else 0
            
            # Preserve raw_errors structure
            clean_raw_errors = {}
            if isinstance(raw_errors, dict):
                clean_raw_errors = raw_errors.copy()  # Preserve structure
            
            return CodeSnippet(
                code=clean_code_val,
                clean_code=clean_clean_code_val,
                raw_errors=clean_raw_errors,
                expected_error_count=clean_expected_count
            )
            
        except Exception as e:
            logger.error(f"Error creating CodeSnippet: {str(e)}")
            return None

    def _create_clean_review_history(self, value) -> List[ReviewAttempt]:
        """
        Create clean review history, preserving all review data.
        """
        try:
            if not value:
                return []
            
            if not isinstance(value, list):
                logger.warning(f"Expected list for review_history, got {type(value)}")
                return []
            
            clean_history = []
            for item in value:
                try:
                    if isinstance(item, ReviewAttempt):
                        clean_history.append(item)  # Already clean
                        continue
                    
                    # Extract data from dict or object
                    if isinstance(item, dict):
                        student_review = item.get('student_review', '')
                        iteration_number = item.get('iteration_number', 1)
                        analysis = item.get('analysis', {})
                        targeted_guidance = item.get('targeted_guidance', None)
                    elif hasattr(item, 'student_review'):
                        student_review = getattr(item, 'student_review', '')
                        iteration_number = getattr(item, 'iteration_number', 1)
                        analysis = getattr(item, 'analysis', {})
                        targeted_guidance = getattr(item, 'targeted_guidance', None)
                    else:
                        logger.warning(f"Cannot convert review item: {type(item)}")
                        continue
                    
                    # Ensure proper types
                    clean_student_review = str(student_review) if student_review else ''
                    clean_iteration_number = int(iteration_number) if str(iteration_number).isdigit() else 1
                    clean_analysis = analysis if isinstance(analysis, dict) else {}
                    clean_targeted_guidance = str(targeted_guidance) if targeted_guidance else None
                    
                    # Create ReviewAttempt
                    review_attempt = ReviewAttempt(
                        student_review=clean_student_review,
                        iteration_number=clean_iteration_number,
                        analysis=clean_analysis,
                        targeted_guidance=clean_targeted_guidance
                    )
                    clean_history.append(review_attempt)
                    
                except Exception as item_error:
                    logger.warning(f"Error processing review item: {str(item_error)}")
                    continue
            
            return clean_history
            
        except Exception as e:
            logger.error(f"Error creating review history: {str(e)}")
            return []

    def _convert_state_to_workflow_state(self, state) -> WorkflowState:
        """
        Convert AddableValuesDict to WorkflowState without losing data.
        COMPREHENSIVE: Extract all fields systematically to prevent data loss.
        """
        try:
            # If already WorkflowState, return as-is
            if isinstance(state, WorkflowState):
                logger.debug("State is already WorkflowState")
                return state
            
            logger.debug(f"Converting {type(state)} to WorkflowState")
            
            # Extract all fields systematically
            state_dict = {}
            
            # Define all WorkflowState fields (from state_schema.py)
            all_fields = {
                # Basic workflow control
                'current_step': 'generate',
                'code_length': 'medium',
                'difficulty_level': 'medium',
                'domain': None,
                'error_count_start': 1,
                'error_count_end': 2,
                
                # Error selection
                'selected_error_categories': {},
                'selected_specific_errors': [],
                
                # Code generation state
                'code_snippet': None,
                'original_error_count': 0,
                
                # Code evaluation state
                'evaluation_attempts': 0,
                'max_evaluation_attempts': 3,
                'evaluation_result': None,
                'code_generation_feedback': None,
                
                # Review state
                'pending_review': None,
                'current_iteration': 1,
                'max_iterations': 3,
                'review_sufficient': False,
                'review_history': [],
                
                # Final output
                'comparison_report': None,
                'error': None,
                'final_summary': None
            }
            
            # Extract each field systematically
            for field_name, default_value in all_fields.items():
                extracted_value = self._safe_get_state_value(state, field_name, default_value)
                
                # Handle special objects that need conversion
                if field_name == 'code_snippet':
                    state_dict[field_name] = self._create_clean_code_snippet(extracted_value)
                elif field_name == 'review_history':
                    state_dict[field_name] = self._create_clean_review_history(extracted_value)
                elif field_name in ['selected_error_categories', 'evaluation_result']:
                    # Preserve dict structure
                    if isinstance(extracted_value, dict):
                        state_dict[field_name] = extracted_value
                    else:
                        state_dict[field_name] = default_value
                elif field_name == 'selected_specific_errors':
                    # Preserve list structure
                    if isinstance(extracted_value, list):
                        state_dict[field_name] = extracted_value
                    else:
                        state_dict[field_name] = default_value
                elif field_name in ['error_count_start', 'error_count_end', 'original_error_count', 
                                  'evaluation_attempts', 'max_evaluation_attempts', 'current_iteration', 'max_iterations']:
                    # Ensure integers
                    try:
                        state_dict[field_name] = int(extracted_value) if extracted_value is not None else default_value
                    except (ValueError, TypeError):
                        state_dict[field_name] = default_value
                elif field_name == 'review_sufficient':
                    # Ensure boolean
                    try:
                        state_dict[field_name] = bool(extracted_value) if extracted_value is not None else default_value
                    except (ValueError, TypeError):
                        state_dict[field_name] = default_value
                else:
                    # String fields and others
                    state_dict[field_name] = extracted_value
            
            # Check for any additional fields in the source state that we might have missed
            try:
                if hasattr(state, 'keys'):
                    source_keys = set(state.keys())
                elif hasattr(state, '__dict__'):
                    source_keys = set(state.__dict__.keys())
                else:
                    source_keys = set()
                
                known_keys = set(all_fields.keys())
                missing_keys = source_keys - known_keys
                
                if missing_keys:
                    logger.debug(f"Found additional fields in source state: {missing_keys}")
                    # Add any missing fields to preserve data
                    for key in missing_keys:
                        if key not in state_dict:
                            additional_value = self._safe_get_state_value(state, key)
                            if additional_value is not None:
                                logger.debug(f"Preserving additional field: {key}")
                                # Note: These won't be part of WorkflowState schema, but we log them
                                
            except Exception as e:
                logger.debug(f"Could not check for additional fields: {str(e)}")
            
            # Create WorkflowState with all extracted data
            try:
                new_state = WorkflowState(**state_dict)
                logger.debug(f"Successfully converted to WorkflowState with {len(state_dict)} fields")
                return new_state
                
            except Exception as validation_error:
                logger.error(f"Pydantic validation failed: {str(validation_error)}")
                logger.error(f"Failed state_dict keys: {list(state_dict.keys())}")
                
                # Return minimal valid state with error info
                return WorkflowState(
                    error=f"State conversion validation failed: {str(validation_error)}"
                )
            
        except Exception as e:
            logger.error(f"Error converting {type(state)} to WorkflowState: {str(e)}", exc_info=True)
            return WorkflowState(error=f"State conversion failed: {str(e)}")

    def execute_code_generation_workflow(self, workflow_state: WorkflowState) -> WorkflowState:
        """
        Execute code generation workflow using LangGraph execution.
        FIXED: Removed manual sanitization, rely on Pydantic validation.
        """
        try:
            logger.debug("Starting code generation workflow")
            
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
            
            # Convert result (LangGraph returns AddableValuesDict, not WorkflowState)
            if isinstance(raw_result, WorkflowState):
                result = raw_result
                logger.debug("LangGraph returned WorkflowState directly")
            else:
                logger.debug(f"LangGraph returned {type(raw_result)}, converting to WorkflowState")
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
        FIXED: Removed manual sanitization, rely on Pydantic validation.
        """
        try:
            logger.debug("Starting review workflow")
            logger.debug(f"Processing review: {student_review[:100]}...")  # Log first 100 chars
            
            # Enhanced review validation
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
            logger.debug(f"Pending review set: {workflow_state.pending_review[:100]}...")  # Log first 100 chars
            
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
            
            # Execute the workflow with proper configuration
            config = {"recursion_limit": 30}  # Reasonable limit for review processing
            
            logger.debug("Invoking LangGraph workflow for review processing")
            raw_result = compiled_workflow.invoke(workflow_state, config)
            
            # Convert result (LangGraph returns AddableValuesDict, not WorkflowState)
            if isinstance(raw_result, WorkflowState):
                result = raw_result
                logger.debug("LangGraph returned WorkflowState directly")
            else:
                logger.debug(f"LangGraph returned {type(raw_result)}, converting to WorkflowState")
                result = self._convert_state_to_workflow_state(raw_result)
            
            # Enhanced result validation
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
        FIXED: Removed manual sanitization, rely on Pydantic validation.
        """
        try:
            logger.debug("Executing full workflow")
            
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
            
            # Convert result (LangGraph returns AddableValuesDict, not WorkflowState)
            if isinstance(raw_result, WorkflowState):
                result = raw_result
                logger.debug("LangGraph returned WorkflowState directly")
            else:
                logger.debug(f"LangGraph returned {type(raw_result)}, converting to WorkflowState")
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
            
            logger.debug("Workflow state validation passed")
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating workflow state: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def get_workflow_status(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Get the current status of the workflow with enhanced information.
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