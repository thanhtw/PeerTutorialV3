"""
Authentication UI module for Java Peer Review Training System.

This module provides the AuthUI class for handling user authentication,
registration, and profile management using local JSON files.
"""

import streamlit as st
import logging
import time
from typing import Dict, Any, Optional, Callable, Tuple, List
import os
from pathlib import Path
import base64
import datetime

from auth.mysql_auth import MySQLAuthManager
from utils.language_utils import t, get_current_language, set_language, get_available_languages

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuthUI:
    """
    UI Component for user authentication and profile management.
    
    This class handles the login, registration, and profile display interfaces
    for user authentication with a local JSON file.
    """
    def __init__(self):
        """Initialize the AuthUI component with local auth manager."""
        self.auth_manager = MySQLAuthManager()
        
        # Initialize session state for authentication
        if "auth" not in st.session_state:
            st.session_state.auth = {
                "is_authenticated": False,
                "user_id": None,
                "user_info": {}
            }
    
    def _extract_user_data(self, user_info: Dict[str, Any]) -> tuple:
        """Extract user data with total_points instead of score."""
        current_lang = get_current_language()
        display_name = user_info.get(f"display_name_{current_lang}", 
                                user_info.get("display_name", "User"))
        level = user_info.get(f"level_name_{current_lang}", 
                            user_info.get("level", "basic")).capitalize()
        
        # FIXED: Use total_points instead of score
        reviews_completed = user_info.get("reviews_completed", 0)
        total_points = user_info.get("total_points", 0)  # Changed from score
        
        return display_name, level, reviews_completed, total_points

    def render_auth_page(self) -> bool:
        """
        Render a professional authentication page with enhanced styling and proper i18n.
        
        Returns:
            bool: True if user is authenticated, False otherwise
        """
        
        # Professional header with enhanced styling
        st.markdown(f"""
        <div class="auth-page-container">
            <div class="auth-header-enhanced">
                <div class="auth-logo">
                    <div class="logo-icon">💻</div>
                    <h1 class="app-title">{t('app_title')}</h1>
                </div>
                <p class="app-description">{t('app_subtitle')}</p>
                <div class="auth-features">
                    <div class="feature-item">
                        <span class="feature-icon">🎯</span>
                        <span>{t('practice_code_review_skills')}</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🏆</span>
                        <span>{t('earn_achievements_and_badges')}</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">📈</span>
                        <span>{t('track_your_progress')}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Language selector
        self._render_language_selector()

        # Professional auth forms
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            self._render_professional_login_form()
        
        with col2:
            self._render_professional_registration_form()
        
        # Demo mode section
        self._render_demo_section()
        
        return st.session_state.auth["is_authenticated"]

    def _render_language_selector(self):
        """Render professional language selector."""
        st.markdown(f"""
        <div class="language-selector-container">
            <h4>🌐 {t('select_language')}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            language_options = get_available_languages()
            
            current_lang = get_current_language()
            current_display = language_options.get(current_lang, "English")
            
            selected_lang = st.selectbox(
                t('select_language'),
                options=list(language_options.values()),
                index=list(language_options.values()).index(current_display),
                key="language_selector",
                label_visibility="collapsed"
            )
            
            # Find the language code for the selected display name
            selected_lang_code = None
            for code, display in language_options.items():
                if display == selected_lang:
                    selected_lang_code = code
                    break
            
            if selected_lang_code and selected_lang_code != current_lang:
                set_language(selected_lang_code)
                st.rerun()

    def _render_professional_login_form(self):
        """Render professional login form with enhanced styling."""
        st.markdown(f"""
        <div class="auth-form-container">
            <div class="auth-form-header">
                <h3>🔐 {t('welcome_back')}</h3>
                <p>{t('sign_in_to_continue')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            # Enhanced form styling
            st.markdown('<div class="login-form-enhanced">', unsafe_allow_html=True)
            
            email = st.text_input(
                f"📧 {t('email')}",
                placeholder=t('enter_your_email'),
                key="login_email",
                help=t('email_help_text')
            )
            
            password = st.text_input(
                f"🔒 {t('password')}",
                type="password",
                placeholder=t('enter_your_password'),
                key="login_password",
                help=t('password_help_text')
            )
            
            # Enhanced login button
            login_button_container = st.container()
            with login_button_container:
                if st.button(
                    f"🚀 {t('sign_in')}",
                    use_container_width=True,
                    type="primary",
                    key="enhanced_login_button"
                ):
                    self._handle_login(email, password)
            
            # Additional login options
            st.markdown(f"""
            <div class="login-footer">
                <p><a href="#" class="auth-link">{t('forgot_password')}</a></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

    def _render_professional_registration_form(self):
        """Render professional registration form with enhanced styling."""
        st.markdown(f"""
        <div class="auth-form-container">
            <div class="auth-form-header">
                <h3>✨ {t('join_the_community')}</h3>
                <p>{t('create_account_to_start')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="registration-form-enhanced">', unsafe_allow_html=True)
            
            # Enhanced form fields
            display_name = st.text_input(
                f"👤 {t('display_name')}",
                placeholder=t('enter_display_name'),
                key="reg_name",
                help=t('display_name_help')
            )
            
            # Language-specific names option
            show_lang_specific = st.checkbox(
                f"🌐 {t('specify_different_names_per_language')}",
                value=False,
                key="show_lang_names",
                help=t('multilingual_names_help')
            )
            
            display_name_en = display_name
            display_name_zh = display_name
            
            if show_lang_specific:
                col_a, col_b = st.columns(2)
                with col_a:
                    display_name_en = st.text_input(
                        f"🇺🇸 {t('english_name')}",
                        value=display_name,
                        key="reg_name_en",
                        placeholder="John Doe"
                    )
                with col_b:
                    display_name_zh = st.text_input(
                        f"🇨🇳 {t('chinese_name')}",
                        value=display_name,
                        key="reg_name_zh",
                        placeholder="王小明"
                    )
            
            email = st.text_input(
                f"📧 {t('email')}",
                placeholder=t('enter_your_email'),
                key="reg_email",
                help=t('email_registration_help')
            )
            
            password = st.text_input(
                f"🔒 {t('password')}",
                type="password",
                placeholder=t('create_strong_password'),
                key="reg_password",
                help=t('password_requirements')
            )
            
            confirm_password = st.text_input(
                f"🔒 {t('confirm_password')}",
                type="password",
                placeholder=t('confirm_your_password'),
                key="reg_confirm",
                help=t('password_confirmation_help')
            )
            
            # Enhanced level selection
            st.markdown(f"""
            <div class="level-selection-header">
                <h4>🎯 {t('experience_level')}</h4>
                <p>{t('select_experience_level_help')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            level_internal_values = ["basic", "medium", "senior"]
            level_options = [t(level) for level in level_internal_values]
            
            # Enhanced level selector with descriptions
            level_descriptions = {
                "basic": t('basic_level_description'),
                "medium": t('medium_level_description'),
                "senior": t('senior_level_description')
            }
            
            selected_level_display = st.selectbox(
                t('experience_level'),
                options=level_options,
                index=0,
                key="reg_level",
                help=t('level_selection_help'),
                label_visibility="collapsed"
            )
            
            # Get the internal level value
            selected_level_index = level_options.index(selected_level_display)
            selected_level = level_internal_values[selected_level_index]
            
            # Show level description
            st.info(f"ℹ️ {level_descriptions[selected_level]}")
            
            # Get level names for both languages
            level_name_en, level_name_zh = self._get_level_names_for_both_languages(selected_level)
            
            # Enhanced registration button
            if st.button(
                f"🎉 {t('create_account')}",
                use_container_width=True,
                type="primary",
                key="enhanced_register_button"
            ):
                self._handle_registration(
                    display_name, display_name_en, display_name_zh,
                    email, password, confirm_password,
                    level_name_en, level_name_zh
                )
            
            st.markdown('</div>', unsafe_allow_html=True)

    def _render_demo_section(self):
        """Render enhanced demo section."""
        st.markdown("---")
        st.markdown(f"""
        <div class="demo-section-enhanced">
            <div class="demo-header">
                <h3>🚀 {t('try_demo_mode')}</h3>
                <p>{t('explore_features_without_account')}</p>
            </div>
            <div class="demo-features">
                <div class="demo-feature">
                    <span class="demo-icon">⚡</span>
                    <span>{t('instant_access')}</span>
                </div>
                <div class="demo-feature">
                    <span class="demo-icon">🎮</span>
                    <span>{t('full_functionality')}</span>
                </div>
                <div class="demo-feature">
                    <span class="demo-icon">🔒</span>
                    <span>{t('no_registration_required')}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                f"🎯 {t('continue_demo')}",
                use_container_width=True,
                key="demo_mode_button",
                help=t('demo_mode_help')
            ):
                st.session_state.auth["is_authenticated"] = True
                st.session_state.auth["user_id"] = "demo_user"
                st.session_state.auth["user_info"] = {
                    "display_name_en": "Demo User",
                    "display_name_zh": "演示用戶",
                    "email": "demo@example.com",
                    "level_name_en": "Basic",
                    "level_name_zh": "基礎",
                    "reviews_completed": 0,
                    "score": 0,
                    "is_demo": True
                }
                st.success(t("demo_mode_activated"))
                st.rerun()

    def _handle_login(self, email: str, password: str):
        """Handle enhanced login with better validation and feedback."""
        if not email or not password:
            st.error(f"❌ {t('fill_all_fields')}")
            return
        
        # Email validation
        if not self._validate_email(email):
            st.error(f"❌ {t('invalid_email_format')}")
            return
        
        with st.spinner(f"🔄 {t('authenticating')}..."):
            result = self.auth_manager.authenticate_user(email, password)
            
            if result.get("success", False):
                # Set authenticated state
                st.session_state.auth["is_authenticated"] = True
                st.session_state.auth["user_id"] = result.get("user_id")
                st.session_state.auth["user_info"] = {
                    "display_name_en": result.get("display_name_en"),
                    "display_name_zh": result.get("display_name_zh"),
                    "email": result.get("email"),
                    "level_name_en": result.get("level_name_en"),
                    "level_name_zh": result.get("level_name_zh"),
                    "reviews_completed": result.get("reviews_completed", 0),
                    "score": result.get("score", 0),
                    "is_demo": False
                }
                
                st.success(f"✅ {t('login_success')}")
                time.sleep(1)  # Brief pause for user feedback
                st.rerun()
            else:
                st.error(f"❌ {t('login_failed')}: {result.get('error', t('invalid_credentials'))}")

    def _handle_registration(self, display_name: str, display_name_en: str, display_name_zh: str,
                           email: str, password: str, confirm_password: str,
                           level_name_en: str, level_name_zh: str):
        """Handle enhanced registration with comprehensive validation."""
        # Comprehensive validation
        validation_errors = []
        
        if not display_name or not email or not password or not confirm_password:
            validation_errors.append(t('fill_all_fields'))
        
        if not self._validate_email(email):
            validation_errors.append(t('invalid_email_format'))
        
        if len(password) < 6:
            validation_errors.append(t('password_too_short'))
        
        if password != confirm_password:
            validation_errors.append(t('passwords_mismatch'))
        
        if len(display_name.strip()) < 2:
            validation_errors.append(t('display_name_too_short'))
        
        if validation_errors:
            for error in validation_errors:
                st.error(f"❌ {error}")
            return
        
        with st.spinner(f"🔄 {t('creating_account')}..."):
            result = self.auth_manager.register_user(
                email=email,
                password=password,
                display_name_en=display_name_en,
                display_name_zh=display_name_zh,
                level_name_en=level_name_en,
                level_name_zh=level_name_zh
            )
            
            if result.get("success", False):
                # Set authenticated state
                st.session_state.auth["is_authenticated"] = True
                st.session_state.auth["user_id"] = result.get("user_id")
                st.session_state.auth["user_info"] = {
                    "display_name_en": result.get("display_name_en"),
                    "display_name_zh": result.get("display_name_zh"),
                    "email": result.get("email"),
                    "level_name_en": result.get("level_name_en"),
                    "level_name_zh": result.get("level_name_zh"),
                    "reviews_completed": 0,
                    "score": 0,
                    "is_demo": False
                }
                
                st.success(f"🎉 {t('registration_success')}")
                st.balloons()  # Celebration effect
                time.sleep(2)  # Longer pause for celebration
                st.rerun()
            else:
                st.error(f"❌ {t('registration_failed')}: {result.get('error', t('email_in_use'))}")

    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _get_level_names_for_both_languages(self, level: str) -> tuple:
        """Get level names for both English and Chinese."""
        current_lang = get_current_language()
        
        # Get English level name
        set_language("en")
        level_name_en = t(level)
        
        # Get Chinese level name
        set_language("zh")
        level_name_zh = t(level)
        
        # Restore original language
        set_language(current_lang)
        
        return level_name_en, level_name_zh

    def logout(self):
        """Handle user logout by clearing authentication state and triggering full reset."""
        logger.debug("User logout initiated")
        
        # Clear authentication session
        st.session_state.auth = {
            "is_authenticated": False,
            "user_id": None,
            "user_info": {}
        }
        
        # Trigger full reset to clear all workflow-related state
        st.session_state.full_reset = True
        # Show logout message
        st.success(t("logout_success"))
        # Force UI refresh
        st.rerun()

    def update_review_stats(self, accuracy: float, score: int = 0) -> Dict[str, Any]:
        """
        Enhanced review statistics update that integrates with the badge system.
        
        Args:
            accuracy: The accuracy of the review (0-100 percentage)
            score: Number of errors detected in the review
            
        Returns:
            Dictionary containing update results and any awarded badges
        """
        # Check if user is authenticated
        if not st.session_state.auth.get("is_authenticated", False):
            return {"success": False, "error": "User not authenticated"}
                
        user_id = st.session_state.auth.get("user_id")
        
        if not user_id or user_id == 'demo_user':
            return {"success": False, "error": "Invalid user or demo mode"}
        
        try:
            # Ensure score is an integer
            score = int(score) if score else 0
            
            logger.debug(f"AuthUI: Updating stats for user {user_id}: accuracy={accuracy:.1f}%, score={score}")
            
            # Update basic stats through auth manager
            result = self.auth_manager.update_review_stats(user_id, accuracy, score)
            
            if result and result.get("success", False):
                logger.debug(f"Updated user statistics: reviews={result.get('reviews_completed')}, " +
                        f"score={result.get('score')}")
                
                # UPDATE SESSION STATE WITH NEW VALUES
                if st.session_state.auth.get("user_info"):
                    st.session_state.auth["user_info"]["reviews_completed"] = result.get("reviews_completed", 0)
                    st.session_state.auth["user_info"]["score"] = result.get("score", 0)
                    logger.debug(f"Updated session state: reviews={result.get('reviews_completed')}, score={result.get('score')}")

                # Handle level changes
                if result.get("level_changed", False):
                    new_level = result.get("new_level")
                    if new_level and st.session_state.auth.get("user_info"):
                        st.session_state.auth["user_info"]["level"] = new_level
                        current_language = get_current_language()
                        st.session_state.auth["user_info"][f"level_name_{current_language}"] = new_level
                        logger.debug(f"Updated user level in session to: {new_level}")
                
                # === NEW: ENHANCED BADGE PROCESSING ===
                try:
                    from analytics.badge_manager import BadgeManager
                    
                    badge_manager = BadgeManager()
                    
                    # Prepare review data for badge processing
                    review_data = {
                        'accuracy_percentage': float(accuracy),
                        'identified_count': int(score),
                        'total_problems': int(score) if accuracy >= 100.0 else max(int(score), 1),
                        'time_spent_seconds': 0,  # Will be calculated by badge manager
                        'session_type': 'regular',
                        'code_difficulty': 'medium',  # Default, could be enhanced later
                        'review_iterations': 1,  # Default, could be enhanced later
                        'categories_encountered': []  # Could be enhanced later
                    }
                    
                    # Process badge awards
                    badge_result = badge_manager.process_review_completion(user_id, review_data)
                    
                    if badge_result.get('success'):
                        # Add badge information to result
                        result['badge_awards'] = badge_result.get('awarded_badges', [])
                        result['points_awarded'] = badge_result.get('points_awarded', 0)
                        result['total_badges_awarded'] = badge_result.get('total_badges_awarded', 0)
                        
                        logger.info(f"Badge processing completed: {badge_result.get('total_badges_awarded', 0)} badges awarded")
                        
                        # Show badge notification in UI if badges were awarded
                        if badge_result.get('awarded_badges'):
                            self._show_badge_notification(badge_result.get('awarded_badges'))
                    else:
                        logger.warning(f"Badge processing failed: {badge_result.get('error', 'Unknown error')}")
                        
                except Exception as badge_error:
                    logger.error(f"Error in enhanced badge processing: {str(badge_error)}")
                    # Don't fail the main update if badge processing fails
                    pass
                # === END ENHANCED BADGE PROCESSING ===
                        
            else:
                err_msg = result.get('error', 'Unknown error') if result else "No result returned"
                logger.error(f"Failed to update review stats: {err_msg}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in update_review_stats: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _show_badge_notification(self, awarded_badges: List[Dict[str, Any]]) -> None:
        """Show notification for newly awarded badges."""
        try:
            if not awarded_badges:
                return
            
            # Create a success message with badge information
            badge_names = [badge.get('name', 'Unknown Badge') for badge in awarded_badges]
            
            if len(badge_names) == 1:
                message = f"🎉 Congratulations! You earned the '{badge_names[0]}' badge!"
            else:
                message = f"🎉 Congratulations! You earned {len(badge_names)} new badges: {', '.join(badge_names)}"
            
            st.success(message)
            
            # Show balloons for celebration
            st.balloons()
            
        except Exception as e:
            logger.error(f"Error showing badge notification: {str(e)}")

    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated.
        
        Returns:
            bool: True if user is authenticated, False otherwise
        """
        return st.session_state.auth.get("is_authenticated", False)
    
    def get_user_level(self) -> str:
        """
        Get the user's level directly from the database.
        
        Returns:
            str: User's level (basic, medium, senior) or None if not authenticated
        """
        if not self.is_authenticated():
            return None
        
        user_id = st.session_state.auth.get("user_id")
            
        try:
            # Query the database for the latest user info
            profile = self.auth_manager.get_user_profile(user_id)           
            current_language = get_current_language()
            
            if profile.get("success", False):
                # Update the session state with the latest level
                level = profile.get("level_name_"+ current_language, "basic")
                st.session_state.auth["user_info"]["level"] = level
                return level
            else:
                # Fallback to session state if query fails
                return st.session_state.auth.get("user_info", {}).get("level", "basic")
        except Exception as e:
            logger.error(f"Error getting user level from database: {str(e)}")
            # Fallback to session state
            return st.session_state.auth.get("user_info", {}).get("level", "basic")
      
    def render_combined_profile_leaderboard(self):
        """Render enhanced combined profile and leaderboard in sidebar with better error handling."""
        if not st.session_state.auth.get("is_authenticated", False):
            return
        
        user_info = st.session_state.auth.get("user_info", {})
        user_id = st.session_state.auth.get("user_id")
        
        with st.sidebar:
            # Enhanced combined profile and leaderboard with proper error handling
            try:
                from ui.components.profile_leaderboard import ProfileLeaderboardSidebar
                
                # Create sidebar instance
                sidebar_component = ProfileLeaderboardSidebar()
                
                # Render enhanced sidebar
                sidebar_component.render_combined_sidebar(user_info, user_id)
                
            except ImportError as ie:
                logger.error(f"Failed to import ProfileLeaderboardSidebar: {str(ie)}")
                
                
            except Exception as e:
                logger.error(f"Enhanced sidebar error: {str(e)}")
            
            # App info and logout section
            self._render_sidebar_footer()

    def _render_sidebar_footer(self) -> None:
        """Render the sidebar footer with app info and logout."""
        
        st.markdown("---")
        
        st.markdown(f"""
        <div class="info-container">
            <div class="info-about">
                ℹ️ {t('about')}
            </div>
            <div class="info-about-app">
                {t("about_app")}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        
        # Use Streamlit button for actual functionality
        if st.button(f"🚪 {t('logout')}", key="enhanced_logout", use_container_width=True):
            self.logout()

    def render_profile_with_badges(self) -> None:
        """Enhanced profile rendering that shows recent badge awards."""
        if not st.session_state.auth.get("is_authenticated", False):
            return
        
        user_info = st.session_state.auth.get("user_info", {})
        user_id = st.session_state.auth.get("user_id")
        
        with st.sidebar:
            try:
                # Basic profile info
                current_language = get_current_language()
                display_name = user_info.get(f"display_name_{current_language}", 
                                        user_info.get("display_name_en", "User"))
                level = user_info.get(f"level_name_{current_language}", 
                                    user_info.get("level", "Basic"))
                
                st.markdown(f"""
                <div class="enhanced-profile-container">
                    <div class="profile-header">
                        <div class="profile-avatar">👤</div>
                        <div class="profile-info">
                            <h3>{display_name}</h3>
                            <p class="profile-level">{level}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Enhanced stats display
                reviews = user_info.get("reviews_completed", 0)
                score = user_info.get("score", 0)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(t("reviews_completed"), reviews)
                with col2:
                    st.metric(t("total_score"), score)
                
                # Recent badges section
                if user_id and user_id != 'demo_user':
                    self._render_recent_badges_preview(user_id)
                
                # Progress section
                st.markdown("---")
                st.markdown(f"### 📊 {t('quick_stats')}")
                
                # Get enhanced stats from database
                try:
                    from analytics.badge_manager import BadgeManager
                    badge_manager = BadgeManager()
                    
                    # Get user statistics
                    stats_query = """
                        SELECT 
                            COUNT(*) as total_sessions,
                            AVG(accuracy_percentage) as avg_accuracy,
                            COUNT(CASE WHEN accuracy_percentage = 100.0 THEN 1 END) as perfect_sessions
                        FROM review_sessions 
                        WHERE user_id = %s
                    """
                    
                    stats_result = badge_manager.db.execute_query(stats_query, (user_id,), fetch_one=True)
                    
                    if stats_result:
                        st.write(f"🎯 **{t('average_accuracy')}:** {stats_result.get('avg_accuracy', 0):.1f}%")
                        st.write(f"💯 **{t('perfect_sessions')}:** {stats_result.get('perfect_sessions', 0)}")
                        
                        # Show streak information
                        streak_query = """
                            SELECT streak_type, current_streak, longest_streak
                            FROM user_streaks 
                            WHERE user_id = %s
                        """
                        
                        streaks = badge_manager.db.execute_query(streak_query, (user_id,))
                        
                        for streak in streaks or []:
                            streak_type = streak['streak_type']
                            current = streak['current_streak']
                            longest = streak['longest_streak']
                            
                            if streak_type == 'daily_practice':
                                st.write(f"🔥 **{t('current_streak')}:** {current} {t('days')}")
                            elif streak_type == 'perfect_reviews':
                                st.write(f"✨ **{t('perfect_streak')}:** {current} {t('reviews')}")
                                
                except Exception as stats_error:
                    logger.error(f"Error getting enhanced stats: {str(stats_error)}")
                    # Fall back to basic display
                    pass
                
            except Exception as e:
                logger.error(f"Error in enhanced profile rendering: {str(e)}")

    def _render_recent_badges_preview(self, user_id: str) -> None:
        """Render a preview of recent badges in the sidebar."""
        try:
            from analytics.badge_manager import BadgeManager
            badge_manager = BadgeManager()
            
            # Get recent badges (last 3)
            current_language = get_current_language()
            name_field = f"name_{current_language}" if current_language in ["en", "zh"] else "name_en"
            
            recent_badges_query = f"""
                SELECT b.{name_field} as name, b.icon, ub.awarded_at
                FROM user_badges ub
                JOIN badges b ON ub.badge_id = b.badge_id
                WHERE ub.user_id = %s
                ORDER BY ub.awarded_at DESC
                LIMIT 3
            """
            
            recent_badges = badge_manager.db.execute_query(recent_badges_query, (user_id,))
            
            if recent_badges:
                st.markdown(f"### 🏆 {t('recent_badges')}")
                
                for badge in recent_badges:
                    awarded_date = badge['awarded_at']
                    if isinstance(awarded_date, datetime.datetime):
                        date_str = awarded_date.strftime("%m/%d")
                    else:
                        date_str = str(awarded_date)[:10] if awarded_date else ""
                    
                    st.markdown(f"""
                    <div class="sidebar-badge-item">
                        <span class="badge-icon">{badge.get('icon', '🏅')}</span>
                        <span class="badge-info">
                            <strong>{badge.get('name', 'Badge')}</strong><br>
                            <small>{date_str}</small>
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            
        except Exception as e:
            logger.error(f"Error rendering recent badges preview: {str(e)}")

    def render_combined_profile_leaderboard(self):
        """Render enhanced combined profile and leaderboard with separated badges."""
        if not st.session_state.auth.get("is_authenticated", False):
            return
        
        user_info = st.session_state.auth.get("user_info", {})
        user_id = st.session_state.auth.get("user_id")
        
        with st.sidebar:
            try:
                from ui.components.profile_leaderboard import ProfileLeaderboardSidebar
                from ui.components.badge_sidebar import BadgeSidebar  # NEW IMPORT
                
                # Create sidebar instances
                sidebar_component = ProfileLeaderboardSidebar()
                badge_component = BadgeSidebar()  # NEW COMPONENT
                
                # Render profile (without badges now)
                sidebar_component.render_combined_sidebar(user_info, user_id)
                
                # Render separated badges section
                st.markdown("---")
                badge_component.render_badge_section(user_info, user_id)
                
            except ImportError as ie:
                logger.error(f"Failed to import sidebar components: {str(ie)}")
            except Exception as e:
                logger.error(f"Enhanced sidebar error: {str(e)}")
            
            # App info and logout section
            self._render_sidebar_footer()

# CSS for badge sidebar - Add to your CSS files
BADGE_SIDEBAR_CSS = """
<style>
.sidebar-badges-container {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.badges-header h4 {
    margin: 0;
    color: #495057;
    font-size: 1rem;
}

.no-badges-container {
    text-align: center;
    padding: 1rem;
    color: #6c757d;
}

.no-badges-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.badges-hint {
    margin-top: 0.5rem;
}

.sidebar-badge-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background: white;
    border-radius: 6px;
    margin-bottom: 0.5rem;
    border: 1px solid #e9ecef;
}

.badge-icon-sidebar {
    font-size: 1.2rem;
    min-width: 24px;
}

.badge-info-sidebar {
    flex: 1;
    min-width: 0;
}

.badge-name-sidebar {
    font-weight: 600;
    font-size: 0.8rem;
    line-height: 1.2;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.badge-date-sidebar {
    font-size: 0.7rem;
    color: #6c757d;
}

.badge-stats-container {
    margin-top: 1rem;
    padding: 0.5rem;
    background: white;
    border-radius: 6px;
}

.badge-progress-bar {
    text-align: center;
}

.progress-label {
    font-size: 0.8rem;
    color: #495057;
    margin-bottom: 0.25rem;
}

.progress-bar-bg {
    background: #e9ecef;
    height: 6px;
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 0.25rem;
}

.progress-bar-fill {
    background: linear-gradient(90deg, #28a745, #20c997);
    height: 100%;
    transition: width 0.3s ease;
}

.progress-text {
    font-size: 0.7rem;
    color: #6c757d;
}

.modal-badge-card {
    background: #f8f9fa;
    border-radius: 6px;
    padding: 0.5rem;
    text-align: center;
    margin-bottom: 0.5rem;
    border: 1px solid #e9ecef;
}

.modal-badge-card .badge-icon {
    font-size: 1.5rem;
    margin-bottom: 0.25rem;
}

.modal-badge-card .badge-name {
    font-weight: 600;
    font-size: 0.8rem;
    margin-bottom: 0.25rem;
}

.modal-badge-card .badge-date {
    font-size: 0.7rem;
    color: #6c757d;
}
</style>
"""           
    # Add CSS for enhanced profile display

ENHANCED_PROFILE_CSS = """
    <style>
    .enhanced-profile-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .profile-header {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .profile-avatar {
        font-size: 2rem;
        background: rgba(255,255,255,0.2);
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .profile-info h3 {
        margin: 0;
        font-size: 1.2rem;
    }

    .profile-level {
        margin: 0;
        opacity: 0.8;
        font-size: 0.9rem;
    }

    .sidebar-badge-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem;
        background: #f8f9fa;
        border-radius: 6px;
        margin-bottom: 0.5rem;
    }

    .badge-icon {
        font-size: 1.2rem;
    }

    .badge-info {
        font-size: 0.85rem;
        line-height: 1.2;
    }
    </style>
    """

