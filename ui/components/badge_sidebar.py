# ui/components/badge_sidebar.py - NEW FILE
"""
Always-accessible badge display component for the sidebar.
Users can view their badges regardless of review completion status.
"""

import streamlit as st
import logging
import html
from typing import Dict, Any, List
from analytics.badge_manager import BadgeManager
from utils.language_utils import t, get_current_language
import datetime

logger = logging.getLogger(__name__)

class BadgeSidebar:
    """Always-accessible badge display component for sidebar."""
    
    def __init__(self):
        self.badge_manager = BadgeManager()
    
    def render_badge_section(self, user_info: Dict[str, Any], user_id: str) -> None:
        """
        Render badges section in sidebar that's always accessible.
        
        Args:
            user_info: User information dictionary
            user_id: User ID string
        """
        if not user_id or user_id == 'demo_user':
            st.info(f"🏆 {t('login_to_earn_badges')}")
            return
        
        try:
            # Get user badges
            user_badges = self.badge_manager.get_user_badges(user_id)
            
            # Render badges header
            st.markdown(f"""
            <div class="sidebar-badges-container">
                <div class="badges-header">
                    <h4>🏆 {t('your_badges')} ({len(user_badges)})</h4>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if not user_badges:
                self._render_no_badges_message()
                return
            
            # Show recent badges (last 3) with details
            recent_badges = user_badges[:3]
            self._render_recent_badges(recent_badges)
            
            # Show all badges button if user has more than 3
            if len(user_badges) > 3:
                if st.button(
                    f"📋 {t('view_all_badges')} ({len(user_badges)})",
                    key="view_all_badges_sidebar",
                    use_container_width=True
                ):
                    st.session_state.show_all_badges_modal = True
            
            # Badge statistics
            self._render_badge_statistics(user_badges, user_id)
            
            # Show modal if requested
            if st.session_state.get("show_all_badges_modal", False):
                self._render_all_badges_modal(user_badges)
                
        except Exception as e:
            logger.error(f"Error rendering badge section: {str(e)}")
            st.error(f"❌ {t('error_loading_badges')}")
    
    def _render_no_badges_message(self):
        """Render message when user has no badges yet."""
        st.markdown(f"""
        <div class="no-badges-container">
            <div class="no-badges-icon">🎯</div>
            <p class="no-badges-text">{t('no_badges_yet')}</p>
            <div class="badges-hint">
                <small>💡 {t('complete_reviews_to_earn_badges')}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_recent_badges(self, recent_badges: List[Dict[str, Any]]):
        """Render recent badges with compact display."""
        for badge in recent_badges:
            # Format date
            awarded_at = badge.get("awarded_at", "")
            if isinstance(awarded_at, datetime.datetime):
                date_str = awarded_at.strftime("%m/%d")
            else:
                date_str = str(awarded_at)[:5] if awarded_at else ""
            
            # Render compact badge item
            st.markdown(f"""
            <div class="sidebar-badge-item">
                <div class="badge-icon-sidebar">{badge.get("icon", "🏅")}</div>
                <div class="badge-info-sidebar">
                    <div class="badge-name-sidebar">{html.escape(badge.get("name", "Badge"))}</div>
                    <div class="badge-date-sidebar">{date_str}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_badge_statistics(self, user_badges: List[Dict[str, Any]], user_id: str):
        """Render badge statistics."""
        try:
            # Group badges by category
            categories = {}
            for badge in user_badges:
                category = badge.get("category", "other")
                categories[category] = categories.get(category, 0) + 1
            
            # Get total possible badges for progress
            all_badges_query = "SELECT COUNT(*) as total FROM badges WHERE is_active = TRUE"
            result = self.badge_manager.db.execute_query(all_badges_query, fetch_one=True)
            total_possible = result.get("total", 100) if result else 100
            
            completion_rate = (len(user_badges) / total_possible) * 100
            
            st.markdown(f"""
            <div class="badge-stats-container">
                <div class="badge-progress-bar">
                    <div class="progress-label">{t('collection_progress')}</div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" style="width: {completion_rate:.1f}%"></div>
                    </div>
                    <div class="progress-text">{completion_rate:.1f}% ({len(user_badges)}/{total_possible})</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            logger.error(f"Error rendering badge statistics: {str(e)}")
    
    def _render_all_badges_modal(self, user_badges: List[Dict[str, Any]]):
        """Render modal showing all user badges."""
        with st.expander(f"🏆 {t('all_your_badges')} ({len(user_badges)})", expanded=True):
            # Group badges by category
            badges_by_category = {}
            for badge in user_badges:
                category = badge.get("category", "other")
                if category not in badges_by_category:
                    badges_by_category[category] = []
                badges_by_category[category].append(badge)
            
            # Display by category
            for category, badges in badges_by_category.items():
                st.markdown(f"**{category.title()} ({len(badges)})**")
                
                # Display badges in grid
                cols = st.columns(3)
                for i, badge in enumerate(badges):
                    with cols[i % 3]:
                        awarded_at = badge.get("awarded_at", "")
                        if isinstance(awarded_at, datetime.datetime):
                            date_str = awarded_at.strftime("%Y-%m-%d")
                        else:
                            date_str = str(awarded_at).split(' ')[0] if awarded_at else ""
                        
                        st.markdown(f"""
                        <div class="modal-badge-card">
                            <div class="badge-icon">{badge.get("icon", "🏅")}</div>
                            <div class="badge-name">{badge.get("name", "Badge")}</div>
                            <div class="badge-date">{date_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
            
            # Close button
            if st.button(f"✅ {t('close')}", key="close_badges_modal"):
                st.session_state.show_all_badges_modal = False
                st.rerun()



