"""
LangGraph Workflow for Java Peer Review Training System.

This module implements the code review workflow as a LangGraph graph
by leveraging the modular components from the workflow package.
Enhanced to provide better integration with the workflow manager.
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
    
    This class serves as a facade to the modular workflow system,
    maintaining backward compatibility with the existing API while
    delegating actual implementation to the enhanced workflow manager.
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
        
        # Set up references to workflow components for backward compatibility
        self.workflow = self.workflow_manager.workflow
        self.error_repository = self.workflow_manager.error_repository
        
        # Get references to workflow nodes and conditions
        self.workflow_nodes = self.workflow_manager.workflow_nodes
        self.conditions = WorkflowConditions()
    
    def generate_code_node(self, state: WorkflowState) -> WorkflowState:
        """
        Generate Java code with errors node.
        Enhanced to use the workflow manager's complete code generation process.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state with generated code
        """
        try:
            logger.debug("JavaCodeReviewGraph: Starting code generation")
            
            # Validate the workflow state before proceeding
            is_valid, error_message = self.workflow_manager.validate_workflow_state(state)
            if not is_valid:
                logger.error(f"Invalid workflow state: {error_message}")
                state.error = error_message
                return state
            
            # Use the workflow manager's enhanced code generation method
            # This includes generation, evaluation, and potential regeneration
            updated_state = self.workflow_manager.execute_code_generation(state)
            
            # Log the workflow status
            status = self.workflow_manager.get_workflow_status(updated_state)
            logger.debug(f"Code generation completed with status: {status}")
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in JavaCodeReviewGraph.generate_code_node: {str(e)}")
            state.error = f"Code generation failed: {str(e)}"
            return state
    
    def regenerate_code_node(self, state: WorkflowState) -> WorkflowState:
        """
        Regenerate code based on evaluation feedback.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state with regenerated code
        """
        # Delegate to workflow manager for step execution
        return self.workflow_manager.execute_workflow_step(state, "regenerate_code")
    
    def evaluate_code_node(self, state: WorkflowState) -> WorkflowState:
        """
        Evaluate generated code to ensure it contains the requested errors.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state with evaluation results
        """
        # Delegate to workflow manager for step execution
        return self.workflow_manager.execute_workflow_step(state, "evaluate_code")
    
    def review_code_node(self, state: WorkflowState) -> WorkflowState:
        """
        Review code node - placeholder since user input happens in the UI.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        # Delegate to workflow manager for step execution
        return self.workflow_manager.execute_workflow_step(state, "review_code")
    
    def analyze_review_node(self, state: WorkflowState) -> WorkflowState:
        """
        Analyze student review node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state with review analysis
        """
        # Delegate to workflow manager for step execution
        return self.workflow_manager.execute_workflow_step(state, "analyze_review")
    
    def generate_summary_node(self, state: WorkflowState) -> WorkflowState:
        """
        Generate summary node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state with summary
        """
        # Delegate to workflow manager for step execution
        return self.workflow_manager.execute_workflow_step(state, "generate_summary")
    
    def should_regenerate_or_review(self, state: WorkflowState) -> str:
        """
        Determine if we should regenerate code or move to review.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next step name
        """
        # Delegate to workflow conditions implementation
        return self.conditions.should_regenerate_or_review(state)
    
    def should_continue_review(self, state: WorkflowState) -> str:
        """
        Determine if we should continue with another review iteration or generate summary.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next step name
        """
        # Delegate to workflow conditions implementation
        return self.conditions.should_continue_review(state)
    
    def get_all_error_categories(self) -> Dict[str, List[str]]:
        """
        Get all available error categories.
        
        Returns:
            Dictionary with error categories
        """
        # Delegate to workflow manager
        return self.workflow_manager.get_all_error_categories()
    
    def submit_review(self, state: WorkflowState, student_review: str) -> WorkflowState:
        """
        Submit a student review and update the state.
        
        Args:
            state: Current workflow state
            student_review: The student's review text
            
        Returns:
            Updated workflow state with analysis
        """
        # Delegate to workflow manager implementation
        return self.workflow_manager.submit_review(state, student_review)
    
    def execute_full_workflow(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the complete workflow from start to finish.
        This method provides access to the full LangGraph workflow execution.
        
        Args:
            state: Initial workflow state
            
        Returns:
            Final workflow state after complete execution
        """
        return self.workflow_manager.execute_full_workflow(state)
    
    def get_workflow_status(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Get the current status of the workflow.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with workflow status information
        """
        return self.workflow_manager.get_workflow_status(state)
    
    def validate_state(self, state: WorkflowState) -> tuple[bool, str]:
        """
        Validate the workflow state.
        
        Args:
            state: Workflow state to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.workflow_manager.validate_workflow_state(state)
    
    def get_compiled_workflow(self):
        """
        Get the compiled LangGraph workflow for direct execution.
        
        Returns:
            Compiled LangGraph workflow
        """
        return self.workflow_manager.get_compiled_workflow()
    
    def reset_workflow_state(self, state: WorkflowState) -> WorkflowState:
        """
        Reset the workflow state for a fresh start.
        
        Args:
            state: Current workflow state
            
        Returns:
            Reset workflow state
        """
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
            state.error = None
            
            logger.debug("Workflow state reset successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error resetting workflow state: {str(e)}")
            state.error = f"Failed to reset workflow state: {str(e)}"
            return state