"""
Schema-compliant Workflow Builder for Java Peer Review Training System.

This module provides the GraphBuilder class that works with the existing
WorkflowState schema constraints while maintaining logical separation.
FIXED: Uses existing schema step names to avoid validation errors.
"""

import logging
from langgraph.graph import StateGraph, END

from state_schema import WorkflowState
from workflow.node import WorkflowNodes
from workflow.conditions import WorkflowConditions
from utils.language_utils import t

# Configure logging
logger = logging.getLogger(__name__)

class GraphBuilder:
    """
    Builder for the Java Code Review workflow graph that complies with existing schema.
    
    This class builds the workflow using existing allowed step names while
    maintaining the logical separation between code generation and review phases.
    """
    
    def __init__(self, workflow_nodes: WorkflowNodes):
        """
        Initialize the graph builder with workflow nodes.
        
        Args:
            workflow_nodes: WorkflowNodes instance containing node handlers
        """
        self.workflow_nodes = workflow_nodes
        self.conditions = WorkflowConditions()
    
    def build_graph(self) -> StateGraph:
        """
        Build the complete LangGraph workflow using existing schema step names.
        
        Returns:
            StateGraph: The constructed workflow graph
        """
        logger.debug("Building schema-compliant workflow graph")
        
        # Create a new graph with our state schema
        workflow = StateGraph(WorkflowState)
        
        # Add all nodes to the graph
        self._add_nodes(workflow)
        
        # Add standard edges to the graph
        self._add_standard_edges(workflow)
        
        # Add conditional edges to the graph
        self._add_conditional_edges(workflow)
        
        # Set the entry point
        workflow.set_entry_point("generate_code")
        
        logger.info("Schema-compliant workflow graph construction completed")
        return workflow
    
    def _add_nodes(self, workflow: StateGraph) -> None:
        """
        Add all nodes to the workflow graph using existing schema-compliant names.
        
        Args:
            workflow: StateGraph to add nodes to
        """
        # Code generation and evaluation phase nodes
        workflow.add_node("generate_code", self.workflow_nodes.generate_code_node)
        workflow.add_node("evaluate_code", self.workflow_nodes.evaluate_code_node)
        workflow.add_node("regenerate_code", self.workflow_nodes.regenerate_code_node)
        
        # Review phase nodes - using existing schema names
        workflow.add_node("review_code", self.workflow_nodes.review_code_node)  # Combined review handling
        workflow.add_node("analyze_review", self.workflow_nodes.analyze_review_node)
        
        # Final phase node
        workflow.add_node("generate_comparison_report", self.workflow_nodes.generate_comparison_report_node)
        
        logger.info("Added all nodes to workflow graph with schema compliance")
    
    def _add_standard_edges(self, workflow: StateGraph) -> None:
        """
        Add standard (non-conditional) edges to the workflow graph.
        
        Args:
            workflow: StateGraph to add edges to
        """
        # Code generation/evaluation phase edges
        workflow.add_edge("generate_code", "evaluate_code")
        workflow.add_edge("regenerate_code", "evaluate_code")
        
        # Review phase edges - REMOVED automatic edge to prevent loops
        # workflow.add_edge("review_code", "analyze_review")  # This caused the infinite loop!
        
        # Final edge
        workflow.add_edge("generate_comparison_report", END)
        
        logger.info("Added standard edges to workflow graph")
    
    def _add_conditional_edges(self, workflow: StateGraph) -> None:
        """
        Add conditional edges to the workflow graph with schema compliance.
        
        Args:
            workflow: StateGraph to add conditional edges to
        """
        # PHASE 1: Code Generation/Evaluation Flow
        workflow.add_conditional_edges(
            "evaluate_code",
            self.conditions.should_regenerate_or_review,
            {
                "regenerate_code": "regenerate_code",
                "review_code": "review_code"
            }
        )
        
        # PHASE 2A: Review Setup and Input Handling
        # Only proceed to analysis when there's a pending review, otherwise END workflow
        workflow.add_conditional_edges(
            "review_code",
            self.conditions.should_analyze_or_wait,
            {
                "analyze_review": "analyze_review",  # Student submitted review
                "wait_for_review": END               # Wait for student input (END workflow)
            }
        )
        
        # PHASE 2B: Review Analysis and Continuation
        workflow.add_conditional_edges(
            "analyze_review",
            self.conditions.should_continue_review,
            {
                "continue_review": "review_code",
                "generate_comparison_report": "generate_comparison_report"
            }
        )
        
        logger.info("Added conditional edges to workflow graph with schema compliance")