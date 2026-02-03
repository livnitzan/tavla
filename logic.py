import streamlit as st
import pandas as pd

def apply_custom_style():
    """תיקון תצוגה לגרסת הענן - מניעת חיתוך טקסט ב-Sidebar"""
    import streamlit as st
    st.markdown("""
        <style>
        /* יישור כללי לימין בלי לשבור את המבנה של Streamlit */
        .main .block-container {
            direction: RTL;
            text-align: right;
        }
        
        /* תיקון ספציפי ל-Sidebar למניעת חיתוך טקסט */
        [data-testid="stSidebar"] {
            direction: RTL;
        }
        
        [data-testid="stSidebar"] .stSelectbox, 
        [data-testid="stSidebar"] .stRadio {
            direction: RTL;
            text-align: right;
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

        /* הודעות מערכת בכחול בהיר (הגוון שביקשת) */
        div[data-testid="stNotification"] { 
            background-color: #E8F0FE !important; 
            color: #1967D2 !important; 
            border: 1px solid #D2E3FC !important;
        }

        /* צבע כחול לסליידר ולרכיבי בחירה */
        .stSlider [data-baseweb="slider"] > div > div {
            background-color: #4482eb !important;
        }
        
        span[data-baseweb="tag"] {
            background-color: #4482eb !important;
        }
        </style>
        """, unsafe_allow_html=True)

def reset_params():
    """איפוס פרמטרים וחזרה למצב נקי תוך שמירת העמוד הנוכחי"""
    active = st.session_state.get('active_query')
    selected = st.session_state.get('selected_mode')
    
    for key in list(st.session_state.keys()):
        # לא מוחקים משתני מערכת של Streamlit
        if not key.startswith('_'):
            del st.session_state[key]
        
    if active: 
        st.session_state.active_query = active
    if selected:
        st.session_state.selected_mode = selected
        
    st.session_state.custom_conditions = []
    st.rerun()
