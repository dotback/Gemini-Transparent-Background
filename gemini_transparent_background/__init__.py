"""
Gemini Transparent Background
=============================

A Python package to remove green backgrounds from AI-generated images
(specifically from Gemini Nano Banana Pro) and convert them to transparent PNGs.
"""

__version__ = "0.1.0"

from .advanced import remove_background_advanced

__all__ = [
    "remove_background_advanced",
]
