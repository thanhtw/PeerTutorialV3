"""
Enhanced Tutorial UI Component for Java Peer Review Training System.

This module provides an advanced tutorial interface with interactive elements,
progress tracking, and adaptive content delivery.
"""

import streamlit as st
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from learning.enhanced_tutorial import EnhancedTutorial
from learning.hint_system import SmartHintSystem
from learning.progress_manager import LearningProgressManager
from utils.language_utils import t
from utils.code_utils import add_line_numbers

logger = logging.getLogger(__name__)

class EnhancedTutorialUI:
    """
    Advanced tutorial UI with interactive learning components.
    """
    
    def __init__(self, llm_manager=None):
        self.tutorial_system = EnhancedTutorial(llm_manager)
        self.hint_system = SmartHintSystem()
        self.progress_manager = LearningProgressManager()
        
        # Initialize session state for tutorial
        if "tutorial_session" not in st.session_state:
            st.session_state.tutorial_session = {
                "current_step": 0,
                "session_start_time": time.time(),
                "step_start_time": time.time(),
                "attempts": 0,
                "hints_used": [],
                "session_id": str(int(time.time()))
            }
    
    def render(self, user_id: str, on_complete: Callable = None):
        """
        Render the complete enhanced tutorial interface.
        
        Args:
            user_id: Current user's ID
            on_complete: Callback function when tutorial is completed
        """
        try:
            # Get user's tutorial progress
            progress = self.tutorial_system.get_tutorial_progress(user_id)
            
            if progress.get("is_completed") and not st.session_state.get("tutorial_retake", False):
                if on_complete:
                    on_complete()
                return
            
            # Render tutorial header with progress
            self._render_tutorial_header(progress)
            
            # Get current step content
            current_step = st.session_state.tutorial_session["current_step"]
            step_content = self.tutorial_system.get_tutorial_step_content(user_id, current_step)
            
            if "error" in step_content:
                st.error(f"{t('error')}: {step_content['error']}")
                return
            
            # Render the current step
            self._render_tutorial_step(user_id, step_content, on_complete)
            
        except Exception as e:
            logger.error(f"Error rendering enhanced tutorial: {str(e)}")
            st.error(f"{t('tutorial_error')}: {str(e)}")
    
    def _render_tutorial_header(self, progress: Dict[str, Any]):
        """Render tutorial header with progress tracking."""
        
        # Calculate progress percentage
        current_step = st.session_state.tutorial_session["current_step"]
        total_steps = 8  # Total number of tutorial steps
        progress_percent = (current_step / total_steps) * 100
        
        # Header with progress bar
        st.markdown(f"""
        <div class="tutorial-header">
            <div class="tutorial-title">
                <h1>🎓 {t('interactive_tutorial')}</h1>
                <p>{t('learn_code_review_basics')}</p>
            </div>
            <div class="progress-section">
                <div class="progress-bar-container">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progress_percent}%"></div>
                    </div>
                    <div class="progress-text">{current_step + 1} / {total_steps + 1}</div>
                </div>
                <div class="progress-stats">
                    <span class="stat-item">📊 {t('progress')}: {progress_percent:.0f}%</span>
                    <span class="stat-item">🔄 {t('attempts')}: {progress.get('attempts_count', 0)}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_tutorial_step(self, user_id: str, step_content: Dict[str, Any], on_complete: Callable):
        """Render individual tutorial step content."""
        
        step_config = step_content["step_config"]
        content = step_content["content"]
        navigation = step_content["navigation"]
        
        # Render step title and estimated time
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"## {step_config['title']}")
        with col2:
            st.markdown(f"⏱️ {t('estimated_time')}: {step_config['estimated_time']} {t('minutes')}")
        
        # Render content based on step type
        step_type = step_config["type"]
        
        if step_type == "information":
            self._render_information_step(content)
        elif step_type == "code_display":
            self._render_code_display_step(content)
        elif step_type == "interactive_gallery":
            self._render_error_gallery_step(content)
        elif step_type == "example_analysis":
            self._render_example_analysis_step(content)
        elif step_type == "guided_practice":
            self._render_guided_practice_step(user_id, content)
        elif step_type == "pattern_game":
            self._render_pattern_game_step(user_id, content)
        elif step_type == "mini_review":
            self._render_mini_review_step(user_id, content)
        elif step_type == "completion":
            self._render_completion_step(user_id, content, on_complete)
        
        # Render navigation
        self._render_step_navigation(user_id, navigation, step_config)
    
    def _render_information_step(self, content: Dict[str, Any]):
        """Render information-based tutorial step."""
        
        st.info(content["content"])
        
        if "key_points" in content:
            st.markdown(f"### {t('key_points')}")
            for point in content["key_points"]:
                st.markdown(f"• {point}")
    
    def _render_code_display_step(self, content: Dict[str, Any]):
        """Render code display tutorial step."""
        
        st.markdown(content["explanation"])
        
        # Display code with line numbers
        code_with_lines = add_line_numbers(content["code"])
        st.code(code_with_lines, language="java")
        
        # Show what to look for
        st.markdown(f"### {t('what_to_look_for')}")
        for item in content["what_to_look_for"]:
            st.markdown(f"🔍 {item}")
        
        # Show difficulty and error count
        col1, col2 = st.columns(2)
        with col1:
            st.metric(t("difficulty"), content["difficulty"].title())
        with col2:
            st.metric(t("errors_present"), content["errors_present"])
    
    def _render_error_gallery_step(self, content: Dict[str, Any]):
        """Render interactive error type gallery."""
        
        st.markdown(f"### {t('explore_error_types')}")
        st.info(t("click_error_types_to_learn"))
        
        # Create error type cards
        error_types = [
            {"name": "logical", "icon": "🧠", "color": "#e74c3c"},
            {"name": "syntax", "icon": "🔍", "color": "#3498db"},
            {"name": "code_quality", "icon": "✨", "color": "#9b59b6"},
            {"name": "standard_violation", "icon": "📏", "color": "#f39c12"},
            {"name": "java_specific", "icon": "☕", "color": "#27ae60"}
        ]
        
        # Render cards in grid
        cols = st.columns(3)
        for i, error_type in enumerate(error_types):
            with cols[i % 3]:
                if st.button(
                    f"{error_type['icon']} {t(error_type['name'])}", 
                    key=f"error_type_{error_type['name']}",
                    use_container_width=True
                ):
                    self._show_error_type_details(error_type["name"])
    
    def _render_example_analysis_step(self, content: Dict[str, Any]):
        """Render good/poor review example analysis."""
        
        example_type = content["type"]
        
        # Show the review example
        st.markdown(f"### {t('example_review')}")
        
        if example_type == "poor_example":
            st.markdown(f"""
            <div class="review-example poor-example">
                <h4>{t('poor_quality_review')}</h4>
                <div class="review-text">{content['review_text']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"### {t('problems_with_this_review')}")
            for problem in content["problems"]:
                st.markdown(f"❌ {problem}")
                
        else:  # good_example
            st.markdown(f"""
            <div class="review-example good-example">
                <h4>{t('good_quality_review')}</h4>
                <div class="review-text">{content['review_text']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"### {t('strengths_of_this_review')}")
            for strength in content["strengths"]:
                st.markdown(f"✅ {strength}")
        
        # Show lesson learned
        st.success(f"**{t('lesson_learned')}:** {content['lesson']}")
    
    def _render_guided_practice_step(self, user_id: str, content: Dict[str, Any]):
        """Render guided practice step with hints and feedback."""
        
        st.markdown(f"### {t('your_turn_to_practice')}")
        st.info(t("guided_practice_instructions"))
        
        # Show practice code
        practice_code = content.get("practice_code", "")
        if practice_code:
            code_with_lines = add_line_numbers(practice_code)
            st.code(code_with_lines, language="java")
        
        # Practice input area
        user_response = st.text_area(
            t("write_your_review"),
            height=200,
            placeholder=t("guided_practice_placeholder"),
            key="guided_practice_response"
        )
        
        # Hint system
        col1, col2 = st.columns([3, 1])
        with col2:
            self._render_hint_system(user_id, "guided_practice")
        
        # Submit button
        with col1:
            if st.button(t("submit_review"), type="primary", key="submit_guided_practice"):
                if user_response.strip():
                    self._evaluate_guided_practice(user_id, user_response, content)
                else:
                    st.warning(t("please_enter_review"))
    
    def _render_pattern_game_step(self, user_id: str, content: Dict[str, Any]):
        """Render pattern recognition game."""
        
        st.markdown(f"### {t('pattern_recognition_game')}")
        
        # Get pattern challenge
        challenge = self.tutorial_system.get_pattern_recognition_challenge(user_id)
        
        if "error" in challenge:
            st.error(challenge["error"])
            return
        
        st.info(challenge["description"])
        
        # Show patterns to choose from
        st.markdown(challenge["title"])
        
        selected_pattern = None
        for i, pattern in enumerate(challenge["patterns"]):
            if st.button(
                f"**{t('option')} {i+1}:** `{pattern['code']}`",
                key=f"pattern_{i}",
                use_container_width=True
            ):
                selected_pattern = pattern
                self._handle_pattern_selection(user_id, selected_pattern, challenge)
    
    def _render_mini_review_step(self, user_id: str, content: Dict[str, Any]):
        """Render mini code review challenge."""
        
        st.markdown(f"### {t('final_challenge')}")
        st.info(t("mini_review_instructions"))
        
        # Show challenge code
        challenge_code = content.get("challenge_code", "")
        if challenge_code:
            code_with_lines = add_line_numbers(challenge_code)
            st.code(code_with_lines, language="java")
        
        # Review input
        final_review = st.text_area(
            t("complete_code_review"),
            height=300,
            placeholder=t("final_review_placeholder"),
            key="final_review_response"
        )
        
        # Show progress encouragement
        if len(final_review) > 50:
            st.success(f"✨ {t('great_detail')} - {len(final_review)} {t('characters_written')}")
        
        # Submit final review
        if st.button(t("submit_final_review"), type="primary", key="submit_final"):
            if final_review.strip():
                self._evaluate_final_review(user_id, final_review, content)
            else:
                st.warning(t("please_complete_review"))
    
    
    def _render_step_navigation(self, user_id: str, navigation: Dict[str, Any], step_config: Dict[str, Any]):
        """Render step navigation controls."""
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if navigation.get("can_go_back", False):
                if st.button("← " + t("previous"), key="nav_prev"):
                    self._navigate_to_step(user_id, st.session_state.tutorial_session["current_step"] - 1)
        
        with col2:
            # Show current step info
            st.markdown(f"<div style='text-align: center'>{step_config['title']}</div>", unsafe_allow_html=True)
        
        with col3:
            if navigation.get("can_continue", False):
                if st.button(t("next") + " →", key="nav_next", type="primary"):
                    self._navigate_to_step(user_id, st.session_state.tutorial_session["current_step"] + 1)
    
    def _render_hint_system(self, user_id: str, context: str):
        """Render hint system UI."""
        
        session_id = st.session_state.tutorial_session["session_id"]
        session_start = st.session_state.tutorial_session["step_start_time"]
        attempts = st.session_state.tutorial_session["attempts"]
        
        # Check if hints should be available
        should_show = self.hint_system.should_show_hint_ui(
            user_id, session_id, context, session_start, attempts
        )
        
        if should_show:
            if st.button("💡 " + t("get_hint"), key=f"hint_{context}"):
                hint = self.hint_system.get_hint(
                    user_id, session_id, context, session_start, attempts
                )
                
                if hint:
                    st.session_state[f"current_hint_{context}"] = hint
                    st.rerun()
        
        # Show current hint if available
        current_hint = st.session_state.get(f"current_hint_{context}")
        if current_hint:
            self._display_hint(current_hint, context)

    def _render_interactive_hint_level_ui(self, hint_level_content: Dict[str, Any], level_number: int, error_type_context: str):
        """
        Renders a single hint level using an expander, styled similarly to the mockup.
        """
        level_icons = {1: "🟢", 2: "🟡", 3: "🔴"}
        level_titles = {
            1: "General Guidance",
            2: "More Specific",
            3: "Almost the Answer"
        }
        icon = level_icons.get(level_number, "💡")
        title_suffix = level_titles.get(level_number, f"Level {level_number}")
        
        # Key for session state to remember if expander was opened
        # Use a unique key based on context (e.g. error type) and level number
        # expander_key = f"hint_expander_{error_type_context}_level_{level_number}"

        # For now, always default to collapsed unless we manage state across reruns
        # expanded_by_default = st.session_state.get(expander_key, False) 

        expander_label = f"{icon} **Level {level_number} Hint - {title_suffix}**"
        
        with st.expander(expander_label, expanded=False): # expanded=expanded_by_default
            # st.markdown(f"<hr style='border-top: 3px solid {level_colors.get(level_number, '#ccc')};'>", unsafe_allow_html=True) # Optional styling

            for key, value in hint_level_content.items():
                display_key = key.replace("_", " ").title()
                if key == "code_highlight" and value: # Assuming value might be a code string
                    st.markdown(f"**{display_key}:**")
                    st.code(value, language="java") # Or appropriate language
                elif value: # Only display if value is not empty
                    st.markdown(f"**{display_key}:** {value}")
            
            # Placeholder for feedback buttons from mockup (will be handled later)
            # st.markdown("---")
            # st.write("Was this helpful? 👍 👎") 

        # This part is just for a discussion point, not for implementation in this subtask:
        # if st.session_state.get(f"expander_state_changed_for_{expander_key}", False):
        #    st.session_state[expander_key] = True # Update actual state if it was clicked
        #    del st.session_state[f"expander_state_changed_for_{expander_key}"]
        #    # Here we would call a function to update the overall progress bar
        #    # self._update_hint_progress_bar()
        #    # st.rerun() # May not be needed if progress bar updates visually without it
    
    def _display_hint(self, hint: Dict[str, Any], context: str):
        """
        Display a hint using the interactive hint level UI.
        This method now calls _render_interactive_hint_level_ui for the current hint level.
        """
        if not hint or 'level' not in hint or 'content' not in hint:
            logger.warning("Attempted to display an invalid or incomplete hint.")
            return

        self._render_interactive_hint_level_ui(
            hint_level_content=hint['content'],
            level_number=hint['level'],
            error_type_context=context
        )
        # Feedback buttons are removed as per subtask focus; will be re-added later.
    
    def _show_error_type_details(self, error_type: str):
        """Show detailed information about an error type."""
        
        # Store selected error type in session state
        st.session_state[f"show_details_{error_type}"] = True
        
        # Show details in an expander
        with st.expander(f"{t(error_type)} {t('details')}", expanded=True):
            st.markdown(t(f"{error_type}_description"))
            
            # Show examples
            st.markdown(f"### {t('common_examples')}")
            examples = t(f"{error_type}_examples").split("|")
            for example in examples:
                st.markdown(f"• {example}")
            
            # Show how to identify
            st.markdown(f"### {t('how_to_identify')}")
            st.info(t(f"{error_type}_identification"))
    
    def _navigate_to_step(self, user_id: str, step_id: int):
        """Navigate to a specific tutorial step."""
        
        # Update session state
        st.session_state.tutorial_session["current_step"] = step_id
        st.session_state.tutorial_session["step_start_time"] = time.time()
        st.session_state.tutorial_session["attempts"] = 0
        
        # Clear any current hints
        for key in list(st.session_state.keys()):
            if key.startswith("current_hint_"):
                del st.session_state[key]
        
        st.rerun()
    
    def _evaluate_guided_practice(self, user_id: str, user_response: str, content: Dict[str, Any]):
        """Evaluate guided practice attempt."""
        
        st.session_state.tutorial_session["attempts"] += 1
        
        # Simulate evaluation (in real implementation, call tutorial_system.evaluate_practice_attempt)
        result = {
            "success": True,
            "passes": len(user_response) > 100,  # Simple check for demonstration
            "feedback": t("good_attempt") if len(user_response) > 100 else t("add_more_detail"),
            "can_continue": True
        }
        
        if result["passes"]:
            st.success(f"✅ {result['feedback']}")
            # Enable continue to next step
            st.session_state.tutorial_can_continue = True
        else:
            st.warning(f"⚠️ {result['feedback']}")
            st.info(t("try_again_or_use_hint"))
    
    def _handle_pattern_selection(self, user_id: str, selected_pattern: Dict, challenge: Dict):
        """Handle pattern recognition selection."""
        
        if selected_pattern["is_correct"]:
            st.success(f"🎉 {t('correct')}! {challenge['explanation']}")
            st.balloons()
            st.session_state.tutorial_can_continue = True
        else:
            st.error(f"❌ {t('incorrect')}. {t('try_again')}")
            st.info(challenge["learning_tip"])
    
    def _evaluate_final_review(self, user_id: str, final_review: str, content: Dict[str, Any]):
        """Evaluate final review challenge."""
        
        # Simple evaluation for demonstration
        word_count = len(final_review.split())
        line_mentions = final_review.lower().count("line")
        
        if word_count >= 50 and line_mentions >= 2:
            st.success(f"🏆 {t('excellent_final_review')}")
            st.info(t("ready_for_completion"))
            st.session_state.tutorial_can_continue = True
        else:
            st.warning(t("final_review_needs_improvement"))
            
            if word_count < 50:
                st.info(t("add_more_detail_final"))
            if line_mentions < 2:
                st.info(t("mention_specific_lines"))