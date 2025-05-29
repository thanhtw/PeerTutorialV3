"""
Merged Error Selector and Generator UI for Java Peer Review Training System.

This module provides a combined interface for selecting Java error categories/specific errors
and generating code problems with the selected errors.
"""

import streamlit as st
import logging
import random
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
from utils.language_utils import t, get_current_language
from state_schema import WorkflowState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ErrorSelectorUI:
    """
    UI Component for selecting Java error categories.
    
    This class handles displaying and selecting Java error categories
    from java errors.
    """
    
    def __init__(self):
        """Initialize the ErrorSelectorUI component with empty selections."""
        # Track selected categories - initialize with empty collections if not in session state
        if "selected_error_categories" not in st.session_state:
            st.session_state.selected_error_categories = {
               "java_errors": []
            }
        elif not isinstance(st.session_state.selected_error_categories, dict):
            # Fix if it's not a proper dictionary
            st.session_state.selected_error_categories = {
                "java_errors": []
            }
        elif "java_errors" not in st.session_state.selected_error_categories:
            # Make sure java_errors key exists
            st.session_state.selected_error_categories["java_errors"] = []
        
        # Track error selection mode
        if "error_selection_mode" not in st.session_state:
            st.session_state.error_selection_mode = "advanced"
        
        # Track expanded categories
        if "expanded_categories" not in st.session_state:
            st.session_state.expanded_categories = {}
            
        # Track selected specific errors - initialize as empty list
        if "selected_specific_errors" not in st.session_state:
            st.session_state.selected_specific_errors = []
    
    def render_category_selection(self, all_categories: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Render the error category selection UI for advanced mode with enhanced styling and layout.
        Each error category from database is displayed as a visually distinct card.
        Uses database fields based on current language.
        
        Args:
            all_categories: Dictionary with 'java_errors' categories from database
            
        Returns:
            Dictionary with selected categories
        """
        # Enhanced header with professional styling
        st.markdown("""
        <div class="section-header">
            <span class="section-icon">🎯</span>
            <div>
                <h3 class="section-title">""" + t("select_error_categories") + """</h3>
                <p class="section-subtitle">""" + t("choose_categories_for_practice") + """</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced help section
        st.markdown(f"""
        <div class="selection-help">
            <span class="selection-help-icon">💡</span>
            <strong>{t("advanced_mode_help")}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        java_error_categories = all_categories.get("java_errors", [])
        
        # Ensure the session state structure is correct
        if "selected_error_categories" not in st.session_state:
            st.session_state.selected_error_categories = {"java_errors": []}
        if "java_errors" not in st.session_state.selected_error_categories:
            st.session_state.selected_error_categories["java_errors"] = []
        
        # Get the current selection state from session
        current_selections = st.session_state.selected_error_categories.get("java_errors", [])
        
        # Enhanced grid layout for categories
        st.markdown('<div class="problem-area-grid-enhanced">', unsafe_allow_html=True)
        
        # Get current language for database field selection
        current_lang = get_current_language()
        
        # Define category icons for visual appeal (fallback for missing database icons)
        default_category_icons = {
            "Logical": "🧠", "Logical Errors": "🧠", "邏輯錯誤": "🧠",
            "Syntax": "🔍", "Syntax Errors": "🔍", "語法錯誤": "🔍",
            "Code Quality": "✨", "Code Quality Issues": "✨", "程式碼品質": "✨",
            "Standard Violation": "📏", "Standard Violations": "📏", "標準違規": "📏",
            "Java Specific": "☕", "Java-Specific": "☕", "Java特定錯誤": "☕"
        }
        
        # Generate enhanced cards for each category from database
        for i, category_data in enumerate(java_error_categories):
            # Create a unique and safe key for this category
            category_key = f"java_category_{i}"
            
            # Extract category information from database based on language
            if isinstance(category_data, dict):
                # If category_data is a dict with language-specific fields
                if current_lang == 'zh':
                    category_name = category_data.get('name_zh', category_data.get('name_en', 'Unknown'))
                    category_desc = category_data.get('description_zh', category_data.get('description_en', ''))
                else:
                    category_name = category_data.get('name_en', category_data.get('name_zh', 'Unknown'))
                    category_desc = category_data.get('description_en', category_data.get('description_zh', ''))
                
                category_code = category_data.get('category_code', category_name)
                icon = category_data.get('icon', default_category_icons.get(category_name, "📁"))
            else:
                # Fallback for string category names
                category_name = str(category_data)
                category_code = category_name
                category_desc = t("error_category")
                icon = default_category_icons.get(category_name, "📁")
            
            # Check if category is already selected from session state
            is_selected = category_code in current_selections
            
            # Create enhanced card with professional styling
            selected_class = "selected" if is_selected else ""
            st.markdown(f"""
            <div class="problem-area-card-enhanced {selected_class}" id="{category_key}_card" 
                onclick="this.classList.toggle('selected'); 
                        document.getElementById('{category_key}_checkbox').click();">
                <div class="problem-area-header">
                    <div class="problem-area-title-enhanced">
                        <span class="problem-area-icon">{icon}</span>
                        <span>{category_name}</span>
                    </div>
                    <div class="selection-indicator">{'✓' if is_selected else ''}</div>
                </div>
                <p class="problem-area-description-enhanced">{category_desc}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Hidden checkbox to track state
            selected = st.checkbox(
                f"Category {i}",
                key=category_key,
                value=is_selected,
                label_visibility="collapsed"
            )
            
            # Update selection state based on checkbox
            if selected:
                if category_code not in current_selections:
                    current_selections.append(category_code)
            else:
                if category_code in current_selections:
                    current_selections.remove(category_code)
        
        # Close the grid container
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Enhanced selection summary
        st.markdown(f"""
        <div class="selected-categories-enhanced">
            <div class="selected-categories-header">
                <h4>{t("selected_categories")}</h4>
                <span class="selected-categories-count">{len(current_selections)}</span>
            </div>
        """, unsafe_allow_html=True)
        
        if not current_selections:
            st.markdown(f"""
            <div class="no-selection-message">
                <strong>⚠️ {t("no_categories")}</strong><br>
                <small>{t("please_select_at_least_one_category")}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display selected categories with enhanced styling
            st.markdown('<div class="selected-categories-list">', unsafe_allow_html=True)
            for i, category_code in enumerate(current_selections):
                # Find the category data for display
                category_display_name = category_code
                icon = "📁"
                
                for category_data in java_error_categories:
                    if isinstance(category_data, dict):
                        if category_data.get('category_code') == category_code:
                            if current_lang == 'zh':
                                category_display_name = category_data.get('name_zh', category_data.get('name_en', category_code))
                            else:
                                category_display_name = category_data.get('name_en', category_data.get('name_zh', category_code))
                            icon = category_data.get('icon', default_category_icons.get(category_display_name, "📁"))
                            break
                    elif str(category_data) == category_code:
                        category_display_name = category_code
                        icon = default_category_icons.get(category_code, "📁")
                        break
                
                st.markdown(f"""
                <div class="selected-category-tag">
                    <span class="category-tag-icon">{icon}</span>
                    <span>{category_display_name}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Update selections in session state
        st.session_state.selected_error_categories["java_errors"] = current_selections
        
        return st.session_state.selected_error_categories
    
    def render_specific_error_selection(self, error_repository) -> List[Dict[str, Any]]:
        """
        Render UI for selecting specific errors to include in generated code.
        Each group in Java_code_review_errors.json is displayed as a tab.
        
        Args:
            error_repository: Repository for accessing Java error data
            
        Returns:
            List of selected specific errors
        """
        st.subheader(t("select_specific_errors"))
        
        # Get all categories
        all_categories = error_repository.get_all_categories()
        java_error_categories = all_categories.get("java_errors", [])
        
        # Container for selected errors
        if "selected_specific_errors" not in st.session_state:
            st.session_state.selected_specific_errors = []
            
        # Check if there are any categories to display
        if not java_error_categories:
            st.warning("No error categories found. Please check that the error repository is properly configured.")
            return st.session_state.selected_specific_errors
            
        # Create tabs for each error category
        error_tabs = st.tabs(java_error_categories)

        # For each category tab
        for i, category in enumerate(java_error_categories):
            with error_tabs[i]:
                # Get errors for this category
                errors = error_repository.get_category_errors(category)
                if not errors:
                    st.info(f"{t('no_errors_found')} {category} {t('category')}.")
                    continue
                    
                # Display each error with a select button
                for j, error in enumerate(errors):
                    # Handle potential missing field names
                    error_name = error.get(t("error_name_variable"), "Unknown")
                    description = error.get(t("description"), "")
                    
                    # Check if already selected
                    is_selected = any(
                        e[t("error_name_variable")] == error_name and e[t("category")] == category
                        for e in st.session_state.selected_specific_errors
                    )
                    
                    # Add select button with an index to ensure unique keys
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(f"**{error_name}**")
                        st.markdown(f"*{description}*")
                    with col2:
                        if not is_selected:
                            # Add indices to ensure key uniqueness
                            unique_key = f"select_{i}_{j}_{category}"
                            if st.button(t("select"), key=unique_key):
                                st.session_state.selected_specific_errors.append({                                   
                                    t("category"): category,
                                    t("error_name_variable"): error_name,
                                    t("description"): description,
                                    t("implementation_guide"): error.get(t("implementation_guide"), "")
                                })
                                st.rerun()
                        else:
                            # Just display "Selected" text without a button
                            st.success(t("selected"))
                    
                    st.markdown("---")
        
        # Show selected errors
        st.subheader(t("selected_issues"))
        
        if not st.session_state.selected_specific_errors:
            st.info(t("no_specific_issues"))
        else:
            for idx, error in enumerate(st.session_state.selected_specific_errors):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{error[t('category')]} - {error[t('error_name_variable')]}**")
                    st.markdown(f"*{error[t('description')]}*")
                with col2:
                    # Use numerical index only to avoid potential issues with Chinese characters in keys
                    remove_key = f"remove_{idx}"
                    if st.button(t("remove"), key=remove_key):
                        st.session_state.selected_specific_errors.pop(idx)
                        st.rerun()
        
        return st.session_state.selected_specific_errors
        
    def render_mode_selector(self) -> str:
        """
        Render the enhanced mode selector UI with professional styling.
        
        Returns:
            Selected mode ("advanced" or "specific")
        """
        st.markdown(f"""
        <div class="mode-selector-container">
            <div class="mode-selector-header">
                <h4>🎯 {t("error_selection_mode")}</h4>
                <p>{t("choose_how_to_select_errors")}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Get current mode
        current_mode = st.session_state.error_selection_mode
        
        # Create enhanced mode selection
        col1, col2 = st.columns(2)
        
        with col1:
            advanced_selected = "selected" if current_mode == "advanced" else ""
            if st.button("", key="advanced_mode_btn", help=t("advanced_mode_description")):
                st.session_state.error_selection_mode = "advanced"
                st.rerun()
            
            # Display mode option with enhanced styling
            st.markdown(f"""
            <div class="mode-option {advanced_selected}" onclick="document.getElementById('advanced_mode_btn').click();">
                <span class="mode-option-icon">🎯</span>
                <h5 class="mode-option-title">{t("advanced_mode")}</h5>
                <p class="mode-option-description">{t("select_error_categories")}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            specific_selected = "selected" if current_mode == "specific" else ""
            if st.button("", key="specific_mode_btn", help=t("specific_mode_description")):
                st.session_state.error_selection_mode = "specific"
                st.rerun()
            
            # Display mode option with enhanced styling
            st.markdown(f"""
            <div class="mode-option {specific_selected}" onclick="document.getElementById('specific_mode_btn').click();">
                <span class="mode-option-icon">🔍</span>
                <h5 class="mode-option-title">{t("specific_mode")}</h5>
                <p class="mode-option-description">{t("select_specific_errors")}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return st.session_state.error_selection_mode
    
    def get_code_params_for_level(self, user_level: str = None) -> Dict[str, str]:
        """
        Get code generation parameters based on user level stored in session state.
        
        Args:
            user_level: Fallback user level if not found in session state
            
        Returns:
            Dictionary with difficulty_level and code_length parameters
        """
        # First check if user level is in session state
        level_from_session = st.session_state.get("user_level", None)
        
        
        # Set appropriate difficulty based on normalized user level
        difficulty_mapping = {
            t("basic"): f"{t('easy')}",
            t("medium"): f"{t('medium')}",
            t("senior"): f"{t('hard')}"
        }
        difficulty_level = difficulty_mapping.get(level_from_session, f"{t('medium')}")
        
        # Set code length based on difficulty
        length_mapping = {
        f"{t('easy')}": f"{t('short')}",
        f"{t('medium')}": f"{t('medium')}",
        f"{t('hard')}": f"{t('long')}"
        }
        code_length = length_mapping.get(difficulty_level, f"{t('medium')}")
    
        # Update session state for consistency
        st.session_state.difficulty_level = difficulty_level.capitalize()
        st.session_state.code_length = code_length.capitalize()
        
        return {
            "difficulty_level": difficulty_level,
            "code_length": code_length
        }


def generate_code_problem(workflow, 
                        params: Dict[str, str], 
                        error_selection_mode: str,
                        selected_error_categories: Dict[str, List[str]],
                        selected_specific_errors: List[Dict[str, Any]] = None):
    """Generate a code problem with progress indicator and evaluation visualization."""
    try:
        # Initialize workflow steps
        if 'workflow_steps' not in st.session_state:
            st.session_state.workflow_steps = []
        
        # Reset and start tracking steps
        st.session_state.workflow_steps = [t("step1")]
        
        # Initialize state and parameters
        state = st.session_state.workflow_state
        code_length = str(params.get("code_length", "medium"))
        difficulty_level = str(params.get("difficulty_level", "medium"))
        state.code_length = code_length
        state.difficulty_level = difficulty_level
        
        # Verify we have error selections based on mode
        has_selections = False
        if error_selection_mode == "specific" and selected_specific_errors:
            has_selections = len(selected_specific_errors) > 0
            # Update state with specific errors
            state.selected_specific_errors = selected_specific_errors
            # Clear categories for this mode
            state.selected_error_categories = {"java_errors": []}
        elif error_selection_mode in ["standard", "advanced"]:
            java_errors_selected = selected_error_categories.get("java_errors", [])
            has_selections = len(java_errors_selected) > 0
            # Update state with selected categories
            state.selected_error_categories = selected_error_categories
            # Clear specific errors in this mode
            state.selected_specific_errors = []
        
        if not has_selections:
            st.error(t("no_categories"))
            return False
        
        # First stage: Generate initial code
        with st.status(t("step1"), expanded=True) as status:           
            state.current_step = "generate"
            state.evaluation_attempts = 0
            updated_state = workflow.generate_code_node(state)
            st.session_state.workflow_steps.append(t("step1"))
            
            # Important: Update the session state immediately after code generation
            st.session_state.workflow_state = updated_state
            
            if updated_state.error:
                st.error(f"Error: {updated_state.error}")
                return False
        
        # Second stage: Display the evaluation process
        st.info(t("step2"))
        
        # Create a process visualization using columns and containers instead of expanders
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(t("code_generation_process"))
            
            # Create a progress container
            progress_container = st.container()
            with progress_container:
                # Create a progress bar
                progress_bar = st.progress(0.25)
                st.write(f"**{t('step1')}** {t('generating_code')}")
                
                # Evaluate the code
                with st.status(t("step2"), expanded=False):
                    updated_state.current_step = "evaluate"
                    updated_state = workflow.evaluate_code_node(updated_state)
                    # Update session state after each step
                    st.session_state.workflow_state = updated_state
                    st.session_state.workflow_steps.append(t("step2"))
                
                progress_bar.progress(0.5)
                st.write(f"**{t('step2')}** {t('completed')}")
                
                # Show evaluation results
                if hasattr(updated_state, 'evaluation_result') and updated_state.evaluation_result:
                    found = len(updated_state.evaluation_result.get("found_errors", []))
                    missing = len(updated_state.evaluation_result.get("missing_errors", []))
                    total = found + missing
                    if total == 0:
                        total = 1  # Avoid division by zero
                    
                    quality_percentage = (found / total * 100)
                    st.write(f"**{t('quality')}:** {quality_percentage:.1f}%: {found}/{total} {t('errors_found')}")
                    
                    # Regeneration cycle if needed
                    if missing > 0 and workflow.should_regenerate_or_review(updated_state) == "regenerate_code":
                        st.write(f"**{t('step3')}** {t('improving_code')}")
                        
                        attempt = 1
                        max_attempts = getattr(updated_state, 'max_evaluation_attempts', 3)
                        previous_found = found
                        
                        # Loop through regeneration attempts
                        while (attempt < max_attempts and 
                              workflow.should_regenerate_or_review(updated_state) == "regenerate_code"):
                            progress_value = 0.5 + (0.5 * (attempt / max_attempts))
                            progress_bar.progress(progress_value)
                            
                            # Regenerate code
                            with st.status(f"{t('step3')} ({attempt+1}/{max_attempts})...", expanded=False):
                                updated_state.current_step = "regenerate"
                                updated_state = workflow.regenerate_code_node(updated_state)
                                # Update session state after code regeneration
                                st.session_state.workflow_state = updated_state
                                st.session_state.workflow_steps.append(f"{t('step3')} ({attempt+1})")
                            
                            # Re-evaluate code
                            with st.status(t("reevaluating_code"), expanded=False):
                                updated_state.current_step = "evaluate"
                                updated_state = workflow.evaluate_code_node(updated_state)
                                # Update session state after evaluation
                                st.session_state.workflow_state = updated_state
                                st.session_state.workflow_steps.append(t("reevaluating_code"))
                            
                            # Show updated results
                            if hasattr(updated_state, 'evaluation_result'):
                                new_found = len(updated_state.evaluation_result.get("found_errors", []))
                                new_missing = len(updated_state.evaluation_result.get("missing_errors", []))
                                
                                st.write(f"**{t('quality')} {attempt+1}:** {new_found/total*100:.1f}%: {new_found}/{total} {t('errors_found')}")
                                
                                if new_found > previous_found:
                                    st.success(f"✅ {t('added')} {new_found - previous_found} {t('new_errors')}")
                                    
                                previous_found = new_found
                            
                            # Increment the attempt counter
                            attempt += 1
                            updated_state.evaluation_attempts = attempt
                            # Make sure to update session state with the new attempt count
                            st.session_state.workflow_state = updated_state
                    
                    # Complete the progress
                    progress_bar.progress(1.0)
                    
                    # Show final outcome
                    if quality_percentage == 100:
                        st.success(f"✅ {t('all_errors_implemented')}")
                    elif quality_percentage >= 80:
                        st.success(f"✅ {t('good_quality')} {quality_percentage:.1f}%")
                    else:
                        st.warning(f"⚠️ {t('partial_quality')} {quality_percentage:.1f}%")
                
        with col2:
            # Show statistics in the sidebar
            st.subheader(t("generation_stats"))
            
            if hasattr(updated_state, 'evaluation_result') and updated_state.evaluation_result:
                found = len(updated_state.evaluation_result.get("found_errors", []))
                missing = len(updated_state.evaluation_result.get("missing_errors", []))
                total = found + missing
                if total > 0:
                    quality_percentage = (found / total * 100)
                    st.metric(t("quality"), f"{quality_percentage:.1f}%")
                
                st.metric(t("errors_found"), f"{found}/{total}")
                
                if hasattr(updated_state, 'evaluation_attempts'):
                    st.metric(t("generation_attempts"), updated_state.evaluation_attempts)
        
        # Update session state with completed process
        updated_state.current_step = "review"
        st.session_state.workflow_state = updated_state
        st.session_state.active_tab = 1  # Move to the review tab
        st.session_state.error = None
        st.session_state.workflow_steps.append(t("code_generation_completed"))
        
        # Display the generated code
        if hasattr(updated_state, 'code_snippet') and updated_state.code_snippet:
            # Show the generated code in this tab for immediate feedback
            st.subheader(t("generated_java_code"))
            
            code_to_display = None
            if hasattr(updated_state.code_snippet, 'clean_code') and updated_state.code_snippet.clean_code:
                code_to_display = updated_state.code_snippet.clean_code
            elif hasattr(updated_state.code_snippet, 'code') and updated_state.code_snippet.code:
                code_to_display = updated_state.code_snippet.code
                
            if code_to_display:
                st.code(code_to_display, language="java")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating code problem: {str(e)}")
        import traceback
        traceback.print_exc()
        st.error(f"Error generating code problem: {str(e)}")
        return False


def show_workflow_process():
    """Show a visual representation of the workflow process with improved styling."""
    # Check if we have the necessary state information
    if not hasattr(st.session_state, 'workflow_state'):
        return
    
    state = st.session_state.workflow_state
    
    # Get the current step and evaluation attempts
    current_step = getattr(state, 'current_step', 'generate')
    evaluation_attempts = getattr(state, 'evaluation_attempts', 0)
    max_evaluation_attempts = getattr(state, 'max_evaluation_attempts', 3)
    
    # Create a workflow visualization with improved style
    
    st.subheader(t("code_generation_process"))
    
    st.markdown('<div class="workflow-container">', unsafe_allow_html=True)
    
    # Create columns for the process steps
    cols = st.columns(4)
    
    # Step 1: Generate Code - Always completed if we're showing workflow
    with cols[0]:
        st.markdown(f"<div class='workflow-step step-completed'>{t('step1')}</div>", unsafe_allow_html=True)
    
    # Step 2: Evaluate Code
    with cols[1]:
        evaluate_style = "step-completed" if current_step in ['evaluate', 'regenerate', 'review'] else "step-pending"
        st.markdown(f"<div class='workflow-step {evaluate_style}'>{t('step2')}</div>", unsafe_allow_html=True)
    
    # Step 3: Regenerate
    with cols[2]:
        # Set the text for regeneration step
        if evaluation_attempts > 0:
            regenerate_text = f"{t('step3')} ({evaluation_attempts} {t('attempts')})"
            regenerate_style = "step-completed"
        else:
            regenerate_text = t("step3")
            regenerate_style = "step-pending"
        
        # Set active class if this is the current step
        if current_step == 'regenerate':
            regenerate_style = "step-active"
            
        st.markdown(f"<div class='workflow-step {regenerate_style}'>{regenerate_text}</div>", unsafe_allow_html=True)
    
    # Step 4: Ready for Review
    with cols[3]:
        review_style = "step-active" if current_step == 'review' else "step-pending"
        st.markdown(f"<div class='workflow-step {review_style}'>{t('step4')}</div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show process details in an expander
    with st.expander(t("process_details"), expanded=False):
        if hasattr(st.session_state, 'workflow_steps') and st.session_state.workflow_steps:
            for i, step in enumerate(st.session_state.workflow_steps, 1):
                st.markdown(f"{i}. {step}")
        else:
            st.write(t("no_process_details"))

    # If we have evaluation results, show a summary card
    if (hasattr(state, 'evaluation_result') and state.evaluation_result and 
        'found_errors' in state.evaluation_result):
        
        found = len(state.evaluation_result.get("found_errors", []))
        missing = len(state.evaluation_result.get("missing_errors", []))
        total = found + missing
        if total > 0:
            quality_percentage = (found / total * 100)
            
            # Generate color based on quality percentage
            if quality_percentage >= 80:
                color = "#28a745"  # Green for good quality
                icon = "✅"
            elif quality_percentage >= 60:
                color = "#ffc107"  # Yellow for medium quality
                icon = "⚠️"
            else:
                color = "#dc3545"  # Red for low quality
                icon = "❌"
                
            st.markdown(f"""
            <div style="background-color: rgba({color.replace('#', '')}, 0.1); 
                        border-left: 4px solid {color}; 
                        padding: 15px; margin: 15px 0; border-radius: 5px;">
                <div style="display: flex; align-items: center;">
                    <div style="font-size: 24px; margin-right: 15px;">{icon}</div>
                    <div>
                        <div style="font-weight: 500; font-size: 1.1rem;">{t("code_quality")}: {quality_percentage:.1f}%</div>
                        <div>{t("found")} {found} {t("of")} {total} {t("requested_errors")}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_generate_tab(workflow, error_selector_ui, code_display_ui, user_level=None):
    """
    Render the problem generation tab with enhanced professional styling.
    
    Args:
        workflow: JavaCodeReviewGraph workflow
        error_selector_ui: ErrorSelectorUI instance
        code_display_ui: CodeDisplayUI instance
        user_level: Optional user level from authentication (basic, medium, senior)
    """
    # Enhanced tab container
    st.markdown('<div class="generate-tab-container">', unsafe_allow_html=True)
    
    # Enhanced header
    st.markdown(f"""
    <div class="generate-header">
        <h2>🚀 {t("generate_problem")}</h2>
        <p>{t("create_java_code_with_errors_for_review_practice")}</p>
    </div>
    """, unsafe_allow_html=True)

    force_regenerate = st.session_state.get("force_regeneration", False)

    if force_regenerate:
        st.session_state.force_regeneration = False
        st.info(t("starting_new_session"))
    
    # Initialize workflow steps if not present
    if not hasattr(st.session_state, 'workflow_steps'):
        st.session_state.workflow_steps = []
    
    # If we already have a code snippet, show the workflow process
    if hasattr(st.session_state, 'workflow_state') and hasattr(st.session_state.workflow_state, 'code_snippet') and st.session_state.workflow_state.code_snippet:
        # Enhanced workflow display
        st.markdown('<div class="workflow-display-enhanced">', unsafe_allow_html=True)
        show_workflow_process()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Enhanced code display section
        st.markdown(f"""
        <div class="generate-section">
            <div class="section-header">
                <span class="section-icon">💻</span>
                <div>
                    <h3 class="section-title">{t("generated_java_code")}</h3>
                    <p class="section-subtitle">{t("review_the_generated_code_below")}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Get known problems from multiple sources to ensure we have data for instructor view
        known_problems = []
        
        # First, try to get problems from evaluation_result['found_errors']
        if (hasattr(st.session_state.workflow_state, 'evaluation_result') and 
            st.session_state.workflow_state.evaluation_result and 
            'found_errors' in st.session_state.workflow_state.evaluation_result):
            found_errors = st.session_state.workflow_state.evaluation_result.get('found_errors', [])
            if found_errors:
                known_problems = found_errors
        
        # If we couldn't get known problems from evaluation, try to get from selected errors
        if not known_problems and hasattr(st.session_state.workflow_state, 'selected_specific_errors'):
            selected_errors = st.session_state.workflow_state.selected_specific_errors
            if selected_errors:
                # Format selected errors to match expected format
                known_problems = [
                    f"{error.get('type', '').upper()} - {error.get('name', '')}" 
                    for error in selected_errors
                ]
        
        # As a last resort, try to extract from raw_errors in code_snippet
        if not known_problems and hasattr(st.session_state.workflow_state.code_snippet, 'raw_errors'):
            raw_errors = st.session_state.workflow_state.code_snippet.raw_errors
            if isinstance(raw_errors, dict):
                for error_type, errors in raw_errors.items():
                    for error in errors:
                        if isinstance(error, dict):
                            error_type_str = error.get('type', error_type).upper()
                            error_name = error.get(t('error_name_variable'), error.get(t('error_name_variable'), error.get('check_name', 'Unknown')))
                            known_problems.append(f"{error_type_str} - {error_name}")
        
        # Always pass known_problems, the render_code_display function will handle showing
        # the instructor view based on session state and checkbox status
        code_display_ui.render_code_display(
            st.session_state.workflow_state.code_snippet,
            known_problems=known_problems
        )
        
        # Enhanced regenerate button
        st.markdown(f"""
        <div class="generate-button-section">
            <h4>🔄 {t("generate_new_problem")}</h4>
            <p>{t("create_different_code_problem")}</p>
        """, unsafe_allow_html=True)
        
        if st.button("", key="regenerate_btn"):
            # Store items we want to preserve
            preserved_keys = ["auth", "provider_selection", "user_level", "language"]
            
            # Back up preserved values
            preserved_values = {}
            for key in preserved_keys:
                if key in st.session_state:
                    preserved_values[key] = st.session_state[key]
            
            # Perform a mini-reset: Remove workflow state and process details
            workflow_related_keys = ["workflow_state", "workflow_steps", "code_snippet", 
                           "error", "feedback_tab_switch_attempted", 
                           "evaluation_result", "comparison_report",
                           "error_selection_mode", "selected_error_categories", 
                           "selected_specific_errors"]
            
            # Clear specific workflow-related keys but keep others
            for key in workflow_related_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Restore preserved values
            for key, value in preserved_values.items():
                st.session_state[key] = value

            # Initialize a fresh workflow state
            st.session_state.workflow_state = WorkflowState()

            # Initialize empty workflow steps
            st.session_state.workflow_steps = []

            # Reset error selection to default (advanced mode)
            st.session_state.error_selection_mode = "advanced"
            st.session_state.selected_error_categories = {"java_errors": []}
            st.session_state.selected_specific_errors = []

            # Keep us on the generate tab
            st.session_state.active_tab = 0
            # Rerun to update UI
            st.rerun()
            
        st.markdown(f"""
        <div class="generate-button-enhanced" onclick="document.getElementById('regenerate_btn').click();">
            <div class="generate-button-text">
                <span class="generate-button-icon">🔄</span>
                <span>{t("generate_new")}</span>
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Enhanced mode selection section
        st.markdown(f'<div class="generate-section">', unsafe_allow_html=True)
        selection_mode = error_selector_ui.render_mode_selector()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Enhanced parameters display section
        st.markdown(f"""
        <div class="generate-section">
            <div class="section-header">
                <span class="section-icon">⚙️</span>
                <div>
                    <h3 class="section-title">{t("generation_parameters")}</h3>
                    <p class="section-subtitle">{t("auto_configured_based_on_level")}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Set parameters automatically based on user level (no UI controls)
        params = error_selector_ui.get_code_params_for_level(user_level)
        
        # Show the auto-set parameters with enhanced styling
        difficulty_level = params["difficulty_level"].capitalize()
        code_length = params["code_length"].capitalize()
        
        st.markdown(f"""
        <div class="parameters-display">
            <div class="parameters-header">
                <h4>📊 {t("code_parameters")}</h4>
            </div>
            <div class="parameters-grid">
                <div class="parameter-card">
                    <span class="parameter-icon">🎯</span>
                    <p class="parameter-label">{t("difficulty")}</p>
                    <h4 class="parameter-value">{difficulty_level}</h4>
                </div>
                <div class="parameter-card">
                    <span class="parameter-icon">📏</span>
                    <p class="parameter-label">{t("code_length")}</p>
                    <h4 class="parameter-value">{code_length}</h4>
                </div>
            </div>
            <div class="parameters-note">
                💡 {t("params_based_on_level")} ({user_level or 'medium'})
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced error selection section
        st.markdown(f"""
        <div class="category-selection-enhanced">
            <div class="section-header">
                <span class="section-icon">🎯</span>
                <div>
                    <h3 class="section-title">{t("error_selection")}</h3>
                    <p class="section-subtitle">{t("choose_errors_to_include")}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        all_categories = workflow.get_all_error_categories()
        
        if selection_mode == "advanced":
            # Advanced mode - select categories
            selected_categories = error_selector_ui.render_category_selection(all_categories)
            specific_errors = []
        else:
            # Specific mode - select specific errors
            specific_errors = error_selector_ui.render_specific_error_selection(workflow.error_repository)
            # Initialize empty categories for this mode
            selected_categories = {"java_errors": []}
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Enhanced generate button section
        st.markdown(f"""
        <div class="generate-button-section">
            <h4>🚀 {t("ready_to_generate")}</h4>
            <p>{t("click_below_to_create_java_code")}</p>
        """, unsafe_allow_html=True)
        
        if st.button("", key="generate_code_btn"):
            # Reset workflow steps for a fresh generation
            st.session_state.workflow_steps = [f"{t('start_process')}"]
            
            # Store parameters in state for generation
            if hasattr(st.session_state, 'workflow_state'):
                # Set basic parameters
                st.session_state.workflow_state.code_length = params["code_length"]
                st.session_state.workflow_state.difficulty_level = params["difficulty_level"]
                
                # Set selection based on mode
                if selection_mode == "advanced":
                    st.session_state.workflow_state.selected_error_categories = selected_categories
                    st.session_state.workflow_state.selected_specific_errors = []
                else:
                    st.session_state.workflow_state.selected_error_categories = {"java_errors": []}
                    st.session_state.workflow_state.selected_specific_errors = specific_errors
                
                # Initialize generation state
                st.session_state.workflow_state.current_step = "generate"
                st.session_state.workflow_state.evaluation_attempts = 0
                
                try:
                    # Run the full generate-evaluate-regenerate workflow
                    with st.spinner(t("generating_code")):
                        # Step 1: Generate initial code
                        state = workflow.generate_code_node(st.session_state.workflow_state)
                        st.session_state.workflow_steps.append(t("generated_initial_code"))
                        
                        if state.error:
                            st.error(f"Error: {state.error}")
                            return
                        
                        # Step 2: Evaluate code
                        st.session_state.workflow_state = state  # Update state
                        status_placeholder = st.empty()
                        status_placeholder.info(t("evaluating_code"))
                        state = workflow.evaluate_code_node(state)
                        st.session_state.workflow_steps.append(t("evaluated_code"))
                        
                        if state.error:
                            st.error(f"Error: {state.error}")
                            return
                        
                        # Step 3: Regenerate if needed
                        evaluation_attempts = 1
                        max_attempts = state.max_evaluation_attempts
                        
                        # Loop for regeneration attempts
                        while evaluation_attempts < max_attempts and workflow.should_regenerate_or_review(state) == "regenerate_code":
                            # Update steps and status
                            st.session_state.workflow_steps.append(f"{t('regenerating_code')} ({evaluation_attempts})")
                            status_placeholder.warning(f"{t('regenerating_code')} ({evaluation_attempts}/{max_attempts})...")
                            
                            # Regenerate code
                            state.current_step = "regenerate"
                            state = workflow.regenerate_code_node(state)
                            
                            if state.error:
                                st.error(f"Error: {state.error}")
                                return
                                
                            # Re-evaluate code
                            st.session_state.workflow_steps.append(t("reevaluated_code"))
                            status_placeholder.info(t("reevaluating_code"))
                            state = workflow.evaluate_code_node(state)
                            
                            if state.error:
                                st.error(f"Error: {state.error}")
                                return
                                
                            # Increment attempt counter
                            evaluation_attempts += 1
                        
                        # Update state and finalize
                        state.current_step = "review"
                        state.evaluation_attempts = evaluation_attempts
                        st.session_state.workflow_state = state
                        st.session_state.workflow_steps.append(t("code_generation_completed"))
                        
                        # Move to review tab
                        st.session_state.active_tab = 1
                        status_placeholder.success(t("code_generation_complete"))
                        
                        # Force UI refresh
                        st.rerun()
                        
                except Exception as e:
                    logger.error(f"Error in workflow: {str(e)}", exc_info=True)
                    st.session_state.workflow_steps.append(f"Error in code generation: {str(e)}")
                    st.error(f"Error: {str(e)}")
            else:
                # If workflow state doesn't exist yet
                st.error(t("workflow_not_initialized"))
        
        # Enhanced generate button display
        st.markdown(f"""
        <div class="generate-button-enhanced" onclick="document.getElementById('generate_code_btn').click();">
            <div class="generate-button-text">
                <span class="generate-button-icon">🚀</span>
                <span>{t("generate_code_button")}</span>
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Close tab container
    st.markdown('</div>', unsafe_allow_html=True)

# Usage example:
class CodeGeneratorUI:
    """
    Comprehensive UI for the Java Code Review training system's generation tab.
    Combines error selection and code generation in one component.
    """
    
    def __init__(self, workflow, code_display_ui=None):
        """
        Initialize the CodeGeneratorUI.
        
        Args:
            workflow: JavaCodeReviewGraph workflow
            code_display_ui: Optional CodeDisplayUI instance for displaying code
        """
        self.workflow = workflow
        self.error_selector = ErrorSelectorUI()
        self.code_display_ui = code_display_ui
    
    def render(self, user_level=None):
        """
        Render the full code generator UI including error selection and code generation.
        
        Args:
            user_level: Optional user level from authentication (basic, medium, senior)
        """
        # Remove the tutorial check - allow direct access to code generation
        render_generate_tab(self.workflow, self.error_selector, self.code_display_ui, user_level)
    
    def generate_code(self, params, error_selection_mode, selected_categories, selected_specific_errors=None):
        """
        Programmatically generate code with selected errors.
        
        Args:
            params: Code generation parameters
            error_selection_mode: Mode for error selection
            selected_categories: Selected error categories
            selected_specific_errors: Selected specific errors
            
        Returns:
            bool: True if generation succeeded, False otherwise
        """
        return generate_code_problem(
            self.workflow, 
            params, 
            error_selection_mode, 
            selected_categories, 
            selected_specific_errors
        )