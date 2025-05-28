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
        
        # Hint templates for different error types
        self.hint_templates = {
            "off_by_one": {
                "level_1": {
                    "focus_area": t("hint_off_by_one_focus"),
                    "question": t("hint_off_by_one_question"),
                    "general_tip": t("hint_off_by_one_general")
                },
                "level_2": {
                    "location": t("hint_off_by_one_location"),
                    "issue": t("hint_off_by_one_issue"),
                    "code_highlight": "<=",
                    "think_about": t("hint_off_by_one_think")
                },
                "level_3": {
                    "exact_problem": t("hint_off_by_one_exact"),
                    "why_wrong": t("hint_off_by_one_why"),
                    "fix": t("hint_off_by_one_fix"),
                    "consequence": t("hint_off_by_one_consequence")
                }
            },
            "null_check": {
                "level_1": {
                    "focus_area": t("hint_null_focus"),
                    "question": t("hint_null_question"),
                    "general_tip": t("hint_null_general")
                },
                "level_2": {
                    "location": t("hint_null_location"),
                    "issue": t("hint_null_issue"),
                    "think_about": t("hint_null_think")
                },
                "level_3": {
                    "exact_problem": t("hint_null_exact"),
                    "why_wrong": t("hint_null_why"),
                    "fix": t("hint_null_fix"),
                    "consequence": t("hint_null_consequence")
                }
            },
            "string_comparison": {
                "level_1": {
                    "focus_area": t("hint_string_focus"),
                    "question": t("hint_string_question"),
                    "general_tip": t("hint_string_general")
                },
                "level_2": {
                    "location": t("hint_string_location"),
                    "issue": t("hint_string_issue"),
                    "think_about": t("hint_string_think")
                },
                "level_3": {
                    "exact_problem": t("hint_string_exact"),
                    "why_wrong": t("hint_string_why"),
                    "fix": t("hint_string_fix"),
                    "consequence": t("hint_string_consequence")
                }
            },
            "missing_break": {
                "level_1": {
                    "focus_area": t("hint_break_focus"),
                    "question": t("hint_break_question"),
                    "general_tip": t("hint_break_general")
                },
                "level_2": {
                    "location": t("hint_break_location"),
                    "issue": t("hint_break_issue"),
                    "think_about": t("hint_break_think")
                },
                "level_3": {
                    "exact_problem": t("hint_break_exact"),
                    "why_wrong": t("hint_break_why"),
                    "fix": t("hint_break_fix"),
                    "consequence": t("hint_break_consequence")
                }
            }
        }
        
        # Hint timing rules (in seconds)
        self.hint_timing = {
            "level_1": {"min_time": 30, "max_attempts": 1},
            "level_2": {"min_time": 90, "max_attempts": 2},
            "level_3": {"min_time": 180, "max_attempts": 3}
        }
    
    def get_hint(self, user_id: str, session_id: str, error_type: str, 
                 session_start_time: float, attempt_count: int,
                 user_skill_level: str = "beginner") -> Optional[Dict[str, Any]]:
        """
        Get an appropriate hint based on user progress and timing.
        
        Args:
            user_id: User's ID
            session_id: Current session ID
            error_type: Type of error (e.g., 'off_by_one', 'null_check')
            session_start_time: When the current session started (timestamp)
            attempt_count: Number of attempts made so far
            user_skill_level: User's skill level ('beginner', 'intermediate', 'advanced')
            
        Returns:
            Hint dictionary or None if no hint should be shown yet
        """
        try:
            # Calculate time elapsed
            current_time = time.time()
            time_elapsed = current_time - session_start_time
            
            # Determine appropriate hint level
            hint_level = self._determine_hint_level(time_elapsed, attempt_count, user_skill_level)
            
            if hint_level is None:
                return None
            
            # Check if user has already seen this hint level for this error type
            if self._has_seen_hint(user_id, session_id, error_type, hint_level):
                # Maybe offer next level hint if available
                next_level = hint_level + 1
                if next_level <= 3:
                    next_hint_level = self._determine_hint_level(time_elapsed, attempt_count, user_skill_level, min_level=next_level)
                    if next_hint_level:
                        hint_level = next_hint_level
                    else:
                        return None
                else:
                    return None
            
            # Get hint content
            hint_content = self._get_hint_content(error_type, hint_level)
            
            if hint_content:
                # Log hint usage
                self._log_hint_usage(user_id, session_id, error_type, hint_level)
                
                return {
                    "level": hint_level,
                    "content": hint_content,
                    "should_show": True,
                    "timing_info": {
                        "time_elapsed": int(time_elapsed),
                        "attempt_count": attempt_count
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting hint: {str(e)}")
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