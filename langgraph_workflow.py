"""
LangGraph Workflow for Java Peer Review Training System.

This module implements the code review workflow as a LangGraph graph
by leveraging the modular components from the workflow package.
Enhanced to use proper LangGraph execution instead of direct node calls.
"""

__all__ = ['JavaCodeReviewGraph']

import logging
from typing import Dict, List, Any, Optional

from state_schema import WorkflowState

# Import workflow components
from workflow.manager import WorkflowManager
from workflow.conditions import WorkflowConditions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class JavaCodeReviewGraph:
    """
    LangGraph implementation of the Java Code Review workflow.
    
    This class now properly uses the compiled LangGraph workflow
    instead of calling nodes directly.
    """
    
    def __init__(self, llm_manager=None):
        """
        Initialize the graph with domain components.
        
        Args:
            llm_manager: Optional LLMManager for managing language models
        """
        # Initialize the workflow manager with LLM manager
        self.llm_manager = llm_manager
        self.workflow_manager = WorkflowManager(llm_manager)
        
        # Get references to workflow components
        self.error_repository = self.workflow_manager.error_repository
        self.workflow_nodes = self.workflow_manager.workflow_nodes
        self.conditions = WorkflowConditions()
        
        # Get the compiled workflow
        self._compiled_workflow = self.workflow_manager.get_compiled_workflow()
    
    def execute_code_generation(self, state: WorkflowState) -> WorkflowState:
        """
        Execute code generation using the compiled LangGraph workflow.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state after code generation and evaluation
        """
        try:
            logger.debug("Executing code generation through compiled workflow")
            
            # Validate the workflow state before proceeding
            is_valid, error_message = self.workflow_manager.validate_workflow_state(state)
            if not is_valid:
                logger.error(f"Invalid workflow state: {error_message}")
                state.error = error_message
                return state
            
            # Set initial step
            state.current_step = "generate"
            
            # Execute the workflow until we reach the review step
            result = self._execute_until_step(state, target_step="review")
            
            # Log the workflow status
            status = self.workflow_manager.get_workflow_status(result)
            logger.debug(f"Code generation completed with status: {status}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in code generation workflow: {str(e)}")
            state.error = f"Code generation failed: {str(e)}"
            return state
    
    def submit_review(self, state: WorkflowState, student_review: str) -> WorkflowState:
        """
        Submit a student review using the compiled LangGraph workflow with safety limits.
        
        Args:
            state: Current workflow state
            student_review: The student's review text
            
        Returns:
            Updated workflow state with analysis
        """
        try:
            logger.debug(f"Submitting review through compiled workflow with safety limits")
            
            # FIXED: Use the workflow manager's improved execution method
            result = self.workflow_manager.execute_review_workflow(state, student_review)
            
            return result
            
        except Exception as e:
            logger.error(f"Error submitting review: {str(e)}")
            state.error = f"Review submission failed: {str(e)}"
            return state

    def execute_full_workflow(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the complete workflow using the compiled LangGraph workflow with safety limits.
        
        Args:
            state: Initial workflow state
            
        Returns:
            Final workflow state after complete execution
        """
        try:
            logger.debug("Executing full workflow using compiled LangGraph with safety limits")
            
            # FIXED: Use the workflow manager's improved execution method
            result = self.workflow_manager.execute_full_workflow(state)
            
            logger.debug("Full workflow execution completed")
            return result
            
        except Exception as e:
            logger.error(f"Error executing full workflow: {str(e)}")
            state.error = f"Full workflow execution failed: {str(e)}"
            return state
    
    def get_all_error_categories(self) -> Dict[str, List[str]]:
        """Get all available error categories."""
        return self.workflow_manager.get_all_error_categories()
    
    def validate_state(self, state: WorkflowState) -> tuple[bool, str]:
        """Validate the workflow state."""
        return self.workflow_manager.validate_workflow_state(state)
    
    def get_workflow_status(self, state: WorkflowState) -> Dict[str, Any]:
        """Get the current status of the workflow."""
        return self.workflow_manager.get_workflow_status(state)
    
    def get_compiled_workflow(self):
        """Get the compiled LangGraph workflow for direct execution."""
        return self._compiled_workflow
    
    def reset_workflow_state(self, state: WorkflowState) -> WorkflowState:
        """Reset the workflow state for a fresh start."""
        try:
            # Preserve configuration but reset execution state
            state.current_step = "generate"
            state.evaluation_attempts = 0
            state.evaluation_result = None
            state.code_generation_feedback = None
            state.code_snippet = None
            state.review_history = []
            state.current_iteration = 1
            state.review_sufficient = False
            state.comparison_report = None
            state.pending_review = None
            state.error = None
            
            logger.debug("Workflow state reset successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error resetting workflow state: {str(e)}")
            state.error = f"Failed to reset workflow state: {str(e)}"
            return state

    def _execute_until_step(self, state: WorkflowState, target_step: str) -> WorkflowState:
        """
        Execute workflow until reaching a specific step.
        
        Args:
            state: Current workflow state
            target_step: Target step to stop at
            
        Returns:
            Updated workflow state
        """
        current_state = state
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while (current_state.current_step != target_step and 
               current_state.current_step != "complete" and 
               not current_state.error and
               iteration < max_iterations):
            
            # Execute one step
            current_state = self._compiled_workflow.invoke(current_state)
            iteration += 1
            
            logger.debug(f"Workflow step {iteration}: {current_state.current_step}")
            
            # Stop if we've reached the target step
            if current_state.current_step == target_step:
                break
        
        return current_state
    
    def _execute_from_step(self, state: WorkflowState, current_step: str) -> WorkflowState:
        """
        Execute workflow from a specific step.
        
        Args:
            state: Current workflow state
            current_step: Current step to start from
            
        Returns:
            Updated workflow state
        """
        # Set the current step
        state.current_step = current_step
        
        # Execute the workflow
        return self._compiled_workflow.invoke(state)
    
    
    
    
    
    
    
    