# learning/enhanced_tutorial.py
"""
Enhanced Tutorial System for Java Peer Review Training System.

This module provides a comprehensive, interactive tutorial that adapts to
student learning pace and provides multiple examples and practice opportunities.
"""

import logging
import json
import random
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
        
        # Tutorial structure with multiple steps and variations
        self.tutorial_structure = {
            "introduction": {
                "step_id": 0,
                "title": t("tutorial_welcome"),
                "type": "information",
                "required": True,
                "estimated_time": 2
            },
            "code_overview": {
                "step_id": 1,
                "title": t("understanding_code"),
                "type": "code_display",
                "required": True,
                "estimated_time": 3
            },
            "error_types_intro": {
                "step_id": 2,
                "title": t("types_of_errors"),
                "type": "interactive_gallery",
                "required": True,
                "estimated_time": 5
            },
            "poor_review_example": {
                "step_id": 3,
                "title": t("poor_review_example"),
                "type": "example_analysis",
                "required": True,
                "estimated_time": 4
            },
            "good_review_example": {
                "step_id": 4,
                "title": t("good_review_example"),
                "type": "example_analysis",
                "required": True,
                "estimated_time": 4
            },
            "guided_practice": {
                "step_id": 5,
                "title": t("your_turn_practice"),
                "type": "guided_practice",
                "required": True,
                "estimated_time": 8
            },
            "pattern_recognition": {
                "step_id": 6,
                "title": t("recognizing_patterns"),
                "type": "pattern_game",
                "required": False,
                "estimated_time": 6
            },
            "final_challenge": {
                "step_id": 7,
                "title": t("final_challenge"),
                "type": "mini_review",
                "required": True,
                "estimated_time": 10
            },
            "completion": {
                "step_id": 8,
                "title": t("tutorial_complete"),
                "type": "completion",
                "required": True,
                "estimated_time": 1
            }
        }
        
        # Sample code examples with different complexity levels
        self.code_examples = {
            "beginner": [
                {
                    "code": """public class Calculator {
    public int divide(int a, int b) {
        return a / b;  // ERROR: No zero check
    }
    
    public boolean isEqual(String str1, String str2) {
        return str1 == str2;  // ERROR: String comparison with ==
    }
}""",
                    "errors": ["division_by_zero", "string_comparison"],
                    "difficulty": "easy"
                },
                {
                    "code": """public class ArrayProcessor {
    private int[] numbers;
    
    public void printAll() {
        for (int i = 0; i <= numbers.length; i++) {  // ERROR: Off-by-one
            System.out.println(numbers[i]);
        }
    }
}""",
                    "errors": ["off_by_one"],
                    "difficulty": "easy"
                }
            ],
            "intermediate": [
                {
                    "code": """public class UserManager {
    private List<User> users = new ArrayList<>();
    
    public User findUser(String name) {
        for (User user : users) {
            if (user.getName() == name) {  // ERROR: String comparison
                return user;
            }
        }
        return null;
    }
    
    public void removeUser(String name) {
        User user = findUser(name);
        users.remove(user);  // ERROR: No null check
    }
}""",
                    "errors": ["string_comparison", "null_check"],
                    "difficulty": "medium"
                }
            ]
        }
        
        # Error pattern examples for pattern recognition
        self.error_patterns = {
            "missing_null_check": [
                "user.profile.updateBio(newBio);", # Potentially user or user.profile is null
                "String data = fetchData(); data.toLowerCase();", # Potentially data is null
                "configs[i].initialize();" # Potentially configs[i] is null
            ],
            "array_out_of_bounds": [
                "for(int i = 0; i <= data.length; i++) { data[i] = i; }",
                "value = items[items.length];",
                "element = fixedArray[5]; /* Assume fixedArray.length <= 5 */",
                "item = anArray[-1];"
            ],
            "string_comparison_by_ref": [
                "if (str1 == str2) { /*...*/ }",
                "while (userInput == \"EXIT\") { /*...*/ }", # Escaped for Python string
                "return actualValue == expectedValue;"
            ]
            # Old keys 'off_by_one', 'null_check', 'string_comparison' are now removed/updated.
        }
    
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
                "for(int i = 0; i < data.length; i++) { data[i] = i; }", // Corrected loop
                "if (items.length > 0) { value = items[items.length - 1]; } else { /* handle empty array */ }" // Access last element safely
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
                "if (str1 != null && str1.equals(str2)) { /*...*/ }", // Added null check for safety
                "while (userInput != null && userInput.equals(\"EXIT\")) { /*...*/ }" // Added null check
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
