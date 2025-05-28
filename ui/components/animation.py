"""
Animation utilities for the Java Peer Code Review Training System.
"""

import streamlit as st
import time
import os # For path joining

# Helper function to load CSS
def load_css(file_path):
    with open(file_path) as f:
        return f.read()

# Get the absolute path to the CSS file
# Assuming this script is in ui/components and css is in static/css
# Adjust the path as necessary based on your project structure
CSS_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "static", "css", "animations.css")
# print(f"Attempting to load CSS from: {CSS_FILE_PATH}") # For debugging path issues

try:
    ANIMATION_CSS = load_css(CSS_FILE_PATH)
except FileNotFoundError:
    ANIMATION_CSS = "/* CSS file not found, using fallback styles */"
    # print(f"Error: CSS file not found at {CSS_FILE_PATH}") # For debugging

def level_up_animation(old_level: str, new_level: str) -> None:
    """
    Display a level-up animation when a user advances to a new level.
    
    Args:
        old_level: Previous user level
        new_level: New user level
    """
    # Inject CSS into the page
    st.markdown(f"<style>{ANIMATION_CSS}</style>", unsafe_allow_html=True)

    # Create a container for the animation
    animation_placeholder = st.empty()

    # Initial state
    initial_html = f"""
    <div class="level-up-container initial">
        <div class="level-up-text-wrapper">
            <div class="level-up-title level-up-text-pop delay-1">Level Up!</div>
            <div class="level-up-levels level-up-text-pop delay-2">
                {old_level.capitalize()} → {new_level.capitalize()}
            </div>
        </div>
    </div>
    """
    animation_placeholder.markdown(initial_html, unsafe_allow_html=True)
    time.sleep(1) # Hold initial state for a moment

    # Animate with fireworks effect
    # The fireworks are now CSS-driven, but we can trigger them by adding/removing classes
    # or by re-rendering the container with particle elements.
    # For this iteration, we'll create a more dynamic particle effect in the final state.

    # Transition to final state with particles
    particles_html = ""
    particle_emojis = ["✨", "🎉", "🌟", "🏆", "💖", "🚀"]
    for i in range(8): # Number of particles
        emoji = particle_emojis[i % len(particle_emojis)]
        top = (i * 13 + 10 + (i*3)) % 80  # Spread them out
        left = (i * 17 + 5 + (i*5)) % 90
        delay = i * 0.1 # Staggered animation
        particles_html += f"""
        <div class="firework-particle" style="top: {top}%; left: {left}%; animation-delay: {delay}s;">{emoji}</div>
        """

    final_html = f"""
    <div class="level-up-container final">
        {particles_html}
        <div class="level-up-text-wrapper">
            <div class="level-up-congrats level-up-text-pop delay-1">Congratulations!</div>
            <div class="level-up-reached level-up-text-pop delay-2">
                You've reached {new_level.capitalize()} Level!
            </div>
            <div class="level-up-unlocked-message level-up-text-pop delay-3">
                <span class="level-up-unlocked-text">
                    New badges and challenges unlocked!
                </span>
            </div>
        </div>
    </div>
    """
    animation_placeholder.markdown(final_html, unsafe_allow_html=True)
    
    # Keep the final state visible for a few seconds
    time.sleep(3)

    # Clear the animation area after a delay or keep it, depending on desired UX
    # For now, let it stay, then show the success message.
    # animation_placeholder.empty() # Optional: clear after animation

    st.success(f"You've been promoted to {new_level.capitalize()} level! New challenges and badges are now available.")