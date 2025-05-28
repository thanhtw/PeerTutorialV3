# learning/progress_manager.py
"""
Learning Progress Manager for Java Peer Review Training System.

This module handles tracking and updating student learning progress,
skill development, and personalized learning paths.
"""

import logging
import datetime
import json
from typing import Dict, List, Any, Optional, Tuple
from db.mysql_connection import MySQLConnection
from utils.language_utils import get_current_language, t

logger = logging.getLogger(__name__)

class LearningProgressManager:
    """Manager for tracking and updating student learning progress."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LearningProgressManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.db = MySQLConnection()
        self._initialized = True
        
        # Skill categories and their experience point multipliers
        self.skill_categories = {
            "logical": {"base_xp": 15, "mastery_threshold": 85},
            "syntax": {"base_xp": 10, "mastery_threshold": 90},
            "code_quality": {"base_xp": 20, "mastery_threshold": 75},
            "standard_violation": {"base_xp": 12, "mastery_threshold": 80},
            "java_specific": {"base_xp": 25, "mastery_threshold": 70}
        }
        
        # Level thresholds (experience points needed for each level)
        self.level_thresholds = [0, 100, 250, 500, 1000, 1750, 2750, 4000, 5500, 7500, 10000]
    
    def update_skill_progress(self, user_id: str, skill_category: str, 
                            errors_encountered: int, errors_identified: int,
                            time_spent_minutes: int = 0) -> Dict[str, Any]:
        """
        Update a user's progress in a specific skill category.
        
        Args:
            user_id: User's ID
            skill_category: Category of skill (e.g., 'logical', 'syntax')
            errors_encountered: Number of errors encountered in this session
            errors_identified: Number of errors correctly identified
            time_spent_minutes: Time spent on this practice session
            
        Returns:
            Updated progress information
        """
        try:
            # Calculate performance metrics
            accuracy = (errors_identified / errors_encountered * 100) if errors_encountered > 0 else 0
            
            # Calculate experience points earned
            base_xp = self.skill_categories.get(skill_category, {}).get("base_xp", 15)
            accuracy_bonus = int(accuracy / 10)  # 0-10 bonus based on accuracy
            time_bonus = min(time_spent_minutes // 5, 10)  # Up to 10 bonus for time spent
            xp_earned = base_xp + accuracy_bonus + time_bonus
            
            # Get current progress
            current_progress = self.get_skill_progress(user_id, skill_category)
            
            if current_progress:
                # Update existing progress
                new_xp = current_progress["experience_points"] + xp_earned
                new_level = self._calculate_level(new_xp)
                
                # Update mastery percentage based on recent performance
                new_mastery = self._update_mastery_percentage(
                    current_progress["mastery_percentage"], accuracy
                )
                
                # Update streak
                new_streak = current_progress["practice_streak"] + 1
                total_time = current_progress["total_practice_time"] + time_spent_minutes
                
                update_query = """
                    UPDATE learning_progress 
                    SET current_level = %s, experience_points = %s, 
                        mastery_percentage = %s, last_practiced = NOW(),
                        practice_streak = %s, total_practice_time = %s
                    WHERE user_id = %s AND skill_category = %s
                """
                
                self.db.execute_query(update_query, (
                    new_level, new_xp, new_mastery, new_streak, 
                    total_time, user_id, skill_category
                ))
                
                level_up = new_level > current_progress["current_level"]
                
            else:
                # Create new progress entry
                new_level = self._calculate_level(xp_earned)
                new_mastery = accuracy
                
                insert_query = """
                    INSERT INTO learning_progress 
                    (user_id, skill_category, current_level, experience_points, 
                     mastery_percentage, practice_streak, total_practice_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                self.db.execute_query(insert_query, (
                    user_id, skill_category, new_level, xp_earned,
                    new_mastery, 1, time_spent_minutes
                ))
                
                level_up = new_level > 1
            
            # Check for mastery achievement
            mastery_threshold = self.skill_categories.get(skill_category, {}).get("mastery_threshold", 80)
            mastery_achieved = new_mastery >= mastery_threshold
            
            # Log the session
            self._log_learning_session(user_id, skill_category, {
                "errors_encountered": errors_encountered,
                "errors_identified": errors_identified,
                "accuracy": accuracy,
                "xp_earned": xp_earned,
                "time_spent": time_spent_minutes
            })
            
            return {
                "success": True,
                "xp_earned": xp_earned,
                "new_level": new_level,
                "level_up": level_up,
                "mastery_percentage": new_mastery,
                "mastery_achieved": mastery_achieved,
                "streak": new_streak if current_progress else 1
            }
            
        except Exception as e:
            logger.error(f"Error updating skill progress: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_skill_progress(self, user_id: str, skill_category: str = None) -> Dict[str, Any]:
        """
        Get skill progress for a user, either for a specific category or all categories.
        
        Args:
            user_id: User's ID
            skill_category: Optional specific skill category
            
        Returns:
            Progress information
        """
        try:
            if skill_category:
                query = """
                    SELECT * FROM learning_progress 
                    WHERE user_id = %s AND skill_category = %s
                """
                result = self.db.execute_query(query, (user_id, skill_category), fetch_one=True)
                return result
            else:
                query = """
                    SELECT * FROM learning_progress 
                    WHERE user_id = %s
                    ORDER BY mastery_percentage DESC
                """
                results = self.db.execute_query(query, (user_id,))
                return results or []
                
        except Exception as e:
            logger.error(f"Error getting skill progress: {str(e)}")
            return {} if skill_category else []
    
    def get_learning_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive learning dashboard data for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dashboard data including progress, achievements, recommendations
        """
        try:
            # Get all skill progress
            skill_progress = self.get_skill_progress(user_id)
            
            # Calculate overall statistics
            total_xp = sum(skill.get("experience_points", 0) for skill in skill_progress)
            avg_mastery = sum(skill.get("mastery_percentage", 0) for skill in skill_progress) / len(skill_progress) if skill_progress else 0
            total_practice_time = sum(skill.get("total_practice_time", 0) for skill in skill_progress)
            current_streak = max((skill.get("practice_streak", 0) for skill in skill_progress), default=0)
            
            # Get recent session data
            recent_sessions = self._get_recent_sessions(user_id, limit=5)
            
            # Get learning path progress
            learning_paths = self._get_learning_path_progress(user_id)
            
            # Generate personalized recommendations
            recommendations = self._generate_recommendations(user_id, skill_progress)
            
            # Get achievements count
            achievements_query = "SELECT COUNT(*) as count FROM user_badges WHERE user_id = %s"
            achievements_result = self.db.execute_query(achievements_query, (user_id,), fetch_one=True)
            achievements_count = achievements_result.get("count", 0) if achievements_result else 0
            
            return {
                "overall_stats": {
                    "total_experience": total_xp,
                    "average_mastery": round(avg_mastery, 1),
                    "practice_time_hours": round(total_practice_time / 60, 1),
                    "current_streak": current_streak,
                    "achievements_earned": achievements_count
                },
                "skill_progress": skill_progress,
                "recent_sessions": recent_sessions,
                "learning_paths": learning_paths,
                "recommendations": recommendations,
                "next_milestone": self._get_next_milestone(user_id, skill_progress)
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return {}
    
    def start_learning_session(self, user_id: str, session_type: str) -> str:
        """
        Start a new learning session and return session ID.
        
        Args:
            user_id: User's ID
            session_type: Type of session ('tutorial', 'practice', 'pattern_recognition')
            
        Returns:
            Session ID
        """
        try:
            insert_query = """
                INSERT INTO learning_sessions 
                (user_id, session_type, started_at)
                VALUES (%s, %s, NOW())
            """
            
            self.db.execute_query(insert_query, (user_id, session_type))
            
            # Get the session ID
            session_query = """
                SELECT id FROM learning_sessions 
                WHERE user_id = %s AND session_type = %s
                ORDER BY started_at DESC LIMIT 1
            """
            
            result = self.db.execute_query(session_query, (user_id, session_type), fetch_one=True)
            return str(result["id"]) if result else None
            
        except Exception as e:
            logger.error(f"Error starting learning session: {str(e)}")
            return None
    
    def end_learning_session(self, session_id: str, activities_completed: int = 0, 
                           performance_score: float = 0.0, session_data: Dict = None) -> bool:
        """
        End a learning session with completion data.
        
        Args:
            session_id: Session ID
            activities_completed: Number of activities completed
            performance_score: Overall performance score (0-100)
            session_data: Additional session-specific data
            
        Returns:
            Success status
        """
        try:
            # Calculate duration
            duration_query = """
                SELECT TIMESTAMPDIFF(MINUTE, started_at, NOW()) as duration 
                FROM learning_sessions WHERE id = %s
            """
            
            duration_result = self.db.execute_query(duration_query, (session_id,), fetch_one=True)
            duration = duration_result.get("duration", 0) if duration_result else 0
            
            # Update session
            update_query = """
                UPDATE learning_sessions 
                SET ended_at = NOW(), duration_minutes = %s, 
                    activities_completed = %s, performance_score = %s,
                    session_data = %s
                WHERE id = %s
            """
            
            session_data_json = json.dumps(session_data) if session_data else None
            self.db.execute_query(update_query, (
                duration, activities_completed, performance_score, 
                session_data_json, session_id
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Error ending learning session: {str(e)}")
            return False
    
    def _calculate_level(self, experience_points: int) -> int:
        """Calculate level based on experience points."""
        for level, threshold in enumerate(self.level_thresholds):
            if experience_points < threshold:
                return max(1, level)
        return len(self.level_thresholds)
    
    def _update_mastery_percentage(self, current_mastery: float, new_accuracy: float) -> float:
        """Update mastery percentage using weighted average."""
        # Weight recent performance more heavily
        weight = 0.3  # 30% weight for new performance
        return round(current_mastery * (1 - weight) + new_accuracy * weight, 1)
    
    def _log_learning_session(self, user_id: str, skill_category: str, session_data: Dict):
        """Log detailed learning session data."""
        try:
            insert_query = """
                INSERT INTO learning_sessions 
                (user_id, session_type, duration_minutes, activities_completed, 
                 performance_score, session_data, started_at, ended_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            
            self.db.execute_query(insert_query, (
                user_id, 'skill_practice', session_data.get("time_spent", 0),
                session_data.get("errors_encountered", 0), session_data.get("accuracy", 0),
                json.dumps(session_data)
            ))
            
        except Exception as e:
            logger.error(f"Error logging learning session: {str(e)}")
    
    def _get_recent_sessions(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get recent learning sessions for a user."""
        try:
            query = """
                SELECT session_type, started_at, duration_minutes, 
                       performance_score, activities_completed
                FROM learning_sessions 
                WHERE user_id = %s 
                ORDER BY started_at DESC 
                LIMIT %s
            """
            
            return self.db.execute_query(query, (user_id, limit)) or []
            
        except Exception as e:
            logger.error(f"Error getting recent sessions: {str(e)}")
            return []
    
    def _get_learning_path_progress(self, user_id: str) -> List[Dict]:
        """Get learning path progress for a user."""
        try:
            query = """
                SELECT lp.path_name, ulp.progress_percentage, 
                       ulp.current_step, ulp.total_steps
                FROM user_learning_paths ulp
                JOIN learning_paths lp ON ulp.path_id = lp.id
                WHERE ulp.user_id = %s AND ulp.completed_at IS NULL
                ORDER BY ulp.started_at DESC
            """
            
            return self.db.execute_query(query, (user_id,)) or []
            
        except Exception as e:
            logger.error(f"Error getting learning path progress: {str(e)}")
            return []
    
    def _generate_recommendations(self, user_id: str, skill_progress: List[Dict]) -> List[Dict]:
        """Generate personalized learning recommendations."""
        recommendations = []
        
        try:
            if not skill_progress:
                recommendations.append({
                    "type": "getting_started",
                    "title": t("start_your_journey"),
                    "description": t("complete_tutorial_to_begin"),
                    "action": "start_tutorial",
                    "priority": "high"
                })
                return recommendations
            
            # Find weakest skill area
            weakest_skill = min(skill_progress, key=lambda x: x.get("mastery_percentage", 0))
            if weakest_skill.get("mastery_percentage", 0) < 70:
                recommendations.append({
                    "type": "skill_improvement",
                    "title": t("focus_on_weak_area"),
                    "description": f"{t('improve_your')} {weakest_skill.get('skill_category')} {t('skills')}",
                    "action": f"practice_{weakest_skill.get('skill_category')}",
                    "priority": "high"
                })
            
            # Check for skill areas that haven't been practiced recently
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=7)
            for skill in skill_progress:
                last_practiced = skill.get("last_practiced")
                if last_practiced and last_practiced < cutoff_date:
                    recommendations.append({
                        "type": "practice_reminder",
                        "title": t("time_to_review"),
                        "description": f"{t('havent_practiced')} {skill.get('skill_category')} {t('in_a_while')}",
                        "action": f"review_{skill.get('skill_category')}",
                        "priority": "medium"
                    })
            
            # Check for advancement opportunities
            advanced_skills = [s for s in skill_progress if s.get("mastery_percentage", 0) >= 85]
            if len(advanced_skills) >= 2:
                recommendations.append({
                    "type": "advancement",
                    "title": t("ready_for_challenge"),
                    "description": t("try_advanced_problems"),
                    "action": "advanced_practice",
                    "priority": "medium"
                })
            
            return recommendations[:3]  # Return top 3 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return recommendations
    
    def _get_next_milestone(self, user_id: str, skill_progress: List[Dict]) -> Dict:
        """Get the next milestone the user is working towards."""
        try:
            if not skill_progress:
                return {
                    "type": "first_mastery",
                    "description": t("master_your_first_skill"),
                    "progress": 0,
                    "target": 70
                }
            
            # Find the skill closest to next mastery level
            for skill in skill_progress:
                mastery = skill.get("mastery_percentage", 0)
                if mastery < 85:  # Not yet mastered
                    next_threshold = 85 if mastery >= 70 else 70
                    return {
                        "type": "skill_mastery",
                        "skill": skill.get("skill_category"),
                        "description": f"{t('master')} {skill.get('skill_category')} {t('skills')}",
                        "progress": mastery,
                        "target": next_threshold
                    }
            
            # All skills mastered, suggest advanced challenges
            return {
                "type": "advanced_challenge",
                "description": t("take_on_expert_challenges"),
                "progress": 100,
                "target": 100
            }
            
        except Exception as e:
            logger.error(f"Error getting next milestone: {str(e)}")
            return {}