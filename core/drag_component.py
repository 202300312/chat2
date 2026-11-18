"""Lightweight, dependency-free draggable room designer Streamlit component."""
from pathlib import Path
import streamlit.components.v1 as components

_designer = components.declare_component('eco_drag_designer', path=str(Path(__file__).resolve().parent.parent / 'frontend'))

def designer(design, catalog, key='designer'):
    return _designer(design=design, catalog=catalog, key=key, default=None, height=max(875, 270 + 43 * len(catalog)))
