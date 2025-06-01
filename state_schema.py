"""
State Schema for Java Peer Review Training System.

This module defines the state schema for the LangGraph workflow,
ensuring proper type safety and state management.
FIXED: Added workflow_phase for proper workflow control.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from typing_extensions import TypedDict

@dataclass
class CodeSnippet:
    """Represents a generated code snippet with its metadata."""
    code: str = ""
    clean_code: str = ""
    raw_errors: Dict[str, Any] = field(default_factory=dict)
    expected_error_count: int = 0

@dataclass
class ReviewAttempt:
    """Represents a student's review attempt with analysis."""
    student_review: str = ""
    iteration_number: int = 1
    analysis: Dict[str, Any] = field(default_factory=dict)
    targeted_guidance: Optional[str] = None

class WorkflowState(TypedDict, total=False):
    """
    State schema for the Java Code Review workflow.
    FIXED: Added workflow_phase for proper workflow control and recursion prevention.
    
    This TypedDict defines all possible state variables that can be passed
    between nodes in the LangGraph workflow.
    """
    
    # Workflow Control
    current_step: str
    workflow_phase: str  # "generation", "review", "full" - NEW FIELD
    error: Optional[str]
    
    # Code Generation Parameters
    code_length: str
    difficulty_level: str
    domain: str
    error_count_start: str
    error_count_end: str
    selected_error_categories: Dict[str, List[str]]
    selected_specific_errors: List[Dict[str, Any]]
    
    # Code Generation State
    code_snippet: Optional[CodeSnippet]
    original_error_count: int
    
    # Code Evaluation State
    evaluation_attempts: int
    max_evaluation_attempts: int  # Add explicit limit
    evaluation_result: Optional[Dict[str, Any]]
    code_generation_feedback: Optional[str]
    
    # Review State
    pending_review: Optional[str]
    current_iteration: int
    max_iterations: int
    review_sufficient: bool
    review_history: List[ReviewAttempt]
    
    # Final Output
    comparison_report: Optional[str]
    final_summary: Optional[str]