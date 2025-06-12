"""
Utility functions for code generation and processing in the Java Code Review System.

This module provides shared functionality for generating prompts, 
extracting code from responses, and handling error comments with improved
organization, error handling, and type safety.
"""
import streamlit as st
import re
import random
import logging
import json
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass

from utils.language_utils import t, get_llm_prompt_instructions, get_current_language
from analytics.behavior_tracker import behavior_tracker
from prompts import get_prompt_template, format_prompt_safely
import time
import uuid

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
    FIXED: Enhanced regex patterns and better handling of various response formats.
    
    Args:
        response: LLM response containing code blocks
        
    Returns:
        Tuple of (annotated_code, clean_code)
    """
    try:
        response_text = process_llm_response(response)
        
        if not response_text:
            logger.error("Empty response from LLM")
            return "", ""
        
        logger.debug(f"Processing LLM response (length: {len(response_text)})")
        logger.debug(f"Response preview: {response_text[:200]}...")
        
        # More comprehensive patterns for different code block formats
        # Order matters - more specific patterns first
        patterns = [
            # Specific annotated and clean patterns
            (r'```java-annotated\s*\n(.*?)```', r'```java-clean\s*\n(.*?)```'),
            (r'```java-annotated(.*?)```', r'```java-clean(.*?)```'),
            
            # Generic Java patterns
            (r'```java\s*\n(.*?)```', r'```java\s*\n(.*?)```'),
            (r'```java(.*?)```', r'```java(.*?)```'),
            
            # Generic code patterns
            (r'```\s*\n(.*?)```', r'```\s*\n(.*?)```'),
            (r'```(.*?)```', r'```(.*?)```'),
        ]
        
        # Try each pattern combination
        for annotated_pattern, clean_pattern in patterns:
            annotated_matches = re.findall(annotated_pattern, response_text, re.DOTALL | re.IGNORECASE)
            clean_matches = re.findall(clean_pattern, response_text, re.DOTALL | re.IGNORECASE)
            
            if annotated_matches and clean_matches:
                # Found both versions
                annotated_code = _clean_extracted_code(annotated_matches[0])
                clean_code = _clean_extracted_code(clean_matches[-1] if len(clean_matches) > 1 else clean_matches[0])
                
                if annotated_code.strip() and clean_code.strip():
                    logger.debug(f"Successfully extracted both versions (annotated: {len(annotated_code)} chars, clean: {len(clean_code)} chars)")
                    return annotated_code, clean_code
        
        # Fallback: try to find any code blocks
        all_code_blocks = []
        fallback_patterns = [
            r'```java-annotated\s*\n?(.*?)```',
            r'```java-clean\s*\n?(.*?)```', 
            r'```java\s*\n?(.*?)```',
            r'```\s*\n?(.*?)```'
        ]
        
        for pattern in fallback_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                cleaned = _clean_extracted_code(match)
                if cleaned.strip() and len(cleaned.strip()) > 10:  # Must have some substantial content
                    all_code_blocks.append(cleaned)
        
        # Remove duplicates while preserving order
        unique_blocks = []
        for block in all_code_blocks:
            if block not in unique_blocks:
                unique_blocks.append(block)
        
        if len(unique_blocks) >= 2:
            logger.debug(f"Using fallback extraction: found {len(unique_blocks)} unique code blocks")
            return unique_blocks[0], unique_blocks[1]
        elif len(unique_blocks) == 1:
            logger.debug("Using single code block for both versions")
            return unique_blocks[0], unique_blocks[0]
        
        # Last resort: try to extract any Java-like content
        java_content = _extract_java_content_heuristic(response_text)
        if java_content:
            logger.debug("Using heuristic Java content extraction")
            return java_content, java_content
        
        # If all else fails, log the issue and return the raw response
        logger.error("No code blocks found in response using any pattern")
        logger.debug(f"Full response for debugging: {response_text}")
        
        # Return a minimal fallback
        fallback_content = response_text.strip()
        if len(fallback_content) > 100:  # If there's substantial content
            return fallback_content, fallback_content
        else:
            return "", ""
            
    except Exception as e:
        logger.error(f"Error extracting code versions: {str(e)}")
        return "", ""

def _clean_extracted_code(code_text: str) -> str:
    """
    Clean extracted code text by removing common artifacts.
    
    Args:
        code_text: Raw extracted code text
        
    Returns:
        Cleaned code text
    """
    if not code_text:
        return ""
    
    # Remove leading/trailing whitespace
    code = code_text.strip()
    
    # Remove common prefixes/suffixes that might be captured
    prefixes_to_remove = ['java', 'java-annotated', 'java-clean', '\n', '\r\n']
    for prefix in prefixes_to_remove:
        if code.startswith(prefix):
            code = code[len(prefix):].strip()
    
    # Fix line endings
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove excessive blank lines
    code = re.sub(r'\n{3,}', '\n\n', code)
    
    return code

def _extract_java_content_heuristic(text: str) -> str:
    """
    Heuristic approach to extract Java-like content from text.
    
    Args:
        text: Text to extract Java content from
        
    Returns:
        Extracted Java content or empty string
    """
    try:
        # Look for Java class definition patterns
        java_patterns = [
            r'(public\s+class\s+\w+.*?(?=public\s+class|\Z))',
            r'(class\s+\w+.*?(?=class|\Z))',
            r'(import\s+.*?(?:\n.*?)*?public\s+class.*?(?=import|public\s+class|\Z))'
        ]
        
        for pattern in java_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                content = matches[0].strip()
                if len(content) > 50 and ('class' in content.lower() or 'public' in content.lower()):
                    logger.debug(f"Extracted Java content using heuristic (length: {len(content)})")
                    return content
        
        return ""
        
    except Exception as e:
        logger.error(f"Error in heuristic Java extraction: {str(e)}")
        return ""

def process_llm_response(response) -> str:
    """
    Process and clean LLM response with improved error handling.
    FIXED: Enhanced response processing to handle various response types.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Processed response string
    """
    try:
        if response is None:
            logger.warning("Received None response from LLM")
            return ""
        
        # Handle different response types
        content = ""
        
        if hasattr(response, 'content'):
            content = response.content
        elif isinstance(response, dict):
            if 'content' in response:
                content = response['content']
            elif 'text' in response:
                content = response['text']
            elif 'output' in response:
                content = response['output']
        elif isinstance(response, (str, bytes)):
            content = response
        else:
            # Try to convert to string as last resort
            content = str(response)
        
        # Ensure we have a string
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        
        result = str(content).strip() if content else ""
        
        if not result:
            logger.warning("Empty content after processing LLM response")
        
        return result
        
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
        
        total_problems = review_analysis.get(t("total_problems"), 0)
        identified_count = review_analysis.get(t("identified_count"), 0)        
        prompt_vars = {
            "total_problems": total_problems,
            "identified_count": identified_count,
            "accuracy": review_analysis.get(t("identified_percentage"), 0),
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

def _get_category_icon(category_name: str) -> str:
        
    """Get icon for category based on name (language-aware)."""
    # Map both English and Chinese category names to icons
    icon_mapping = {
            # English category names (from database)
            "logical errors": "🧠",
            "syntax errors": "🔤", 
            "code quality": "⭐",
            "standard violation": "📋",
            "java specific": "☕",
            
            # Chinese category names (from database)
            "邏輯錯誤": "🧠",
            "語法錯誤": "🔤",
            "程式碼品質": "⭐", 
            "標準違規": "📋",
            "java 特定錯誤": "☕",
            
            # Category codes (fallback)
            "logical": "🧠",
            "syntax": "🔤",
            "code_quality": "⭐",
            "standard_violation": "📋", 
            "java_specific": "☕"
        }
        
    # Try exact match first (case-sensitive)
    if category_name in icon_mapping:
        return icon_mapping[category_name]
        
    # Try case-insensitive match
    category_lower = category_name.lower()
    for key, icon in icon_mapping.items():
        if key.lower() == category_lower:
            return icon
        
        # Default fallback icon
    return "🐛"

def _get_difficulty_icon(difficulty_name: str) -> str:
        
    """Get icon for category based on name (language-aware)."""
    # Map both English and Chinese category names to icons
    icon_mapping = {
            # English category names (from database)
            "easy": "⭐",
            "medium": "⭐⭐", 
            "hard": "⭐⭐⭐",           
            
            # Chinese category names (from database)
            "简单": "⭐",
            "中等": "⭐⭐",
            "困難": "⭐⭐⭐"  
        }
        
    # Try exact match first (case-sensitive)
    if difficulty_name in icon_mapping:
        return icon_mapping[difficulty_name]
        
    # Try case-insensitive match
    difficulty_name_lower = difficulty_name.lower()
    for key, icon in icon_mapping.items():
        if key.lower() == difficulty_name_lower:
            return icon
        
        # Default fallback icon
    return "🐛"

def _log_user_interaction_code_display( 
                         user_id: str,
                         interaction_type: str,
                         action: str,
                         component: str = "code_display_ui",
                         success: bool = True,
                         error_message: str = None,
                         details: Dict[str, Any] = None,
                         time_spent_seconds: int = None) -> None:
    """
    Centralized method to log all user interactions to the database.
    
    Args:
        user_id: The user's ID
        interaction_type: 'main_workflow' for main workflow interactions
        action: Specific action taken
        component: UI component name
        success: Whether the action was successful
        error_message: Error message if any
        details: Additional details about the interaction
        time_spent_seconds: Time spent on this interaction
    """
    try:
        if not user_id:
            return
        
        # Get or create session ID
        session_id = st.session_state.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            st.session_state.session_id = session_id
        
        # Prepare context data
        context_data = {            
            "current_step": getattr(st.session_state.get("workflow_state"), 'current_step', 'unknown') if hasattr(st.session_state, 'workflow_state') else 'unknown',
            "current_iteration": getattr(st.session_state.get("workflow_state"), 'current_iteration', 0) if hasattr(st.session_state, 'workflow_state') else 0,
            "has_code_snippet": hasattr(st.session_state.get("workflow_state"), 'code_snippet') if hasattr(st.session_state, 'workflow_state') else False,
            "language": get_current_language(),
            "timestamp": time.time()
        }
        
        # Add any additional details
        if details:
            context_data.update(details)
        
        # Log through behavior tracker
        behavior_tracker.log_interaction(
            user_id=user_id,
            interaction_type=action,
            interaction_category=interaction_type,
            component=component,
            action=action,
            details=context_data,
            time_spent_seconds=time_spent_seconds,
            success=success,
            error_message=error_message,
            context_data=context_data
        )
        
        logger.debug(f"Logged {interaction_type} interaction: {action} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error logging user interaction: {str(e)}")

def _log_user_interaction_code_generator( 
                         user_id: str,
                         interaction_type: str,
                         action: str,
                         component: str = "code_generator_ui",
                         success: bool = True,
                         error_message: str = None,
                         details: Dict[str, Any] = None,
                         time_spent_seconds: int = None) -> None:
    """
    Centralized method to log all user interactions to the database.
    """
    try:
        if not user_id:
            return
        
        session_id = st.session_state.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            st.session_state.session_id = session_id
        
        context_data = {            
            "selected_categories": st.session_state.get("selected_categories", []),
            "user_level": st.session_state.get("user_level", "medium"),
            "workflow_step": "generate",
            "language": get_current_language(),
            "timestamp": time.time()
        }
        
        if details:
            context_data.update(details)
        
        behavior_tracker.log_interaction(
            user_id=user_id,
            interaction_type=action,
            interaction_category=interaction_type,
            component=component,
            action=action,
            details=context_data,
            time_spent_seconds=time_spent_seconds,
            success=success,
            error_message=error_message,
            context_data=context_data
        )
        
        logger.debug(f"Logged {interaction_type} interaction: {action} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error logging user interaction: {str(e)}")

def _log_user_interaction_feedback_system( 
                         user_id: str,
                         interaction_type: str,
                         action: str,
                         component: str = "feedback_system",
                         success: bool = True,
                         error_message: str = None,
                         details: Dict[str, Any] = None,
                         time_spent_seconds: int = None) -> None:
    """
    Centralized method to log all user interactions to the database.
    """
    try:
        if not user_id:
            return
        
        session_id = st.session_state.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            st.session_state.session_id = session_id
        
        context_data = {          
            "has_review_history": bool(getattr(st.session_state.get("workflow_state"), 'review_history', [])) if hasattr(st.session_state, 'workflow_state') else False,
            "language": get_current_language(),
            "timestamp": time.time()
        }
        
        if details:
            context_data.update(details)
        
        behavior_tracker.log_interaction(
            user_id=user_id,
            interaction_type=action,
            interaction_category=interaction_type,
            component=component,
            action=action,
            details=context_data,
            time_spent_seconds=time_spent_seconds,
            success=success,
            error_message=error_message,
            context_data=context_data
        )
        
        logger.debug(f"Logged {interaction_type} interaction: {action} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error logging user interaction: {str(e)}")
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

def parse_comparison_report(report_text: str) -> Dict[str, Any]:
    """
    Parse comparison report text and extract JSON data with improved error handling.
    
    Args:
        report_text: Text containing comparison report
        
    Returns:
        Dictionary containing parsed report data
    """
    if not report_text:
        return {
            "error": "Empty report text",
            "performance_summary": {
                "total_issues": 0,
                "identified_count": 0,
                "accuracy_percentage": 0.0,
                "missed_count": 0,
                "overall_assessment": "No report available",
                "completion_status": "Error"
            },
            "correctly_identified_issues": [],
            "missed_issues": [],
            "tips_for_improvement": [],
            "java_specific_guidance": [],
            "encouragement_and_next_steps": {
                "positive_feedback": "No feedback available",
                "next_focus_areas": "Please try again",
                "learning_objectives": "Continue practicing"
            },
            "detailed_feedback": {
                "strengths_identified": [],
                "improvement_patterns": [],
                "review_approach_feedback": "No feedback available"
            }
        }
    
    try:
        # First try to parse as direct JSON
        if report_text.strip().startswith('{') and report_text.strip().endswith('}'):
            try:
                return json.loads(report_text)
            except json.JSONDecodeError:
                pass
        
        # Try to extract JSON from text
        json_match = re.search(r'\{.*\}', report_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            
            # Clean up common JSON issues
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)  # Remove trailing commas
            json_str = re.sub(r'([{,]\s*)(\w+):', r'\1"\2":', json_str)  # Quote unquoted keys
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse cleaned JSON: {e}")
        
        # If all JSON parsing fails, return a basic structure
        logger.warning("Could not parse comparison report as JSON, returning basic structure")
        return {
            "error": "Failed to parse JSON",
            "raw_text": report_text[:500] + ("..." if len(report_text) > 500 else ""),
            "performance_summary": {
                "total_issues": 0,
                "identified_count": 0,
                "accuracy_percentage": 0.0,
                "missed_count": 0,
                "overall_assessment": "Report parsing failed",
                "completion_status": "Error"
            },
            "correctly_identified_issues": [],
            "missed_issues": [],
            "tips_for_improvement": [],
            "java_specific_guidance": [],
            "encouragement_and_next_steps": {
                "positive_feedback": "System encountered an error",
                "next_focus_areas": "Please try again",
                "learning_objectives": "Continue practicing"
            },
            "detailed_feedback": {
                "strengths_identified": [],
                "improvement_patterns": [],
                "review_approach_feedback": "Report parsing failed"
            }
        }
        
    except Exception as e:
        logger.error(f"Error parsing comparison report: {str(e)}")
        return {
            "error": f"Parse error: {str(e)}",
            "performance_summary": {
                "total_issues": 0,
                "identified_count": 0,
                "accuracy_percentage": 0.0,
                "missed_count": 0,
                "overall_assessment": "Error parsing report",
                "completion_status": "Error"
            },
            "correctly_identified_issues": [],
            "missed_issues": [],
            "tips_for_improvement": [],
            "java_specific_guidance": [],
            "encouragement_and_next_steps": {
                "positive_feedback": "System error occurred",
                "next_focus_areas": "Please try again",
                "learning_objectives": "Continue practicing"
            },
            "detailed_feedback": {
                "strengths_identified": [],
                "improvement_patterns": [],
                "review_approach_feedback": "Error occurred"
            }
        }