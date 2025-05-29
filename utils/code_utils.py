"""
Utility functions for code generation and processing in the Java Code Review System.

This module provides shared functionality for generating prompts, 
extracting code from responses, and handling error comments.
"""

import re
import random
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.language_models import BaseLanguageModel
from utils.language_utils import t, get_llm_prompt_instructions, get_current_language

# Import prompt templates
from prompts import get_prompt_template, format_prompt_safely

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_error_count_from_state(state) -> int:
    """
    Get the total number of errors from the workflow state.
    
    Args:
        state: The workflow state containing error information
        
    Returns:
        int: Total number of errors
    """
    try:
        # Try to get from evaluation result first
        if hasattr(state, 'evaluation_result') and state.evaluation_result:
            found_errors = state.evaluation_result.get(t('found_errors'), [])
            missing_errors = state.evaluation_result.get(t('missing_errors'), [])
            return len(found_errors) + len(missing_errors)
        
        # Try to get from selected specific errors
        if hasattr(state, 'selected_specific_errors') and state.selected_specific_errors:
            return len(state.selected_specific_errors)
        
        # Try to get from code snippet known problems
        if hasattr(state, 'code_snippet') and state.code_snippet:
            if hasattr(state.code_snippet, 'known_problems') and state.code_snippet.known_problems:
                return len(state.code_snippet.known_problems)
        
        # Default fallback
        logger.warning(t("could_not_determine_error_count"))
        return 0
        
    except Exception as e:
        logger.error(f"{t('error')} {t('getting_error_count_from_state')}: {str(e)}")
        return 0

def add_line_numbers(code: str) -> str:
    """
    Add line numbers to code snippet.
    
    Args:
        code: The code snippet to add line numbers to
        
    Returns:
        Code with line numbers
    """
    lines = code.splitlines()
    max_line_num = len(lines)
    padding = len(str(max_line_num))
    
    # Create a list of lines with line numbers
    numbered_lines = []
    for i, line in enumerate(lines, 1):
        # Format line number with consistent padding
        line_num = str(i).rjust(padding)
        numbered_lines.append(f"{line_num} | {line}")
    
    return "\n".join(numbered_lines)

def create_code_generation_prompt(code_length: str, difficulty_level: str, selected_errors: list, domain: str = None, include_error_annotations: bool = True) -> str:
    """
    Create a concise prompt for generating Java code with intentional errors.
    Enhanced to emphasize the exact number of errors required and ensure one per error type.
    Now uses language-specific templates based on current language and database fields.
    
    Args:
        code_length: Length of code (short, medium, long)
        difficulty_level: Difficulty level (easy, medium, hard)
        selected_errors: List of errors to include in the code
        domain: Domain context for the code
        include_error_annotations: Whether to include error annotations
        
    Returns:
        Optimized prompt string for LLM
    """
    # Define code complexity by length
    complexity = {
        "short": "1 simple class with 1-2 basic methods (15-30 lines total)",
        "medium": "1 class with 3-5 methods of moderate complexity (40-80 lines total)",
        "long": "1-2 classes with 4-8 methods and clear relationships (100-150 lines total)"
    }.get(str(code_length).lower(), "1 class with methods")
    
    # Count the number of errors
    error_count = len(selected_errors)
    
    # Format errors concisely with language-aware field access
    current_lang = get_current_language()
    error_list = []
    for i, error in enumerate(selected_errors, 1):
        # Use language-specific field names based on current language
        if current_lang == 'zh':
            error_name = error.get('error_name_zh', error.get('error_name_en', "Unknown Error"))
            error_description = error.get('description_zh', error.get('description_en', ""))
        else:
            error_name = error.get('error_name_en', error.get('error_name_zh', "Unknown Error"))
            error_description = error.get('description_en', error.get('description_zh', ""))
        
        error_list.append(f"{i}. {error_name}: {error_description}")
    
    # Join errors with clear separation
    error_instructions = "\n\n".join(error_list)
    
    # Get language-specific difficulty instructions template
    if difficulty_level.lower() == t("easy"):
        difficulty_instructions = t("easy_difficulty_instructions")
    elif difficulty_level.lower() == t("medium"):
        difficulty_instructions = t("medium_difficulty_instructions")
    else:        
        difficulty_instructions = t("hard_difficulty_instructions")
    
    domain_str = domain or "general"
    
    # Get language-specific instructions
    language_instructions = get_llm_prompt_instructions(get_current_language())
    
    # Get language-specific template
    template = get_prompt_template("code_generation_template")
    
    # Create the prompt by filling in the template safely
    prompt = f"{language_instructions}. " + format_prompt_safely(
        template,
        code_length=code_length,
        domain_str=domain_str,
        error_count=error_count,
        complexity=complexity,
        difficulty_instructions=difficulty_instructions,
        error_instructions=error_instructions,
        difficulty_level=difficulty_level
    )

    return prompt

def create_evaluation_prompt(code: str, requested_errors: list) -> str:
    """
    Create a clear and concise prompt for evaluating whether code contains required errors.
    Improved with detailed evaluation criteria and structured output format.
    Now uses language-specific templates and database fields.
    
    Args:
        code: The code to evaluate
        requested_errors: List of errors that should be in the code
        
    Returns:
        Evaluation prompt string
    """
    # Count the exact number of requested errors
    error_count = len(requested_errors)
    
    # Format requested errors clearly with language-aware field access
    current_lang = get_current_language()
    error_list = []
    for i, error in enumerate(requested_errors, 1):
        # Use language-specific field names based on current language
        if current_lang == 'zh':
            error_name = error.get('error_name_zh', error.get('error_name_en', "Unknown Error"))
            error_description = error.get('description_zh', error.get('description_en', ""))
        else:
            error_name = error.get('error_name_en', error.get('error_name_zh', "Unknown Error"))
            error_description = error.get('description_en', error.get('description_zh', ""))
        
        error_list.append(f"{i}. {error_name}: {error_description}")

    error_instructions = "\n".join(error_list)

    # Get language-specific instructions
    language_instructions = get_llm_prompt_instructions(get_current_language())

    # Get language-specific template
    template = get_prompt_template("evaluation_template")
    
    # Create the prompt by filling in the template safely
    prompt = f"{language_instructions}. " + format_prompt_safely(
        template,
        code=add_line_numbers(code),
        error_count=error_count,
        error_instructions=error_instructions
    )
    
    return prompt

def create_regeneration_prompt(code: str, domain: str, missing_errors: list, found_errors: list, requested_errors: list) -> str:
    """
    Create a prompt for regenerating code with missing errors.
    Now uses language-specific templates based on current language.
    
    Args:
        code: The original code
        domain: Domain context for the code
        missing_errors: List of errors that need to be added
        found_errors: List of errors that were found and should be preserved
        requested_errors: List of all requested errors
        
    Returns:
        Regeneration prompt string
    """
    # Count the total number of errors that should be in the final code
    total_requested = len(requested_errors)
    
    # Format missing errors for prompt
    missing_text = ""
    if missing_errors:
        for i, error in enumerate(missing_errors, 1):
            error_type = error.get(t("category"), "").upper()
            name = error.get(t("error_name_variable"), "")
            description = error.get(t("description"), "")
            implementation_guide = error.get(t("implementation_guide"), "")
            
            missing_text += f"{i}. {error_type} - {name}: {description}\n"
            if implementation_guide:
                missing_text += f"   {t('implementation_guide')}: {implementation_guide}\n"
            missing_text += "\n"
    
    # Format found errors for prompt
    found_text = ""
    if found_errors:
        for i, error in enumerate(found_errors, 1):
            error_type = error.get(t("category"), "").upper()
            name = error.get(t("error_name_variable"), "")
            description = error.get(t("description"), "")
            
            found_text += f"{i}. {error_type} - {name}: {description}\n"
    
    # Get language-specific instructions
    language_instructions = get_llm_prompt_instructions(get_current_language())
    
    # Get language-specific template
    template = get_prompt_template("regeneration_template")
    
    # Create the prompt by filling in the template safely
    prompt = f"{language_instructions}. " + format_prompt_safely(
        template,
        total_requested=total_requested,
        domain=domain,
        missing_text=missing_text or t("no_missing_errors"),
        found_text=found_text or t("no_found_errors"),
        code=code
    )
    
    return prompt

def create_review_analysis_prompt(code: str, known_problems: list, student_review: str) -> str:
    """
    Create a prompt for analyzing a student's review against known problems.
    Now uses language-specific templates based on current language.
    
    Args:
        code: The code being reviewed
        known_problems: List of known problems in the code
        student_review: The student's review text
        
    Returns:
        Review analysis prompt string
    """
    # Count problems
    problem_count = len(known_problems)
    
    # Format problems for prompt
    problems_text = ""
    for i, problem in enumerate(known_problems, 1):
        problems_text += f"- {problem}\n"
    
    # Get evaluation thresholds from environment or use defaults
    meaningful_threshold = 0.6  # Default threshold
    accuracy_threshold = 0.7    # Default threshold
    
    # Get language-specific instructions
    language_instructions = get_llm_prompt_instructions(get_current_language())
    
    # Get language-specific template
    template = get_prompt_template("review_analysis_template")
    
    # Create the prompt by filling in the template safely
    prompt = f"{language_instructions}. " + format_prompt_safely(
        template,
        code=add_line_numbers(code),
        problem_count=problem_count,
        problems_text=problems_text,
        student_review=student_review,
        meaningful_score_threshold=meaningful_threshold,
        accuracy_score_threshold=accuracy_threshold
    )
    
    return prompt

def create_feedback_prompt(code: str, known_problems: list, review_analysis: dict) -> str:
    """
    Create a prompt for generating targeted feedback based on review analysis.
    Now uses language-specific templates based on current language.
    
    Args:
        code: The code being reviewed
        known_problems: List of known problems in the code
        review_analysis: Analysis results from the student's review
        
    Returns:
        Feedback prompt string
    """
    # Extract information from review analysis
    iteration = review_analysis.get(t("iteration_count"), 1)
    max_iterations = review_analysis.get(t("max_iterations"), 3)
    identified = review_analysis.get(t("identified_count"), 0)
    total = review_analysis.get(t("total_problems"), len(known_problems))
    remaining = max_iterations - iteration
    accuracy = (identified / total * 100) if total > 0 else 0
    
    # Format identified and missed issues
    identified_problems = review_analysis.get(t("identified_problems"), [])
    missed_problems = review_analysis.get(t("missed_problems"), [])
    
    identified_text = ""
    if identified_problems:
        for problem in identified_problems:
            problem_desc = problem.get(t("problem"), "")
            identified_text += f"- {problem_desc}\n"
    
    missed_text = ""
    if missed_problems:
        for problem in missed_problems:
            problem_desc = problem.get(t("problem"), "")
            identified_text += f"- {problem_desc}\n"
    
    # Get language-specific instructions
    language_instructions = get_llm_prompt_instructions(get_current_language())
    
    # Get language-specific template
    template = get_prompt_template("feedback_template")
    
    # Create the prompt by filling in the template safely
    prompt = f"{language_instructions}. " + format_prompt_safely(
        template,
        iteration=iteration,
        max_iterations=max_iterations,
        identified=identified,
        total=total,
        accuracy=accuracy,
        remaining=remaining,
        identified_text=identified_text or t("no_issues_identified"),
        missed_text=missed_text or t("no_issues_missed")
    )
    
    return prompt

def create_comparison_report_prompt(evaluation_errors: list, review_analysis: dict, review_history: list = None) -> str:
    """
    Create a prompt for generating a comparison report.
    Now uses language-specific templates based on current language.
    
    Args:
        evaluation_errors: List of errors found by evaluation
        review_analysis: Analysis of the latest review
        review_history: History of all review attempts
        
    Returns:
        Comparison report prompt string
    """
    # Extract metrics
    total_problems = len(evaluation_errors)
    identified_count = review_analysis.get(t("identified_count"), 0)
    accuracy = (identified_count / total_problems * 100) if total_problems > 0 else 0
    
    # Format identified and missed issues
    identified_problems = review_analysis.get(t("identified_problems"), [])
    missed_problems = review_analysis.get(t("missed_problems"), [])
    
    identified_text = ""
    if identified_problems:
        for problem in identified_problems:
            problem_desc = problem.get(t("problem"), "")
            identified_text += f"- {problem_desc}\n"
    
    missed_text = ""
    if missed_problems:
        for problem in missed_problems:
            problem_desc = problem.get(t("problem"), "")
            missed_text += f"- {problem_desc}\n"
    
    # Format progress info
    progress_info = ""
    if review_history and len(review_history) > 1:
        progress_info = f"This is attempt {len(review_history)} of the review process."
    
    # Get language-specific instructions
    language_instructions = get_llm_prompt_instructions(get_current_language())
    
    # Get language-specific template
    template = get_prompt_template("comparison_report_template")
    
    # Create the prompt by filling in the template safely
    prompt = f"{language_instructions}. " + format_prompt_safely(
        template,
        total_problems=total_problems,
        identified_count=identified_count,
        accuracy=accuracy,
        len_missed_str=len(missed_problems),
        identified_text=identified_text or t("no_issues_identified"),
        missed_text=missed_text or t("no_issues_missed"),
        progress_info=progress_info
    )
    
    return prompt

def extract_both_code_versions(response) -> Tuple[str, str]:
    """
    Extract both original and corrected code versions from LLM response.
    
    Args:
        response: LLM response containing code
        
    Returns:
        Tuple of (original_code, corrected_code)
    """
    try:
        response_text = str(response)
        
        # Try to find code blocks
        import re
        code_blocks = re.findall(r'```(?:java)?\s*(.*?)```', response_text, re.DOTALL)
        
        if len(code_blocks) >= 2:
            return code_blocks[0].strip(), code_blocks[1].strip()
        elif len(code_blocks) == 1:
            return code_blocks[0].strip(), ""
        else:
            return response_text, ""
            
    except Exception as e:
        logger.error(f"Error extracting code versions: {str(e)}")
        return "", ""

def process_llm_response(response) -> str:
    """
    Process and clean LLM response.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Processed response string
    """
    try:
        if hasattr(response, 'content'):
            return str(response.content).strip()
        else:
            return str(response).strip()
    except Exception as e:
        logger.error(f"Error processing LLM response: {str(e)}")
        return ""

def get_prompt_template(template_name: str) -> str:
    """
    Get a prompt template by name.
    
    Args:
        template_name: Name of the template
        
    Returns:
        Template string
    """
    templates = {
        "code_generation_template": """
Generate Java code with the following specifications:
- Code Length: {code_length}
- Domain: {domain_str} 
- Complexity: {complexity}
- Difficulty: {difficulty_level}
- Number of errors to include: {error_count}

Specific errors to implement:
{error_instructions}

{difficulty_instructions}

Please generate complete, compilable Java code that contains exactly {error_count} intentional errors as specified above.
        """,
        "evaluation_template": """
Evaluate the following Java code to determine if it contains the requested errors:

Code to evaluate:
{code}

Expected errors ({error_count} total):
{error_instructions}

Please analyze the code and return a JSON response indicating which errors are present and which are missing.
        """,
        "regeneration_template": """
Improve the following Java code to include the missing errors while preserving the found ones:

Current code:
{code}

Total errors needed: {total_requested}
Domain: {domain}

Missing errors to add:
{missing_text}

Found errors to preserve:
{found_text}

Please regenerate the code to include all required errors.
        """,
        "review_analysis_template": """
Analyze the student's review of the following Java code:

Code being reviewed:
{code}

Known problems ({problem_count} total):
{problems_text}

Student's review:
{student_review}

Please analyze how well the student identified the problems and provide scores for meaningfulness (>{meaningful_score_threshold}) and accuracy (>{accuracy_score_threshold}).
        """,
        "feedback_template": """
Generate targeted feedback for the student based on their review performance:

Iteration: {iteration}/{max_iterations}
Issues identified: {identified}/{total} ({accuracy:.1f}% accuracy)
Remaining attempts: {remaining}

Issues correctly identified:
{identified_text}

Issues missed:
{missed_text}

Provide encouraging, specific feedback to help the student improve.
        """,
        "comparison_report_template": """
Generate a comprehensive comparison report between expected errors and student's review:

Expected errors: {evaluation_errors}
Student identified: {identified_count}/{total_problems} ({accuracy:.1f}% accuracy)

Correctly identified:
{identified_text}

Missed issues:
{missed_text}

Progress information:
{progress_info}

Provide detailed educational feedback.
        """
    }
    
    return templates.get(template_name, "Template not found: {template_name}")

def format_prompt_safely(template: str, **kwargs) -> str:
    """
    Safely format a prompt template with provided arguments.
    
    Args:
        template: Template string with placeholders
        **kwargs: Arguments to fill in the template
        
    Returns:
        Formatted template string
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.warning(f"Missing template argument: {e}")
        return template
    except Exception as e:
        logger.error(f"Error formatting template: {str(e)}")
        return template