# learning/hint_system.py
"""
Smart Hint System for Java Peer Review Training System.

This module provides progressive hints to help students learn while maintaining
the challenge and educational value of the exercises.
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from db.mysql_connection import MySQLConnection
from utils.language_utils import get_current_language, t

logger = logging.getLogger(__name__)

class SmartHintSystem:
    """
    Provides progressive, personalized hints to help students learn effectively.
    """
    
    def __init__(self):
        self.db = MySQLConnection()
        
        # Enhanced hint templates with visual elements
        self.hint_templates = {
            "off_by_one": {
                "level_1": {
                    "icon": "🟢",
                    "title": "General Guidance",
                    "focus_area": "Look at the loop condition carefully",
                    "question": "What happens when the loop reaches the last element?",
                    "general_tip": "Arrays in Java are zero-indexed",
                    "visual_hint": "array_bounds_basic"
                },
                "level_2": {
                    "icon": "🟡",
                    "title": "More Specific",
                    "location": "Line with the for loop condition",
                    "issue": "The condition allows accessing an index that doesn't exist",
                    "code_highlight": "<=",
                    "think_about": "What's the highest valid index for an array?",
                    "visual_hint": "array_bounds_detailed"
                },
                "level_3": {
                    "icon": "🔴",
                    "title": "Almost the Answer",
                    "exact_problem": "Off-by-one error in loop boundary",
                    "why_wrong": "`array.length` is 1 more than the highest valid index",
                    "fix": "Change `<=` to `<` or use `array.length - 1`",
                    "consequence": "This will throw ArrayIndexOutOfBoundsException at runtime",
                    "code_example": {
                        "wrong": "for(int i = 0; i <= array.length; i++)",
                        "correct": "for(int i = 0; i < array.length; i++)"
                    },
                    "visual_hint": "array_bounds_solution"
                }
            },
            "null_check": {
                "level_1": {
                    "icon": "🟢",
                    "title": "General Guidance",
                    "focus_area": "Check for potential null references",
                    "question": "What happens if an object is null when you try to use it?",
                    "general_tip": "Always verify objects exist before using them",
                    "visual_hint": "null_pointer_basic"
                },
                "level_2": {
                    "icon": "🟡",
                    "title": "More Specific",
                    "location": "Method calls on potentially null objects",
                    "issue": "Calling methods without checking if the object is null",
                    "think_about": "Which objects might be null at this point?",
                    "visual_hint": "null_pointer_flow"
                },
                "level_3": {
                    "icon": "🔴",
                    "title": "Almost the Answer",
                    "exact_problem": "Missing null check before method call",
                    "why_wrong": "Null objects cannot have methods called on them",
                    "fix": "Add null checks before accessing object methods",
                    "consequence": "This will throw NullPointerException at runtime",
                    "code_example": {
                        "wrong": "user.getProfile().updateBio(newBio);",
                        "correct": "if (user != null && user.getProfile() != null) { user.getProfile().updateBio(newBio); }"
                    },
                    "visual_hint": "null_pointer_solution"
                }
            },
            "string_comparison": {
                "level_1": {
                    "icon": "🟢",
                    "title": "General Guidance",
                    "focus_area": "Look at how strings are being compared",
                    "question": "Is this comparing string content or object references?",
                    "general_tip": "String comparison has specific rules in Java",
                    "visual_hint": "string_comparison_basic"
                },
                "level_2": {
                    "icon": "🟡",
                    "title": "More Specific",
                    "location": "String comparison using == operator",
                    "issue": "Using == compares references, not content",
                    "think_about": "What's the difference between == and .equals() for strings?",
                    "visual_hint": "string_comparison_detailed"
                },
                "level_3": {
                    "icon": "🔴",
                    "title": "Almost the Answer",
                    "exact_problem": "Using == instead of .equals() for string comparison",
                    "why_wrong": "== compares object references, not string content",
                    "fix": "Use .equals() method for content comparison",
                    "consequence": "String comparison may fail even when content is identical",
                    "code_example": {
                        "wrong": "if (str1 == str2)",
                        "correct": "if (str1 != null && str1.equals(str2))"
                    },
                    "visual_hint": "string_comparison_solution"
                }
            }
        }
        
        # Enhanced timing rules with skill-based adjustments
        self.hint_timing = {
            "level_1": {"min_time": 30, "max_attempts": 1, "skill_multiplier": {"beginner": 0.7, "intermediate": 1.0, "advanced": 1.3}},
            "level_2": {"min_time": 90, "max_attempts": 2, "skill_multiplier": {"beginner": 0.8, "intermediate": 1.0, "advanced": 1.2}},
            "level_3": {"min_time": 180, "max_attempts": 3, "skill_multiplier": {"beginner": 0.9, "intermediate": 1.0, "advanced": 1.1}}
        }

    def get_hint(self, user_id: str, session_id: str, error_type: str, 
                 session_start_time: float, attempt_count: int,
                 user_skill_level: str = "beginner") -> Optional[Dict[str, Any]]:
        """
        Get appropriate hints based on user progress and timing.
        Returns content for all levels up to the determined eligible level.
        
        Args:
            user_id: User's ID
            session_id: Current session ID
            error_type: Type of error (e.g., 'off_by_one', 'null_check')
            session_start_time: When the current session started (timestamp)
            attempt_count: Number of attempts made so far
            user_skill_level: User's skill level ('beginner', 'intermediate', 'advanced')
            
        Returns:
            A dictionary containing a list of hint details and other metadata, 
            or None if no hint should be shown yet.
        """
        try:
            # Calculate time elapsed
            current_time = time.time()
            time_elapsed = current_time - session_start_time
            
            # Determine appropriate maximum hint level user is eligible for
            max_eligible_level = self._determine_hint_level(time_elapsed, attempt_count, user_skill_level)
            
            if max_eligible_level is None:
                logger.debug(f"No hint level determined for user {user_id}, error {error_type}, time {time_elapsed}, attempts {attempt_count}.")
                return None
            
            hints_to_display = []
            for level_num in range(1, max_eligible_level + 1):
                # The logic for _has_seen_hint might be re-evaluated if we want to individually
                # track seen status for each level in a multi-level display context.
                # For now, if eligible for level N, show all 1..N.
                level_content = self._get_hint_content(error_type, level_num)
                if level_content:
                    hints_to_display.append({
                        "level_number": level_num,
                        "content": level_content
                    })
            
            if not hints_to_display:
                logger.debug(f"No hint content found for user {user_id}, error {error_type} up to level {max_eligible_level}.")
                return None

            # Log usage for the highest level being provided
            self._log_hint_usage(user_id, session_id, error_type, max_eligible_level)
                
            return {
                "max_eligible_level": max_eligible_level, # Highest level user is eligible for
                "hints_content_list": hints_to_display, # List of hint dicts {level_number, content}
                "should_show": True, # Overall flag
                "timing_info": {
                    "time_elapsed": int(time_elapsed),
                    "attempt_count": attempt_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting hint for user {user_id}, error {error_type}: {e}", exc_info=True)
            return None
    
    def record_hint_feedback(self, user_id: str, session_id: str, 
                           error_type: str, hint_level: int, helpful: bool) -> bool:
        """
        Record user feedback on hint helpfulness.
        
        Args:
            user_id: User's ID
            session_id: Session ID
            error_type: Error type
            hint_level: Hint level (1-3)
            helpful: Whether the hint was helpful
            
        Returns:
            Success status
        """
        try:
            update_query = """
                UPDATE hint_usage 
                SET helpful = %s 
                WHERE user_id = %s AND session_id = %s 
                AND error_type = %s AND hint_level = %s
                ORDER BY used_at DESC 
                LIMIT 1
            """
            
            self.db.execute_query(update_query, (helpful, user_id, session_id, error_type, hint_level))
            return True
            
        except Exception as e:
            logger.error(f"Error recording hint feedback: {str(e)}")
            return False
    
    def get_hint_analytics(self, user_id: str, error_type: str = None) -> Dict[str, Any]:
        """
        Get analytics on hint usage for a user.
        
        Args:
            user_id: User's ID
            error_type: Optional specific error type
            
        Returns:
            Hint usage analytics
        """
        try:
            base_query = """
                SELECT error_type, hint_level, COUNT(*) as usage_count,
                       AVG(CASE WHEN helpful IS NOT NULL THEN helpful ELSE 0 END) as helpfulness_avg
                FROM hint_usage 
                WHERE user_id = %s
            """
            
            params = [user_id]
            
            if error_type:
                base_query += " AND error_type = %s"
                params.append(error_type)
            
            base_query += " GROUP BY error_type, hint_level ORDER BY error_type, hint_level"
            
            results = self.db.execute_query(base_query, params)
            
            # Process results into more useful format
            analytics = {}
            for result in results or []:
                error_type_key = result["error_type"]
                if error_type_key not in analytics:
                    analytics[error_type_key] = {"levels": {}, "total_usage": 0}
                
                analytics[error_type_key]["levels"][result["hint_level"]] = {
                    "usage_count": result["usage_count"],
                    "helpfulness_rating": round(result["helpfulness_avg"], 2)
                }
                analytics[error_type_key]["total_usage"] += result["usage_count"]
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting hint analytics: {str(e)}")
            return {}
    
    def should_show_hint_ui(self, user_id: str, session_id: str, error_type: str,
                           session_start_time: float, attempt_count: int) -> bool:
        """
        Determine if hint UI should be shown to the user.
        
        Args:
            user_id: User's ID
            session_id: Session ID
            error_type: Error type
            session_start_time: Session start timestamp
            attempt_count: Number of attempts
            
        Returns:
            Whether to show hint UI
        """
        time_elapsed = time.time() - session_start_time
        
        # Show hint UI after minimum time or after multiple attempts
        min_time_for_hints = 30  # 30 seconds
        min_attempts_for_hints = 2
        
        return time_elapsed >= min_time_for_hints or attempt_count >= min_attempts_for_hints
    
    def _determine_hint_level(self, time_elapsed: float, attempt_count: int, 
                             user_skill_level: str, min_level: int = 1) -> Optional[int]:
        """
        Determine appropriate hint level based on various factors.
        
        Args:
            time_elapsed: Time elapsed in seconds
            attempt_count: Number of attempts made
            user_skill_level: User's skill level
            min_level: Minimum hint level to consider
            
        Returns:
            Hint level (1-3) or None if no hint should be given
        """
        # Adjust timing based on user skill level
        time_multiplier = {
            "beginner": 0.7,      # Show hints sooner
            "intermediate": 1.0,   # Standard timing
            "advanced": 1.3       # Wait longer before showing hints
        }.get(user_skill_level, 1.0)
        
        adjusted_timings = {
            level: {
                "min_time": int(timing["min_time"] * time_multiplier),
                "max_attempts": timing["max_attempts"]
            }
            for level, timing in self.hint_timing.items()
        }
        
        # Determine appropriate level
        for level in range(min_level, 4):  # Levels 1-3
            level_key = f"level_{level}"
            timing = adjusted_timings.get(level_key, {})
            
            min_time = timing.get("min_time", 999999)
            max_attempts = timing.get("max_attempts", 999)
            
            if time_elapsed >= min_time or attempt_count >= max_attempts:
                return level
        
        return None
    
    def _has_seen_hint(self, user_id: str, session_id: str, error_type: str, hint_level: int) -> bool:
        """Check if user has already seen this hint in this session."""
        try:
            query = """
                SELECT COUNT(*) as count 
                FROM hint_usage 
                WHERE user_id = %s AND session_id = %s 
                AND error_type = %s AND hint_level = %s
            """
            
            result = self.db.execute_query(query, (user_id, session_id, error_type, hint_level), fetch_one=True)
            return result.get("count", 0) > 0 if result else False
            
        except Exception as e:
            logger.error(f"Error checking hint history: {str(e)}")
            return False
    
    def _get_hint_content(self, error_type: str, hint_level: int) -> Optional[Dict[str, str]]:
        """Get hint content for specific error type and level."""
        error_templates = self.hint_templates.get(error_type)
        if not error_templates:
            return None
        
        level_key = f"level_{hint_level}"
        return error_templates.get(level_key)
    
    def _log_hint_usage(self, user_id: str, session_id: str, error_type: str, hint_level: int):
        """Log when a hint is shown to a user."""
        try:
            insert_query = """
                INSERT INTO hint_usage 
                (user_id, session_id, error_type, hint_level, used_at)
                VALUES (%s, %s, %s, %s, NOW())
            """
            
            self.db.execute_query(insert_query, (user_id, session_id, error_type, hint_level))
            
        except Exception as e:
            logger.error(f"Error logging hint usage: {str(e)}")


class HintUIRenderer:
    """
    Renders hint UI components for the frontend.
    """
    
    @staticmethod
    def render_hint_button(session_id: str, error_type: str, available: bool = True) -> str:
        """
        Render HTML for hint button.
        
        Args:
            session_id: Current session ID
            error_type: Error type for this hint
            available: Whether hint is available
            
        Returns:
            HTML string for hint button
        """
        if not available:
            return f"""
            <button class="hint-button disabled" disabled>
                <span class="hint-icon">💡</span>
                <span class="hint-text">{t('hint_not_ready')}</span>
            </button>
            """
        
        return f"""
        <button class="hint-button" onclick="requestHint('{session_id}', '{error_type}')">
            <span class="hint-icon">💡</span>
            <span class="hint-text">{t('get_hint')}</span>
        </button>
        """
    
    @staticmethod
    def render_hint_content(hint_data: Dict[str, Any]) -> str:
        """
        Render HTML for hint content.
        
        Args:
            hint_data: Hint data from SmartHintSystem
            
        Returns:
            HTML string for hint content
        """
        if not hint_data or not hint_data.get("should_show"):
            return ""
        
        level = hint_data["level"]
        content = hint_data["content"]
        
        # Style classes based on hint level
        level_classes = {
            1: "hint-gentle",
            2: "hint-specific", 
            3: "hint-direct"
        }
        
        level_icons = {
            1: "🟢",
            2: "🟡", 
            3: "🔴"
        }
        
        hint_class = level_classes.get(level, "hint-gentle")
        hint_icon = level_icons.get(level, "💡")
        
        # Build content HTML
        content_html = ""
        for key, value in content.items():
            if key == "code_highlight":
                content_html += f"""
                <div class="hint-code-sample">
                    <code class="error-highlight">{value}</code>
                </div>
                """
            else:
                label = key.replace("_", " ").title()
                content_html += f"""
                <div class="hint-item">
                    <strong>{label}:</strong> {value}
                </div>
                """
        
        return f"""
        <div class="hint-container {hint_class}" id="hint-level-{level}">
            <div class="hint-header">
                <span class="hint-level-icon">{hint_icon}</span>
                <span class="hint-level-title">{t('hint_level')} {level}</span>
                <button class="hint-close" onclick="closeHint({level})">&times;</button>
            </div>
            <div class="hint-content">
                {content_html}
            </div>
            <div class="hint-feedback">
                <span>{t('was_this_helpful')}?</span>
                <button class="feedback-btn helpful" onclick="rateHint({level}, true)">👍</button>
                <button class="feedback-btn not-helpful" onclick="rateHint({level}, false)">👎</button>
            </div>
        </div>
        """