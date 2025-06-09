# ui/components/learning_dashboard.py
"""
Learning Dashboard UI Component for Java Peer Review Training System.

This module provides a comprehensive dashboard showing student progress,
achievements, skill development, and personalized recommendations.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import datetime
import logging
from typing import Dict, List, Any, Optional
from learning.progress_manager import LearningProgressManager
from auth.badge_manager import BadgeManager
from utils.language_utils import t

logger = logging.getLogger(__name__)

class LearningDashboardUI:
    """
    Comprehensive learning dashboard with analytics and progress visualization.
    """
    
    def __init__(self):
        self.progress_manager = LearningProgressManager()
        self.badge_manager = BadgeManager()
    
    def render(self, user_id: str):
        """
        Render the complete learning dashboard.
        
        Args:
            user_id: Current user's ID
        """
        try:
            # Get dashboard data
            dashboard_data = self.progress_manager.get_learning_dashboard_data(user_id)
            
            if not dashboard_data:                
                return
            
            # Render dashboard sections
            self._render_dashboard_header(dashboard_data["overall_stats"])
            
            # Create tabs for different dashboard sections
            tab1, tab2 = st.tabs([              
                t("achievements"), 
                t("activity_history")               
            ])
            
            with tab1:
                self._render_achievements_tab(user_id)
            
            with tab2:
                self._render_activity_history_tab(dashboard_data["recent_sessions"])
                 
        except Exception as e:
            logger.error(f"Error rendering learning dashboard: {str(e)}")
            st.error(f"{t('dashboard_error')}: {str(e)}")
    
    def _render_dashboard_header(self, overall_stats: Dict[str, Any]):
        """Render dashboard header with key statistics."""
        
        st.markdown(f"""
        <div class="dashboard-header">
            <h1>📊 {t('learning_dashboard')}</h1>
            <p>{t('track_your_progress')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key metrics in columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label=t("total_experience"),
                value=f"{overall_stats.get('total_experience', 0):,}",
                delta=None
            )
        
        with col2:
            avg_mastery = overall_stats.get('average_mastery', 0)
            st.metric(
                label=t("average_mastery"),
                value=f"{avg_mastery:.1f}%",
                delta=f"{avg_mastery - 50:.1f}%" if avg_mastery > 0 else None
            )
        
        with col3:
            practice_hours = overall_stats.get('practice_time_hours', 0)
            st.metric(
                label=t("practice_hours"),
                value=f"{practice_hours:.1f}h",
                delta=None
            )
        
        with col4:
            current_streak = overall_stats.get('current_streak', 0)
            st.metric(
                label=t("current_streak"),
                value=f"{current_streak} {t('days')}",
                delta=None
            )
        
        with col5:
            achievements = overall_stats.get('achievements_earned', 0)
            st.metric(
                label=t("achievements"),
                value=str(achievements),
                delta=None
            )
    
    def _render_achievements_tab(self, user_id: str):
        """Render achievements and badges tab."""
        
        st.subheader(t("your_achievements"))
        
        # Get user badges
        user_badges = self.badge_manager.get_user_badges(user_id)
        
        if not user_badges:
            st.info(t("no_badges_yet"))
            st.markdown(t("earn_badges_by_practicing"))
            return
        
        # Group badges by category
        badge_categories = {}
        for badge in user_badges:
            category = badge.get('category', 'other')
            if category not in badge_categories:
                badge_categories[category] = []
            badge_categories[category].append(badge)
        
        # Render badges by category
        for category, badges in badge_categories.items():
            st.markdown(f"### {t(category)} {t('badges')}")
            
            # Create columns for badge display
            cols = st.columns(min(len(badges), 4))
            
            for i, badge in enumerate(badges):
                with cols[i % 4]:
                    self._render_badge_card(badge)
        
        # Achievement statistics
        st.subheader(t("achievement_statistics"))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(t("total_badges"), len(user_badges))
        
        with col2:
            # Calculate total points from badges
            total_badge_points = sum(badge.get('points', 0) for badge in user_badges)
            st.metric(t("badge_points"), total_badge_points)
        
        with col3:
            # Show rarest badge
            rarest_badge = max(user_badges, key=lambda x: x.get('difficulty', ''), default=None)
            if rarest_badge:
                st.metric(t("rarest_badge"), rarest_badge.get('name', ''))
    
    def _render_badge_card(self, badge: Dict[str, Any]):
        """Render individual badge card."""
        
        badge_name = badge.get('name', t('unknown_badge'))
        badge_icon = badge.get('icon', '🏅')
        badge_description = badge.get('description', '')
        badge_difficulty = badge.get('difficulty', 'easy')
        awarded_at = badge.get('awarded_at', '')
        
        # Format date
        if awarded_at:
            try:
                if isinstance(awarded_at, str):
                    date_str = awarded_at.split(' ')[0]
                else:
                    date_str = awarded_at.strftime('%Y-%m-%d')
            except:
                date_str = str(awarded_at)
        else:
            date_str = t('unknown_date')
        
        # Difficulty colors
        difficulty_colors = {
            'easy': '#27ae60',
            'medium': '#f39c12', 
            'hard': '#e74c3c'
        }
        
        difficulty_color = difficulty_colors.get(badge_difficulty, '#95a5a6')
        
        st.markdown(f"""
        <div class="badge-card" style="
            border: 2px solid {difficulty_color}; 
            border-radius: 12px; 
            padding: 15px; 
            text-align: center; 
            background: white;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="font-size: 2em; margin-bottom: 8px;">{badge_icon}</div>
            <div style="font-weight: bold; margin-bottom: 5px; color: #2c3e50;">{badge_name}</div>
            <div style="font-size: 0.8em; color: #7f8c8d; margin-bottom: 8px;">{badge_description}</div>
            <div style="
                background: {difficulty_color}; 
                color: white; 
                padding: 2px 6px; 
                border-radius: 8px; 
                font-size: 0.7em;
                display: inline-block;
                margin-bottom: 5px;
            ">{t(badge_difficulty)}</div>
            <div style="font-size: 0.7em; color: #95a5a6;">📅 {date_str}</div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_activity_history_tab(self, recent_sessions: List[Dict[str, Any]]):
        """Render activity history and analytics tab."""
        
        st.subheader(t("recent_activity"))
        
        if not recent_sessions:
            st.info(t("no_recent_activity"))
            return
        
        # Activity timeline
        for session in recent_sessions:
            session_type = session.get('session_type', 'unknown')
            started_at = session.get('started_at', 'unknown')
            duration = session.get('duration_minutes', 0)
            performance = session.get('performance_score', 0)
            activities = session.get('activities_completed', 0)
            
            # Format date
            try:
                if isinstance(started_at, str):
                    date_str = started_at
                else:
                    date_str = started_at.strftime('%Y-%m-%d %H:%M')
            except:
                date_str = str(started_at)
            
            # Performance color
            if performance >= 80:
                perf_color = "#27ae60"
                perf_icon = "🎯"
            elif performance >= 60:
                perf_color = "#f39c12"  
                perf_icon = "📈"
            else:
                perf_color = "#e74c3c"
                perf_icon = "📊"
            
            st.markdown(f"""
            <div class="activity-item" style="
                border-left: 4px solid {perf_color};
                padding: 12px;
                margin: 8px 0;
                background: #f8f9fa;
                border-radius: 0 8px 8px 0;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{perf_icon} {t(session_type)}</strong>
                        <div style="font-size: 0.8em; color: #7f8c8d;">{date_str}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: bold; color: {perf_color};">{performance:.0f}%</div>
                        <div style="font-size: 0.8em; color: #7f8c8d;">{duration} {t('minutes')}</div>
                    </div>
                </div>
                <div style="margin-top: 8px; font-size: 0.9em;">
                    {t('activities_completed')}: {activities}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Activity summary chart
        if len(recent_sessions) > 1:
            st.subheader(t("performance_trend"))
            
            # Create performance trend chart
            sessions_df = pd.DataFrame(recent_sessions)
            sessions_df['date'] = pd.to_datetime(sessions_df['started_at'])
            sessions_df = sessions_df.sort_values('date')
            
            fig_trend = px.line(
                sessions_df,
                x='date',
                y='performance_score',
                title=t("performance_over_time"),
                labels={
                    'date': t('date'),
                    'performance_score': t('performance_score')
                }
            )
            
            fig_trend.update_traces(mode='markers+lines')
            fig_trend.update_layout(yaxis_range=[0, 100])
            
            st.plotly_chart(fig_trend, use_container_width=True)
    
def render_learning_dashboard(user_id: str):
    """
    Standalone function to render learning dashboard with enhanced styling.
    
    Args:
        user_id: Current user's ID
    """
    try:
        dashboard = LearningDashboardUI()
        dashboard.render(user_id)
    except Exception as e:
        logger.error(f"Error rendering learning dashboard: {str(e)}")
        st.error(f"{t('dashboard_error')}: {str(e)}")

