"""
Workflow Manager for Java Peer Review Training System.

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
    Manager class for the Java Code Review workflow system.
    This class integrates all components and provides LangGraph execution.
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
        
        # Build workflow graph
        self.workflow = self._build_workflow_graph()
        
        # Store the compiled workflow for execution
        self._compiled_workflow = None
    
    def _initialize_domain_objects(self) -> None:
        """Initialize domain objects with appropriate LLMs."""
        logger.debug(t("initializing_domain_objects"))
        
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
        
        logger.debug(t("domain_objects_initialization_completed"))

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
    
    def get_compiled_workflow(self):
        """Get the compiled workflow for execution with proper recursion limit."""
        if self._compiled_workflow is None:
            logger.debug("Compiling workflow for execution")
            # FIXED: Add recursion limit and other safety configurations
            self._compiled_workflow = self.workflow.compile(
                checkpointer=None,  # No checkpointing needed for this use case
                debug=False
            )
        return self._compiled_workflow
    
    def execute_code_generation_workflow(self, workflow_state: WorkflowState) -> WorkflowState:
        """
        Execute code generation workflow using LangGraph - FIXED to prevent infinite loops.
        
        Args:
            workflow_state: Initial workflow state with parameters
            
        Returns:
            Updated workflow state after generation and evaluation
        """
        try:
            logger.debug("Starting LangGraph code generation workflow")
            
            # Set initial step
            workflow_state.current_step = "generate"
            
            # FIXED: Use direct LangGraph invoke with proper config instead of manual loops
            # Configure execution with recursion limit and max steps
            config = {
                "recursion_limit": 50,  # Increase recursion limit
                "max_steps": 20,       # Limit maximum steps to prevent infinite loops
            }
            
            # Get compiled workflow
            compiled_workflow = self.get_compiled_workflow()
            
            # Execute the workflow with safety limits
            logger.debug("Executing workflow with safety limits...")
            result = compiled_workflow.invoke(workflow_state, config=config)
            
            # Check if we reached a valid stopping point
            if result.current_step in ["review", "complete"] or result.error:
                logger.debug(f"Code generation workflow completed at step: {result.current_step}")
                return result
            else:
                # If we didn't reach a proper end state, force it to review
                logger.warning(f"Workflow stopped at unexpected step: {result.current_step}. Forcing to review state.")
                result.current_step = "review"
                return result
            
        except Exception as e:
            logger.error(f"Error in LangGraph code generation workflow: {str(e)}")
            workflow_state.error = f"Code generation workflow failed: {str(e)}"
            return workflow_state
    
    def execute_review_workflow(self, workflow_state: WorkflowState, student_review: str) -> WorkflowState:
        """
        Execute review analysis workflow using LangGraph - FIXED with proper termination.
        
        Args:
            workflow_state: Current workflow state
            student_review: Student's review text
            
        Returns:
            Updated workflow state after review analysis
        """
        try:
            logger.debug("Starting LangGraph review workflow")
            
            # Set pending review in state
            workflow_state.pending_review = student_review
            workflow_state.current_step = "review"
            
            # FIXED: Configure execution with proper limits
            config = {
                "recursion_limit": 30,
                "max_steps": 10,
            }
            
            # Get compiled workflow
            compiled_workflow = self.get_compiled_workflow()
            
            # Execute the review workflow
            result = compiled_workflow.invoke(workflow_state, config=config)
            
            logger.debug(f"Review workflow completed at step: {result.current_step}")
            return result
            
        except Exception as e:
            logger.error(f"Error in LangGraph review workflow: {str(e)}")
            workflow_state.error = f"Review workflow failed: {str(e)}"
            return workflow_state
    
    def execute_full_workflow(self, workflow_state: WorkflowState) -> WorkflowState:
        """
        Execute the complete workflow using LangGraph - FIXED with safety limits.
        
        Args:
            workflow_state: Initial workflow state
            
        Returns:
            Final workflow state after complete execution
        """
        try:
            logger.debug("Executing full workflow using LangGraph")
            
            # FIXED: Configure with safety limits
            config = {
                "recursion_limit": 100,  # Higher limit for full workflow
                "max_steps": 50,         # Maximum steps for safety
            }
            
            # Get compiled workflow
            compiled_workflow = self.get_compiled_workflow()
            
            # Execute the workflow
            result = compiled_workflow.invoke(workflow_state, config=config)
            
            logger.debug("Full workflow execution completed")
            return result
            
        except Exception as e:
            logger.error(f"Error executing full workflow: {str(e)}")
            workflow_state.error = f"Full workflow execution failed: {str(e)}"
            return workflow_state
    
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