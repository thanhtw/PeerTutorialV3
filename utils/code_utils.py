"""
Utility functions for code generation and processing in the Java Code Review System.

This module provides shared functionality for generating prompts, 
extracting code from responses, and handling error comments with improved
organization, error handling, and type safety.
"""

import re
import random
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass

from utils.language_utils import t, get_llm_prompt_instructions, get_current_language
from prompts import get_prompt_template, format_prompt_safely

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CODE_LENGTH = "medium"
DEFAULT_DIFFICULTY = "medium"
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_MAX_ITERATIONS = 3
LINE_NUMBER_PADDING = 2

# Domain mapping for code generation
DEFAULT_DOMAINS = [
    "user_management", "file_processing", "data_validation", 
    "calculation", "inventory_system", "notification_service",
    "logging", "banking", "e-commerce", "student_management"
]

# Code complexity mapping
CODE_COMPLEXITY_MAP = {
    "short": "1 simple class with 1-2 basic methods (15-30 lines total)",
    "medium": "1 class with 3-5 methods of moderate complexity (40-80 lines total)",
    "long": "1-2 classes with 4-8 methods and clear relationships (100-150 lines total)"
}


@dataclass
class PromptContext:
    """Context information for prompt generation."""
    code_length: str = DEFAULT_CODE_LENGTH
    difficulty_level: str = DEFAULT_DIFFICULTY
    domain: str = ""
    error_count: int = 0
    language: str = "en"


class PromptBuilder:
    """Builder class for creating LLM prompts with consistent formatting."""
    
    def __init__(self, context: PromptContext):
        self.context = context
        self.language_instructions = get_llm_prompt_instructions(context.language)
    
    def build_prompt(self, template_name: str, **kwargs) -> str:
        """
        Build a prompt using the specified template and context.
        
        Args:
            template_name: Name of the prompt template
            **kwargs: Additional template variables
            
        Returns:
            Formatted prompt string
        """
        try:
            template = get_prompt_template(template_name, self.context.language)
            if not template:
                logger.error(f"Template '{template_name}' not found for language '{self.context.language}'")
                return ""
            
            # Merge context and kwargs
            prompt_vars = {
                **self._get_base_variables(),
                **kwargs
            }
            
            # Build the prompt with language instructions
            prompt = f"{self.language_instructions}. " + format_prompt_safely(template, **prompt_vars)
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error building prompt '{template_name}': {str(e)}")
            return ""
    
    def _get_base_variables(self) -> Dict[str, Any]:
        """Get base variables from context."""
        return {
            "code_length": self.context.code_length,
            "difficulty_level": self.context.difficulty_level,
            "domain": self.context.domain,
            "error_count": self.context.error_count
        }


# =============================================================================
# State and Error Extraction Functions
# =============================================================================

def get_error_count_from_state(state) -> int:
    """
    Get the total number of errors from the workflow state.
    
    Args:
        state: The workflow state containing error information
        
    Returns:
        int: Total number of errors, 0 if cannot be determined
    """
    try:
        # Priority order for extracting error count
        extraction_methods = [
            lambda: _get_count_from_evaluation_result(state),
            lambda: _get_count_from_specific_errors(state),
            lambda: _get_count_from_code_snippet(state),
            lambda: _get_count_from_original_count(state)
        ]
        
        for method in extraction_methods:
            count = method()
            if count > 0:
                logger.debug(f"Error count extracted: {count}")
                return count
        
        logger.warning(t("could_not_determine_error_count"))
        return 0
        
    except Exception as e:
        logger.error(f"Error getting error count from state: {str(e)}")
        return 0


def _get_count_from_evaluation_result(state) -> int:
    """Extract error count from evaluation result."""
    if hasattr(state, 'evaluation_result') and state.evaluation_result:
        found_errors = state.evaluation_result.get(t('found_errors'), [])
        missing_errors = state.evaluation_result.get(t('missing_errors'), [])
        return len(found_errors) + len(missing_errors)
    return 0


def _get_count_from_specific_errors(state) -> int:
    """Extract error count from selected specific errors."""
    if hasattr(state, 'selected_specific_errors') and state.selected_specific_errors:
        return len(state.selected_specific_errors)
    return 0


def _get_count_from_code_snippet(state) -> int:
    """Extract error count from code snippet."""
    if (hasattr(state, 'code_snippet') and state.code_snippet and
        hasattr(state.code_snippet, 'known_problems') and state.code_snippet.known_problems):
        return len(state.code_snippet.known_problems)
    return 0


def _get_count_from_original_count(state) -> int:
    """Extract error count from original count attribute."""
    return getattr(state, 'original_error_count', 0)


# =============================================================================
# Code Processing Functions
# =============================================================================

def add_line_numbers(code: str) -> str:
    """
    Add line numbers to code snippet with consistent formatting.
    
    Args:
        code: The code snippet to add line numbers to
        
    Returns:
        Code with line numbers, empty string if input is invalid
    """
    if not code or not isinstance(code, str):
        logger.warning("Invalid code input for line numbering")
        return ""
    
    try:
        lines = code.splitlines()
        if not lines:
            return ""
        
        max_line_num = len(lines)
        padding = max(LINE_NUMBER_PADDING, len(str(max_line_num)))
        
        numbered_lines = []
        for i, line in enumerate(lines, 1):
            line_num = str(i).rjust(padding)
            numbered_lines.append(f"{line_num} | {line}")
        
        return "\n".join(numbered_lines)
        
    except Exception as e:
        logger.error(f"Error adding line numbers: {str(e)}")
        return code  # Return original code if numbering fails


def extract_both_code_versions(response) -> Tuple[str, str]:
    """
    Extract both annotated and clean code versions from LLM response.
    
    Args:
        response: LLM response containing code blocks
        
    Returns:
        Tuple of (annotated_code, clean_code)
    """
    try:
        response_text = str(response)
        
        # Patterns for different code block formats
        patterns = [
            r'```java-annotated\s*(.*?)```',  # Annotated version
            r'```java-clean\s*(.*?)```',      # Clean version
            r'```java\s*(.*?)```',            # Generic Java
            r'```\s*(.*?)```'                 # Generic code block
        ]
        
        code_blocks = []
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            code_blocks.extend([match.strip() for match in matches])
        
        # Return based on what we found
        if len(code_blocks) >= 2:
            return code_blocks[0], code_blocks[1]
        elif len(code_blocks) == 1:
            return code_blocks[0], code_blocks[0]  # Use same code for both
        else:
            logger.warning("No code blocks found in response")
            return response_text.strip(), response_text.strip()
            
    except Exception as e:
        logger.error(f"Error extracting code versions: {str(e)}")
        return "", ""


def process_llm_response(response) -> str:
    """
    Process and clean LLM response with improved error handling.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Processed response string
    """
    try:
        if response is None:
            return ""
        
        if hasattr(response, 'content'):
            content = response.content
        elif isinstance(response, dict) and 'content' in response:
            content = response['content']
        else:
            content = response
        
        return str(content).strip() if content else ""
        
    except Exception as e:
        logger.error(f"Error processing LLM response: {str(e)}")
        return ""


# =============================================================================
# Error Formatting Functions
# =============================================================================

def format_errors_for_prompt(errors: List[Dict[str, Any]], language: str = None) -> str:
    """
    Format errors for inclusion in prompts with language support.
    
    Args:
        errors: List of error dictionaries
        language: Target language (uses current if None)
        
    Returns:
        Formatted error string
    """
    if not errors:
        return t("no_errors_available")
    
    error_list = []
    
    for i, error in enumerate(errors, 1):
        try:
            error_name = error.get('error_name', "Unknown Error")
            error_description = error.get('description', "Description not available")
            error_implementation_guide = error.get('implementation_guide', "")
            error_category = error.get('category', "General").upper()
            error_list.append(f"{i}. {t('error_category')}: {error_category} | {t('error_name_variable')}: {error_name} | {t('description')}: {error_description} | {t('implementation_guide')}: {error_implementation_guide}")

        except Exception as e:
            logger.warning(f"Error formatting error {i}: {str(e)}")
            continue
    
    return "\n\n".join(error_list)


def format_problems_for_prompt(problems: List[str]) -> str:
    """
    Format problem list for prompt inclusion.
    
    Args:
        problems: List of problem descriptions
        
    Returns:
        Formatted problems string
    """
    if not problems:
        return t("no_problems_found")
    
    return "\n".join(f"- {problem}" for problem in problems if problem)


def get_difficulty_instructions(difficulty_level: str) -> str:
    """
    Get difficulty-specific instructions for code generation.
    
    Args:
        difficulty_level: Difficulty level (easy, medium, hard)
        
    Returns:
        Difficulty instructions string
    """
    difficulty_map = {
        t("easy"): "beginner_instructions",
        t("medium"): "intermediate_instructions", 
        t("hard"): "advanced_instructions"
    }
    
    template_name = difficulty_map.get(difficulty_level.lower())
    if template_name:
        return get_prompt_template(template_name) or ""
    
    return get_prompt_template("intermediate_instructions") or ""


# =============================================================================
# Prompt Creation Functions
# =============================================================================

def create_code_generation_prompt(code_length: str, difficulty_level: str, 
                                 selected_errors: List[Dict], domain: str = None, 
                                 include_error_annotations: bool = True) -> str:
    """
    Create a prompt for generating Java code with intentional errors.
    
    Args:
        code_length: Length of code (short, medium, long)
        difficulty_level: Difficulty level (easy, medium, hard)
        selected_errors: List of errors to include
        domain: Domain context for the code
        include_error_annotations: Whether to include error annotations
        
    Returns:
        Generated prompt string
    """
    try:
        # Validate inputs
        if not selected_errors:
            logger.error("No errors provided for code generation")
            return ""
        
        # Create context
        context = PromptContext(
            code_length=code_length,
            difficulty_level=difficulty_level,
            domain=domain or random.choice(DEFAULT_DOMAINS),
            error_count=len(selected_errors),
            language=get_current_language()
        )
        
        # Build prompt
        builder = PromptBuilder(context)
        prompt_vars = {
            "domain_str": context.domain,
            "complexity": CODE_COMPLEXITY_MAP.get(code_length.lower(), CODE_COMPLEXITY_MAP["medium"]),
            "difficulty_instructions": get_difficulty_instructions(difficulty_level),
            "error_instructions": format_errors_for_prompt(selected_errors, context.language)
        }
        
        return builder.build_prompt("code_generation_template", **prompt_vars)
        
    except Exception as e:
        logger.error(f"Error creating code generation prompt: {str(e)}")
        return ""


def create_evaluation_prompt(code: str, requested_errors: List[Dict]) -> str:
    """
    Create a prompt for evaluating whether code contains required errors.
    
    Args:
        code: The code to evaluate
        requested_errors: List of errors that should be in the code
        
    Returns:
        Evaluation prompt string
    """
    try:
        if not code or not requested_errors:
            logger.error("Invalid inputs for evaluation prompt")
            return ""
        
        context = PromptContext(
            error_count=len(requested_errors),
            language=get_current_language()
        )
        
        builder = PromptBuilder(context)
        
        prompt_vars = {
            "code": add_line_numbers(code),
            "error_instructions": format_errors_for_prompt(requested_errors, context.language)
        }
        
        return builder.build_prompt("evaluation_template", **prompt_vars)
        
    except Exception as e:
        logger.error(f"Error creating evaluation prompt: {str(e)}")
        return ""


def create_regeneration_prompt(code: str, domain: str, missing_errors: List,
                              found_errors: List, requested_errors: List) -> str:
    """
    Create a prompt for regenerating code with missing errors.
    
    Args:
        code: The original code
        domain: Domain context
        missing_errors: Errors that need to be added
        found_errors: Errors that were found and should be preserved
        requested_errors: All requested errors
        
    Returns:
        Regeneration prompt string
    """
    try:
        context = PromptContext(
            domain=domain,
            error_count=len(requested_errors),
            language=get_current_language()
        )
        
        builder = PromptBuilder(context)
        
        prompt_vars = {
            "total_requested": len(requested_errors),
            "missing_text": _format_missing_errors(missing_errors),
            "found_text": _format_found_errors(found_errors),
            "code": code
        }
        
        return builder.build_prompt("regeneration_template", **prompt_vars)
        
    except Exception as e:
        logger.error(f"Error creating regeneration prompt: {str(e)}")
        return ""


def create_review_analysis_prompt(code: str, known_problems: List[str], 
                                 student_review: str) -> str:
    """
    Create a prompt for analyzing a student's review.
    
    Args:
        code: The code being reviewed
        known_problems: List of known problems
        student_review: Student's review text
        
    Returns:
        Review analysis prompt string
    """
    try:
        if not all([code, known_problems, student_review]):
            logger.error("Invalid inputs for review analysis prompt")
            return ""
        
        context = PromptContext(language=get_current_language())
        builder = PromptBuilder(context)
        
        prompt_vars = {
            "code": add_line_numbers(code),
            "problem_count": len(known_problems),
            "problems_text": format_problems_for_prompt(known_problems),
            "student_review": student_review,
            "meaningful_score_threshold": 0.6,
            "accuracy_score_threshold": 0.7
        }
        
        return builder.build_prompt("review_analysis_template", **prompt_vars)
        
    except Exception as e:
        logger.error(f"Error creating review analysis prompt: {str(e)}")
        return ""


def create_feedback_prompt(code: str, known_problems: List[str], 
                          review_analysis: Dict[str, Any]) -> str:
    """
    Create a prompt for generating targeted feedback.
    
    Args:
        code: The code being reviewed
        known_problems: List of known problems
        review_analysis: Analysis results
        
    Returns:
        Feedback prompt string
    """
    try:
        context = PromptContext(language=get_current_language())
        builder = PromptBuilder(context)
        
        # Extract metrics safely
        iteration = review_analysis.get(t("iteration_count"), 1)
        max_iterations = review_analysis.get(t("max_iterations"), DEFAULT_MAX_ITERATIONS)
        identified = review_analysis.get(t("identified_count"), 0)
        total = review_analysis.get(t("total_problems"), len(known_problems))
        
        prompt_vars = {
            "iteration": iteration,
            "max_iterations": max_iterations,
            "identified": identified,
            "total": total,
            "accuracy": (identified / total * 100) if total > 0 else 0,
            "remaining": max_iterations - iteration,
            "identified_text": _extract_problems_text(review_analysis, t("identified_problems")),
            "missed_text": _extract_problems_text(review_analysis, t("missed_problems"))
        }
        
        return builder.build_prompt("feedback_template", **prompt_vars)
        
    except Exception as e:
        logger.error(f"Error creating feedback prompt: {str(e)}")
        return ""


def create_comparison_report_prompt(evaluation_errors: List[str], 
                                   review_analysis: Dict[str, Any],
                                   review_history: List = None) -> str:
    """
    Create a prompt for generating a comparison report.
    
    Args:
        evaluation_errors: List of errors found by evaluation
        review_analysis: Analysis of the latest review
        review_history: History of all review attempts
        
    Returns:
        Comparison report prompt string
    """
    try:
        context = PromptContext(language=get_current_language())
        builder = PromptBuilder(context)
        
        total_problems = len(evaluation_errors)
        identified_count = review_analysis.get(t("identified_count"), 0)
        
        prompt_vars = {
            "total_problems": total_problems,
            "identified_count": identified_count,
            "accuracy": (identified_count / total_problems * 100) if total_problems > 0 else 0,
            "len_missed_str": len(review_analysis.get(t("missed_problems"), [])),
            "identified_text": _extract_problems_text(review_analysis, t("identified_problems")),
            "missed_text": _extract_problems_text(review_analysis, t("missed_problems")),
            "progress_info": _format_progress_info(review_history)
        }
        
        return builder.build_prompt("comparison_report_template", **prompt_vars)
        
    except Exception as e:
        logger.error(f"Error creating comparison report prompt: {str(e)}")
        return ""


# =============================================================================
# Helper Functions
# =============================================================================

def _format_missing_errors(missing_errors: List) -> str:
    """Format missing errors for prompt inclusion."""
    if not missing_errors:
        return t("no_missing_errors")
    
    formatted = []
    for i, error in enumerate(missing_errors, 1):
        try:
            if isinstance(error, dict):
                error_type = error.get(t("category"), "").upper()
                name = error.get(t("error_name_variable"), "")
                description = error.get(t("description"), "")
                implementation_guide = error.get(t("implementation_guide"), "")
                
                formatted.append(f"{i}. {error_type} - {name}: {description}")
                if implementation_guide:
                    formatted.append(f"   {t('implementation_guide')}: {implementation_guide}")
                formatted.append("")
            else:
                formatted.append(f"{i}. {str(error)}")
        except Exception as e:
            logger.warning(f"Error formatting missing error {i}: {str(e)}")
            continue
    
    return "\n".join(formatted)


def _format_found_errors(found_errors: List) -> str:
    """Format found errors for prompt inclusion."""
    if not found_errors:
        return t("no_found_errors")
    
    formatted = []
    for i, error in enumerate(found_errors, 1):
        try:
            if isinstance(error, dict):
                error_type = error.get(t("category"), "").upper()
                name = error.get(t("error_name_variable"), "")
                description = error.get(t("description"), "")
                formatted.append(f"{i}. {error_type} - {name}: {description}")
            else:
                formatted.append(f"{i}. {str(error)}")
        except Exception as e:
            logger.warning(f"Error formatting found error {i}: {str(e)}")
            continue
    
    return "\n".join(formatted)


def _extract_problems_text(analysis: Dict[str, Any], key: str) -> str:
    """Extract and format problems text from analysis."""
    problems = analysis.get(key, [])
    if not problems:
        return t("no_issues_identified") if "identified" in key else t("no_issues_missed")
    
    formatted = []
    for problem in problems:
        try:
            if isinstance(problem, dict):
                problem_desc = problem.get(t("problem"), "")
                if problem_desc:
                    formatted.append(f"- {problem_desc}")
            else:
                formatted.append(f"- {str(problem)}")
        except Exception as e:
            logger.warning(f"Error formatting problem: {str(e)}")
            continue
    
    return "\n".join(formatted)


def _format_progress_info(review_history: Optional[List]) -> str:
    """Format progress information from review history."""
    if not review_history or len(review_history) <= 1:
        return ""
    
    return f"This is attempt {len(review_history)} of the review process."


# =============================================================================
# Validation Functions
# =============================================================================

def validate_prompt_inputs(code_length: str = None, difficulty_level: str = None,
                          errors: List = None) -> Tuple[bool, str]:
    """
    Validate inputs for prompt creation.
    
    Args:
        code_length: Code length parameter
        difficulty_level: Difficulty level parameter
        errors: List of errors
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if code_length and code_length not in CODE_COMPLEXITY_MAP:
            return False, f"Invalid code length: {code_length}"
        
        valid_difficulties = ["easy", "medium", "hard", t("easy"), t("medium"), t("hard")]
        if difficulty_level and difficulty_level not in valid_difficulties:
            return False, f"Invalid difficulty level: {difficulty_level}"
        
        if errors is not None and not isinstance(errors, list):
            return False, "Errors must be provided as a list"
        
        return True, ""
        
    except Exception as e:
        logger.error(f"Error validating prompt inputs: {str(e)}")
        return False, f"Validation error: {str(e)}"