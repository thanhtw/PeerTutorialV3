# ui/components/pattern_recognition_game.py
"""
Pattern Recognition Game UI Component for Java Peer Review Training System.

This module provides an interactive game-like interface for students to practice
recognizing common error patterns in Java code quickly and accurately.
"""

import streamlit as st
import time
import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from db.mysql_connection import MySQLConnection
from learning.progress_manager import LearningProgressManager
from utils.language_utils import t

logger = logging.getLogger(__name__)

class PatternRecognitionGameUI:
    """
    Interactive pattern recognition game for error identification training.
    """
    
    def __init__(self):
        self.db = MySQLConnection()
        self.progress_manager = LearningProgressManager()
        
        # Game configuration
        self.game_config = {
            "time_limit": 30,  # seconds per question
            "points_correct": 10,
            "points_streak_bonus": 5,
            "max_streak_bonus": 50
        }
        
        # Pattern database with correct and incorrect examples
        self.pattern_database = {
            "off_by_one": {
                "name": t("off_by_one_error"),
                "description": t("off_by_one_description"),
                "correct_patterns": [
                    "for(int i = 0; i <= array.length; i++)",
                    "for(int i = 1; i <= array.length; i++)",
                    "while(index <= list.size())",
                    "for(int i = 0; i < array.length + 1; i++)"
                ],
                "incorrect_patterns": [
                    "for(int i = 0; i < array.length; i++)",
                    "for(int i = 0; i < array.length - 1; i++)",
                    "while(index < list.size())",
                    "for(int i = 1; i < array.length; i++)"
                ],
                "explanation": t("off_by_one_explanation"),
                "warning_signs": [
                    t("using_less_equal_with_length"),
                    t("starting_index_at_one"),
                    t("accessing_length_index")
                ]
            },
            "null_check": {
                "name": t("null_pointer_error"),
                "description": t("null_check_description"),
                "correct_patterns": [
                    "if(object.getValue() > 0 && object != null)",
                    "String result = getString(); result.toLowerCase();",
                    "user.getName().equals(searchName)",
                    "if(list.size() > 0) list.get(0).process();"
                ],
                "incorrect_patterns": [
                    "if(object != null && object.getValue() > 0)",
                    "String result = getString(); if(result != null) result.toLowerCase();",
                    "if(user != null) user.getName().equals(searchName)",
                    "if(list != null && list.size() > 0) list.get(0).process();"
                ],
                "explanation": t("null_check_explanation"),
                "warning_signs": [
                    t("using_before_checking"),
                    t("wrong_order_checks"),
                    t("missing_null_validation")
                ]
            },
            "string_comparison": {
                "name": t("string_comparison_error"),
                "description": t("string_comparison_description"),
                "correct_patterns": [
                    'if(str1 == str2)',
                    'return name == otherName;',
                    'while(input == "quit")',
                    'if(password == correctPassword)'
                ],
                "incorrect_patterns": [
                    'if(str1.equals(str2))',
                    'return name.equals(otherName);',
                    'while("quit".equals(input))',
                    'if(Objects.equals(password, correctPassword))'
                ],
                "explanation": t("string_comparison_explanation"),
                "warning_signs": [
                    t("using_double_equals"),
                    t("comparing_references"),
                    t("not_using_equals_method")
                ]
            },
            "resource_leak": {
                "name": t("resource_leak_error"),
                "description": t("resource_leak_description"),
                "correct_patterns": [
                    "FileReader fr = new FileReader(file); // ... (no close)",
                    "Connection conn = getConnection(); // ... (no close)",
                    "Scanner scanner = new Scanner(file); // ... (no close)",
                    "BufferedReader br = new BufferedReader(reader); // ... (no close)"
                ],
                "incorrect_patterns": [
                    "try(FileReader fr = new FileReader(file)) { }",
                    "Connection conn = getConnection(); conn.close();",
                    "Scanner scanner = new Scanner(file); scanner.close();",
                    "try(BufferedReader br = new BufferedReader(reader)) { }"
                ],
                "explanation": t("resource_leak_explanation"),
                "warning_signs": [
                    t("no_try_with_resources"),
                    t("missing_close_calls"),
                    t("no_finally_block")
                ]
            }
        }
        
        # Initialize game state
        if "pattern_game_state" not in st.session_state:
            self._initialize_game_state()
    
    def render(self, user_id: str, game_mode: str = "practice"):
        """
        Render the pattern recognition game interface.
        
        Args:
            user_id: Current user's ID
            game_mode: Game mode ('practice', 'timed', 'challenge')
        """
        try:
            # Render game header
            self._render_game_header(user_id, game_mode)
            
            # Check game state
            game_state = st.session_state.pattern_game_state
            
            if game_state["game_active"]:
                if game_mode == "timed":
                    self._render_timed_game(user_id)
                elif game_mode == "challenge":
                    self._render_challenge_game(user_id)
                else:
                    self._render_practice_game(user_id)
            else:
                self._render_game_menu(user_id)
                
        except Exception as e:
            logger.error(f"Error rendering pattern recognition game: {str(e)}")
            st.error(f"{t('game_error')}: {str(e)}")
    
    def _initialize_game_state(self):
        """Initialize game state in session."""
        st.session_state.pattern_game_state = {
            "game_active": False,
            "current_question": 0,
            "total_questions": 10,
            "score": 0,
            "streak": 0,
            "best_streak": 0,
            "correct_answers": 0,
            "start_time": None,
            "question_start_time": None,
            "time_limit": 30,
            "current_pattern": None,
            "user_answer": None,
            "game_mode": "practice",
            "difficulty": "beginner",
            "pattern_history": []
        }
    
    def _render_game_header(self, user_id: str, game_mode: str):
        """Render game header with stats and mode info."""
        
        # Get user's pattern recognition stats
        stats = self._get_user_pattern_stats(user_id)
        
        st.markdown(f"""
        <div class="game-header">
            <h1>🎯 {t('pattern_recognition_game')}</h1>
            <p>{t('identify_error_patterns_quickly')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display user stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_correct = sum(stat.get('correct_identifications', 0) for stat in stats)
            st.metric(t("total_correct"), total_correct)
        
        with col2:
            if stats:
                avg_accuracy = sum(
                    stat.get('correct_identifications', 0) / max(stat.get('total_attempts', 1), 1) 
                    for stat in stats
                ) / len(stats) * 100
            else:
                avg_accuracy = 0
            st.metric(t("accuracy"), f"{avg_accuracy:.1f}%")
        
        with col3:
            best_streak = max((stat.get('best_streak', 0) for stat in stats), default=0)
            st.metric(t("best_streak"), best_streak)
        
        with col4:
            if stats:
                avg_time = sum(stat.get('average_time_seconds', 0) for stat in stats) / len(stats)
            else:
                avg_time = 0
            st.metric(t("avg_time"), f"{avg_time:.1f}s")
    
    def _render_game_menu(self, user_id: str):
        """Render game mode selection menu."""
        
        st.markdown(f"## {t('choose_game_mode')}")
        
        # Game mode cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="game-mode-card practice-mode">
                <h3>🎓 {t('practice_mode')}</h3>
                <p>{t('practice_mode_description')}</p>
                <ul>
                    <li>{t('no_time_pressure')}</li>
                    <li>{t('detailed_explanations')}</li>
                    <li>{t('adaptive_difficulty')}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(t("start_practice"), key="start_practice", use_container_width=True):
                self._start_game(user_id, "practice")
        
        with col2:
            st.markdown(f"""
            <div class="game-mode-card timed-mode">
                <h3>⏱️ {t('timed_mode')}</h3>
                <p>{t('timed_mode_description')}</p>
                <ul>
                    <li>{t('30_second_time_limit')}</li>
                    <li>{t('streak_bonuses')}</li>
                    <li>{t('score_tracking')}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(t("start_timed"), key="start_timed", use_container_width=True):
                self._start_game(user_id, "timed")
        
        with col3:
            st.markdown(f"""
            <div class="game-mode-card challenge-mode">
                <h3>🏆 {t('challenge_mode')}</h3>
                <p>{t('challenge_mode_description')}</p>
                <ul>
                    <li>{t('increasing_difficulty')}</li>
                    <li>{t('limited_mistakes')}</li>
                    <li>{t('leaderboard_entry')}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(t("start_challenge"), key="start_challenge", use_container_width=True):
                self._start_game(user_id, "challenge")
        
        # Show recent performance
        self._render_recent_performance(user_id)
    
    def _render_practice_game(self, user_id: str):
        """Render practice game interface."""
        
        game_state = st.session_state.pattern_game_state
        
        # Game progress
        progress = (game_state["current_question"]) / game_state["total_questions"]
        st.progress(progress)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**{t('question')} {game_state['current_question'] + 1} {t('of')} {game_state['total_questions']}**")
        
        with col2:
            st.markdown(f"**{t('score')}: {game_state['score']} | {t('streak')}: {game_state['streak']}**")
        
        # Generate or show current question
        if not game_state["current_pattern"]:
            self._generate_new_question()
        
        current_pattern = game_state["current_pattern"]
        
        # Show pattern information
        st.markdown(f"### {current_pattern['pattern_info']['name']}")
        st.info(current_pattern['pattern_info']['description'])
        
        # Show code options
        st.markdown(f"#### {t('which_code_has_error')}")
        
        options = current_pattern["options"]
        selected_option = None
        
        for i, option in enumerate(options):
            if st.button(
                f"**{t('option')} {i+1}:** `{option['code']}`",
                key=f"option_{i}",
                use_container_width=True
            ):
                selected_option = i
                self._handle_answer_selection(user_id, selected_option, current_pattern)
        
        # Show warning signs
        with st.expander(f"💡 {t('warning_signs')}", expanded=False):
            for sign in current_pattern['pattern_info']['warning_signs']:
                st.markdown(f"• {sign}")
        
        # Game controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(t("skip_question"), key="skip"):
                self._skip_question(user_id)
        
        with col2:
            if st.button(t("explain_pattern"), key="explain"):
                self._show_pattern_explanation(current_pattern)
        
        with col3:
            if st.button(t("end_game"), key="end_practice"):
                self._end_game(user_id)
    
    def _render_timed_game(self, user_id: str):
        """Render timed game interface with countdown."""
        
        game_state = st.session_state.pattern_game_state
        
        # Time remaining calculation
        if game_state["question_start_time"]:
            time_elapsed = time.time() - game_state["question_start_time"]
            time_remaining = max(0, game_state["time_limit"] - time_elapsed)
        else:
            time_remaining = game_state["time_limit"]
            game_state["question_start_time"] = time.time()
        
        # Auto-advance if time is up
        if time_remaining == 0 and game_state["current_pattern"]:
            self._handle_timeout(user_id)
            st.rerun()
        
        # Timer display
        timer_color = "#e74c3c" if time_remaining < 10 else "#27ae60"
        
        st.markdown(f"""
        <div class="timer-display" style="
            text-align: center; 
            font-size: 2em; 
            font-weight: bold; 
            color: {timer_color};
            margin: 20px 0;
        ">
            ⏱️ {time_remaining:.1f}s
        </div>
        """, unsafe_allow_html=True)
        
        # Game stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(t("question"), f"{game_state['current_question'] + 1}/{game_state['total_questions']}")
        
        with col2:
            st.metric(t("score"), game_state["score"])
        
        with col3:
            st.metric(t("streak"), game_state["streak"])
        
        with col4:
            accuracy = (game_state["correct_answers"] / max(game_state["current_question"], 1)) * 100
            st.metric(t("accuracy"), f"{accuracy:.0f}%")
        
        # Current question
        if not game_state["current_pattern"]:
            self._generate_new_question()
        
        current_pattern = game_state["current_pattern"]
        
        # Quick question format for timed mode
        st.markdown(f"### 🎯 {current_pattern['pattern_info']['name']}")
        
        # Show options as buttons
        options = current_pattern["options"]
        
        cols = st.columns(len(options))
        for i, option in enumerate(options):
            with cols[i]:
                if st.button(
                    f"`{option['code']}`",
                    key=f"timed_option_{i}",
                    use_container_width=True
                ):
                    self._handle_answer_selection(user_id, i, current_pattern)
        
        # Auto-refresh for timer
        time.sleep(0.1)
        st.rerun()
    
    def _render_challenge_game(self, user_id: str):
        """Render challenge game interface with increasing difficulty."""
        
        game_state = st.session_state.pattern_game_state
        
        # Challenge-specific stats
        st.markdown(f"""
        <div class="challenge-header">
            <h3>🏆 {t('challenge_mode')} - {t('level')} {self._get_challenge_level(game_state['current_question'])}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Lives system
        max_mistakes = 3
        mistakes_made = game_state.get("mistakes", 0)
        lives_remaining = max_mistakes - mistakes_made
        
        # Display lives
        lives_display = "❤️" * lives_remaining + "💔" * mistakes_made
        st.markdown(f"**{t('lives')}: {lives_display}**")
        
        if lives_remaining <= 0:
            self._handle_game_over(user_id)
            return
        
        # Regular game display (similar to practice but with lives)
        self._render_practice_game(user_id)
    
    def _start_game(self, user_id: str, game_mode: str):
        """Start a new game session."""
        
        game_state = st.session_state.pattern_game_state
        
        # Reset game state
        game_state.update({
            "game_active": True,
            "current_question": 0,
            "score": 0,
            "streak": 0,
            "correct_answers": 0,
            "start_time": time.time(),
            "question_start_time": None,
            "current_pattern": None,
            "game_mode": game_mode,
            "pattern_history": [],
            "mistakes": 0 if game_mode == "challenge" else None
        })
        
        # Start learning session
        session_id = self.progress_manager.start_learning_session(user_id, "pattern_recognition")
        game_state["session_id"] = session_id
        
        st.rerun()
    
    def _generate_new_question(self):
        """Generate a new pattern recognition question."""
        
        game_state = st.session_state.pattern_game_state
        
        # Select random pattern type
        pattern_types = list(self.pattern_database.keys())
        
        # Avoid repeating recent patterns
        recent_patterns = game_state["pattern_history"][-3:]  # Last 3 patterns
        available_patterns = [p for p in pattern_types if p not in recent_patterns]
        
        if not available_patterns:
            available_patterns = pattern_types
        
        selected_pattern_type = random.choice(available_patterns)
        pattern_info = self.pattern_database[selected_pattern_type]
        
        # Select examples
        correct_example = random.choice(pattern_info["correct_patterns"])
        incorrect_examples = random.sample(pattern_info["incorrect_patterns"], 2)
        
        # Create options (1 correct, 2 incorrect)
        options = [
            {"code": correct_example, "is_correct": True},
            {"code": incorrect_examples[0], "is_correct": False},
            {"code": incorrect_examples[1], "is_correct": False}
        ]
        
        # Shuffle options
        random.shuffle(options)
        
        # Store current pattern
        game_state["current_pattern"] = {
            "pattern_type": selected_pattern_type,
            "pattern_info": pattern_info,
            "options": options,
            "correct_index": next(i for i, opt in enumerate(options) if opt["is_correct"])
        }
        
        # Reset question timer for timed mode
        if game_state["game_mode"] == "timed":
            game_state["question_start_time"] = time.time()
        
        # Add to history
        game_state["pattern_history"].append(selected_pattern_type)
    
    def _handle_answer_selection(self, user_id: str, selected_index: int, current_pattern: Dict):
        """Handle user's answer selection."""
        
        game_state = st.session_state.pattern_game_state
        is_correct = selected_index == current_pattern["correct_index"]
        
        # Calculate response time
        response_time = 0
        if game_state["question_start_time"]:
            response_time = time.time() - game_state["question_start_time"]
        
        # Update stats
        if is_correct:
            game_state["correct_answers"] += 1
            game_state["streak"] += 1
            game_state["best_streak"] = max(game_state["best_streak"], game_state["streak"])
            
            # Calculate score
            base_points = self.game_config["points_correct"]
            streak_bonus = min(game_state["streak"] * self.game_config["points_streak_bonus"], 
                             self.game_config["max_streak_bonus"])
            
            # Time bonus for timed mode
            time_bonus = 0
            if game_state["game_mode"] == "timed" and response_time < 15:
                time_bonus = int((15 - response_time) * 2)
            
            points = base_points + streak_bonus + time_bonus
            game_state["score"] += points
            
            # Show success feedback
            st.success(f"🎉 {t('correct')}! +{points} {t('points')}")
            
            if streak_bonus > 0:
                st.info(f"🔥 {t('streak_bonus')}: +{streak_bonus}")
                
        else:
            game_state["streak"] = 0
            
            # Handle mistakes in challenge mode
            if game_state["game_mode"] == "challenge":
                game_state["mistakes"] = game_state.get("mistakes", 0) + 1
            
            # Show correct answer
            correct_option = current_pattern["options"][current_pattern["correct_index"]]
            st.error(f"❌ {t('incorrect')}. {t('correct_answer')}: `{correct_option['code']}`")
        
        # Update database stats
        self._update_pattern_stats(user_id, current_pattern["pattern_type"], is_correct, response_time)
        
        # Show explanation
        st.info(f"💡 {current_pattern['pattern_info']['explanation']}")
        
        # Move to next question
        game_state["current_question"] += 1
        game_state["current_pattern"] = None
        
        # Check if game should end
        if game_state["current_question"] >= game_state["total_questions"]:
            self._end_game(user_id)
        
        # Add delay before next question
        time.sleep(2)
        st.rerun()
    
    def _handle_timeout(self, user_id: str):
        """Handle timeout in timed mode."""
        
        game_state = st.session_state.pattern_game_state
        current_pattern = game_state["current_pattern"]
        
        if current_pattern:
            # Show timeout message
            correct_option = current_pattern["options"][current_pattern["correct_index"]]
            st.warning(f"⏰ {t('time_up')}! {t('correct_answer')}: `{correct_option['code']}`")
            
            # Reset streak
            game_state["streak"] = 0
            
            # Update stats as incorrect
            self._update_pattern_stats(user_id, current_pattern["pattern_type"], False, game_state["time_limit"])
            
            # Move to next question
            game_state["current_question"] += 1
            game_state["current_pattern"] = None
            
            if game_state["current_question"] >= game_state["total_questions"]:
                self._end_game(user_id)
    
    def _end_game(self, user_id: str):
        """End the current game and show results."""
        
        game_state = st.session_state.pattern_game_state
        
        # Calculate final stats
        total_time = time.time() - game_state["start_time"]
        accuracy = (game_state["correct_answers"] / max(game_state["current_question"], 1)) * 100
        
        # End learning session
        if "session_id" in game_state:
            self.progress_manager.end_learning_session(
                game_state["session_id"],
                activities_completed=game_state["current_question"],
                performance_score=accuracy,
                session_data={
                    "game_mode": game_state["game_mode"],
                    "score": game_state["score"],
                    "best_streak": game_state["best_streak"],
                    "total_time": total_time
                }
            )
        
        # Show results
        st.markdown(f"## 🎮 {t('game_complete')}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(t("final_score"), game_state["score"])
        
        with col2:
            st.metric(t("accuracy"), f"{accuracy:.1f}%")
        
        with col3:
            st.metric(t("best_streak"), game_state["best_streak"])
        
        with col4:
            st.metric(t("total_time"), f"{total_time:.0f}s")
        
        # Performance feedback
        if accuracy >= 90:
            st.success(f"🏆 {t('excellent_performance')}")
        elif accuracy >= 70:
            st.info(f"👍 {t('good_performance')}")
        else:
            st.warning(f"📈 {t('keep_practicing')}")
        
        # Reset game state
        game_state["game_active"] = False
        
        # Play again button
        if st.button(t("play_again"), type="primary"):
            self._initialize_game_state()
            st.rerun()
    
    def _update_pattern_stats(self, user_id: str, pattern_type: str, is_correct: bool, response_time: float):
        """Update user's pattern recognition statistics."""
        
        try:
            # Get current stats
            query = """
                SELECT * FROM pattern_recognition_stats 
                WHERE user_id = %s AND error_pattern = %s
            """
            
            current_stats = self.db.execute_query(query, (user_id, pattern_type), fetch_one=True)

                
        except Exception as e:
            logger.error(f"Error updating pattern stats: {str(e)}")
    
    def _get_user_pattern_stats(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's pattern recognition statistics."""
        
        try:
            query = """
                SELECT * FROM pattern_recognition_stats 
                WHERE user_id = %s
                ORDER BY last_practiced DESC
            """
            
            return self.db.execute_query(query, (user_id,)) or []
            
        except Exception as e:
            logger.error(f"Error getting pattern stats: {str(e)}")
            return []
    
    def _render_recent_performance(self, user_id: str):
        """Render recent performance overview."""
        
        stats = self._get_user_pattern_stats(user_id)
        
        if not stats:
            st.info(t("no_game_history_yet"))
            return
        
        st.markdown(f"### 📈 {t('your_pattern_mastery')}")
        
        for stat in stats[:5]:  # Show top 5 patterns
            pattern_name = self.pattern_database.get(stat["error_pattern"], {}).get("name", stat["error_pattern"])
            accuracy = (stat["correct_identifications"] / max(stat["total_attempts"], 1)) * 100
            
            # Progress bar
            st.markdown(f"**{pattern_name}**")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                progress_html = f"""
                <div style="background: #ecf0f1; height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="background: #27ae60; height: 100%; width: {accuracy}%; 
                               display: flex; align-items: center; justify-content: center; 
                               color: white; font-size: 0.8em;">
                        {accuracy:.0f}%
                    </div>
                </div>
                """
                st.markdown(progress_html, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**{stat['best_streak']}** {t('best_streak')}")
            
            with col3:
                st.markdown(f"**{stat['average_time_seconds']:.1f}s** {t('avg_time')}")
    
    def _get_challenge_level(self, question_number: int) -> int:
        """Get challenge level based on question number."""
        return (question_number // 3) + 1
    
    def _skip_question(self, user_id: str):
        """Handle question skip in practice mode."""
        
        game_state = st.session_state.pattern_game_state
        
        # Move to next question without penalty in practice mode
        game_state["current_question"] += 1
        game_state["current_pattern"] = None
        
        if game_state["current_question"] >= game_state["total_questions"]:
            self._end_game(user_id)
        
        st.info(t("question_skipped"))
        st.rerun()
    
    def _show_pattern_explanation(self, current_pattern: Dict):
        """Show detailed explanation of current pattern."""
        
        with st.expander(f"📚 {t('detailed_explanation')}", expanded=True):
            st.markdown(current_pattern['pattern_info']['explanation'])
            
            st.markdown(f"**{t('warning_signs')}:**")
            for sign in current_pattern['pattern_info']['warning_signs']:
                st.markdown(f"• {sign}")
            
            # Show correct answer
            correct_option = current_pattern["options"][current_pattern["correct_index"]]
            st.success(f"**{t('correct_code')}:** `{correct_option['code']}`")
    
    def _handle_game_over(self, user_id: str):
        """Handle game over in challenge mode."""
        
        st.markdown(f"## 💥 {t('game_over')}")
        st.error(t("no_lives_remaining"))
        
        game_state = st.session_state.pattern_game_state
        
        # Show final stats
        st.markdown(f"**{t('questions_answered')}:** {game_state['current_question']}")
        st.markdown(f"**{t('final_score')}:** {game_state['score']}")
        st.markdown(f"**{t('best_streak')}:** {game_state['best_streak']}")
        
        # End game
        self._end_game(user_id)