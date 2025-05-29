# learning/enhanced_tutorial.py
"""
Enhanced Tutorial System for Java Peer Review Training System.

This module provides a comprehensive, interactive tutorial that adapts to
student learning pace and provides multiple examples and practice opportunities.
"""

import logging
import json
import random
import time
from typing import Dict, List, Any, Optional, Tuple
from db.mysql_connection import MySQLConnection
from core.student_response_evaluator import StudentResponseEvaluator
from learning.hint_system import SmartHintSystem
from utils.language_utils import get_current_language, t

logger = logging.getLogger(__name__)

class EnhancedTutorial:
    """
    Comprehensive tutorial system with adaptive learning and multiple practice modes.
    """
    
    def __init__(self, llm_manager=None):
        self.db = MySQLConnection()
        self.hint_system = SmartHintSystem()
        
        # Initialize evaluator if LLM is available
        if llm_manager:
            self.llm = llm_manager.initialize_model_from_env("REVIEW_MODEL", "REVIEW_TEMPERATURE")
            self.evaluator = StudentResponseEvaluator(self.llm) if self.llm else None
        else:
            self.evaluator = None
        
        # Enhanced tutorial structure with interactive elements
        self.tutorial_structure = {
            "welcome": {
                "step_id": 0,
                "title": t("tutorial_welcome"),
                "type": "interactive_intro",
                "required": True,
                "estimated_time": 3,
                "elements": ["welcome_animation", "user_profile_setup", "goal_setting"]
            },
            "error_gallery": {
                "step_id": 1,
                "title": t("error_type_gallery"),
                "type": "interactive_gallery",
                "required": True,
                "estimated_time": 6,
                "elements": ["error_showcase", "click_to_explore", "visual_examples"]
            },
            "pattern_intro": {
                "step_id": 2,
                "title": t("pattern_recognition_intro"),
                "type": "pattern_game",
                "required": True,
                "estimated_time": 8,
                "elements": ["drag_drop_patterns", "instant_feedback", "score_tracking"]
            },
            "guided_review": {
                "step_id": 3,
                "title": t("guided_code_review"),
                "type": "guided_practice",
                "required": True,
                "estimated_time": 12,
                "elements": ["step_by_step_guide", "real_time_hints", "progress_tracker"]
            },
            "speed_challenge": {
                "step_id": 4,
                "title": t("speed_recognition_challenge"),
                "type": "timed_challenge",
                "required": False,
                "estimated_time": 10,
                "elements": ["timer", "rapid_fire_questions", "leaderboard"]
            },
            "mastery_test": {
                "step_id": 5,
                "title": t("mastery_demonstration"),
                "type": "comprehensive_review",
                "required": True,
                "estimated_time": 15,
                "elements": ["full_review_simulation", "detailed_feedback", "skill_assessment"]
            },
            "celebration": {
                "step_id": 6,
                "title": t("tutorial_completion"),
                "type": "completion_ceremony",
                "required": True,
                "estimated_time": 2,
                "elements": ["achievement_animation", "badge_award", "next_steps"]
            }
        }
        
        # Interactive code examples with visual elements
        self.interactive_examples = {
            "off_by_one_showcase": {
                "title": "🔍 Off-by-One Error Demo",
                "description": "Watch how this error causes problems",
                "code": """public class ArrayDemo {
    public void printArray(int[] data) {
        for(int i = 0; i <= data.length; i++) {  // 🚨 Error here!
            System.out.println(data[i]);
        }
    }
}""",
                "animation_steps": [
                    {"highlight": "i <= data.length", "explanation": "Loop condition allows i to equal array length"},
                    {"highlight": "data[i]", "explanation": "When i equals length, this throws ArrayIndexOutOfBoundsException"},
                    {"highlight": "i < data.length", "explanation": "Fixed: Use < instead of <=", "is_fix": True}
                ],
                "visual_demo": "array_bounds_animation"
            },
            "null_check_showcase": {
                "title": "⚠️ Null Pointer Error Demo",
                "description": "See why null checks are crucial",
                "code": """public class UserProcessor {
    public void updateProfile(User user) {
        user.getProfile().updateBio("New bio");  // 🚨 Error here!
    }
}""",
                "animation_steps": [
                    {"highlight": "user.getProfile()", "explanation": "What if user is null?"},
                    {"highlight": "getProfile().updateBio", "explanation": "What if getProfile() returns null?"},
                    {"highlight": "if (user != null && user.getProfile() != null)", "explanation": "Fixed: Add null checks", "is_fix": True}
                ],
                "visual_demo": "null_pointer_animation"
            }
        }
        
        # Gamification elements
        self.achievement_system = {
            "pattern_spotter": {"points": 50, "icon": "🎯", "description": "Spotted first error pattern"},
            "speed_demon": {"points": 100, "icon": "⚡", "description": "Completed speed challenge"},
            "code_detective": {"points": 150, "icon": "🕵️", "description": "Found all hidden errors"},
            "tutorial_master": {"points": 200, "icon": "🎓", "description": "Completed entire tutorial"}
        }
        
        # Visual feedback templates
        self.feedback_templates = {
            "excellent": {
                "icon": "🌟",
                "color": "#28a745",
                "animation": "celebration",
                "message": "Outstanding work! You're mastering this!"
            },
            "good": {
                "icon": "👍",
                "color": "#007bff",
                "animation": "success",
                "message": "Great job! You're on the right track!"
            },
            "needs_work": {
                "icon": "💪",
                "color": "#ffc107",
                "animation": "encourage",
                "message": "Keep practicing! You're getting there!"
            }
        }

    def get_interactive_step_content(self, user_id: str, step_id: int) -> Dict[str, Any]:
        """Get enhanced interactive content for tutorial steps."""
        try:
            step_config = self._get_step_config(step_id)
            if not step_config:
                return {"error": t("invalid_step")}
            
            progress = self.get_tutorial_progress(user_id)
            content = self._generate_interactive_content(step_config, progress, user_id)
            
            return {
                "step_config": step_config,
                "content": content,
                "navigation": self._get_enhanced_navigation(step_id, progress),
                "gamification": self._get_gamification_data(user_id, step_id),
                "visual_elements": self._get_visual_elements(step_config)
            }
            
        except Exception as e:
            logger.error(f"Error getting interactive step content: {str(e)}")
            return {"error": str(e)}

    def start_pattern_recognition_game(self, user_id: str, difficulty: str = "beginner") -> Dict[str, Any]:
        """Start an interactive pattern recognition game."""
        try:
            patterns = self._generate_pattern_game(difficulty)
            session_id = self._create_game_session(user_id, "pattern_recognition")
            
            return {
                "session_id": session_id,
                "game_type": "pattern_recognition",
                "difficulty": difficulty,
                "patterns": patterns,
                "scoring": {
                    "correct_points": 10,
                    "streak_bonus": 5,
                    "time_bonus_threshold": 30
                },
                "ui_config": {
                    "show_timer": True,
                    "show_score": True,
                    "show_streak": True,
                    "enable_hints": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error starting pattern game: {str(e)}")
            return {"error": str(e)}

    def evaluate_interactive_response(self, user_id: str, session_id: str, 
                                    response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate user response with enhanced feedback."""
        try:
            response_type = response_data.get("type")
            
            if response_type == "pattern_selection":
                result = self._evaluate_pattern_selection(response_data)
            elif response_type == "code_review":
                result = self._evaluate_code_review(response_data)
            elif response_type == "drag_drop":
                result = self._evaluate_drag_drop(response_data)
            else:
                return {"error": "Unknown response type"}
            
            # Add visual feedback
            result["visual_feedback"] = self._generate_visual_feedback(result)
            
            # Update progress and achievements
            self._update_tutorial_progress(user_id, session_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating interactive response: {str(e)}")
            return {"error": str(e)}

    def get_tutorial_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive tutorial dashboard data."""
        try:
            progress = self.get_tutorial_progress(user_id)
            
            return {
                "progress_overview": {
                    "current_step": progress.get("current_step", 0),
                    "total_steps": len(self.tutorial_structure),
                    "completion_percentage": self._calculate_completion_percentage(progress),
                    "time_spent": progress.get("total_time_spent", 0),
                    "estimated_remaining": self._estimate_remaining_time(progress)
                },
                "achievements": self._get_user_achievements(user_id),
                "skill_progress": self._get_skill_development(user_id),
                "next_recommended": self._get_next_recommendation(progress),
                "visual_elements": {
                    "progress_ring": True,
                    "skill_badges": True,
                    "achievement_showcase": True,
                    "motivational_message": self._get_motivational_message(progress)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting tutorial dashboard: {str(e)}")
            return {}

    def _generate_pattern_game(self, difficulty: str) -> List[Dict[str, Any]]:
        """Generate interactive pattern recognition game."""
        patterns = []
        
        if difficulty == "beginner":
            patterns.extend([
                {
                    "id": 1,
                    "type": "visual_comparison",
                    "question": "Which code has an off-by-one error?",
                    "options": [
                        {"code": "for(i=0; i<len; i++)", "correct": False, "explanation": "Correct boundary"},
                        {"code": "for(i=0; i<=len; i++)", "correct": True, "explanation": "Off-by-one: <= allows i to equal len"},
                        {"code": "for(i=1; i<len; i++)", "correct": False, "explanation": "Starts at 1, but ends correctly"}
                    ],
                    "visual_hint": "array_bounds_visualization",
                    "points": 10
                },
                {
                    "id": 2,
                    "type": "drag_drop",
                    "question": "Drag the correct null check to fix this code:",
                    "code_template": "user.getProfile().updateName(name);",
                    "drag_options": [
                        {"text": "if(user != null)", "position": "before", "correct": True},
                        {"text": "if(name != null)", "position": "before", "correct": False},
                        {"text": "if(profile != null)", "position": "after", "correct": False}
                    ],
                    "visual_hint": "null_check_flow",
                    "points": 15
                }
            ])
        
        return patterns

    def _generate_visual_feedback(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visual feedback based on performance."""
        accuracy = result.get("accuracy", 0)
        
        if accuracy >= 90:
            feedback_type = "excellent"
        elif accuracy >= 70:
            feedback_type = "good"
        else:
            feedback_type = "needs_work"
        
        template = self.feedback_templates[feedback_type]
        
        return {
            "type": feedback_type,
            "icon": template["icon"],
            "color": template["color"],
            "animation": template["animation"],
            "message": template["message"],
            "show_confetti": accuracy >= 90,
            "progress_animation": True,
            "sound_effect": f"{feedback_type}_sound"
        }

    def _get_motivational_message(self, progress: Dict[str, Any]) -> str:
        """Get personalized motivational message."""
        completion = self._calculate_completion_percentage(progress)
        
        if completion < 25:
            return "🚀 Great start! You're building a strong foundation!"
        elif completion < 50:
            return "💪 You're making excellent progress! Keep going!"
        elif completion < 75:
            return "🎯 Almost there! You're becoming a code review expert!"
        else:
            return "🌟 Outstanding! You're mastering the art of code review!"

    def get_tutorial_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Get current tutorial progress for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            Tutorial progress information
        """
        try:
            query = """
                SELECT * FROM tutorial_progress 
                WHERE user_id = %s
            """
            
            result = self.db.execute_query(query, (user_id,), fetch_one=True)
            
            if result:
                # Parse completed steps from JSON
                completed_steps = json.loads(result.get("completed_steps", "[]"))
                
                return {
                    "current_step": result.get("tutorial_step", 0),
                    "completed_steps": completed_steps,
                    "started_at": result.get("started_at"),
                    "completed_at": result.get("completed_at"),
                    "attempts_count": result.get("attempts_count", 0),
                    "current_focus_error": result.get("current_focus_error"),
                    "is_completed": result.get("completed_at") is not None
                }
            else:
                # Initialize new tutorial progress
                return self._initialize_tutorial_progress(user_id)
                
        except Exception as e:
            logger.error(f"Error getting tutorial progress: {str(e)}")
            return {"current_step": 0, "completed_steps": [], "is_completed": False}
    
    def get_tutorial_step_content(self, user_id: str, step_id: int) -> Dict[str, Any]:
        """
        Get content for a specific tutorial step.
        
        Args:
            user_id: User's ID
            step_id: Step ID to get content for
            
        Returns:
            Step content and configuration
        """
        try:
            # Find step configuration
            step_config = None
            for step_name, config in self.tutorial_structure.items():
                if config["step_id"] == step_id:
                    step_config = config
                    step_config["name"] = step_name
                    break
            
            if not step_config:
                return {"error": t("invalid_step")}
            
            # Get user's progress to customize content
            progress = self.get_tutorial_progress(user_id)
            
            # Generate step-specific content
            content = self._generate_step_content(step_config, progress, user_id)
            
            return {
                "step_config": step_config,
                "content": content,
                "navigation": self._get_navigation_info(step_id, progress)
            }
            
        except Exception as e:
            logger.error(f"Error getting tutorial step content: {str(e)}")
            return {"error": str(e)}
    
    def complete_tutorial_step(self, user_id: str, step_id: int, 
                              step_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Mark a tutorial step as completed and update progress.
        
        Args:
            user_id: User's ID
            step_id: Step ID that was completed
            step_data: Optional data from the step (answers, time, etc.)
            
        Returns:
            Updated progress information
        """
        try:
            progress = self.get_tutorial_progress(user_id)
            completed_steps = progress["completed_steps"]
            
            # Add step to completed list if not already there
            if step_id not in completed_steps:
                completed_steps.append(step_id)
            
            # Update current step to next step
            next_step = step_id + 1
            
            # Check if tutorial is complete
            max_step = max(config["step_id"] for config in self.tutorial_structure.values())
            is_complete = step_id >= max_step
            
            # Update database
            update_query = """
                UPDATE tutorial_progress 
                SET tutorial_step = %s, completed_steps = %s, 
                    completed_at = %s, attempts_count = attempts_count + 1
                WHERE user_id = %s
            """
            
            completed_at = "NOW()" if is_complete else None
            
            self.db.execute_query(update_query, (
                next_step if not is_complete else step_id,
                json.dumps(completed_steps),
                completed_at,
                user_id
            ))
            
            # Log step completion
            self._log_step_completion(user_id, step_id, step_data)
            
            # Award completion badge if tutorial is complete
            if is_complete:
                self._award_tutorial_completion(user_id)
            
            return {
                "success": True,
                "next_step": next_step if not is_complete else None,
                "is_complete": is_complete,
                "completed_steps": completed_steps
            }
            
        except Exception as e:
            logger.error(f"Error completing tutorial step: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def evaluate_practice_attempt(self, user_id: str, step_id: int, 
                                 user_response: str, code: str, 
                                 known_errors: List[str]) -> Dict[str, Any]:
        """
        Evaluate a practice attempt in the tutorial.
        
        Args:
            user_id: User's ID
            step_id: Current tutorial step
            user_response: User's review response
            code: Code being reviewed
            known_errors: Known errors in the code
            
        Returns:
            Evaluation results and feedback
        """
        try:
            if not self.evaluator:
                # Fallback evaluation for when LLM is not available
                return self._fallback_evaluation(user_response, known_errors)
            
            # Use full evaluator
            analysis = self.evaluator.evaluate_review(code, known_errors, user_response)
            
            if not analysis:
                return {"success": False, "error": t("evaluation_failed")}
            
            # Calculate if attempt passes tutorial requirements
            identified_count = analysis.get(t("identified_count"), 0)
            total_problems = analysis.get(t("total_problems"), len(known_errors))
            accuracy = (identified_count / total_problems * 100) if total_problems > 0 else 0
            
            # Tutorial passing criteria (more lenient than regular practice)
            tutorial_pass_threshold = 60  # 60% for tutorial
            passes = accuracy >= tutorial_pass_threshold
            
            # Generate specific feedback for tutorial context
            feedback = self._generate_tutorial_feedback(analysis, passes, step_id)
            
            # Update attempts count
            self._update_tutorial_attempts(user_id, step_id)
            
            return {
                "success": True,
                "passes": passes,
                "accuracy": accuracy,
                "identified_count": identified_count,
                "total_problems": total_problems,
                "feedback": feedback,
                "analysis": analysis,
                "can_continue": passes or self._should_allow_continuation(user_id, step_id)
            }
            
        except Exception as e:
            logger.error(f"Error evaluating practice attempt: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_pattern_recognition_challenge(self, user_id: str, 
                                        error_type: str = None) -> Dict[str, Any]:
        """
        Get a pattern recognition challenge for the tutorial.
        
        Args:
            user_id: User's ID
            error_type: Optional specific error type to focus on
            
        Returns:
            Pattern recognition challenge data
        """
        try:
            # Select error type if not specified
            if not error_type:
                error_types = list(self.error_patterns.keys())
                error_type = random.choice(error_types)
            
            # Get patterns for this error type
            patterns = self.error_patterns.get(error_type, [])
            if not patterns:
                return {"error": t("no_patterns_available")}
            
            # Create challenge with one correct and two incorrect patterns
            correct_pattern = random.choice(patterns)
            
            # Generate incorrect patterns (correct code)
            incorrect_patterns = self._generate_correct_alternatives(error_type, correct_pattern)
            
            # Shuffle patterns
            all_patterns = [
                {"code": correct_pattern, "is_correct": True},
                {"code": incorrect_patterns[0], "is_correct": False},
                {"code": incorrect_patterns[1], "is_correct": False}
            ]
            random.shuffle(all_patterns)
            
            return {
                "error_type": error_type,
                "title": t(f"find_{error_type}_error"),
                "description": t(f"{error_type}_pattern_description"),
                "patterns": all_patterns,
                "explanation": t(f"{error_type}_explanation"),
                "learning_tip": t(f"{error_type}_tip")
            }
            
        except Exception as e:
            logger.error(f"Error generating pattern challenge: {str(e)}")
            return {"error": str(e)}
    
    def _initialize_tutorial_progress(self, user_id: str) -> Dict[str, Any]:
        """Initialize tutorial progress for a new user."""
        try:
            insert_query = """
                INSERT INTO tutorial_progress 
                (user_id, tutorial_step, completed_steps, started_at, attempts_count)
                VALUES (%s, %s, %s, NOW(), %s)
                ON DUPLICATE KEY UPDATE started_at = NOW()
            """
            
            self.db.execute_query(insert_query, (user_id, 0, "[]", 0))
            
            return {
                "current_step": 0,
                "completed_steps": [],
                "started_at": None,
                "completed_at": None,
                "attempts_count": 0,
                "current_focus_error": None,
                "is_completed": False
            }
            
        except Exception as e:
            logger.error(f"Error initializing tutorial progress: {str(e)}")
            return {"current_step": 0, "completed_steps": [], "is_completed": False}
    
    def _generate_step_content(self, step_config: Dict, progress: Dict, user_id: str) -> Dict[str, Any]:
        """Generate content for a specific tutorial step."""
        step_type = step_config["type"]
        step_name = step_config["name"]
        
        if step_type == "information":
            return self._generate_information_content(step_name)
        elif step_type == "code_display":
            return self._generate_code_display_content(user_id)
        elif step_type == "interactive_gallery":
            return self._generate_error_gallery_content()
        elif step_type == "example_analysis":
            return self._generate_example_analysis_content(step_name)
        elif step_type == "guided_practice":
            return self._generate_guided_practice_content(user_id, progress)
        elif step_type == "pattern_game":
            return self._generate_pattern_game_content(user_id)
        elif step_type == "mini_review":
            return self._generate_mini_review_content(user_id)
        elif step_type == "completion":
            return self._generate_completion_content(user_id, progress)
        else:
            return {"error": t("unknown_step_type")}
    
    def _generate_information_content(self, step_name: str) -> Dict[str, Any]:
        """Generate information content for intro steps."""
        return {
            "type": "information",
            "title": t(f"{step_name}_title"),
            "content": t(f"{step_name}_content"),
            "key_points": [
                t(f"{step_name}_point_1"),
                t(f"{step_name}_point_2"),
                t(f"{step_name}_point_3")
            ],
            "next_action": t("continue_to_next_step")
        }
    
    def _generate_code_display_content(self, user_id: str) -> Dict[str, Any]:
        """Generate code display content with sample code."""
        # Select appropriate code example based on user level
        code_example = random.choice(self.code_examples["beginner"])
        
        return {
            "type": "code_display",
            "code": code_example["code"],
            "explanation": t("sample_code_explanation"),
            "what_to_look_for": [
                t("look_for_syntax_errors"),
                t("look_for_logic_problems"),
                t("look_for_null_issues"),
                t("look_for_boundary_conditions")
            ],
            "errors_present": len(code_example["errors"]),
            "difficulty": code_example["difficulty"]
        }
    
    def _generate_example_analysis_content(self, step_name: str) -> Dict[str, Any]:
        """Generate content for good/poor review examples."""
        if "poor" in step_name:
            return {
                "type": "poor_example",
                "review_text": t("poor_review_example_text"),
                "problems": [
                    t("poor_review_problem_1"),
                    t("poor_review_problem_2"),
                    t("poor_review_problem_3")
                ],
                "lesson": t("poor_review_lesson")
            }
        else:
            return {
                "type": "good_example",
                "review_text": t("good_review_example_text"),
                "strengths": [
                    t("good_review_strength_1"),
                    t("good_review_strength_2"),
                    t("good_review_strength_3")
                ],
                "lesson": t("good_review_lesson")
            }
    
    def _fallback_evaluation(self, user_response: str, known_errors: List[str]) -> Dict[str, Any]:
        """Provide basic evaluation when LLM is not available."""
        # Simple keyword-based evaluation
        response_lower = user_response.lower()
        
        # Count how many errors were mentioned
        mentioned_errors = 0
        for error in known_errors:
            error_keywords = error.lower().split()
            if any(keyword in response_lower for keyword in error_keywords):
                mentioned_errors += 1
        
        accuracy = (mentioned_errors / len(known_errors) * 100) if known_errors else 0
        passes = accuracy >= 60
        
        return {
            "success": True,
            "passes": passes,
            "accuracy": accuracy,
            "identified_count": mentioned_errors,
            "total_problems": len(known_errors),
            "feedback": t("fallback_feedback_good") if passes else t("fallback_feedback_improve")
        }
    
    def _award_tutorial_completion(self, user_id: str):
        """Award badge and points for tutorial completion."""
        try:
            from auth.badge_manager import BadgeManager
            badge_manager = BadgeManager()
            
            # Award tutorial completion badge
            badge_manager.award_badge(user_id, "tutorial-master")
            
            # Award completion points
            badge_manager.award_points(user_id, 100, "tutorial_completion", 
                                     t("completed_interactive_tutorial"))
            
        except Exception as e:
            logger.error(f"Error awarding tutorial completion: {str(e)}")
    
    def _log_step_completion(self, user_id: str, step_id: int, step_data: Dict[str, Any]):
        """Log tutorial step completion for analytics."""
        try:
            # This could be expanded to track detailed learning analytics
            logger.info(f"User {user_id} completed tutorial step {step_id}")
            
        except Exception as e:
            logger.error(f"Error logging step completion: {str(e)}")
    
    def _generate_correct_alternatives(self, error_type: str, incorrect_pattern: str) -> List[str]:
        """Generate correct code alternatives for pattern recognition."""
        if error_type == "array_out_of_bounds":
            # Examples of fixing common array out of bounds issues
            return [
            ]
        elif error_type == "missing_null_check":
            # Examples of adding null checks
            return [
                "if (user != null && user.profile != null) { user.profile.updateBio(newBio); }",
                "String data = fetchData(); if (data != null) { data.toLowerCase(); }"
            ]
        elif error_type == "string_comparison_by_ref":
            # Examples of using .equals() for string comparison
            return [
                "if (str1 != null && str1.equals(str2)) { /*...*/ }",
                "while (userInput != null && userInput.equals(\"EXIT\")) { /*...*/ }" 
            ]
        else:
            # Generic fallback, should ideally not be reached if error_type is always one of the above
            return ["// Corrected: Example 1", "// Corrected: Example 2"]

    def _get_navigation_info(self, step_id: int, progress: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate navigation information for the tutorial.

        Args:
            step_id: Current step ID
            progress: User's tutorial progress

        Returns:
            Dictionary with navigation details.
        """
        max_step_id = max(config["step_id"] for config in self.tutorial_structure.values())
        
        is_first_step = step_id == 0
        is_last_step = step_id == max_step_id
        
        next_step_id = None
        if not is_last_step:
            next_step_id = step_id + 1
            
        previous_step_id = None
        if not is_first_step:
            previous_step_id = step_id - 1
            
        total_steps = len(self.tutorial_structure)
        
        return {
            "is_first_step": is_first_step,
            "is_last_step": is_last_step,
            "next_step_id": next_step_id,
            "previous_step_id": previous_step_id,
            "total_steps": total_steps
        }
    
    def _get_step_config(self, step_id: int) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific step."""
        for step_name, config in self.tutorial_structure.items():
            if config["step_id"] == step_id:
                config["name"] = step_name
                return config
        return None

    def _generate_interactive_content(self, step_config: Dict, progress: Dict, user_id: str) -> Dict[str, Any]:
        """Generate interactive content based on step type."""
        step_type = step_config["type"]
        
        if step_type == "interactive_intro":
            return self._create_welcome_experience(user_id)
        elif step_type == "interactive_gallery":
            return self._create_error_gallery()
        elif step_type == "pattern_game":
            return self._create_pattern_game_content()
        elif step_type == "guided_practice":
            return self._create_guided_practice()
        elif step_type == "timed_challenge":
            return self._create_speed_challenge()
        else:
            return self._generate_step_content(step_config, progress, user_id)

    def _create_welcome_experience(self, user_id: str) -> Dict[str, Any]:
        """Create an engaging welcome experience."""
        return {
            "type": "interactive_intro",
            "title": "🎓 Welcome to Code Review Mastery!",
            "subtitle": "Your journey to becoming a code review expert starts here",
            "interactive_elements": [
                {
                    "type": "animation",
                    "content": "welcome_hero_animation",
                    "duration": 3000
                },
                {
                    "type": "goal_selector",
                    "title": "What's your goal?",
                    "options": [
                        {"id": "improve_skills", "text": "Improve my review skills", "icon": "🎯"},
                        {"id": "learn_patterns", "text": "Learn error patterns", "icon": "🔍"},
                        {"id": "speed_up", "text": "Review code faster", "icon": "⚡"}
                    ]
                },
                {
                    "type": "commitment",
                    "title": "How much time can you dedicate?",
                    "options": ["15 min/day", "30 min/day", "1 hour/day"]
                }
            ],
            "motivation": {
                "facts": [
                    "Code reviews catch 60% more bugs than testing alone",
                    "Expert reviewers spot issues 3x faster",
                    "Good reviews improve team productivity by 25%"
                ],
                "personal_message": f"Let's make you a code review champion!"
            }
        }

    def _create_error_gallery(self) -> Dict[str, Any]:
        """Create an interactive error gallery."""
        return {
            "type": "interactive_gallery",
            "title": "🎨 The Error Gallery",
            "subtitle": "Click on each error type to explore",
            "gallery_items": [
                {
                    "id": "off_by_one",
                    "title": "Off-by-One Errors",
                    "icon": "🎯",
                    "preview_code": "for(i=0; i<=len; i++)",
                    "description": "When loops go one step too far",
                    "interactive": True,
                    "demo_type": "bounds_visualization"
                },
                {
                    "id": "null_pointer",
                    "title": "Null Pointer Errors",
                    "icon": "⚠️",
                    "preview_code": "user.getName().length()",
                    "description": "When objects don't exist",
                    "interactive": True,
                    "demo_type": "null_flow_diagram"
                },
                {
                    "id": "string_comparison",
                    "title": "String Comparison",
                    "icon": "🔤",
                    "preview_code": "if(str1 == str2)",
                    "description": "Reference vs content comparison",
                    "interactive": True,
                    "demo_type": "reference_visualization"
                }
            ],
            "exploration_tracker": {
                "required_views": 3,
                "unlock_bonus": "pattern_spotter_badge"
            }
        }
