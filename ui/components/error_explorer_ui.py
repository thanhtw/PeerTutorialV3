import streamlit as st
import logging
from data.database_error_repository import DatabaseErrorRepository
from typing import List, Dict, Optional, Any
from utils.language_utils import t
from static.css_utils import load_css
import os

logger = logging.getLogger(__name__)

class ErrorExplorerUI:
    """
    Enhanced UI component for exploring detailed information about programming errors.
    Provides comprehensive error exploration with modern interface and full i18n support.
    """

    def __init__(self):
        """
        Initializes the ErrorExplorerUI with a DatabaseErrorRepository instance.
        """
        self.repository = DatabaseErrorRepository()
        self.error_data = self._load_error_database()
        
        # Initialize session state
        if "selected_error_code" not in st.session_state:
            st.session_state.selected_error_code = None
        if "error_explorer_view" not in st.session_state:
            st.session_state.error_explorer_view = "list"
        if "user_progress" not in st.session_state:
            st.session_state.user_progress = {}
        
        # Load CSS styles
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
        """
        Renders the complete Enhanced Error Explorer UI with modern design.
        """
        # Professional header
        self._render_header()
        
        # Main content layout
        self._render_main_content()

    def _render_header(self):
        """Render the professional header with branding and statistics."""
        # Get error statistics from database
        try:
            stats = self.repository.get_error_statistics()
            total_errors = stats.get('total_errors', 0)
            total_categories = stats.get('total_categories', 0)
        except Exception as e:
            logger.debug(f"Could not get database statistics: {str(e)}")
            # Fallback to counting loaded data
            total_errors = sum(len(errors) for errors in self.error_data.values())
            total_categories = len(self.error_data)
        
        st.markdown(f"""
        <div class="error-explorer-header">
            <div class="header-content">
                <div class="title-section">
                    <h1>🔍 {t('error_explorer')}</h1>
                    <p class="subtitle">{t('explore_comprehensive_error_library')}</p>
                </div>
                <div class="stats-section">
                    <div class="stat-card">
                        <div class="stat-number">{total_errors}</div>
                        <div class="stat-label">{t('total_errors_available')}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{total_categories}</div>
                        <div class="stat-label">{t('error_categories')}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _render_main_content(self):
        """Render the main content area with enhanced layout."""
        # Search and filter controls
        self._render_search_and_filters()
       
        # Main content based on view mode
        self._render_list_view()

    def _render_search_and_filters(self):
        """Render enhanced search and filter controls."""
        st.markdown(f"### 🔎 {t('search_and_filter')}")
        
        # Search and filters in a nice container
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                search_term = st.text_input(
                    t("error_search"),
                    placeholder=t("search_placeholder_detailed"),
                    key="error_search_input",
                    help=t("search_help_text")
                )
            
            with col2:
                selected_category = st.selectbox(
                    t("filter_by_category"),
                    [t("all_categories")] + list(self.error_data.keys()),
                    key="category_filter",
                    help=t("category_filter_help")
                )
            
            with col3:
                selected_difficulty = st.selectbox(
                    t("filter_by_difficulty"),
                    [t("all_difficulties"), t("easy"), t("medium"), t("hard")],
                    key="difficulty_filter",
                    help=t("difficulty_filter_help")
                )
            
            with col4:
                selected_frequency = st.selectbox(
                    t("filter_by_frequency"),
                    [t("all_frequencies"), t("high_frequency"), t("medium_frequency"), t("low_frequency")],
                    key="frequency_filter",
                    help=t("frequency_filter_help")
                )
        
        # Store filters in session state
        st.session_state.error_filters = {
            "search": search_term,
            "category": selected_category,
            "difficulty": selected_difficulty,
            "frequency": selected_frequency
        }

    
    

    def _render_error_card(self, error: Dict[str, Any], category: str):
        """Render individual error card with enhanced styling and proper content display."""
        error_name = error.get("name", t("unknown_error"))
        description = error.get("description", "")
        difficulty = error.get("difficulty", t("medium"))
        frequency = error.get("frequency", t("medium_frequency"))
        
        # Get user progress for this error
        progress = st.session_state.user_progress.get(error_name, {})
        practiced = progress.get("practiced", False)
        mastered = progress.get("mastered", False)
        
        # Use a container for better layout control
        with st.container():
            # Card header with title
            st.markdown(f"**{error_name}**")
            
            # Badges in a single row using inline HTML
            difficulty_color = "🟢" if difficulty.lower() == "easy" else "🔴" if difficulty.lower() == "hard" else "🟡"
            st.markdown(f"{difficulty_color} {difficulty} | 📊 {frequency}", help="Difficulty and Frequency")
            
            # Description
            if description:
                # Truncate description for card display
                display_description = description[:100] + "..." if len(description) > 100 else description
                st.write(display_description)
            
            # Progress indicators
            progress_text = []
            if practiced:
                progress_text.append("✅ Practiced")
            if mastered:
                progress_text.append("🏆 Mastered")
            
            if progress_text:
                st.markdown(" | ".join(progress_text))
            
            # Action buttons in columns
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(f"📖 {t('view_details')}", key=f"view_{error_name}_{category}", use_container_width=True):
                    self._show_error_details(error, category)
            
            with col2:
                if st.button(f"🎯 {t('practice_error')}", key=f"practice_{error_name}_{category}", use_container_width=True):
                    self._handle_practice_error(error, category)
            
            # Add separator between cards
            st.markdown("---")

    def _render_list_view(self):
        """Render errors in a detailed list view."""
        filtered_data = self._apply_filters()
        
        if not filtered_data:
            self._render_no_results()
            return
        
        # Create a comprehensive list
        all_errors = []
        for category, errors in filtered_data.items():
            for error in errors:
                error_copy = error.copy()
                error_copy["category"] = category
                all_errors.append(error_copy)
        
        # Sort options
        col1, col2 = st.columns([1, 3])
        
        with col1:
            sort_by = st.selectbox(
                t("sort_by"),
                [t("error_name"), t("difficulty"), t("frequency"), t("category")],
                key="sort_option"
            )
        
        # Sort errors
        sort_key_map = {
            t("error_name"): "name",
            t("difficulty"): "difficulty",
            t("frequency"): "frequency",
            t("category"): "category"
        }
        
        sort_key = sort_key_map.get(sort_by, "name")
        all_errors.sort(key=lambda x: x.get(sort_key, ""))
        
        # Render list
        for error in all_errors:
            self._render_error_list_item(error)

    def _render_error_list_item(self, error: Dict[str, Any]):
        """Render individual error as a list item."""
        error_name = error.get("name", t("unknown_error"))
        description = error.get("description", "")
        difficulty = error.get("difficulty", t("medium"))
        frequency = error.get("frequency", t("medium_frequency"))
        category = error.get("category", t("unknown_category"))
        example = error.get("example", "")
        fix = error.get("fix", "")
        
        with st.expander(f"{self._get_category_icon(category)} {error_name} ({category})", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**{t('description')}:** {description}")
                
                if example:
                    st.markdown(f"**{t('example_code')}:**")
                    st.code(example, language="java")
                
                if fix:
                    st.markdown(f"**{t('solution')}:** {fix}")
            
            with col2:
                # Metadata
                st.markdown(f"**{t('difficulty')}:** {difficulty}")
                st.markdown(f"**{t('frequency')}:** {frequency}")
                st.markdown(f"**{t('category')}:** {category}")
                
                # Action buttons
                st.markdown("---")
                
                if st.button(f"🎯 {t('practice_error')}", key=f"list_practice_{error_name}", use_container_width=True):
                    self._handle_practice_error(error, category)
                
                if st.button(f"✅ {t('mark_as_learned')}", key=f"list_learned_{error_name}", use_container_width=True):
                    self._handle_mark_as_learned(error)

    def _render_no_results(self):
        """Render no results message."""
        st.markdown(f"""
        <div class="no-results">
            <div class="no-results-icon">🔍</div>
            <h3>{t('no_errors_found')}</h3>
            <p>{t('try_adjusting_filters')}</p>
        </div>
        """, unsafe_allow_html=True)

    def _show_error_details(self, error: Dict[str, Any], category: str):
        """Show detailed error information in a modal-like expander."""
        error_name = error.get("name", t("unknown_error"))
        error_code = error.get("error_code", "")
        
        # Track viewing in database
        if error_code:
            try:
                self.repository.update_error_usage(
                    error_code=error_code,
                    action_type='viewed',
                    context={'category': category, 'source': 'error_explorer_details'}
                )
            except Exception as e:
                logger.debug(f"Could not track error viewing: {str(e)}")
        
        # Create a detailed view
        st.markdown("---")
        st.markdown(f"## 🔍 {t('error_details')}: {error_name}")
        
        # Detailed information tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            t("overview"), 
            t("examples"), 
            t("solutions"), 
            t("practice_tips")
        ])
        
        with tab1:
            self._render_error_overview(error, category)
        
        with tab2:
            self._render_error_examples(error)
        
        with tab3:
            self._render_error_solutions(error)
        
        with tab4:
            self._render_practice_tips(error)

    def _render_error_overview(self, error: Dict[str, Any], category: str):
        """Render error overview information."""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**{t('description')}:**")
            st.write(error.get("description", t("no_description_available")))
            
            st.markdown(f"**{t('why_important')}:**")
            st.info(t("error_importance_explanation"))
        
        with col2:
            # Metadata
            st.markdown(f"**{t('category')}:** {category}")
            st.markdown(f"**{t('difficulty')}:** {error.get('difficulty', t('medium'))}")
            st.markdown(f"**{t('frequency')}:** {error.get('frequency', t('medium_frequency'))}")
            
            # Progress tracking
            progress = st.session_state.user_progress.get(error.get("name", ""), {})
            
            st.markdown("---")
            st.markdown(f"**{t('your_progress')}:**")
            
            if progress.get("practiced", False):
                st.success(f"✅ {t('practiced')}")
            else:
                st.info(f"⏳ {t('not_practiced_yet')}")
            
            if progress.get("mastered", False):
                st.success(f"🏆 {t('mastered')}")

    def _render_error_examples(self, error: Dict[str, Any]):
        """Render error code examples."""
        example = error.get("example", "")
        
        if example:
            st.markdown(f"### {t('problematic_code')}")
            st.code(example, language="java")
            
            # Generate corrected example (simplified)
            corrected_example = self._generate_corrected_example(example)
            if corrected_example:
                st.markdown(f"### {t('corrected_code')}")
                st.code(corrected_example, language="java")
        else:
            st.info(t("no_examples_available"))

    def _render_error_solutions(self, error: Dict[str, Any]):
        """Render error solutions and fixes."""
        fix = error.get("fix", "")
        
        if fix:
            st.markdown(f"### {t('how_to_fix')}")
            st.success(fix)
            
            # Additional best practices
            st.markdown(f"### {t('best_practices')}")
            st.markdown(t("general_best_practices"))
        else:
            st.info(t("no_solutions_available"))

    def _render_practice_tips(self, error: Dict[str, Any]):
        """Render practice tips and recommendations."""
        st.markdown(f"### {t('practice_recommendations')}")
        
        tips = [
            t("practice_tip_1"),
            t("practice_tip_2"), 
            t("practice_tip_3"),
            t("practice_tip_4")
        ]
        
        for i, tip in enumerate(tips, 1):
            st.markdown(f"{i}. {tip}")
        
        # Related errors
        st.markdown(f"### {t('related_errors')}")
        st.info(t("related_errors_coming_soon"))

    def _handle_practice_error(self, error: Dict[str, Any], category: str):
        """Handle practice error action."""
        error_name = error.get("name", "")
        error_code = error.get("error_code", "")
        
        # Update progress
        if error_name not in st.session_state.user_progress:
            st.session_state.user_progress[error_name] = {}
        
        st.session_state.user_progress[error_name]["practiced"] = True
        
        # Track usage in database
        if error_code:
            try:
                self.repository.update_error_usage(
                    error_code=error_code,
                    action_type='practiced',
                    context={'category': category, 'source': 'error_explorer'}
                )
            except Exception as e:
                logger.debug(f"Could not track error usage: {str(e)}")
        
        st.success(f"🎯 {t('practice_started')}: {error_name}")
        st.info(t("practice_feature_coming_soon"))

    def _handle_mark_as_learned(self, error: Dict[str, Any]):
        """Handle mark as learned action."""
        error_name = error.get("name", "")
        error_code = error.get("error_code", "")
        
        # Update progress
        if error_name not in st.session_state.user_progress:
            st.session_state.user_progress[error_name] = {}
        
        st.session_state.user_progress[error_name]["mastered"] = True
        
        # Track usage in database
        if error_code:
            try:
                self.repository.update_error_usage(
                    error_code=error_code,
                    action_type='mastered',
                    context={'source': 'error_explorer'}
                )
            except Exception as e:
                logger.debug(f"Could not track error usage: {str(e)}")
        
        st.success(f"🏆 {t('marked_as_mastered')}: {error_name}")

    def _load_error_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load the error database from DatabaseErrorRepository."""
        try:
            # Get all categories from database
            categories_data = self.repository.get_all_categories()
            java_categories = categories_data.get("java_errors", [])
            
            if not java_categories:
                logger.warning("No categories found in database, using fallback data")
                return self._get_fallback_error_data()
            
            error_data = {}
            
            # Load errors for each category
            for category_name in java_categories:
                try:
                    category_errors = self.repository.get_category_errors(category_name)
                    
                    # Transform database format to UI format
                    formatted_errors = []
                    for error in category_errors:
                        formatted_error = {
                            "name": error.get(t("error_name"), error.get("error_name", t("unknown_error"))),
                            "description": error.get(t("description"), error.get("description", "")),
                            "difficulty": error.get("difficulty_level", t("medium")),
                            "frequency": self._map_difficulty_to_frequency(error.get("difficulty_level", "medium")),
                            "example": self._generate_example_code(error.get("error_code", ""), error.get(t("error_name"), "")),
                            "fix": error.get(t("implementation_guide"), error.get("implementation_guide", "")),
                            "error_code": error.get("error_code", "")
                        }
                        formatted_errors.append(formatted_error)
                    
                    if formatted_errors:
                        error_data[category_name] = formatted_errors
                        logger.debug(f"Loaded {len(formatted_errors)} errors for category: {category_name}")
                    
                except Exception as e:
                    logger.error(f"Error loading category {category_name}: {str(e)}")
                    continue
            
            if not error_data:
                logger.warning("No error data loaded from database, using fallback")
                return self._get_fallback_error_data()
            
            logger.info(f"Successfully loaded {sum(len(errors) for errors in error_data.values())} errors from database")
            return error_data
            
        except Exception as e:
            logger.error(f"Error loading error database: {str(e)}")
            return self._get_fallback_error_data()

    def _map_difficulty_to_frequency(self, difficulty: str) -> str:
        """Map difficulty level to frequency for display purposes."""
        difficulty_frequency_map = {
            "easy": t("high_frequency"),
            "medium": t("medium_frequency"), 
            "hard": t("low_frequency"),
            t("easy"): t("high_frequency"),
            t("medium"): t("medium_frequency"),
            t("hard"): t("low_frequency")
        }
        return difficulty_frequency_map.get(difficulty, t("medium_frequency"))

    def _generate_example_code(self, error_code: str, error_name: str) -> str:
        """Generate example code based on error type."""
        # Basic example code mapping based on error patterns
        code_examples = {
            "null_pointer": "String str = null; int len = str.length();",
            "array_bounds": "int[] arr = new int[5]; int x = arr[5];",
            "class_cast": "Object obj = \"Hello\"; Integer num = (Integer) obj;",
            "number_format": "int num = Integer.parseInt(\"abc\");",
            "file_not_found": "FileReader fr = new FileReader(\"missing.txt\");",
            "division_by_zero": "int result = 10 / 0;",
            "concurrent_modification": "List<String> list = new ArrayList<>(); for(String s : list) { list.add(\"new\"); }",
            "stack_overflow": "public void recursiveMethod() { recursiveMethod(); }",
            "out_of_memory": "List<Integer> list = new ArrayList<>(); while(true) { list.add(1); }",
            "illegal_argument": "Thread.sleep(-1000);",
            "unsupported_operation": "List<String> list = Arrays.asList(\"a\"); list.add(\"b\");"
        }
        
        # Try to match error name or code to example
        error_key = error_code.lower() if error_code else error_name.lower()
        
        for key, example in code_examples.items():
            if key in error_key:
                return example
        
        # Default example if no match found
        return "// Example code will be provided based on error type"

    def _get_fallback_error_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Provide fallback error data when database is not available."""
        return {
            t("logical"): [
                {
                    "name": t("null_pointer_access"),
                    "description": t("null_pointer_description"),
                    "difficulty": t("medium"),
                    "frequency": t("high_frequency"),
                    "example": "String str = null; int len = str.length();",
                    "fix": t("null_pointer_fix"),
                    "error_code": "NPE001"
                }
            ],
            t("syntax"): [
                {
                    "name": t("missing_semicolon"),
                    "description": t("missing_semicolon_description"),
                    "difficulty": t("easy"),
                    "frequency": t("high_frequency"),
                    "example": "int x = 5",
                    "fix": t("missing_semicolon_fix"),
                    "error_code": "SYN001"
                }
            ]
        }

    def _apply_filters(self) -> Dict[str, List[Dict[str, Any]]]:
        """Apply search and filter criteria to error database."""
        filters = st.session_state.get("error_filters", {})
        filtered_data = {}
        
        for category, errors in self.error_data.items():
            # Apply category filter
            if filters.get("category") and filters["category"] != t("all_categories"):
                if category != filters["category"]:
                    continue
            
            filtered_errors = []
            for error in errors:
                # Apply search filter
                if filters.get("search"):
                    search_term = filters["search"].lower()
                    if (search_term not in error["name"].lower() and 
                        search_term not in error["description"].lower()):
                        continue
                
                # Apply difficulty filter
                if filters.get("difficulty") and filters["difficulty"] != t("all_difficulties"):
                    if error["difficulty"] != filters["difficulty"]:
                        continue
                
                # Apply frequency filter
                if filters.get("frequency") and filters["frequency"] != t("all_frequencies"):
                    if error["frequency"] != filters["frequency"]:
                        continue
                
                filtered_errors.append(error)
            
            if filtered_errors:
                filtered_data[category] = filtered_errors
        
        return filtered_data

    def _get_category_icon(self, category_name: str) -> str:
        """Get icon for category based on name."""
        icon_mapping = {
            t("logical"): "🧠",
            t("syntax"): "🔤", 
            t("code_quality"): "⭐",
            t("standard_violation"): "📋",
            t("java_specific"): "☕",
        }
        return icon_mapping.get(category_name, "🐛")

    def _generate_corrected_example(self, problematic_code: str) -> str:
        """Generate a corrected version of problematic code (simplified)."""
        # This is a simplified example - in real implementation,
        # you would have actual corrected code examples
        corrections = {
            "String str = null; int len = str.length();": "String str = null;\nif (str != null) {\n    int len = str.length();\n}",
            "for(int i = 0; i <= array.length; i++)": "for(int i = 0; i < array.length; i++)",
            "int x = 5": "int x = 5;",
            "if (condition) { ... ": "if (condition) {\n    // code here\n}",
            "int x = calculateTotal();": "int totalAmount = calculateTotal();",
            "class myClass { ... }": "class MyClass {\n    // class implementation\n}"
        }
        
        return corrections.get(problematic_code, "")

    # CSS Styles for the enhanced UI
    def load_error_explorer_styles():
        """Load custom CSS styles for the Error Explorer."""
        st.markdown("""
        <style>
        .error-explorer-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .title-section h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }
        
        .subtitle {
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .stats-section {
            display: flex;
            gap: 1.5rem;
        }
        
        .stat-card {
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        
        .category-section {
            margin: 2rem 0 1rem 0;
        }
        
        .category-title {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .error-count {
            font-size: 0.8em;
            color: #7f8c8d;
            font-weight: normal;
        }
        
        .error-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            border: 1px solid #e9ecef;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .error-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }
        
        .error-title {
            margin: 0;
            color: #2c3e50;
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .badges {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .difficulty-badge, .frequency-badge {
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .error-description {
            color: #6c757d;
            line-height: 1.5;
            margin-bottom: 1rem;
        }
        
        .progress-section {
            margin-bottom: 1rem;
        }
        
        .progress-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            margin-right: 0.5rem;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .progress-badge.practiced {
            background-color: rgba(40, 167, 69, 0.1);
            color: #28a745;
            border: 1px solid #28a745;
        }
        
        .progress-badge.mastered {
            background-color: rgba(255, 193, 7, 0.1);
            color: #ffc107;
            border: 1px solid #ffc107;
        }
        
        .no-results {
            text-align: center;
            padding: 3rem;
            color: #6c757d;
        }
        
        .no-results-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                text-align: center;
            }
            
            .stats-section {
                flex-direction: column;
                width: 100%;
            }
            
            .stat-card {
                width: 100%;
            }
        }
        </style>
        """, unsafe_allow_html=True)

    def get_database_statistics(self) -> Dict[str, Any]:
        """Get database statistics for display or analysis."""
        try:
            return self.repository.get_error_statistics()
        except Exception as e:
            logger.error(f"Error getting database statistics: {str(e)}")
            return {
                'total_errors': sum(len(errors) for errors in self.error_data.values()),
                'total_categories': len(self.error_data),
                'errors_by_category': {cat: len(errors) for cat, errors in self.error_data.items()},
                'most_used_errors': []
            }

    def refresh_error_data(self):
        """Refresh error data from database."""
        try:
            self.error_data = self._load_error_database()
            st.success(t("error_data_refreshed"))
        except Exception as e:
            logger.error(f"Error refreshing data: {str(e)}")
            st.error(t("error_refreshing_data"))
