"""
Simplified LangGraph Workflow for Java Peer Review Training System.

This module implements the code review workflow as a LangGraph graph
by leveraging the modular components from the workflow package.
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
    Simplified LangGraph implementation of the Java Code Review workflow.
    
    This class provides a clean interface to the LangGraph workflow
    with straightforward execution methods.
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
        
        logger.debug("JavaCodeReviewGraph initialized successfully")
    
    def execute_code_generation(self, state: WorkflowState) -> WorkflowState:
        """
        Execute code generation workflow.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state after code generation and evaluation
        """
        try:
            logger.debug("Executing code generation")
            
            # Validate the workflow state before proceeding
            is_valid, error_message = self.workflow_manager.validate_workflow_state(state)
            if not is_valid:
                logger.error(f"Invalid workflow state: {error_message}")
                state.error = error_message
                return state
            
            # Set initial step
            state.current_step = "generate"
            
            # Execute using the workflow manager
            result = self.workflow_manager.execute_code_generation_workflow(state)
            
            # Log the workflow status
            if not result.error:
                logger.debug("Code generation completed successfully")
            else:
                logger.error(f"Code generation failed: {result.error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in code generation: {str(e)}")
            state.error = f"Code generation failed: {str(e)}"
            return state
    
    def submit_review(self, state: WorkflowState, student_review: str) -> WorkflowState:
        """
        Submit a student review for analysis.
        
        Args:
            state: Current workflow state
            student_review: The student's review text
            
        Returns:
            Updated workflow state with analysis
        """
        try:
            logger.debug("Submitting review for analysis")
            
            # Use the workflow manager execution method
            result = self.workflow_manager.execute_review_workflow(state, student_review)
            
            if not result.error:
                logger.debug("Review submission completed successfully")
            else:
                logger.error(f"Review submission failed: {result.error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error submitting review: {str(e)}")
            state.error = f"Review submission failed: {str(e)}"
            return state

    def execute_full_workflow(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the complete workflow from start to finish.
        
        Args:
            state: Initial workflow state
            
        Returns:
            Final workflow state after complete execution
        """
        try:
            logger.debug("Executing full workflow")
            
            # Use the workflow manager execution method
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
        """Get the compiled LangGraph workflow."""
        return self._compiled_workflow
    
    def reset_workflow_state(self, state: WorkflowState) -> WorkflowState:
        """Reset the workflow state for a fresh start."""
        try:
            # Reset execution state while preserving configuration
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
            state.final_summary = None
            
            logger.debug("Workflow state reset successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error resetting workflow state: {str(e)}")
            state.error = f"Failed to reset workflow state: {str(e)}"
            return state