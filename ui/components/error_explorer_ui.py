import streamlit as st
from learning.error_library_manager import ErrorLibraryManager # Assuming correct path
from typing import List, Dict, Optional

class ErrorExplorerUI:
    """
    UI component for exploring detailed information about programming errors.
    """

    def __init__(self):
        """
        Initializes the ErrorExplorerUI with an ErrorLibraryManager instance.
        """
        self.manager = ErrorLibraryManager()
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
            st.sidebar.warning("No errors found in the library.")
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
            "Select an Error to View Details:",
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

if __name__ == '__main__':
    # For testing this component independently
    ui = ErrorExplorerUI()
    ui.render()
