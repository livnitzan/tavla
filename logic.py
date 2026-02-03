import streamlit as st
import pandas as pd

def apply_custom_style():
    """תיקון לסליידר משובש ויישור לימין של תוכן האפליקציה"""
    import streamlit as st
    st.markdown("""
        <style>
        /* יישור כללי לימין של התוכן */
        [data-testid="stMain"] .block-container {
            direction: RTL;
            text-align: right;
        }

        /* יישור התוכן בתוך הסיידבר */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            direction: RTL;
            text-align: right;
        }

        /* תיקון לסליידר - כפיית כיוון שמאל-לימין לרכיב עצמו למניעת שיבוש חזותי */
        div[data-testid="stSlider"] {
            direction: LTR !important;
        }
        
        /* החזרת הכותרת של הסליידר לימין */
        div[data-testid="stSlider"] label {
            direction: RTL !important;
            text-align: right !important;
            display: block;
            width: 100%;
        }

        /* כפתורים אפורים נייטרליים */
        .stButton>button { 
            width: 100%; border-radius: 5px; 
            background-color: #F8F9FA !important; color: #495057 !important;
            border: 1px solid #CED4DA !important;
        }
        
        /* הודעות מערכת בכחול בהיר מהתמונה */
        div[data-testid="stNotification"] { 
            background-color: #E8F0FE !important; 
            color: #1967D2 !important; 
            border: 1px solid #D2E3FC !important;
        }

        /* צבע כחול לסליידר ולתגיות */
        .stSlider [data-baseweb="slider"] > div > div {
            background-color: #4482eb !important;
        }
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
