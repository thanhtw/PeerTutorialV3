# ui/components/error_explorer_ui.py - Enhanced version

import streamlit as st
import os
import logging
import time
from typing import Dict, List, Any, Optional
from data.database_error_repository import DatabaseErrorRepository
from utils.language_utils import t, get_current_language
from static.css_utils import load_css
from utils.code_utils import _get_category_icon, _get_difficulty_icon, add_line_numbers
from state_schema import WorkflowState
from ui.components.comparison_report_renderer import ComparisonReportRenderer
import json
import re
from analytics.behavior_tracker import behavior_tracker
import uuid


logger = logging.getLogger(__name__)

class TutorialUI:
    """UI component for exploring Java errors with examples and solutions."""
    
    def __init__(self, workflow=None):
        """Initialize the Error Explorer UI."""
        self.repository = DatabaseErrorRepository()
        self.workflow = workflow  # JavaCodeReviewGraph instance
        self.comparison_renderer = ComparisonReportRenderer()
        self.behavior_tracker = behavior_tracker
        self.interaction_start_times = {}
        
        self.practice_session_id = None

        # Log workflow initialization for debugging
        if workflow:
            logger.info(f"Tutorial initialized with workflow: {type(workflow)}")
        else:
            logger.warning("Tutorial initialized without workflow - practice mode will not work")
        
        # Initialize session state
        if "selected_error_code" not in st.session_state:
            st.session_state.selected_error_code = None
        if "user_progress" not in st.session_state:
            st.session_state.user_progress = {}
        if "practice_mode_active" not in st.session_state:
            st.session_state.practice_mode_active = False
        # Initialize timing for interactions
        if "error_explorer_start_time" not in st.session_state:
            st.session_state.error_explorer_start_time = time.time()
         # Track component load time
        if "error_explorer_load_time" not in st.session_state:
            st.session_state.error_explorer_load_time = time.time()
        
        self._load_styles()
    
    def _load_styles(self):
        """Load CSS styles for the Error Explorer UI with safe encoding handling."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            css_dir = os.path.join(current_dir, "..", "..", "static", "css", "error_explorer")
            from static.css_utils import load_css_safe
            result = load_css_safe(css_directory=css_dir)
        except Exception as e:
            logger.error(f"Error loading Error Explorer CSS: {str(e)}")
            st.warning(t("css_loading_warning"))

    # ==========================================
    # PRACTICE SESSION TRACKING METHODS
    # ==========================================

    def _start_practice_session(self, 
                               user_id: str,
                               error_code: str,
                               error_name: str,
                               error_category: str,
                               difficulty_level: str,
                               context_data: Dict[str, Any] = None) -> str:
        """
        Start tracking a practice session with comprehensive initialization.
        
        Args:
            user_id: The user's ID
            error_code: Code of the error being practiced
            error_name: Name of the error
            error_category: Category of the error
            difficulty_level: Difficulty level
            context_data: Additional context information
            
        Returns:
            Practice session ID
        """
        try:
            practice_session_id = str(uuid.uuid4())
            session_id = st.session_state.get("session_id")
            
            # Store practice session ID for updates
            self.practice_session_id = practice_session_id
            st.session_state.practice_session_id = practice_session_id
            st.session_state.practice_start_time = time.time()
            
            # Prepare initial practice data
            practice_data = {
                "start_time": time.time(),
                "language": get_current_language(),
                "source": "error_explorer",
                "selection_context": context_data or {},
                "workflow_steps": ["session_started"]
            }
            
            # Insert practice session record using behavior tracker
            self.behavior_tracker.start_practice_session(
                user_id=user_id,
                error_code=error_code,
                error_name=error_name,
                error_category=error_category,
                difficulty_level=difficulty_level
            )
            
            # Log the practice session start
            self.behavior_tracker.log_interaction(
                user_id=user_id,
                interaction_type="start_session",
                interaction_category="practice",
                component="code_generation",
                action="start_practice_session",
                details={
                    "practice_session_id": practice_session_id,
                    "error_code": error_code,
                    "error_name": error_name,
                    "error_category": error_category,
                    "difficulty_level": difficulty_level,
                    "context_data": context_data
                }
            )
            
            logger.info(f"Started practice session {practice_session_id} for error {error_code}")
            return practice_session_id
            
        except Exception as e:
            logger.error(f"Error starting practice session: {str(e)}")
            return str(uuid.uuid4())  # Return a fallback ID

    def _update_practice_session(self,
                                user_id: str,
                                step_name: str,
                                step_data: Dict[str, Any] = None,
                                time_spent_seconds: int = None) -> None:
        """
        Insert new record for practice session step updates.
        
        Args:
            user_id: The user's ID
            step_name: Name of the step (e.g., 'code_generate_complete', 'ready_for_review', 
                      'review_submitted', 'pass_practice', 'submit_again')
            step_data: Additional data for this step
            time_spent_seconds: Time spent on this step
        """
        try:
            if not self.practice_session_id:
                logger.warning("No active practice session to update")
                return
            
            # Calculate time spent if not provided
            if time_spent_seconds is None:
                current_time = time.time()
                start_time = st.session_state.get("practice_start_time", current_time)
                time_spent_seconds = int(current_time - start_time)
            
            # Prepare step details
            step_details = {
                "practice_session_id": self.practice_session_id,
                "step_name": step_name,
                "step_data": step_data or {},
                "timestamp": time.time(),
                "time_spent_seconds": time_spent_seconds
            }
            
            # Insert step record through behavior tracker
            self.behavior_tracker.log_interaction(
                user_id=user_id,
                interaction_type="step_change",
                interaction_category="practice",
                component="practice_session",
                action=f"practice_step_{step_name}",
                time_spent_seconds=time_spent_seconds,
                details=step_details
            )
            
            # Update the legacy practice session status based on step
            status_mapping = {
                "code_generate_complete": "code_ready",
                "ready_for_review": "code_ready", 
                "review_submitted": "reviewing",
                "pass_practice": "review_complete",
                "submit_again": "in_progress",
                "practice_abandoned": "abandoned"
            }
            
            if step_name in status_mapping:
                self.behavior_tracker.update_practice_session(
                    user_id=user_id,
                    status=status_mapping[step_name],
                    additional_data=step_data
                )
            
            logger.debug(f"Updated practice session step: {step_name}")
            
        except Exception as e:
            logger.error(f"Error updating practice session step: {str(e)}")

    def _completed_practice_session(self,
                                  user_id: str,
                                  completion_status: str,
                                  final_results: Dict[str, Any] = None,
                                  next_steps: List[str] = None) -> None:
        """
        Complete the practice session with final results and analytics.
        
        Args:
            user_id: The user's ID
            completion_status: Final status ('completed', 'abandoned', 'timeout')
            final_results: Final metrics and results
            next_steps: Suggested next actions for the user
        """
        try:
            if not self.practice_session_id:
                logger.warning("No active practice session to complete")
                return
            
            # Calculate total session duration
            start_time = st.session_state.get("practice_start_time", time.time())
            total_duration = time.time() - start_time
            
            # Prepare completion data
            completion_data = {
                "practice_session_id": self.practice_session_id,
                "completion_status": completion_status,
                "total_duration_seconds": int(total_duration),
                "final_results": final_results or {},
                "next_steps": next_steps or [],
                "completion_timestamp": time.time()
            }
            
            # Log the practice session completion
            self.behavior_tracker.log_interaction(
                user_id=user_id,
                interaction_type="complete_session",
                interaction_category="practice",
                component="practice_session",
                action=f"complete_practice_{completion_status}",
                time_spent_seconds=int(total_duration),
                success=(completion_status == "completed"),
                details=completion_data
            )
            
            # Update the legacy practice session with final status
            self.behavior_tracker.update_practice_session(
                user_id=user_id,
                status=completion_status,
                additional_data=final_results
            )
            
            # Track error identification if results available
            if final_results and "error_code" in final_results:
                error_code = final_results["error_code"]
                identified_correctly = final_results.get("identified_correctly", False)
                review_text = final_results.get("final_review_text", "")
                review_iteration = final_results.get("review_iterations", 1)
                
                self.behavior_tracker.track_error_identification(
                    user_id=user_id,
                    error_code=error_code,
                    review_iteration=review_iteration,
                    review_text=review_text,
                    identified_correctly=identified_correctly,
                    time_to_identify=int(total_duration),
                    analysis_data=final_results.get("analysis_data", {})
                )
            
            # Clear practice session state
            self.practice_session_id = None
            if "practice_session_id" in st.session_state:
                del st.session_state["practice_session_id"]
            
            logger.info(f"Completed practice session with status: {completion_status}")
            
        except Exception as e:
            logger.error(f"Error completing practice session: {str(e)}")

    # ==========================================
    # MAIN RENDER METHODS (Updated with new tracking)
    # ==========================================

    def render(self, workflow=None):
        """Render the complete error explorer interface."""

        user_id = st.session_state.auth.get("user_id") if "auth" in st.session_state else None

        if user_id:
            # Start session tracking if not already started
            if "session_tracking_started" not in st.session_state:
                self.behavior_tracker.start_user_session(user_id)
                st.session_state.session_tracking_started = True
          
        # Only update workflow if one is provided, otherwise keep the existing one
        if workflow is not None:
            self.workflow = workflow
        
        # Check if we're in practice mode
        if st.session_state.get("practice_mode_active", False):
            self._render_practice_mode()
            self.behavior_tracker.log_interaction(
                user_id=user_id,
                interaction_type="access",
                interaction_category="practice",
                component="practice_UI",
                action="access_code_review_practice_UI",
                details={
                    "load_time": time.time() - st.session_state.error_explorer_load_time,
                    "practice_mode_active": st.session_state.get("practice_mode_active", False)
                }
            )
        else:
            self._render_exploration_mode()
            self.behavior_tracker.log_interaction(
                user_id=user_id,
                interaction_type="access",
                interaction_category="practice",
                component="code_generation",
                action="access_code_review_practice_UI",
                details={
                    "load_time": time.time() - st.session_state.error_explorer_load_time,
                    "practice_mode_active": st.session_state.get("practice_mode_active", False)
                }
            )
            
    def _render_practice_mode(self):
        """Render the enhanced professional practice mode interface."""
        practice_error = st.session_state.get("practice_error_data", {})        
        error_name = practice_error.get("error_name", t("unknown_error"))        
        difficulty = practice_error.get("difficulty_level", "medium")
        category = practice_error.get("category", "")
        
        # Professional practice mode header with enhanced styling
        self._render_professional_practice_header(error_name, difficulty, category)
        
        # Main practice workflow based on status
        workflow_status = st.session_state.get("practice_workflow_status", "setup")
        
        if workflow_status == "setup":
            self._render_practice_setup(practice_error)
        elif workflow_status == "code_ready":
            self._render_practice_review()
        elif workflow_status == "review_complete":
            self._render_practice_feedback()

    def _render_exploration_mode(self):
        """Render the normal exploration mode."""
        # Professional header
        self._render_header()
        
        # Search and filter section
        self._render_search_filters()
        
        # Main content area
        self._render_error_content()
        
    def _process_practice_review_with_tracking(self, student_review):
        """Process the submitted practice review with step-by-step tracking."""
        try:
            user_id = st.session_state.auth.get("user_id") if "auth" in st.session_state else None
            workflow_state = st.session_state.practice_workflow_state
            
            if user_id:
                # Update practice session: review submitted
                self._update_practice_session(
                    user_id=user_id,
                    step_name="review_submitted",
                    step_data={
                        "review_length": len(student_review),
                        "review_iteration": getattr(workflow_state, 'current_iteration', 1),
                        "word_count": len(student_review.split())
                    }
                )

                self.behavior_tracker.log_interaction(
                            user_id=user_id,
                            interaction_type="action",
                            interaction_category="practice",
                            component="code_review",
                            action="Submit_review_to_system_for_analysis",
                            details={
                                "load_time": time.time() - st.session_state.error_explorer_load_time,
                                "practice_mode_active": st.session_state.get("practice_mode_active", False)
                            }
                        )
                    

            with st.spinner(f"🔄 {t('analyzing_your_review')}"):
                # Submit review through workflow
                updated_state = self.workflow.submit_review(workflow_state, student_review)
                # Update stored state
                st.session_state.practice_workflow_state = updated_state
                
                # Check if review is complete
                review_sufficient = getattr(updated_state, 'review_sufficient', False)
                current_iteration = getattr(updated_state, 'current_iteration', 1)
                max_iterations = getattr(updated_state, 'max_iterations', 3)
                
                if user_id:
                    # Get analysis results for tracking
                    latest_review = updated_state.review_history[-1] if updated_state.review_history else None
                    analysis = latest_review.analysis if latest_review else {}
                    print(analysis)
                    identified_count = analysis.get(t('identified_count'), 0)
                    total_problems = analysis.get(t('total_problems'), 0)
                    accuracy = (identified_count / total_problems * 100) if total_problems > 0 else 0
                    
                    # Track analysis completion
                    self._update_practice_session(
                        user_id=user_id,
                        step_name="review_analysis_complete",
                        step_data={
                            "identified_count": identified_count,
                            "total_problems": total_problems,
                            "accuracy": accuracy,
                            "review_sufficient": review_sufficient,
                            "iteration": current_iteration,
                            "analysis_data": analysis
                        }
                    )

                    self.behavior_tracker.log_interaction(
                            user_id=user_id,
                            interaction_type="action",
                            interaction_category="practice",
                            component="code_review",
                            action="review_analysis_complete",
                            details={
                                "load_time": time.time() - st.session_state.error_explorer_load_time,
                                "practice_mode_active": st.session_state.get("practice_mode_active", False)
                            }
                        )
                    
                # Complete or continue practice session
                if review_sufficient or current_iteration > max_iterations:
                    st.session_state.practice_workflow_status = "review_complete"
                    
                    if user_id:
                        # Determine if user passed
                        passed = review_sufficient and identified_count == total_problems
                        
                        if passed:
                            self._update_practice_session(
                                user_id=user_id,
                                step_name="pass_practice",
                                step_data={
                                    "final_accuracy": accuracy,
                                    "errors_identified": identified_count,
                                    "total_errors": total_problems,
                                    "review_iterations": current_iteration,
                                    "passed": True
                                }
                            )

                            self.behavior_tracker.log_interaction(
                            user_id=user_id,
                            interaction_type="action",
                            interaction_category="practice",
                            component="code_review",
                            action="pass_practice",
                            details={
                                "load_time": time.time() - st.session_state.error_explorer_load_time,
                                "practice_mode_active": st.session_state.get("practice_mode_active", False)
                            }
                        )

                        else:
                            self._update_practice_session(
                                user_id=user_id,
                                step_name="practice_completed_incomplete",
                                step_data={
                                    "final_accuracy": accuracy,
                                    "errors_identified": identified_count,
                                    "total_errors": total_problems,
                                    "review_iterations": current_iteration,
                                    "passed": False,
                                    "max_iterations_reached": current_iteration > max_iterations
                                }
                            )

                            self.behavior_tracker.log_interaction(
                                user_id=user_id,
                                interaction_type="action",
                                interaction_category="practice",
                                component="code_review",
                                action="review_DO_NOT_pass_practice",
                                details={
                                    "load_time": time.time() - st.session_state.error_explorer_load_time,
                                    "practice_mode_active": st.session_state.get("practice_mode_active", False)
                                }
                            )
                        
                        # Complete the practice session
                        practice_error = st.session_state.get("practice_error_data", {})
                        final_results = {
                            "accuracy": accuracy,
                            "identified_count": identified_count,
                            "total_problems": total_problems,
                            "iterations_used": current_iteration,
                            "review_sufficient": review_sufficient,
                            "identified_correctly": identified_count == total_problems,
                            "error_code": practice_error.get('error_code', ''),
                            "final_review_text": student_review,
                            "review_iterations": current_iteration,
                            "analysis_data": analysis
                        }
                        
                        completion_status = "completed" if review_sufficient else "incomplete"
                        next_steps = ["view_results", "practice_again", "explore_related"] if passed else ["try_again", "view_hints", "practice_different"]
                        
                        self._completed_practice_session(
                            user_id=user_id,
                            completion_status=completion_status,
                            final_results=final_results,
                            next_steps=next_steps
                        )

                        self.behavior_tracker.log_interaction(
                                user_id=user_id,
                                interaction_type="action",
                                interaction_category="practice",
                                component="code_review",
                                action="complete_practice_session",
                                details={
                                    "load_time": time.time() - st.session_state.error_explorer_load_time,
                                    "practice_mode_active": st.session_state.get("practice_mode_active", False)
                                }
                        )
                    
                    st.success(f"✅ {t('review_analysis_complete')}")
                else:
                    # Track need to submit again
                    if user_id:
                        self._update_practice_session(
                            user_id=user_id,
                            step_name="submit_again",
                            step_data={
                                "current_accuracy": accuracy,
                                "iteration": current_iteration,
                                "max_iterations": max_iterations,
                                "needs_improvement": True
                            }
                        )

                        self.behavior_tracker.log_interaction(
                                user_id=user_id,
                                interaction_type="action",
                                interaction_category="practice",
                                component="code_review",
                                action="Submit_again_for_review",
                                details={
                                    "load_time": time.time() - st.session_state.error_explorer_load_time,
                                    "practice_mode_active": st.session_state.get("practice_mode_active", False)
                                }
                            )
                    
                    st.info(f"📝 {t('review_submitted_try_improve')}")
                
                time.sleep(1)
                st.rerun()
                
        except Exception as e:
            logger.error(f"Error processing practice review: {str(e)}")
            
            # Track error
            if user_id:
                self._update_practice_session(
                    user_id=user_id,
                    step_name="review_processing_error",
                    step_data={
                        "error_message": str(e),
                        "failed_action": "process_practice_review"
                    }
                )
            
            st.error(f"❌ {t('error_processing_review')}: {str(e)}")
    
    def _exit_practice_mode_with_tracking(self):
        """Exit practice mode with proper tracking."""
        user_id = st.session_state.auth.get("user_id") if "auth" in st.session_state else None
        
        if user_id and self.practice_session_id:
            # Complete practice session as abandoned
            final_results = {
                "abandoned": True,
                "exit_reason": "user_requested",
                "practice_error": st.session_state.get("practice_error_data", {}),
                "workflow_status": st.session_state.get("practice_workflow_status", "unknown")
            }
            
            self._completed_practice_session(
                user_id=user_id,
                completion_status="abandoned",
                final_results=final_results,
                next_steps=["return_to_explorer", "try_different_error"]
            )

            self.behavior_tracker.log_interaction(
                user_id=user_id,
                interaction_type="action",
                interaction_category="practice",
                component="code_review",
                action="Exit_practice_mode",
                details={
                            "load_time": time.time() - st.session_state.error_explorer_load_time,
                            "practice_mode_active": st.session_state.get("practice_mode_active", False)
                        }
            )
        
        # Clear all practice-related session state
        practice_keys = [key for key in st.session_state.keys() if key.startswith("practice_")]
        for key in practice_keys:
            del st.session_state[key]
        
        st.session_state.practice_mode_active = False
        st.rerun()

    def _restart_practice_session(self):
        """Restart the practice session with the same error."""
        # Clear practice session state but keep error data
        practice_error = st.session_state.get("practice_error_data", {})
        
        keys_to_clear = [
            "practice_code_generated",
            "practice_workflow_state", 
            "practice_workflow_status"
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state.practice_workflow_status = "setup"
        st.rerun()
    
    def _regenerate_practice_code(self):
        """Regenerate practice code with the same error."""
        practice_error = st.session_state.get("practice_error_data", {})
        try:
            user_id = st.session_state.auth.get("user_id") if "auth" in st.session_state else None
        except KeyError:
            user_id = None
        # Clear code generation state
        if "practice_code_generated" in st.session_state:
            del st.session_state["practice_code_generated"]
        if "practice_workflow_state" in st.session_state:
            del st.session_state["practice_workflow_state"]
        
        self.behavior_tracker.log_interaction(
            user_id=user_id,
            interaction_type="action",
            interaction_category="practice",
            component="code_review",
            action="Regenerate_practice_code",
            details={
                        "load_time": time.time() - st.session_state.error_explorer_load_time,
                        "practice_mode_active": st.session_state.get("practice_mode_active", False)
                    }
        )

        st.session_state.practice_workflow_status = "setup"
        st.rerun()
    
    def _render_header(self):
        """Render an enhanced professional header with branding and statistics."""
        try:
            stats = self.repository.get_error_statistics()
            total_errors = stats.get('total_errors', 0)
            total_categories = stats.get('total_categories', 0)            
        except Exception as e:
            logger.debug(f"Could not get database statistics: {str(e)}")
            total_errors = 0
            total_categories = 0           
        
        st.markdown(f"""
        <div class="error-explorer-header-compact">
            <div class="header-content-compact">
                <div class="title-section-compact">
                    <h1>🔍 {t('error_explorer')}</h1>
                    <p class="subtitle-compact">{t('explore_comprehensive_error_library')}</p>
                </div>
                <div class="stats-section-compact">
                    <div class="stat-card-compact">
                        <div class="stat-number-compact">{total_errors}</div>
                        <div class="stat-label-compact">{t('errors')}</div>
                    </div>
                    <div class="stat-card-compact">
                        <div class="stat-number-compact">{total_categories}</div>
                        <div class="stat-label-compact">{t('categories')}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_search_filters(self):
        """Render enhanced search and filter controls with professional styling."""
        st.markdown('<div class="search-filter-container">', unsafe_allow_html=True)
        
        # Search section header
        st.markdown(f"""
        <div class="section-header">           
            <div>
                <div class="section-title">{t('search_and_filter_errors')}</div>
                <div class="section-subtitle">{t('find_specific_errors_or_browse')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Main search and filter controls
        col1, col2, col3 = st.columns([4, 2, 2])
        
        with col1:
            search_term = st.text_input(
                "",
                placeholder=f"🔍 {t('search_errors_placeholder')}",
                key="error_search",
                help=t('search_help_text')
            )
        
        with col2:
            categories = self._get_categories()
            selected_category = st.selectbox(
                f"📂 {t('category')}",
                options=[t('all_categories')] + categories,
                key="category_filter",
                help=t('category_filter_help')
            )
        
        with col3:
            difficulty_levels = [t('all_levels'), t('easy'), t('medium'), t('hard')]
            selected_difficulty = st.selectbox(
                f"⚡ {t('difficulty')}",
                options=difficulty_levels,
                key="difficulty_filter",
                help=t('difficulty_filter_help')
            )
        
        st.markdown('</div>', unsafe_allow_html=True)        
        st.session_state.search_term = search_term
        st.session_state.selected_category = selected_category
        st.session_state.selected_difficulty = selected_difficulty

    #render error cards
    def _render_error_content(self):
        """Render the main error content with professional cards."""
        # Get filtered errors
        filtered_errors = self._get_filtered_errors()
        
        if not filtered_errors:
            self._render_no_results()
            return
        
        # Render professional error cards
        self._render_error_cards(filtered_errors)
    
    def _get_filtered_errors(self) -> List[Dict[str, Any]]:
        """Get errors based on current filters."""
        try:
            # Get all categories if no specific filter
            selected_category = st.session_state.get('selected_category', t('all_categories'))
            
            if selected_category == t('all_categories'):                
                categories = self._get_categories()
            else:
                categories = [selected_category]
            
            all_errors = []
            for category in categories:
                category_errors = self.repository.get_category_errors(category)
                for error in category_errors:
                    error['category'] = category
                    all_errors.append(error)
            
            # Apply filters
            filtered_errors = self._apply_filters(all_errors)
            return filtered_errors
            
        except Exception as e:
            logger.error(f"Error getting filtered errors: {str(e)}")
            return []

    def _get_categories(self) -> List[str]:
        """Get all available categories."""
        try:
            categories_data = self.repository.get_all_categories()
            return categories_data.get("java_errors", [])
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []

    def _apply_filters(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply search and difficulty filters to errors."""
        filtered = errors       
        # Search filter
        search_term = st.session_state.get('search_term', '').lower()
        if search_term:
            filtered = [
                error for error in filtered
                if search_term in error.get(t("implementation_guide"), "").lower() or
                   search_term in error.get(t("description"), "").lower()
            ]
        
        # Difficulty filter
        selected_difficulty = st.session_state.get('selected_difficulty', t('all_levels'))
        
        if selected_difficulty != t('all_levels'):
            difficulty_map = {
               t("easy"): "easy",
               t("medium"): "medium", 
               t("hard"): "hard"
            }
            db_difficulty = difficulty_map.get(selected_difficulty, "medium")
            
            filtered = [
                error for error in filtered   
                if error.get('difficulty_level') == db_difficulty
            ]
        
        return filtered

    def _render_no_results(self):
        """Render enhanced no results message."""
        st.markdown(f"""
        <div class="no-results">
            <div class="no-results-icon">🔍</div>
            <h3>{t('no_errors_found')}</h3>
            <p>{t('no_errors_found_message')}</p>
            <div class="no-results-suggestions">
                <h4>{t('try_these_suggestions')}:</h4>
                <ul>
                    <li>{t('check_spelling_try_different_keywords')}</li>
                    <li>{t('broaden_search_select_all_categories')}</li>
                    <li>{t('try_searching_common_terms')}</li>
                    <li>{t('clear_search_box_browse_all')}</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _render_error_cards(self, filtered_errors: List[Dict[str, Any]]):
        """Render errors in professional card format with consecutive container styling."""
        errors_by_category = self._group_errors_by_category(filtered_errors)
        
        for category_name, errors in errors_by_category.items():
            # Sort errors by difficulty within each category
            sorted_errors = self._sort_errors_by_difficulty(errors)
            
            # Category section with professional styling
            st.markdown(f"""
            <div class="category-section">
                <h3 class="category-title">
                    <span class="category-icon">{_get_category_icon(category_name.lower())}</span>
                    {category_name}
                    <span class="error-count">{len(sorted_errors)}</span>
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            for error in sorted_errors:
                self._render_consecutive_error_card(error)

    def _group_errors_by_category(self, errors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group errors by category."""
        grouped = {}
        for error in errors:
            category = error.get('category', 'Unknown')
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(error)
        return grouped

    def _sort_errors_by_difficulty(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort errors by difficulty level (easy -> medium -> hard)."""
        difficulty_order = {'easy': 1, 'medium': 2, 'hard': 3}
        
        def get_difficulty_sort_key(error):
            difficulty = error.get('difficulty_level', 'medium')
            return difficulty_order.get(difficulty, 2)  # Default to medium if unknown
        
        return sorted(errors, key=get_difficulty_sort_key)

    def _render_consecutive_error_card(self, error: Dict[str, Any]):
        """Enhanced error card with detailed interaction tracking."""        
        error_name = error.get(t("error_name_variable"), t("unknown_error"))
        error_code = error.get('error_code', f"error_{hash(error_name) % 10000}")

        
        description = error.get(t("description"), "")
        implementation_guide = error.get(t("implementation_guide"), "")
        difficulty = error.get('difficulty_level', 'medium')       
        difficulty_text = difficulty.title()        
        examples = self.repository.get_error_examples(error_name)              
        expander_title = f" {_get_difficulty_icon(difficulty_text)} **{error_name}**"
        
        # Single professional expander with all content
        with st.expander(expander_title, expanded=False):
            # Description section with enhanced styling
            if description or implementation_guide:
              
                if description:
                    st.markdown(f"""
                    <div class="section-header-inline">
                        <h4 class="section-title">📋 {t('error_description')}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f'<div class="description-content">{description}</div>', unsafe_allow_html=True)
                
                if implementation_guide:
                    st.markdown(f"""
                    <div class="section-header-inline">
                        <h4 class="section-title">💡 {t('how_to_fix')}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f'<div class="solution-content">{implementation_guide}</div>', unsafe_allow_html=True)
                
            # Code examples section with improved layout
            if examples.get("wrong_examples") or examples.get("correct_examples"):
               
                st.markdown(f"""
                    <div class="section-header-inline">
                        <h4 class="section-title">💻 {t('code_example')}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                # Create columns for side-by-side comparison when both exist
                if examples.get("wrong_examples") and examples.get("correct_examples"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="code-section-header error-header">
                            <h4 class="code-section-title">❌ {t('problematic_code')}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, example in enumerate(examples["wrong_examples"][:2], 1):
                            if len(examples["wrong_examples"]) > 1:
                                st.markdown(f'<div class="example-label">Example {i}:</div>', unsafe_allow_html=True)
                            st.code(example, language="java")
                    
                    with col2:
                        st.markdown(f"""
                        <div class="code-section-header solution-header">
                            <h4 class="code-section-title">✅ {t('corrected_code')}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, example in enumerate(examples["correct_examples"][:2], 1):
                            if len(examples["correct_examples"]) > 1:
                                st.markdown(f'<div class="example-label">Example {i}:</div>', unsafe_allow_html=True)
                            st.code(example, language="java")
                
                else:
                    # Single column layout when only one type exists
                    if examples.get("wrong_examples"):
                        st.markdown(f"""
                        <div class="code-section-header error-header">
                            <h4 class="code-section-title">❌ {t('problematic_code')} {t('examples')}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, example in enumerate(examples["wrong_examples"][:3], 1):
                            if len(examples["wrong_examples"]) > 1:
                                st.markdown(f'<div class="example-label">{t("example")} {i}:</div>', unsafe_allow_html=True)
                            st.code(example, language="java")
                            if i < len(examples["wrong_examples"][:3]):
                                st.markdown('<hr class="example-divider">', unsafe_allow_html=True)
                    
                    if examples.get("correct_examples"):
                        st.markdown(f"""
                        <div class="code-section-header solution-header">
                            <h4 class="code-section-title">✅ {t('corrected_code')} {t('examples')}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, example in enumerate(examples["correct_examples"][:3], 1):
                            if len(examples["correct_examples"]) > 1:
                                st.markdown(f'<div class="example-label">{t("example")} {i}:</div>', unsafe_allow_html=True)
                            st.code(example, language="java")
                            if i < len(examples["correct_examples"][:3]):
                                st.markdown('<hr class="example-divider">', unsafe_allow_html=True)
        
            # Enhanced practice button with tracking
            practice_key = f"practice_{error_code}_{hash(error_name) % 1000}"
            
            if st.button(
                f"🚀 {t('start_practice_session')}", 
                key=practice_key, 
                use_container_width=True,
                type="primary",
                help=t('generate_practice_code_with_error_type')
            ):
                
                self._start_practice_session(error)

    def _prepare_practice_workflow_state(self, error: Dict[str, Any]) -> Optional[WorkflowState]:
        """Prepare a WorkflowState specifically for practice sessions with a single error."""
        try:
            error_name = error.get(t("error_name_variable"), t("unknown_error"))
            difficulty_level = error.get('difficulty_level', 'medium')
            category = error.get('category', 'Other')
            
            logger.debug(f"Preparing practice state for error: {error_name}, difficulty: {difficulty_level}")
            
            # Create a new WorkflowState
            state = WorkflowState()
            
            # Set basic parameters optimized for single error practice
            state.code_length = "medium"  # Good balance for practice
            state.difficulty_level = difficulty_level
            state.error_count_start = 1
            state.error_count_end = 1
            
            # Set domain based on error category if available
            domain_mapping = {
                "logical errors": "calculation",
                "logical_errors": "calculation", 
                "syntax errors": "user_management",
                "syntax_errors": "user_management",
                "code quality": "file_processing",
                "code_quality": "file_processing",
                "standard violation": "data_validation",
                "standard_violation": "data_validation",
                "java specific": "banking",
                "java_specific": "banking"
            }
            state.domain = domain_mapping.get(category.lower(), "student_management")
            
            # Configure for specific error mode
            state.selected_error_categories = {"java_errors": []}  # Empty for specific mode
            state.selected_specific_errors = [error]  # Focus on this single error
            
            # Set workflow control parameters
            state.current_step = "generate"
            state.max_evaluation_attempts = 3
            state.max_iterations = 3
            
            # Reset all other state fields to defaults
            state.evaluation_attempts = 0
            state.current_iteration = 1
            state.review_sufficient = False
            state.review_history = []
            state.evaluation_result = None
            state.code_snippet = None
            state.comparison_report = None
            state.error = None
            
            logger.debug(f"Practice state prepared successfully for {error_name}")
            return state
            
        except Exception as e:
            logger.error(f"Error preparing practice workflow state: {str(e)}")
            return None
    
    def _start_practice_session(self, error: Dict[str, Any]):
        """Enhanced practice session start with comprehensive tracking."""
        try:
            user_id = st.session_state.auth.get("user_id") if "auth" in st.session_state else None
            error_name = error.get(t("error_name_variable"), t("unknown_error"))
            error_code = error.get('error_code', f"error_{hash(error_name) % 10000}")
            error_category = error.get('category', 'Unknown')
            difficulty = error.get('difficulty_level', 'medium')
            
            logger.info(f"Starting practice session for error: {error_name}")
            
            # Track practice session initiation
            if user_id:
                # Start practice session tracking
                practice_session_id = self.behavior_tracker.start_practice_session(
                    user_id=user_id,
                    error_code=error_code,
                    error_name=error_name,
                    error_category=error_category,
                    difficulty_level=difficulty
                )
                
                # Store additional tracking data
                st.session_state.practice_session_id = practice_session_id
                st.session_state.practice_start_interaction_time = time.time()
                st.session_state.practice_error_selection_context = {
                    "source": "error_explorer",
                    "selection_method": "manual_card_selection",
                    "search_context": {
                        "had_search_term": bool(st.session_state.get("error_search", "")),
                        "category_filter": st.session_state.get("category_filter", ""),
                        "difficulty_filter": st.session_state.get("difficulty_filter", "")
                    }
                }
            
            # Set session state flags
            st.session_state.practice_mode_active = True
            st.session_state.practice_error_data = error
            st.session_state.practice_workflow_status = "setup"
            
            # Show immediate feedback
            st.success(t('starting_practice_session_with').format(error_name=error_name))
            st.info(f"✨ {t('practice_mode_activated_interface_reload')}")
            
            time.sleep(0.5)
            st.rerun()
            
        except Exception as e:
            logger.error(f"Error starting practice session: {str(e)}", exc_info=True)
            
            # Track error
            if user_id:
                self.behavior_tracker.log_interaction(
                    user_id=user_id,
                    interaction_type="error",
                    interaction_category="practice",
                    component="code_generation",
                    action="start_practice_error",
                    success=False,
                    error_message=str(e),
                    details={"error_code": error_code}
                )
            
            st.error(f"❌ {t('error_setting_up_practice_session')}: {str(e)}")
    
    def _render_professional_practice_header(self, error_name: str, difficulty: str, category: str):
        """Render enhanced professional practice mode header."""
        # Difficulty colors and icons
        difficulty_config = {
            "easy": {"color": "#28a745", "icon": "🟢", "bg": "#d4edda"},
            "medium": {"color": "#ffc107", "icon": "🟡", "bg": "#fff3cd"},
            "hard": {"color": "#dc3545", "icon": "🔴", "bg": "#f8d7da"}
        }
        
        config = difficulty_config.get(difficulty, difficulty_config["medium"])
        category_icon = _get_category_icon(category.lower()) if category else "📚"
        
        st.markdown(f"""
        <div class="professional-practice-header">
            <div class="practice-header-content">
                <div class="practice-title-section">
                    <div class="practice-mode-badge">
                        <span class="practice-icon">🎯</span>
                        <span class="practice-label">{t('practice_mode')}</span>
                    </div>
                    <h1 class="practice-error-title">{error_name}</h1>
                    <div class="practice-meta-info">
                        <span class="practice-category">
                            <span class="category-icon">{category_icon}</span>
                            {category}
                        </span>
                        <span class="practice-difficulty" style="background: {config['bg']}; color: {config['color']};">
                            <span class="difficulty-icon">{config['icon']}</span>
                            {t(difficulty)}
                        </span>
                    </div>
                </div>
                <div class="practice-actions-section">
                    <div class="practice-progress-indicator">
                        <div class="progress-step active">1</div>
                        <div class="progress-connector"></div>
                        <div class="progress-step">2</div>
                        <div class="progress-connector"></div>
                        <div class="progress-step">3</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    #render practice setup
    def _render_practice_setup(self, practice_error):
        """Render the enhanced practice setup phase."""
        st.markdown(f"""
        <div class="professional-practice-container">
            <div class="practice-section-header">
                <span class="section-icon">⚙️</span>
                <div>
                    <h3 class="section-title">{t('preparing_practice_session')}</h3>
                    <p class="section-subtitle">{t('generating_custom_code_challenge')}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced error details with professional cards
        self._render_error_details(practice_error)
        
        # Workflow validation and generation
        if not self.workflow:
            self._render_workflow_error_message()
            return
        
        # Auto-generate code with enhanced status
        if "practice_code_generated" not in st.session_state:
            self._generate_practice_code_with_tracking(practice_error)

    def _render_error_details(self, practice_error):
        """Render enhanced error details with professional styling."""
        description = practice_error.get(t('description'), t('no_description_available'))
        implementation_guide = practice_error.get('implementation_guide', '')
        difficulty = practice_error.get('difficulty_level', 'medium')
        
        st.markdown(f"""
        <div class="enhanced-error-details-container">
            <div class="error-details-header">
                <h4><span class="details-icon">📋</span> {t('error_overview')}</h4>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Create columns for better layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Description card
            st.markdown(f"""
            <div class="detail-card description-card">
                <div class="card-header">
                    <span class="card-icon">📝</span>
                    <h5>{t('what_youll_learn')}</h5>
                </div>
                <div class="card-content">
                    {description}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if implementation_guide:
                # Implementation guide card
                st.markdown(f"""
                <div class="detail-card guide-card">
                    <div class="card-header">
                        <span class="card-icon">💡</span>
                        <h5>{t('identification_tips')}</h5>
                    </div>
                    <div class="card-content">
                        {implementation_guide}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Session info card
            st.markdown(f"""
            <div class="detail-card session-info-card">
                <div class="card-header">
                    <span class="card-icon">⚡</span>
                    <h5>{t('session_details')}</h5>
                </div>
                <div class="card-content">
                    <div class="info-item">
                        <span class="info-label">{t('difficulty')}:</span>
                        <span class="info-value difficulty-{difficulty}">{t(difficulty)}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">{t('focus_area')}:</span>
                        <span class="info-value">{t('single_error_type')}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">{t('attempts')}:</span>
                        <span class="info-value">3 {t('maximum')}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def _render_workflow_error_message(self):
        """Render professional workflow error message."""
        st.markdown(f"""
        <div class="workflow-error-container">
            <div class="error-icon">⚠️</div>
            <h3>{t('practice_session_unavailable')}</h3>
            <p>{t('workflow_system_not_initialized')}</p>
            <div class="error-actions">
                <button onclick="window.location.reload()" class="refresh-button">
                    🔄 {t('refresh_page')}
                </button>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _generate_practice_code_with_tracking(self, practice_error):
        """Enhanced code generation with step-by-step tracking."""
        user_id = st.session_state.auth.get("user_id") if "auth" in st.session_state else None
        
        if not self.workflow:
            logger.error("No workflow available for practice mode")
            st.error(f"❌ {t('practice_mode_requires_workflow_refresh')}")
            return
        
        try:
            generation_start_time = time.time()
            
            # Update practice session: starting code generation
            if user_id:
                self._update_practice_session(
                    user_id=user_id,
                    step_name="code_generation_started",
                    step_data={
                        "error_code": practice_error.get('error_code', ''),
                        "error_name": practice_error.get(t("error_name_variable"), ''),
                        "difficulty": practice_error.get('difficulty_level', 'medium')
                    }
                )

                self.behavior_tracker.log_interaction(
                    user_id=user_id,
                    interaction_type="action",
                    interaction_category="practice",
                    component="code_generation",
                    action="generate_practice_code",
                    details={
                        "load_time": time.time() - st.session_state.error_explorer_load_time,
                        "practice_mode_active": st.session_state.get("practice_mode_active", False)
                    }
                )
            
            # Enhanced status display
            with st.status(f"🚀 {t('generating_practice_challenge')}", expanded=True) as status:
                # Execute the generation
                workflow_state = self._prepare_practice_workflow_state(practice_error)
                
                if not workflow_state:
                    st.error(f"❌ {t('failed_prepare_practice_session')}")
                    return
                
                logger.info(f"Executing code generation with workflow: {type(self.workflow)}")
                updated_state = self.workflow.execute_code_generation(workflow_state)
                
                generation_duration = time.time() - generation_start_time
                
                # Validate and handle result
                if hasattr(updated_state, 'error') and updated_state.error:
                    error_msg = updated_state.error
                    
                    # Track generation failure
                    if user_id:
                        self._update_practice_session(
                            user_id=user_id,
                            step_name="code_generation_failed",
                            step_data={
                                "error_message": error_msg,
                                "generation_duration": generation_duration,
                                "generation_attempts": getattr(updated_state, 'evaluation_attempts', 1)
                            },
                            time_spent_seconds=int(generation_duration)
                        )
                        
                    st.error(f"❌ {t('failed_to_generate_practice_code')}: {error_msg}")
                    return
                
                if not hasattr(updated_state, 'code_snippet') or not updated_state.code_snippet:
                    # Track generation failure
                    if user_id:
                        self._update_practice_session(
                            user_id=user_id,
                            step_name="code_generation_no_output",
                            step_data={
                                "generation_duration": generation_duration
                            },
                            time_spent_seconds=int(generation_duration)
                        )
                    
                    st.error(f"❌ {t('failed_to_generate_practice_code')}: No code generated")
                    return
                
                # Track successful generation
                if user_id:
                    code_snippet = updated_state.code_snippet
                    code_stats = {
                        "lines_of_code": len(code_snippet.code.split('\n')) if hasattr(code_snippet, 'code') else 0,
                        "code_length_chars": len(code_snippet.code) if hasattr(code_snippet, 'code') else 0,
                        "has_clean_code": hasattr(code_snippet, 'clean_code') and bool(code_snippet.clean_code),
                        "expected_errors": getattr(code_snippet, 'expected_error_count', 0)
                    }
                    
                    self._update_practice_session(
                        user_id=user_id,
                        step_name="code_generate_complete",
                        step_data={
                            "generation_successful": True,
                            "generation_duration": generation_duration,
                            "generation_attempts": getattr(updated_state, 'evaluation_attempts', 1),
                            "code_stats": code_stats,
                            "workflow_step": getattr(updated_state, 'current_step', 'unknown')
                        },
                        time_spent_seconds=int(generation_duration)
                    )

                    self.behavior_tracker.log_interaction(
                            user_id=user_id,
                            interaction_type="action",
                            interaction_category="practice",
                            component="code_generation",
                            action="Competed_generate_practice_code",
                            details={
                                "load_time": time.time() - st.session_state.error_explorer_load_time,
                                "practice_mode_active": st.session_state.get("practice_mode_active", False)
                            }
                        )
    
            # Store results and update status
            st.session_state.practice_workflow_state = updated_state
            st.session_state.practice_code_generated = True
            st.session_state.practice_workflow_status = "code_ready"
            
            # Update to ready for review step
            if user_id:
                self._update_practice_session(
                    user_id=user_id,
                    step_name="ready_for_review",
                    step_data={
                        "code_ready": True,
                        "total_generation_time": generation_duration
                    }
                )

                self.behavior_tracker.log_interaction(
                            user_id=user_id,
                            interaction_type="action",
                            interaction_category="practice",
                            component="code_review",
                            action="code_ready for review",
                            details={
                                "load_time": time.time() - st.session_state.error_explorer_load_time,
                                "practice_mode_active": st.session_state.get("practice_mode_active", False)
                            }
                        )
            
            st.success("✅ Practice challenge ready!")
            
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            logger.error(f"Error generating practice code: {str(e)}", exc_info=True)
            
            # Track unexpected error
            if user_id:
                self._update_practice_session(
                    user_id=user_id,
                    step_name="code_generation_exception",
                    step_data={
                        "error_message": str(e),
                        "failed_action": "generate_practice_code"
                    }
                )
            st.error(f"❌ {t('error_setting_up_practice_session')}: {str(e)}")
            if user_id:
                self._update_practice_session(
                    user_id=user_id,
                    step_name="code_generation_exception",
                    step_data={
                        "error_message": str(e),
                        "failed_action": "generate_practice_code"
                    }
                )

    # Render Review Practice
    def _render_practice_review(self):
        """Render the enhanced practice review interface."""
        workflow_state = st.session_state.get("practice_workflow_state")
        
        if not workflow_state or not hasattr(workflow_state, 'code_snippet'):
            st.error(t('no_practice_session_data'))
            return
        
        # Enhanced practice review container
        st.markdown(f"""
        <div class="professional-practice-review-container">
            <div class="review-phase-header">
                <div class="phase-indicator">
                    <span class="phase-icon">👀</span>
                    <div class="phase-info">
                        <h3>{t('code_review_phase')}</h3>
                        <p>{t('analyze_code_find_specific_error')}</p>
                    </div>
                </div>
                <div class="practice-tips">
                    <span class="tip-icon">💡</span>
                    <span>{t('look_for_specific_error_practicing')}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced code display section
        self._render_code_display(workflow_state)
        
        # Enhanced review input section
        self._render_review_input(workflow_state)

    def _render_code_display(self, workflow_state):
        """Render enhanced code display for practice mode."""
        code_to_display = workflow_state.code_snippet.clean_code
        
        # Professional code container
        st.markdown(f"""
        <div class="enhanced-code-container">
            <div class="code-header-professional">
                <div class="code-meta">
                    <span class="file-icon">📄</span>
                    <span class="file-name">PracticeChallenge.java</span>
                </div>
                <div class="code-stats">
                    <span class="stat-item">
                        <span class="stat-icon">📏</span>
                        <span>{len(code_to_display.split())} {t('lines')}</span>
                    </span>
                    <span class="language-badge">☕ Java</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Code display with professional styling
        st.code(add_line_numbers(code_to_display), language="java")

    def _render_review_input(self, workflow_state):
        """Render enhanced review input section for practice mode."""
        current_iteration = getattr(workflow_state, 'current_iteration', 1)
        max_iterations = getattr(workflow_state, 'max_iterations', 3)
        
        # Show guidance if available
        review_history = getattr(workflow_state, 'review_history', [])
        if review_history:
            latest_review = review_history[-1]
            if hasattr(latest_review, 'targeted_guidance') and latest_review.targeted_guidance:
                st.markdown(f"""
                <div class="professional-guidance-container">
                    <div class="guidance-header">
                        <span class="guidance-icon">🎯</span>
                        <h4>{t('personalized_guidance')}</h4>
                    </div>
                    <div class="guidance-content">
                        {latest_review.targeted_guidance}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Enhanced review input container
        st.markdown(f"""
        <div class="enhanced-review-input-container">
            <div class="input-section-header">
                <div class="input-meta">
                    <span class="input-icon">✍️</span>
                    <div class="input-info">
                        <h4>{t('submit_your_analysis')}</h4>
                        <p>{t('attempt')} {current_iteration} {t('of')} {max_iterations}</p>
                    </div>
                </div>
                <div class="attempt-progress">
                    <div class="progress-circles">
                        {"".join(f'<div class="circle {"active" if i < current_iteration else ""}"></div>' for i in range(1, max_iterations + 1))}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Review input
        review_key = f"practice_review_{current_iteration}"
        student_review = st.text_area(
            "",
            height=250,
            key=review_key,
            placeholder=f"🔍 {t('example_review_format_line')}",
            label_visibility="collapsed"
        )
        
        # Enhanced action buttons - REMOVED DISABLED FUNCTIONALITY
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # REMOVED: submit_disabled = not student_review or len(student_review.strip()) < 10
            if st.button(
                f"🚀 {t('submit_review_button')}",
                # REMOVED: disabled=submit_disabled,
                key=f"submit_practice_review_{current_iteration}",
                use_container_width=True,
                type="primary"
            ):
                # Add basic validation in the processing function instead
                if student_review and student_review.strip():
                    self._process_practice_review_with_tracking(student_review.strip())
                else:
                    st.warning(f"⚠️ {t('please_enter_review')}")
        
        with col2:
            if st.button(
                f"🔄 {t('generate_new_challenge')}",
                key="regenerate_practice",
                use_container_width=True
            ):
                self._regenerate_practice_code()
        
        with col3:
            if st.button(
                f"🏠 {t('exit')}",
                key="exit_practice_from_review",
                use_container_width=True
            ):
                self._exit_practice_mode_with_tracking()

    # render feedback interface for professional practice mode
    def _render_practice_feedback(self):
        """Render the enhanced professional practice feedback interface."""
        workflow_state = st.session_state.get("practice_workflow_state")
        
        if not workflow_state:
            st.error(t('no_practice_session_data'))
            return
        
        # Professional feedback header
        st.markdown(f"""
        <div class="professional-feedback-header">
            <div class="feedback-celebration">
                <div class="celebration-icon">🎉</div>
                <div class="celebration-content">
                    <h2>{t('practice_session_complete')}</h2>
                    <p>{t('excellent_work_analysis_complete')}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        self._render_results_dashboard(workflow_state)
        self._render_action_panel()

    def _render_results_dashboard(self, workflow_state):
        """Render enhanced results dashboard with detailed metrics."""
        review_history = getattr(workflow_state, 'review_history', [])
        
        if review_history:
            latest_review = review_history[-1]
            analysis = getattr(latest_review, 'analysis', {}) if hasattr(latest_review, 'analysis') else {}
            
            identified = analysis.get(t('identified_count'), 0)
            total = analysis.get(t('total_problems'), 1)
            accuracy = analysis.get(t('identified_percentage'), 0)
            attempts = len(review_history)
            
            # Enhanced metrics dashboard
            st.markdown(f"""
            <div class="enhanced-results-dashboard">
                <div class="dashboard-header">
                    <h3><span class="dashboard-icon">📊</span> {t('performance_summary')}</h3>
                </div>
                <div class="metrics-grid">
                    <div class="metric-card primary">
                        <div class="metric-icon">🎯</div>
                        <div class="metric-content">
                            <div class="metric-value">{identified}/{total}</div>
                            <div class="metric-label">{t('issues_identified')}</div>
                        </div>
                    </div>
                    <div class="metric-card success">
                        <div class="metric-icon">📈</div>
                        <div class="metric-content">
                            <div class="metric-value">{accuracy:.1f}%</div>
                            <div class="metric-label">{t('accuracy_score')}</div>
                        </div>
                    </div>
                    <div class="metric-card info">
                        <div class="metric-icon">🔄</div>
                        <div class="metric-content">
                            <div class="metric-value">{attempts}</div>
                            <div class="metric-label">{t('attempts_used')}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Detailed feedback section
            comparison_report = getattr(workflow_state, 'comparison_report', None)
            if comparison_report:               
                self.comparison_renderer.render_comparison_report(comparison_report)

    def _render_action_panel(self):
        """Render enhanced action panel for practice session completion."""
        st.markdown(f"""
        <div class="enhanced-action-panel">
            <div class="action-panel-header">
                <h3><span class="action-icon">🎯</span> {t('whats_next')}</h3>
                <p>{t('choose_your_next_action')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(
                f"🔄 {t('try_another_challenge')}",
                key="restart_practice_session",
                use_container_width=True,
                type="primary"
            ):
                self._restart_practice_session()
        
        with col2:
            if st.button(
                f"🎲 {t('generate_new_challenge')}",
                key="new_practice_challenge",
                use_container_width=True
            ):
                self._regenerate_practice_code()
        
        with col3:
            if st.button(
                f"🏠 {t('back_to_explorer')}",
                key="exit_practice_to_explorer",
                use_container_width=True
            ):
                self._exit_practice_mode_with_tracking()