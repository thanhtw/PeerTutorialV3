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
        
        # DISABLED: Build workflow graph - using simplified execution instead
        # self.workflow = self._build_workflow_graph()
        self.workflow = None
        
        # DISABLED: Store the compiled workflow for execution
        # self._compiled_workflow = None
        self._compiled_workflow = None
        
        logger.debug("WorkflowManager initialized with simplified execution mode")
    
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
    
    def execute_code_generation_workflow(self, workflow_state: WorkflowState) -> WorkflowState:
        """
        Execute code generation workflow - COMPLETELY REWRITTEN to avoid recursion issues.
        
        Args:
            workflow_state: Initial workflow state with parameters
            
        Returns:
            Updated workflow state after generation and evaluation
        """
        try:
            logger.debug("Starting SIMPLIFIED code generation workflow")
            
            # STEP 1: Generate Code
            logger.debug("Step 1: Generating code")
            workflow_state = self.workflow_nodes.generate_code_node(workflow_state)
            if workflow_state.error:
                return workflow_state
            
            # STEP 2-4: Evaluation Loop with Hard Limits
            max_attempts = getattr(workflow_state, "max_evaluation_attempts", 3)
            
            for attempt in range(max_attempts):
                logger.debug(f"Step {attempt + 2}: Evaluating code (attempt {attempt + 1}/{max_attempts})")
                
                # Evaluate code
                workflow_state = self.workflow_nodes.evaluate_code_node(workflow_state)
                if workflow_state.error:
                    return workflow_state
                
                evaluation_result = getattr(workflow_state, "evaluation_result", {})
                is_valid = evaluation_result.get("valid", False)
                missing_errors = evaluation_result.get("missing_errors", [])
                
                logger.debug(f"Evaluation result: valid={is_valid}, missing_errors={len(missing_errors)}")
                
                # If valid or last attempt, break
                if is_valid or attempt >= max_attempts - 1:
                    logger.debug(f"Breaking evaluation loop: valid={is_valid}, last_attempt={attempt >= max_attempts - 1}")
                    break
                
                # Regenerate if not valid and not last attempt
                if not is_valid and len(missing_errors) > 0:
                    logger.debug(f"Step {attempt + 2}.5: Regenerating code")
                    workflow_state = self.workflow_nodes.regenerate_code_node(workflow_state)
                    if workflow_state.error:
                        return workflow_state
            
            # STEP FINAL: Set to review state
            workflow_state.current_step = "review"
            logger.debug("Code generation workflow completed successfully")
            
            return workflow_state
            
        except Exception as e:
            logger.error(f"Error in simplified code generation workflow: {str(e)}")
            workflow_state.error = f"Code generation workflow failed: {str(e)}"
            return workflow_state

    def execute_review_workflow(self, workflow_state: WorkflowState, student_review: str) -> WorkflowState:
        """
        Execute review analysis workflow - COMPLETELY REWRITTEN to avoid recursion issues.
        
        Args:
            workflow_state: Current workflow state
            student_review: Student's review text
            
        Returns:
            Updated workflow state after review analysis
        """
        try:
            logger.debug("Starting SIMPLIFIED review workflow")
            
            # Set pending review
            workflow_state.pending_review = student_review
            
            # STEP 1: Process the review
            logger.debug("Step 1: Processing review")
            workflow_state = self.workflow_nodes.review_code_node(workflow_state)
            if workflow_state.error:
                return workflow_state
            
            # STEP 2: Analyze the review
            logger.debug("Step 2: Analyzing review")
            workflow_state = self.workflow_nodes.analyze_review_node(workflow_state)
            if workflow_state.error:
                return workflow_state
            
            # STEP 3: Check if we should continue or complete
            max_iterations = getattr(workflow_state, "max_iterations", 3)
            current_iteration = getattr(workflow_state, "current_iteration", 1)
            review_sufficient = getattr(workflow_state, "review_sufficient", False)
            
            # Check if all errors were found
            if workflow_state.review_history:
                latest_review = workflow_state.review_history[-1]
                if hasattr(latest_review, "analysis"):
                    analysis = latest_review.analysis
                    identified_count = analysis.get("identified_count", 0)
                    total_problems = analysis.get("total_problems", 0)
                    if identified_count == total_problems and total_problems > 0:
                        review_sufficient = True
                        workflow_state.review_sufficient = True
            
            logger.debug(f"Review decision: iteration={current_iteration}/{max_iterations}, sufficient={review_sufficient}")
            
            # If review is sufficient or max iterations reached, generate comparison report
            if review_sufficient or current_iteration > max_iterations:
                logger.debug("Step 3: Generating comparison report")
                workflow_state = self.workflow_nodes.comparison_report_node(workflow_state)
                if workflow_state.error:
                    return workflow_state
                
                logger.debug("Step 4: Generating summary")
                workflow_state = self.workflow_nodes.generate_summary_node(workflow_state)
            
            logger.debug("Review workflow completed successfully")
            return workflow_state
            
        except Exception as e:
            logger.error(f"Error in simplified review workflow: {str(e)}")
            workflow_state.error = f"Review workflow failed: {str(e)}"
            return workflow_state

    def execute_full_workflow(self, workflow_state: WorkflowState) -> WorkflowState:
        """
        Execute the complete workflow - SIMPLIFIED VERSION.
        
        Args:
            workflow_state: Initial workflow state
            
        Returns:
            Final workflow state after complete execution
        """
        try:
            logger.debug("Executing SIMPLIFIED full workflow")
            
            # Step 1: Code Generation
            workflow_state = self.execute_code_generation_workflow(workflow_state)
            if workflow_state.error:
                return workflow_state
            
            # The full workflow stops here - review submission happens separately
            logger.debug("Full workflow (code generation phase) completed")
            return workflow_state
            
        except Exception as e:
            logger.error(f"Error executing simplified full workflow: {str(e)}")
            workflow_state.error = f"Full workflow execution failed: {str(e)}"
            return workflow_state

    def get_compiled_workflow(self):
        """Get the compiled workflow - COMPLETELY DISABLED for simplified execution."""
        if self._compiled_workflow is None:
            logger.debug("LangGraph compilation disabled - using simplified execution")
            # Return a dummy object that won't be used
            class DummyWorkflow:
                def invoke(self, state, config=None):
                    raise NotImplementedError("Use simplified execution methods instead")
            
            self._compiled_workflow = DummyWorkflow()
        
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