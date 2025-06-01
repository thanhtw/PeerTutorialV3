"""
State Schema for Java Code Review Training System.

This module defines the state schema for the LangGraph-based workflow.
"""

__all__ = ['WorkflowState', 'CodeSnippet', 'ReviewAttempt']

from typing import List, Dict, Any, Optional, TypedDict, Literal
from pydantic import BaseModel, Field


class CodeSnippet(BaseModel):
    """Schema for code snippet data"""
    code: str = Field(description="The Java code snippet with annotations")
    clean_code: str = Field("", description="The Java code snippet without annotations")
    raw_errors: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="Raw error data organized by type")
    expected_error_count: int = Field(0, description="Number of errors originally requested for code generation")

class ReviewAttempt(BaseModel):
    """Schema for a student review attempt"""
    student_review: str = Field(description="The student's review text")
    iteration_number: int = Field(description="Iteration number of this review")
    analysis: Dict[str, Any] = Field(default_factory=dict, description="Analysis of the review")
    targeted_guidance: Optional[str] = Field(None, description="Targeted guidance for next iteration")

class WorkflowState(BaseModel):
    """The state for the Java Code Review workflow"""
    # Current workflow step - FIXED: Updated step names to match nodes
    current_step: Literal["generate", "evaluate", "regenerate", "review", "analyze", "generate_comparison_report", "complete"] = Field(
        "generate", description="Current step in the workflow"
    )
    
    # Code generation parameters
    code_length: str = Field("medium", description="Length of code (short, medium, long)")
    difficulty_level: str = Field("medium", description="Difficulty level (easy, medium, hard)")
    domain: Optional[str] = Field(None, description="Domain context for the generated code")
    
    # Error selection parameters
    selected_error_categories: Dict[str, List[str]] = Field(
        default_factory=lambda: {"java_errors": []}, 
        description="Selected error categories"
    )
    selected_specific_errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Specifically selected errors (when using specific mode)"
    )
    
    # Code data
    code_snippet: Optional[CodeSnippet] = Field(None, description="Generated code snippet data")
    
    # Review data
    review_history: List[ReviewAttempt] = Field(default_factory=list, description="History of review attempts")
    current_iteration: int = Field(1, description="Current iteration number")
    max_iterations: int = Field(3, description="Maximum number of iterations")
    
    # Analysis results
    review_sufficient: bool = Field(False, description="Whether the review is sufficient")    
    comparison_report: Optional[str] = Field(None, description="Comparison report")
    
    # NEW: Student review submission for workflow processing
    pending_review: Optional[str] = Field(None, description="Student review waiting to be processed")
    
    # Error handling
    error: Optional[str] = Field(None, description="Error message if any")
    evaluation_result: Optional[Dict[str, Any]] = Field(None, description="Results from code evaluation")
    evaluation_attempts: int = Field(0, description="Number of attempts to generate code")
    max_evaluation_attempts: int = Field(5, description="Maximum number of code generation attempts")
    code_generation_feedback: Optional[str] = Field(None, description="Feedback for code generation")
    
    # Original requested errors count (for consistency throughout the workflow)
    original_error_count: int = Field(0, description="Original number of errors requested for generation")
    error_count_start: int = Field(1, description="Minimum number of errors to generate")
    error_count_end: int = Field(2, description="Maximum number of errors to generate")