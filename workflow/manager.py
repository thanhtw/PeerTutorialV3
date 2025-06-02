"""
Simplified Workflow Manager for Java Peer Review Training System.

This module provides a central manager class that integrates
all components of the workflow system using LangGraph execution.
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
    Simplified manager class for the Java Code Review workflow system.
    This class integrates all components and provides proper LangGraph execution.
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
        
        logger.info("WorkflowManager initialized successfully")
    
    def _initialize_domain_objects(self) -> None:
        """Initialize domain objects with appropriate LLMs."""
        logger.info("Initializing domain objects")
        
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
        
        logger.info("Domain objects initialization completed")

    def _initialize_model_for_role(self, role: str):
        """Initialize an LLM for a specific role."""
        try:
            logger.info(f"Attempting to initialize {role} model")
            
            model = self.llm_manager.initialize_model_from_env(f"{role}_MODEL", f"{role}_TEMPERATURE")
            
            if model:
                logger.info(f"Successfully initialized {role} model")
                return model
            else:
                logger.warning(f"Failed to initialize {role} model")
                return None
                
        except Exception as e:
            logger.error(f"Exception while initializing {role} model: {str(e)}")
            return None
    
    def _create_workflow_nodes(self) -> WorkflowNodes:
        """Create workflow nodes with initialized domain objects."""
        logger.info("Creating workflow nodes")
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
        logger.info("Building workflow graph")
        self.graph_builder = GraphBuilder(self.workflow_nodes)
        return self.graph_builder.build_graph()
    
    def _safe_get_state_value(self, state, key: str, default=None):
        """
        Safely get a value from a state object, handling both dict-like and attribute access.
        
        Args:
            state: State object (could be WorkflowState, dict, or AddableValuesDict)
            key: Key to access
            default: Default value if key not found
            
        Returns:
            Value from state or default
        """
        try:
            # Try attribute access first (for WorkflowState objects)
            if hasattr(state, key):
                return getattr(state, key)
            
            # Try dictionary access (for dict-like objects)
            if hasattr(state, '__getitem__'):
                try:
                    return state[key]
                except (KeyError, TypeError):
                    pass
            
            # Try get method (for dict-like objects)
            if hasattr(state, 'get'):
                return state.get(key, default)
            
            return default
            
        except Exception as e:
            logger.warning(f"Error accessing key '{key}' from state: {str(e)}")
            return default

    def _convert_state_to_workflow_state(self, state) -> WorkflowState:
        """
        Convert a state object (potentially AddableValuesDict) to a WorkflowState object.
        
        Args:
            state: State object from LangGraph workflow
            
        Returns:
            WorkflowState object
        """
        try:
            # If it's already a WorkflowState, return as-is
            if isinstance(state, WorkflowState):
                return state
            
            # If it's dict-like, extract all the fields
            state_dict = {}
            
            # Define all possible WorkflowState fields
            workflow_state_fields = [
                'current_step', 'code_length', 'difficulty_level', 'domain',
                'error_count_start', 'error_count_end', 'selected_error_categories',
                'selected_specific_errors', 'code_snippet', 'original_error_count',
                'evaluation_attempts', 'max_evaluation_attempts', 'evaluation_result',
                'code_generation_feedback', 'pending_review', 'current_iteration',
                'max_iterations', 'review_sufficient', 'review_history',
                'comparison_report', 'error', 'final_summary'
            ]
            
            # Extract each field
            for field in workflow_state_fields:
                value = self._safe_get_state_value(state, field)
                if value is not None:
                    state_dict[field] = value
            
            # Create and return new WorkflowState
            return WorkflowState(**state_dict)
            
        except Exception as e:
            logger.error(f"Error converting state to WorkflowState: {str(e)}")
            # Return a minimal WorkflowState with error
            return WorkflowState(error=f"State conversion failed: {str(e)}")

    def execute_code_generation_workflow(self, workflow_state: WorkflowState) -> WorkflowState:
        """
        Execute code generation workflow using LangGraph execution.
        
        Args:
            workflow_state: Initial workflow state with parameters
            
        Returns:
            Updated workflow state after generation and evaluation
        """
        try:
            logger.info("Starting code generation workflow")
            
            # Set initial step
            workflow_state.current_step = "generate"
            
            # Ensure max attempts are set to prevent infinite loops
            if not hasattr(workflow_state, 'max_evaluation_attempts'):
                workflow_state.max_evaluation_attempts = 3
            
            # Get the compiled workflow
            compiled_workflow = self.get_compiled_workflow()
            
            # Execute the workflow with increased recursion limit
            config = {"recursion_limit": 100}
            raw_result = compiled_workflow.invoke(workflow_state, config)
            
            # Convert the result back to a WorkflowState object
            result = self._convert_state_to_workflow_state(raw_result)
            
            logger.info("Code generation workflow completed")
            return result
            
        except Exception as e:
            logger.error(f"Error in code generation workflow: {str(e)}")
            workflow_state.error = f"Code generation workflow failed: {str(e)}"
            return workflow_state

    def execute_review_workflow(self, workflow_state: WorkflowState, student_review: str) -> WorkflowState:
        """
        Execute review analysis workflow using LangGraph execution.
        
        Args:
            workflow_state: Current workflow state
            student_review: Student's review text
            
        Returns:
            Updated workflow state after review analysis
        """
        try:
            logger.info("Starting review workflow")
            
            # Set the pending review and current step
            workflow_state.pending_review = student_review
            workflow_state.current_step = "review"
            
            # Ensure max iterations are set
            if not hasattr(workflow_state, 'max_iterations'):
                workflow_state.max_iterations = 3
            
            # Get the compiled workflow
            compiled_workflow = self.get_compiled_workflow()
            
            # Execute the workflow with increased recursion limit
            #config = {"recursion_limit": 500}
            raw_result = compiled_workflow.invoke(workflow_state)
            
            # Convert the result back to a WorkflowState object
            result = self._convert_state_to_workflow_state(raw_result)
            
            logger.info("Review workflow completed")
            return result
            
        except Exception as e:
            logger.error(f"Error in review workflow: {str(e)}")
            workflow_state.error = f"Review workflow failed: {str(e)}"
            return workflow_state

    def execute_full_workflow(self, workflow_state: WorkflowState) -> WorkflowState:
        """
        Execute the complete workflow using LangGraph execution.
        
        Args:
            workflow_state: Initial workflow state
            
        Returns:
            Final workflow state after complete execution
        """
        try:
            logger.info("Executing full workflow")
            
            # Set initial step
            workflow_state.current_step = "generate"
            
            # Ensure all limits are set
            if not hasattr(workflow_state, 'max_evaluation_attempts'):
                workflow_state.max_evaluation_attempts = 3
            if not hasattr(workflow_state, 'max_iterations'):
                workflow_state.max_iterations = 3
            
            # Get the compiled workflow
            compiled_workflow = self.get_compiled_workflow()
            
            # Execute the workflow with increased recursion limit
            #config = {"recursion_limit": 500}  # Higher limit for full workflow
            raw_result = compiled_workflow.invoke(workflow_state)
            
            # Convert the result back to a WorkflowState object
            result = self._convert_state_to_workflow_state(raw_result)
            
            logger.info("Full workflow completed")
            return result
            
        except Exception as e:
            logger.error(f"Error executing full workflow: {str(e)}")
            workflow_state.error = f"Full workflow execution failed: {str(e)}"
            return workflow_state

    def get_compiled_workflow(self):
        """
        Get the compiled workflow.
        """
        if self._compiled_workflow is None:
            logger.info("Compiling LangGraph workflow")
            self._compiled_workflow = self.workflow.compile()
            logger.info("LangGraph workflow compiled successfully")
        
        return self._compiled_workflow

    def get_all_error_categories(self) -> Dict[str, List[str]]:
        """Get all available error categories."""
        return self.error_repository.get_all_categories()
    
    def validate_workflow_state(self, state: WorkflowState) -> Tuple[bool, str]:
        """Validate that the workflow state is ready for execution."""
        try:
            # Check required parameters
            if not hasattr(state, 'code_length') or not state.code_length:
                return False, "Code length parameter is required"
            
            if not hasattr(state, 'difficulty_level') or not state.difficulty_level:
                return False, "Difficulty level parameter is required"
            
            # Check error selection
            has_categories = (hasattr(state, 'selected_error_categories') and 
                            state.selected_error_categories and
                            state.selected_error_categories.get("java_errors", []))
            
            has_specific_errors = (hasattr(state, 'selected_specific_errors') and 
                                 state.selected_specific_errors)
            
            if not has_categories and not has_specific_errors:
                return False, "Either error categories or specific errors must be selected"
            
            logger.debug("Workflow state validation passed")
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating workflow state: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def get_workflow_status(self, state: WorkflowState) -> Dict[str, Any]:
        """Get the current status of the workflow."""
        try:
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
                "has_comparison_report": hasattr(state, 'comparison_report') and state.comparison_report is not None
            }
            
            # Add evaluation status if available
            if hasattr(state, 'evaluation_result') and state.evaluation_result:
                status["evaluation_valid"] = state.evaluation_result.get("valid", False)
                status["found_errors_count"] = len(state.evaluation_result.get("found_errors", []))
                status["missing_errors_count"] = len(state.evaluation_result.get("missing_errors", []))
            
            # Add review status if available
            if hasattr(state, 'review_history') and state.review_history:
                status["review_attempts"] = len(state.review_history)
                latest_review = state.review_history[-1]
                if hasattr(latest_review, 'analysis') and latest_review.analysis:
                    status["identified_count"] = latest_review.analysis.get("identified_count", 0)
                    status["identified_percentage"] = latest_review.analysis.get("identified_percentage", 0)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {"error": f"Status retrieval failed: {str(e)}"}