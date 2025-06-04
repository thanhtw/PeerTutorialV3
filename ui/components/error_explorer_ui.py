import streamlit as st
import os
import logging
from typing import Dict, List, Any, Optional
from data.database_error_repository import DatabaseErrorRepository
from utils.language_utils import t, get_current_language
from static.css_utils import load_css

logger = logging.getLogger(__name__)

class ErrorExplorerUI:
    """UI component for exploring Java errors with examples and solutions."""
    
    def __init__(self):
        """Initialize the Error Explorer UI."""
        self.repository = DatabaseErrorRepository()
        
        # Initialize session state
        if "selected_error_code" not in st.session_state:
            st.session_state.selected_error_code = None
        if "user_progress" not in st.session_state:
            st.session_state.user_progress = {}
        
        self._load_styles()
    
    def _load_styles(self):
        """Load CSS styles for the Error Explorer UI."""
        try:
            # Get the current directory and construct path to CSS files
            current_dir = os.path.dirname(os.path.abspath(__file__))
            css_dir = os.path.join(current_dir, "..", "..", "static", "css", "error_explorer")
            
            if os.path.exists(css_dir):
                loaded_files = load_css(css_directory=css_dir)
                if loaded_files:
                    logger.debug(f"Loaded Error Explorer CSS files: {loaded_files}")
            else:
                logger.warning(f"CSS directory not found: {css_dir}")
        except Exception as e:
            logger.error(f"Error loading Error Explorer CSS: {str(e)}")

    def render(self):
        """Render the complete error explorer interface."""
        # Professional header
        self._render_enhanced_header()
        
        # Search and filter section
        self._render_enhanced_search_filters()
        
        # Main content area
        self._render_error_content()
    
    def _render_enhanced_header(self):
        """Render an enhanced professional header with branding and statistics."""
        try:
            stats = self.repository.get_error_statistics()
            total_errors = stats.get('total_errors', 0)
            total_categories = stats.get('total_categories', 0)
            errors_by_category = stats.get('errors_by_category', {})
        except Exception as e:
            logger.debug(f"Could not get database statistics: {str(e)}")
            total_errors = 0
            total_categories = 0
            errors_by_category = {}
        
        st.markdown(f"""
        <div class="error-explorer-header-compact">
            <div class="header-content-compact">
                <div class="title-section-compact">
                    <h1>🔍 {t('error_explorer')}</h1>
                    <p class="subtitle-compact">{t('explore_comprehensive_error_library')}</p>
                </div>
                <div class="stats-section-compact">
                    <div class="stat-card-compact">
                        <div class="stat-number-compact">{total_errors}</div>
                        <div class="stat-label-compact">Errors</div>
                    </div>
                    <div class="stat-card-compact">
                        <div class="stat-number-compact">{total_categories}</div>
                        <div class="stat-label-compact">Categories</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_enhanced_search_filters(self):
        """Render enhanced search and filter controls with professional styling."""
        st.markdown('<div class="search-filter-container">', unsafe_allow_html=True)
        
        # Search section header
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">🔍</div>
            <div>
                <div class="section-title">Search & Filter Errors</div>
                <div class="section-subtitle">Find specific errors or browse by category and difficulty</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Main search and filter controls
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            search_term = st.text_input(
                "",
                placeholder="🔍 Search errors by name or description...",
                key="error_search",
                help="Search for specific error patterns, keywords, or descriptions"
            )
        
        with col2:
            categories = self._get_categories()
            selected_category = st.selectbox(
                "📂 Category",
                options=["All Categories"] + categories,
                key="category_filter",
                help="Filter by error category"
            )
        
        with col3:
            difficulty_levels = ["All Levels", "Easy", "Medium", "Hard"]
            selected_difficulty = st.selectbox(
                "⚡ Difficulty",
                options=difficulty_levels,
                key="difficulty_filter",
                help="Filter by difficulty level"
            )
        
        with col4:
            if st.button("🔄 Reset", help="Clear all filters", use_container_width=True):
                st.session_state.error_search = ""
                st.session_state.category_filter = "All Categories"
                st.session_state.difficulty_filter = "All Levels"
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Store filters in session state
        st.session_state.search_term = search_term
        st.session_state.selected_category = selected_category
        st.session_state.selected_difficulty = selected_difficulty

    def _render_view_toggle(self):
        """Render view toggle controls."""
        st.markdown('<div class="view-toggle-section">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col2:
            view_mode = st.radio(
                "View Mode",
                options=["Cards", "List"],
                horizontal=True,
                key="view_mode",
                help="Choose how to display the errors"
            )
            st.session_state.error_explorer_view = view_mode.lower()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_error_content(self):
        """Render the main error content based on filters."""
        # Get filtered errors
        filtered_errors = self._get_filtered_errors()
        
        if not filtered_errors:
            self._render_no_results()
            return
        
        # Results count with enhanced styling
        st.markdown(f"""
        <div class="results-count">
            <div class="count-info">
                <span class="count-number">{len(filtered_errors)}</span> 
                <span class="count-text">{t("errors_found")}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Render in list view only
        self._render_list_view(filtered_errors)
    
    def _render_list_view(self, filtered_errors: List[Dict[str, Any]]):
        """Render errors in a compact list view with expandable details."""
        errors_by_category = self._group_errors_by_category(filtered_errors)
        
        for category_name, errors in errors_by_category.items():
            st.markdown(f'<h3 class="category-title">{category_name} <span class="error-count">({len(errors)})</span></h3>', 
                       unsafe_allow_html=True)
            
            for error in errors:
                self._render_error_list_item(error)
    
    def _render_expanded_error_details(self, error: Dict[str, Any]):
        """Render detailed error information when expanded."""
        error_name = error.get(t("error_name"), "Unknown Error")
        implementation_guide = error.get(t("implementation_guide"), "")
        
        # Create a container for the expanded content
        st.markdown('<div class="expanded-details-container">', unsafe_allow_html=True)
        
        # Show full description
        full_description = error.get(t("description"), "")
        if full_description:
            st.markdown("**📋 Full Description:**")
            st.info(full_description)
        
        # Show implementation guide if available
        if implementation_guide:
            st.markdown("**💡 How to Fix This Error:**")
            st.success(implementation_guide)
        
        # Get and display examples
        examples = self.repository.get_error_examples(error_name)
        
        # Create tabs for different content sections
        if examples.get("wrong_examples") or examples.get("correct_examples"):
            tab1, tab2, tab3 = st.tabs(["❌ Problematic Code", "✅ Corrected Code", "📚 Additional Info"])
            
            with tab1:
                if examples.get("wrong_examples"):
                    st.markdown("**Examples of code that causes this error:**")
                    for i, example in enumerate(examples["wrong_examples"][:2]):
                        st.markdown(f"**Example {i+1}:**")
                        st.code(example, language="java")
                        if i < len(examples["wrong_examples"]) - 1:
                            st.markdown("---")
                else:
                    st.info("📝 No problematic code examples available for this error yet.")
            
            with tab2:
                if examples.get("correct_examples"):
                    st.markdown("**Corrected versions of the problematic code:**")
                    for i, example in enumerate(examples["correct_examples"][:2]):
                        st.markdown(f"**Corrected Example {i+1}:**")
                        st.code(example, language="java")
                        if i < len(examples["correct_examples"]) - 1:
                            st.markdown("---")
                else:
                    st.info("📝 No corrected code examples available for this error yet.")
            
            with tab3:
                # Show additional information
                explanation = examples.get("explanation", "")
                if explanation:
                    st.markdown("**💡 Key Learning Points:**")
                    st.info(explanation)
                
                # Show error metadata
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**🏷️ Error Code:**")
                    st.code(error.get('error_code', 'N/A'))
                
                with col2:
                    st.markdown("**⚡ Difficulty:**")
                    difficulty = error.get('difficulty_level', 'medium')
                    if difficulty == 'easy':
                        st.success(f"🟢 {difficulty.title()}")
                    elif difficulty == 'medium':
                        st.warning(f"🟡 {difficulty.title()}")
                    else:
                        st.error(f"🔴 {difficulty.title()}")
        else:
            # If no examples, just show the additional info
            explanation = examples.get("explanation", "")
            if explanation:
                st.markdown("**💡 Key Learning Points:**")
                st.info(explanation)
            
            # Show error metadata
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🏷️ Error Code:**")
                st.code(error.get('error_code', 'N/A'))
            
            with col2:
                st.markdown("**⚡ Difficulty:**")
                difficulty = error.get('difficulty_level', 'medium')
                if difficulty == 'easy':
                    st.success(f"🟢 {difficulty.title()}")
                elif difficulty == 'medium':
                    st.warning(f"🟡 {difficulty.title()}")
                else:
                    st.error(f"🔴 {difficulty.title()}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_expanded_error_content(self, error: Dict[str, Any]):
        """Render the expanded content for an error card with professional styling."""
        error_name = error.get(t("error_name"), "Unknown Error")
        implementation_guide = error.get(t("implementation_guide"), "")
        
        # Enhanced expanded content container
        st.markdown('<div class="expanded-content-container">', unsafe_allow_html=True)
        
        # Detailed description section
        if implementation_guide:
            st.markdown(f"""
            <div class="enhanced-guidance-section">
                <div class="guidance-header">
                    <span class="guidance-icon">💡</span>
                    <h4>How to Fix This Error</h4>
                </div>
                <div class="guidance-content">
                    <p>{implementation_guide}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Get and display examples
        examples = self.repository.get_error_examples(error_name)
        
        # Create tabs for different content sections
        tab1, tab2, tab3 = st.tabs(["❌ Problematic Code", "✅ Corrected Code", "📚 Learning Resources"])
        
        with tab1:
            if examples.get("wrong_examples"):
                st.markdown("**Examples of code that causes this error:**")
                for i, example in enumerate(examples["wrong_examples"][:3]):
                    st.markdown(f"""
                    <div class="example-header">
                        <div class="example-icon wrong">❌</div>
                        <h5>Problematic Example {i+1}</h5>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown('<div class="code-example error-code">', unsafe_allow_html=True)
                    st.code(example, language="java")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("📝 No problematic code examples available for this error yet.")
        
        with tab2:
            if examples.get("correct_examples"):
                st.markdown("**Corrected versions of the problematic code:**")
                for i, example in enumerate(examples["correct_examples"][:3]):
                    st.markdown(f"""
                    <div class="example-header">
                        <div class="example-icon correct">✅</div>
                        <h5>Corrected Example {i+1}</h5>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown('<div class="code-example correct-code">', unsafe_allow_html=True)
                    st.code(example, language="java")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("📝 No corrected code examples available for this error yet.")
        
        with tab3:
            # Learning resources and tips
            explanation = examples.get("explanation", "")
            if explanation:
                st.markdown("**💡 Key Learning Points:**")
                st.info(explanation)
            
            # Additional learning suggestions
            st.markdown("**🎓 Recommended Learning Path:**")
            learning_steps = [
                "Understand the root cause of this error",
                "Practice identifying this pattern in code",
                "Learn the correct implementation approach",
                "Apply the fix in real scenarios",
                "Review and prevent similar errors"
            ]
            
            for i, step in enumerate(learning_steps, 1):
                st.write(f"{i}. {step}")
            
            # Related errors suggestion
            st.markdown("**🔗 Related Error Patterns:**")
            st.info("Explore similar errors in the same category to build comprehensive understanding.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_error_list_item(self, error: Dict[str, Any]):
        """Render an error in list format with expandable details."""
        error_name = error.get(t("error_name"), "Unknown Error")
        description = error.get(t("description"), "")
        difficulty = error.get('difficulty_level', 'medium')
        error_code = error.get('error_code', f"error_{hash(error_name) % 10000}")
        
        # Check if this error is expanded
        expanded_key = f"expanded_{error_code}"
        is_expanded = st.session_state.get(expanded_key, False)
        
        # Render the list item header
        st.markdown(f"""
        <div class="error-list-item">
            <div class="error-list-header">
                <div class="list-title">
                    <span class="error-icon">🔧</span>
                    <span class="error-name">{error_name}</span>
                </div>
                <div class="list-badges">
                    <span class="error-badge {difficulty}">{difficulty.title()}</span>
                </div>
            </div>
            <div class="error-list-content">
                <p class="list-description">{description[:150]}{'...' if len(description) > 150 else ''}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Empty column for spacing
            pass
            
        with col2:
            if st.button(
                f"{'Hide' if is_expanded else 'View'}", 
                key=f"view_{error_code}", 
                use_container_width=True
            ):
                st.session_state[expanded_key] = not is_expanded
                st.rerun()
        
        with col3:
            if st.button(f"Practice", key=f"practice_list_{error_code}", use_container_width=True):
                self._handle_practice_error(error)
        
        # Show expanded content if the error is expanded
        if is_expanded:
            self._render_expanded_error_details(error)
    
    def _render_progress_badges(self, error: Dict[str, Any]) -> str:
        """Generate HTML for progress badges."""
        # This would integrate with user progress tracking
        # For now, showing sample progress states
        return """
        <div class="progress-badges">
            <span class="progress-badge practiced">📚 Available</span>
        </div>
        """
    
    def _get_frequency_class(self, error: Dict[str, Any]) -> str:
        """Get CSS class for frequency badge based on error frequency."""
        frequency_weight = error.get('frequency_weight', 1)
        if frequency_weight >= 4:
            return "high-frequency"
        elif frequency_weight >= 2:
            return "medium-frequency"
        else:
            return "low-frequency"
    
    def _get_frequency_display(self, error: Dict[str, Any]) -> str:
        """Get display text for frequency."""
        frequency_weight = error.get('frequency_weight', 1)
        if frequency_weight >= 4:
            return "High Frequency"
        elif frequency_weight >= 2:
            return "Medium Frequency"
        else:
            return "Low Frequency"
    
    def _handle_practice_error(self, error: Dict[str, Any]):
        """Handle practice error button click with enhanced feedback."""
        error_name = error.get(t("error_name"), "Unknown Error")
        
        # Enhanced success message with actionable next steps
        st.success("🎯 Practice Session Started!")
        
        # Create an info container with next steps
        st.markdown(f"""
        <div class="practice-started-container">
            <div class="practice-header">
                <h4>🚀 Now Practicing: {error_name}</h4>
            </div>
            <div class="practice-instructions">
                <p><strong>Next Steps:</strong></p>
                <ul>
                    <li>Review the problematic code examples above</li>
                    <li>Try to identify the error patterns</li>
                    <li>Study the corrected implementations</li>
                    <li>Practice writing your own solutions</li>
                </ul>
                <p><em>💡 Tip: Use the "Generate" tab to create practice code with this error type!</em></p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Track usage in database
        try:
            self.repository.update_error_usage(
                error_code=error.get('error_code', ''),
                action_type='practiced',
                context={'source': 'error_explorer', 'method': 'practice_button'}
            )
        except Exception as e:
            logger.debug(f"Could not track error usage: {str(e)}")
    
    def _show_error_statistics(self, error: Dict[str, Any]):
        """Show detailed statistics for an error."""
        error_name = error.get(t("error_name"), "Unknown Error")
        
        # This would show real statistics from the database
        st.markdown(f"""
        <div class="stats-popup">
            <h4>📊 Statistics for {error_name}</h4>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{error.get('usage_count', 0)}</div>
                    <div class="stat-label">Total Views</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{error.get('difficulty_level', 'medium').title()}</div>
                    <div class="stat-label">Difficulty</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{error.get('frequency_weight', 1)}/5</div>
                    <div class="stat-label">Frequency</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _get_categories(self) -> List[str]:
        """Get all available categories."""
        try:
            categories_data = self.repository.get_all_categories()
            return categories_data.get("java_errors", [])
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []
    
    def _get_filtered_errors(self) -> List[Dict[str, Any]]:
        """Get errors based on current filters."""
        try:
            # Get all categories if no specific filter
            selected_category = st.session_state.get('selected_category', 'All Categories')
            if selected_category == 'All Categories':
                categories = self._get_categories()
            else:
                categories = [selected_category]
            
            all_errors = []
            for category in categories:
                category_errors = self.repository.get_category_errors(category)
                for error in category_errors:
                    error['category'] = category
                    all_errors.append(error)
            
            # Apply filters
            filtered_errors = self._apply_filters(all_errors)
            return filtered_errors
            
        except Exception as e:
            logger.error(f"Error getting filtered errors: {str(e)}")
            return []
    
    def _apply_filters(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply search and difficulty filters to errors."""
        filtered = errors
        
        # Search filter
        search_term = st.session_state.get('search_term', '').lower()
        if search_term:
            filtered = [
                error for error in filtered
                if search_term in error.get(t("error_name"), "").lower() or
                   search_term in error.get(t("description"), "").lower()
            ]
        
        # Difficulty filter
        selected_difficulty = st.session_state.get('selected_difficulty', 'All Levels')
        if selected_difficulty != 'All Levels':
            difficulty_map = {
                "Easy": "easy",
                "Medium": "medium", 
                "Hard": "hard"
            }
            db_difficulty = difficulty_map.get(selected_difficulty, "medium")
            
            filtered = [
                error for error in filtered
                if error.get('difficulty_level') == db_difficulty
            ]
        
        return filtered
    
    def _group_errors_by_category(self, errors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group errors by category."""
        grouped = {}
        for error in errors:
            category = error.get('category', 'Unknown')
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(error)
        return grouped
    
    def _render_no_results(self):
        """Render enhanced no results message."""
        st.markdown("""
        <div class="no-results">
            <div class="no-results-icon">🔍</div>
            <h3>No Errors Found</h3>
            <p>We couldn't find any errors matching your search criteria.</p>
            <div class="no-results-suggestions">
                <h4>Try these suggestions:</h4>
                <ul>
                    <li>Check your spelling and try different keywords</li>
                    <li>Broaden your search by selecting "All Categories"</li>
                    <li>Try searching for common terms like "null", "loop", or "syntax"</li>
                    <li>Reset all filters and browse the complete error library</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_error_explorer():
    """Main function to render the error explorer."""
    explorer = ErrorExplorerUI()
    explorer.render()