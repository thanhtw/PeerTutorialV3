import streamlit as st
from learning.error_library_manager import ErrorLibraryManager # Assuming correct path
from typing import List, Dict, Optional, Any
from utils.language_utils import t

class ErrorExplorerUI:
    """
    UI component for exploring detailed information about programming errors.
    """

    def __init__(self):
        """
        Initializes the ErrorExplorerUI with an ErrorLibraryManager instance.
        """
        self.manager = ErrorLibraryManager()
        self.error_data = self._load_error_database()
        if "selected_error_code" not in st.session_state:
            st.session_state.selected_error_code = None

    def render_error_selection(self) -> Optional[str]:
        """
        Renders the error selection interface (e.g., a selectbox in the sidebar).
        Fetches available errors from the ErrorLibraryManager.
        Updates and returns the selected error_code from session state.
        """
        error_list: List[Dict[str, str]] = self.manager.get_all_error_codes_and_titles()

        if not error_list:
            st.sidebar.warning(f"{t('no_errors_found_in_library')}")
            st.session_state.selected_error_code = None
            return None

        # Create a list of display options for the selectbox: "Title (error_code)"
        # And a mapping from this display option back to the error_code
        display_options = [f"{item['title']} ({item['error_code']})" for item in error_list]
        options_to_codes = {f"{item['title']} ({item['error_code']})": item['error_code'] for item in error_list}
        codes_to_options = {v: k for k, v in options_to_codes.items()}

        # Get current selection from session state to set default for selectbox
        current_selected_display_option = None
        if st.session_state.selected_error_code and st.session_state.selected_error_code in codes_to_options:
            current_selected_display_option = codes_to_options[st.session_state.selected_error_code]
        
        st.sidebar.title("Error Explorer")
        selected_display_option = st.sidebar.selectbox(
            t("select_error_to_view"),  # Better descriptive label
            options=display_options,
            index=display_options.index(current_selected_display_option) if current_selected_display_option in display_options else 0,
            key="error_explorer_selectbox" 
        )

        if selected_display_option:
            st.session_state.selected_error_code = options_to_codes[selected_display_option]
        else: # Should not happen with selectbox unless error_list is empty initially
            st.session_state.selected_error_code = None
            
        return st.session_state.selected_error_code

    def render(self):
        """
        Renders the complete Error Explorer UI.
        """
        selected_code = self.render_error_selection()

        if selected_code:
            details = self.manager.get_error_detail(selected_code)
            if details:
                st.header(details.get('title', selected_code)) # Fallback to code if title missing
                
                st.markdown("---")
                st.subheader("Description")
                st.markdown(details.get('detailed_description_md', "*No description available.*"))

                st.subheader("Problematic Code Example")
                st.markdown(details.get('example_bad_code_md', "*No bad code example available.*"))

                st.subheader("Correct Code Example")
                st.markdown(details.get('example_good_code_md', "*No good code example available.*"))

                st.subheader("Before & After Comparison / Explanation")
                st.markdown(details.get('before_after_comparison_md', "*No comparison available.*"))
                
                st.subheader("Common Misconceptions")
                st.markdown(details.get('common_misconceptions_md', "*No common misconceptions listed.*"))

                st.subheader("Why It's Important")
                st.markdown(details.get('importance_explanation_md', "*No importance explanation provided.*"))
                
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"Language: {details.get('language', 'N/A')}")
                with col2:
                    st.caption(f"Created: {details.get('created_at', 'N/A')}")
                with col3:
                    st.caption(f"Last Updated: {details.get('updated_at', 'N/A')}")

            else:
                st.warning(f"Could not retrieve details for error code: {selected_code}")
        else:
            st.info("Select an error from the sidebar to view its details.")

        # New UI Elements using translation functions
        st.header(f"🔍 {t('error_explorer')}")
        
        # Search and filter controls
        self._render_search_filters()
        
        # Error categories overview
        self._render_categories_overview()
        
        # Main content area
        col1, col2 = st.columns([1, 2])
        
        with col1:
            selected_error = self._render_error_list()
        
        with col2:
            if selected_error:
                self._render_error_details(selected_error)
            else:
                self._render_welcome_message()

    def _load_error_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load the error database (mock data)."""
        return {
            t("logical"): [
                {
                    "name": "Null Pointer Access",
                    "description": "Accessing an object reference that points to null",
                    "difficulty": t("medium"),
                    "frequency": "High",
                    "example": "String str = null; int len = str.length();",
                    "fix": "Check for null before accessing: if (str != null) { ... }"
                },
                {
                    "name": "Off-by-One Error", 
                    "description": "Array or loop boundary errors",
                    "difficulty": t("easy"),
                    "frequency": "Medium",
                    "example": "for(int i = 0; i <= array.length; i++)",
                    "fix": "Use < instead of <= for array bounds"
                }
            ],
            t("syntax"): [
                {
                    "name": "Missing Semicolon",
                    "description": "Statement not terminated with semicolon",
                    "difficulty": t("easy"),
                    "frequency": "High", 
                    "example": "int x = 5",
                    "fix": "Add semicolon: int x = 5;"
                },
                {
                    "name": "Mismatched Braces",
                    "description": "Opening and closing braces don't match",
                    "difficulty": t("easy"),
                    "frequency": "Medium",
                    "example": "if (condition) { ... ",
                    "fix": "Ensure every opening brace has a closing brace"
                }
            ],
            t("code_quality"): [
                {
                    "name": "Poor Variable Naming",
                    "description": "Variable names are not descriptive",
                    "difficulty": t("medium"),
                    "frequency": "High",
                    "example": "int x = calculateTotal();",
                    "fix": "Use descriptive names: int totalAmount = calculateTotal();"
                }
            ],
            t("standard_violation"): [
                {
                    "name": "Naming Convention Violation",
                    "description": "Class or method names don't follow Java conventions",
                    "difficulty": t("easy"),
                    "frequency": "Medium",
                    "example": "class myClass { ... }",
                    "fix": "Use PascalCase for classes: class MyClass { ... }"
                }
            ],
            t("java_specific"): [
                {
                    "name": "Resource Leak",
                    "description": "Resources not properly closed",
                    "difficulty": t("hard"),
                    "frequency": "Medium",
                    "example": "FileInputStream fis = new FileInputStream(file);",
                    "fix": "Use try-with-resources or ensure proper closing"
                }
            ]
        }
    
    def _render_search_filters(self):
        """Render search and filter controls."""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input(
                t("error_search"),
                placeholder=t("search_placeholder"),
                key="error_search"
            )
        
        with col2:
            selected_category = st.selectbox(
                t("filter_by_category"),
                [t("all_categories")] + list(self.error_data.keys()),
                key="category_filter"
            )
        
        with col3:
            selected_difficulty = st.selectbox(
                t("difficulty_level"),
                [t("all_categories"), t("easy"), t("medium"), t("hard")],
                key="difficulty_filter"
            )
        
        # Store filters in session state
        st.session_state.error_filters = {
            "search": search_term,
            "category": selected_category,
            "difficulty": selected_difficulty
        }
    
    def _render_categories_overview(self):
        """Render error categories overview."""
        st.subheader(f"📊 {t('error_categories')}")
        
        cols = st.columns(len(self.error_data))
        
        for i, (category, errors) in enumerate(self.error_data.items()):
            with cols[i]:
                st.metric(
                    category,
                    len(errors),
                    delta=f"{len([e for e in errors if e['frequency'] == 'High'])} high freq"
                )
    
    def _render_error_list(self) -> Optional[Dict[str, Any]]:
        """Render the list of errors and return selected error."""
        st.subheader(f"📋 {t('browse_errors')}")
        
        # Apply filters
        filtered_errors = self._apply_filters()
        
        if not filtered_errors:
            st.warning(t("no_errors_found_in_library"))
            return None
        
        # Create selection list
        error_options = []
        error_map = {}
        
        for category, errors in filtered_errors.items():
            for error in errors:
                option_text = f"{error['name']} ({category})"
                error_options.append(option_text)
                error_map[option_text] = {"error": error, "category": category}
        
        selected_option = st.selectbox(
            t("select_error_for_details"),  # Better descriptive label
            error_options,
            key="selected_error"
        )
        
        if selected_option:
            return error_map[selected_option]
        
        return None
    
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
                if filters.get("difficulty") and filters["difficulty"] != t("all_categories"):
                    if error["difficulty"] != filters["difficulty"]:
                        continue
                
                filtered_errors.append(error)
            
            if filtered_errors:
                filtered_data[category] = filtered_errors
        
        return filtered_data
    
    def _render_error_details(self, selected_data: Dict[str, Any]):
        """Render detailed information about the selected error."""
        error = selected_data["error"]
        category = selected_data["category"]
        
        st.subheader(f"🔍 {error['name']}")
        
        # Error metadata
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(t("difficulty_level"), error["difficulty"])
        
        with col2:
            st.metric(t("error_frequency"), error["frequency"])
        
        with col3:
            st.metric("Category", category)
        
        # Error description
        st.markdown(f"**{t('error_details')}:**")
        st.write(error["description"])
        
        # Code example
        st.markdown(f"**{t('common_mistakes')}:**")
        st.code(error["example"], language="java")
        
        # Fix suggestion
        st.markdown(f"**{t('best_practices')}:**")
        st.success(error["fix"])
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"🎯 {t('practice_this_error')}", key=f"practice_{error['name']}"):
                st.info(f"🚀 {t('practice_this_error')} feature coming soon!")
        
        with col2:
            if st.button(f"✅ {t('mark_as_learned')}", key=f"learned_{error['name']}"):
                st.success(f"✅ {t('mark_as_learned')}!")
        
        with col3:
            if st.button(f"📖 {t('view_details')}", key=f"details_{error['name']}"):
                self._show_detailed_explanation(error)
    
    def _render_welcome_message(self):
        """Render welcome message when no error is selected."""
        st.markdown(f"""
        <div style="text-align: center; padding: 40px;">
            <h3>👋 {t('welcome_to')} {t('error_explorer')}</h3>
            <p>{t('browse_errors')} and learn about different types of Java errors.</p>
            <p>Select an error from the list to see detailed information and examples.</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _show_detailed_explanation(self, error: Dict[str, Any]):
        """Show detailed explanation in an expander."""
        with st.expander(f"📖 {t('implementation_examples')}", expanded=True):
            st.markdown(f"""
            ### {t('implementation_examples')}
            
            **Problem:** {error['description']}
            
            **Example of the Error:**
            ```java
            {error['example']}
            ```
            
            **How to Fix:**
            {error['fix']}
            
            **{t('best_practices')}:**
            - Always validate inputs
            - Use proper error handling
            - Follow Java naming conventions
            - Write clear, self-documenting code
            """)
