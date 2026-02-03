import streamlit as st
import pandas as pd

def apply_custom_style():
    """עיצוב נקי עם תיקון סליידר - צביעת הבחירה בלבד"""
    st.markdown("""
        <style>
        /* יישור טקסט לימין בלי לשבור מבנה */
        .main, div[data-testid="stSidebar"] {
            text-align: right;
        }

        h1, h2, h3, h4, h5, h6, label, p, .stMarkdown {
            text-align: right !important;
            direction: rtl !important;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            text-align: right;
            direction: rtl;
        }

        /* תיקון הסליידר: צביעת הטווח הנבחר בלבד (Inner track) */
        /* אנחנו מבטלים את הצבע הכללי שנתנו קודם לכל הדיב */
        div[data-testid="stSlider"] [data-baseweb="slider"] > div {
            background-color: transparent !important;
        }

        /* צביעת הבר הפנימי (הבחירה) בכחול הנכון מהתמונה */
        div[data-testid="stSlider"] [data-baseweb="slider"] div[style*="left"] {
            background-color: #4482eb !important;
        }

        /* כפתורים אפורים נייטרליים */
        .stButton>button { 
            width: 100%; border-radius: 5px; 
            background-color: #F8F9FA !important; color: #495057 !important;
            border: 1px solid #CED4DA !important;
        }
        
        .stButton>button:hover {
            background-color: #E2E6EA !important;
            border-color: #ADB5BD !important;
        }

        /* הודעות מערכת בכחול בהיר */
        div[data-testid="stNotification"] { 
            background-color: #E8F0FE !important; 
            color: #1967D2 !important; 
            border: 1px solid #D2E3FC !important;
        }

        /* צבע לתגיות בחירה (Multi-select) */
        span[data-baseweb="tag"] {
            background-color: #4482eb !important;
        }
        </style>
        """, unsafe_allow_html=True)

def reset_params():
    """איפוס פרמטרים וחזרה למצב נקי"""
    active = st.session_state.get('active_query')
    selected = st.session_state.get('selected_mode')
    for key in list(st.session_state.keys()):
        if not key.startswith('_'):
            del st.session_state[key]
    if active: st.session_state.active_query = active
    if selected: st.session_state.selected_mode = selected
    st.session_state.custom_conditions = []
    st.rerun()
